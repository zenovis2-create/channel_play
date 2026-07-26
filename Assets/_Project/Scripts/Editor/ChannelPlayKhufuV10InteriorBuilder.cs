using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV10InteriorBuilder
{
    public const string ScenePath = ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath;
    public const string MapRootName = ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName;
    public const string RunRoot = "runs/khufu-v10-interior-spine";
    public const string RootName = "Runtime_Khufu_V10_Interior_Spine";
    public const string VisualRootName = "V10_Visuals";
    public const string PairRootName = "V10_Structural_Pairs";
    public const string CollisionRootName = "V10_Collision_Proxies";
    public const string MetadataRootName = "V10_Metadata";
    public const string MaterialRoot = "Assets/_Project/Materials/KhufuV10Interior";
    public const string DisableManifestPath = "docs/khufu-v10-interior-spine/disable-manifest.json";
    public const string ClassificationPath = "docs/khufu-v10-interior-spine/segment-classification.json";

    public const int BaselineRenderers = 818;
    public const int BaselineVertices = 59030;
    public const int BaselineTriangles = 44540;
    public const int BaselineColliders = 464;
    public const int MaximumRootRenderers = 6;
    public const int MaximumRootVertices = 100000;
    public const int MaximumRootTriangles = 80000;
    public const int MaximumMapRenderers = 824;
    public const int MaximumMapColliders = 620;

    [MenuItem("Channel Play/Khufu V10/Rebuild Interior Spine")]
    public static void Rebuild()
    {
        var manifest = LoadDisableManifest();
        var classification = LoadClassification();
        ValidateContracts(manifest, classification);

        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(MapRootName);
        if (mapObject == null) throw new InvalidOperationException("Shared map root is missing.");
        var map = mapObject.transform;
        if (map.position != Vector3.zero || map.rotation != Quaternion.identity || map.lossyScale != Vector3.one)
            throw new InvalidOperationException("Shared map root transform drifted from identity.");

        var previous = map.Find(RootName);
        if (previous == null)
        {
            var sceneSha = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ScenePath);
            if (!string.Equals(sceneSha, manifest.SceneSha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("V10 first-write scene SHA drifted. expected=" + manifest.SceneSha256 + " actual=" + sceneSha);
        }

        RestoreManifestTransitions(map, manifest);
        var mapBeforeBuild = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        var baseline = previous == null
            ? mapBeforeBuild
            : Subtract(mapBeforeBuild, ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(previous));
        if (!Matches(baseline, BaselineRenderers, BaselineVertices, BaselineTriangles, BaselineColliders))
            throw new InvalidOperationException("Frozen V9 map baseline drifted: " + MetricsToken(baseline));

        var specs = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs();
        ValidateSpecs(specs, classification);
        var meshes = ChannelPlayKhufuV10InteriorMeshPipeline.BuildAndSaveMeshes(specs);
        var materials = BuildMaterials();

        var root = previous ?? Child(map, RootName);
        root.SetParent(map, false);
        root.localPosition = Vector3.zero;
        root.localRotation = Quaternion.identity;
        root.localScale = Vector3.one;
        var visuals = EnsureChild(root, VisualRootName);
        var pairs = EnsureChild(root, PairRootName);
        var proxies = EnsureChild(root, CollisionRootName);
        var metadata = EnsureChild(root, MetadataRootName);
        PruneChildren(root, new[] { VisualRootName, PairRootName, CollisionRootName, MetadataRootName });
        ConfigureTag(root, ChannelPlayKhufuV10InteriorMeshPipeline.Segments, classification);
        ConfigureTag(visuals, ChannelPlayKhufuV10InteriorMeshPipeline.Segments, classification);
        ConfigureTag(pairs, ChannelPlayKhufuV10InteriorMeshPipeline.Segments, classification);
        ConfigureTag(proxies, ChannelPlayKhufuV10InteriorMeshPipeline.Segments, classification);
        ConfigureTag(metadata, ChannelPlayKhufuV10InteriorMeshPipeline.Segments, classification);

        foreach (var bucket in ChannelPlayKhufuV10InteriorMeshPipeline.Buckets)
        {
            var segmentIds = specs.Where(item => item.Bucket == bucket).Select(item => item.SegmentId).Distinct();
            CreateRenderer(visuals, bucket, meshes[bucket], materials[bucket], segmentIds, classification);
        }
        PruneChildren(visuals, ChannelPlayKhufuV10InteriorMeshPipeline.Buckets.Select(item => "V10_" + item));

        var pairNames = new List<string>();
        var proxyNames = new List<string>();
        foreach (var spec in specs.Where(item => item.Structural && item.Collider))
        {
            var pairName = "V10_PAIR_" + spec.SegmentId + "_" + spec.Name;
            var proxyName = "V10_PROXY_" + spec.SegmentId + "_" + spec.Name;
            pairNames.Add(pairName);
            proxyNames.Add(proxyName);
            var marker = EnsureChild(pairs, pairName);
            SetTransform(marker, spec);
            ConfigureTag(marker, new[] { spec.SegmentId }, classification);

            var proxy = EnsureChild(proxies, proxyName);
            SetTransform(proxy, spec);
            ConfigureTag(proxy, new[] { spec.SegmentId }, classification);
            var collider = proxy.GetComponent<BoxCollider>();
            if (collider == null) collider = proxy.gameObject.AddComponent<BoxCollider>();
            collider.center = Vector3.zero;
            collider.size = Vector3.one;
            collider.isTrigger = false;
            collider.enabled = true;
        }
        PruneChildren(pairs, pairNames);
        PruneChildren(proxies, proxyNames);

        PruneChildren(metadata, AddMetadata(metadata, classification));
        ApplyManifestTransitions(map, manifest);
        ValidateAppliedTransitions(map, manifest);

        var added = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        var expectedColliders = specs.Count(item => item.Structural && item.Collider);
        if (added.Renderers != ChannelPlayKhufuV10InteriorMeshPipeline.ExpectedRendererCount ||
            added.Colliders != expectedColliders || added.Renderers > MaximumRootRenderers ||
            added.Vertices > MaximumRootVertices || added.Triangles > MaximumRootTriangles)
        {
            throw new InvalidOperationException("V10 root exceeded budget: " + MetricsToken(added));
        }

        var finalMap = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (finalMap.Renderers > MaximumMapRenderers || finalMap.Colliders > MaximumMapColliders)
            throw new InvalidOperationException("V10 full-map budget exceeded: " + MetricsToken(finalMap));

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V10_BUILD result=built renderers=" + added.Renderers +
                  " vertices=" + added.Vertices + " triangles=" + added.Triangles +
                  " colliders=" + added.Colliders + " disabledRenderers=" + manifest.ExpectedRendererTransitions +
                  " disabledColliders=" + manifest.ExpectedColliderTransitions);
    }

    public static void RunBatch()
    {
        try
        {
            Rebuild();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    public static ChannelPlayKhufuV10InteriorAudit.DisableManifest LoadDisableManifest()
    {
        if (!File.Exists(DisableManifestPath)) throw new FileNotFoundException("V10 disable manifest is missing.", DisableManifestPath);
        var manifest = JsonUtility.FromJson<ChannelPlayKhufuV10InteriorAudit.DisableManifest>(File.ReadAllText(DisableManifestPath));
        if (manifest == null) throw new InvalidOperationException("V10 disable manifest could not be parsed.");
        return manifest;
    }

    public static SegmentClassificationDocument LoadClassification()
    {
        if (!File.Exists(ClassificationPath)) throw new FileNotFoundException("V10 segment classification is missing.", ClassificationPath);
        var document = JsonUtility.FromJson<SegmentClassificationDocument>(File.ReadAllText(ClassificationPath));
        if (document == null) throw new InvalidOperationException("V10 segment classification could not be parsed.");
        return document;
    }

    public static Transform ResolvePath(Transform map, string relativePath)
    {
        if (map == null || string.IsNullOrEmpty(relativePath)) return null;
        return map.Find(relativePath);
    }

    public static void RestoreManifestTransitions(Transform map, ChannelPlayKhufuV10InteriorAudit.DisableManifest manifest)
    {
        foreach (var transition in manifest.Transitions)
        {
            var target = ResolveRequired(map, transition.Path);
            var renderer = target.GetComponent<Renderer>();
            if (transition.DisableRenderer)
            {
                if (renderer == null) throw new InvalidOperationException("Manifest renderer is missing: " + transition.Path);
                renderer.enabled = transition.RendererEnabled;
            }
            if (transition.DisableCollider)
            {
                var collider = target.GetComponent<Collider>();
                if (collider == null) throw new InvalidOperationException("Manifest collider is missing: " + transition.Path);
                collider.enabled = transition.ColliderEnabled;
                collider.isTrigger = transition.ColliderIsTrigger;
            }
        }
    }

    public static void ApplyManifestTransitions(Transform map, ChannelPlayKhufuV10InteriorAudit.DisableManifest manifest)
    {
        foreach (var transition in manifest.Transitions)
        {
            var target = ResolveRequired(map, transition.Path);
            if (transition.DisableRenderer) target.GetComponent<Renderer>().enabled = false;
            if (transition.DisableCollider) target.GetComponent<Collider>().enabled = false;
        }
    }

    public static List<Renderer> CollectManifestRenderers(Transform map, ChannelPlayKhufuV10InteriorAudit.DisableManifest manifest)
    {
        return manifest.Transitions.Where(item => item.DisableRenderer)
            .Select(item => ResolveRequired(map, item.Path).GetComponent<Renderer>())
            .OrderBy(item => item.name, StringComparer.Ordinal)
            .ToList();
    }

    public static List<Collider> CollectManifestColliders(Transform map, ChannelPlayKhufuV10InteriorAudit.DisableManifest manifest)
    {
        return manifest.Transitions.Where(item => item.DisableCollider)
            .Select(item => ResolveRequired(map, item.Path).GetComponent<Collider>())
            .OrderBy(item => item.name, StringComparer.Ordinal)
            .ToList();
    }

    private static void ValidateContracts(ChannelPlayKhufuV10InteriorAudit.DisableManifest manifest,
        SegmentClassificationDocument classification)
    {
        if (manifest.Schema != "khufu-v10-interior-disable-manifest-v1")
            throw new InvalidOperationException("V10 disable manifest schema drifted.");
        if (manifest.ScenePath != ScenePath || manifest.ExpectedRendererTransitions != 60 ||
            manifest.ExpectedColliderTransitions != 39 || manifest.CrownIntersectionCount != 0)
            throw new InvalidOperationException("V10 disable manifest contract drifted.");
        if (manifest.Transitions.Count(item => item.DisableRenderer) != manifest.ExpectedRendererTransitions ||
            manifest.Transitions.Count(item => item.DisableCollider) != manifest.ExpectedColliderTransitions)
            throw new InvalidOperationException("V10 disable transition counts drifted.");
        if (classification.schema != "khufu-v10-interior-segment-classification-v1")
            throw new InvalidOperationException("V10 segment classification schema drifted.");
        var expected = new HashSet<string>(ChannelPlayKhufuV10InteriorMeshPipeline.Segments, StringComparer.Ordinal);
        var actual = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        if (!expected.SetEquals(actual) || classification.segments.Count != expected.Count)
            throw new InvalidOperationException("V10 segment classification inventory drifted.");
    }

    private static void ValidateSpecs(IEnumerable<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs,
        SegmentClassificationDocument classification)
    {
        var segments = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        foreach (var spec in specs)
        {
            if (!segments.Contains(spec.SegmentId)) throw new InvalidOperationException("Unclassified V10 spec: " + spec.Name);
            if (!ChannelPlayKhufuV10InteriorMeshPipeline.Buckets.Contains(spec.Bucket))
                throw new InvalidOperationException("Unknown V10 mesh bucket: " + spec.Bucket);
            if (spec.Scale.x <= 0f || spec.Scale.y <= 0f || spec.Scale.z <= 0f)
                throw new InvalidOperationException("Invalid V10 spec scale: " + spec.Name);
        }
    }

    private static Dictionary<string, Material> BuildMaterials()
    {
        EnsureAssetFolder(MaterialRoot);
        var result = new Dictionary<string, Material>(StringComparer.Ordinal)
        {
            { ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket,
                CreateOrUpdateMaterial("V10_Aged_Limestone", "V6_Interior_Limestone", new Color(0.67f, 0.57f, 0.42f, 1f), 0.02f, 0.25f) },
            { ChannelPlayKhufuV10InteriorMeshPipeline.GalleryDetailBucket,
                CreateOrUpdateMaterial("V10_Gallery_Detail", "V6_Tura_Casing", new Color(0.50f, 0.38f, 0.24f, 1f), 0.03f, 0.28f) },
            { ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket,
                CreateOrUpdateMaterial("V10_Red_Granite", "V6_Red_Granite", new Color(0.42f, 0.13f, 0.09f, 1f), 0.06f, 0.34f) },
            { ChannelPlayKhufuV10InteriorMeshPipeline.HybridBucket,
                CreateOrUpdateMaterial("V10_Hybrid_Service", "V6_Basalt_Court", new Color(0.16f, 0.18f, 0.16f, 1f), 0.16f, 0.28f) },
            { ChannelPlayKhufuV10InteriorMeshPipeline.ShadowBucket,
                CreateOrUpdateMaterial("V10_Deep_Shadow", "V6_Core_Limestone", new Color(0.018f, 0.014f, 0.012f, 1f), 0f, 0.08f) },
            { ChannelPlayKhufuV10InteriorMeshPipeline.InlayBucket,
                CreateOrUpdateMaterial("V10_Route_Amber", "V6_Scan_Inlay", new Color(1f, 0.30f, 0.035f, 1f), 0.08f, 0.42f,
                    new Color(2.6f, 0.55f, 0.04f, 1f)) }
        };
        AssetDatabase.SaveAssets();
        return result;
    }

    private static Material CreateOrUpdateMaterial(string assetName, string baseName, Color color, float metallic,
        float smoothness, Color? emission = null)
    {
        var source = ChannelPlayKhufuV6VisualFidelityBuilder.LoadMaterial(baseName);
        if (source == null) throw new InvalidOperationException("V10 source material is missing: " + baseName);
        var path = MaterialRoot + "/" + assetName + ".mat";
        var target = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (target == null)
        {
            target = new Material(source) { name = assetName };
            AssetDatabase.CreateAsset(target, path);
        }
        else
        {
            EditorUtility.CopySerialized(source, target);
            target.name = assetName;
        }
        SetColor(target, "_BaseColor", color);
        SetColor(target, "_Color", color);
        SetFloat(target, "_Metallic", metallic);
        SetFloat(target, "_Smoothness", smoothness);
        if (emission.HasValue)
        {
            SetColor(target, "_EmissionColor", emission.Value);
            target.EnableKeyword("_EMISSION");
        }
        EditorUtility.SetDirty(target);
        return target;
    }

    private static IReadOnlyCollection<string> AddMetadata(Transform metadata, SegmentClassificationDocument classification)
    {
        var names = new List<string>();
        names.Add("V10_Anchor_North_Entrance");
        AddMarker(metadata, "V10_Anchor_North_Entrance", ChannelPlayKhufuV10InteriorMeshPipeline.Entrance,
            new[] { ChannelPlayKhufuV10InteriorMeshPipeline.NorthApproachSegment, ChannelPlayKhufuV10InteriorMeshPipeline.EntranceBranchSegment }, classification);
        names.Add("V10_Anchor_Ascending_Branch");
        AddMarker(metadata, "V10_Anchor_Ascending_Branch", ChannelPlayKhufuV10InteriorMeshPipeline.Branch,
            new[] { ChannelPlayKhufuV10InteriorMeshPipeline.EntranceBranchSegment, ChannelPlayKhufuV10InteriorMeshPipeline.BranchGallerySegment,
                ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnSegment }, classification);
        names.Add("V10_Anchor_Grand_Gallery_Foot");
        AddMarker(metadata, "V10_Anchor_Grand_Gallery_Foot", ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFoot,
            new[] { ChannelPlayKhufuV10InteriorMeshPipeline.BranchGallerySegment, ChannelPlayKhufuV10InteriorMeshPipeline.GrandGallerySegment,
                ChannelPlayKhufuV10InteriorMeshPipeline.QueenThresholdSegment, ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnSegment }, classification);
        names.Add("V10_Anchor_Great_Step_Stop");
        AddMarker(metadata, "V10_Anchor_Great_Step_Stop", ChannelPlayKhufuV10InteriorMeshPipeline.GreatStepStop(),
            new[] { ChannelPlayKhufuV10InteriorMeshPipeline.GrandGallerySegment, ChannelPlayKhufuV10InteriorMeshPipeline.GreatStepSegment }, classification);
        names.Add("V10_Anchor_Historic_Service_Mouth");
        AddMarker(metadata, "V10_Anchor_Historic_Service_Mouth", ChannelPlayKhufuV10InteriorMeshPipeline.HistoricServiceMouth(),
            new[] { ChannelPlayKhufuV10InteriorMeshPipeline.HistoricServiceSegment }, classification);
        var returnPoints = ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnPoints();
        for (var index = 0; index < returnPoints.Count; index++)
        {
            var name = "V10_Anchor_HYBRID_Return_" + index.ToString("D2");
            names.Add(name);
            AddMarker(metadata, name, returnPoints[index],
                new[] { ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnSegment }, classification);
        }
        foreach (var segment in classification.segments.OrderBy(item => item.id, StringComparer.Ordinal))
        {
            var name = "V10_SEGMENT_" + segment.id;
            names.Add(name);
            AddMarker(metadata, name, Vector3.zero, new[] { segment.id }, classification);
        }
        return names;
    }

    private static void CreateRenderer(Transform parent, string bucket, Mesh mesh, Material material,
        IEnumerable<string> segmentIds, SegmentClassificationDocument classification)
    {
        if (mesh == null || material == null) throw new InvalidOperationException("V10 mesh/material is missing: " + bucket);
        var child = EnsureChild(parent, "V10_" + bucket);
        var filter = child.GetComponent<MeshFilter>();
        if (filter == null) filter = child.gameObject.AddComponent<MeshFilter>();
        filter.sharedMesh = mesh;
        var renderer = child.GetComponent<MeshRenderer>();
        if (renderer == null) renderer = child.gameObject.AddComponent<MeshRenderer>();
        renderer.enabled = true;
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = bucket == ChannelPlayKhufuV10InteriorMeshPipeline.InlayBucket ||
                                     bucket == ChannelPlayKhufuV10InteriorMeshPipeline.ShadowBucket
            ? ShadowCastingMode.Off
            : ShadowCastingMode.On;
        renderer.receiveShadows = bucket != ChannelPlayKhufuV10InteriorMeshPipeline.InlayBucket;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        ConfigureTag(child, segmentIds, classification);
    }

    private static void ConfigureTag(Transform target, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var ids = segmentIds.Distinct().OrderBy(item => item, StringComparer.Ordinal).ToArray();
        if (ids.Length == 0) throw new InvalidOperationException("V10 object has no segment classification: " + target.name);
        var records = ids.Select(id => classification.segments.Single(item => item.id == id)).ToArray();
        var truth = records.Select(item => item.truth).Distinct(StringComparer.Ordinal).Count() == 1 ? records[0].truth : "MIXED";
        var tag = target.GetComponent<KhufuV10SegmentTag>();
        if (tag == null) tag = target.gameObject.AddComponent<KhufuV10SegmentTag>();
        tag.Configure(ids, truth, records.All(item => item.factual_shape), records.Any(item => item.gameplay_scale));
    }

    private static void AddMarker(Transform parent, string name, Vector3 position, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var marker = EnsureChild(parent, name);
        marker.position = position;
        ConfigureTag(marker, segmentIds, classification);
    }

    private static void SetTransform(Transform target, ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec spec)
    {
        target.SetPositionAndRotation(spec.Position, spec.Rotation);
        target.localScale = spec.Scale;
    }

    private static Transform ResolveRequired(Transform map, string path)
    {
        var target = ResolvePath(map, path);
        if (target == null) throw new InvalidOperationException("V10 manifest target is missing: " + path);
        return target;
    }

    private static void ValidateAppliedTransitions(Transform map, ChannelPlayKhufuV10InteriorAudit.DisableManifest manifest)
    {
        var renderers = CollectManifestRenderers(map, manifest);
        var colliders = CollectManifestColliders(map, manifest);
        if (renderers.Count != manifest.ExpectedRendererTransitions || renderers.Any(item => item == null || item.enabled))
            throw new InvalidOperationException("V10 renderer transitions were not applied exactly.");
        if (colliders.Count != manifest.ExpectedColliderTransitions || colliders.Any(item => item == null || item.enabled))
            throw new InvalidOperationException("V10 collider transitions were not applied exactly.");
    }

    private static Transform Child(Transform parent, string name)
    {
        var child = new GameObject(name).transform;
        child.SetParent(parent, false);
        return child;
    }

    private static Transform EnsureChild(Transform parent, string name)
    {
        return parent.Find(name) ?? Child(parent, name);
    }

    private static void PruneChildren(Transform parent, IEnumerable<string> expectedNames)
    {
        var expected = new HashSet<string>(expectedNames, StringComparer.Ordinal);
        var stale = parent.Cast<Transform>().Where(item => !expected.Contains(item.name)).ToArray();
        foreach (var child in stale) UnityEngine.Object.DestroyImmediate(child.gameObject);
    }

    private static void EnsureAssetFolder(string path)
    {
        var segments = path.Split('/');
        var current = segments[0];
        for (var index = 1; index < segments.Length; index++)
        {
            var next = current + "/" + segments[index];
            if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(current, segments[index]);
            current = next;
        }
    }

    private static void SetColor(Material material, string property, Color value)
    {
        if (material.HasProperty(property)) material.SetColor(property, value);
    }

    private static void SetFloat(Material material, string property, float value)
    {
        if (material.HasProperty(property)) material.SetFloat(property, value);
    }

    private static bool Matches(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics,
        int renderers, int vertices, int triangles, int colliders)
    {
        return metrics.Renderers == renderers && metrics.Vertices == vertices &&
               metrics.Triangles == triangles && metrics.Colliders == colliders;
    }

    private static ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Subtract(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics total,
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics owned)
    {
        return new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics
        {
            Renderers = total.Renderers - owned.Renderers,
            Vertices = total.Vertices - owned.Vertices,
            Triangles = total.Triangles - owned.Triangles,
            Colliders = total.Colliders - owned.Colliders
        };
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    [Serializable]
    public sealed class SegmentClassificationDocument
    {
        public string schema = string.Empty;
        public string baseline_commit = string.Empty;
        public List<SegmentClassificationRecord> segments = new List<SegmentClassificationRecord>();
    }

    [Serializable]
    public sealed class SegmentClassificationRecord
    {
        public string id = string.Empty;
        public string truth = string.Empty;
        public bool factual_shape;
        public bool gameplay_scale;
    }
}

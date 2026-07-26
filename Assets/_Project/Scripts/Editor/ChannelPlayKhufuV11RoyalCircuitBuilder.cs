using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV11RoyalCircuitBuilder
{
    public const string ScenePath = ChannelPlayKhufuV10InteriorBuilder.ScenePath;
    public const string MapRootName = ChannelPlayKhufuV10InteriorBuilder.MapRootName;
    public const string RunRoot = "runs/khufu-v11-royal-circuit";
    public const string RootName = "Runtime_Khufu_V11_Royal_Circuit";
    public const string VisualRootName = "V11_Visuals";
    public const string PairRootName = "V11_Structural_Pairs";
    public const string CollisionRootName = "V11_Collision_Proxies";
    public const string MetadataRootName = "V11_Metadata";
    public const string MaterialRoot = "Assets/_Project/Materials/KhufuV11RoyalCircuit";
    public const string ClassificationPath = "docs/khufu-v11-royal-circuit/segment-classification.json";
    public const string PerformanceBudgetPath = "docs/khufu-v11-royal-circuit/performance-budget.json";

    public const string V10RootName = ChannelPlayKhufuV10InteriorBuilder.RootName;
    public const string V10LimestoneRendererPath =
        ChannelPlayKhufuV10InteriorBuilder.VisualRootName + "/V10_" +
        ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket;
    public const string V10GraniteRendererPath =
        ChannelPlayKhufuV10InteriorBuilder.VisualRootName + "/V10_" +
        ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket;
    public const string V10GreatStepBlockerPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary";

    public const int V10BaselineRenderers = 824;
    public const int V10BaselineVertices = 64046;
    public const int V10BaselineTriangles = 47048;
    public const int V10BaselineColliders = 534;
    internal static bool InjectFailureAfterClosedBindingsForValidation;

    [MenuItem("Channel Play/Khufu V11/Rebuild Royal Circuit")]
    public static void Rebuild()
    {
        var classification = LoadClassification();
        var budget = LoadPerformanceBudget();
        ValidateContracts(classification, budget);

        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(MapRootName);
        if (mapObject == null) throw new InvalidOperationException("Shared map root is missing.");
        var map = mapObject.transform;
        if (map.position != Vector3.zero || map.rotation != Quaternion.identity || map.lossyScale != Vector3.one)
            throw new InvalidOperationException("Shared map root transform drifted from identity.");

        var v10 = map.Find(V10RootName);
        if (v10 == null) throw new InvalidOperationException("Accepted V10 root is missing.");
        var previous = map.Find(RootName);
        ValidateTransitionInputs(v10);
        var transitionState = CaptureTransitionState(v10);
        var completed = false;
        try
        {
            ApplyV10ClosedBindingsInMemory(v10);
            if (InjectFailureAfterClosedBindingsForValidation)
                throw new InvalidOperationException("Injected V11 transition failure after closed bindings.");
            var mapBeforeBuild = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            var baseline = previous == null
                ? mapBeforeBuild
                : Subtract(mapBeforeBuild, ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(previous));
            if (!Matches(baseline, V10BaselineRenderers, V10BaselineVertices, V10BaselineTriangles,
                    V10BaselineColliders))
                throw new InvalidOperationException("Frozen V10 map baseline drifted: " + MetricsToken(baseline));

            var specs = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildSpecs();
            ValidateSpecs(specs, classification);
            var meshes = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildAndSaveMeshes(specs);
            var v10Variants = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildAndSaveV10OpenVariants();
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

            ConfigureTag(root, ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments, classification);
            ConfigureTag(visuals, ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments, classification);
            ConfigureTag(pairs, ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments, classification);
            ConfigureTag(proxies, ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments, classification);
            ConfigureTag(metadata, ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments, classification);

            foreach (var bucket in ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Buckets)
            {
                var segmentIds = specs.Where(item => item.Bucket == bucket).Select(item => item.SegmentId).Distinct();
                CreateRenderer(visuals, bucket, meshes[bucket], materials[bucket], segmentIds, classification);
            }
            PruneChildren(visuals,
                ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Buckets.Select(item => "V11_" + item));

            var pairNames = new List<string>();
            var proxyNames = new List<string>();
            foreach (var spec in specs.Where(item => item.Structural && item.Collider))
            {
                var pairName = "V11_PAIR_" + spec.SegmentId + "_" + spec.Name;
                var proxyName = "V11_PROXY_" + spec.SegmentId + "_" + spec.Name;
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

            ApplyV10OpenBindings(v10, v10Variants);
            ValidateAppliedBindings(v10);

            var rootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
            var expectedColliders = specs.Count(item => item.Structural && item.Collider);
            if (rootMetrics.Renderers != ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ExpectedRendererCount ||
                rootMetrics.Colliders != expectedColliders ||
                rootMetrics.Renderers > budget.root.renderers_max ||
                rootMetrics.Vertices > budget.root.vertices_max ||
                rootMetrics.Triangles > budget.root.triangles_max ||
                rootMetrics.Colliders > budget.root.colliders_max)
                throw new InvalidOperationException("V11 root exceeded budget: " + MetricsToken(rootMetrics));

            var finalMap = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            if (finalMap.Renderers > budget.map.renderers_max || finalMap.Colliders > budget.map.colliders_max)
                throw new InvalidOperationException("V11 full-map budget exceeded: " + MetricsToken(finalMap));

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            EditorSceneManager.MarkSceneDirty(scene);
            if (!EditorSceneManager.SaveScene(scene)) throw new InvalidOperationException("V11 scene save failed.");
            completed = true;
            Debug.Log("CHANNEL_PLAY_KHUFU_V11_BUILD result=built root=" + MetricsToken(rootMetrics) +
                      " map=" + MetricsToken(finalMap) + " v10Boundary=open");
        }
        finally
        {
            if (!completed) RollBackFailedBuild(v10, transitionState);
        }
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

    [MenuItem("Channel Play/Khufu V11/Restore Closed V10 Boundary")]
    public static void RestoreV10ClosedBindings()
    {
        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(MapRootName);
        if (mapObject == null) throw new InvalidOperationException("Shared map root is missing.");
        var v10 = mapObject.transform.Find(V10RootName);
        if (v10 == null) throw new InvalidOperationException("Accepted V10 root is missing.");

        SetMesh(v10, V10LimestoneRendererPath,
            AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedLimestonePath));
        SetMesh(v10, V10GraniteRendererPath,
            AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedGranitePath));
        var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        if (blocker == null) throw new InvalidOperationException("V10 Great Step blocker collider is missing.");
        blocker.enabled = true;
        EditorUtility.SetDirty(blocker);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
    }

    public static SegmentClassificationDocument LoadClassification()
    {
        if (!File.Exists(ClassificationPath))
            throw new FileNotFoundException("V11 classification is missing.", ClassificationPath);
        return JsonUtility.FromJson<SegmentClassificationDocument>(File.ReadAllText(ClassificationPath));
    }

    public static PerformanceBudgetDocument LoadPerformanceBudget()
    {
        if (!File.Exists(PerformanceBudgetPath))
            throw new FileNotFoundException("V11 performance budget is missing.", PerformanceBudgetPath);
        return JsonUtility.FromJson<PerformanceBudgetDocument>(File.ReadAllText(PerformanceBudgetPath));
    }

    private static void ValidateContracts(SegmentClassificationDocument classification,
        PerformanceBudgetDocument budget)
    {
        if (classification == null || classification.schema_version != 1 || classification.segments == null)
            throw new InvalidOperationException("V11 classification schema is invalid.");
        var expected = new HashSet<string>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments,
            StringComparer.Ordinal);
        var actual = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        if (!expected.SetEquals(actual)) throw new InvalidOperationException("V11 classification segment set drifted.");
        if (classification.segments.Any(item =>
                item.truth != "FACT" && item.truth != "FACT/HYBRID" &&
                item.truth != "FACT/DISPLAY" && item.truth != "HYBRID"))
            throw new InvalidOperationException("V11 classification contains an unknown truth class.");

        if (budget == null || budget.schema_version != 1 || budget.root == null || budget.map == null ||
            budget.root.renderers_max != ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ExpectedRendererCount ||
            budget.root.vertices_max <= 0 || budget.root.triangles_max <= 0 || budget.root.colliders_max <= 0 ||
            budget.map.renderers_max < V10BaselineRenderers || budget.map.colliders_max < V10BaselineColliders)
            throw new InvalidOperationException("V11 performance budget is invalid.");
    }

    private static void ValidateSpecs(IEnumerable<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec> specs,
        SegmentClassificationDocument classification)
    {
        var segments = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        var names = new HashSet<string>(StringComparer.Ordinal);
        foreach (var spec in specs)
        {
            if (!segments.Contains(spec.SegmentId)) throw new InvalidOperationException("Unclassified V11 spec: " + spec.Name);
            if (!ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Buckets.Contains(spec.Bucket))
                throw new InvalidOperationException("Unknown V11 mesh bucket: " + spec.Bucket);
            if (!names.Add(spec.Name)) throw new InvalidOperationException("Duplicate V11 spec name: " + spec.Name);
            if (spec.Scale.x <= 0f || spec.Scale.y <= 0f || spec.Scale.z <= 0f)
                throw new InvalidOperationException("Invalid V11 spec scale: " + spec.Name);
            if (spec.Collider && !spec.Structural)
                throw new InvalidOperationException("V11 collider spec is not structural: " + spec.Name);
        }
    }

    private static void ValidateTransitionInputs(Transform v10)
    {
        ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ValidateFrozenV10Sources();
        ValidateMeshInput(v10, V10LimestoneRendererPath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedLimestonePath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath);
        ValidateMeshInput(v10, V10GraniteRendererPath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedGranitePath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath);
        var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        if (blocker == null) throw new InvalidOperationException("V10 Great Step blocker collider is missing.");
    }

    private static void ValidateMeshInput(Transform root, string relativePath, string closedPath, string openPath)
    {
        var filter = ResolveRequired(root, relativePath).GetComponent<MeshFilter>();
        if (filter == null || filter.sharedMesh == null)
            throw new InvalidOperationException("V10 transition mesh filter is missing: " + relativePath);
        var actual = AssetDatabase.GetAssetPath(filter.sharedMesh);
        if (actual != closedPath && actual != openPath)
            throw new InvalidOperationException("V10 transition binding drifted: " + relativePath + " actual=" + actual);
    }

    private static void ApplyV10OpenBindings(Transform v10, IReadOnlyDictionary<string, Mesh> variants)
    {
        SetMesh(v10, V10LimestoneRendererPath,
            variants[ChannelPlayKhufuV11RoyalCircuitMeshPipeline.LimestoneBucket]);
        SetMesh(v10, V10GraniteRendererPath,
            variants[ChannelPlayKhufuV11RoyalCircuitMeshPipeline.GraniteBucket]);
        var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        blocker.enabled = false;
        EditorUtility.SetDirty(blocker);
    }

    private static void ApplyV10ClosedBindingsInMemory(Transform v10)
    {
        SetMesh(v10, V10LimestoneRendererPath,
            AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedLimestonePath));
        SetMesh(v10, V10GraniteRendererPath,
            AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedGranitePath));
        var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        if (blocker == null) throw new InvalidOperationException("V10 Great Step blocker collider is missing.");
        blocker.enabled = true;
        EditorUtility.SetDirty(blocker);
    }

    private static TransitionState CaptureTransitionState(Transform v10)
    {
        var limestone = ResolveRequired(v10, V10LimestoneRendererPath).GetComponent<MeshFilter>();
        var granite = ResolveRequired(v10, V10GraniteRendererPath).GetComponent<MeshFilter>();
        var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        if (limestone == null || granite == null || limestone.sharedMesh == null || granite.sharedMesh == null ||
            blocker == null)
            throw new InvalidOperationException("V10 transition state could not be captured.");
        return new TransitionState(limestone.sharedMesh, granite.sharedMesh, blocker.enabled);
    }

    private static void RollBackFailedBuild(Transform v10, TransitionState state)
    {
        try
        {
            SetMesh(v10, V10LimestoneRendererPath, state.Limestone);
            SetMesh(v10, V10GraniteRendererPath, state.Granite);
            var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
            if (blocker != null) blocker.enabled = state.BlockerEnabled;
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }
        catch (Exception rollbackException)
        {
            Debug.LogError("V11 failed-build rollback also failed: " + rollbackException);
        }
    }

    private static void ValidateAppliedBindings(Transform v10)
    {
        ExpectMeshPath(v10, V10LimestoneRendererPath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath);
        ExpectMeshPath(v10, V10GraniteRendererPath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath);
        var blocker = ResolveRequired(v10, V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        if (blocker == null || blocker.enabled)
            throw new InvalidOperationException("V10 Great Step blocker was not disabled.");
    }

    private static void ExpectMeshPath(Transform root, string relativePath, string expectedPath)
    {
        var filter = ResolveRequired(root, relativePath).GetComponent<MeshFilter>();
        var actual = filter == null || filter.sharedMesh == null ? string.Empty : AssetDatabase.GetAssetPath(filter.sharedMesh);
        if (actual != expectedPath)
            throw new InvalidOperationException("V10 open binding mismatch: " + relativePath + " actual=" + actual);
    }

    private static void SetMesh(Transform root, string relativePath, Mesh mesh)
    {
        if (mesh == null) throw new InvalidOperationException("V10 transition mesh asset is missing: " + relativePath);
        var filter = ResolveRequired(root, relativePath).GetComponent<MeshFilter>();
        if (filter == null) throw new InvalidOperationException("V10 transition mesh filter is missing: " + relativePath);
        filter.sharedMesh = mesh;
        EditorUtility.SetDirty(filter);
    }

    private static Dictionary<string, Material> BuildMaterials()
    {
        EnsureAssetFolder(MaterialRoot);
        var result = new Dictionary<string, Material>(StringComparer.Ordinal)
        {
            { ChannelPlayKhufuV11RoyalCircuitMeshPipeline.LimestoneBucket,
                CreateOrUpdateMaterial("V11_Royal_Limestone", "V10_Aged_Limestone",
                    new Color(0.58f, 0.49f, 0.36f, 1f), 0.02f, 0.24f) },
            { ChannelPlayKhufuV11RoyalCircuitMeshPipeline.GraniteBucket,
                CreateOrUpdateMaterial("V11_Royal_Red_Granite", "V10_Red_Granite",
                    new Color(0.38f, 0.105f, 0.075f, 1f), 0.08f, 0.38f) },
            { ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ShadowBucket,
                CreateOrUpdateMaterial("V11_Royal_Deep_Shadow", "V10_Deep_Shadow",
                    new Color(0.012f, 0.009f, 0.008f, 1f), 0f, 0.05f) },
            { ChannelPlayKhufuV11RoyalCircuitMeshPipeline.DisplayBucket,
                CreateOrUpdateMaterial("V11_Stacked_Display", "V10_Gallery_Detail",
                    new Color(0.34f, 0.27f, 0.20f, 1f), 0.03f, 0.22f) },
            { ChannelPlayKhufuV11RoyalCircuitMeshPipeline.InlayBucket,
                CreateOrUpdateMaterial("V11_Royal_Amber", "V10_Route_Amber",
                    new Color(1f, 0.34f, 0.035f, 1f), 0.06f, 0.4f,
                    new Color(2.4f, 0.48f, 0.025f, 1f)) }
        };
        AssetDatabase.SaveAssets();
        return result;
    }

    private static Material CreateOrUpdateMaterial(string assetName, string sourceName, Color color,
        float metallic, float smoothness, Color? emission = null)
    {
        var sourcePath = "Assets/_Project/Materials/KhufuV10Interior/" + sourceName + ".mat";
        var source = AssetDatabase.LoadAssetAtPath<Material>(sourcePath);
        if (source == null) throw new InvalidOperationException("V11 source material is missing: " + sourcePath);
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

    private static IReadOnlyCollection<string> AddMetadata(Transform metadata,
        SegmentClassificationDocument classification)
    {
        var markers = new Dictionary<string, Vector3>(StringComparer.Ordinal)
        {
            { "V11_Anchor_Great_Step_Open", KhufuV11RoyalRouteContract.GreatStepEntry },
            { "V11_Anchor_Royal_Threshold", KhufuV11RoyalRouteContract.RoyalThreshold },
            { "V11_Anchor_Antechamber", KhufuV11RoyalRouteContract.AntechamberCenter },
            { "V11_Anchor_Kings_Entrance", KhufuV11RoyalRouteContract.KingsEntrance },
            { "V11_Anchor_Kings_Chamber", KhufuV11RoyalRouteContract.KingsChamberCenter },
            { "V11_Anchor_Sarcophagus", KhufuV11RoyalRouteContract.SarcophagusCenter },
            { "V11_Anchor_Stacked_Display", KhufuV11RoyalRouteContract.StackedDisplayCenter() }
        };
        var names = new List<string>();
        foreach (var item in markers)
        {
            names.Add(item.Key);
            AddMarker(metadata, item.Key, item.Value, ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments,
                classification);
        }
        foreach (var segment in classification.segments.OrderBy(item => item.id, StringComparer.Ordinal))
        {
            var name = "V11_SEGMENT_" + segment.id;
            names.Add(name);
            AddMarker(metadata, name, Vector3.zero, new[] { segment.id }, classification);
        }
        return names;
    }

    private static void AddMarker(Transform parent, string name, Vector3 position, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var marker = EnsureChild(parent, name);
        marker.localPosition = position;
        marker.localRotation = Quaternion.identity;
        marker.localScale = Vector3.one;
        ConfigureTag(marker, segmentIds, classification);
    }

    private static void CreateRenderer(Transform parent, string bucket, Mesh mesh, Material material,
        IEnumerable<string> segmentIds, SegmentClassificationDocument classification)
    {
        if (mesh == null || material == null) throw new InvalidOperationException("V11 mesh/material is missing: " + bucket);
        var child = EnsureChild(parent, "V11_" + bucket);
        var filter = child.GetComponent<MeshFilter>();
        if (filter == null) filter = child.gameObject.AddComponent<MeshFilter>();
        filter.sharedMesh = mesh;
        var renderer = child.GetComponent<MeshRenderer>();
        if (renderer == null) renderer = child.gameObject.AddComponent<MeshRenderer>();
        renderer.enabled = true;
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = bucket == ChannelPlayKhufuV11RoyalCircuitMeshPipeline.InlayBucket ||
                                     bucket == ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ShadowBucket
            ? ShadowCastingMode.Off
            : ShadowCastingMode.On;
        renderer.receiveShadows = bucket != ChannelPlayKhufuV11RoyalCircuitMeshPipeline.InlayBucket;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        ConfigureTag(child, segmentIds, classification);
    }

    private static void ConfigureTag(Transform target, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var ids = segmentIds.Distinct().OrderBy(item => item, StringComparer.Ordinal).ToArray();
        if (ids.Length == 0) throw new InvalidOperationException("V11 object has no segment classification: " + target.name);
        var records = ids.Select(id => classification.segments.Single(item => item.id == id)).ToArray();
        var truth = records.Select(item => item.truth).Distinct(StringComparer.Ordinal).Count() == 1
            ? records[0].truth
            : "MIXED";
        var tag = target.GetComponent<KhufuV11SegmentTag>();
        if (tag == null) tag = target.gameObject.AddComponent<KhufuV11SegmentTag>();
        tag.Configure(ids, truth, records.All(item => item.factual_shape),
            records.Any(item => item.gameplay_scale));
    }

    private static void SetTransform(Transform target,
        ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec spec)
    {
        target.localPosition = spec.Position;
        target.localRotation = spec.Rotation;
        target.localScale = spec.Scale;
    }

    private static Transform ResolveRequired(Transform root, string relativePath)
    {
        var target = root.Find(relativePath);
        if (target == null) throw new InvalidOperationException("Required V11 dependency is missing: " + relativePath);
        return target;
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
        for (var index = parent.childCount - 1; index >= 0; index--)
        {
            var child = parent.GetChild(index);
            if (!expected.Contains(child.name)) UnityEngine.Object.DestroyImmediate(child.gameObject);
        }
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
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics left,
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics right)
    {
        return new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics
        {
            Renderers = left.Renderers - right.Renderers,
            Vertices = left.Vertices - right.Vertices,
            Triangles = left.Triangles - right.Triangles,
            Colliders = left.Colliders - right.Colliders
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
        public int schema_version;
        public List<SegmentClassificationRecord> segments = new List<SegmentClassificationRecord>();
    }

    private sealed class TransitionState
    {
        public readonly Mesh Limestone;
        public readonly Mesh Granite;
        public readonly bool BlockerEnabled;

        public TransitionState(Mesh limestone, Mesh granite, bool blockerEnabled)
        {
            Limestone = limestone;
            Granite = granite;
            BlockerEnabled = blockerEnabled;
        }
    }

    [Serializable]
    public sealed class SegmentClassificationRecord
    {
        public string id = string.Empty;
        public string truth = string.Empty;
        public bool factual_shape;
        public bool gameplay_scale;
        public string note = string.Empty;
    }

    [Serializable]
    public sealed class PerformanceBudgetDocument
    {
        public int schema_version;
        public RootBudget root = new RootBudget();
        public MapBudget map = new MapBudget();
        public CaptureBudget captures = new CaptureBudget();
    }

    [Serializable]
    public sealed class RootBudget
    {
        public int renderers_max;
        public int vertices_max;
        public int triangles_max;
        public int colliders_max;
    }

    [Serializable]
    public sealed class MapBudget
    {
        public int renderers_max;
        public int colliders_max;
    }

    [Serializable]
    public sealed class CaptureBudget
    {
        public int required;
        public int width;
        public int height;
    }
}

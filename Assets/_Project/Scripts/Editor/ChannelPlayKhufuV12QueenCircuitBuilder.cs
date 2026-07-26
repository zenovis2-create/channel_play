using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV12QueenCircuitBuilder
{
    public const string ScenePath = ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath;
    public const string MapRootName = ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName;
    public const string RunRoot = "runs/khufu-v12-queen-circuit";
    public const string RootName = "Runtime_Khufu_V12_Queen_Circuit";
    public const string VisualRootName = "V12_Visuals";
    public const string PairRootName = "V12_Structural_Pairs";
    public const string CollisionRootName = "V12_Collision_Proxies";
    public const string MetadataRootName = "V12_Metadata";
    public const string MaterialRoot = "Assets/_Project/Materials/KhufuV12QueenCircuit";
    public const string ClassificationPath = "docs/khufu-v12-queen-circuit/segment-classification.json";
    public const string PerformanceBudgetPath = "docs/khufu-v12-queen-circuit/performance-budget.json";
    public const string PrewriteAuditPath = RunRoot + "/prewrite-audit.json";
    public const string QueenGateProxyPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Ownership_Gate";
    public const string GalleryFloorProxyPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp";
    public const string HistoricServiceWestProxyPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Historic_Service_Mouth_Historic_Service_Mouth_West_Frame";
    public const string HistoricServiceEastProxyPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Historic_Service_Mouth_Historic_Service_Mouth_East_Frame";
    public const string HistoricServiceLintelProxyPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Historic_Service_Mouth_Historic_Service_Mouth_Lintel";

    public const int V11BaselineRenderers = 829;
    public const int V11BaselineVertices = 65918;
    public const int V11BaselineTriangles = 47984;
    public const int V11BaselineColliders = 567;
    public const string V11RestoredSignature =
        "9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9";
    public static readonly string[] HistoricServiceProxyPaths =
    {
        HistoricServiceWestProxyPath,
        HistoricServiceEastProxyPath,
        HistoricServiceLintelProxyPath
    };

    public static readonly string[] ThresholdProxyPaths =
    {
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Threshold_West_Post",
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Threshold_East_Post",
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Threshold_Lintel"
    };

    public static readonly string[] V4QueenTargets =
    {
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_Floor",
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_East",
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_West",
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_Roof",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Floor",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Back",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_East",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_West",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Roof_East",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Roof_West"
    };

    internal static bool InjectFailureAfterSuccessorBindingsForValidation;

    [MenuItem("Channel Play/Khufu V12/Rebuild Queen Circuit")]
    public static void Rebuild()
    {
        var classification = LoadClassification();
        var budget = LoadPerformanceBudget();
        ValidateContracts(classification, budget);

        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var map = Require(GameObject.Find(MapRootName)?.transform, "shared map root");
        if (map.position != Vector3.zero || map.rotation != Quaternion.identity || map.lossyScale != Vector3.one)
            throw new InvalidOperationException("Shared map root transform drifted from identity.");
        var v4 = Require(map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName), "V4 root");
        var v10 = Require(map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName), "V10 root");
        Require(map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.RootName), "V11 root");
        var previous = map.Find(RootName);

        ValidateTransitionInputs(v4, v10);
        var snapshot = new BuildSnapshot();
        var completed = false;
        try
        {
            ApplyV11Context(v4, v10);
            ValidateRestoredV11Context(map, previous);
            var mapWithPrevious = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            var baseline = previous == null
                ? mapWithPrevious
                : Subtract(mapWithPrevious, ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(previous));
            if (!Matches(baseline, V11BaselineRenderers, V11BaselineVertices, V11BaselineTriangles,
                    V11BaselineColliders))
                throw new InvalidOperationException("Frozen V11 map baseline drifted: " + MetricsToken(baseline));

            var specs = ChannelPlayKhufuV12QueenCircuitMeshPipeline.BuildSpecs();
            ValidateSpecs(specs, classification);
            var meshes = ChannelPlayKhufuV12QueenCircuitMeshPipeline.BuildAndSaveMeshes(specs);
            var variants = ChannelPlayKhufuV12QueenCircuitMeshPipeline.BuildAndSaveSuccessorVariants();
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

            ConfigureTag(root, ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments, classification);
            ConfigureTag(visuals, ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments, classification);
            ConfigureTag(pairs, ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments, classification);
            ConfigureTag(proxies, ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments, classification);
            ConfigureTag(metadata, ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments, classification);

            foreach (var bucket in ChannelPlayKhufuV12QueenCircuitMeshPipeline.Buckets)
            {
                var segmentIds = specs.Where(item => item.Bucket == bucket)
                    .Select(item => item.SegmentId).Distinct();
                CreateRenderer(visuals, bucket, meshes[bucket], materials[bucket], segmentIds, classification);
            }
            PruneChildren(visuals,
                ChannelPlayKhufuV12QueenCircuitMeshPipeline.Buckets.Select(item => "V12_" + item));

            var pairNames = new List<string>();
            var proxyNames = new List<string>();
            foreach (var spec in specs.Where(item => item.Structural && item.Collider))
            {
                var pairName = "V12_PAIR_" + spec.SegmentId + "_" + spec.Name;
                var proxyName = "V12_PROXY_" + spec.SegmentId + "_" + spec.Name;
                pairNames.Add(pairName);
                proxyNames.Add(proxyName);

                var pair = EnsureChild(pairs, pairName);
                SetTransform(pair, spec);
                ConfigureTag(pair, new[] { spec.SegmentId }, classification);

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

            ApplyV12Context(v4, v10, variants);
            ConfigureTransitionControl(metadata, v10);
            if (InjectFailureAfterSuccessorBindingsForValidation)
                throw new InvalidOperationException("Injected V12 failure after successor bindings.");
            ValidateAppliedTransitions(v4, v10);

            var rootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
            if (!Matches(rootMetrics, ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedRendererCount,
                    specs.Count * 24, specs.Count * 12,
                    ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedColliderCount) ||
                rootMetrics.Renderers != budget.root.renderers_exact ||
                rootMetrics.Vertices > budget.root.vertices_max ||
                rootMetrics.Triangles > budget.root.triangles_max ||
                rootMetrics.Colliders > budget.root.colliders_max)
                throw new InvalidOperationException("V12 root metric contract failed: " + MetricsToken(rootMetrics));

            var finalMap = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            var expectedMapVertices = V11BaselineVertices - 24 + rootMetrics.Vertices;
            var expectedMapTriangles = V11BaselineTriangles - 12 + rootMetrics.Triangles;
            var expectedMapColliders = V11BaselineColliders + rootMetrics.Colliders;
            if (!Matches(finalMap, budget.map.renderers_exact, expectedMapVertices, expectedMapTriangles,
                    expectedMapColliders) ||
                finalMap.Colliders > budget.map.colliders_max)
                throw new InvalidOperationException("V12 full-map metric contract failed: " + MetricsToken(finalMap));

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            EditorSceneManager.MarkSceneDirty(scene);
            if (!EditorSceneManager.SaveScene(scene)) throw new InvalidOperationException("V12 scene save failed.");
            completed = true;
            Debug.Log("CHANNEL_PLAY_KHUFU_V12_BUILD result=built root=" + MetricsToken(rootMetrics) +
                      " map=" + MetricsToken(finalMap) + " queenBoundary=open");
        }
        finally
        {
            if (!completed) snapshot.Restore();
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

    public static SegmentClassificationDocument LoadClassification()
    {
        if (!File.Exists(ClassificationPath))
            throw new FileNotFoundException("V12 classification is missing.", ClassificationPath);
        return JsonUtility.FromJson<SegmentClassificationDocument>(File.ReadAllText(ClassificationPath));
    }

    public static PerformanceBudgetDocument LoadPerformanceBudget()
    {
        if (!File.Exists(PerformanceBudgetPath))
            throw new FileNotFoundException("V12 performance budget is missing.", PerformanceBudgetPath);
        return JsonUtility.FromJson<PerformanceBudgetDocument>(File.ReadAllText(PerformanceBudgetPath));
    }

    public static void ApplyV11Context(Transform v4, Transform v10)
    {
        SetMesh(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath,
            AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath));
        SetMesh(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath,
            AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath));
        SetCollider(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath, false);
        SetCollider(v10, QueenGateProxyPath, true);
        SetCollider(v10, GalleryFloorProxyPath, true);
        foreach (var path in HistoricServiceProxyPaths) SetCollider(v10, path, true);
        SetV4QueenComponents(v4, true);
    }

    public static void ApplyV12Context(Transform v4, Transform v10,
        IReadOnlyDictionary<string, Mesh> variants = null)
    {
        var limestone = variants == null
            ? AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenLimestonePath)
            : variants[ChannelPlayKhufuV12QueenCircuitMeshPipeline.LimestoneBucket];
        var granite = variants == null
            ? AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenGranitePath)
            : variants[ChannelPlayKhufuV12QueenCircuitMeshPipeline.ShadowBucket];
        SetMesh(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath, limestone);
        SetMesh(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath, granite);
        SetCollider(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath, false);
        SetCollider(v10, QueenGateProxyPath, false);
        SetCollider(v10, GalleryFloorProxyPath, false);
        foreach (var path in HistoricServiceProxyPaths) SetCollider(v10, path, false);
        SetV4QueenComponents(v4, false);
    }

    private static void ValidateContracts(SegmentClassificationDocument classification,
        PerformanceBudgetDocument budget)
    {
        if (classification == null || classification.schema != "khufu-v12-queen-circuit-segments-v1" ||
            classification.segments == null)
            throw new InvalidOperationException("V12 classification schema is invalid.");
        var expected = new HashSet<string>(ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments,
            StringComparer.Ordinal);
        var actual = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        if (!expected.SetEquals(actual) || classification.segments.Count != expected.Count)
            throw new InvalidOperationException("V12 classification segment inventory drifted.");
        if (classification.segments.Any(item =>
                item.truth != "FACT" && item.truth != "FACT_HYBRID" && item.truth != "HYBRID"))
            throw new InvalidOperationException("V12 classification contains an unknown truth class.");

        if (budget == null || budget.schema != "khufu-v12-queen-circuit-budget-v1" ||
            budget.root == null || budget.map == null || budget.captures == null ||
            budget.root.renderers_exact != ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedRendererCount ||
            budget.root.colliders_exact != ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedColliderCount ||
            budget.root.colliders_max < ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedColliderCount ||
            budget.map.renderers_exact != V11BaselineRenderers +
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedRendererCount ||
            budget.map.colliders_exact != V11BaselineColliders +
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedColliderCount ||
            budget.map.colliders_max < V11BaselineColliders +
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedColliderCount ||
            budget.captures.required != 6 || budget.captures.width != 1600 || budget.captures.height != 1000)
            throw new InvalidOperationException("V12 performance budget is invalid.");
    }

    private static void ValidateSpecs(IEnumerable<ChannelPlayKhufuV12QueenCircuitMeshPipeline.BoxSpec> specs,
        SegmentClassificationDocument classification)
    {
        var segments = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        var names = new HashSet<string>(StringComparer.Ordinal);
        foreach (var spec in specs)
        {
            if (!segments.Contains(spec.SegmentId))
                throw new InvalidOperationException("Unclassified V12 spec: " + spec.Name);
            if (!ChannelPlayKhufuV12QueenCircuitMeshPipeline.Buckets.Contains(spec.Bucket))
                throw new InvalidOperationException("Unknown V12 mesh bucket: " + spec.Bucket);
            if (!names.Add(spec.Name)) throw new InvalidOperationException("Duplicate V12 spec name: " + spec.Name);
            if (spec.Name.Contains("Queens_Shaft"))
                throw new InvalidOperationException("V12 spec contains a forbidden legacy shaft token: " + spec.Name);
            if (spec.Scale.x <= 0f || spec.Scale.y <= 0f || spec.Scale.z <= 0f)
                throw new InvalidOperationException("Invalid V12 spec scale: " + spec.Name);
            if (spec.Collider && !spec.Structural)
                throw new InvalidOperationException("V12 collider spec is not structural: " + spec.Name);
        }
        if (specs.Count(item => item.Structural && item.Collider) !=
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedColliderCount)
            throw new InvalidOperationException("V12 structural collider inventory drifted.");
    }

    private static void ValidateTransitionInputs(Transform v4, Transform v10)
    {
        ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ValidateV10TransitionAssets();
        var limestone = MeshPath(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath);
        var granite = MeshPath(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath);
        var v11 = limestone == ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath &&
                  granite == ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath;
        var v12 = limestone == ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenLimestonePath &&
                  granite == ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenGranitePath;
        if (!v11 && !v12)
            throw new InvalidOperationException("V12 transition input must be a complete V11-open or V12-open pair.");
        var greatStep = Collider(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath);
        var queenGate = Collider(v10, QueenGateProxyPath);
        var galleryFloor = Collider(v10, GalleryFloorProxyPath);
        var historicServiceStates = HistoricServiceProxyPaths
            .Select(path => Collider(v10, path).enabled).ToArray();
        if (greatStep.enabled || queenGate.enabled != v11 ||
            galleryFloor.enabled != v11 ||
            historicServiceStates.Any(enabled => enabled != v11))
            throw new InvalidOperationException("V10 proxy state does not match the accepted V11/V12 binding pair.");
        var states = V4QueenTargets.Select(path => ComponentState(v4, path)).ToArray();
        if (states.Any(item => !item.ActiveSelf) ||
            (v11 && states.Any(item => !item.RendererEnabled || !item.ColliderEnabled)) ||
            (v12 && states.Any(item => item.RendererEnabled || item.ColliderEnabled)))
            throw new InvalidOperationException("V4 Queen component state does not match the accepted input context.");
        ValidateFrozenV4Transforms(v4);
        ValidateThresholdProxies(v10);
        ValidateInheritedV4State(v4);
    }

    private static void ValidateAppliedTransitions(Transform v4, Transform v10)
    {
        if (MeshPath(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath) !=
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenLimestonePath ||
            MeshPath(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath) !=
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenGranitePath ||
            Collider(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath).enabled ||
            Collider(v10, QueenGateProxyPath).enabled ||
            Collider(v10, GalleryFloorProxyPath).enabled ||
            HistoricServiceProxyPaths.Any(path => Collider(v10, path).enabled))
            throw new InvalidOperationException("V12 successor binding/proxy state was not applied.");
        if (V4QueenTargets.Select(path => ComponentState(v4, path))
            .Any(item => !item.ActiveSelf || item.RendererEnabled || item.ColliderEnabled))
            throw new InvalidOperationException("V4 Queen blockout was not disabled component-by-component.");
        ValidateFrozenV4Transforms(v4);
        ValidateThresholdProxies(v10);
        ValidateInheritedV4State(v4);
        ChannelPlayKhufuV12QueenCircuitMeshPipeline.ValidateSuccessorAssets();
    }

    private static void ValidateInheritedV4State(Transform v4)
    {
        var marker = Require(v4.Find("V4_Gameplay_Route/V4_Route_Queens_Chamber"), "V4 Queen marker");
        var markerRenderer = marker.GetComponent<Renderer>();
        var glowRenderer = Require(v4.Find("V4_Gameplay_Route/V4_Glow_Queens"), "V4 Queen glow")
            .GetComponent<Renderer>();
        var light = Require(v4.Find("V4_Lighting/V4_Light_Queens"), "V4 Queen light").GetComponent<Light>();
        if (marker.position != KhufuV10RouteContract.QueensChamber || markerRenderer == null ||
            markerRenderer.enabled || glowRenderer == null || glowRenderer.enabled || light == null || !light.enabled)
            throw new InvalidOperationException("Inherited V4 marker/glow/light contract drifted.");
    }

    private static void ConfigureTransitionControl(Transform metadata, Transform v10)
    {
        var filter = Require(v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath),
            "V10 granite renderer").GetComponent<MeshFilter>();
        var gate = Collider(v10, QueenGateProxyPath);
        var predecessor = AssetDatabase.LoadAssetAtPath<Mesh>(
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath);
        var successor = AssetDatabase.LoadAssetAtPath<Mesh>(
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenGranitePath);
        if (filter == null || predecessor == null || successor == null)
            throw new InvalidOperationException("V12 runtime transition-control assets are missing.");
        var control = metadata.GetComponent<KhufuV12TransitionControl>();
        if (control == null) control = metadata.gameObject.AddComponent<KhufuV12TransitionControl>();
        control.Configure(predecessor, successor, filter, gate);
        EditorUtility.SetDirty(control);
    }

    private static void ValidateFrozenV4Transforms(Transform v4)
    {
        if (!File.Exists(PrewriteAuditPath))
            throw new FileNotFoundException("V12 prewrite audit is missing.", PrewriteAuditPath);
        var audit = JsonUtility.FromJson<PrewriteAuditDocument>(File.ReadAllText(PrewriteAuditPath));
        if (audit == null || audit.schema != "khufu-v12-prewrite-audit-v1" ||
            audit.v4_queen_targets == null || audit.v4_queen_targets.Count != V4QueenTargets.Length)
            throw new InvalidOperationException("V12 prewrite transform inventory is invalid.");
        foreach (var path in V4QueenTargets)
        {
            var frozen = audit.v4_queen_targets.SingleOrDefault(item => item.path == path);
            var target = Require(v4.Find(path), path);
            var collider = target.GetComponent<BoxCollider>();
            if (frozen == null ||
                Vector3.Distance(target.localPosition, frozen.local_position) > 0.001f ||
                Quaternion.Angle(target.localRotation, frozen.local_rotation) > 0.01f ||
                Vector3.Distance(target.localScale, frozen.local_scale) > 0.001f ||
                collider == null || collider.isTrigger != frozen.is_trigger ||
                !target.gameObject.activeSelf || !target.gameObject.activeInHierarchy)
                throw new InvalidOperationException("Frozen V4 Queen transform/trigger state drifted: " + path);
        }
    }

    private static void ValidateThresholdProxies(Transform v10)
    {
        foreach (var path in ThresholdProxyPaths)
        {
            var target = Require(v10.Find(path), path);
            var colliders = target.GetComponents<BoxCollider>();
            if (!target.gameObject.activeSelf || !target.gameObject.activeInHierarchy ||
                colliders.Length != 1 || !colliders[0].enabled || colliders[0].isTrigger)
                throw new InvalidOperationException("Inherited Queen threshold proxy drifted: " + path);
        }
    }

    private static void ValidateRestoredV11Context(Transform map, Transform previous)
    {
        var parent = previous == null ? null : previous.parent;
        var sibling = previous == null ? -1 : previous.GetSiblingIndex();
        var localPosition = previous == null ? Vector3.zero : previous.localPosition;
        var localRotation = previous == null ? Quaternion.identity : previous.localRotation;
        var localScale = previous == null ? Vector3.one : previous.localScale;
        try
        {
            if (previous != null) previous.SetParent(null, true);
            var method = typeof(ChannelPlayKhufuV11RoyalCircuitValidator).GetMethod(
                "ValidateScene", BindingFlags.NonPublic | BindingFlags.Static);
            var validation = method?.Invoke(null, new object[] { false });
            if (validation == null) throw new InvalidOperationException("V11 restored-context result is missing.");
            var type = validation.GetType();
            var failures = type.GetField("Failures")?.GetValue(validation) as System.Collections.ICollection;
            var signature = Convert.ToString(type.GetField("Signature")?.GetValue(validation));
            if (failures == null || failures.Count != 0 || signature != V11RestoredSignature)
                throw new InvalidOperationException("V11 restored-context validator/signature drifted: " + signature);
            var metrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            if (!Matches(metrics, V11BaselineRenderers, V11BaselineVertices, V11BaselineTriangles,
                    V11BaselineColliders))
                throw new InvalidOperationException("V11 restored-context metrics drifted: " + MetricsToken(metrics));
        }
        finally
        {
            if (previous != null)
            {
                previous.SetParent(parent, false);
                previous.SetSiblingIndex(sibling);
                previous.localPosition = localPosition;
                previous.localRotation = localRotation;
                previous.localScale = localScale;
            }
        }
    }

    private static Dictionary<string, Material> BuildMaterials()
    {
        EnsureAssetFolder(MaterialRoot);
        var result = new Dictionary<string, Material>(StringComparer.Ordinal)
        {
            { ChannelPlayKhufuV12QueenCircuitMeshPipeline.LimestoneBucket,
                CreateOrUpdateMaterial("V12_Queen_Limestone", "V10_Aged_Limestone",
                    new Color(0.59f, 0.50f, 0.37f, 1f), 0.02f, 0.23f) },
            { ChannelPlayKhufuV12QueenCircuitMeshPipeline.DetailBucket,
                CreateOrUpdateMaterial("V12_Queen_Detail", "V10_Gallery_Detail",
                    new Color(0.42f, 0.34f, 0.24f, 1f), 0.02f, 0.19f) },
            { ChannelPlayKhufuV12QueenCircuitMeshPipeline.ShadowBucket,
                CreateOrUpdateMaterial("V12_Queen_Shadow", "V10_Deep_Shadow",
                    new Color(0.009f, 0.007f, 0.006f, 1f), 0f, 0.03f) },
            { ChannelPlayKhufuV12QueenCircuitMeshPipeline.AccentBucket,
                CreateOrUpdateMaterial("V12_Queen_Inspection", "V10_Gallery_Detail",
                    new Color(0.52f, 0.36f, 0.17f, 1f), 0.03f, 0.29f) },
            { ChannelPlayKhufuV12QueenCircuitMeshPipeline.InlayBucket,
                CreateOrUpdateMaterial("V12_Queen_Route_Amber", "V10_Route_Amber",
                    new Color(1f, 0.31f, 0.025f, 1f), 0.05f, 0.38f,
                    new Color(2.1f, 0.39f, 0.018f, 1f)) }
        };
        AssetDatabase.SaveAssets();
        return result;
    }

    private static Material CreateOrUpdateMaterial(string assetName, string sourceName, Color color,
        float metallic, float smoothness, Color? emission = null)
    {
        var sourcePath = "Assets/_Project/Materials/KhufuV10Interior/" + sourceName + ".mat";
        var source = AssetDatabase.LoadAssetAtPath<Material>(sourcePath);
        if (source == null) throw new InvalidOperationException("V12 source material is missing: " + sourcePath);
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
            { "V12_Anchor_Gallery_Foot", KhufuV12QueenRouteContract.GalleryFoot },
            { "V12_Anchor_Queen_Threshold", KhufuV12QueenRouteContract.ThresholdCenter },
            { "V12_Anchor_Passage_Turn", KhufuV12QueenRouteContract.PassageTurn },
            { "V12_Anchor_Chamber_Door", KhufuV12QueenRouteContract.ChamberDoor },
            { "V12_Anchor_Queens_Chamber", KhufuV12QueenRouteContract.ChamberCenter },
            { "V12_Anchor_East_Wall_Niche", KhufuV12QueenRouteContract.NicheStop }
        };
        var names = new List<string>();
        foreach (var item in markers)
        {
            names.Add(item.Key);
            AddMarker(metadata, item.Key, item.Value, ChannelPlayKhufuV12QueenCircuitMeshPipeline.Segments,
                classification);
        }
        foreach (var segment in classification.segments.OrderBy(item => item.id, StringComparer.Ordinal))
        {
            var name = "V12_SEGMENT_" + segment.id;
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
        if (mesh == null || material == null)
            throw new InvalidOperationException("V12 mesh/material is missing: " + bucket);
        var child = EnsureChild(parent, "V12_" + bucket);
        var filter = child.GetComponent<MeshFilter>();
        if (filter == null) filter = child.gameObject.AddComponent<MeshFilter>();
        filter.sharedMesh = mesh;
        var renderer = child.GetComponent<MeshRenderer>();
        if (renderer == null) renderer = child.gameObject.AddComponent<MeshRenderer>();
        renderer.enabled = true;
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode =
            bucket == ChannelPlayKhufuV12QueenCircuitMeshPipeline.InlayBucket ||
            bucket == ChannelPlayKhufuV12QueenCircuitMeshPipeline.ShadowBucket
                ? ShadowCastingMode.Off
                : ShadowCastingMode.On;
        renderer.receiveShadows = bucket != ChannelPlayKhufuV12QueenCircuitMeshPipeline.InlayBucket;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        ConfigureTag(child, segmentIds, classification);
    }

    private static void ConfigureTag(Transform target, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var ids = segmentIds.Distinct().OrderBy(item => item, StringComparer.Ordinal).ToArray();
        if (ids.Length == 0) throw new InvalidOperationException("V12 object has no classification: " + target.name);
        var records = ids.Select(id => classification.segments.Single(item => item.id == id)).ToArray();
        var truth = records.Select(item => item.truth).Distinct(StringComparer.Ordinal).Count() == 1
            ? records[0].truth
            : "MIXED";
        var tag = target.GetComponent<KhufuV12SegmentTag>();
        if (tag == null) tag = target.gameObject.AddComponent<KhufuV12SegmentTag>();
        tag.Configure(ids, truth, records.All(item => item.factual_shape),
            records.Any(item => item.gameplay_scale));
    }

    private static void SetV4QueenComponents(Transform v4, bool enabled)
    {
        foreach (var path in V4QueenTargets)
        {
            var target = Require(v4.Find(path), path);
            var renderer = target.GetComponent<Renderer>();
            var collider = target.GetComponent<BoxCollider>();
            if (renderer == null || collider == null)
                throw new InvalidOperationException("V4 Queen renderer/collider pair is missing: " + path);
            renderer.enabled = enabled;
            collider.enabled = enabled;
            EditorUtility.SetDirty(renderer);
            EditorUtility.SetDirty(collider);
        }
    }

    private static ComponentRecord ComponentState(Transform v4, string path)
    {
        var target = Require(v4.Find(path), path);
        var renderer = target.GetComponent<Renderer>();
        var collider = target.GetComponent<BoxCollider>();
        if (renderer == null || collider == null)
            throw new InvalidOperationException("V4 Queen renderer/collider pair is missing: " + path);
        return new ComponentRecord(target.gameObject.activeSelf, renderer.enabled, collider.enabled);
    }

    private static string MeshPath(Transform root, string relativePath)
    {
        var filter = Require(root.Find(relativePath), relativePath).GetComponent<MeshFilter>();
        if (filter == null || filter.sharedMesh == null)
            throw new InvalidOperationException("Transition mesh binding is missing: " + relativePath);
        return AssetDatabase.GetAssetPath(filter.sharedMesh);
    }

    private static void SetMesh(Transform root, string relativePath, Mesh mesh)
    {
        if (mesh == null) throw new InvalidOperationException("Transition mesh asset is missing: " + relativePath);
        var filter = Require(root.Find(relativePath), relativePath).GetComponent<MeshFilter>();
        if (filter == null) throw new InvalidOperationException("Transition mesh filter is missing: " + relativePath);
        filter.sharedMesh = mesh;
        EditorUtility.SetDirty(filter);
    }

    private static BoxCollider Collider(Transform root, string relativePath)
    {
        var collider = Require(root.Find(relativePath), relativePath).GetComponent<BoxCollider>();
        if (collider == null) throw new InvalidOperationException("Transition collider is missing: " + relativePath);
        return collider;
    }

    private static void SetCollider(Transform root, string relativePath, bool enabled)
    {
        var collider = Collider(root, relativePath);
        collider.enabled = enabled;
        EditorUtility.SetDirty(collider);
    }

    private static void SetTransform(Transform target,
        ChannelPlayKhufuV12QueenCircuitMeshPipeline.BoxSpec spec)
    {
        target.localPosition = spec.Position;
        target.localRotation = spec.Rotation;
        target.localScale = spec.Scale;
    }

    private static Transform Require(Transform target, string label)
    {
        if (target == null) throw new InvalidOperationException("Required V12 dependency is missing: " + label);
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
        var parts = path.Split('/');
        var current = parts[0];
        for (var index = 1; index < parts.Length; index++)
        {
            var next = current + "/" + parts[index];
            if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(current, parts[index]);
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
        public string schema = string.Empty;
        public List<SegmentClassificationRecord> segments = new List<SegmentClassificationRecord>();
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
        public string schema = string.Empty;
        public RootBudget root = new RootBudget();
        public MapBudget map = new MapBudget();
        public CaptureBudget captures = new CaptureBudget();
    }

    [Serializable]
    public sealed class RootBudget
    {
        public int renderers_exact;
        public int colliders_exact;
        public int colliders_max;
        public int vertices_max;
        public int triangles_max;
    }

    [Serializable]
    public sealed class MapBudget
    {
        public int renderers_exact;
        public int colliders_exact;
        public int colliders_max;
    }

    [Serializable]
    public sealed class CaptureBudget
    {
        public int required;
        public int width;
        public int height;
    }

    private readonly struct ComponentRecord
    {
        public readonly bool ActiveSelf;
        public readonly bool RendererEnabled;
        public readonly bool ColliderEnabled;

        public ComponentRecord(bool activeSelf, bool rendererEnabled, bool colliderEnabled)
        {
            ActiveSelf = activeSelf;
            RendererEnabled = rendererEnabled;
            ColliderEnabled = colliderEnabled;
        }
    }

    [Serializable]
    private sealed class PrewriteAuditDocument
    {
        public string schema = string.Empty;
        public List<FrozenTargetRecord> v4_queen_targets = new List<FrozenTargetRecord>();
    }

    [Serializable]
    private sealed class FrozenTargetRecord
    {
        public string path = string.Empty;
        public bool is_trigger;
        public Vector3 local_position;
        public Quaternion local_rotation;
        public Vector3 local_scale;
    }

    private sealed class BuildSnapshot
    {
        private readonly byte[] sceneBytes = File.ReadAllBytes(ScenePath);
        private readonly DirectorySnapshot generated =
            new DirectorySnapshot(ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeneratedRoot);
        private readonly DirectorySnapshot materials = new DirectorySnapshot(MaterialRoot);

        public void Restore()
        {
            File.WriteAllBytes(ScenePath, sceneBytes);
            generated.Restore();
            materials.Restore();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            if (!File.ReadAllBytes(ScenePath).SequenceEqual(sceneBytes) ||
                !generated.MatchesSnapshot() || !materials.MatchesSnapshot())
                throw new InvalidOperationException("V12 failed-build rollback verification failed.");
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }
    }

    private sealed class DirectorySnapshot
    {
        private readonly string path;
        private readonly Dictionary<string, byte[]> files = new Dictionary<string, byte[]>(StringComparer.Ordinal);
        private readonly bool existed;
        private readonly bool metaExisted;
        private readonly byte[] metaBytes;

        public DirectorySnapshot(string assetPath)
        {
            path = assetPath.Replace('/', Path.DirectorySeparatorChar);
            existed = Directory.Exists(path);
            metaExisted = File.Exists(path + ".meta");
            metaBytes = metaExisted ? File.ReadAllBytes(path + ".meta") : Array.Empty<byte>();
            if (!existed) return;
            foreach (var file in Directory.GetFiles(path, "*", SearchOption.AllDirectories))
                files[file] = File.ReadAllBytes(file);
        }

        public void Restore()
        {
            if (Directory.Exists(path))
            {
                foreach (var file in Directory.GetFiles(path, "*", SearchOption.AllDirectories))
                    File.Delete(file);
            }
            if (!existed)
            {
                if (Directory.Exists(path)) Directory.Delete(path, true);
            }
            else
            {
                Directory.CreateDirectory(path);
                foreach (var item in files)
                {
                    var parent = Path.GetDirectoryName(item.Key);
                    if (!string.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
                    File.WriteAllBytes(item.Key, item.Value);
                }
            }
            if (metaExisted) File.WriteAllBytes(path + ".meta", metaBytes);
            else if (File.Exists(path + ".meta")) File.Delete(path + ".meta");
        }

        public bool MatchesSnapshot()
        {
            if (Directory.Exists(path) != existed || File.Exists(path + ".meta") != metaExisted) return false;
            if (metaExisted && !File.ReadAllBytes(path + ".meta").SequenceEqual(metaBytes)) return false;
            if (!existed) return true;
            var current = Directory.GetFiles(path, "*", SearchOption.AllDirectories);
            return current.Length == files.Count &&
                   current.All(file => files.TryGetValue(file, out var bytes) &&
                                       File.ReadAllBytes(file).SequenceEqual(bytes));
        }
    }
}

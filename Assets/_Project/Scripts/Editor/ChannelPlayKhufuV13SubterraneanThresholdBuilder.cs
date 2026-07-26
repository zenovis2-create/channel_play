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

public static class ChannelPlayKhufuV13SubterraneanThresholdBuilder
{
    public const string ScenePath = ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath;
    public const string MapRootName = ChannelPlayKhufuV12QueenCircuitBuilder.MapRootName;
    public const string RunRoot = "runs/khufu-v13-subterranean-threshold";
    public const string RootName = "Runtime_Khufu_V13_Subterranean_Threshold";
    public const string VisualRootName = "V13_Visuals";
    public const string PairRootName = "V13_Structural_Pairs";
    public const string CollisionRootName = "V13_Collision_Proxies";
    public const string MetadataRootName = "V13_Metadata";
    public const string MaterialRoot =
        "Assets/_Project/Materials/KhufuV13SubterraneanThreshold";
    public const string ClassificationPath =
        "docs/khufu-v13-subterranean-threshold/segment-classification.json";
    public const string PerformanceBudgetPath =
        "docs/khufu-v13-subterranean-threshold/performance-budget.json";
    public const string PrewriteAuditPath = RunRoot + "/prewrite-audit.json";
    public const string V12BaselineStaticSignature =
        "6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd";
    public const int V12BaselineRenderers = 834;
    public const int V12BaselineVertices = 67070;
    public const int V12BaselineTriangles = 48560;
    public const int V12BaselineColliders = 589;
    public const int ExpectedRootVertices = 792;
    public const int ExpectedRootTriangles = 396;
    public const int ExpectedMapRenderers = 839;
    public const int ExpectedMapVertices = 67862;
    public const int ExpectedMapTriangles = 48956;
    public const int ExpectedMapColliders = 609;

    public const string RendererOnlyPitPath =
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Chamber/" +
        "V4_Subterranean_Unfinished_Pit";
    public const string V10BranchAnchorPath =
        "V10_Metadata/V10_Anchor_Ascending_Branch";
    public const string V4SubterraneanLightPath =
        "V4_Lighting/V4_Light_Subterranean";

    public static readonly string[] V4SubterraneanTargets =
    {
        "V4_Embedded_Interior_Architecture/V4_Descending_Bedrock_Floor",
        "V4_Embedded_Interior_Architecture/V4_Descending_Bedrock_East",
        "V4_Embedded_Interior_Architecture/V4_Descending_Bedrock_West",
        "V4_Embedded_Interior_Architecture/V4_Descending_Bedrock_Roof",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Level_Floor",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Level_East",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Level_West",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Level_Roof",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Chamber/V4_Subterranean_Floor",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Chamber/V4_Subterranean_Back",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Chamber/V4_Subterranean_West",
        "V4_Embedded_Interior_Architecture/V4_Subterranean_Chamber/V4_Subterranean_East",
        RendererOnlyPitPath
    };

    public static readonly string[] PreservedV4RendererPaths =
    {
        "V4_Gameplay_Route/V4_Route_Branch",
        "V4_Gameplay_Route/V4_Route_Subterranean_Approach",
        "V4_Gameplay_Route/V4_Route_Subterranean_Chamber",
        "V4_Gameplay_Route/V4_Glow_Descending",
        "V4_Gameplay_Route/V4_Glow_Subterranean"
    };

    internal static bool InjectFailureAfterSuccessorBindingsForValidation;

    [MenuItem("Channel Play/Khufu V13/Rebuild Subterranean Threshold")]
    public static void Rebuild()
    {
        var classification = LoadClassification();
        var budget = LoadPerformanceBudget();
        var audit = LoadPrewriteAudit();
        ValidateContracts(classification, budget, audit);

        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var map = Require(GameObject.Find(MapRootName)?.transform, "shared map root");
        if (map.position != Vector3.zero || map.rotation != Quaternion.identity ||
            map.lossyScale != Vector3.one)
            throw new InvalidOperationException("Shared map root transform drifted from identity.");
        var v4 = Require(map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName), "V4 root");
        var v10 = Require(map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName), "V10 root");
        Require(map.Find(ChannelPlayKhufuV12QueenCircuitBuilder.RootName), "V12 root");
        var previous = map.Find(RootName);

        ValidateInputContext(v4, v10, previous, audit);
        var snapshot = new BuildSnapshot();
        var completed = false;
        try
        {
            ValidateV12BaselineContext(map, v4, previous);
            var mapWithPrevious = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            var baseline = previous == null
                ? mapWithPrevious
                : Subtract(mapWithPrevious,
                    ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(previous));
            if (!Matches(baseline, V12BaselineRenderers, V12BaselineVertices,
                    V12BaselineTriangles, V12BaselineColliders))
                throw new InvalidOperationException(
                    "Frozen V12 map baseline drifted: " + MetricsToken(baseline));

            var specs = ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BuildSpecs();
            ValidateSpecs(specs, classification);
            var meshes = BuildAndSaveMeshes(specs);
            var materials = BuildMaterials();

            var root = previous ?? Child(map, RootName);
            root.SetParent(map, false);
            root.localPosition = Vector3.zero;
            root.localRotation = Quaternion.identity;
            root.localScale = Vector3.one;
            root.gameObject.SetActive(true);
            var visuals = EnsureChild(root, VisualRootName);
            var pairs = EnsureChild(root, PairRootName);
            var proxies = EnsureChild(root, CollisionRootName);
            var metadata = EnsureChild(root, MetadataRootName);
            PruneChildren(root,
                new[] { VisualRootName, PairRootName, CollisionRootName, MetadataRootName });

            ConfigureTag(root, ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
                classification);
            ConfigureTag(visuals, ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
                classification);
            ConfigureTag(pairs, ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
                classification);
            ConfigureTag(proxies, ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
                classification);
            ConfigureTag(metadata, ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
                classification);

            foreach (var bucket in ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Buckets)
            {
                var segmentIds = specs.Where(item => item.Bucket == bucket)
                    .Select(item => item.SegmentId).Distinct();
                CreateRenderer(visuals, bucket, meshes[bucket], materials[bucket], segmentIds,
                    classification);
            }
            PruneChildren(visuals,
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Buckets
                    .Select(item => "V13_" + item));

            var pairNames = new List<string>();
            var proxyNames = new List<string>();
            var proxyColliders = new List<BoxCollider>();
            Transform solidPitBacking = null;
            foreach (var spec in specs.Where(item => item.Collider))
            {
                var pairName = PairName(spec);
                pairNames.Add(pairName);
                proxyNames.Add(spec.ColliderName);

                var pair = EnsureChild(pairs, pairName);
                SetTransform(pair, spec);
                ConfigureTag(pair, new[] { spec.SegmentId }, classification);

                var proxy = EnsureChild(proxies, spec.ColliderName);
                SetTransform(proxy, spec);
                ConfigureTag(proxy, new[] { spec.SegmentId }, classification);
                var collider = proxy.GetComponent<BoxCollider>();
                if (collider == null) collider = proxy.gameObject.AddComponent<BoxCollider>();
                collider.center = Vector3.zero;
                collider.size = Vector3.one;
                collider.isTrigger = false;
                collider.enabled = true;
                proxyColliders.Add(collider);
                if (spec.Name ==
                    ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.SolidPitBackingName)
                    solidPitBacking = proxy;
            }
            PruneChildren(pairs, pairNames);
            PruneChildren(proxies, proxyNames);

            var anchors = AddMetadata(metadata, classification, out var metadataNames);
            PruneChildren(metadata, metadataNames);
            ApplyV13Context(v4);
            ConfigureThresholdControl(metadata, v4, proxyColliders, anchors, solidPitBacking);
            if (InjectFailureAfterSuccessorBindingsForValidation)
                throw new InvalidOperationException(
                    "Injected V13 failure after successor bindings.");
            ValidateAppliedContext(v4, v10, root, audit);

            var rootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
            if (!Matches(rootMetrics,
                    ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedRendererCount,
                    ExpectedRootVertices, ExpectedRootTriangles,
                    ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedColliderCount) ||
                rootMetrics.Renderers != budget.root.renderers_exact ||
                rootMetrics.Vertices > budget.root.vertices_max ||
                rootMetrics.Triangles > budget.root.triangles_max ||
                rootMetrics.Colliders > budget.root.colliders_max)
                throw new InvalidOperationException(
                    "V13 root metric contract failed: " + MetricsToken(rootMetrics));

            var finalMap = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            if (!Matches(finalMap, ExpectedMapRenderers, ExpectedMapVertices,
                    ExpectedMapTriangles, ExpectedMapColliders) ||
                finalMap.Renderers != budget.map.renderers_exact ||
                finalMap.Colliders != budget.map.colliders_exact ||
                finalMap.Colliders > budget.map.colliders_max)
                throw new InvalidOperationException(
                    "V13 full-map metric contract failed: " + MetricsToken(finalMap));

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            EditorSceneManager.MarkSceneDirty(scene);
            if (!EditorSceneManager.SaveScene(scene))
                throw new InvalidOperationException("V13 scene save failed.");
            completed = true;
            Debug.Log("CHANNEL_PLAY_KHUFU_V13_BUILD result=built root=" +
                      MetricsToken(rootMetrics) + " map=" + MetricsToken(finalMap) +
                      " subterraneanBoundary=open");
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
            throw new FileNotFoundException("V13 classification is missing.",
                ClassificationPath);
        return JsonUtility.FromJson<SegmentClassificationDocument>(
            File.ReadAllText(ClassificationPath));
    }

    public static PerformanceBudgetDocument LoadPerformanceBudget()
    {
        if (!File.Exists(PerformanceBudgetPath))
            throw new FileNotFoundException("V13 performance budget is missing.",
                PerformanceBudgetPath);
        return JsonUtility.FromJson<PerformanceBudgetDocument>(
            File.ReadAllText(PerformanceBudgetPath));
    }

    public static PrewriteAuditDocument LoadPrewriteAudit()
    {
        if (!File.Exists(PrewriteAuditPath))
            throw new FileNotFoundException("V13 prewrite audit is missing.",
                PrewriteAuditPath);
        return JsonUtility.FromJson<PrewriteAuditDocument>(
            File.ReadAllText(PrewriteAuditPath));
    }

    public static void ApplyPredecessorContext(Transform v4)
    {
        SetV4SubterraneanComponents(v4, true);
    }

    public static void ApplyV13Context(Transform v4)
    {
        SetV4SubterraneanComponents(v4, false);
    }

    internal static string PairName(
        ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec spec)
    {
        return "V13_PAIR_" + spec.Name;
    }

    internal static void ValidateFrozenTargets(Transform v4, PrewriteAuditDocument audit,
        bool componentsEnabled)
    {
        if (audit.v4_subterranean_targets.Count != V4SubterraneanTargets.Length)
            throw new InvalidOperationException("V13 frozen target inventory drifted.");
        for (var index = 0; index < V4SubterraneanTargets.Length; index++)
        {
            var path = V4SubterraneanTargets[index];
            var frozen = audit.v4_subterranean_targets[index];
            var expectedFullPath =
                ChannelPlayPyramidReferenceMatchedV4Builder.RootName + "/" + path;
            var target = Require(v4.Find(path), path);
            var renderers = target.GetComponents<Renderer>();
            var colliders = target.GetComponents<Collider>();
            var expectedColliderCount = path == RendererOnlyPitPath ? 0 : 1;
            if (frozen.path != expectedFullPath || !frozen.active_self ||
                !frozen.active_in_hierarchy || frozen.renderer_count != 1 ||
                frozen.collider_count != expectedColliderCount ||
                frozen.box_collider_count != expectedColliderCount ||
                !target.gameObject.activeSelf || !target.gameObject.activeInHierarchy ||
                renderers.Length != 1 || renderers[0].enabled != componentsEnabled ||
                colliders.Length != expectedColliderCount ||
                colliders.Any(item => item.enabled != componentsEnabled || item.isTrigger) ||
                Vector3.Distance(target.localPosition, frozen.local_position) > 0.0001f ||
                Quaternion.Angle(target.localRotation, frozen.local_rotation) > 0.001f ||
                Vector3.Distance(target.localScale, frozen.local_scale) > 0.0001f)
                throw new InvalidOperationException(
                    "Frozen V4 subterranean target drifted: " + path);
        }
    }

    internal static void ValidatePreservedObservations(Transform v4, Transform v10,
        PrewriteAuditDocument audit)
    {
        if (audit.preserved_observations.Count != 7)
            throw new InvalidOperationException("V13 preserved observation inventory drifted.");
        foreach (var frozen in audit.preserved_observations)
        {
            Transform root;
            string relativePath;
            var v4Prefix = ChannelPlayPyramidReferenceMatchedV4Builder.RootName + "/";
            var v10Prefix = ChannelPlayKhufuV10InteriorBuilder.RootName + "/";
            if (frozen.path.StartsWith(v4Prefix, StringComparison.Ordinal))
            {
                root = v4;
                relativePath = frozen.path.Substring(v4Prefix.Length);
            }
            else if (frozen.path.StartsWith(v10Prefix, StringComparison.Ordinal))
            {
                root = v10;
                relativePath = frozen.path.Substring(v10Prefix.Length);
            }
            else
            {
                throw new InvalidOperationException(
                    "Unknown V13 preserved observation root: " + frozen.path);
            }

            var target = Require(root.Find(relativePath), frozen.path);
            var renderers = target.GetComponents<Renderer>();
            var lights = target.GetComponents<Light>();
            var colliders = target.GetComponents<Collider>();
            if (!target.gameObject.activeSelf || !target.gameObject.activeInHierarchy ||
                renderers.Length != frozen.renderer_count ||
                renderers.Any(item => item.enabled != frozen.renderer_enabled) ||
                lights.Length != frozen.light_count ||
                lights.Any(item => item.enabled != frozen.light_enabled) ||
                colliders.Length != frozen.collider_count ||
                Vector3.Distance(target.localPosition, frozen.local_position) > 0.0001f ||
                Quaternion.Angle(target.localRotation, frozen.local_rotation) > 0.001f ||
                Vector3.Distance(target.localScale, frozen.local_scale) > 0.0001f ||
                Vector3.Distance(target.position, frozen.world_position) > 0.0001f)
                throw new InvalidOperationException(
                    "Preserved V10/V4 dependency drifted: " + frozen.path);
        }
    }

    private static void ValidateContracts(SegmentClassificationDocument classification,
        PerformanceBudgetDocument budget, PrewriteAuditDocument audit)
    {
        if (classification == null ||
            classification.schema != "khufu-v13-subterranean-threshold-segments-v1" ||
            classification.segments == null || classification.ownership == null ||
            classification.ownership.transition_policy != "component-disable-only")
            throw new InvalidOperationException("V13 classification schema is invalid.");
        var expectedSegments = new HashSet<string>(
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
            StringComparer.Ordinal);
        var actualSegments = new HashSet<string>(
            classification.segments.Select(item => item.id), StringComparer.Ordinal);
        if (!expectedSegments.SetEquals(actualSegments) ||
            classification.segments.Count != expectedSegments.Count)
            throw new InvalidOperationException(
                "V13 classification segment inventory drifted.");
        if (classification.segments.Any(item =>
                item.truth != "FACT/HYBRID" && item.truth != "FACT/DISPLAY" &&
                item.truth != "HYBRID"))
            throw new InvalidOperationException(
                "V13 classification contains an unknown truth class.");
        if (classification.ownership.targets == null ||
            classification.ownership.targets.Count != V4SubterraneanTargets.Length)
            throw new InvalidOperationException("V13 ownership target inventory drifted.");
        for (var index = 0; index < V4SubterraneanTargets.Length; index++)
        {
            var target = classification.ownership.targets[index];
            var expectedPath =
                ChannelPlayPyramidReferenceMatchedV4Builder.RootName + "/" +
                V4SubterraneanTargets[index];
            var expectedColliders =
                V4SubterraneanTargets[index] == RendererOnlyPitPath ? 0 : 1;
            if (target.path != expectedPath || target.renderer_count != 1 ||
                target.collider_count != expectedColliders ||
                !target.active_self_before || !target.active_self_after ||
                !target.renderer_enabled_before || target.renderer_enabled_after ||
                (expectedColliders == 1 &&
                 (!target.collider_enabled_before || target.collider_enabled_after)))
                throw new InvalidOperationException(
                    "V13 ownership transition drifted: " + expectedPath);
        }

        if (budget == null ||
            budget.schema != "khufu-v13-subterranean-threshold-budget-v1" ||
            budget.baseline_v12 == null || budget.root == null || budget.map == null ||
            budget.captures == null ||
            budget.baseline_v12.static_signature != V12BaselineStaticSignature ||
            !MetricsMatch(budget.baseline_v12.root, 5, 1176, 588, 22) ||
            !MetricsMatch(budget.baseline_v12.map, V12BaselineRenderers,
                V12BaselineVertices, V12BaselineTriangles, V12BaselineColliders) ||
            budget.root.renderers_exact !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedRendererCount ||
            budget.root.colliders_exact !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedColliderCount ||
            budget.root.colliders_max !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedColliderCount ||
            budget.map.renderers_exact != ExpectedMapRenderers ||
            budget.map.colliders_exact != ExpectedMapColliders ||
            budget.map.colliders_max != 612 ||
            budget.captures.required != 6 || budget.captures.width != 1600 ||
            budget.captures.height != 1000)
            throw new InvalidOperationException("V13 performance budget is invalid.");

        if (audit == null || audit.schema != "khufu-v13-prewrite-audit-v1" ||
            !audit.passed || !audit.scene_unchanged || !audit.asset_tree_unchanged ||
            !audit.no_scene_or_asset_writes || audit.v4_subterranean_target_count != 13 ||
            audit.preserved_observation_count != 7 ||
            audit.v12_static_signature != V12BaselineStaticSignature ||
            audit.v12_validator_failures.Count != 0 ||
            !MetricsMatch(audit.v12_root_metrics, 5, 1176, 588, 22) ||
            !MetricsMatch(audit.v12_map_metrics, V12BaselineRenderers,
                V12BaselineVertices, V12BaselineTriangles, V12BaselineColliders))
            throw new InvalidOperationException("V13 prewrite audit contract is invalid.");
    }

    private static void ValidateSpecs(
        IReadOnlyList<ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec> specs,
        SegmentClassificationDocument classification)
    {
        var segments = new HashSet<string>(
            classification.segments.Select(item => item.id), StringComparer.Ordinal);
        if (specs.Count != ExpectedRootVertices / 24 ||
            specs.Count(item => item.Collider) !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedColliderCount)
            throw new InvalidOperationException("V13 geometry inventory drifted.");
        if (specs.Any(item => !segments.Contains(item.SegmentId) ||
                              !ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Buckets
                                  .Contains(item.Bucket) ||
                              item.Scale.x <= 0f || item.Scale.y <= 0f ||
                              item.Scale.z <= 0f ||
                              (item.Collider && item.ColliderIsTrigger)))
            throw new InvalidOperationException("V13 geometry contract is invalid.");
        if (specs.Select(item => item.Name).Distinct(StringComparer.Ordinal).Count() !=
            specs.Count)
            throw new InvalidOperationException("V13 geometry names are not unique.");
        foreach (var shell in
                 ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.PassageShells)
        {
            if (specs.Count(item => item.Shell == shell && item.Collider) != 4)
                throw new InvalidOperationException(
                    "V13 passage enclosure drifted: " + shell);
        }
        if (specs.Count(item =>
                item.Shell ==
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ChamberShell &&
                item.Collider) != 8)
            throw new InvalidOperationException("V13 chamber enclosure drifted.");
    }

    private static void ValidateInputContext(Transform v4, Transform v10,
        Transform previous, PrewriteAuditDocument audit)
    {
        if (previous != null &&
            (previous.localPosition != Vector3.zero ||
             previous.localRotation != Quaternion.identity ||
             previous.localScale != Vector3.one ||
             !previous.gameObject.activeSelf || !previous.gameObject.activeInHierarchy))
            throw new InvalidOperationException("Existing V13 root identity drifted.");
        ValidateFrozenTargets(v4, audit, previous == null);
        ValidatePreservedObservations(v4, v10, audit);
    }

    private static void ValidateAppliedContext(Transform v4, Transform v10,
        Transform root, PrewriteAuditDocument audit)
    {
        ValidateFrozenTargets(v4, audit, false);
        ValidatePreservedObservations(v4, v10, audit);
        var control = root.GetComponentInChildren<KhufuV13SubterraneanThresholdControl>(true);
        if (control == null ||
            control.PredecessorTargets.Count != V4SubterraneanTargets.Length ||
            control.CollisionProxies.Count !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ExpectedColliderCount ||
            control.RouteAnchors.Count !=
            KhufuV13SubterraneanRouteContract.ForwardRoute().Count ||
            control.SolidPitBacking == null ||
            control.SolidPitBacking.name !=
            "V13_Proxy_" +
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.SolidPitBackingName)
            throw new InvalidOperationException(
                "V13 runtime threshold-control binding drifted.");
    }

    private static void ValidateV12BaselineContext(Transform map, Transform v4,
        Transform previous)
    {
        var parent = previous == null ? null : previous.parent;
        var sibling = previous == null ? -1 : previous.GetSiblingIndex();
        var active = previous != null && previous.gameObject.activeSelf;
        var localPosition = previous == null ? Vector3.zero : previous.localPosition;
        var localRotation = previous == null ? Quaternion.identity : previous.localRotation;
        var localScale = previous == null ? Vector3.one : previous.localScale;
        try
        {
            if (previous != null)
            {
                previous.SetParent(null, true);
                previous.gameObject.SetActive(false);
            }
            ApplyPredecessorContext(v4);
            var validation = InvokeV12();
            if (validation.Failures.Count != 0 ||
                validation.Signature != V12BaselineStaticSignature)
                throw new InvalidOperationException(
                    "V12 baseline validator/signature drifted: " +
                    validation.Signature + " failures=" +
                    string.Join(" | ", validation.Failures));
            var metrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            if (!Matches(metrics, V12BaselineRenderers, V12BaselineVertices,
                    V12BaselineTriangles, V12BaselineColliders))
                throw new InvalidOperationException(
                    "V12 baseline metrics drifted: " + MetricsToken(metrics));
        }
        finally
        {
            if (previous == null) ApplyPredecessorContext(v4);
            else
            {
                ApplyV13Context(v4);
                previous.SetParent(parent, false);
                previous.SetSiblingIndex(sibling);
                previous.localPosition = localPosition;
                previous.localRotation = localRotation;
                previous.localScale = localScale;
                previous.gameObject.SetActive(active);
            }
            Physics.SyncTransforms();
        }
    }

    private static V12ValidationResult InvokeV12()
    {
        var method = typeof(ChannelPlayKhufuV12QueenCircuitValidator).GetMethod(
            "ValidateScene", BindingFlags.NonPublic | BindingFlags.Static);
        var raw = method?.Invoke(null, new object[] { false });
        if (raw == null)
            throw new InvalidOperationException("V12 validator result is missing.");
        var type = raw.GetType();
        var failures = type.GetField("Failures")?.GetValue(raw) as IEnumerable<string>;
        return new V12ValidationResult
        {
            Failures = failures?.ToList() ??
                       new List<string> { "V12 failures unavailable" },
            Signature = Convert.ToString(type.GetField("Signature")?.GetValue(raw))
        };
    }

    private static Dictionary<string, Mesh> BuildAndSaveMeshes(
        IReadOnlyList<ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec> specs)
    {
        EnsureAssetFolder(
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.GeneratedRoot);
        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal);
        foreach (var bucket in
                 ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Buckets)
        {
            var generated =
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BuildTransientMesh(
                    specs, bucket, "KhufuV13_" + bucket);
            var path =
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.GeneratedRoot +
                "/KhufuV13_" + bucket + ".asset";
            result.Add(bucket, SaveMesh(generated, path));
        }
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        return result;
    }

    private static Mesh SaveMesh(Mesh generated, string path)
    {
        var existing = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (existing == null)
        {
            AssetDatabase.CreateAsset(generated, path);
            return generated;
        }
        EditorUtility.CopySerialized(generated, existing);
        existing.name = generated.name;
        EditorUtility.SetDirty(existing);
        UnityEngine.Object.DestroyImmediate(generated);
        return existing;
    }

    private static Dictionary<string, Material> BuildMaterials()
    {
        EnsureAssetFolder(MaterialRoot);
        var result = new Dictionary<string, Material>(StringComparer.Ordinal)
        {
            {
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.StructureBucket,
                CreateOrUpdateMaterial("V13_Bedrock_Structure", "V10_Aged_Limestone",
                    new Color(0.48f, 0.40f, 0.30f, 1f), 0.01f, 0.16f)
            },
            {
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.DetailBucket,
                CreateOrUpdateMaterial("V13_Passage_Detail", "V10_Gallery_Detail",
                    new Color(0.35f, 0.28f, 0.20f, 1f), 0.01f, 0.13f)
            },
            {
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ShadowBucket,
                CreateOrUpdateMaterial("V13_Subterranean_Shadow", "V10_Deep_Shadow",
                    new Color(0.007f, 0.006f, 0.005f, 1f), 0f, 0.02f)
            },
            {
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.AccentBucket,
                CreateOrUpdateMaterial("V13_Evidence_Limit", "V10_Gallery_Detail",
                    new Color(0.55f, 0.34f, 0.13f, 1f), 0.02f, 0.24f)
            },
            {
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.InlayBucket,
                CreateOrUpdateMaterial("V13_Route_Inlay", "V10_Route_Amber",
                    new Color(1f, 0.28f, 0.02f, 1f), 0.04f, 0.34f,
                    new Color(2f, 0.34f, 0.015f, 1f))
            }
        };
        AssetDatabase.SaveAssets();
        return result;
    }

    private static Material CreateOrUpdateMaterial(string assetName,
        string sourceName, Color color, float metallic, float smoothness,
        Color? emission = null)
    {
        var sourcePath =
            "Assets/_Project/Materials/KhufuV10Interior/" + sourceName + ".mat";
        var source = AssetDatabase.LoadAssetAtPath<Material>(sourcePath);
        if (source == null)
            throw new InvalidOperationException(
                "V13 source material is missing: " + sourcePath);
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
        else
        {
            target.DisableKeyword("_EMISSION");
        }
        EditorUtility.SetDirty(target);
        return target;
    }

    private static IReadOnlyList<Transform> AddMetadata(Transform metadata,
        SegmentClassificationDocument classification,
        out IReadOnlyCollection<string> expectedNames)
    {
        var markers = new[]
        {
            new Marker("V13_Anchor_V10_Branch",
                KhufuV13SubterraneanRouteContract.V10BranchAnchor),
            new Marker("V13_Anchor_Junction_End",
                KhufuV13SubterraneanRouteContract.JunctionEnd),
            new Marker("V13_Anchor_Subterranean_Landing",
                KhufuV13SubterraneanRouteContract.SubterraneanLanding),
            new Marker("V13_Anchor_Chamber_Door",
                KhufuV13SubterraneanRouteContract.ChamberDoor),
            new Marker("V13_Anchor_Chamber_Center",
                KhufuV13SubterraneanRouteContract.ChamberCenter),
            new Marker("V13_Anchor_Pit_Inspection",
                KhufuV13SubterraneanRouteContract.PitInspection)
        };
        var names = new List<string>();
        var anchors = new List<Transform>();
        foreach (var item in markers)
        {
            names.Add(item.Name);
            anchors.Add(AddMarker(metadata, item.Name, item.Position,
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Segments,
                classification));
        }
        foreach (var segment in classification.segments
                     .OrderBy(item => item.id, StringComparer.Ordinal))
        {
            var name = "V13_SEGMENT_" + segment.id;
            names.Add(name);
            AddMarker(metadata, name, Vector3.zero, new[] { segment.id },
                classification);
        }
        expectedNames = names;
        return anchors;
    }

    private static Transform AddMarker(Transform parent, string name,
        Vector3 position, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var marker = EnsureChild(parent, name);
        marker.localPosition = position;
        marker.localRotation = Quaternion.identity;
        marker.localScale = Vector3.one;
        ConfigureTag(marker, segmentIds, classification);
        return marker;
    }

    private static void ConfigureThresholdControl(Transform metadata, Transform v4,
        IEnumerable<BoxCollider> proxies, IEnumerable<Transform> anchors,
        Transform solidPitBacking)
    {
        if (solidPitBacking == null)
            throw new InvalidOperationException(
                "V13 solid unfinished-pit backing is missing.");
        var targets = V4SubterraneanTargets
            .Select(path => Require(v4.Find(path), path).gameObject).ToArray();
        var control = metadata.GetComponent<KhufuV13SubterraneanThresholdControl>();
        if (control == null)
            control =
                metadata.gameObject.AddComponent<KhufuV13SubterraneanThresholdControl>();
        control.Configure(targets, proxies, anchors, solidPitBacking);
        EditorUtility.SetDirty(control);
    }

    private static void CreateRenderer(Transform parent, string bucket, Mesh mesh,
        Material material, IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        if (mesh == null || material == null)
            throw new InvalidOperationException(
                "V13 mesh/material is missing: " + bucket);
        var child = EnsureChild(parent, "V13_" + bucket);
        var filter = child.GetComponent<MeshFilter>();
        if (filter == null) filter = child.gameObject.AddComponent<MeshFilter>();
        filter.sharedMesh = mesh;
        var renderer = child.GetComponent<MeshRenderer>();
        if (renderer == null)
            renderer = child.gameObject.AddComponent<MeshRenderer>();
        renderer.enabled = true;
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode =
            bucket == ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.InlayBucket ||
            bucket == ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ShadowBucket
                ? ShadowCastingMode.Off
                : ShadowCastingMode.On;
        renderer.receiveShadows =
            bucket != ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.InlayBucket;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        ConfigureTag(child, segmentIds, classification);
    }

    private static void ConfigureTag(Transform target,
        IEnumerable<string> segmentIds,
        SegmentClassificationDocument classification)
    {
        var ids = segmentIds.Distinct().OrderBy(item => item, StringComparer.Ordinal)
            .ToArray();
        if (ids.Length == 0)
            throw new InvalidOperationException(
                "V13 object has no classification: " + target.name);
        var records = ids
            .Select(id => classification.segments.Single(item => item.id == id))
            .ToArray();
        var truth =
            records.Select(item => item.truth).Distinct(StringComparer.Ordinal).Count() == 1
                ? records[0].truth
                : "MIXED";
        var tag = target.GetComponent<KhufuV13SegmentTag>();
        if (tag == null)
            tag = target.gameObject.AddComponent<KhufuV13SegmentTag>();
        tag.Configure(ids, truth, records.All(item => item.factual_shape),
            records.Any(item => item.gameplay_scale));
    }

    private static void SetV4SubterraneanComponents(Transform v4, bool enabled)
    {
        foreach (var path in V4SubterraneanTargets)
        {
            var target = Require(v4.Find(path), path);
            var renderers = target.GetComponents<Renderer>();
            var colliders = target.GetComponents<Collider>();
            var expectedColliderCount = path == RendererOnlyPitPath ? 0 : 1;
            if (renderers.Length != 1 || colliders.Length != expectedColliderCount ||
                (expectedColliderCount == 1 &&
                 !(colliders[0] is BoxCollider)))
                throw new InvalidOperationException(
                    "V4 subterranean component inventory drifted: " + path);
            renderers[0].enabled = enabled;
            EditorUtility.SetDirty(renderers[0]);
            foreach (var collider in colliders)
            {
                collider.enabled = enabled;
                EditorUtility.SetDirty(collider);
            }
        }
    }

    private static void SetTransform(Transform target,
        ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec spec)
    {
        target.localPosition = spec.Position;
        target.localRotation = spec.Rotation;
        target.localScale = spec.Scale;
        target.gameObject.SetActive(true);
    }

    private static Transform Require(Transform target, string label)
    {
        if (target == null)
            throw new InvalidOperationException(
                "Required V13 dependency is missing: " + label);
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

    private static void PruneChildren(Transform parent,
        IEnumerable<string> expectedNames)
    {
        var expected = new HashSet<string>(expectedNames, StringComparer.Ordinal);
        for (var index = parent.childCount - 1; index >= 0; index--)
        {
            var child = parent.GetChild(index);
            if (!expected.Contains(child.name))
                UnityEngine.Object.DestroyImmediate(child.gameObject);
        }
    }

    private static void EnsureAssetFolder(string path)
    {
        var parts = path.Split('/');
        var current = parts[0];
        for (var index = 1; index < parts.Length; index++)
        {
            var next = current + "/" + parts[index];
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(current, parts[index]);
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

    private static bool Matches(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics,
        int renderers, int vertices, int triangles, int colliders)
    {
        return metrics.Renderers == renderers && metrics.Vertices == vertices &&
               metrics.Triangles == triangles && metrics.Colliders == colliders;
    }

    private static bool MetricsMatch(MetricsRecord metrics,
        int renderers, int vertices, int triangles, int colliders)
    {
        return metrics != null && metrics.renderers == renderers &&
               metrics.vertices == vertices && metrics.triangles == triangles &&
               metrics.colliders == colliders;
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

    private static string MetricsToken(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    [Serializable]
    public sealed class SegmentClassificationDocument
    {
        public string schema = string.Empty;
        public List<SegmentClassificationRecord> segments =
            new List<SegmentClassificationRecord>();
        public OwnershipDocument ownership = new OwnershipDocument();
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
    public sealed class OwnershipDocument
    {
        public string transition_policy = string.Empty;
        public List<OwnershipRecord> targets = new List<OwnershipRecord>();
    }

    [Serializable]
    public sealed class OwnershipRecord
    {
        public string path = string.Empty;
        public int renderer_count;
        public int collider_count;
        public bool active_self_before;
        public bool active_self_after;
        public bool renderer_enabled_before;
        public bool renderer_enabled_after;
        public bool collider_enabled_before;
        public bool collider_enabled_after;
    }

    [Serializable]
    public sealed class PerformanceBudgetDocument
    {
        public string schema = string.Empty;
        public BaselineBudget baseline_v12 = new BaselineBudget();
        public RootBudget root = new RootBudget();
        public MapBudget map = new MapBudget();
        public CaptureBudget captures = new CaptureBudget();
    }

    [Serializable]
    public sealed class BaselineBudget
    {
        public string static_signature = string.Empty;
        public MetricsRecord root = new MetricsRecord();
        public MetricsRecord map = new MetricsRecord();
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

    [Serializable]
    public sealed class PrewriteAuditDocument
    {
        public string schema = string.Empty;
        public bool passed;
        public bool scene_unchanged;
        public bool asset_tree_unchanged;
        public bool no_scene_or_asset_writes;
        public int v4_subterranean_target_count;
        public List<FrozenTargetRecord> v4_subterranean_targets =
            new List<FrozenTargetRecord>();
        public int preserved_observation_count;
        public List<FrozenObservationRecord> preserved_observations =
            new List<FrozenObservationRecord>();
        public MetricsRecord v12_root_metrics = new MetricsRecord();
        public MetricsRecord v12_map_metrics = new MetricsRecord();
        public string v12_static_signature = string.Empty;
        public List<string> v12_validator_failures = new List<string>();
    }

    [Serializable]
    public sealed class FrozenTargetRecord
    {
        public string path = string.Empty;
        public bool active_self;
        public bool active_in_hierarchy;
        public int renderer_count;
        public int collider_count;
        public int box_collider_count;
        public bool renderer_enabled;
        public bool collider_enabled;
        public bool is_trigger;
        public Vector3 local_position;
        public Quaternion local_rotation;
        public Vector3 local_scale;
    }

    [Serializable]
    public sealed class FrozenObservationRecord
    {
        public string path = string.Empty;
        public string kind = string.Empty;
        public string owner = string.Empty;
        public bool active_self;
        public bool active_in_hierarchy;
        public int renderer_count;
        public bool renderer_enabled;
        public int light_count;
        public bool light_enabled;
        public int collider_count;
        public Vector3 local_position;
        public Quaternion local_rotation;
        public Vector3 local_scale;
        public Vector3 world_position;
    }

    [Serializable]
    public sealed class MetricsRecord
    {
        public int renderers;
        public int vertices;
        public int triangles;
        public int colliders;
    }

    private readonly struct Marker
    {
        public readonly string Name;
        public readonly Vector3 Position;

        public Marker(string name, Vector3 position)
        {
            Name = name;
            Position = position;
        }
    }

    private sealed class V12ValidationResult
    {
        public List<string> Failures = new List<string>();
        public string Signature = string.Empty;
    }

    private sealed class BuildSnapshot
    {
        private readonly byte[] sceneBytes = File.ReadAllBytes(ScenePath);
        private readonly DirectorySnapshot generated =
            new DirectorySnapshot(
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.GeneratedRoot);
        private readonly DirectorySnapshot materials =
            new DirectorySnapshot(MaterialRoot);

        public void Restore()
        {
            File.WriteAllBytes(ScenePath, sceneBytes);
            generated.Restore();
            materials.Restore();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            if (!File.ReadAllBytes(ScenePath).SequenceEqual(sceneBytes) ||
                !generated.MatchesSnapshot() || !materials.MatchesSnapshot())
                throw new InvalidOperationException(
                    "V13 failed-build rollback verification failed.");
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }
    }

    private sealed class DirectorySnapshot
    {
        private readonly string path;
        private readonly Dictionary<string, byte[]> files =
            new Dictionary<string, byte[]>(StringComparer.Ordinal);
        private readonly bool existed;
        private readonly bool metaExisted;
        private readonly byte[] metaBytes;

        public DirectorySnapshot(string assetPath)
        {
            path = assetPath.Replace('/', Path.DirectorySeparatorChar);
            existed = Directory.Exists(path);
            metaExisted = File.Exists(path + ".meta");
            metaBytes = metaExisted
                ? File.ReadAllBytes(path + ".meta")
                : Array.Empty<byte>();
            if (!existed) return;
            foreach (var file in Directory.GetFiles(path, "*",
                         SearchOption.AllDirectories))
                files[file] = File.ReadAllBytes(file);
        }

        public void Restore()
        {
            if (Directory.Exists(path))
            {
                foreach (var file in Directory.GetFiles(path, "*",
                             SearchOption.AllDirectories))
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
                    if (!string.IsNullOrEmpty(parent))
                        Directory.CreateDirectory(parent);
                    File.WriteAllBytes(item.Key, item.Value);
                }
            }
            if (metaExisted) File.WriteAllBytes(path + ".meta", metaBytes);
            else if (File.Exists(path + ".meta")) File.Delete(path + ".meta");
        }

        public bool MatchesSnapshot()
        {
            if (Directory.Exists(path) != existed ||
                File.Exists(path + ".meta") != metaExisted)
                return false;
            if (metaExisted &&
                !File.ReadAllBytes(path + ".meta").SequenceEqual(metaBytes))
                return false;
            if (!existed) return true;
            var current = Directory.GetFiles(path, "*",
                SearchOption.AllDirectories);
            return current.Length == files.Count &&
                   current.All(file =>
                       files.TryGetValue(file, out var bytes) &&
                       File.ReadAllBytes(file).SequenceEqual(bytes));
        }
    }
}

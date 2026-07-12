using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV10InteriorValidator
{
    private const float PairTolerance = 0.01f;
    private const float MarkerTolerance = 0.001f;
    private const float ClearanceWidth = 1.8f;
    private const float ClearanceHeight = 2.2f;
    private const float EnclosureDistance = 4.5f;
    private const float MinimumEnclosureRatio = 0.75f;
    private const string FrozenV8Signature = "be64fa8b33e798093d55087fc279377446e6e5556e059ad273aeaf1d87ccdfa4";
    private const string FrozenV9Signature = "8301ccc17bf1323fb8e9d1a525a778bf9ccdbf2da3dc15412b4bbf790ac85da8";

    private static readonly Dictionary<string, string> ExpectedMaterials = new Dictionary<string, string>(StringComparer.Ordinal)
    {
        { ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket, "V10_Aged_Limestone" },
        { ChannelPlayKhufuV10InteriorMeshPipeline.GalleryDetailBucket, "V10_Gallery_Detail" },
        { ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket, "V10_Red_Granite" },
        { ChannelPlayKhufuV10InteriorMeshPipeline.HybridBucket, "V10_Hybrid_Service" },
        { ChannelPlayKhufuV10InteriorMeshPipeline.ShadowBucket, "V10_Deep_Shadow" },
        { ChannelPlayKhufuV10InteriorMeshPipeline.InlayBucket, "V10_Route_Amber" }
    };

    // Fixed and intentionally explicit. The enclosure gate must never depend on random sampling.
    private static readonly Vector3[] EnclosureDirections =
    {
        new Vector3(-1.00f, 0.00f, 0.00f), new Vector3(1.00f, 0.00f, 0.00f),
        new Vector3(-0.98f, 0.20f, 0.00f), new Vector3(0.98f, 0.20f, 0.00f),
        new Vector3(-0.92f, 0.38f, 0.00f), new Vector3(0.92f, 0.38f, 0.00f),
        new Vector3(-0.82f, 0.57f, 0.00f), new Vector3(0.82f, 0.57f, 0.00f),
        new Vector3(-0.68f, 0.73f, 0.00f), new Vector3(0.68f, 0.73f, 0.00f),
        new Vector3(-0.50f, 0.86f, 0.00f), new Vector3(0.50f, 0.86f, 0.00f),
        new Vector3(-0.30f, 0.95f, 0.00f), new Vector3(0.30f, 0.95f, 0.00f),
        new Vector3(-0.14f, 0.98f, -0.16f), new Vector3(0.14f, 0.98f, -0.16f),
        new Vector3(-0.14f, 0.98f, 0.16f), new Vector3(0.14f, 0.98f, 0.16f),
        new Vector3(-0.86f, 0.46f, -0.22f), new Vector3(0.86f, 0.46f, -0.22f),
        new Vector3(-0.86f, 0.46f, 0.22f), new Vector3(0.86f, 0.46f, 0.22f),
        new Vector3(-0.58f, 0.78f, -0.24f), new Vector3(0.58f, 0.78f, 0.24f)
    };

    [MenuItem("Channel Play/Khufu V10/Run All Static Gates")]
    public static void RunAllStaticGates()
    {
        ValidateMenu();
        ValidateIdempotence();
        ValidatePairMutation();
        ValidateTransitionMutation();
        ValidateMetricMutation();
        Debug.Log("CHANNEL_PLAY_KHUFU_V10_STATIC_GATES result=passed");
    }

    public static void RunAllStaticGatesBatch()
    {
        try
        {
            RunAllStaticGates();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    [MenuItem("Channel Play/Khufu V10/Validate Interior Spine")]
    public static void ValidateMenu()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV10InteriorBuilder.RunRoot);
        EditorSceneManager.OpenScene(ChannelPlayKhufuV10InteriorBuilder.ScenePath, OpenSceneMode.Single);
        var result = ValidateScene();
        WriteValidation(result);
        WritePostwriteAudit(result);
        if (!result.Passed)
            throw new InvalidOperationException("Khufu V10 validation failed: " + string.Join("; ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V10_VALIDATE result=passed signature=" + result.Signature +
                  " clearance_samples=" + result.ClearanceSamples + " enclosure_min=" +
                  result.MinimumEnclosureRatio.ToString("0.000", CultureInfo.InvariantCulture));
    }

    public static void ValidateBatch()
    {
        try
        {
            ValidateMenu();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    public static void DumpSpatialDiagnosticsBatch()
    {
        try
        {
            EditorSceneManager.OpenScene(ChannelPlayKhufuV10InteriorBuilder.ScenePath, OpenSceneMode.Single);
            var map = GameObject.Find(ChannelPlayKhufuV10InteriorBuilder.MapRootName).transform;
            var text = new StringBuilder("# Khufu V10 Spatial Diagnostics\n\n## Route Points\n\n");
            var route = ChannelPlayKhufuV10InteriorMeshPipeline.NormalRoute();
            for (var index = 0; index < route.Count; index++)
                text.AppendLine("- `" + index + "`: `" + VectorToken(route[index]) + "`");
            text.AppendLine();
            text.AppendLine("## Candidate Blocker Bounds");
            text.AppendLine();
            foreach (var collider in map.GetComponentsInChildren<Collider>(true)
                         .Where(item => item.name.IndexOf("Branch_Junction", StringComparison.Ordinal) >= 0 ||
                                        item.name.IndexOf("Descending_Bedrock", StringComparison.Ordinal) >= 0 ||
                                        item.name.IndexOf("Queens_", StringComparison.Ordinal) >= 0 ||
                                        item.name.IndexOf("Kings_", StringComparison.Ordinal) >= 0 ||
                                        item.name.IndexOf("Antechamber", StringComparison.Ordinal) >= 0 ||
                                        item.name.IndexOf("Core_Block", StringComparison.Ordinal) >= 0 ||
                                        item.name.IndexOf("Approach_Step", StringComparison.Ordinal) >= 0)
                         .OrderBy(item => HierarchyPath(map, item.transform), StringComparer.Ordinal))
                text.AppendLine("- `" + HierarchyPath(map, collider.transform) + "`: center=`" +
                                VectorToken(collider.bounds.center) + "`, size=`" + VectorToken(collider.bounds.size) +
                                "`, enabled=`" + collider.enabled + "`");
            File.WriteAllText(RunPath("spatial-diagnostic.md"), text.ToString());
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    [MenuItem("Channel Play/Khufu V10/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV10InteriorBuilder.RunRoot);
        ChannelPlayKhufuV10InteriorBuilder.Rebuild();
        var first = ValidateScene();
        var firstScene = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV10InteriorBuilder.ScenePath);
        var firstAssets = GeneratedAssetBindings();

        ChannelPlayKhufuV10InteriorBuilder.Rebuild();
        var second = ValidateScene();
        var secondScene = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV10InteriorBuilder.ScenePath);
        var secondAssets = GeneratedAssetBindings();
        var passed = first.Passed && second.Passed && first.Signature == second.Signature &&
                     Same(first.RootMetrics, second.RootMetrics) && firstScene == secondScene &&
                     firstAssets.SequenceEqual(secondAssets);

        var text = new StringBuilder("# Khufu V10 Rebuild Idempotence\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- First scene SHA256: `" + firstScene + "`");
        text.AppendLine("- Second scene SHA256: `" + secondScene + "`");
        text.AppendLine("- First signature: `" + first.Signature + "`");
        text.AppendLine("- Second signature: `" + second.Signature + "`");
        text.AppendLine("- Stable generated asset bindings: `" + firstAssets.Count + "`");
        text.AppendLine();
        text.AppendLine("V10_IDEMPOTENCE: " + (passed ? "passed" : "failed"));
        File.WriteAllText(RunPath("idempotence.md"), text.ToString());
        if (!passed) throw new InvalidOperationException("Khufu V10 idempotence failed.");
    }

    [MenuItem("Channel Play/Khufu V10/Validate Structural Pair Mutation")]
    public static void ValidatePairMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV10InteriorBuilder.ScenePath, OpenSceneMode.Single);
        var root = FindRoot();
        if (root == null) throw new InvalidOperationException("V10 root missing for pair mutation.");
        var proxies = root.Find(ChannelPlayKhufuV10InteriorBuilder.CollisionRootName);
        var target = proxies.Cast<Transform>().OrderBy(item => item.name, StringComparer.Ordinal).First();
        var original = target.position;
        target.position += Vector3.right * 0.25f;
        Physics.SyncTransforms();
        var mutated = ValidateScene(false);
        target.position = original;
        Physics.SyncTransforms();
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("pair bounds", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("pair-mutation.md", "Offset " + target.name + " by +0.25m world X", mutated.Failures, rejected, "V10_PAIR_MUTATION");
        if (!rejected) throw new InvalidOperationException("V10 structural-pair mutation was not rejected.");
    }

    [MenuItem("Channel Play/Khufu V10/Validate Transition Mutation")]
    public static void ValidateTransitionMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV10InteriorBuilder.ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV10InteriorBuilder.MapRootName).transform;
        var manifest = ChannelPlayKhufuV10InteriorBuilder.LoadDisableManifest();
        var target = ChannelPlayKhufuV10InteriorBuilder.CollectManifestRenderers(map, manifest).First();
        var original = target.enabled;
        target.enabled = true;
        var mutated = ValidateScene(false);
        target.enabled = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("transition renderer", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("transition-mutation.md", "Re-enable " + target.name, mutated.Failures, rejected, "V10_TRANSITION_MUTATION");
        if (!rejected) throw new InvalidOperationException("V10 transition mutation was not rejected.");
    }

    [MenuItem("Channel Play/Khufu V10/Validate Observation Metric Mutation")]
    public static void ValidateMetricMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV10InteriorBuilder.ScenePath, OpenSceneMode.Single);
        var root = FindRoot();
        var metadata = root == null ? null : root.Find(ChannelPlayKhufuV10InteriorBuilder.MetadataRootName);
        var target = metadata == null ? null : metadata.Find("V10_Anchor_Great_Step_Stop");
        if (target == null) throw new InvalidOperationException("V10 Great Step observation anchor is missing.");
        var original = target.position;
        target.position += Vector3.up * 0.75f;
        var mutated = ValidateScene(false);
        target.position = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item =>
            item.IndexOf("observation error", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("metric-mutation.md", "Offset Great Step observation by +0.75m world Y against 0.40m threshold",
            mutated.Failures, rejected, "V10_METRIC_MUTATION");
        if (!rejected) throw new InvalidOperationException("V10 observation metric mutation was not rejected.");
    }

    private static ValidationResult ValidateScene(bool validateGeneratedBindings = true)
    {
        var result = new ValidationResult();
        var mapObject = GameObject.Find(ChannelPlayKhufuV10InteriorBuilder.MapRootName);
        if (mapObject == null)
        {
            result.Failures.Add("Shared map root missing");
            return Finish(result, null);
        }

        var map = mapObject.transform;
        var roots = map.Cast<Transform>().Where(item => item.name == ChannelPlayKhufuV10InteriorBuilder.RootName).ToArray();
        if (roots.Length != 1)
        {
            result.Failures.Add("Expected exactly one V10 root, found " + roots.Length);
            return Finish(result, null);
        }

        var root = roots[0];
        if (!TransformMatches(root, Vector3.zero, Quaternion.identity, Vector3.one))
            result.Failures.Add("V10 root placement drifted from the shared world frame");
        if (root.childCount != 4) result.Failures.Add("V10 root ownership groups drifted");

        var specs = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs();
        var expectedRoot = Metrics(6, specs.Count * 24, specs.Count * 12, specs.Count(item => item.Structural && item.Collider));
        result.RootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        result.MapMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        var expectedMap = Metrics(ChannelPlayKhufuV10InteriorBuilder.BaselineRenderers + expectedRoot.Renderers,
            ChannelPlayKhufuV10InteriorBuilder.BaselineVertices + expectedRoot.Vertices,
            ChannelPlayKhufuV10InteriorBuilder.BaselineTriangles + expectedRoot.Triangles,
            ChannelPlayKhufuV10InteriorBuilder.BaselineColliders + expectedRoot.Colliders);
        if (!Same(result.RootMetrics, expectedRoot)) result.Failures.Add("Unexpected V10 root metrics: " + MetricsToken(result.RootMetrics));
        if (!Same(result.MapMetrics, expectedMap)) result.Failures.Add("Unexpected full-map V10 metrics: " + MetricsToken(result.MapMetrics));

        Physics.SyncTransforms();
        ValidateGeneratedVisuals(root, specs, result, validateGeneratedBindings);
        ValidateStructuralPairs(root, specs, result);
        ValidateSegmentClassification(root, result);
        ValidateObservationAnchors(root, result);
        ValidateNamedEvidence(specs, result);
        ValidateTransitionsAndFrozenMarkers(map, result);
        ValidateLegacyOwnership(map, result);
        ValidateColliderEnvelope(map, root, specs, result);
        ValidateRouteClearance(map, result);
        ValidateGrandGalleryEnclosure(root, result);
        ValidateVisibleBudget(map, result);
        ValidateForbiddenComponents(root, result);
        return Finish(result, root);
    }

    private static void ValidateGeneratedVisuals(Transform root,
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, ValidationResult result,
        bool validateBindings)
    {
        var visuals = root.Find(ChannelPlayKhufuV10InteriorBuilder.VisualRootName);
        if (visuals == null)
        {
            result.Failures.Add("V10 visual root missing");
            return;
        }
        var renderers = visuals.GetComponentsInChildren<MeshRenderer>(true);
        if (renderers.Length != ChannelPlayKhufuV10InteriorMeshPipeline.ExpectedRendererCount)
            result.Failures.Add("V10 renderer bucket count drifted to " + renderers.Length);

        foreach (var bucket in ChannelPlayKhufuV10InteriorMeshPipeline.Buckets)
        {
            var rendererTransform = visuals.Find("V10_" + bucket);
            var renderer = rendererTransform == null ? null : rendererTransform.GetComponent<MeshRenderer>();
            var filter = rendererTransform == null ? null : rendererTransform.GetComponent<MeshFilter>();
            if (renderer == null || filter == null || filter.sharedMesh == null)
            {
                result.Failures.Add("V10 generated renderer missing: " + bucket);
                continue;
            }
            var bucketSpecs = specs.Where(item => item.Bucket == bucket).ToArray();
            if (filter.sharedMesh.vertexCount != bucketSpecs.Length * 24 ||
                ChannelPlayKhufuV10InteriorMeshPipeline.TriangleCount(filter.sharedMesh) != bucketSpecs.Length * 12)
                result.Failures.Add("V10 mesh topology drifted: " + bucket);
            if (renderer.sharedMaterial == null || renderer.sharedMaterial.name != ExpectedMaterials[bucket])
                result.Failures.Add("V10 material binding drifted: " + bucket);
            foreach (var spec in bucketSpecs)
                if (!MeshContainsSpec(filter.sharedMesh, spec)) result.Failures.Add("V10 mesh omits spec corners: " + spec.Name);
            if (validateBindings)
            {
                var expectedPath = ChannelPlayKhufuV10InteriorMeshPipeline.GeneratedRoot + "/KhufuV10_" + bucket + ".asset";
                if (AssetDatabase.GetAssetPath(filter.sharedMesh) != expectedPath)
                    result.Failures.Add("V10 generated mesh binding drifted: " + bucket);
            }
        }
    }

    private static void ValidateStructuralPairs(Transform root,
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, ValidationResult result)
    {
        var pairs = root.Find(ChannelPlayKhufuV10InteriorBuilder.PairRootName);
        var proxies = root.Find(ChannelPlayKhufuV10InteriorBuilder.CollisionRootName);
        if (pairs == null || proxies == null)
        {
            result.Failures.Add("V10 pair or collision root missing");
            return;
        }
        var structural = specs.Where(item => item.Structural && item.Collider).ToArray();
        if (pairs.childCount != structural.Length || proxies.childCount != structural.Length)
            result.Failures.Add("V10 structural-pair inventory drifted");
        foreach (var spec in structural)
        {
            var suffix = spec.SegmentId + "_" + spec.Name;
            var pair = pairs.Find("V10_PAIR_" + suffix);
            var proxy = proxies.Find("V10_PROXY_" + suffix);
            if (pair == null || proxy == null)
            {
                result.Failures.Add("V10 structural pair missing: " + suffix);
                continue;
            }
            if (!TransformMatches(pair, spec.Position, spec.Rotation, spec.Scale) ||
                !TransformMatches(proxy, spec.Position, spec.Rotation, spec.Scale) ||
                BoundsDelta(BoundsForTransform(pair), BoundsForTransform(proxy)) > PairTolerance)
                result.Failures.Add("V10 pair bounds drifted: " + suffix);
            var collider = proxy.GetComponent<BoxCollider>();
            if (collider == null || !collider.enabled || collider.isTrigger || collider.center != Vector3.zero || collider.size != Vector3.one)
                result.Failures.Add("V10 proxy collider drifted: " + suffix);
        }
    }

    private static void ValidateSegmentClassification(Transform root, ValidationResult result)
    {
        var classification = ChannelPlayKhufuV10InteriorBuilder.LoadClassification();
        var expected = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        foreach (var target in root.GetComponentsInChildren<Transform>(true))
        {
            if (target.name.IndexOf("Well Shaft", StringComparison.OrdinalIgnoreCase) >= 0)
                result.Failures.Add("Forbidden V10 runtime label found: " + target.name);
            var tag = target.GetComponent<KhufuV10SegmentTag>();
            if (tag == null)
            {
                result.Failures.Add("V10 object lacks segment classification: " + HierarchyPath(root, target));
                continue;
            }
            if (tag.SegmentIds.Count == 0 || tag.SegmentIds.Any(item => !expected.Contains(item)))
                result.Failures.Add("V10 object has invalid segment classification: " + HierarchyPath(root, target));
            if (tag.SegmentIds.Any(item => item.IndexOf("Well Shaft", StringComparison.OrdinalIgnoreCase) >= 0) ||
                tag.TruthClass.IndexOf("Well Shaft", StringComparison.OrdinalIgnoreCase) >= 0)
                result.Failures.Add("Forbidden V10 metadata label found: " + HierarchyPath(root, target));
        }

        var metadata = root.Find(ChannelPlayKhufuV10InteriorBuilder.MetadataRootName);
        foreach (var record in classification.segments)
        {
            var marker = metadata == null ? null : metadata.Find("V10_SEGMENT_" + record.id);
            var tag = marker == null ? null : marker.GetComponent<KhufuV10SegmentTag>();
            if (tag == null || tag.SegmentIds.Count != 1 || tag.SegmentIds[0] != record.id ||
                tag.TruthClass != record.truth || tag.FactualShape != record.factual_shape ||
                tag.GameplayScale != record.gameplay_scale)
                result.Failures.Add("V10 segment metadata drifted: " + record.id);
        }
    }

    private static void ValidateNamedEvidence(IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        ExpectCount(specs, "Gallery_Corbel_West_", 7, result);
        ExpectCount(specs, "Gallery_Corbel_East_", 7, result);
        ExpectCount(specs, "Gallery_Bench_Slot_West_", 27, result);
        ExpectCount(specs, "Gallery_Bench_Slot_East_", 27, result);
        ExpectCount(specs, "Great_Step_West_Slot", 1, result);
        ExpectCount(specs, "Great_Step_East_Slot", 1, result);
        ExpectCount(specs, "Granite_Plug_", 3, result);
        var greatStep = specs.SingleOrDefault(item => item.Name == "Great_Step_Diegetic_Boundary" &&
                                                       item.Structural && item.Collider);
        if (greatStep == null)
            result.Failures.Add("Great Step visible collision boundary is missing");
        var galleryFloor = specs.SingleOrDefault(item => item.Name == "Gallery_Floor_Ramp" && item.Collider);
        if (greatStep != null && galleryFloor != null)
        {
            var gallery = ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFrame();
            var floorEnd = galleryFloor.Position +
                           galleryFloor.Rotation * Vector3.forward * (galleryFloor.Scale.z * 0.5f);
            var floorEndDistance = Vector3.Dot(floorEnd - ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFoot,
                gallery.Forward);
            var boundaryDistance = Vector3.Dot(
                greatStep.Position - ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFoot, gallery.Forward);
            if (floorEndDistance < boundaryDistance + 0.45f)
                result.Failures.Add("Gallery floor does not carry a full capsule beneath the named Great Step boundary");
        }
        var hybrid = ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnPoints();
        if (hybrid.Count < 3 || Mathf.Abs(hybrid[1].y - hybrid[0].y) > 0.05f || hybrid[2].y > hybrid[1].y)
            result.Failures.Add("HYBRID service return reintroduced a non-playable rise-then-descent crest");
        if (!specs.Any(item => item.Name == "Historic_Service_Mouth_Recess" && !item.Collider))
            result.Failures.Add("Historic service mouth evidence boundary is missing");
    }

    private static void ValidateObservationAnchors(Transform root, ValidationResult result)
    {
        var metadata = root.Find(ChannelPlayKhufuV10InteriorBuilder.MetadataRootName);
        if (metadata == null)
        {
            result.Failures.Add("V10 metadata root missing for observations");
            return;
        }
        ValidateObservation(metadata, "V10_Anchor_North_Entrance", ChannelPlayKhufuV10InteriorMeshPipeline.Entrance, result);
        ValidateObservation(metadata, "V10_Anchor_Ascending_Branch", ChannelPlayKhufuV10InteriorMeshPipeline.Branch, result);
        ValidateObservation(metadata, "V10_Anchor_Grand_Gallery_Foot", ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFoot, result);
        ValidateObservation(metadata, "V10_Anchor_Great_Step_Stop", ChannelPlayKhufuV10InteriorMeshPipeline.GreatStepStop(), result);
        ValidateObservation(metadata, "V10_Anchor_Historic_Service_Mouth", ChannelPlayKhufuV10InteriorMeshPipeline.HistoricServiceMouth(), result);
        var returnPoints = ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnPoints();
        for (var index = 0; index < returnPoints.Count; index++)
            ValidateObservation(metadata, "V10_Anchor_HYBRID_Return_" + index.ToString("D2"), returnPoints[index], result);
    }

    private static void ValidateObservation(Transform metadata, string name, Vector3 expected, ValidationResult result)
    {
        var target = metadata.Find(name);
        var error = target == null ? float.PositiveInfinity : Vector3.Distance(target.position, expected);
        if (error > 0.40f)
            result.Failures.Add("V10 observation error exceeds 0.40m: " + name + " error=" +
                                error.ToString("0.000", CultureInfo.InvariantCulture));
    }

    private static void ValidateTransitionsAndFrozenMarkers(Transform map, ValidationResult result)
    {
        var manifest = ChannelPlayKhufuV10InteriorBuilder.LoadDisableManifest();
        var renderers = ChannelPlayKhufuV10InteriorBuilder.CollectManifestRenderers(map, manifest);
        var colliders = ChannelPlayKhufuV10InteriorBuilder.CollectManifestColliders(map, manifest);
        result.DisabledRenderers = renderers.Count(item => item != null && !item.enabled);
        result.DisabledColliders = colliders.Count(item => item != null && !item.enabled);
        if (renderers.Count != 60 || result.DisabledRenderers != 60)
            result.Failures.Add("V10 transition renderer state drifted: " + result.DisabledRenderers + "/" + renderers.Count);
        if (colliders.Count != 39 || result.DisabledColliders != 39)
            result.Failures.Add("V10 transition collider state drifted: " + result.DisabledColliders + "/" + colliders.Count);

        foreach (var transition in manifest.Transitions)
        {
            var target = ChannelPlayKhufuV10InteriorBuilder.ResolvePath(map, transition.Path);
            var renderer = target == null ? null : target.GetComponent<Renderer>();
            if (renderer == null || BoundsDelta(renderer.bounds, new Bounds(transition.BoundsCenter, transition.BoundsSize)) > MarkerTolerance)
                result.Failures.Add("V10 transition bounds drifted: " + transition.Path);
        }
        foreach (var marker in manifest.Markers)
        {
            var target = ChannelPlayKhufuV10InteriorBuilder.ResolvePath(map, marker.Path);
            if (target == null || Vector3.Distance(target.position, marker.Position) > MarkerTolerance)
                result.Failures.Add("V4 frozen marker drifted: " + marker.Name);
        }
    }

    private static void ValidateLegacyOwnership(Transform map, ValidationResult result)
    {
        var crown = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_KeyRoute_Crown");
        if (crown == null)
        {
            result.Failures.Add("V5 Crown ownership root missing");
        }
        else
        {
            result.CrownDependencies = crown.GetComponentsInChildren<Transform>(true).Length;
            if (result.CrownDependencies != 42) result.Failures.Add("V5 Crown dependency count drifted: " + result.CrownDependencies);
            if (crown.GetComponentsInChildren<Renderer>(true).Any(item => !item.enabled))
                result.Failures.Add("V5 Crown renderer state drifted");
            if (crown.GetComponentsInChildren<Collider>(true).Any(item => !item.enabled))
                result.Failures.Add("V5 Crown collider state drifted");
            var crownPath = HierarchyPath(map, crown) + "/";
            var manifest = ChannelPlayKhufuV10InteriorBuilder.LoadDisableManifest();
            result.CrownIntersection = manifest.Transitions.Count(item => item.Path.StartsWith(crownPath, StringComparison.Ordinal));
            if (result.CrownIntersection != 0) result.Failures.Add("V10 transitions intersect V5 Crown ownership");
        }

        var v8 = map.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.RootName);
        if (v8 == null)
        {
            result.Failures.Add("Frozen V8 root missing");
        }
        else
        {
            if (!Same(ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v8), Metrics(10, 33550, 27180, 0)))
                result.Failures.Add("Frozen V8 root metrics drifted");
            var v8Method = typeof(ChannelPlayKhufuV9CausewayFidelityValidator).GetMethod("ComputeV8Signature",
                BindingFlags.NonPublic | BindingFlags.Static);
            var v8Signature = v8Method == null ? string.Empty : v8Method.Invoke(null, new object[] { v8 }) as string;
            result.V8Signature = v8Signature ?? string.Empty;
            if (result.V8Signature != FrozenV8Signature)
                result.Failures.Add("Frozen V8 root signature drifted: " + result.V8Signature);
        }

        var v9 = map.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.RootName);
        if (v9 == null)
        {
            result.Failures.Add("Frozen V9 root missing");
            return;
        }
        if (!Same(ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v9), Metrics(5, 1512, 756, 23)))
            result.Failures.Add("Frozen V9 root metrics drifted");
        var method = typeof(ChannelPlayKhufuV9CausewayFidelityValidator).GetMethod("ComputeSignature", BindingFlags.NonPublic | BindingFlags.Static);
        var signature = method == null ? string.Empty : method.Invoke(null, new object[] { v9 }) as string;
        result.V9Signature = signature ?? string.Empty;
        if (result.V9Signature != FrozenV9Signature) result.Failures.Add("Frozen V9 root signature drifted: " + result.V9Signature);
    }

    private static void ValidateColliderEnvelope(Transform map, Transform root,
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, ValidationResult result)
    {
        var envelope = BoundsFromPoints(specs.SelectMany(SpecCorners));
        envelope.Expand(2f);
        foreach (var collider in map.GetComponentsInChildren<Collider>(true))
        {
            if (!collider.enabled || !collider.gameObject.activeInHierarchy || collider.isTrigger || !envelope.Intersects(collider.bounds)) continue;
            if (collider.transform.IsChildOf(root) || HasEnabledRenderer(collider.transform)) continue;
            result.OrphanLegacyColliders++;
            if (result.OrphanLegacyColliders <= 12)
                result.Failures.Add("Orphan legacy collider remains in V10 envelope: " + HierarchyPath(map, collider.transform));
        }
    }

    private static void ValidateRouteClearance(Transform map, ValidationResult result)
    {
        var route = ChannelPlayKhufuV10InteriorMeshPipeline.NormalRoute();
        var v10Root = map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName);
        var colliders = map.GetComponentsInChildren<Collider>(true)
            .Where(item => item.enabled && item.gameObject.activeInHierarchy && !item.isTrigger &&
                           !IsOwnedWalkableFloor(item, v10Root))
            .ToArray();
        var probeObject = new GameObject("V10_Clearance_Probe") { hideFlags = HideFlags.HideAndDontSave };
        var probe = probeObject.AddComponent<BoxCollider>();
        probe.size = new Vector3(ClearanceWidth, ClearanceHeight, 0.08f);
        var collisions = 0;
        try
        {
            for (var segment = 1; segment < route.Count; segment++)
            {
                var start = route[segment - 1];
                var end = route[segment];
                var delta = end - start;
                if (delta.sqrMagnitude < 0.0001f) continue;
                var rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
                var samples = Mathf.Max(2, Mathf.CeilToInt(delta.magnitude / 0.45f));
                for (var sample = 0; sample < samples; sample++)
                {
                    var t = (sample + 0.5f) / samples;
                    var floorPoint = Vector3.Lerp(start, end, t);
                    var position = floorPoint + rotation * Vector3.up * (ClearanceHeight * 0.5f + 0.03f);
                    result.ClearanceSamples++;
                    foreach (var collider in colliders)
                    {
                        if (Physics.ComputePenetration(probe, position, rotation, collider,
                                collider.transform.position, collider.transform.rotation, out _, out var distance) && distance > 0.005f)
                        {
                            collisions++;
                            var blockerPath = HierarchyPath(map, collider.transform);
                            var blockerKey = "segment=" + (segment - 1) + " | " + blockerPath;
                            if (!result.ClearanceBlockers.ContainsKey(blockerKey)) result.ClearanceBlockers.Add(blockerKey, 0);
                            result.ClearanceBlockers[blockerKey]++;
                            if (collisions <= 12)
                                result.Failures.Add("V10 route clearance collision: segment=" + (segment - 1) +
                                                    " sample=" + sample + " collider=" + blockerPath);
                            break;
                        }
                    }
                }
            }
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(probeObject);
        }
        result.ClearanceCollisions = collisions;
        if (collisions > 12) result.Failures.Add("V10 route clearance collision count: " + collisions);
        if (result.ClearanceSamples < 100) result.Failures.Add("V10 route clearance sample count is too low: " + result.ClearanceSamples);
    }

    private static void ValidateGrandGalleryEnclosure(Transform root, ValidationResult result)
    {
        if (EnclosureDirections.Length != 24)
        {
            result.Failures.Add("V10 enclosure direction inventory drifted");
            return;
        }
        var collisionRoot = root.Find(ChannelPlayKhufuV10InteriorBuilder.CollisionRootName);
        if (collisionRoot == null)
        {
            result.Failures.Add("V10 collision root missing for enclosure gate");
            return;
        }
        var colliders = collisionRoot.GetComponentsInChildren<BoxCollider>(true).Where(item => item.enabled).ToArray();
        var frame = ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFrame();
        var start = ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFoot + frame.Forward * 2.8f;
        var end = ChannelPlayKhufuV10InteriorMeshPipeline.GreatStepStop();
        result.MinimumEnclosureRatio = 1f;
        for (var sample = 0; sample < 24; sample++)
        {
            var point = Vector3.Lerp(start, end, (sample + 0.5f) / 24f) + frame.Up * 1.7f;
            var hits = 0;
            var leftHit = false;
            var rightHit = false;
            var overheadHit = false;
            foreach (var local in EnclosureDirections)
            {
                var direction = (frame.Right * local.x + frame.Up * local.y + frame.Forward * local.z).normalized;
                var ray = new Ray(point, direction);
                var hit = colliders.Any(collider => collider.Raycast(ray, out _, EnclosureDistance));
                if (!hit) continue;
                hits++;
                if (local.x < -0.25f) leftHit = true;
                if (local.x > 0.25f) rightHit = true;
                if (local.y > 0.75f) overheadHit = true;
            }
            var ratio = hits / 24f;
            result.MinimumEnclosureRatio = Mathf.Min(result.MinimumEnclosureRatio, ratio);
            if (ratio + 0.0001f < MinimumEnclosureRatio || !leftHit || !rightHit || !overheadHit)
                result.Failures.Add("V10 Grand Gallery enclosure failed: sample=" + sample + " ratio=" +
                                    ratio.ToString("0.000", CultureInfo.InvariantCulture) + " left=" + leftHit +
                                    " right=" + rightHit + " overhead=" + overheadHit);
        }
    }

    private static void ValidateVisibleBudget(Transform map, ValidationResult result)
    {
        var visible = map.GetComponentsInChildren<Renderer>(true).Where(item => item.enabled && item.gameObject.activeInHierarchy).ToArray();
        result.VisibleRenderers = visible.Length;
        foreach (var renderer in visible)
        {
            var filter = renderer.GetComponent<MeshFilter>();
            var mesh = filter == null ? null : filter.sharedMesh;
            if (mesh == null) continue;
            result.VisibleVertices += mesh.vertexCount;
            result.VisibleTriangles += ChannelPlayKhufuV10InteriorMeshPipeline.TriangleCount(mesh);
        }
        if (result.VisibleRenderers > 819 || result.VisibleVertices > 100000 || result.VisibleTriangles > 80000)
            result.Failures.Add("V10 visible performance budget exceeded: renderers=" + result.VisibleRenderers +
                                " vertices=" + result.VisibleVertices + " triangles=" + result.VisibleTriangles);
    }

    private static void ValidateForbiddenComponents(Transform root, ValidationResult result)
    {
        if (root.GetComponentsInChildren<MeshCollider>(true).Length != 0) result.Failures.Add("V10 root contains MeshCollider");
        if (root.GetComponentsInChildren<Rigidbody>(true).Length != 0) result.Failures.Add("V10 root contains Rigidbody");
        if (root.GetComponentsInChildren<Camera>(true).Length != 0) result.Failures.Add("V10 root contains Camera");
    }

    private static ValidationResult Finish(ValidationResult result, Transform root)
    {
        result.Signature = root == null ? string.Empty : ComputeSignature(root);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static string ComputeSignature(Transform root)
    {
        var text = new StringBuilder(ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(root));
        foreach (var binding in GeneratedAssetBindings()) text.AppendLine(binding);
        foreach (var tag in root.GetComponentsInChildren<KhufuV10SegmentTag>(true)
                     .OrderBy(item => HierarchyPath(root, item.transform), StringComparer.Ordinal))
            text.AppendLine(HierarchyPath(root, tag.transform) + "|" + tag.TruthClass + "|" +
                            string.Join(",", tag.SegmentIds) + "|" + tag.FactualShape + "|" + tag.GameplayScale);
        return Sha256Text(text.ToString());
    }

    private static List<string> GeneratedAssetBindings()
    {
        var paths = new List<string>();
        foreach (var bucket in ChannelPlayKhufuV10InteriorMeshPipeline.Buckets)
            paths.Add(ChannelPlayKhufuV10InteriorMeshPipeline.GeneratedRoot + "/KhufuV10_" + bucket + ".asset");
        foreach (var material in ExpectedMaterials.Values)
            paths.Add(ChannelPlayKhufuV10InteriorBuilder.MaterialRoot + "/" + material + ".mat");
        return paths.OrderBy(item => item, StringComparer.Ordinal)
            .SelectMany(path => new[] { path, path + ".meta" })
            .Select(path => path + "|guid=" + AssetDatabase.AssetPathToGUID(path.EndsWith(".meta", StringComparison.Ordinal) ?
                    path.Substring(0, path.Length - 5) : path) + "|sha256=" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path))
            .ToList();
    }

    private static bool MeshContainsSpec(Mesh mesh, ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec spec)
    {
        var vertices = mesh.vertices;
        return SpecCorners(spec).All(corner => vertices.Any(vertex => Vector3.Distance(vertex, corner) <= PairTolerance));
    }

    private static IEnumerable<Vector3> SpecCorners(ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec spec)
    {
        var half = spec.Scale * 0.5f;
        for (var x = -1; x <= 1; x += 2)
        for (var y = -1; y <= 1; y += 2)
        for (var z = -1; z <= 1; z += 2)
            yield return spec.Position + spec.Rotation * Vector3.Scale(half, new Vector3(x, y, z));
    }

    private static Bounds BoundsForTransform(Transform target)
    {
        var half = target.localScale * 0.5f;
        var points = new List<Vector3>();
        for (var x = -1; x <= 1; x += 2)
        for (var y = -1; y <= 1; y += 2)
        for (var z = -1; z <= 1; z += 2)
            points.Add(target.position + target.rotation * Vector3.Scale(half, new Vector3(x, y, z)));
        return BoundsFromPoints(points);
    }

    private static Bounds BoundsFromPoints(IEnumerable<Vector3> source)
    {
        var points = source.ToArray();
        if (points.Length == 0) return new Bounds();
        var bounds = new Bounds(points[0], Vector3.zero);
        foreach (var point in points.Skip(1)) bounds.Encapsulate(point);
        return bounds;
    }

    private static float BoundsDelta(Bounds left, Bounds right)
    {
        return Mathf.Max(MaxComponentDelta(left.center, right.center), MaxComponentDelta(left.size, right.size));
    }

    private static float MaxComponentDelta(Vector3 left, Vector3 right)
    {
        var delta = left - right;
        return Mathf.Max(Mathf.Abs(delta.x), Mathf.Abs(delta.y), Mathf.Abs(delta.z));
    }

    private static bool TransformMatches(Transform target, Vector3 position, Quaternion rotation, Vector3 scale)
    {
        return Vector3.Distance(target.position, position) <= PairTolerance &&
               Quaternion.Angle(target.rotation, rotation) <= 0.05f &&
               MaxComponentDelta(target.localScale, scale) <= PairTolerance;
    }

    private static bool HasEnabledRenderer(Transform target)
    {
        var renderer = target.GetComponent<Renderer>();
        return renderer != null && renderer.enabled && renderer.gameObject.activeInHierarchy;
    }

    private static bool IsOwnedWalkableFloor(Collider collider, Transform v10Root)
    {
        if (v10Root == null || !collider.transform.IsChildOf(v10Root)) return false;
        return collider.name.EndsWith("_Floor", StringComparison.Ordinal) ||
               collider.name.EndsWith("Gallery_Floor_Ramp", StringComparison.Ordinal);
    }

    private static void ExpectCount(IEnumerable<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs,
        string token, int expected, ValidationResult result)
    {
        var actual = specs.Count(item => item.Name.StartsWith(token, StringComparison.Ordinal));
        if (actual != expected) result.Failures.Add("V10 evidence count drifted: " + token + " expected=" + expected + " actual=" + actual);
    }

    private static Transform FindRoot()
    {
        var map = GameObject.Find(ChannelPlayKhufuV10InteriorBuilder.MapRootName);
        return map == null ? null : map.transform.Find(ChannelPlayKhufuV10InteriorBuilder.RootName);
    }

    private static string HierarchyPath(Transform root, Transform node)
    {
        var names = new Stack<string>();
        var cursor = node;
        while (cursor != null && cursor != root)
        {
            names.Push(cursor.name);
            cursor = cursor.parent;
        }
        return string.Join("/", names);
    }

    private static void WriteValidation(ValidationResult result)
    {
        var text = new StringBuilder("# Khufu V10 Interior Spine Validation\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Root metrics: `" + MetricsToken(result.RootMetrics) + "`");
        text.AppendLine("- Map metrics: `" + MetricsToken(result.MapMetrics) + "`");
        text.AppendLine("- Visible metrics: `renderers=" + result.VisibleRenderers + "_vertices=" + result.VisibleVertices +
                        "_triangles=" + result.VisibleTriangles + "`");
        text.AppendLine("- Exact transitions: `renderers=" + result.DisabledRenderers + "_colliders=" + result.DisabledColliders + "`");
        text.AppendLine("- Clearance: `samples=" + result.ClearanceSamples + "_collisions=" + result.ClearanceCollisions + "`");
        text.AppendLine("- Grand Gallery minimum enclosure ratio: `" + result.MinimumEnclosureRatio.ToString("0.000", CultureInfo.InvariantCulture) + "`");
        text.AppendLine("- Orphan legacy colliders in V10 envelope: `" + result.OrphanLegacyColliders + "`");
        text.AppendLine("- V5 Crown: `dependencies=" + result.CrownDependencies + "_intersection=" + result.CrownIntersection + "`");
        text.AppendLine("- Frozen V8 signature: `" + result.V8Signature + "`");
        text.AppendLine("- Frozen V9 signature: `" + result.V9Signature + "`");
        text.AppendLine("- V10 signature: `" + result.Signature + "`");
        if (result.ClearanceBlockers.Count > 0)
        {
            text.AppendLine();
            text.AppendLine("## Clearance Blocker Histogram");
            text.AppendLine();
            foreach (var blocker in result.ClearanceBlockers.OrderByDescending(item => item.Value).ThenBy(item => item.Key, StringComparer.Ordinal))
                text.AppendLine("- `" + blocker.Value + "`: `" + blocker.Key + "`");
        }
        foreach (var failure in result.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V10_STATIC_VALIDATION: " + (result.Passed ? "passed" : "failed"));
        File.WriteAllText(RunPath("validation.md"), text.ToString());
    }

    private static void WritePostwriteAudit(ValidationResult result)
    {
        var passed = result.DisabledRenderers == 60 && result.DisabledColliders == 39 &&
                     result.CrownDependencies == 42 && result.CrownIntersection == 0;
        var text = new StringBuilder("# Khufu V10 Post-Write Ownership Audit\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Renderer transitions applied: `" + result.DisabledRenderers + "/60`");
        text.AppendLine("- Collider transitions applied: `" + result.DisabledColliders + "/39`");
        text.AppendLine("- V5 Crown dependencies preserved: `" + result.CrownDependencies + "/42`");
        text.AppendLine("- V5 Crown intersection: `" + result.CrownIntersection + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V10_POSTWRITE_AUDIT: " + (passed ? "passed" : "failed"));
        File.WriteAllText(RunPath("postwrite-audit.md"), text.ToString());
    }

    private static void WriteMutation(string filename, string mutation, IEnumerable<string> failures, bool rejected, string token)
    {
        var text = new StringBuilder("# Khufu V10 Mutation Gate\n\n");
        text.AppendLine("- Mutation: `" + mutation + "`");
        text.AppendLine("- Rejected: **" + rejected.ToString().ToLowerInvariant() + "**");
        foreach (var failure in failures) text.AppendLine("- Observed failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine(token + ": " + (rejected ? "passed" : "failed"));
        File.WriteAllText(RunPath(filename), text.ToString());
    }

    private static string RunPath(string filename)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV10InteriorBuilder.RunRoot);
        return ChannelPlayKhufuV10InteriorBuilder.RunRoot + "/" + filename;
    }

    private static ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Metrics(int renderers, int vertices, int triangles, int colliders)
    {
        return new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics
        {
            Renderers = renderers,
            Vertices = vertices,
            Triangles = triangles,
            Colliders = colliders
        };
    }

    private static bool Same(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics left,
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics right)
    {
        return left.Renderers == right.Renderers && left.Vertices == right.Vertices &&
               left.Triangles == right.Triangles && left.Colliders == right.Colliders;
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("0.###", CultureInfo.InvariantCulture) + ", " +
               value.y.ToString("0.###", CultureInfo.InvariantCulture) + ", " +
               value.z.ToString("0.###", CultureInfo.InvariantCulture);
    }

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create())
            return string.Concat(sha.ComputeHash(Encoding.UTF8.GetBytes(value)).Select(item => item.ToString("x2")));
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public string Signature = string.Empty;
        public string V8Signature = string.Empty;
        public string V9Signature = string.Empty;
        public int DisabledRenderers;
        public int DisabledColliders;
        public int CrownDependencies;
        public int CrownIntersection;
        public int OrphanLegacyColliders;
        public int ClearanceSamples;
        public int ClearanceCollisions;
        public float MinimumEnclosureRatio;
        public int VisibleRenderers;
        public int VisibleVertices;
        public int VisibleTriangles;
        public readonly Dictionary<string, int> ClearanceBlockers = new Dictionary<string, int>(StringComparer.Ordinal);
        public readonly List<string> Failures = new List<string>();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics RootMetrics = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics MapMetrics = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
    }
}

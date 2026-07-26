using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV11RoyalCircuitValidator
{
    private const float TransformTolerance = 0.001f;
    private const float ClearanceRadius = 0.32f;

    [MenuItem("Channel Play/Khufu V11/Validate Royal Circuit")]
    public static void ValidateMenu()
    {
        var result = ValidateScene();
        WriteValidation(result);
        if (result.Failures.Count > 0)
            throw new InvalidOperationException("V11 validation failed: " + string.Join(" | ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V11_STATIC_VALIDATION result=passed signature=" + result.Signature);
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

    [MenuItem("Channel Play/Khufu V11/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV11RoyalCircuitBuilder.RunRoot);
        var frozenSourcesBefore = FrozenV10SourceSignature();
        ChannelPlayKhufuV11RoyalCircuitBuilder.Rebuild();
        var firstScene = Sha256File(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath);
        var firstAssets = GeneratedAssetSignature();
        ChannelPlayKhufuV11RoyalCircuitBuilder.Rebuild();
        var secondScene = Sha256File(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath);
        var secondAssets = GeneratedAssetSignature();
        var frozenSourcesAfter = FrozenV10SourceSignature();
        var passed = firstScene == secondScene && firstAssets == secondAssets &&
                     frozenSourcesBefore == frozenSourcesAfter;
        File.WriteAllText(RunPath("idempotence.md"),
            "# Khufu V11 Idempotence\n\n" +
            "- Verdict: **" + (passed ? "passed" : "failed") + "**\n" +
            "- First scene SHA-256: `" + firstScene + "`\n" +
            "- Second scene SHA-256: `" + secondScene + "`\n" +
            "- First generated signature: `" + firstAssets + "`\n" +
            "- Second generated signature: `" + secondAssets + "`\n\n" +
            "- Frozen V10 source signature before: `" + frozenSourcesBefore + "`\n" +
            "- Frozen V10 source signature after: `" + frozenSourcesAfter + "`\n\n" +
            "KHUFU_V11_IDEMPOTENCE: " + (passed ? "passed" : "failed") + "\n");
        if (!passed) throw new InvalidOperationException("V11 rebuild is not idempotent.");
        Debug.Log("CHANNEL_PLAY_KHUFU_V11_IDEMPOTENCE result=passed");
    }

    public static void ValidateIdempotenceBatch()
    {
        try
        {
            ValidateIdempotence();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    [MenuItem("Channel Play/Khufu V11/Validate Negative Controls")]
    public static void ValidateNegativeControls()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV11RoyalCircuitBuilder.RunRoot);
        var scene = EditorSceneManager.OpenScene(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName).transform;
        var root = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.RootName);
        if (root == null) throw new InvalidOperationException("V11 root is missing.");
        var v10 = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10RootName);
        var blocker = v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath).GetComponent<BoxCollider>();
        var limestoneFilter = v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath)
            .GetComponent<MeshFilter>();
        var pairTarget = root.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.CollisionRootName)
            .Cast<Transform>().First(item => item.name.Contains("Kings_Chamber_Floor"));
        var displayFilter = root.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.VisualRootName + "/V11_" +
                                      ChannelPlayKhufuV11RoyalCircuitMeshPipeline.DisplayBucket)
            .GetComponent<MeshFilter>();
        if (blocker == null || limestoneFilter == null || displayFilter == null)
            throw new InvalidOperationException("V11 negative-control targets are incomplete.");

        var originalLimestone = limestoneFilter.sharedMesh;
        var originalPairPosition = pairTarget.localPosition;
        var originalBlockerState = blocker.enabled;
        var originalDisplay = displayFilter.sharedMesh;
        Mesh reducedDisplay = null;
        GameObject externalBlocker = null;
        var closedBindingRejected = false;
        var pairRejected = false;
        var blockerRejected = false;
        var externalBlockerRejected = false;
        var displayLevelRejected = false;
        try
        {
            limestoneFilter.sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(
                ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedLimestonePath);
            closedBindingRejected = ValidateScene(false).Failures.Any(item =>
                item.Contains("binding", StringComparison.OrdinalIgnoreCase));
            limestoneFilter.sharedMesh = originalLimestone;

            pairTarget.localPosition += Vector3.right * 0.5f;
            Physics.SyncTransforms();
            pairRejected = ValidateScene(false).Failures.Any(item =>
                item.Contains("pair", StringComparison.OrdinalIgnoreCase));
            pairTarget.localPosition = originalPairPosition;

            blocker.enabled = true;
            Physics.SyncTransforms();
            var blockerResult = ValidateScene(false);
            blockerRejected = blockerResult.ClearanceBlockers.Contains("Great Step blocker") &&
                              blockerResult.Failures.Any(item =>
                                  item.Contains("clearance", StringComparison.OrdinalIgnoreCase));
            blocker.enabled = originalBlockerState;

            externalBlocker = new GameObject("V11_Negative_Control_External_Map_Blocker");
            externalBlocker.transform.SetParent(map, false);
            externalBlocker.transform.localPosition = Vector3.Lerp(
                KhufuV11RoyalRouteContract.RoyalThreshold, KhufuV11RoyalRouteContract.EntryEnd, 0.5f) +
                                                      Vector3.up * 1.2f;
            var externalCollider = externalBlocker.AddComponent<BoxCollider>();
            externalCollider.size = new Vector3(0.9f, 2.4f, 0.9f);
            Physics.SyncTransforms();
            var externalResult = ValidateScene(false);
            externalBlockerRejected = externalResult.ClearanceBlockers.Any(item =>
                                          item.Contains(externalBlocker.name, StringComparison.Ordinal)) &&
                                      externalResult.Failures.Any(item =>
                                          item.Contains("clearance", StringComparison.OrdinalIgnoreCase));
            UnityEngine.Object.DestroyImmediate(externalBlocker);
            externalBlocker = null;

            var reducedSpecs = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildSpecs()
                .Where(item => item.Bucket != ChannelPlayKhufuV11RoyalCircuitMeshPipeline.DisplayBucket ||
                               !item.Name.StartsWith("Display_Level_05_", StringComparison.Ordinal))
                .ToArray();
            reducedDisplay = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildTransientMesh(reducedSpecs,
                ChannelPlayKhufuV11RoyalCircuitMeshPipeline.DisplayBucket, "Negative_Control_Missing_Display_Level");
            displayFilter.sharedMesh = reducedDisplay;
            displayLevelRejected = ValidateScene(false).Failures.Any(item =>
                item.Contains("visual geometry", StringComparison.OrdinalIgnoreCase));
        }
        finally
        {
            limestoneFilter.sharedMesh = originalLimestone;
            pairTarget.localPosition = originalPairPosition;
            blocker.enabled = originalBlockerState;
            displayFilter.sharedMesh = originalDisplay;
            if (externalBlocker != null) UnityEngine.Object.DestroyImmediate(externalBlocker);
            if (reducedDisplay != null) UnityEngine.Object.DestroyImmediate(reducedDisplay);
            Physics.SyncTransforms();
            EditorSceneManager.OpenScene(scene.path, OpenSceneMode.Single);
        }

        var rollbackRestored = ValidateRollbackNegativeControl();
        var passed = closedBindingRejected && pairRejected && blockerRejected && externalBlockerRejected &&
                     displayLevelRejected && rollbackRestored;
        File.WriteAllText(RunPath("negative-controls.md"),
            "# Khufu V11 Negative Controls\n\n" +
            "- Closed V10 renderer binding rejected: `" + closedBindingRejected.ToString().ToLowerInvariant() + "`\n" +
            "- Structural-pair mutation rejected: `" + pairRejected.ToString().ToLowerInvariant() + "`\n" +
            "- Great Step blocker mutation rejected: `" + blockerRejected.ToString().ToLowerInvariant() + "`\n" +
            "- External map blocker rejected by clearance: `" + externalBlockerRejected.ToString().ToLowerInvariant() + "`\n" +
            "- Missing stacked display level rejected: `" + displayLevelRejected.ToString().ToLowerInvariant() + "`\n\n" +
            "- Injected transition failure rolled back: `" + rollbackRestored.ToString().ToLowerInvariant() + "`\n\n" +
            "KHUFU_V11_NEGATIVE_CONTROLS: " + (passed ? "passed" : "failed") + "\n");
        if (!passed) throw new InvalidOperationException("V11 negative controls were not rejected.");
        Debug.Log("CHANNEL_PLAY_KHUFU_V11_NEGATIVE_CONTROLS result=passed");
    }

    private static bool ValidateRollbackNegativeControl()
    {
        var rejected = false;
        ChannelPlayKhufuV11RoyalCircuitBuilder.InjectFailureAfterClosedBindingsForValidation = true;
        try
        {
            ChannelPlayKhufuV11RoyalCircuitBuilder.Rebuild();
        }
        catch (InvalidOperationException exception)
        {
            rejected = exception.Message.Contains("Injected V11 transition failure", StringComparison.Ordinal);
        }
        finally
        {
            ChannelPlayKhufuV11RoyalCircuitBuilder.InjectFailureAfterClosedBindingsForValidation = false;
        }

        EditorSceneManager.OpenScene(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName);
        var v10 = mapObject == null
            ? null
            : mapObject.transform.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10RootName);
        if (v10 == null) return false;
        var limestone = v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath)
            ?.GetComponent<MeshFilter>();
        var granite = v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath)
            ?.GetComponent<MeshFilter>();
        var blocker = v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath)
            ?.GetComponent<BoxCollider>();
        return rejected && limestone != null && granite != null && blocker != null && !blocker.enabled &&
               AssetDatabase.GetAssetPath(limestone.sharedMesh) ==
               ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath &&
               AssetDatabase.GetAssetPath(granite.sharedMesh) ==
               ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath;
    }

    public static void ValidateNegativeControlsBatch()
    {
        try
        {
            ValidateNegativeControls();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static ValidationResult ValidateScene(bool reopen = true)
    {
        if (reopen)
            EditorSceneManager.OpenScene(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var result = new ValidationResult();
        var mapObject = GameObject.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName);
        if (mapObject == null)
        {
            result.Failures.Add("Shared map root is missing.");
            return result;
        }
        var map = mapObject.transform;
        var root = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.RootName);
        if (root == null)
        {
            result.Failures.Add("V11 root is missing.");
            return result;
        }

        var classification = ChannelPlayKhufuV11RoyalCircuitBuilder.LoadClassification();
        var budget = ChannelPlayKhufuV11RoyalCircuitBuilder.LoadPerformanceBudget();
        var specs = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildSpecs();
        ValidateIdentity(root, result);
        ValidateBindings(map, result);
        ValidateVisuals(root, specs, classification, result);
        ValidateStructuralPairs(root, specs, result);
        ValidateSemanticGeometry(specs, result);
        ValidatePyramidEnvelope(specs, result);
        ValidateClearance(map, root, result);
        ValidateEnclosure(map, root, result);
        ValidateForbiddenComponents(root, result);

        result.RootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        result.MapMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (result.RootMetrics.Renderers > budget.root.renderers_max ||
            result.RootMetrics.Vertices > budget.root.vertices_max ||
            result.RootMetrics.Triangles > budget.root.triangles_max ||
            result.RootMetrics.Colliders > budget.root.colliders_max)
            result.Failures.Add("V11 root performance budget exceeded: " + MetricsToken(result.RootMetrics));
        if (result.MapMetrics.Renderers > budget.map.renderers_max ||
            result.MapMetrics.Colliders > budget.map.colliders_max)
            result.Failures.Add("V11 map performance budget exceeded: " + MetricsToken(result.MapMetrics));

        result.Signature = ComputeSignature(root, map);
        return result;
    }

    private static void ValidateIdentity(Transform root, ValidationResult result)
    {
        if (root.localPosition != Vector3.zero || root.localRotation != Quaternion.identity || root.localScale != Vector3.one)
            result.Failures.Add("V11 root transform is not identity.");
        var expected = new HashSet<string>(new[]
        {
            ChannelPlayKhufuV11RoyalCircuitBuilder.VisualRootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.PairRootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.CollisionRootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.MetadataRootName
        }, StringComparer.Ordinal);
        var actual = new HashSet<string>(root.Cast<Transform>().Select(item => item.name), StringComparer.Ordinal);
        if (!expected.SetEquals(actual)) result.Failures.Add("V11 root child set drifted.");
    }

    private static void ValidateBindings(Transform map, ValidationResult result)
    {
        var v10 = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10RootName);
        if (v10 == null)
        {
            result.Failures.Add("V10 dependency root is missing.");
            return;
        }
        ExpectMesh(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath, result);
        ExpectMesh(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath, result);
        var blockerTarget = v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath);
        var blocker = blockerTarget == null ? null : blockerTarget.GetComponent<BoxCollider>();
        if (blocker == null || blocker.enabled) result.Failures.Add("V10 Great Step blocker is not disabled.");

        try
        {
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ValidateV10TransitionAssets();
        }
        catch (Exception exception)
        {
            result.Failures.Add("V10 transition asset integrity failed: " + exception.Message);
        }
    }

    private static void ExpectMesh(Transform root, string relativePath, string expectedPath, ValidationResult result)
    {
        var target = root.Find(relativePath);
        var filter = target == null ? null : target.GetComponent<MeshFilter>();
        var actual = filter == null || filter.sharedMesh == null ? string.Empty : AssetDatabase.GetAssetPath(filter.sharedMesh);
        if (actual != expectedPath)
            result.Failures.Add("V10 open mesh binding mismatch: " + relativePath + " actual=" + actual);
    }

    private static void ValidateVisuals(Transform root,
        IReadOnlyList<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec> specs,
        ChannelPlayKhufuV11RoyalCircuitBuilder.SegmentClassificationDocument classification,
        ValidationResult result)
    {
        var visuals = root.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.VisualRootName);
        if (visuals == null)
        {
            result.Failures.Add("V11 visuals root is missing.");
            return;
        }
        var children = visuals.Cast<Transform>().ToArray();
        if (children.Length != ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ExpectedRendererCount)
            result.Failures.Add("V11 visual renderer count drifted: " + children.Length);
        foreach (var bucket in ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Buckets)
        {
            var target = visuals.Find("V11_" + bucket);
            if (target == null)
            {
                result.Failures.Add("V11 visual bucket is missing: " + bucket);
                continue;
            }
            var filter = target.GetComponent<MeshFilter>();
            var renderer = target.GetComponent<MeshRenderer>();
            if (filter == null || filter.sharedMesh == null || renderer == null || !renderer.enabled ||
                renderer.sharedMaterial == null)
            {
                result.Failures.Add("V11 visual binding is incomplete: " + bucket);
                continue;
            }
            var expectedMesh = ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BuildTransientMesh(specs, bucket,
                "Expected_V11_" + bucket);
            try
            {
                if (ChannelPlayKhufuV11RoyalCircuitMeshPipeline.GeometrySignature(filter.sharedMesh) !=
                    ChannelPlayKhufuV11RoyalCircuitMeshPipeline.GeometrySignature(expectedMesh))
                    result.Failures.Add("V11 visual geometry drifted: " + bucket);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(expectedMesh);
            }
            var tag = target.GetComponent<KhufuV11SegmentTag>();
            var expectedSegments = specs.Where(item => item.Bucket == bucket)
                .Select(item => item.SegmentId).Distinct(StringComparer.Ordinal).OrderBy(item => item).ToArray();
            if (tag == null || !expectedSegments.SequenceEqual(tag.SegmentIds.OrderBy(item => item)))
                result.Failures.Add("V11 visual classification drifted: " + bucket);
        }
        var classified = new HashSet<string>(classification.segments.Select(item => item.id), StringComparer.Ordinal);
        if (!classified.SetEquals(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.Segments))
            result.Failures.Add("V11 classification segment set drifted.");
    }

    private static void ValidateStructuralPairs(Transform root,
        IReadOnlyList<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        var pairs = root.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.PairRootName);
        var proxies = root.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.CollisionRootName);
        if (pairs == null || proxies == null)
        {
            result.Failures.Add("V11 pair/proxy roots are missing.");
            return;
        }

        var expected = specs.Where(item => item.Structural && item.Collider).ToArray();
        if (pairs.childCount != expected.Length || proxies.childCount != expected.Length)
            result.Failures.Add("V11 structural pair count drifted.");
        foreach (var spec in expected)
        {
            var pair = pairs.Find("V11_PAIR_" + spec.SegmentId + "_" + spec.Name);
            var proxy = proxies.Find("V11_PROXY_" + spec.SegmentId + "_" + spec.Name);
            if (pair == null || proxy == null)
            {
                result.Failures.Add("V11 pair/proxy missing: " + spec.Name);
                continue;
            }
            if (!TransformMatches(pair, spec) || !TransformMatches(proxy, spec))
                result.Failures.Add("V11 structural pair transform mismatch: " + spec.Name);
            var collider = proxy.GetComponent<BoxCollider>();
            if (collider == null || !collider.enabled || collider.isTrigger ||
                Vector3.Distance(collider.center, Vector3.zero) > TransformTolerance ||
                Vector3.Distance(collider.size, Vector3.one) > TransformTolerance)
                result.Failures.Add("V11 structural pair collider mismatch: " + spec.Name);
        }
    }

    private static bool TransformMatches(Transform target,
        ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec spec)
    {
        return Vector3.Distance(target.localPosition, spec.Position) <= TransformTolerance &&
               Quaternion.Angle(target.localRotation, spec.Rotation) <= TransformTolerance &&
               Vector3.Distance(target.localScale, spec.Scale) <= TransformTolerance;
    }

    private static void ValidateSemanticGeometry(
        IReadOnlyList<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        ExpectCount(specs, item => item.Name.StartsWith("Portcullis_Raised_Slab_", StringComparison.Ordinal), 3,
            "portcullis positions", result);
        ExpectCount(specs, item => item.Name.StartsWith("Kings_Ceiling_Beam_", StringComparison.Ordinal), 9,
            "King's Chamber ceiling beams", result);
        ExpectCount(specs, item => item.Name.StartsWith("Display_Level_", StringComparison.Ordinal) &&
                                   item.Name.EndsWith("_Beam", StringComparison.Ordinal), 5,
            "stacked display levels", result);
        ExpectCount(specs, item => item.SegmentId == ChannelPlayKhufuV11RoyalCircuitMeshPipeline.ShaftSegment &&
                                  item.Name.EndsWith("_Recess", StringComparison.Ordinal), 2,
            "shaft boundary recesses", result);
        ExpectCount(specs, item => item.SegmentId == ChannelPlayKhufuV11RoyalCircuitMeshPipeline.SarcophagusSegment, 6,
            "sarcophagus parts", result);
        if (!specs.Any(item => item.Name == "Display_Gabled_Cap_West") ||
            !specs.Any(item => item.Name == "Display_Gabled_Cap_East"))
            result.Failures.Add("V11 stacked display gabled cap is incomplete.");
    }

    private static void ExpectCount(IEnumerable<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec> specs,
        Func<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec, bool> predicate,
        int expected, string label, ValidationResult result)
    {
        var actual = specs.Count(predicate);
        if (actual != expected) result.Failures.Add("V11 " + label + " count drifted: " + actual);
    }

    private static void ValidatePyramidEnvelope(
        IEnumerable<ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        const float halfBase = 28f;
        const float height = 35.636f;
        const float tolerance = 0.12f;
        foreach (var spec in specs)
        foreach (var corner in SpecCorners(spec))
        {
            var halfWidth = halfBase * (1f - Mathf.Clamp01(corner.y / height));
            if (Mathf.Abs(corner.x) <= halfWidth + tolerance && Mathf.Abs(corner.z) <= halfWidth + tolerance)
                continue;
            result.Failures.Add("V11 pyramid envelope exceeded: " + spec.Name + " corner=" + VectorToken(corner));
            break;
        }
    }

    private static IEnumerable<Vector3> SpecCorners(
        ChannelPlayKhufuV11RoyalCircuitMeshPipeline.BoxSpec spec)
    {
        var half = spec.Scale * 0.5f;
        for (var x = -1; x <= 1; x += 2)
        for (var y = -1; y <= 1; y += 2)
        for (var z = -1; z <= 1; z += 2)
            yield return spec.Position + spec.Rotation * new Vector3(half.x * x, half.y * y, half.z * z);
    }

    private static void ValidateClearance(Transform map, Transform root, ValidationResult result)
    {
        Physics.SyncTransforms();
        var route = KhufuV11RoyalRouteContract.TraversalRoute();
        var v10 = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10RootName);
        var mapColliders = new HashSet<Collider>(map.GetComponentsInChildren<Collider>(true));
        var blockerTarget = v10 == null
            ? null
            : v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath);
        var blocker = blockerTarget == null ? null : blockerTarget.GetComponent<Collider>();
        for (var segment = 1; segment < route.Count; segment++)
        {
            for (var sample = 0; sample <= 12; sample++)
            {
                var point = Vector3.Lerp(route[segment - 1], route[segment], sample / 12f);
                var bottom = point + Vector3.up * 0.58f;
                var top = point + Vector3.up * 2.05f;
                var hits = Physics.OverlapCapsule(bottom, top, ClearanceRadius, ~0,
                    QueryTriggerInteraction.Ignore);
                result.ClearanceSamples++;
                foreach (var hit in hits)
                {
                    if (!mapColliders.Contains(hit) || !hit.enabled || hit.isTrigger) continue;
                    if (hit == blocker)
                    {
                        result.ClearanceBlockers.Add("Great Step blocker");
                        continue;
                    }
                    if (hit.bounds.max.y <= point.y + 0.30f) continue;
                    result.ClearanceBlockers.Add(HierarchyPath(map, hit.transform));
                }
            }
        }
        if (result.ClearanceBlockers.Count > 0)
            result.Failures.Add("V11 route clearance has blockers: " +
                                string.Join(",", result.ClearanceBlockers.OrderBy(item => item).Take(8)));
    }

    private static void ValidateEnclosure(Transform map, Transform root, ValidationResult result)
    {
        Physics.SyncTransforms();
        var v11Colliders = new HashSet<Collider>(root.GetComponentsInChildren<Collider>(true));
        var samples = new[]
        {
            EnclosureSample.Passage("great-step",
                KhufuV11RoyalRouteContract.GreatStepEntry, KhufuV11RoyalRouteContract.RoyalThreshold, 2.2f, 2.1f),
            EnclosureSample.Passage("royal-entry",
                KhufuV11RoyalRouteContract.RoyalThreshold, KhufuV11RoyalRouteContract.EntryEnd, 2.2f, 2.1f),
            EnclosureSample.Room("antechamber", KhufuV11RoyalRouteContract.AntechamberCenter,
                KhufuV11RoyalRouteContract.Rotation, 2.4f, 2.5f, false),
            EnclosureSample.Room("kings-chamber", KhufuV11RoyalRouteContract.KingsChamberCenter,
                KhufuV11RoyalRouteContract.Rotation, 5.3f, 3.8f, true)
        };

        foreach (var sample in samples)
        {
            var origin = sample.Position + sample.Up * 1.55f;
            ValidateBoundaryRay(origin, sample.Right, sample.SideDistance, "Wall", sample.Name + ":right",
                v11Colliders, result);
            ValidateBoundaryRay(origin, -sample.Right, sample.SideDistance, "Wall", sample.Name + ":left",
                v11Colliders, result);
            ValidateBoundaryRay(origin, sample.Up, sample.CeilingDistance, "Ceiling", sample.Name + ":ceiling",
                v11Colliders, result);
            if (sample.RequireForwardWall)
                ValidateBoundaryRay(origin, sample.Forward, 3.5f, "South_Wall", sample.Name + ":south-wall",
                    v11Colliders, result);
        }

        if (result.EnclosureMisses.Count > 0)
            result.Failures.Add("V11 route enclosure has gaps: " +
                                string.Join(",", result.EnclosureMisses.OrderBy(item => item)));
    }

    private static void ValidateBoundaryRay(Vector3 origin, Vector3 direction, float distance, string expectedToken,
        string label, HashSet<Collider> v11Colliders, ValidationResult result)
    {
        result.EnclosureSamples++;
        var hit = Physics.RaycastAll(origin, direction.normalized, distance, ~0, QueryTriggerInteraction.Ignore)
            .Where(item => v11Colliders.Contains(item.collider) && item.collider.enabled)
            .OrderBy(item => item.distance)
            .FirstOrDefault();
        if (hit.collider == null || !hit.collider.name.Contains(expectedToken, StringComparison.Ordinal))
            result.EnclosureMisses.Add(label);
    }

    private static void ValidateForbiddenComponents(Transform root, ValidationResult result)
    {
        if (root.GetComponentsInChildren<Light>(true).Length > 0 ||
            root.GetComponentsInChildren<Camera>(true).Length > 0 ||
            root.GetComponentsInChildren<AudioSource>(true).Length > 0 ||
            root.GetComponentsInChildren<ParticleSystem>(true).Length > 0 ||
            root.GetComponentsInChildren<Animator>(true).Length > 0 ||
            root.GetComponentsInChildren<MeshCollider>(true).Length > 0)
            result.Failures.Add("V11 root contains a forbidden component.");
    }

    private static string ComputeSignature(Transform root, Transform map)
    {
        var lines = new List<string>();
        foreach (var target in root.GetComponentsInChildren<Transform>(true)
                     .OrderBy(item => HierarchyPath(root, item), StringComparer.Ordinal))
        {
            lines.Add(HierarchyPath(root, target) + "|" + VectorToken(target.localPosition) + "|" +
                      VectorToken(target.localEulerAngles) + "|" + VectorToken(target.localScale));
            var filter = target.GetComponent<MeshFilter>();
            if (filter != null && filter.sharedMesh != null)
                lines.Add("mesh|" + AssetDatabase.GetAssetPath(filter.sharedMesh) + "|" +
                          ChannelPlayKhufuV11RoyalCircuitMeshPipeline.GeometrySignature(filter.sharedMesh));
            var renderer = target.GetComponent<Renderer>();
            if (renderer != null && renderer.sharedMaterial != null)
                lines.Add("material|" + AssetDatabase.GetAssetPath(renderer.sharedMaterial));
            var collider = target.GetComponent<Collider>();
            if (collider != null) lines.Add("collider|" + collider.enabled + "|" + collider.GetType().Name);
        }
        var v10 = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10RootName);
        foreach (var path in new[]
                 {
                     ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath,
                     ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath
                 })
        {
            var mesh = v10.Find(path).GetComponent<MeshFilter>().sharedMesh;
            lines.Add("v10-binding|" + path + "|" + AssetDatabase.GetAssetPath(mesh));
        }
        return Sha256Text(string.Join("\n", lines));
    }

    private static string GeneratedAssetSignature()
    {
        var paths = AssetDatabase.FindAssets(string.Empty,
                new[] { ChannelPlayKhufuV11RoyalCircuitMeshPipeline.GeneratedRoot,
                        ChannelPlayKhufuV11RoyalCircuitBuilder.MaterialRoot })
            .Select(AssetDatabase.GUIDToAssetPath)
            .Where(File.Exists)
            .OrderBy(item => item, StringComparer.Ordinal)
            .ToArray();
        return Sha256Text(string.Join("\n", paths.Select(path => path + "|" + Sha256File(path))) + "\n" +
                          FrozenV10SourceSignature());
    }

    private static string HierarchyPath(Transform root, Transform node)
    {
        if (node == root) return root.name;
        var parts = new Stack<string>();
        var current = node;
        while (current != null && current != root)
        {
            parts.Push(current.name);
            current = current.parent;
        }
        return root.name + "/" + string.Join("/", parts);
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV11RoyalCircuitBuilder.RunRoot);
        var passed = result.Failures.Count == 0;
        var text = new StringBuilder();
        text.AppendLine("# Khufu V11 Royal Circuit Validation");
        text.AppendLine();
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Root metrics: `" + MetricsToken(result.RootMetrics) + "`");
        text.AppendLine("- Map metrics: `" + MetricsToken(result.MapMetrics) + "`");
        text.AppendLine("- Clearance samples: `" + result.ClearanceSamples + "`");
        text.AppendLine("- Clearance blockers: `" + result.ClearanceBlockers.Count + "`");
        text.AppendLine("- Enclosure rays: `" + result.EnclosureSamples + "`");
        text.AppendLine("- Enclosure misses: `" + result.EnclosureMisses.Count + "`");
        text.AppendLine("- V11 signature: `" + result.Signature + "`");
        if (result.Failures.Count > 0)
        {
            text.AppendLine();
            text.AppendLine("## Failures");
            foreach (var failure in result.Failures) text.AppendLine("- " + failure);
        }
        text.AppendLine();
        text.AppendLine("KHUFU_V11_STATIC_VALIDATION: " + (passed ? "passed" : "failed"));
        File.WriteAllText(RunPath("validation.md"), text.ToString());
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("F5") + "," + value.y.ToString("F5") + "," + value.z.ToString("F5");
    }

    private static string Sha256File(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
    }

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value)))
                .Replace("-", string.Empty).ToLowerInvariant();
    }

    private static string FrozenV10SourceSignature()
    {
        var paths = new[]
        {
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedLimestonePath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedLimestonePath + ".meta",
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedGranitePath,
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10ClosedGranitePath + ".meta"
        };
        return Sha256Text(string.Join("\n", paths.Select(path => path + "|" + Sha256File(path))));
    }

    private static string RunPath(string filename)
    {
        return ChannelPlayKhufuV11RoyalCircuitBuilder.RunRoot + "/" + filename;
    }

    private sealed class ValidationResult
    {
        public readonly List<string> Failures = new List<string>();
        public readonly HashSet<string> ClearanceBlockers = new HashSet<string>(StringComparer.Ordinal);
        public readonly HashSet<string> EnclosureMisses = new HashSet<string>(StringComparer.Ordinal);
        public int ClearanceSamples;
        public int EnclosureSamples;
        public string Signature = string.Empty;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics RootMetrics =
            new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics MapMetrics =
            new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
    }

    private sealed class EnclosureSample
    {
        public string Name = string.Empty;
        public Vector3 Position;
        public Vector3 Right;
        public Vector3 Up;
        public Vector3 Forward;
        public float SideDistance;
        public float CeilingDistance;
        public bool RequireForwardWall;

        public static EnclosureSample Passage(string name, Vector3 start, Vector3 end, float sideDistance,
            float ceilingDistance)
        {
            var rotation = Quaternion.LookRotation((end - start).normalized, Vector3.up);
            return Room(name, (start + end) * 0.5f, rotation, sideDistance, ceilingDistance, false);
        }

        public static EnclosureSample Room(string name, Vector3 position, Quaternion rotation, float sideDistance,
            float ceilingDistance, bool requireForwardWall)
        {
            return new EnclosureSample
            {
                Name = name,
                Position = position,
                Right = rotation * Vector3.right,
                Up = rotation * Vector3.up,
                Forward = rotation * Vector3.forward,
                SideDistance = sideDistance,
                CeilingDistance = ceilingDistance,
                RequireForwardWall = requireForwardWall
            };
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV13SubterraneanThresholdValidator
{
    public const string ValidationPath =
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot +
        "/static-validation.md";
    public const string IdempotencePath =
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot +
        "/idempotence.md";
    public const string NegativePath =
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot +
        "/negative-controls.md";

    [MenuItem("Channel Play/Khufu V13/Validate Subterranean Threshold")]
    public static void ValidateMenu()
    {
        var result = ValidateScene();
        WriteValidation(result);
        if (result.Failures.Count > 0)
            throw new InvalidOperationException(
                "Khufu V13 validation failed: " +
                string.Join(" | ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V13_VALIDATE result=passed signature=" +
                  result.Signature);
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

    [MenuItem("Channel Play/Khufu V13/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.Rebuild();
        var first = ValidateScene(false);
        var firstScene =
            Sha256File(ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath);
        var firstAssets = GeneratedAssetSignature();
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.Rebuild();
        var second = ValidateScene(false);
        var secondScene =
            Sha256File(ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath);
        var secondAssets = GeneratedAssetSignature();
        var passed = first.Failures.Count == 0 && second.Failures.Count == 0 &&
                     first.Signature == second.Signature &&
                     firstScene == secondScene && firstAssets == secondAssets;
        Directory.CreateDirectory(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot);
        File.WriteAllText(IdempotencePath,
            "# Khufu V13 Rebuild Idempotence\n\n" +
            "- Verdict: **" + (passed ? "passed" : "failed") + "**\n" +
            "- First / second signature: `" + first.Signature + " / " +
            second.Signature + "`\n" +
            "- First / second scene SHA256: `" + firstScene + " / " +
            secondScene + "`\n" +
            "- First / second generated signature: `" + firstAssets + " / " +
            secondAssets + "`\n\n" +
            "KHUFU_V13_IDEMPOTENCE: " + (passed ? "passed" : "failed") + "\n",
            new UTF8Encoding(false));
        WriteValidation(second);
        if (!passed)
            throw new InvalidOperationException(
                "Khufu V13 rebuild idempotence failed.");
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V13_IDEMPOTENCE result=passed signature=" +
            second.Signature);
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

    [MenuItem("Channel Play/Khufu V13/Validate Negative Controls And Rollback")]
    public static void ValidateNegativeControls()
    {
        var cases = new List<string>();
        RunMutation("V4 renderer restored", "V4 predecessor target state", () =>
        {
            var context = OpenContext();
            Require(context.V4.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V4SubterraneanTargets[0]), "first V4 target")
                .GetComponent<Renderer>().enabled = true;
        }, cases);
        RunMutation("V4 target deactivated", "V4 predecessor target state", () =>
        {
            var context = OpenContext();
            Require(context.V4.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V4SubterraneanTargets[0]), "first V4 target")
                .gameObject.SetActive(false);
        }, cases);
        RunMutation("Structural pair drift", "structural pair transform", () =>
        {
            var context = OpenContext();
            Require(context.Root.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.PairRootName)
                    ?.GetChild(0), "first structural pair").localPosition +=
                Vector3.right * 0.25f;
        }, cases);
        RunMutation("Chamber ceiling proxy disabled", "proxy collider", () =>
        {
            var context = OpenContext();
            Collider(context.Root,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.CollisionRootName +
                    "/V13_Proxy_Chamber_Ceiling")
                .enabled = false;
        }, cases);
        RunMutation("Pit backing disabled", "solid pit backing", () =>
        {
            var context = OpenContext();
            Collider(context.Root,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.CollisionRootName +
                    "/V13_Proxy_" +
                    ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                        .SolidPitBackingName)
                .enabled = false;
        }, cases);
        RunMutation("V10-owned marker moved", "preserved dependency", () =>
        {
            var context = OpenContext();
            Require(context.V4.Find(
                    "V4_Gameplay_Route/V4_Route_Subterranean_Approach"),
                "V4 approach marker").localPosition += Vector3.right * 0.25f;
        }, cases);
        RunMutation("Inherited light disabled", "preserved dependency", () =>
        {
            var context = OpenContext();
            Require(context.V4.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V4SubterraneanLightPath), "V4 subterranean light")
                .GetComponent<Light>().enabled = false;
        }, cases);
        RunMutation("Junction inner wall trim reverted",
            "route clearance blocked", () =>
        {
            var context = OpenContext();
            var target = Require(context.Root.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .CollisionRootName +
                    "/V13_Proxy_" +
                    ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                        .DescendingShell +
                    "_West_Wall"), "descending inner wall proxy");
            var release =
                KhufuV13SubterraneanRouteContract.JunctionInnerWallRelease;
            var forward =
                (KhufuV13SubterraneanRouteContract.SubterraneanLanding -
                 KhufuV13SubterraneanRouteContract.JunctionEnd).normalized;
            target.localPosition -= forward * (release * 0.5f);
            target.localScale += new Vector3(0f, 0f, release);
            Physics.SyncTransforms();
        }, cases);

        var beforeScene =
            Sha256File(ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath);
        var beforeAssets = GeneratedAssetSignature();
        var beforeSignature = ValidateScene().Signature;
        var threw = false;
        try
        {
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .InjectFailureAfterSuccessorBindingsForValidation = true;
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.Rebuild();
        }
        catch (InvalidOperationException exception)
        {
            threw = exception.Message.Contains(
                "Injected V13 failure", StringComparison.Ordinal);
        }
        finally
        {
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .InjectFailureAfterSuccessorBindingsForValidation = false;
        }
        var after = ValidateScene();
        var rollbackPassed =
            threw && after.Failures.Count == 0 &&
            beforeScene ==
            Sha256File(ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath) &&
            beforeAssets == GeneratedAssetSignature() &&
            beforeSignature == after.Signature;
        if (!rollbackPassed)
            throw new InvalidOperationException(
                "V13 rollback negative control failed.");
        cases.Add("Injected successor failure -> rollback verified");

        Directory.CreateDirectory(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot);
        var text =
            new StringBuilder("# Khufu V13 Negative Controls And Rollback\n\n");
        text.AppendLine("- Verdict: **passed**");
        foreach (var item in cases)
            text.AppendLine("- " + item + ": `rejected`");
        text.AppendLine("- Rollback scene SHA256: `" + beforeScene + "`");
        text.AppendLine("- Rollback generated signature: `" + beforeAssets + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V13_NEGATIVE_CONTROLS: passed");
        File.WriteAllText(NegativePath, text.ToString(),
            new UTF8Encoding(false));
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V13_NEGATIVE_CONTROLS result=passed cases=" +
            cases.Count);
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

    private static void RunMutation(string label, string expectedFailure,
        Action mutation, ICollection<string> cases)
    {
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath,
            OpenSceneMode.Single);
        mutation();
        var result = ValidateScene(false);
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath,
            OpenSceneMode.Single);
        if (!result.Failures.Any(item =>
                item.Contains(expectedFailure, StringComparison.Ordinal)))
            throw new InvalidOperationException(
                "V13 negative control was not rejected: " + label +
                " failures=" + string.Join(" | ", result.Failures));
        cases.Add(label);
    }

    private static ValidationResult ValidateScene(bool reopen = true)
    {
        var result = new ValidationResult();
        if (reopen)
            EditorSceneManager.OpenScene(
                ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath,
                OpenSceneMode.Single);
        var context = OpenContext();
        var specs =
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BuildSpecs();
        var budget =
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.LoadPerformanceBudget();
        var audit =
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.LoadPrewriteAudit();

        ValidateIdentity(context.Root, result);
        ValidateVisuals(context.Root, specs, result);
        ValidateStructuralPairs(context.Root, specs, result);
        ValidateTransitions(context, audit, result);
        ValidateClearanceSlopeAndEnclosure(context.Root, specs, result);

        result.RootMetrics =
            ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(context.Root);
        result.MapMetrics =
            ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(context.Map);
        if (!MetricsMatch(result.RootMetrics,
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                    .ExpectedRendererCount,
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ExpectedRootVertices,
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ExpectedRootTriangles,
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                    .ExpectedColliderCount))
            result.Failures.Add(
                "V13 root metrics drifted: " +
                MetricsToken(result.RootMetrics));
        if (!MetricsMatch(result.MapMetrics,
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ExpectedMapRenderers,
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ExpectedMapVertices,
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ExpectedMapTriangles,
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ExpectedMapColliders))
            result.Failures.Add(
                "V13 map metrics drifted: " +
                MetricsToken(result.MapMetrics));
        if (budget.root.renderers_exact != 5 ||
            budget.root.colliders_exact != 20 ||
            budget.root.colliders_max != 20 ||
            budget.map.renderers_exact != 839 ||
            budget.map.colliders_exact != 609 ||
            budget.map.colliders_max != 612)
            result.Failures.Add("V13 exact performance budget drifted.");

        result.V12RestoredSignature =
            ValidateV12RestoredContext(context, result);
        result.Signature = ComputeSignature(context, audit);
        return result;
    }

    private static void ValidateIdentity(Transform root,
        ValidationResult result)
    {
        if (root.localPosition != Vector3.zero ||
            root.localRotation != Quaternion.identity ||
            root.localScale != Vector3.one ||
            !root.gameObject.activeSelf || !root.gameObject.activeInHierarchy)
            result.Failures.Add("V13 root identity/active hierarchy drifted.");
        var expected = new HashSet<string>(new[]
        {
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.VisualRootName,
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.PairRootName,
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.CollisionRootName,
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.MetadataRootName
        }, StringComparer.Ordinal);
        var actual = Enumerable.Range(0, root.childCount)
            .Select(index => root.GetChild(index).name).ToArray();
        if (actual.Length != expected.Count || !expected.SetEquals(actual))
            result.Failures.Add("V13 root hierarchy drifted.");
        if (root.GetComponentsInChildren<KhufuV13SegmentTag>(true)
            .Any(tag => tag.SegmentIds.Count == 0 ||
                        string.IsNullOrWhiteSpace(tag.TruthClass)))
            result.Failures.Add("V13 semantic tag coverage drifted.");
    }

    private static void ValidateVisuals(Transform root,
        IReadOnlyList<
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        var visuals = Require(root.Find(
                ChannelPlayKhufuV13SubterraneanThresholdBuilder.VisualRootName),
            "visual root");
        if (visuals.childCount !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .ExpectedRendererCount)
            result.Failures.Add("V13 visual renderer inventory drifted.");
        foreach (var bucket in
                 ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.Buckets)
        {
            var child = visuals.Find("V13_" + bucket);
            if (child == null)
            {
                result.Failures.Add(
                    "V13 visual bucket is missing: " + bucket);
                continue;
            }
            var filters = child.GetComponents<MeshFilter>();
            var renderers = child.GetComponents<MeshRenderer>();
            if (!child.gameObject.activeSelf ||
                !child.gameObject.activeInHierarchy)
                result.Failures.Add(
                    "V13 visual active hierarchy drifted: " + bucket);
            if (filters.Length != 1 || filters[0].sharedMesh == null ||
                renderers.Length != 1 || !renderers[0].enabled ||
                renderers[0].sharedMaterial == null)
            {
                result.Failures.Add(
                    "V13 visual component contract drifted: " + bucket);
                continue;
            }
            var expectedPath =
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                    .GeneratedRoot +
                "/KhufuV13_" + bucket + ".asset";
            if (AssetDatabase.GetAssetPath(filters[0].sharedMesh) != expectedPath)
                result.Failures.Add(
                    "V13 visual mesh path drifted: " + bucket);
            var expected =
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                    .BuildTransientMesh(specs, bucket, "Expected_" + bucket);
            try
            {
                if (ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                        .GeometrySignature(expected) !=
                    ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                        .GeometrySignature(filters[0].sharedMesh))
                    result.Failures.Add(
                        "V13 visual geometry drifted: " + bucket);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(expected);
            }
            var materialPath =
                AssetDatabase.GetAssetPath(renderers[0].sharedMaterial);
            if (!materialPath.StartsWith(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.MaterialRoot +
                    "/", StringComparison.Ordinal))
                result.Failures.Add(
                    "V13 material ownership drifted: " + bucket);
        }
    }

    private static void ValidateStructuralPairs(Transform root,
        IReadOnlyList<
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        var pairs = Require(root.Find(
                ChannelPlayKhufuV13SubterraneanThresholdBuilder.PairRootName),
            "pair root");
        var proxies = Require(root.Find(
                ChannelPlayKhufuV13SubterraneanThresholdBuilder.CollisionRootName),
            "proxy root");
        var structural = specs.Where(item => item.Collider).ToArray();
        if (pairs.childCount != structural.Length ||
            proxies.childCount != structural.Length ||
            structural.Length !=
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .ExpectedColliderCount)
            result.Failures.Add(
                "V13 structural pair/proxy inventory drifted.");
        foreach (var spec in structural)
        {
            var pair = pairs.Find(
                ChannelPlayKhufuV13SubterraneanThresholdBuilder.PairName(spec));
            var proxy = proxies.Find(spec.ColliderName);
            if (pair == null || proxy == null)
            {
                result.Failures.Add(
                    "V13 structural pair is missing: " + spec.Name);
                continue;
            }
            if (!TransformMatches(pair, spec) ||
                !TransformMatches(proxy, spec))
                result.Failures.Add(
                    "V13 structural pair transform drifted: " + spec.Name);
            var colliders = proxy.GetComponents<BoxCollider>();
            if (!pair.gameObject.activeSelf ||
                !pair.gameObject.activeInHierarchy ||
                !proxy.gameObject.activeSelf ||
                !proxy.gameObject.activeInHierarchy ||
                colliders.Length != 1 || !colliders[0].enabled ||
                colliders[0].isTrigger ||
                colliders[0].center != Vector3.zero ||
                colliders[0].size != Vector3.one)
                result.Failures.Add(
                    "V13 proxy collider/active hierarchy drifted: " +
                    spec.Name);
        }
    }

    private static void ValidateTransitions(Context context,
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.PrewriteAuditDocument
            audit,
        ValidationResult result)
    {
        try
        {
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ValidateFrozenTargets(context.V4, audit, false);
        }
        catch (Exception exception)
        {
            result.Failures.Add(
                "V4 predecessor target state drifted: " + exception.Message);
        }
        try
        {
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ValidatePreservedObservations(context.V4, context.V10, audit);
        }
        catch (Exception exception)
        {
            result.Failures.Add(
                "V13 preserved dependency drifted: " + exception.Message);
        }

        var control =
            context.Root
                .GetComponentsInChildren<
                    KhufuV13SubterraneanThresholdControl>(true)
                .SingleOrDefault();
        if (control == null)
        {
            result.Failures.Add(
                "V13 runtime threshold-control binding is missing.");
            return;
        }
        var expectedTargets =
            new HashSet<GameObject>(
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .V4SubterraneanTargets
                    .Select(path => Require(context.V4.Find(path), path)
                        .gameObject));
        if (control.PredecessorTargets.Count != expectedTargets.Count ||
            !expectedTargets.SetEquals(control.PredecessorTargets))
            result.Failures.Add(
                "V13 transition-control predecessor inventory drifted.");
        var expectedProxyNames =
            new HashSet<string>(
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BuildSpecs()
                    .Where(item => item.Collider)
                    .Select(item => item.ColliderName), StringComparer.Ordinal);
        if (control.CollisionProxies.Count != expectedProxyNames.Count ||
            !expectedProxyNames.SetEquals(
                control.CollisionProxies.Select(item => item.name)) ||
            control.CollisionProxies.Any(item =>
                item == null || !item.enabled || item.isTrigger))
            result.Failures.Add(
                "V13 transition-control proxy inventory drifted.");
        var route = KhufuV13SubterraneanRouteContract.ForwardRoute();
        if (control.RouteAnchors.Count != route.Count)
            result.Failures.Add(
                "V13 transition-control route anchor inventory drifted.");
        else
        {
            for (var index = 0; index < route.Count; index++)
            {
                if (control.RouteAnchors[index] == null ||
                    Vector3.Distance(
                        control.RouteAnchors[index].position,
                        route[index]) > 0.001f)
                    result.Failures.Add(
                        "V13 transition-control route anchor drifted: " +
                        index);
            }
        }
        var expectedBackingName =
            "V13_Proxy_" +
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .SolidPitBackingName;
        if (control.SolidPitBacking == null ||
            control.SolidPitBacking.name != expectedBackingName ||
            control.SolidPitBacking.GetComponent<BoxCollider>() == null ||
            !control.SolidPitBacking.GetComponent<BoxCollider>().enabled ||
            control.SolidPitBacking.GetComponent<BoxCollider>().isTrigger)
            result.Failures.Add(
                "V13 solid pit backing control binding drifted.");
    }

    private static void ValidateClearanceSlopeAndEnclosure(Transform root,
        IReadOnlyList<
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec> specs,
        ValidationResult result)
    {
        if (Mathf.Abs(
                KhufuV13SubterraneanRouteContract.DescentAngleDegrees - 29f) >
            0.5f ||
            KhufuV13SubterraneanRouteContract.DescentAngleDegrees > 45f)
            result.Failures.Add("V13 descent slope contract drifted.");
        if (Mathf.Abs(
                KhufuV13SubterraneanRouteContract.PassageClearWidth - 2.50f) >
            0.001f ||
            Mathf.Abs(
                KhufuV13SubterraneanRouteContract.PassageClearHeight - 2.40f) >
            0.001f ||
            Mathf.Abs(
                KhufuV13SubterraneanRouteContract
                    .JunctionTransitionEndRelease - 1.45f) > 0.001f ||
            Mathf.Abs(
                KhufuV13SubterraneanRouteContract.JunctionInnerWallRelease -
                1.80f) > 0.001f ||
            Mathf.Abs(
                KhufuV13SubterraneanRouteContract.LandingRoofEndRelease -
                1.55f) > 0.001f)
            result.Failures.Add("V13 passage clearance dimensions drifted.");

        Physics.SyncTransforms();
        var playerController =
            GameObject.Find("MVP_Player")?.GetComponent<CharacterController>();
        if (playerController == null)
            result.Failures.Add(
                "V13 traversal CharacterController contract is missing.");
        var playerScale = playerController == null
            ? Vector3.one
            : playerController.transform.lossyScale;
        var playerRadius = playerController == null
            ? 0.45f
            : playerController.radius *
              Mathf.Max(Mathf.Abs(playerScale.x), Mathf.Abs(playerScale.z));
        var playerHeight = playerController == null
            ? 2f
            : Mathf.Max(playerController.height * Mathf.Abs(playerScale.y),
                playerRadius * 2f);
        foreach (var point in ClearanceSamples(
                     KhufuV13SubterraneanRouteContract.RoundTripRoute(), 0.25f))
        {
            var hits = Physics.OverlapCapsule(
                point + Vector3.up *
                (KhufuV13SubterraneanRouteContract.TraversalFloorOffset +
                 playerRadius),
                point + Vector3.up *
                (KhufuV13SubterraneanRouteContract.TraversalFloorOffset +
                 playerHeight - playerRadius),
                playerRadius, ~0, QueryTriggerInteraction.Ignore);
            var owned = hits.Where(hit => hit.transform.IsChildOf(root))
                .Select(hit => hit.name).Distinct(StringComparer.Ordinal)
                .ToArray();
            if (owned.Length > 0)
                result.Failures.Add(
                    "V13 route clearance blocked at " +
                    VectorToken(point) + ": " + string.Join(",", owned));
        }

        ValidatePassageShell(root,
            KhufuV13SubterraneanRouteContract.V10BranchAnchor,
            KhufuV13SubterraneanRouteContract.JunctionEnd,
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .TransitionShell, result);
        ValidatePassageShell(root,
            KhufuV13SubterraneanRouteContract.JunctionEnd,
            KhufuV13SubterraneanRouteContract.SubterraneanLanding,
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .DescendingShell, result);
        ValidatePassageShell(root,
            KhufuV13SubterraneanRouteContract.SubterraneanLanding,
            KhufuV13SubterraneanRouteContract.ChamberDoor,
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.ApproachShell,
            result);

        var center =
            KhufuV13SubterraneanRouteContract.ChamberCenter +
            Vector3.up * 1.2f;
        ValidateRay(root, center, Vector3.left, 4f,
            "Chamber_West_Wall", result);
        ValidateRay(root, center, Vector3.right, 4f,
            "Chamber_East_Wall", result);
        ValidateRay(root, center, Vector3.forward, 4f,
            "Chamber_North_Wall", result);
        ValidateRay(root, center, Vector3.down, 2f,
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .SolidPitBackingName, result);
        ValidateRay(root, center, Vector3.up, 3f,
            "Chamber_Ceiling", result);
        ValidateRay(root, center + Vector3.left * 1.75f, Vector3.back, 4f,
            "Chamber_South_West_Jamb", result);
        ValidateRay(root, center + Vector3.right * 1.75f, Vector3.back, 4f,
            "Chamber_South_East_Jamb", result);
        ValidateRay(root,
            KhufuV13SubterraneanRouteContract.ChamberCenter +
            Vector3.up * 2.8f, Vector3.back, 4f,
            "Chamber_South_Lintel", result);

        var pit = KhufuV13SubterraneanRouteContract.PitInspection;
        var pitOverlap = Physics.OverlapSphere(
                pit + Vector3.down * 0.03f, 0.06f, ~0,
                QueryTriggerInteraction.Ignore)
            .Where(hit => hit.transform.IsChildOf(root)).ToArray();
        var backingToken =
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                .SolidPitBackingName;
        if (!pitOverlap.Any(hit =>
                hit.name.Contains(backingToken, StringComparison.Ordinal)))
            result.Failures.Add(
                "V13 solid pit backing overlap evidence is missing.");
        ValidateRay(root, pit + Vector3.up * 0.6f, Vector3.down, 1.2f,
            backingToken, result, "solid pit backing cast");

        if (specs.Count(item =>
                item.Shell ==
                ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                    .ChamberShell && item.Collider) != 8 ||
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.PassageShells
                .Any(shell =>
                    specs.Count(item =>
                        item.Shell == shell && item.Collider) != 4))
            result.Failures.Add("V13 enclosure spec inventory drifted.");
    }

    private static void ValidatePassageShell(Transform root, Vector3 start,
        Vector3 end, string shell, ValidationResult result)
    {
        var delta = end - start;
        var rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
        var center = (start + end) * 0.5f +
                     rotation * Vector3.up * 1.2f;
        ValidateRay(root, center, rotation * Vector3.left, 2f,
            shell + "_West_Wall", result);
        ValidateRay(root, center, rotation * Vector3.right, 2f,
            shell + "_East_Wall", result);
        ValidateRay(root, center, rotation * Vector3.down, 2f,
            shell + "_Floor", result);
        ValidateRay(root, center, rotation * Vector3.up, 2f,
            shell + "_Roof", result);
    }

    private static IEnumerable<Vector3> ClearanceSamples(
        IReadOnlyList<Vector3> route, float maximumStep)
    {
        if (route == null || route.Count == 0 || maximumStep <= 0f)
            throw new InvalidOperationException(
                "V13 clearance sampling contract is invalid.");
        yield return route[0];
        for (var segment = 1; segment < route.Count; segment++)
        {
            var start = route[segment - 1];
            var end = route[segment];
            var steps = Mathf.Max(1,
                Mathf.CeilToInt(Vector3.Distance(start, end) / maximumStep));
            for (var step = 1; step <= steps; step++)
                yield return Vector3.Lerp(start, end, (float)step / steps);
        }
    }

    private static void ValidateRay(Transform root, Vector3 origin,
        Vector3 direction, float distance, string token,
        ValidationResult result, string label = "enclosure ray")
    {
        var hits = Physics.RaycastAll(origin, direction, distance, ~0,
                QueryTriggerInteraction.Ignore)
            .Where(hit => hit.collider.transform.IsChildOf(root))
            .OrderBy(hit => hit.distance).ToArray();
        if (hits.Length == 0 ||
            !hits[0].collider.name.Contains(token, StringComparison.Ordinal))
            result.Failures.Add(
                "V13 " + label + " missed " + token + " from " +
                VectorToken(origin));
    }

    private static string ValidateV12RestoredContext(Context context,
        ValidationResult result)
    {
        var parent = context.Root.parent;
        var sibling = context.Root.GetSiblingIndex();
        var active = context.Root.gameObject.activeSelf;
        try
        {
            context.Root.SetParent(null, true);
            context.Root.gameObject.SetActive(false);
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ApplyPredecessorContext(context.V4);
            var restored = InvokeV12();
            if (restored.Failures.Count != 0 ||
                restored.Signature !=
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .V12BaselineStaticSignature)
                result.Failures.Add(
                    "V12 restored-context validator/signature drifted: " +
                    restored.Signature + " failures=" +
                    string.Join(" | ", restored.Failures));
            var metrics =
                ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(
                    context.Map);
            if (!MetricsMatch(metrics,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V12BaselineRenderers,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V12BaselineVertices,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V12BaselineTriangles,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .V12BaselineColliders))
                result.Failures.Add(
                    "V12 restored-context map metrics drifted: " +
                    MetricsToken(metrics));
            return restored.Signature;
        }
        catch (Exception exception)
        {
            result.Failures.Add(
                "V12 restored-context validation failed: " +
                exception.Message);
            return string.Empty;
        }
        finally
        {
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ApplyV13Context(context.V4);
            context.Root.SetParent(parent, false);
            context.Root.SetSiblingIndex(sibling);
            context.Root.localPosition = Vector3.zero;
            context.Root.localRotation = Quaternion.identity;
            context.Root.localScale = Vector3.one;
            context.Root.gameObject.SetActive(active);
            Physics.SyncTransforms();
        }
    }

    private static V12Result InvokeV12()
    {
        var method = typeof(ChannelPlayKhufuV12QueenCircuitValidator).GetMethod(
            "ValidateScene", BindingFlags.NonPublic | BindingFlags.Static);
        var raw = method?.Invoke(null, new object[] { false });
        if (raw == null)
            throw new InvalidOperationException(
                "V12 validator result is missing.");
        var type = raw.GetType();
        var failures =
            type.GetField("Failures")?.GetValue(raw) as IEnumerable<string>;
        return new V12Result
        {
            Failures = failures?.ToList() ??
                       new List<string> { "V12 failures unavailable" },
            Signature =
                Convert.ToString(type.GetField("Signature")?.GetValue(raw))
        };
    }

    private static string ComputeSignature(Context context,
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.PrewriteAuditDocument
            audit)
    {
        var lines = new List<string>();
        foreach (var node in context.Root.GetComponentsInChildren<Transform>(true)
                     .OrderBy(node => HierarchyPath(context.Root, node),
                         StringComparer.Ordinal))
        {
            var path = HierarchyPath(context.Root, node);
            lines.Add("T|" + path + "|" + node.gameObject.activeSelf + "|" +
                      VectorToken(node.localPosition) + "|" +
                      QuaternionToken(node.localRotation) + "|" +
                      VectorToken(node.localScale));
            var filter = node.GetComponent<MeshFilter>();
            if (filter != null && filter.sharedMesh != null)
                lines.Add("M|" + path + "|" +
                          AssetDatabase.GetAssetPath(filter.sharedMesh) + "|" +
                          ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
                              .GeometrySignature(filter.sharedMesh));
            var renderer = node.GetComponent<MeshRenderer>();
            if (renderer != null)
                lines.Add("R|" + path + "|" + renderer.enabled + "|" +
                          AssetDatabase.GetAssetPath(renderer.sharedMaterial));
            var collider = node.GetComponent<BoxCollider>();
            if (collider != null)
                lines.Add("C|" + path + "|" + collider.enabled + "|" +
                          collider.isTrigger + "|" +
                          VectorToken(collider.center) + "|" +
                          VectorToken(collider.size));
        }

        foreach (var path in
                 ChannelPlayKhufuV13SubterraneanThresholdBuilder
                     .V4SubterraneanTargets)
        {
            var target = Require(context.V4.Find(path), path);
            var renderer = target.GetComponent<Renderer>();
            var collider = target.GetComponent<Collider>();
            lines.Add("V4|" + path + "|" + target.gameObject.activeSelf + "|" +
                      renderer.enabled + "|" +
                      (collider == null
                          ? "none"
                          : collider.enabled + "|" + collider.isTrigger) + "|" +
                      VectorToken(target.localPosition) + "|" +
                      QuaternionToken(target.localRotation) + "|" +
                      VectorToken(target.localScale));
        }
        foreach (var frozen in audit.preserved_observations)
        {
            var target = ResolveObservation(context, frozen.path);
            var renderer = target.GetComponent<Renderer>();
            var light = target.GetComponent<Light>();
            lines.Add("OBS|" + frozen.path + "|" +
                      target.gameObject.activeSelf + "|" +
                      (renderer == null
                          ? "none"
                          : renderer.enabled.ToString()) + "|" +
                      (light == null
                          ? "none"
                          : light.enabled.ToString()) + "|" +
                      VectorToken(target.localPosition) + "|" +
                      QuaternionToken(target.localRotation) + "|" +
                      VectorToken(target.localScale));
        }
        foreach (var path in new[]
                 {
                     ChannelPlayKhufuV13SubterraneanThresholdBuilder
                         .ClassificationPath,
                     ChannelPlayKhufuV13SubterraneanThresholdBuilder
                         .PerformanceBudgetPath,
                     ChannelPlayKhufuV13SubterraneanThresholdBuilder
                         .PrewriteAuditPath
                 })
            lines.Add("F|" + path + "|" + Sha256File(path));

        var control =
            context.Root
                .GetComponentsInChildren<
                    KhufuV13SubterraneanThresholdControl>(true)
                .SingleOrDefault();
        if (control != null)
        {
            lines.Add("CTRL|targets|" +
                      string.Join(",", control.PredecessorTargets
                          .Select(item => item.name)));
            lines.Add("CTRL|proxies|" +
                      string.Join(",", control.CollisionProxies
                          .Select(item => item.name)));
            lines.Add("CTRL|anchors|" +
                      string.Join(",", control.RouteAnchors
                          .Select(item => item.name)));
            lines.Add("CTRL|pit|" +
                      (control.SolidPitBacking == null
                          ? string.Empty
                          : control.SolidPitBacking.name));
        }
        return Sha256Text(string.Join("\n", lines));
    }

    private static string GeneratedAssetSignature()
    {
        var roots = new[]
        {
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.GeneratedRoot,
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.MaterialRoot
        };
        var paths = roots.Where(Directory.Exists)
            .SelectMany(root =>
                Directory.GetFiles(root, "*", SearchOption.AllDirectories))
            .Concat(roots.Select(root => root + ".meta").Where(File.Exists))
            .OrderBy(path => path, StringComparer.Ordinal).ToArray();
        return Sha256Text(string.Join("\n", paths.Select(path =>
            path.Replace('\\', '/') + "|" + Sha256File(path))));
    }

    private static Context OpenContext()
    {
        var map = Require(
            GameObject.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.MapRootName)
                ?.transform, "shared map root");
        return new Context
        {
            Map = map,
            Root = Require(map.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.RootName),
                "V13 root"),
            V4 = Require(map.Find(
                    ChannelPlayPyramidReferenceMatchedV4Builder.RootName),
                "V4 root"),
            V10 = Require(map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName),
                "V10 root")
        };
    }

    private static Transform ResolveObservation(Context context, string fullPath)
    {
        var v4Prefix =
            ChannelPlayPyramidReferenceMatchedV4Builder.RootName + "/";
        if (fullPath.StartsWith(v4Prefix, StringComparison.Ordinal))
            return Require(context.V4.Find(fullPath.Substring(v4Prefix.Length)),
                fullPath);
        var v10Prefix = ChannelPlayKhufuV10InteriorBuilder.RootName + "/";
        if (fullPath.StartsWith(v10Prefix, StringComparison.Ordinal))
            return Require(
                context.V10.Find(fullPath.Substring(v10Prefix.Length)),
                fullPath);
        throw new InvalidOperationException(
            "Unknown V13 observation root: " + fullPath);
    }

    private static bool TransformMatches(Transform target,
        ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.BoxSpec spec)
    {
        return Vector3.Distance(target.localPosition, spec.Position) <= 0.001f &&
               Quaternion.Angle(target.localRotation, spec.Rotation) <= 0.01f &&
               Vector3.Distance(target.localScale, spec.Scale) <= 0.001f;
    }

    private static BoxCollider Collider(Transform root, string path)
    {
        var collider = Require(root.Find(path), path).GetComponent<BoxCollider>();
        if (collider == null)
            throw new InvalidOperationException(
                "Required V13 collider is missing: " + path);
        return collider;
    }

    private static Transform Require(Transform target, string label)
    {
        if (target == null)
            throw new InvalidOperationException(
                "Required V13 validation target is missing: " + label);
        return target;
    }

    private static bool MetricsMatch(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics,
        int renderers, int vertices, int triangles, int colliders)
    {
        return metrics.Renderers == renderers && metrics.Vertices == vertices &&
               metrics.Triangles == triangles &&
               metrics.Colliders == colliders;
    }

    private static string MetricsToken(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers +
               "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles +
               "_colliders=" + metrics.Colliders;
    }

    private static string HierarchyPath(Transform root, Transform node)
    {
        if (node == root) return root.name;
        var names = new Stack<string>();
        var current = node;
        while (current != null && current != root)
        {
            names.Push(current.name);
            current = current.parent;
        }
        return root.name + "/" + string.Join("/", names);
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("R") + "," + value.y.ToString("R") + "," +
               value.z.ToString("R");
    }

    private static string QuaternionToken(Quaternion value)
    {
        return value.x.ToString("R") + "," + value.y.ToString("R") + "," +
               value.z.ToString("R") + "," + value.w.ToString("R");
    }

    private static string Sha256File(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream))
                .Replace("-", string.Empty).ToLowerInvariant();
    }

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create())
            return BitConverter.ToString(
                    sha.ComputeHash(Encoding.UTF8.GetBytes(value)))
                .Replace("-", string.Empty).ToLowerInvariant();
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V13 Static Validation\n\n");
        text.AppendLine("- Verdict: **" +
                        (result.Failures.Count == 0
                            ? "passed"
                            : "failed") + "**");
        text.AppendLine("- V13 signature: `" + result.Signature + "`");
        text.AppendLine("- V12 restored-context signature: `" +
                        result.V12RestoredSignature + "`");
        text.AppendLine("- Root metrics: `" +
                        MetricsToken(result.RootMetrics) + "`");
        text.AppendLine("- Map metrics: `" +
                        MetricsToken(result.MapMetrics) + "`");
        foreach (var failure in result.Failures)
            text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V13_STATIC_VALIDATION: " +
                        (result.Failures.Count == 0
                            ? "passed"
                            : "failed"));
        File.WriteAllText(ValidationPath, text.ToString(),
            new UTF8Encoding(false));
    }

    private sealed class Context
    {
        public Transform Map;
        public Transform Root;
        public Transform V4;
        public Transform V10;
    }

    private sealed class V12Result
    {
        public List<string> Failures = new List<string>();
        public string Signature = string.Empty;
    }

    private sealed class ValidationResult
    {
        public readonly List<string> Failures = new List<string>();
        public string Signature = string.Empty;
        public string V12RestoredSignature = string.Empty;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics RootMetrics =
            new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics MapMetrics =
            new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
    }
}

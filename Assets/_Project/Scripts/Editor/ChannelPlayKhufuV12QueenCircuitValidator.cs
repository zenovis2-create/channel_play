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

public static class ChannelPlayKhufuV12QueenCircuitValidator
{
    public const string ValidationPath =
        ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot + "/static-validation.md";
    public const string IdempotencePath =
        ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot + "/idempotence.md";
    public const string NegativePath =
        ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot + "/negative-controls.md";
    public const int ExpectedRootVertices = 1176;
    public const int ExpectedRootTriangles = 588;
    public const int ExpectedMapVertices = 67070;
    public const int ExpectedMapTriangles = 48560;

    [MenuItem("Channel Play/Khufu V12/Validate Queen Circuit")]
    public static void ValidateMenu()
    {
        var result = ValidateScene();
        WriteValidation(result);
        if (result.Failures.Count > 0)
            throw new InvalidOperationException("Khufu V12 validation failed: " +
                                                string.Join(" | ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V12_VALIDATE result=passed signature=" + result.Signature);
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

    [MenuItem("Channel Play/Khufu V12/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        ChannelPlayKhufuV12QueenCircuitBuilder.Rebuild();
        var first = ValidateScene(false);
        var firstScene = Sha256File(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath);
        var firstAssets = GeneratedAssetSignature();
        ChannelPlayKhufuV12QueenCircuitBuilder.Rebuild();
        var second = ValidateScene(false);
        var secondScene = Sha256File(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath);
        var secondAssets = GeneratedAssetSignature();
        var passed = first.Failures.Count == 0 && second.Failures.Count == 0 &&
                     first.Signature == second.Signature &&
                     firstScene == secondScene && firstAssets == secondAssets;
        Directory.CreateDirectory(ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot);
        File.WriteAllText(IdempotencePath,
            "# Khufu V12 Rebuild Idempotence\n\n" +
            "- Verdict: **" + (passed ? "passed" : "failed") + "**\n" +
            "- First / second signature: `" + first.Signature + " / " + second.Signature + "`\n" +
            "- First / second scene SHA256: `" + firstScene + " / " + secondScene + "`\n" +
            "- First / second generated signature: `" + firstAssets + " / " + secondAssets + "`\n\n" +
            "KHUFU_V12_IDEMPOTENCE: " + (passed ? "passed" : "failed") + "\n",
            new UTF8Encoding(false));
        WriteValidation(second);
        if (!passed) throw new InvalidOperationException("Khufu V12 rebuild idempotence failed.");
        Debug.Log("CHANNEL_PLAY_KHUFU_V12_IDEMPOTENCE result=passed signature=" + second.Signature);
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

    [MenuItem("Channel Play/Khufu V12/Validate Negative Controls And Rollback")]
    public static void ValidateNegativeControls()
    {
        var cases = new List<string>();
        RunMutation("Queen gate restored", "Queen gate proxy", () =>
        {
            var context = OpenContext();
            Collider(context.V10, ChannelPlayKhufuV12QueenCircuitBuilder.QueenGateProxyPath).enabled = true;
        }, cases);
        RunMutation("Gallery floor ramp restored", "Gallery floor proxy", () =>
        {
            var context = OpenContext();
            Collider(context.V10, ChannelPlayKhufuV12QueenCircuitBuilder.GalleryFloorProxyPath).enabled = true;
        }, cases);
        RunMutation("Historic service frame restored", "Historic service frame proxy", () =>
        {
            var context = OpenContext();
            foreach (var path in ChannelPlayKhufuV12QueenCircuitBuilder.HistoricServiceProxyPaths)
                Collider(context.V10, path).enabled = true;
        }, cases);
        RunMutation("V4 renderer restored", "V4 Queen overlap state", () =>
        {
            var context = OpenContext();
            Require(context.V4.Find(ChannelPlayKhufuV12QueenCircuitBuilder.V4QueenTargets[0]), "V4 target")
                .GetComponent<Renderer>().enabled = true;
        }, cases);
        RunMutation("Structural pair drift", "structural pair", () =>
        {
            var context = OpenContext();
            Require(context.Root.Find(ChannelPlayKhufuV12QueenCircuitBuilder.PairRootName)
                    .GetChild(0), "first pair").localPosition += Vector3.right * 0.25f;
        }, cases);
        RunMutation("Enclosure proxy disabled", "proxy collider", () =>
        {
            var context = OpenContext();
            Collider(context.Root,
                ChannelPlayKhufuV12QueenCircuitBuilder.CollisionRootName +
                "/V12_PROXY_Queens_Chamber_Chamber_Back_Wall").enabled = false;
        }, cases);
        RunMutation("Owned object deactivated", "active hierarchy", () =>
        {
            var context = OpenContext();
            context.Root.Find(ChannelPlayKhufuV12QueenCircuitBuilder.VisualRootName)
                .GetChild(0).gameObject.SetActive(false);
        }, cases);
        RunMutation("V4 glow ownership drift", "V4 marker/glow/light", () =>
        {
            var context = OpenContext();
            Require(context.V4.Find("V4_Gameplay_Route/V4_Glow_Queens"), "V4 glow")
                .GetComponent<Renderer>().enabled = true;
        }, cases);

        var beforeScene = Sha256File(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath);
        var beforeAssets = GeneratedAssetSignature();
        var beforeSignature = ValidateScene().Signature;
        var threw = false;
        try
        {
            ChannelPlayKhufuV12QueenCircuitBuilder.InjectFailureAfterSuccessorBindingsForValidation = true;
            ChannelPlayKhufuV12QueenCircuitBuilder.Rebuild();
        }
        catch (InvalidOperationException exception)
        {
            threw = exception.Message.Contains("Injected V12 failure");
        }
        finally
        {
            ChannelPlayKhufuV12QueenCircuitBuilder.InjectFailureAfterSuccessorBindingsForValidation = false;
        }
        var after = ValidateScene();
        var rollbackPassed = threw && after.Failures.Count == 0 &&
                             beforeScene == Sha256File(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath) &&
                             beforeAssets == GeneratedAssetSignature() &&
                             beforeSignature == after.Signature;
        if (!rollbackPassed) throw new InvalidOperationException("V12 rollback negative control failed.");
        cases.Add("Injected successor failure -> rollback verified");

        Directory.CreateDirectory(ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V12 Negative Controls And Rollback\n\n");
        text.AppendLine("- Verdict: **passed**");
        foreach (var item in cases) text.AppendLine("- " + item + ": `rejected`");
        text.AppendLine("- Rollback scene SHA256: `" + beforeScene + "`");
        text.AppendLine("- Rollback generated signature: `" + beforeAssets + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V12_NEGATIVE_CONTROLS: passed");
        File.WriteAllText(NegativePath, text.ToString(), new UTF8Encoding(false));
        Debug.Log("CHANNEL_PLAY_KHUFU_V12_NEGATIVE_CONTROLS result=passed cases=" + cases.Count);
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

    private static void RunMutation(string label, string expectedFailure, Action mutation, ICollection<string> cases)
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath, OpenSceneMode.Single);
        mutation();
        var result = ValidateScene(false);
        EditorSceneManager.OpenScene(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath, OpenSceneMode.Single);
        if (!result.Failures.Any(item => item.Contains(expectedFailure, StringComparison.Ordinal)))
            throw new InvalidOperationException("V12 negative control was not rejected: " + label +
                                                " failures=" + string.Join(" | ", result.Failures));
        cases.Add(label);
    }

    private static ValidationResult ValidateScene(bool reopen = true)
    {
        var result = new ValidationResult();
        if (reopen)
            EditorSceneManager.OpenScene(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var context = OpenContext();
        var specs = ChannelPlayKhufuV12QueenCircuitMeshPipeline.BuildSpecs();
        var budget = ChannelPlayKhufuV12QueenCircuitBuilder.LoadPerformanceBudget();

        ValidateIdentity(context.Root, result);
        ValidateVisuals(context.Root, specs, result);
        ValidateStructuralPairs(context.Root, specs, result);
        ValidateTransitions(context, result);
        ValidateClearanceAndEnclosure(context.Root, result);

        result.RootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(context.Root);
        result.MapMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(context.Map);
        if (!MetricsMatch(result.RootMetrics, 5, ExpectedRootVertices, ExpectedRootTriangles, 22))
            result.Failures.Add("V12 root metrics drifted: " + MetricsToken(result.RootMetrics));
        if (!MetricsMatch(result.MapMetrics, 834, ExpectedMapVertices, ExpectedMapTriangles, 589))
            result.Failures.Add("V12 map metrics drifted: " + MetricsToken(result.MapMetrics));
        if (budget.root.renderers_exact != 5 || budget.root.colliders_exact != 22 ||
            budget.map.renderers_exact != 834 || budget.map.colliders_exact != 589)
            result.Failures.Add("V12 exact performance budget drifted.");

        result.V11CommittedSignature = InvokeV11().Signature;
        result.V11RestoredSignature = ValidateV11RestoredContext(context, result);
        result.Signature = ComputeSignature(context);
        return result;
    }

    private static void ValidateIdentity(Transform root, ValidationResult result)
    {
        if (root.localPosition != Vector3.zero || root.localRotation != Quaternion.identity ||
            root.localScale != Vector3.one || !root.gameObject.activeSelf || !root.gameObject.activeInHierarchy)
            result.Failures.Add("V12 root identity/active hierarchy drifted.");
        var expected = new HashSet<string>(new[]
        {
            ChannelPlayKhufuV12QueenCircuitBuilder.VisualRootName,
            ChannelPlayKhufuV12QueenCircuitBuilder.PairRootName,
            ChannelPlayKhufuV12QueenCircuitBuilder.CollisionRootName,
            ChannelPlayKhufuV12QueenCircuitBuilder.MetadataRootName
        }, StringComparer.Ordinal);
        var actual = Enumerable.Range(0, root.childCount).Select(index => root.GetChild(index).name).ToArray();
        if (actual.Length != expected.Count || !expected.SetEquals(actual))
            result.Failures.Add("V12 root hierarchy drifted.");
        if (root.GetComponentsInChildren<KhufuV12SegmentTag>(true)
            .Any(tag => tag.SegmentIds.Count == 0 || string.IsNullOrWhiteSpace(tag.TruthClass)))
            result.Failures.Add("V12 semantic tag coverage drifted.");
    }

    private static void ValidateVisuals(Transform root,
        IReadOnlyList<ChannelPlayKhufuV12QueenCircuitMeshPipeline.BoxSpec> specs, ValidationResult result)
    {
        var visuals = Require(root.Find(ChannelPlayKhufuV12QueenCircuitBuilder.VisualRootName), "visual root");
        if (visuals.childCount != ChannelPlayKhufuV12QueenCircuitMeshPipeline.ExpectedRendererCount)
            result.Failures.Add("V12 visual renderer inventory drifted.");
        foreach (var bucket in ChannelPlayKhufuV12QueenCircuitMeshPipeline.Buckets)
        {
            var child = visuals.Find("V12_" + bucket);
            if (child == null)
            {
                result.Failures.Add("V12 visual bucket is missing: " + bucket);
                continue;
            }
            var filters = child.GetComponents<MeshFilter>();
            var renderers = child.GetComponents<MeshRenderer>();
            if (!child.gameObject.activeSelf || !child.gameObject.activeInHierarchy)
                result.Failures.Add("V12 visual active hierarchy drifted: " + bucket);
            if (filters.Length != 1 || filters[0].sharedMesh == null ||
                renderers.Length != 1 || !renderers[0].enabled || renderers[0].sharedMaterial == null)
            {
                result.Failures.Add("V12 visual component contract drifted: " + bucket);
                continue;
            }
            var expectedPath = ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeneratedRoot +
                               "/KhufuV12_" + bucket + ".asset";
            if (AssetDatabase.GetAssetPath(filters[0].sharedMesh) != expectedPath)
                result.Failures.Add("V12 visual mesh path drifted: " + bucket);
            var expected = ChannelPlayKhufuV12QueenCircuitMeshPipeline.BuildTransientMesh(
                specs, bucket, "Expected_" + bucket);
            try
            {
                if (ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeometrySignature(expected) !=
                    ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeometrySignature(filters[0].sharedMesh))
                    result.Failures.Add("V12 visual geometry drifted: " + bucket);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(expected);
            }
            var materialPath = AssetDatabase.GetAssetPath(renderers[0].sharedMaterial);
            if (!materialPath.StartsWith(ChannelPlayKhufuV12QueenCircuitBuilder.MaterialRoot + "/",
                    StringComparison.Ordinal))
                result.Failures.Add("V12 material ownership drifted: " + bucket);
        }
    }

    private static void ValidateStructuralPairs(Transform root,
        IReadOnlyList<ChannelPlayKhufuV12QueenCircuitMeshPipeline.BoxSpec> specs, ValidationResult result)
    {
        var pairs = Require(root.Find(ChannelPlayKhufuV12QueenCircuitBuilder.PairRootName), "pair root");
        var proxies = Require(root.Find(ChannelPlayKhufuV12QueenCircuitBuilder.CollisionRootName), "proxy root");
        var structural = specs.Where(item => item.Structural && item.Collider).ToArray();
        if (pairs.childCount != structural.Length || proxies.childCount != structural.Length)
            result.Failures.Add("V12 structural pair/proxy inventory drifted.");
        foreach (var spec in structural)
        {
            var pair = pairs.Find("V12_PAIR_" + spec.SegmentId + "_" + spec.Name);
            var proxy = proxies.Find("V12_PROXY_" + spec.SegmentId + "_" + spec.Name);
            if (pair == null || proxy == null)
            {
                result.Failures.Add("V12 structural pair is missing: " + spec.Name);
                continue;
            }
            if (!TransformMatches(pair, spec) || !TransformMatches(proxy, spec))
                result.Failures.Add("V12 structural pair transform drifted: " + spec.Name);
            var colliders = proxy.GetComponents<BoxCollider>();
            if (!pair.gameObject.activeInHierarchy || !proxy.gameObject.activeInHierarchy ||
                colliders.Length != 1 || !colliders[0].enabled || colliders[0].isTrigger ||
                colliders[0].center != Vector3.zero || colliders[0].size != Vector3.one)
                result.Failures.Add("V12 proxy collider/active hierarchy drifted: " + spec.Name);
        }
    }

    private static void ValidateTransitions(Context context, ValidationResult result)
    {
        try
        {
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.ValidateSuccessorAssets();
        }
        catch (Exception exception)
        {
            result.Failures.Add("V12 successor mesh contract failed: " + exception.Message);
        }
        if (MeshPath(context.V10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath) !=
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenLimestonePath ||
            MeshPath(context.V10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath) !=
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenGranitePath)
            result.Failures.Add("V12 successor binding paths drifted.");
        if (Collider(context.V10,
                ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath).enabled)
            result.Failures.Add("V12 Great Step proxy state drifted.");
        if (Collider(context.V10, ChannelPlayKhufuV12QueenCircuitBuilder.QueenGateProxyPath).enabled)
            result.Failures.Add("V12 Queen gate proxy state drifted.");
        if (Collider(context.V10, ChannelPlayKhufuV12QueenCircuitBuilder.GalleryFloorProxyPath).enabled)
            result.Failures.Add("V12 Gallery floor proxy state drifted.");
        if (ChannelPlayKhufuV12QueenCircuitBuilder.HistoricServiceProxyPaths
            .Any(path => Collider(context.V10, path).enabled))
            result.Failures.Add("V12 Historic service frame proxy state drifted.");
        foreach (var path in ChannelPlayKhufuV12QueenCircuitBuilder.ThresholdProxyPaths)
        {
            var collider = Collider(context.V10, path);
            if (!collider.enabled || collider.isTrigger || !collider.gameObject.activeInHierarchy)
                result.Failures.Add("V12 inherited threshold proxy drifted: " + path);
        }
        foreach (var path in ChannelPlayKhufuV12QueenCircuitBuilder.V4QueenTargets)
        {
            var target = Require(context.V4.Find(path), path);
            var renderer = target.GetComponent<Renderer>();
            var collider = target.GetComponent<BoxCollider>();
            if (!target.gameObject.activeSelf || !target.gameObject.activeInHierarchy ||
                renderer == null || renderer.enabled || collider == null || collider.enabled || collider.isTrigger)
                result.Failures.Add("V4 Queen overlap state drifted: " + path);
        }
        var marker = Require(context.V4.Find("V4_Gameplay_Route/V4_Route_Queens_Chamber"), "V4 marker");
        var glow = Require(context.V4.Find("V4_Gameplay_Route/V4_Glow_Queens"), "V4 glow");
        var light = Require(context.V4.Find("V4_Lighting/V4_Light_Queens"), "V4 light");
        if (Vector3.Distance(marker.position, KhufuV10RouteContract.QueensChamber) > 0.001f ||
            marker.GetComponent<Renderer>().enabled || glow.GetComponent<Renderer>().enabled ||
            !light.GetComponent<Light>().enabled)
            result.Failures.Add("V4 marker/glow/light inherited state drifted.");
        var control = context.Root.GetComponentInChildren<KhufuV12TransitionControl>(true);
        if (control == null || control.GraniteFilter == null || control.QueenGate == null ||
            control.PredecessorGranite == null || control.SuccessorGranite == null ||
            AssetDatabase.GetAssetPath(control.PredecessorGranite) !=
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath ||
            AssetDatabase.GetAssetPath(control.SuccessorGranite) !=
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.V12OpenGranitePath ||
            control.GraniteFilter.sharedMesh != control.SuccessorGranite ||
            control.QueenGate.enabled)
            result.Failures.Add("V12 runtime transition-control asset binding drifted.");
    }

    private static void ValidateClearanceAndEnclosure(Transform root, ValidationResult result)
    {
        Physics.SyncTransforms();
        foreach (var point in KhufuV12QueenRouteContract.RoundTripRoute())
        {
            var hits = Physics.OverlapCapsule(point + Vector3.up * 0.40f,
                point + Vector3.up * 1.55f, 0.30f, ~0, QueryTriggerInteraction.Ignore);
            var owned = hits.Where(hit => hit.transform.IsChildOf(root)).Select(hit => hit.name)
                .Distinct(StringComparer.Ordinal).ToArray();
            if (owned.Length > 0)
                result.Failures.Add("V12 route clearance blocked at " + VectorToken(point) + ": " +
                                    string.Join(",", owned));
        }

        ValidateRay(root, new Vector3(-1.8f, 6.55f, -2.8f), Vector3.left, 3.2f,
            "Chamber_West_Wall", result);
        ValidateRay(root, new Vector3(-1.8f, 6.55f, -2.8f), Vector3.right, 3.2f,
            "Niche_Back_Boundary", result);
        ValidateRay(root, new Vector3(-1.8f, 6.55f, -2.8f), Vector3.forward, 3.2f,
            "Chamber_Back_Wall", result);
        ValidateRay(root, new Vector3(-3.35f, 6.55f, -2.8f), Vector3.back, 3.2f,
            "Entry_Wall_West", result);
        ValidateRay(root, new Vector3(-1.8f, 6.55f, -2.8f), Vector3.down, 2f,
            "Chamber_Floor", result);
        ValidateRay(root, new Vector3(-1.8f, 6.55f, -2.8f), Vector3.up, 3.2f,
            "Chamber_Roof", result);

        foreach (var token in new[] { "North_Narrow_Mouth_Boundary", "South_Narrow_Mouth_Boundary" })
        {
            var target = root.GetComponentsInChildren<BoxCollider>(true)
                .SingleOrDefault(item => item.name.Contains(token, StringComparison.Ordinal));
            if (target == null || !target.enabled || target.isTrigger)
                result.Failures.Add("V12 narrow-mouth boundary is not collision-sealed: " + token);
        }
    }

    private static void ValidateRay(Transform root, Vector3 origin, Vector3 direction, float distance,
        string token, ValidationResult result)
    {
        var hits = Physics.RaycastAll(origin, direction, distance, ~0, QueryTriggerInteraction.Ignore)
            .Where(hit => hit.collider.transform.IsChildOf(root))
            .OrderBy(hit => hit.distance).ToArray();
        if (hits.Length == 0 || !hits[0].collider.name.Contains(token, StringComparison.Ordinal))
            result.Failures.Add("V12 enclosure ray missed " + token + " from " + VectorToken(origin));
    }

    private static string ValidateV11RestoredContext(Context context, ValidationResult result)
    {
        var parent = context.Root.parent;
        var sibling = context.Root.GetSiblingIndex();
        var committedLimestone = Mesh(context.V10,
            ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath);
        var committedGranite = Mesh(context.V10,
            ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath);
        try
        {
            context.Root.SetParent(null, true);
            ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV11Context(context.V4, context.V10);
            var restored = InvokeV11();
            if (restored.Failures.Count != 0 ||
                restored.Signature != ChannelPlayKhufuV12QueenCircuitBuilder.V11RestoredSignature)
                result.Failures.Add("V11 restored-context validator/signature drifted: " +
                                    string.Join(" | ", restored.Failures));
            var metrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(context.Map);
            if (!MetricsMatch(metrics, 829, 65918, 47984, 567))
                result.Failures.Add("V11 restored-context map metrics drifted: " + MetricsToken(metrics));
            return restored.Signature;
        }
        finally
        {
            SetMesh(context.V10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath,
                committedLimestone);
            SetMesh(context.V10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath,
                committedGranite);
            ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV12Context(context.V4, context.V10);
            context.Root.SetParent(parent, false);
            context.Root.SetSiblingIndex(sibling);
            context.Root.localPosition = Vector3.zero;
            context.Root.localRotation = Quaternion.identity;
            context.Root.localScale = Vector3.one;
            Physics.SyncTransforms();
        }
    }

    private static V11Result InvokeV11()
    {
        var method = typeof(ChannelPlayKhufuV11RoyalCircuitValidator).GetMethod(
            "ValidateScene", BindingFlags.NonPublic | BindingFlags.Static);
        var raw = method?.Invoke(null, new object[] { false });
        if (raw == null) throw new InvalidOperationException("V11 validator result is missing.");
        var type = raw.GetType();
        var failures = type.GetField("Failures")?.GetValue(raw) as IEnumerable<string>;
        return new V11Result
        {
            Failures = failures?.ToList() ?? new List<string> { "V11 failures unavailable" },
            Signature = Convert.ToString(type.GetField("Signature")?.GetValue(raw))
        };
    }

    private static string ComputeSignature(Context context)
    {
        var lines = new List<string>();
        foreach (var node in context.Root.GetComponentsInChildren<Transform>(true)
                     .OrderBy(node => HierarchyPath(context.Root, node), StringComparer.Ordinal))
        {
            var path = HierarchyPath(context.Root, node);
            lines.Add("T|" + path + "|" + node.gameObject.activeSelf + "|" +
                      VectorToken(node.localPosition) + "|" + QuaternionToken(node.localRotation) + "|" +
                      VectorToken(node.localScale));
            var filter = node.GetComponent<MeshFilter>();
            if (filter != null && filter.sharedMesh != null)
                lines.Add("M|" + path + "|" + AssetDatabase.GetAssetPath(filter.sharedMesh) + "|" +
                          ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeometrySignature(filter.sharedMesh));
            var renderer = node.GetComponent<MeshRenderer>();
            if (renderer != null)
                lines.Add("R|" + path + "|" + renderer.enabled + "|" +
                          AssetDatabase.GetAssetPath(renderer.sharedMaterial));
            var collider = node.GetComponent<BoxCollider>();
            if (collider != null)
                lines.Add("C|" + path + "|" + collider.enabled + "|" + collider.isTrigger + "|" +
                          VectorToken(collider.center) + "|" + VectorToken(collider.size));
        }
        lines.Add("B|limestone|" + MeshPath(context.V10,
            ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath));
        lines.Add("B|granite|" + MeshPath(context.V10,
            ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath));
        lines.Add("B|great|" + Collider(context.V10,
            ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath).enabled);
        lines.Add("B|queen|" + Collider(context.V10,
            ChannelPlayKhufuV12QueenCircuitBuilder.QueenGateProxyPath).enabled);
        lines.Add("B|gallery-floor|" + Collider(context.V10,
            ChannelPlayKhufuV12QueenCircuitBuilder.GalleryFloorProxyPath).enabled);
        foreach (var path in ChannelPlayKhufuV12QueenCircuitBuilder.HistoricServiceProxyPaths)
            lines.Add("B|historic-service|" + path + "|" + Collider(context.V10, path).enabled);
        foreach (var path in ChannelPlayKhufuV12QueenCircuitBuilder.V4QueenTargets)
        {
            var target = Require(context.V4.Find(path), path);
            lines.Add("V4|" + path + "|" + target.gameObject.activeSelf + "|" +
                      target.GetComponent<Renderer>().enabled + "|" +
                      target.GetComponent<BoxCollider>().enabled + "|" +
                      target.GetComponent<BoxCollider>().isTrigger + "|" +
                      VectorToken(target.localPosition) + "|" + QuaternionToken(target.localRotation) + "|" +
                      VectorToken(target.localScale));
        }
        foreach (var path in new[]
                 {
                     ChannelPlayKhufuV12QueenCircuitBuilder.ClassificationPath,
                     ChannelPlayKhufuV12QueenCircuitBuilder.PerformanceBudgetPath,
                     ChannelPlayKhufuV12QueenCircuitBuilder.PrewriteAuditPath,
                     ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath,
                     ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath + ".meta",
                     ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath,
                     ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath + ".meta"
                 })
            lines.Add("F|" + path + "|" + Sha256File(path));
        var control = context.Root.GetComponentInChildren<KhufuV12TransitionControl>(true);
        if (control != null)
            lines.Add("CTRL|" + AssetDatabase.GetAssetPath(control.PredecessorGranite) + "|" +
                      AssetDatabase.GetAssetPath(control.SuccessorGranite) + "|" +
                      control.QueenGate.enabled);
        return Sha256Text(string.Join("\n", lines));
    }

    private static string GeneratedAssetSignature()
    {
        var roots = new[]
        {
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeneratedRoot,
            ChannelPlayKhufuV12QueenCircuitBuilder.MaterialRoot
        };
        var paths = roots.Where(Directory.Exists)
            .SelectMany(root => Directory.GetFiles(root, "*", SearchOption.AllDirectories))
            .Concat(roots.Select(root => root + ".meta").Where(File.Exists))
            .OrderBy(path => path, StringComparer.Ordinal).ToArray();
        return Sha256Text(string.Join("\n", paths.Select(path => path.Replace('\\', '/') + "|" +
                                                              Sha256File(path))));
    }

    private static Context OpenContext()
    {
        var map = Require(GameObject.Find(ChannelPlayKhufuV12QueenCircuitBuilder.MapRootName)?.transform,
            "shared map root");
        return new Context
        {
            Map = map,
            Root = Require(map.Find(ChannelPlayKhufuV12QueenCircuitBuilder.RootName), "V12 root"),
            V4 = Require(map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName), "V4 root"),
            V10 = Require(map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName), "V10 root")
        };
    }

    private static bool TransformMatches(Transform target,
        ChannelPlayKhufuV12QueenCircuitMeshPipeline.BoxSpec spec)
    {
        return Vector3.Distance(target.localPosition, spec.Position) <= 0.001f &&
               Quaternion.Angle(target.localRotation, spec.Rotation) <= 0.01f &&
               Vector3.Distance(target.localScale, spec.Scale) <= 0.001f;
    }

    private static Mesh Mesh(Transform root, string path)
    {
        var filter = Require(root.Find(path), path).GetComponent<MeshFilter>();
        if (filter == null || filter.sharedMesh == null)
            throw new InvalidOperationException("Required transition mesh is missing: " + path);
        return filter.sharedMesh;
    }

    private static string MeshPath(Transform root, string path)
    {
        return AssetDatabase.GetAssetPath(Mesh(root, path));
    }

    private static void SetMesh(Transform root, string path, Mesh mesh)
    {
        var filter = Require(root.Find(path), path).GetComponent<MeshFilter>();
        if (filter == null) throw new InvalidOperationException("Required mesh filter is missing: " + path);
        filter.sharedMesh = mesh;
    }

    private static BoxCollider Collider(Transform root, string path)
    {
        var collider = Require(root.Find(path), path).GetComponent<BoxCollider>();
        if (collider == null) throw new InvalidOperationException("Required collider is missing: " + path);
        return collider;
    }

    private static Transform Require(Transform target, string label)
    {
        if (target == null) throw new InvalidOperationException("Required V12 validation target is missing: " + label);
        return target;
    }

    private static bool MetricsMatch(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics,
        int renderers, int vertices, int triangles, int colliders)
    {
        return metrics.Renderers == renderers && metrics.Vertices == vertices &&
               metrics.Triangles == triangles && metrics.Colliders == colliders;
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
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
        return value.x.ToString("R") + "," + value.y.ToString("R") + "," + value.z.ToString("R");
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
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
    }

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value)))
                .Replace("-", string.Empty).ToLowerInvariant();
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V12 Static Validation\n\n");
        text.AppendLine("- Verdict: **" + (result.Failures.Count == 0 ? "passed" : "failed") + "**");
        text.AppendLine("- V12 signature: `" + result.Signature + "`");
        text.AppendLine("- V11 restored-context signature: `" + result.V11RestoredSignature + "`");
        text.AppendLine("- V11 committed-context signature: `" + result.V11CommittedSignature + "`");
        text.AppendLine("- Root metrics: `" + MetricsToken(result.RootMetrics) + "`");
        text.AppendLine("- Map metrics: `" + MetricsToken(result.MapMetrics) + "`");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V12_STATIC_VALIDATION: " +
                        (result.Failures.Count == 0 ? "passed" : "failed"));
        File.WriteAllText(ValidationPath, text.ToString(), new UTF8Encoding(false));
    }

    private sealed class Context
    {
        public Transform Map;
        public Transform Root;
        public Transform V4;
        public Transform V10;
    }

    private sealed class V11Result
    {
        public List<string> Failures = new List<string>();
        public string Signature = string.Empty;
    }

    private sealed class ValidationResult
    {
        public readonly List<string> Failures = new List<string>();
        public string Signature = string.Empty;
        public string V11RestoredSignature = string.Empty;
        public string V11CommittedSignature = string.Empty;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics RootMetrics =
            new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics MapMetrics =
            new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
    }
}

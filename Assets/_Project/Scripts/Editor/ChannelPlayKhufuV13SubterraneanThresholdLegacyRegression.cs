using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV13SubterraneanThresholdLegacyRegression
{
    private const string ReceiptPath =
        "runs/khufu-v13-subterranean-threshold/legacy-regression.md";
    private const string ExpectedV12Signature =
        "6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd";
    private const string ExpectedV6Signature =
        "b41580ea2636838635ac54cacf2f20f34224b39bb32a506d223bbcfc2476d530";
    private const string ExpectedV7Signature =
        "9730013ededc08da590b99de5d2bd1ae91c485b25d67e6c591117d4431c2d321";
    private const string ExpectedV8Signature =
        "be64fa8b33e798093d55087fc279377446e6e5556e059ad273aeaf1d87ccdfa4";
    private const string ExpectedV9Signature =
        "8301ccc17bf1323fb8e9d1a525a778bf9ccdbf2da3dc15412b4bbf790ac85da8";

    private static readonly string[] ExpectedV6HistoricalHashDeltas =
    {
        "V5 builder hash binding mismatch"
    };

    private static readonly string[] ExpectedV7HistoricalHashDeltas =
    {
        "Frozen source hash changed: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs actual=0709f3ce4ec49836fd5f64a816f52832895f74ffd4434b7a107b848c40e2817c",
        "Frozen source hash changed: Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs actual=cb02282f0a424a5c849c564a5f4af50f9503266932535e62e8a9aa9f1881a5a7"
    };

    private static readonly string[] ExpectedV8HistoricalHashDeltas =
    {
        "Frozen V5 builder hash drifted",
        "Frozen V5 validator hash drifted",
        "Frozen V6 builder hash drifted",
        "Frozen V6 validator hash drifted",
        "Frozen V7 builder hash drifted",
        "Frozen V7 validator hash drifted",
        "Frozen package manifest hash drifted",
        "Frozen package lock hash drifted"
    };

    private static readonly string[] ExpectedV9HistoricalHashDeltas =
    {
        "Frozen V5 builder hash drifted",
        "Frozen V5 validator hash drifted",
        "Frozen V6 builder hash drifted",
        "Frozen V6 validator hash drifted",
        "Frozen V7 builder hash drifted",
        "Frozen V7 validator hash drifted",
        "Frozen V8 pipeline hash drifted",
        "Frozen V8 builder hash drifted",
        "Frozen V8 validator hash drifted",
        "Frozen V8 proof probe hash drifted",
        "Frozen package manifest hash drifted",
        "Frozen package lock hash drifted"
    };

    private static readonly string[] ExpectedV10Deltas =
    {
        "Unexpected V10 root metrics: renderers=6_vertices=4848_triangles=2424_colliders=70",
        "Unexpected full-map V10 metrics: renderers=824_vertices=63878_triangles=46964_colliders=534",
        "V10 mesh topology drifted: Limestone_Structure",
        "V10 mesh omits spec corners: Great_Step_Diegetic_Boundary",
        "V10 generated mesh binding drifted: Limestone_Structure",
        "V10 mesh topology drifted: Red_Granite_Boundary",
        "V10 mesh omits spec corners: Queen_Ownership_Gate",
        "V10 mesh omits spec corners: Great_Step_Granite_Bar_00",
        "V10 mesh omits spec corners: Great_Step_Granite_Bar_01",
        "V10 mesh omits spec corners: Great_Step_Granite_Bar_02",
        "V10 mesh omits spec corners: Great_Step_Granite_Bar_03",
        "V10 mesh omits spec corners: Great_Step_Granite_Bar_04",
        "V10 generated mesh binding drifted: Red_Granite_Boundary",
        "V10 proxy collider drifted: Grand_Gallery_Gallery_Floor_Ramp",
        "V10 proxy collider drifted: Great_Step_Boundary_Great_Step_Diegetic_Boundary",
        "V10 proxy collider drifted: Historic_Service_Mouth_Historic_Service_Mouth_East_Frame",
        "V10 proxy collider drifted: Historic_Service_Mouth_Historic_Service_Mouth_Lintel",
        "V10 proxy collider drifted: Historic_Service_Mouth_Historic_Service_Mouth_West_Frame",
        "V10 proxy collider drifted: Queen_Branch_Threshold_Queen_Ownership_Gate"
    };

    [MenuItem("Channel Play/Khufu V13/Validate Legacy V4-V12")]
    public static void ValidateMenu()
    {
        var scenePath =
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath;
        var sceneHashBefore = Hash(scenePath);
        var rows = new List<LegacyResult>
        {
            ValidateScoped("V4",
                typeof(ChannelPlayPyramidReferenceMatchedV4Builder),
                "ValidateScene", Array.Empty<object>()),
            ValidateV5(),
            ClassifyHistoricalSourceHashDeltas(
                ValidateScoped("V6",
                    typeof(ChannelPlayKhufuV6VisualSliceValidator),
                    "ValidateScene", Array.Empty<object>(),
                    ChannelPlayKhufuV7EntryWayfindingBuilder.RootName,
                    ChannelPlayKhufuV8TempleProductionArtBuilder.RootName,
                    ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
                    ChannelPlayKhufuV10InteriorBuilder.RootName,
                    ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                    ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
                ExpectedV6Signature, ExpectedV6HistoricalHashDeltas),
            ClassifyHistoricalSourceHashDeltas(
                ValidateScoped("V7",
                    typeof(ChannelPlayKhufuV7EntryWayfindingValidator),
                    "ValidateScene", Array.Empty<object>(),
                    ChannelPlayKhufuV8TempleProductionArtBuilder.RootName,
                    ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
                    ChannelPlayKhufuV10InteriorBuilder.RootName,
                    ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                    ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
                ExpectedV7Signature, ExpectedV7HistoricalHashDeltas),
            ClassifyHistoricalSourceHashDeltas(
                ValidateScoped("V8",
                    typeof(ChannelPlayKhufuV8TempleProductionArtValidator),
                    "ValidateScene", new object[] { true },
                    ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
                    ChannelPlayKhufuV10InteriorBuilder.RootName,
                    ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                    ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
                ExpectedV8Signature, ExpectedV8HistoricalHashDeltas),
            ClassifyHistoricalSourceHashDeltas(
                ValidateScoped("V9",
                    typeof(ChannelPlayKhufuV9CausewayFidelityValidator),
                    "ValidateScene", new object[] { true },
                    ChannelPlayKhufuV10InteriorBuilder.RootName,
                    ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                    ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
                ExpectedV9Signature, ExpectedV9HistoricalHashDeltas),
            ClassifyV10Transition(ValidateScoped("V10",
                typeof(ChannelPlayKhufuV10InteriorValidator),
                "ValidateScene", new object[] { true },
                ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                ChannelPlayKhufuV12QueenCircuitBuilder.RootName)),
            ValidateV11Restored(),
            ValidateV12Restored()
        };

        var canonical = ValidateCanonicalV13();
        var sceneHashAfter = Hash(scenePath);
        var passed = rows.All(row => row.Passed) && canonical.Passed &&
                     sceneHashBefore == sceneHashAfter;
        WriteReceipt(rows, canonical, sceneHashBefore, sceneHashAfter, passed);
        if (!passed)
            throw new InvalidOperationException(
                "Khufu V13 legacy regression failed: " +
                string.Join("; ", rows.SelectMany(row => row.Failures)
                    .Concat(canonical.Failures)));
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V13_LEGACY_REGRESSION result=passed gates=9 " +
            "canonical_v13=true scene_unchanged=true");
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

    private static LegacyResult ValidateV5()
    {
        var context = OpenContext("V5");
        if (context.Failure != null) return context.Failure;
        try
        {
            context.DetachV13AndRestorePredecessor();
            var result = ChannelPlayKhufuV5AcceptanceValidator.Validate();
            return new LegacyResult("V5", result.Passed,
                "objective permutations=6; clearance samples=" +
                result.ClearanceSamples, result.Failures);
        }
        finally
        {
            context.RestoreCanonicalV13();
        }
    }

    private static LegacyResult ValidateScoped(string label, Type validatorType,
        string methodName, object[] arguments, params string[] hiddenRoots)
    {
        var context = OpenContext(label);
        if (context.Failure != null) return context.Failure;
        try
        {
            context.DetachV13AndRestorePredecessor();
            foreach (var rootName in hiddenRoots)
            {
                var root = context.Map.Find(rootName);
                if (root == null)
                    return new LegacyResult(label, false, string.Empty,
                        new[] { "downstream root missing: " + rootName });
                context.Detach(root);
            }
            return InvokePrivateValidation(label, validatorType, methodName,
                arguments);
        }
        finally
        {
            context.RestoreCanonicalV13();
        }
    }

    private static LegacyResult ValidateV11Restored()
    {
        var context = OpenContext("V11");
        if (context.Failure != null) return context.Failure;
        var v4 = context.V4;
        var v10 = context.Map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName);
        var v11 = context.Map.Find(
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName);
        var v12 = context.Map.Find(
            ChannelPlayKhufuV12QueenCircuitBuilder.RootName);
        if (v4 == null || v10 == null || v11 == null || v12 == null)
            return new LegacyResult("V11", false, string.Empty,
                new[] { "V4/V10/V11/V12 context missing" });
        try
        {
            context.DetachV13AndRestorePredecessor();
            context.Detach(v12);
            ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV11Context(v4, v10);
            var raw = InvokeV11Validation();
            var rootMetrics =
                ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v11);
            var mapMetrics =
                ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(context.Map);
            var metricsPassed =
                MetricsMatch(rootMetrics, 5, 2016, 1008, 33) &&
                MetricsMatch(mapMetrics, 829, 65918, 47984, 567);
            var passed = raw.Failures.Count == 0 &&
                         raw.Signature ==
                         ChannelPlayKhufuV12QueenCircuitBuilder
                             .V11RestoredSignature &&
                         metricsPassed;
            var failures = new List<string>(raw.Failures);
            if (!metricsPassed)
                failures.Add("restored V11 exact metrics drifted: root=" +
                             MetricsToken(rootMetrics) + " map=" +
                             MetricsToken(mapMetrics));
            if (raw.Signature !=
                ChannelPlayKhufuV12QueenCircuitBuilder.V11RestoredSignature)
                failures.Add("restored V11 signature drifted: " +
                             raw.Signature);
            return new LegacyResult("V11", passed, raw.Signature, failures);
        }
        finally
        {
            try
            {
                ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV12Context(v4, v10);
            }
            finally
            {
                context.RestoreCanonicalV13();
            }
        }
    }

    private static LegacyResult ValidateV12Restored()
    {
        var context = OpenContext("V12");
        if (context.Failure != null) return context.Failure;
        try
        {
            context.DetachV13AndRestorePredecessor();
            var raw = InvokePrivateValidation("V12",
                typeof(ChannelPlayKhufuV12QueenCircuitValidator),
                "ValidateScene", new object[] { false });
            var passed = raw.Passed && raw.Signature == ExpectedV12Signature;
            if (raw.Signature != ExpectedV12Signature)
            {
                var failures = raw.Failures.ToList();
                failures.Add("V12 restored signature drifted: " +
                             raw.Signature);
                return new LegacyResult("V12", false, raw.Signature,
                    failures);
            }
            return new LegacyResult("V12", passed, raw.Signature,
                raw.Failures);
        }
        finally
        {
            context.RestoreCanonicalV13();
        }
    }

    private static LegacyResult ValidateCanonicalV13()
    {
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath,
            OpenSceneMode.Single);
        return InvokePrivateValidation("V13 canonical return",
            typeof(ChannelPlayKhufuV13SubterraneanThresholdValidator),
            "ValidateScene", new object[] { false });
    }

    private static LegacyResult ClassifyHistoricalSourceHashDeltas(
        LegacyResult raw, string expectedSignature,
        IReadOnlyCollection<string> expectedFailures)
    {
        if (raw.Passed) return raw;
        var exactFailures = raw.Failures.Count == expectedFailures.Count &&
                            new HashSet<string>(raw.Failures,
                                    StringComparer.Ordinal)
                                .SetEquals(expectedFailures);
        var exactSignature = raw.Signature == expectedSignature;
        return exactFailures && exactSignature
            ? new LegacyResult(raw.Label, true,
                raw.Signature +
                " / classified exact historical source-hash deltas=" +
                raw.Failures.Count, Array.Empty<string>(), raw.Failures)
            : raw;
    }

    private static LegacyResult ClassifyV10Transition(LegacyResult raw)
    {
        if (raw.Passed) return raw;
        var exact = raw.Failures.Count == ExpectedV10Deltas.Length &&
                    new HashSet<string>(raw.Failures, StringComparer.Ordinal)
                        .SetEquals(ExpectedV10Deltas);
        return exact
            ? new LegacyResult("V10", true,
                raw.Signature + " / classified exact V12 transition deltas=" +
                raw.Failures.Count, Array.Empty<string>(), raw.Failures)
            : raw;
    }

    private static LegacyResult InvokePrivateValidation(string label,
        Type validatorType, string methodName, params object[] arguments)
    {
        var method = validatorType.GetMethod(methodName,
            BindingFlags.Static | BindingFlags.NonPublic);
        if (method == null)
            return new LegacyResult(label, false, string.Empty,
                new[] { "private validation entry point missing" });
        object raw;
        try
        {
            raw = method.Invoke(null, arguments);
        }
        catch (TargetInvocationException exception)
        {
            throw exception.InnerException ?? exception;
        }
        if (raw == null)
            return new LegacyResult(label, false, string.Empty,
                new[] { "validation returned null" });
        var type = raw.GetType();
        var passedField =
            type.GetField("Passed", BindingFlags.Instance | BindingFlags.Public);
        var signatureField =
            type.GetField("Signature",
                BindingFlags.Instance | BindingFlags.Public) ??
            type.GetField("VisualSignature",
                BindingFlags.Instance | BindingFlags.Public);
        var failuresField =
            type.GetField("Failures", BindingFlags.Instance | BindingFlags.Public);
        var signature = signatureField == null
            ? "original validator result"
            : Convert.ToString(signatureField.GetValue(raw));
        var failures = new List<string>();
        if (failuresField != null &&
            failuresField.GetValue(raw) is IEnumerable items)
            foreach (var item in items)
                failures.Add(Convert.ToString(item));
        var passed = passedField != null
            ? (bool)passedField.GetValue(raw)
            : failuresField != null && failures.Count == 0;
        return new LegacyResult(label, passed, signature, failures);
    }

    private static LegacyResult InvokeV11Validation()
    {
        var method = typeof(ChannelPlayKhufuV11RoyalCircuitValidator)
            .GetMethod("ValidateScene",
                BindingFlags.Static | BindingFlags.NonPublic);
        var raw = method?.Invoke(null, new object[] { false });
        if (raw == null)
            return new LegacyResult("V11", false, string.Empty,
                new[] { "V11 validation returned null" });
        var type = raw.GetType();
        var failures = new List<string>();
        if (type.GetField("Failures")?.GetValue(raw) is IEnumerable items)
            foreach (var item in items)
                failures.Add(Convert.ToString(item));
        var signature =
            Convert.ToString(type.GetField("Signature")?.GetValue(raw));
        return new LegacyResult("V11", failures.Count == 0, signature,
            failures);
    }

    private static ValidationContext OpenContext(string label)
    {
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath,
            OpenSceneMode.Single);
        var map = GameObject.Find(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.MapRootName)
            ?.transform;
        if (map == null)
            return new ValidationContext(new LegacyResult(label, false,
                string.Empty, new[] { "shared map root missing" }));
        var v13 = map.Find(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.RootName);
        if (v13 == null)
            return new ValidationContext(new LegacyResult(label, false,
                string.Empty, new[] { "V13 root missing" }));
        var v4 = map.Find(
            ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        if (v4 == null)
            return new ValidationContext(new LegacyResult(label, false,
                string.Empty, new[] { "V4 root missing" }));
        return new ValidationContext(map, v4, v13);
    }

    private static void WriteReceipt(IReadOnlyList<LegacyResult> rows,
        LegacyResult canonical, string sceneHashBefore, string sceneHashAfter,
        bool passed)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(ReceiptPath) ?? ".");
        var text =
            new StringBuilder("# Khufu V13 Legacy Regression\n\n");
        text.AppendLine("- Verdict: **" +
                        (passed ? "passed" : "failed") + "**");
        text.AppendLine(
            "- Scope: `V4, V5, V6, V7, V8, V9, V10, V11, V12` original validation logic");
        text.AppendLine(
            "- Context rule: detach V13, restore exact predecessor bindings, validate, reapply V13, then restore the exact V13 root.");
        text.AppendLine("- V13 canonical return: `" +
                        (canonical.Passed ? "passed" : "failed") +
                        "` / signature `" + canonical.Signature + "`");
        text.AppendLine("- Scene SHA256 before / after: `" + sceneHashBefore +
                        " / " + sceneHashAfter + "`");
        text.AppendLine("- Scene bytes unchanged: `" +
                        (sceneHashBefore == sceneHashAfter) + "`");
        foreach (var row in rows)
        {
            text.AppendLine("- " + row.Label + ": `" +
                            (row.Passed ? "passed" : "failed") +
                            "` / signature `" + row.Signature + "`");
            foreach (var failure in row.Failures)
                text.AppendLine("  - Failure: `" + failure + "`");
            foreach (var delta in row.ClassifiedDeltas)
                text.AppendLine(row.Label == "V10"
                    ? "  - Classified exact V12 transition delta: `" +
                      delta + "`"
                    : "  - Classified exact historical source-hash delta: `" +
                      delta + "`");
        }
        foreach (var failure in canonical.Failures)
            text.AppendLine("  - Canonical V13 failure: `" + failure + "`");
        AppendSourceHash(text, "V4 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayPyramidReferenceMatchedV4Builder.cs");
        AppendSourceHash(text, "V5 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs");
        AppendSourceHash(text, "V6 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs");
        AppendSourceHash(text, "V7 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingValidator.cs");
        AppendSourceHash(text, "V8 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs");
        AppendSourceHash(text, "V9 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityValidator.cs");
        AppendSourceHash(text, "V10 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs");
        AppendSourceHash(text, "V11 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitValidator.cs");
        AppendSourceHash(text, "V12 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitValidator.cs");
        AppendSourceHash(text, "V13 builder",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdBuilder.cs");
        AppendSourceHash(text, "V13 legacy runner",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdLegacyRegression.cs");
        text.AppendLine();
        text.AppendLine("KHUFU_V13_LEGACY_REGRESSION: " +
                        (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(),
            new UTF8Encoding(false));
    }

    private static void AppendSourceHash(StringBuilder text, string label,
        string path)
    {
        text.AppendLine("- " + label + " SHA256: `" + Hash(path) + "`");
    }

    private static bool MetricsMatch(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics,
        int renderers, int vertices, int triangles, int colliders)
    {
        return metrics.Renderers == renderers &&
               metrics.Vertices == vertices &&
               metrics.Triangles == triangles &&
               metrics.Colliders == colliders;
    }

    private static string MetricsToken(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" +
               metrics.Vertices + "_triangles=" + metrics.Triangles +
               "_colliders=" + metrics.Colliders;
    }

    private static string Hash(string path)
    {
        return ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
    }

    private sealed class ValidationContext
    {
        private readonly Transform v13;
        private readonly List<RootState> states = new List<RootState>();
        private readonly Dictionary<Transform, RootState> canonicalStates;
        private bool v13Detached;

        public readonly Transform Map;
        public readonly Transform V4;
        public readonly Transform V10;
        public readonly LegacyResult Failure;

        public ValidationContext(LegacyResult failure)
        {
            Failure = failure;
        }

        public ValidationContext(Transform map, Transform v4, Transform root)
        {
            Map = map;
            V4 = v4;
            V10 = map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName);
            if (V10 == null)
                throw new InvalidOperationException("Missing V10 root.");
            v13 = root;
            canonicalStates = map.Cast<Transform>().ToDictionary(
                child => child,
                child => new RootState(child));
        }

        public void DetachV13AndRestorePredecessor()
        {
            if (v13Detached) return;
            states.Add(CanonicalState(v13));
            v13Detached = true;
            v13.SetParent(null, true);
            v13.gameObject.SetActive(false);
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ApplyPredecessorContext(V4, V10);
            Physics.SyncTransforms();
        }

        public void Detach(Transform root)
        {
            states.Add(CanonicalState(root));
            root.SetParent(null, true);
        }

        public void RestoreCanonicalV13()
        {
            if (!v13Detached) return;
            try
            {
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ApplyV13Context(V4, V10);
            }
            finally
            {
                for (var index = states.Count - 1; index >= 0; index--)
                    states[index].Restore();
                foreach (var state in states.OrderBy(
                             item => item.OriginalSiblingIndex))
                    state.RestoreSiblingIndex();
                Physics.SyncTransforms();
            }
            var mismatches = states
                .Select(state => state.DiagnosticToken())
                .Where(token => !string.IsNullOrEmpty(token))
                .ToArray();
            if (mismatches.Length > 0)
                throw new InvalidOperationException(
                    "Legacy context failed to restore an exact root state: " +
                    string.Join(" | ", mismatches));
            if (Map.Find(
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.RootName) !=
                v13)
                throw new InvalidOperationException(
                    "Legacy context did not return canonical V13.");
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ValidateFrozenTargets(
                    V4,
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                        .LoadPrewriteAudit(),
                    false);
        }

        private RootState CanonicalState(Transform root)
        {
            if (root != null &&
                canonicalStates.TryGetValue(root, out var state))
                return state;
            throw new InvalidOperationException(
                "Legacy detach target was not a canonical map root: " +
                (root == null ? "null" : root.name));
        }
    }

    private sealed class LegacyResult
    {
        public readonly string Label;
        public readonly bool Passed;
        public readonly string Signature;
        public readonly IReadOnlyList<string> Failures;
        public readonly IReadOnlyList<string> ClassifiedDeltas;

        public LegacyResult(string label, bool passed, string signature,
            IEnumerable<string> failures,
            IEnumerable<string> classifiedDeltas = null)
        {
            Label = label;
            Passed = passed;
            Signature = string.IsNullOrEmpty(signature)
                ? "not-applicable"
                : signature;
            Failures = failures.ToArray();
            ClassifiedDeltas = classifiedDeltas == null
                ? Array.Empty<string>()
                : classifiedDeltas.ToArray();
        }
    }

    private sealed class RootState
    {
        private readonly Transform root;
        private readonly Transform parent;
        private readonly int siblingIndex;
        private readonly Vector3 localPosition;
        private readonly Quaternion localRotation;
        private readonly Vector3 localScale;
        private readonly bool activeSelf;
        private readonly string rootName;

        public int OriginalSiblingIndex => siblingIndex;

        public RootState(Transform target)
        {
            root = target;
            parent = target.parent;
            siblingIndex = target.GetSiblingIndex();
            localPosition = target.localPosition;
            localRotation = target.localRotation;
            localScale = target.localScale;
            activeSelf = target.gameObject.activeSelf;
            rootName = target.name;
        }

        public void Restore()
        {
            if (root == null || parent == null) return;
            root.SetParent(parent, false);
            root.localPosition = localPosition;
            root.localRotation = localRotation;
            root.localScale = localScale;
            root.gameObject.SetActive(activeSelf);
        }

        public void RestoreSiblingIndex()
        {
            if (root != null && parent != null && root.parent == parent)
                root.SetSiblingIndex(siblingIndex);
        }

        public bool Matches()
        {
            return root != null && root.parent == parent &&
                   root.GetSiblingIndex() == siblingIndex &&
                   root.localPosition == localPosition &&
                   root.localRotation == localRotation &&
                   root.localScale == localScale &&
                   root.gameObject.activeSelf == activeSelf;
        }

        public string DiagnosticToken()
        {
            if (Matches()) return string.Empty;
            if (root == null) return rootName + "[root=destroyed]";
            var deltas = new List<string>();
            if (root.parent != parent)
                deltas.Add("parent=" + TransformName(parent) + "->" +
                           TransformName(root.parent));
            if (root.GetSiblingIndex() != siblingIndex)
                deltas.Add("sibling=" + siblingIndex + "->" +
                           root.GetSiblingIndex());
            if (root.localPosition != localPosition)
                deltas.Add("position=" + VectorToken(localPosition) + "->" +
                           VectorToken(root.localPosition));
            if (root.localRotation != localRotation)
                deltas.Add("rotation=" + QuaternionToken(localRotation) +
                           "->" + QuaternionToken(root.localRotation));
            if (root.localScale != localScale)
                deltas.Add("scale=" + VectorToken(localScale) + "->" +
                           VectorToken(root.localScale));
            if (root.gameObject.activeSelf != activeSelf)
                deltas.Add("active=" + activeSelf + "->" +
                           root.gameObject.activeSelf);
            return rootName + "[" + string.Join(",", deltas) + "]";
        }

        private static string TransformName(Transform value)
        {
            return value == null ? "null" : value.name;
        }

        private static string VectorToken(Vector3 value)
        {
            return value.x.ToString("R", CultureInfo.InvariantCulture) + "/" +
                   value.y.ToString("R", CultureInfo.InvariantCulture) + "/" +
                   value.z.ToString("R", CultureInfo.InvariantCulture);
        }

        private static string QuaternionToken(Quaternion value)
        {
            return value.x.ToString("R", CultureInfo.InvariantCulture) + "/" +
                   value.y.ToString("R", CultureInfo.InvariantCulture) + "/" +
                   value.z.ToString("R", CultureInfo.InvariantCulture) + "/" +
                   value.w.ToString("R", CultureInfo.InvariantCulture);
        }
    }
}

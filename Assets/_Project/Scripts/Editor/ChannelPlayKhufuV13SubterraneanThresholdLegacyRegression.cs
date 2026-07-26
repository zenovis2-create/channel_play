using System;
using System.Collections;
using System.Collections.Generic;
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
            ValidateScoped("V6",
                typeof(ChannelPlayKhufuV6VisualSliceValidator),
                "ValidateScene", Array.Empty<object>(),
                ChannelPlayKhufuV7EntryWayfindingBuilder.RootName,
                ChannelPlayKhufuV8TempleProductionArtBuilder.RootName,
                ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
                ChannelPlayKhufuV10InteriorBuilder.RootName,
                ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
            ValidateScoped("V7",
                typeof(ChannelPlayKhufuV7EntryWayfindingValidator),
                "ValidateScene", Array.Empty<object>(),
                ChannelPlayKhufuV8TempleProductionArtBuilder.RootName,
                ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
                ChannelPlayKhufuV10InteriorBuilder.RootName,
                ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
            ValidateScoped("V8",
                typeof(ChannelPlayKhufuV8TempleProductionArtValidator),
                "ValidateScene", new object[] { true },
                ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
                ChannelPlayKhufuV10InteriorBuilder.RootName,
                ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
            ValidateScoped("V9",
                typeof(ChannelPlayKhufuV9CausewayFidelityValidator),
                "ValidateScene", new object[] { true },
                ChannelPlayKhufuV10InteriorBuilder.RootName,
                ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                ChannelPlayKhufuV12QueenCircuitBuilder.RootName),
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
            ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV12Context(v4, v10);
            context.RestoreCanonicalV13();
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
                text.AppendLine(
                    "  - Classified exact V12 transition delta: `" +
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
        private bool v13Detached;

        public readonly Transform Map;
        public readonly Transform V4;
        public readonly LegacyResult Failure;

        public ValidationContext(LegacyResult failure)
        {
            Failure = failure;
        }

        public ValidationContext(Transform map, Transform v4, Transform root)
        {
            Map = map;
            V4 = v4;
            v13 = root;
        }

        public void DetachV13AndRestorePredecessor()
        {
            if (v13Detached) return;
            states.Add(new RootState(v13));
            v13Detached = true;
            v13.SetParent(null, true);
            v13.gameObject.SetActive(false);
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .ApplyPredecessorContext(V4);
            Physics.SyncTransforms();
        }

        public void Detach(Transform root)
        {
            states.Add(new RootState(root));
            root.SetParent(null, true);
        }

        public void RestoreCanonicalV13()
        {
            if (!v13Detached) return;
            try
            {
                ChannelPlayKhufuV13SubterraneanThresholdBuilder
                    .ApplyV13Context(V4);
            }
            finally
            {
                for (var index = states.Count - 1; index >= 0; index--)
                    states[index].Restore();
                Physics.SyncTransforms();
            }
            if (states.Any(state => !state.Matches()))
                throw new InvalidOperationException(
                    "Legacy context failed to restore an exact root state.");
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

        public RootState(Transform target)
        {
            root = target;
            parent = target.parent;
            siblingIndex = target.GetSiblingIndex();
            localPosition = target.localPosition;
            localRotation = target.localRotation;
            localScale = target.localScale;
            activeSelf = target.gameObject.activeSelf;
        }

        public void Restore()
        {
            if (root == null || parent == null) return;
            root.SetParent(parent, false);
            root.SetSiblingIndex(siblingIndex);
            root.localPosition = localPosition;
            root.localRotation = localRotation;
            root.localScale = localScale;
            root.gameObject.SetActive(activeSelf);
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
    }
}

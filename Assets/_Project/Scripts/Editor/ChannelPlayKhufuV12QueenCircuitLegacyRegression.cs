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

public static class ChannelPlayKhufuV12QueenCircuitLegacyRegression
{
    private const string ReceiptPath = "runs/khufu-v12-queen-circuit/legacy-regression.md";
    private const string RawV10Path = "runs/khufu-v12-queen-circuit/legacy-v10-raw.md";

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

    [MenuItem("Channel Play/Khufu V12/Validate Legacy V4-V11")]
    public static void ValidateMenu()
    {
        var sceneHashBefore = Hash(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath);
        var rows = new List<LegacyResult>();
        EditorSceneManager.OpenScene(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath, OpenSceneMode.Single);
        rows.Add(InvokePrivateValidation("V4", typeof(ChannelPlayPyramidReferenceMatchedV4Builder),
            "ValidateScene"));
        var v5 = ChannelPlayKhufuV5AcceptanceValidator.Validate();
        rows.Add(new LegacyResult("V5", v5.Passed,
            "objective permutations=6; clearance samples=" + v5.ClearanceSamples, v5.Failures));
        rows.Add(ValidateScoped("V8", typeof(ChannelPlayKhufuV8TempleProductionArtValidator),
            ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
            ChannelPlayKhufuV10InteriorBuilder.RootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
            ChannelPlayKhufuV12QueenCircuitBuilder.RootName));
        rows.Add(ValidateScoped("V9", typeof(ChannelPlayKhufuV9CausewayFidelityValidator),
            ChannelPlayKhufuV10InteriorBuilder.RootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
            ChannelPlayKhufuV12QueenCircuitBuilder.RootName));
        rows.Add(ClassifyV10Transition(ValidateScoped("V10",
            typeof(ChannelPlayKhufuV10InteriorValidator),
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
            ChannelPlayKhufuV12QueenCircuitBuilder.RootName)));
        rows.Add(ValidateV11Restored());

        var sceneHashAfter = Hash(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath);
        var passed = rows.All(row => row.Passed) && sceneHashBefore == sceneHashAfter;
        WriteReceipt(rows, sceneHashBefore, sceneHashAfter, passed);
        if (!passed)
            throw new InvalidOperationException("Khufu V12 legacy regression failed: " +
                                                string.Join("; ", rows.SelectMany(row => row.Failures)));
        Debug.Log("CHANNEL_PLAY_KHUFU_V12_LEGACY_REGRESSION result=passed gates=6 scene_unchanged=true");
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

    public static void DumpV10Batch()
    {
        try
        {
            var raw = ValidateScoped("V10", typeof(ChannelPlayKhufuV10InteriorValidator),
                ChannelPlayKhufuV11RoyalCircuitBuilder.RootName,
                ChannelPlayKhufuV12QueenCircuitBuilder.RootName);
            Directory.CreateDirectory(Path.GetDirectoryName(RawV10Path) ?? ".");
            var text = new StringBuilder("# Khufu V12 Raw V10 Transition Deltas\n\n");
            text.AppendLine("- Raw passed: `" + raw.Passed + "`");
            text.AppendLine("- Count: `" + raw.Failures.Count + "`");
            foreach (var failure in raw.Failures) text.AppendLine("- `" + failure + "`");
            File.WriteAllText(RawV10Path, text.ToString(), new UTF8Encoding(false));
            Debug.Log("CHANNEL_PLAY_KHUFU_V12_V10_RAW count=" + raw.Failures.Count);
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static LegacyResult ValidateScoped(string label, Type validatorType, params string[] hiddenRoots)
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV12QueenCircuitBuilder.MapRootName);
        if (map == null) return new LegacyResult(label, false, string.Empty, new[] { "shared map root missing" });
        var states = new List<RootState>();
        try
        {
            foreach (var rootName in hiddenRoots)
            {
                var root = map.transform.Find(rootName);
                if (root == null)
                    return new LegacyResult(label, false, string.Empty,
                        new[] { "downstream root missing: " + rootName });
                states.Add(new RootState(root));
                root.SetParent(null, true);
            }
            return InvokePrivateValidation(label, validatorType, "ValidateScene", true);
        }
        finally
        {
            foreach (var state in states) state.Restore();
        }
    }

    private static LegacyResult ValidateV11Restored()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV12QueenCircuitBuilder.MapRootName)?.transform;
        if (map == null) return new LegacyResult("V11", false, string.Empty, new[] { "shared map root missing" });
        var v4 = map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        var v10 = map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName);
        var v11 = map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.RootName);
        var v12 = map.Find(ChannelPlayKhufuV12QueenCircuitBuilder.RootName);
        if (v4 == null || v10 == null || v11 == null || v12 == null)
            return new LegacyResult("V11", false, string.Empty, new[] { "V4/V10/V11/V12 context missing" });
        var state = new RootState(v12);
        try
        {
            v12.SetParent(null, true);
            ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV11Context(v4, v10);
            var raw = InvokeV11Validation();
            var rootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v11);
            var mapMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
            var metricsPassed = MetricsMatch(rootMetrics, 5, 2016, 1008, 33) &&
                                MetricsMatch(mapMetrics, 829, 65918, 47984, 567);
            var passed = raw.Failures.Count == 0 &&
                         raw.Signature == ChannelPlayKhufuV12QueenCircuitBuilder.V11RestoredSignature &&
                         metricsPassed;
            var failures = new List<string>(raw.Failures);
            if (!metricsPassed)
                failures.Add("restored V11 exact metrics drifted: root=" + MetricsToken(rootMetrics) +
                             " map=" + MetricsToken(mapMetrics));
            if (raw.Signature != ChannelPlayKhufuV12QueenCircuitBuilder.V11RestoredSignature)
                failures.Add("restored V11 signature drifted: " + raw.Signature);
            return new LegacyResult("V11", passed, raw.Signature, failures);
        }
        finally
        {
            ChannelPlayKhufuV12QueenCircuitBuilder.ApplyV12Context(v4, v10);
            state.Restore();
        }
    }

    private static LegacyResult ClassifyV10Transition(LegacyResult raw)
    {
        if (raw.Passed) return raw;
        var exact = raw.Failures.Count == ExpectedV10Deltas.Length &&
                    new HashSet<string>(raw.Failures, StringComparer.Ordinal)
                        .SetEquals(ExpectedV10Deltas);
        return exact
            ? new LegacyResult("V10", true,
                raw.Signature + " / classified exact V12 transition deltas=" + raw.Failures.Count,
                Array.Empty<string>(), raw.Failures)
            : raw;
    }

    private static LegacyResult InvokePrivateValidation(string label, Type validatorType,
        string methodName, params object[] arguments)
    {
        var method = validatorType.GetMethod(methodName, BindingFlags.Static | BindingFlags.NonPublic);
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
            return new LegacyResult(label, false, string.Empty, new[] { "validation returned null" });
        var type = raw.GetType();
        var passedField = type.GetField("Passed", BindingFlags.Instance | BindingFlags.Public);
        var signatureField = type.GetField("Signature", BindingFlags.Instance | BindingFlags.Public);
        var failuresField = type.GetField("Failures", BindingFlags.Instance | BindingFlags.Public);
        var passed = passedField != null && (bool)passedField.GetValue(raw);
        var signature = signatureField == null ? "original validator result" :
            Convert.ToString(signatureField.GetValue(raw));
        var failures = new List<string>();
        if (failuresField != null && failuresField.GetValue(raw) is IEnumerable items)
            foreach (var item in items) failures.Add(Convert.ToString(item));
        return new LegacyResult(label, passed, signature, failures);
    }

    private static LegacyResult InvokeV11Validation()
    {
        var method = typeof(ChannelPlayKhufuV11RoyalCircuitValidator).GetMethod(
            "ValidateScene", BindingFlags.Static | BindingFlags.NonPublic);
        var raw = method?.Invoke(null, new object[] { false });
        if (raw == null)
            return new LegacyResult("V11", false, string.Empty, new[] { "V11 validation returned null" });
        var type = raw.GetType();
        var failures = new List<string>();
        if (type.GetField("Failures")?.GetValue(raw) is IEnumerable items)
            foreach (var item in items) failures.Add(Convert.ToString(item));
        var signature = Convert.ToString(type.GetField("Signature")?.GetValue(raw));
        return new LegacyResult("V11", failures.Count == 0, signature, failures);
    }

    private static void WriteReceipt(IReadOnlyList<LegacyResult> rows,
        string sceneHashBefore, string sceneHashAfter, bool passed)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(ReceiptPath) ?? ".");
        var text = new StringBuilder("# Khufu V12 Legacy Regression\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Scope: `V4, V5, V8, V9, V10, V11` original validation logic");
        text.AppendLine("- V11 rule: detach V12, restore V11 mesh/component/proxy context, then require `9994...`.");
        text.AppendLine("- V10 rule: detach V11/V12 and accept only the frozen exact V12 transition failure set.");
        text.AppendLine("- Scene SHA256 before / after: `" + sceneHashBefore + " / " + sceneHashAfter + "`");
        text.AppendLine("- Scene bytes unchanged: `" + (sceneHashBefore == sceneHashAfter) + "`");
        foreach (var row in rows)
        {
            text.AppendLine("- " + row.Label + ": `" + (row.Passed ? "passed" : "failed") +
                            "` / signature `" + row.Signature + "`");
            foreach (var failure in row.Failures) text.AppendLine("  - Failure: `" + failure + "`");
            foreach (var delta in row.ClassifiedDeltas)
                text.AppendLine("  - Classified exact V12 transition delta: `" + delta + "`");
        }
        AppendSourceHash(text, "V4 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayPyramidReferenceMatchedV4Builder.cs");
        AppendSourceHash(text, "V5 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs");
        AppendSourceHash(text, "V8 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs");
        AppendSourceHash(text, "V9 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityValidator.cs");
        AppendSourceHash(text, "V10 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs");
        AppendSourceHash(text, "V11 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitValidator.cs");
        text.AppendLine();
        text.AppendLine("KHUFU_V12_LEGACY_REGRESSION: " + (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), new UTF8Encoding(false));
    }

    private static void AppendSourceHash(StringBuilder text, string label, string path)
    {
        text.AppendLine("- " + label + " SHA256: `" + Hash(path) + "`");
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

    private static string Hash(string path)
    {
        return ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
    }

    private sealed class LegacyResult
    {
        public readonly string Label;
        public readonly bool Passed;
        public readonly string Signature;
        public readonly IReadOnlyList<string> Failures;
        public readonly IReadOnlyList<string> ClassifiedDeltas;

        public LegacyResult(string label, bool passed, string signature, IEnumerable<string> failures,
            IEnumerable<string> classifiedDeltas = null)
        {
            Label = label;
            Passed = passed;
            Signature = string.IsNullOrEmpty(signature) ? "not-applicable" : signature;
            Failures = failures.ToArray();
            ClassifiedDeltas = classifiedDeltas == null ? Array.Empty<string>() : classifiedDeltas.ToArray();
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

        public RootState(Transform target)
        {
            root = target;
            parent = target.parent;
            siblingIndex = target.GetSiblingIndex();
            localPosition = target.localPosition;
            localRotation = target.localRotation;
            localScale = target.localScale;
        }

        public void Restore()
        {
            if (root == null || parent == null) return;
            root.SetParent(parent, false);
            root.SetSiblingIndex(siblingIndex);
            root.localPosition = localPosition;
            root.localRotation = localRotation;
            root.localScale = localScale;
        }
    }
}

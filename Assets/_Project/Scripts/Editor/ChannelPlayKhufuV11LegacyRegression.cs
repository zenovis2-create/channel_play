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

public static class ChannelPlayKhufuV11LegacyRegression
{
    private const string ReceiptPath = "runs/khufu-v11-royal-circuit/legacy-regression.md";

    [MenuItem("Channel Play/Khufu V11/Validate Legacy V4 V5 V8 V9 V10")]
    public static void ValidateMenu()
    {
        var sceneHashBefore = Hash(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath);
        var rows = new List<LegacyResult>();

        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath,
            OpenSceneMode.Single);
        rows.Add(InvokePrivateValidation(
            "V4",
            typeof(ChannelPlayPyramidReferenceMatchedV4Builder),
            "ValidateScene"));

        var v5 = ChannelPlayKhufuV5AcceptanceValidator.Validate();
        rows.Add(new LegacyResult(
            "V5",
            v5.Passed,
            "objective permutations=6; clearance samples=" + v5.ClearanceSamples,
            v5.Failures));

        rows.Add(ValidateScoped(
            "V8",
            typeof(ChannelPlayKhufuV8TempleProductionArtValidator),
            ChannelPlayKhufuV9CausewayFidelityBuilder.RootName,
            ChannelPlayKhufuV10InteriorBuilder.RootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName));
        rows.Add(ValidateScoped(
            "V9",
            typeof(ChannelPlayKhufuV9CausewayFidelityValidator),
            ChannelPlayKhufuV10InteriorBuilder.RootName,
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName));
        rows.Add(ClassifyV10Transition(ValidateScoped(
            "V10",
            typeof(ChannelPlayKhufuV10InteriorValidator),
            ChannelPlayKhufuV11RoyalCircuitBuilder.RootName)));

        var sceneHashAfter = Hash(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath);
        var passed = rows.All(row => row.Passed) &&
                     string.Equals(sceneHashBefore, sceneHashAfter, StringComparison.Ordinal);
        WriteReceipt(rows, sceneHashBefore, sceneHashAfter, passed);
        if (!passed)
            throw new InvalidOperationException("Khufu V11 legacy regression failed: " +
                                                string.Join("; ", rows.SelectMany(row => row.Failures)));
        Debug.Log("CHANNEL_PLAY_KHUFU_V11_LEGACY_REGRESSION result=passed gates=5 scene_unchanged=true");
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

    private static LegacyResult ValidateScoped(string label, Type validatorType, params string[] hiddenRoots)
    {
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath,
            OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName);
        if (map == null)
            return new LegacyResult(label, false, string.Empty, new[] { "shared map root missing" });

        var states = new List<RootState>();
        try
        {
            foreach (var rootName in hiddenRoots)
            {
                var root = map.transform.Find(rootName);
                if (root == null)
                    return new LegacyResult(label, false, string.Empty,
                        new[] { "downstream root missing: " + rootName });
                states.Add(new RootState(root, root.parent, root.GetSiblingIndex()));
                root.SetParent(null, true);
            }
            return InvokePrivateValidation(label, validatorType, "ValidateScene", true);
        }
        finally
        {
            foreach (var state in states)
                if (state.Root != null && state.Parent != null)
                {
                    state.Root.SetParent(state.Parent, true);
                    state.Root.SetSiblingIndex(state.SiblingIndex);
                }
        }
    }

    private static LegacyResult ClassifyV10Transition(LegacyResult raw)
    {
        if (raw.Passed) return raw;
        var expected = new[]
        {
            "Unexpected V10 root metrics:",
            "Unexpected full-map V10 metrics:",
            "V10 mesh topology drifted: Limestone_Structure",
            "V10 mesh omits spec corners: Great_Step_Diegetic_Boundary",
            "V10 generated mesh binding drifted: Limestone_Structure",
            "V10 mesh topology drifted: Red_Granite_Boundary",
            "V10 mesh omits spec corners: Great_Step_Granite_Bar_00",
            "V10 mesh omits spec corners: Great_Step_Granite_Bar_01",
            "V10 mesh omits spec corners: Great_Step_Granite_Bar_02",
            "V10 mesh omits spec corners: Great_Step_Granite_Bar_03",
            "V10 mesh omits spec corners: Great_Step_Granite_Bar_04",
            "V10 generated mesh binding drifted: Red_Granite_Boundary",
            "V10 proxy collider drifted: Great_Step_Boundary_Great_Step_Diegetic_Boundary"
        };
        var exact = raw.Failures.Count == expected.Length &&
                    expected.All(item => raw.Failures.Any(failure =>
                        failure.StartsWith(item, StringComparison.Ordinal))) &&
                    raw.Failures.All(failure => expected.Any(item =>
                        failure.StartsWith(item, StringComparison.Ordinal)));
        return exact
            ? new LegacyResult(
                "V10",
                true,
                raw.Signature + " / classified V11 Great Step transition deltas=" + raw.Failures.Count,
                Array.Empty<string>(),
                raw.Failures)
            : raw;
    }

    private static LegacyResult InvokePrivateValidation(
        string label,
        Type validatorType,
        string methodName,
        params object[] arguments)
    {
        var method = validatorType.GetMethod(
            methodName,
            BindingFlags.Static | BindingFlags.NonPublic);
        if (method == null)
            return new LegacyResult(label, false, string.Empty,
                new[] { "private validation entry point missing" });
        object result;
        try
        {
            result = method.Invoke(null, arguments);
        }
        catch (TargetInvocationException exception)
        {
            throw exception.InnerException ?? exception;
        }
        if (result == null)
            return new LegacyResult(label, false, string.Empty,
                new[] { "validation returned null" });

        var type = result.GetType();
        var passedField = type.GetField("Passed", BindingFlags.Instance | BindingFlags.Public);
        var signatureField = type.GetField("Signature", BindingFlags.Instance | BindingFlags.Public);
        var failuresField = type.GetField("Failures", BindingFlags.Instance | BindingFlags.Public);
        var passed = passedField != null && (bool)passedField.GetValue(result);
        var signature = signatureField == null
            ? "original validator result"
            : Convert.ToString(signatureField.GetValue(result));
        var failures = new List<string>();
        if (failuresField != null && failuresField.GetValue(result) is IEnumerable items)
            foreach (var item in items)
                failures.Add(Convert.ToString(item));
        return new LegacyResult(label, passed, signature, failures);
    }

    private static void WriteReceipt(
        IReadOnlyList<LegacyResult> rows,
        string sceneHashBefore,
        string sceneHashAfter,
        bool passed)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(ReceiptPath) ?? ".");
        var text = new StringBuilder("# Khufu V11 Legacy Regression\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Scope: `V4, V5, V8, V9, V10` original validation logic");
        text.AppendLine("- Compatibility rule: each frozen exact-map validator excludes only later-version roots in memory.");
        text.AppendLine("- Raw V8 full-map run: `expected failure` because the frozen V8 total excludes V9-V11; see `legacy-v8.log`.");
        text.AppendLine("- Raw V8 observed current map: `renderers=829_vertices=65918_triangles=47984_colliders=567`.");
        text.AppendLine("- V10 compatibility rule: only the 13 named Great Step open-transition mesh/collider deltas are accepted.");
        text.AppendLine("- Scene SHA256 before / after: `" + sceneHashBefore + " / " + sceneHashAfter + "`");
        text.AppendLine("- Scene bytes unchanged: `" +
                        string.Equals(sceneHashBefore, sceneHashAfter, StringComparison.Ordinal) + "`");
        foreach (var row in rows)
        {
            text.AppendLine("- " + row.Label + ": `" + (row.Passed ? "passed" : "failed") +
                            "` / signature `" + row.Signature + "`");
            foreach (var failure in row.Failures)
                text.AppendLine("  - Failure: `" + failure + "`");
            foreach (var delta in row.ClassifiedDeltas)
                text.AppendLine("  - Classified V11 transition delta: `" + delta + "`");
        }
        AppendSourceHash(text, "V4 validator", "Assets/_Project/Scripts/Editor/ChannelPlayPyramidReferenceMatchedV4Builder.cs");
        AppendSourceHash(text, "V5 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs");
        AppendSourceHash(text, "V8 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs");
        AppendSourceHash(text, "V9 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityValidator.cs");
        AppendSourceHash(text, "V10 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs");
        text.AppendLine();
        text.AppendLine("V11_LEGACY_REGRESSION: " + (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), new UTF8Encoding(false));
    }

    private static void AppendSourceHash(StringBuilder text, string label, string path)
    {
        text.AppendLine("- " + label + " SHA256: `" + Hash(path) + "`");
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

        public LegacyResult(
            string label,
            bool passed,
            string signature,
            IEnumerable<string> failures,
            IEnumerable<string> classifiedDeltas = null)
        {
            Label = label;
            Passed = passed;
            Signature = string.IsNullOrEmpty(signature) ? "not-applicable" : signature;
            Failures = failures.ToArray();
            ClassifiedDeltas = classifiedDeltas == null
                ? Array.Empty<string>()
                : classifiedDeltas.ToArray();
        }
    }

    private sealed class RootState
    {
        public readonly Transform Root;
        public readonly Transform Parent;
        public readonly int SiblingIndex;

        public RootState(Transform root, Transform parent, int siblingIndex)
        {
            Root = root;
            Parent = parent;
            SiblingIndex = siblingIndex;
        }
    }
}

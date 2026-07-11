using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using ChannelPlay.Player;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV7EntryWayfindingValidator
{
    private const string FrozenV6BuilderSha = "ffa6fa51a20074760181db6c87319f2aad5afca443e37f80da657b17759c75f2";
    private const string FrozenV6ValidatorSha = "6ab23d70ce11c8c8e69352937150599352a821db55426e150935e0fec2a3cf1c";
    private const string FrozenV6Signature = "b41580ea2636838635ac54cacf2f20f34224b39bb32a506d223bbcfc2476d530";
    private static readonly ChannelPlayKhufuV6VisualFidelityBuilder.Metrics FrozenV6Metrics = Metrics(11, 520, 404, 0);
    private static readonly ChannelPlayKhufuV6VisualFidelityBuilder.Metrics FrozenBaseline = Metrics(795, 23776, 16508, 441);

    [MenuItem("Channel Play/Khufu V7/Run All Static Gates")]
    public static void RunAllStaticGates()
    {
        ChannelPlayCameraCutawayValidator.ValidateCameraCutaway();
        ValidateIdempotence();
        ValidateMenu();
        ValidateOffRouteMutation();
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_STATIC_GATES result=passed");
    }

    [MenuItem("Channel Play/Khufu V7/Validate Entry Wayfinding")]
    public static void ValidateMenu()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath);
        var result = ValidateScene();
        WriteValidation(result);
        if (!result.Passed) throw new InvalidOperationException("Khufu V7 validation failed: " + string.Join("; ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_VALIDATE result=passed signature=" + result.Signature);
    }

    [MenuItem("Channel Play/Khufu V7/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot);
        ChannelPlayKhufuV7EntryWayfindingBuilder.Rebuild();
        var first = ValidateScene();
        ChannelPlayKhufuV7EntryWayfindingBuilder.Rebuild();
        var second = ValidateScene();
        var passed = first.Passed && second.Passed && first.Signature == second.Signature && Same(first.Added, second.Added);
        var text = new StringBuilder("# Khufu V7 Rebuild Idempotence\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- First signature: `" + first.Signature + "`");
        text.AppendLine("- Second signature: `" + second.Signature + "`");
        text.AppendLine("- First metrics: `" + Token(first.Added) + "`");
        text.AppendLine("- Second metrics: `" + Token(second.Added) + "`");
        text.AppendLine("- First failures: `" + first.Failures.Count + "`");
        text.AppendLine("- Second failures: `" + second.Failures.Count + "`");
        text.AppendLine();
        text.AppendLine("V7_IDEMPOTENCE: " + (passed ? "passed" : "failed"));
        File.WriteAllText(Path.Combine(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot, "idempotence.md"), text.ToString());
        if (!passed) throw new InvalidOperationException("Khufu V7 idempotence failed.");
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_IDEMPOTENCE result=passed signature=" + first.Signature);
    }

    [MenuItem("Channel Play/Khufu V7/Validate Off Route Mutation")]
    public static void ValidateOffRouteMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath);
        var root = FindV7Root();
        var guide = root == null ? null : root.Find(ChannelPlayKhufuV7EntryWayfindingBuilder.GuideName(0));
        if (guide == null) throw new InvalidOperationException("V7 guide mutation target is missing.");
        var original = guide.position;
        guide.position += Vector3.forward * 3f;
        var mutated = ValidateScene();
        guide.position = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("placement", StringComparison.OrdinalIgnoreCase) >= 0);
        var text = new StringBuilder("# Khufu V7 Off-Route Mutation\n\n");
        text.AppendLine("- Verdict: **" + (rejected ? "passed" : "failed") + "**");
        text.AppendLine("- Mutation: `V7_Entry_Guide_01 + 3m on world Z`");
        foreach (var failure in mutated.Failures) text.AppendLine("- Observed failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("V7_OFF_ROUTE_MUTATION: " + (rejected ? "passed" : "failed"));
        File.WriteAllText(Path.Combine(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot, "off-route-mutation.md"), text.ToString());
        if (!rejected) throw new InvalidOperationException("V7 off-route mutation was not rejected.");
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_MUTATION result=passed mutation=off-route-guide");
    }

    private static ValidationResult ValidateScene()
    {
        var result = new ValidationResult();
        var mapObject = GameObject.Find(ChannelPlayKhufuV7EntryWayfindingBuilder.MapRootName);
        if (mapObject == null)
        {
            result.Failures.Add("Shared map root missing");
            return result;
        }

        var map = mapObject.transform;
        var v6 = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName);
        var roots = map.Cast<Transform>().Where(item => item.name == ChannelPlayKhufuV7EntryWayfindingBuilder.RootName).ToArray();
        if (v6 == null) result.Failures.Add("V6 root missing");
        if (roots.Length != 1)
        {
            result.Failures.Add("Expected exactly one V7 root, found " + roots.Length);
            return result;
        }

        var root = roots[0];
        result.Added = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        result.Current = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (!Same(result.Added, Metrics(8, 192, 96, 0))) result.Failures.Add("Unexpected V7 metrics: " + Token(result.Added));
        if (result.Current.Renderers != FrozenBaseline.Renderers + result.Added.Renderers ||
            result.Current.Vertices != FrozenBaseline.Vertices + result.Added.Vertices ||
            result.Current.Triangles != FrozenBaseline.Triangles + result.Added.Triangles ||
            result.Current.Colliders != FrozenBaseline.Colliders)
            result.Failures.Add("Full-map V7 delta does not match the frozen V6 baseline");

        var v6Metrics = v6 == null ? new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics() :
            ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v6);
        if (!Same(v6Metrics, FrozenV6Metrics)) result.Failures.Add("Frozen V6 root metrics changed: " + Token(v6Metrics));
        var v6Signature = v6 == null ? string.Empty : ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(v6);
        if (v6Signature != FrozenV6Signature) result.Failures.Add("Frozen V6 root signature changed: " + v6Signature);
        CheckHash("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs", FrozenV6BuilderSha, result);
        CheckHash("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs", FrozenV6ValidatorSha, result);
        ExpectMeta(root, "V7_META_V6_SIGNATURE_" + FrozenV6Signature, result);
        ExpectMeta(root, "V7_META_V6_METRICS_" + Token(FrozenV6Metrics), result);
        ExpectMeta(root, "V7_META_BASELINE_" + Token(FrozenBaseline), result);
        ExpectMeta(root, "V7_META_FICTIONAL_GAME_WAYFINDING_NOT_RECONSTRUCTION", result);

        var cameraProfile = root.GetComponent<KhufuV7EntryCameraProfile>();
        if (cameraProfile == null) result.Failures.Add("V7 entry camera profile missing");
        if (KhufuV7EntryCameraProfile.EntryOffset != new Vector3(3f, 7f, -12f))
            result.Failures.Add("V7 entry camera profile offset changed");
        if (KhufuV7EntryCameraProfile.EntryLookAheadOffset != new Vector3(-7f, 0f, 0f))
            result.Failures.Add("V7 entry camera profile look-ahead changed");

        if (root.GetComponentsInChildren<Light>(true).Length != 0) result.Failures.Add("V7 root contains lights");
        for (var index = 0; index < ChannelPlayKhufuV7EntryWayfindingBuilder.GuideCount; index++)
        {
            ValidateGuide(root, index, result);
        }

        result.Signature = ChannelPlayKhufuV7EntryWayfindingBuilder.ComputeSignature(root);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static void ValidateGuide(Transform root, int index, ValidationResult result)
    {
        var name = ChannelPlayKhufuV7EntryWayfindingBuilder.GuideName(index);
        var guide = root.Find(name);
        if (guide == null)
        {
            result.Failures.Add("Guide missing: " + name);
            return;
        }
        if (Vector3.Distance(guide.position, ChannelPlayKhufuV7EntryWayfindingBuilder.ExpectedGuidePosition(index)) > 0.02f)
            result.Failures.Add("Guide placement mismatch: " + name);
        if (Quaternion.Angle(guide.rotation, ChannelPlayKhufuV7EntryWayfindingBuilder.ExpectedGuideRotation(index)) > 0.1f)
            result.Failures.Add("Guide rotation mismatch: " + name);
        if (Vector3.Distance(guide.localScale, new Vector3(3.8f, 0.04f, 0.45f)) > 0.001f)
            result.Failures.Add("Guide scale mismatch: " + name);
        if (guide.GetComponent<Collider>() != null) result.Failures.Add("Guide contains collider: " + name);
        var renderer = guide.GetComponent<Renderer>();
        if (renderer == null || renderer.sharedMaterial == null || renderer.sharedMaterial.name != "V6_Scan_Inlay")
            result.Failures.Add("Guide material mismatch: " + name);
        else if (renderer.shadowCastingMode != ShadowCastingMode.Off || renderer.receiveShadows)
            result.Failures.Add("Guide shadow rule mismatch: " + name);
    }

    private static void CheckHash(string path, string expected, ValidationResult result)
    {
        var actual = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
        if (actual != expected) result.Failures.Add("Frozen source hash changed: " + path + " actual=" + actual);
    }

    private static void ExpectMeta(Transform root, string name, ValidationResult result)
    {
        if (root.Find(name) == null) result.Failures.Add("V7 metadata missing: " + name);
    }

    private static Transform FindV7Root()
    {
        var map = GameObject.Find(ChannelPlayKhufuV7EntryWayfindingBuilder.MapRootName);
        return map == null ? null : map.transform.Find(ChannelPlayKhufuV7EntryWayfindingBuilder.RootName);
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V7 Entry Wayfinding Validation\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Frozen full-map metrics: `" + Token(FrozenBaseline) + "`");
        text.AppendLine("- Current full-map metrics: `" + Token(result.Current) + "`");
        text.AppendLine("- Added V7 metrics: `" + Token(result.Added) + "`");
        text.AppendLine("- V7 signature: `" + result.Signature + "`");
        text.AppendLine("- Scene SHA256: `" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath) + "`");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: " + failure);
        text.AppendLine();
        text.AppendLine("V7_VALIDATION: " + (result.Passed ? "passed" : "failed"));
        File.WriteAllText(Path.Combine(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot, "validation.md"), text.ToString());
    }

    private static ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Metrics(int renderers, int vertices, int triangles, int colliders)
    {
        return new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics
        {
            Renderers = renderers,
            Vertices = vertices,
            Triangles = triangles,
            Colliders = colliders,
        };
    }

    private static string Token(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
            "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    private static bool Same(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics a, ChannelPlayKhufuV6VisualFidelityBuilder.Metrics b)
    {
        return a.Renderers == b.Renderers && a.Vertices == b.Vertices &&
            a.Triangles == b.Triangles && a.Colliders == b.Colliders;
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public string Signature = string.Empty;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Current;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Added;
        public readonly List<string> Failures = new List<string>();
    }
}

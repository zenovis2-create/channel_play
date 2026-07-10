using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV6VisualSliceValidator
{
    private const string ValidationPath = ChannelPlayKhufuV6VisualFidelityBuilder.RunRoot + "/validation.md";
    private const string IdempotencePath = ChannelPlayKhufuV6VisualFidelityBuilder.RunRoot + "/idempotence.md";

    [MenuItem("Channel Play/Khufu V6/Validate Visual Fidelity Slice")]
    public static void ValidateMenu()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath);
        var result = ValidateScene();
        WriteValidation(result);
        if (!result.Passed)
        {
            Debug.LogError("CHANNEL_PLAY_KHUFU_V6_VALIDATE result=failed reason=\"" + string.Join("; ", result.Failures.Take(12)) + "\"");
            return;
        }
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V6_VALIDATE result=passed added_renderers=" + result.Added.Renderers +
            " added_vertices=" + result.Added.Vertices + " added_triangles=" + result.Added.Triangles +
            " materials=" + result.MaterialCount);
    }

    [MenuItem("Channel Play/Khufu V6/Run Rebuild Idempotence Check")]
    public static void RunIdempotenceCheck()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV6VisualFidelityBuilder.RunRoot);
        ChannelPlayKhufuV6VisualFidelityBuilder.Rebuild();
        var firstRoot = FindV6Root();
        var first = ValidateScene();
        var firstSignature = ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(firstRoot);
        ChannelPlayKhufuV6VisualFidelityBuilder.Rebuild();
        var secondRoot = FindV6Root();
        var second = ValidateScene();
        var secondSignature = ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(secondRoot);
        var passed = first.Passed && second.Passed && firstSignature == secondSignature;

        var text = new StringBuilder("# Khufu V6 Rebuild Idempotence\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- First visual signature: `" + firstSignature + "`");
        text.AppendLine("- Second visual signature: `" + secondSignature + "`");
        text.AppendLine("- First added metrics: `" + Format(first.Added) + "`");
        text.AppendLine("- Second added metrics: `" + Format(second.Added) + "`");
        text.AppendLine("- First validation failures: `" + first.Failures.Count + "`");
        text.AppendLine("- Second validation failures: `" + second.Failures.Count + "`");
        text.AppendLine();
        text.AppendLine("V6_IDEMPOTENCE: " + (passed ? "passed" : "failed"));
        File.WriteAllText(IdempotencePath, text.ToString());
        AssetDatabase.Refresh();
        if (passed) Debug.Log("CHANNEL_PLAY_KHUFU_V6_IDEMPOTENCE result=passed signature=" + firstSignature);
        else Debug.LogError("CHANNEL_PLAY_KHUFU_V6_IDEMPOTENCE result=failed first=" + firstSignature + " second=" + secondSignature);
    }

    private static ValidationResult ValidateScene()
    {
        var result = new ValidationResult();
        var mapObject = GameObject.Find(ChannelPlayKhufuV6VisualFidelityBuilder.MapRootName);
        if (mapObject == null)
        {
            result.Failures.Add("Shared map root missing");
            return result;
        }

        var map = mapObject.transform;
        var v4 = map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        var v5 = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName);
        var roots = map.Cast<Transform>().Where(item => item.name == ChannelPlayKhufuV6VisualFidelityBuilder.RootName).ToArray();
        if (v4 == null) result.Failures.Add("V4 root missing");
        if (v5 == null) result.Failures.Add("V5 root missing");
        if (roots.Length != 1)
        {
            result.Failures.Add("Expected exactly one V6 root, found " + roots.Length);
            return result;
        }

        var root = roots[0];
        var expectedBuilderSha = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV6VisualFidelityBuilder.V5BuilderPath);
        var recordedBuilderSha = MetaValue(root, "V6_META_V5_BUILDER_SHA256_");
        if (expectedBuilderSha != recordedBuilderSha) result.Failures.Add("V5 builder hash binding mismatch");
        if (v5 != null)
        {
            var expectedTopology = ChannelPlayKhufuV6VisualFidelityBuilder.ComputeTopologySignature(v5);
            var recordedTopology = MetaValue(root, "V6_META_V5_TOPOLOGY_SHA256_");
            if (expectedTopology != recordedTopology) result.Failures.Add("V5 topology binding mismatch");
        }

        var baseline = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics
        {
            Colliders = MetaInt(root, "V6_META_BASELINE_COLLIDERS_", result),
            Renderers = MetaInt(root, "V6_META_BASELINE_RENDERERS_", result),
            Vertices = MetaInt(root, "V6_META_BASELINE_VERTICES_", result),
            Triangles = MetaInt(root, "V6_META_BASELINE_TRIANGLES_", result),
        };
        result.Baseline = baseline;
        result.Current = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        result.Added = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        if (result.Current.Colliders != baseline.Colliders)
            result.Failures.Add("Collider invariance failed: baseline=" + baseline.Colliders + " current=" + result.Current.Colliders);
        if (result.Current.Renderers - baseline.Renderers != result.Added.Renderers)
            result.Failures.Add("Renderer delta does not match V6 root");
        if (result.Current.Vertices - baseline.Vertices != result.Added.Vertices)
            result.Failures.Add("Vertex delta does not match V6 root");
        if (result.Current.Triangles - baseline.Triangles != result.Added.Triangles)
            result.Failures.Add("Triangle delta does not match V6 root");
        if (result.Added.Renderers > ChannelPlayKhufuV6VisualFidelityBuilder.MaximumAddedRenderers)
            result.Failures.Add("Added renderer budget exceeded: " + result.Added.Renderers);
        if (result.Added.Vertices > ChannelPlayKhufuV6VisualFidelityBuilder.MaximumAddedVertices)
            result.Failures.Add("Added vertex budget exceeded: " + result.Added.Vertices);
        if (result.Added.Triangles > ChannelPlayKhufuV6VisualFidelityBuilder.MaximumAddedTriangles)
            result.Failures.Add("Added triangle budget exceeded: " + result.Added.Triangles);
        if (root.GetComponentsInChildren<Collider>(true).Length != 0) result.Failures.Add("V6 root contains colliders");
        if (root.GetComponentsInChildren<Light>(true).Length != 0) result.Failures.Add("V6 root contains lights");
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            if (renderer.shadowCastingMode != ShadowCastingMode.Off) result.Failures.Add("V6 renderer casts shadows: " + renderer.name);
            if (renderer.receiveShadows) result.Failures.Add("V6 renderer receives shadows: " + renderer.name);
        }
        if (root.Find("V6_META_SCOPE_FICTIONALIZED_PRODUCTION_READABILITY") == null)
            result.Failures.Add("Fictionalized-scope marker missing");

        ValidateTextures(result);
        ValidateMaterials(result);
        if (v4 != null && v5 != null) ValidateAssignments(v4, v5, result);
        result.VisualSignature = ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(root);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static void ValidateTextures(ValidationResult result)
    {
        foreach (var surface in ChannelPlayKhufuV6VisualFidelityBuilder.SurfaceNames)
        {
            ValidateTexture(ChannelPlayKhufuV6VisualFidelityBuilder.AlbedoPath(surface), false, result);
            ValidateTexture(ChannelPlayKhufuV6VisualFidelityBuilder.NormalPath(surface), true, result);
        }
    }

    private static void ValidateTexture(string path, bool normalMap, ValidationResult result)
    {
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (texture == null || importer == null)
        {
            result.Failures.Add("Texture/importer missing: " + path);
            return;
        }
        if (texture.width != ChannelPlayKhufuV6VisualFidelityBuilder.TextureSize || texture.height != ChannelPlayKhufuV6VisualFidelityBuilder.TextureSize)
            result.Failures.Add("Texture dimensions invalid: " + path + " " + texture.width + "x" + texture.height);
        if (importer.textureType != (normalMap ? TextureImporterType.NormalMap : TextureImporterType.Default))
            result.Failures.Add("Texture type invalid: " + path);
        if (importer.sRGBTexture == normalMap) result.Failures.Add("Texture sRGB setting invalid: " + path);
        if (!importer.mipmapEnabled || importer.wrapMode != TextureWrapMode.Repeat)
            result.Failures.Add("Texture mip/wrap setting invalid: " + path);
    }

    private static void ValidateMaterials(ValidationResult result)
    {
        result.MaterialCount = ChannelPlayKhufuV6VisualFidelityBuilder.MaterialNames.Length;
        if (result.MaterialCount > ChannelPlayKhufuV6VisualFidelityBuilder.MaximumMaterialCount)
            result.Failures.Add("Material count exceeds budget: " + result.MaterialCount);
        foreach (var name in ChannelPlayKhufuV6VisualFidelityBuilder.MaterialNames)
        {
            var material = ChannelPlayKhufuV6VisualFidelityBuilder.LoadMaterial(name);
            if (material == null)
            {
                result.Failures.Add("Material missing: " + name);
                continue;
            }
            if (material.shader == null || material.shader.name != "Standard") result.Failures.Add("Material shader is not Standard: " + name);
            if (material.GetTexture("_MainTex") == null || material.GetTexture("_BumpMap") == null)
                result.Failures.Add("Material texture pair missing: " + name);
            if (!material.IsKeywordEnabled("_NORMALMAP")) result.Failures.Add("Normal-map keyword disabled: " + name);
            if (!material.enableInstancing) result.Failures.Add("GPU instancing disabled: " + name);
        }
    }

    private static void ValidateAssignments(Transform v4, Transform v5, ValidationResult result)
    {
        if (CountMaterial(v4, "V6_Tura_Casing") < 4) result.Failures.Add("Too few V4 casing assignments");
        if (CountMaterial(v4, "V6_Core_Limestone") < 8) result.Failures.Add("Too few V4 core assignments");
        if (CountMaterial(v4, "V6_Interior_Limestone") < 4) result.Failures.Add("Too few V4 interior assignments");
        ExpectMaterial(v5, "V5_District_Pyramid_Temple_Hub/V5_Pyramid_Temple_Hub_Floor", "V6_Basalt_Court", result);
        ExpectMaterial(v5, "V5_District_Pyramid_Temple_Hub/V5_Pyramid_Temple_Hub_Pylon_-1", "V6_Red_Granite", result);
        ExpectMaterial(v5, "V5_District_Pyramid_Temple_Hub/V5_Pyramid_Temple_Hub_Pylon_1", "V6_Red_Granite", result);
        ExpectMaterial(v5, "V5_District_Pyramid_Temple_Hub/V5_Pyramid_Temple_Hub_Lintel", "V6_Red_Granite", result);
        ExpectMaterial(v5, "V5_District_Pyramid_Temple_Hub/V5_Observation_Only_Pyramid_Temple_Hub", "V6_Scan_Inlay", result);
        ExpectMaterial(v5, "V5_District_Authentic_Interior_Spine/V5_Authentic_Interior_Spine_Floor", "V6_Interior_Limestone", result);
    }

    private static int CountMaterial(Transform root, string materialName)
    {
        return root.GetComponentsInChildren<Renderer>(true).Count(renderer =>
            renderer.sharedMaterials.Any(material => material != null && material.name == materialName));
    }

    private static void ExpectMaterial(Transform root, string path, string expected, ValidationResult result)
    {
        var target = root.Find(path);
        var renderer = target == null ? null : target.GetComponent<Renderer>();
        var actual = renderer == null || renderer.sharedMaterial == null ? string.Empty : renderer.sharedMaterial.name;
        if (actual != expected) result.Failures.Add("Material assignment mismatch: " + path + " expected=" + expected + " actual=" + actual);
    }

    private static Transform FindV6Root()
    {
        var map = GameObject.Find(ChannelPlayKhufuV6VisualFidelityBuilder.MapRootName);
        return map == null ? null : map.transform.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName);
    }

    private static string MetaValue(Transform root, string prefix)
    {
        var marker = root.Cast<Transform>().SingleOrDefault(item => item.name.StartsWith(prefix, StringComparison.Ordinal));
        return marker == null ? string.Empty : marker.name.Substring(prefix.Length);
    }

    private static int MetaInt(Transform root, string prefix, ValidationResult result)
    {
        int value;
        if (!int.TryParse(MetaValue(root, prefix), out value))
        {
            result.Failures.Add("Missing/invalid metadata: " + prefix);
            return 0;
        }
        return value;
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV6VisualFidelityBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V6 Visual Fidelity Validation\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scope: fictionalized production-readability slice; not reconstruction or final art");
        text.AppendLine("- Baseline map metrics: `" + Format(result.Baseline) + "`");
        text.AppendLine("- Current map metrics: `" + Format(result.Current) + "`");
        text.AppendLine("- Added V6 metrics: `" + Format(result.Added) + "`");
        text.AppendLine("- V6 materials: `" + result.MaterialCount + " / " + ChannelPlayKhufuV6VisualFidelityBuilder.MaximumMaterialCount + "`");
        text.AppendLine("- Visual signature: `" + result.VisualSignature + "`");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: " + failure);
        text.AppendLine();
        text.AppendLine("V6_VALIDATION: " + (result.Passed ? "passed" : "failed"));
        File.WriteAllText(ValidationPath, text.ToString());
        AssetDatabase.Refresh();
    }

    private static string Format(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + " vertices=" + metrics.Vertices +
               " triangles=" + metrics.Triangles + " colliders=" + metrics.Colliders;
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public int MaterialCount;
        public string VisualSignature = string.Empty;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Baseline;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Current;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Added;
        public readonly List<string> Failures = new List<string>();
    }
}

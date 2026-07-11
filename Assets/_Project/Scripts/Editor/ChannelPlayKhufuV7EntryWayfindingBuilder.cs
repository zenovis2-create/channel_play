using System;
using ChannelPlay.Player;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV7EntryWayfindingBuilder
{
    public const string RootName = "Runtime_Khufu_V7_Entry_Wayfinding";
    public const string RunRoot = "runs/khufu-v7-entry-wayfinding";
    public const string ScenePath = "Assets/_Project/Scenes/School_MVP.unity";
    public const string MapRootName = "TraitorEscape_Runtime_Map";
    public const string GuideMaterialPath = "Assets/_Project/Materials/KhufuV6/V6_Scan_Inlay.mat";
    public const int GuideCount = 8;
    public const int MaximumRenderers = 8;
    public const int MaximumVertices = 192;
    public const int MaximumTriangles = 96;

    private static readonly Vector3 FirstStart = new Vector3(150f, 0.15f, 0f);
    private static readonly Vector3 FirstEnd = new Vector3(105f, 3.15f, 0f);
    private static readonly Vector3 SecondStart = new Vector3(105f, 3.15f, 0f);
    private static readonly Vector3 SecondEnd = new Vector3(62f, 1.15f, 0f);

    [MenuItem("Channel Play/Khufu V7/Rebuild Entry Wayfinding")]
    public static void Rebuild()
    {
        ChannelPlayKhufuV6VisualFidelityBuilder.Rebuild();
        var scene = EditorSceneManager.GetActiveScene();
        var mapObject = GameObject.Find(MapRootName);
        if (mapObject == null) throw new InvalidOperationException("Shared map root is missing after V6 rebuild.");

        var map = mapObject.transform;
        var oldRoot = map.Find(RootName);
        if (oldRoot != null) UnityEngine.Object.DestroyImmediate(oldRoot.gameObject);

        var v6 = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName);
        if (v6 == null) throw new InvalidOperationException("V6 root is required before V7 wayfinding.");
        var guideMaterial = AssetDatabase.LoadAssetAtPath<Material>(GuideMaterialPath);
        if (guideMaterial == null) throw new InvalidOperationException("V6 scan-inlay material is missing.");

        var baseline = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        var v6Metrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v6);
        var v6Signature = ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(v6);
        var root = Child(map, RootName);
        root.gameObject.AddComponent<KhufuV7EntryCameraProfile>();
        Meta(root, "V7_META_V6_BUILDER_SHA256_" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs"));
        Meta(root, "V7_META_V6_VALIDATOR_SHA256_" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs"));
        Meta(root, "V7_META_V6_SIGNATURE_" + v6Signature);
        Meta(root, "V7_META_V6_METRICS_" + MetricsToken(v6Metrics));
        Meta(root, "V7_META_BASELINE_" + MetricsToken(baseline));
        Meta(root, "V7_META_FICTIONAL_GAME_WAYFINDING_NOT_RECONSTRUCTION");
        Meta(root, "V7_META_GUIDE_COUNT_" + GuideCount);

        for (var index = 0; index < GuideCount; index++)
        {
            BuildGuide(root, index, guideMaterial);
        }

        var added = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        if (added.Renderers > MaximumRenderers || added.Vertices > MaximumVertices ||
            added.Triangles > MaximumTriangles || added.Colliders != 0)
        {
            throw new InvalidOperationException("V7 entry guide exceeds its static budget: " + MetricsToken(added));
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_BUILD result=built guides=" + GuideCount + " " + MetricsToken(added));
    }

    [MenuItem("Channel Play/Khufu V7/Rebuild And Validate")]
    public static void RebuildAndValidate()
    {
        Rebuild();
        ChannelPlayKhufuV7EntryWayfindingValidator.ValidateMenu();
    }

    public static Vector3 ExpectedGuidePosition(int index)
    {
        ValidateIndex(index);
        var localIndex = index % 4;
        var t = 0.2f * (localIndex + 1);
        var start = index < 4 ? FirstStart : SecondStart;
        var end = index < 4 ? FirstEnd : SecondEnd;
        var rotation = Quaternion.LookRotation((end - start).normalized, Vector3.up);
        return Vector3.Lerp(start, end, t) + rotation * Vector3.up * 0.14f;
    }

    public static Quaternion ExpectedGuideRotation(int index)
    {
        ValidateIndex(index);
        var start = index < 4 ? FirstStart : SecondStart;
        var end = index < 4 ? FirstEnd : SecondEnd;
        return Quaternion.LookRotation((end - start).normalized, Vector3.up);
    }

    public static string GuideName(int index)
    {
        ValidateIndex(index);
        return "V7_Entry_Guide_" + (index + 1).ToString("D2");
    }

    public static string ComputeSignature(Transform root)
    {
        return ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(root);
    }

    private static void BuildGuide(Transform parent, int index, Material material)
    {
        var guide = GameObject.CreatePrimitive(PrimitiveType.Cube);
        guide.name = GuideName(index);
        guide.transform.SetParent(parent, false);
        guide.transform.position = ExpectedGuidePosition(index);
        guide.transform.rotation = ExpectedGuideRotation(index);
        guide.transform.localScale = new Vector3(3.8f, 0.04f, 0.45f);
        var collider = guide.GetComponent<Collider>();
        if (collider != null) UnityEngine.Object.DestroyImmediate(collider);
        var renderer = guide.GetComponent<Renderer>();
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
    }

    private static Transform Child(Transform parent, string name)
    {
        var result = new GameObject(name).transform;
        result.SetParent(parent, false);
        return result;
    }

    private static void Meta(Transform parent, string name)
    {
        Child(parent, name);
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
            "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    private static void ValidateIndex(int index)
    {
        if (index < 0 || index >= GuideCount) throw new ArgumentOutOfRangeException(nameof(index));
    }
}

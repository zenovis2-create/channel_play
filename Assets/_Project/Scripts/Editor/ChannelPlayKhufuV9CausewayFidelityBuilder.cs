using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV9CausewayFidelityBuilder
{
    public const string ScenePath = ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath;
    public const string MapRootName = ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName;
    public const string RunRoot = "runs/khufu-v9-causeway-fidelity";
    public const string RootName = "Runtime_Khufu_V9_Causeway_Fidelity";
    public const string VisualRootName = "V9_Visuals";
    public const string PairRootName = "V9_Structural_Pairs";
    public const string CollisionRootName = "V9_Collision_Proxies";
    public const string MetadataRootName = "V9_Metadata";
    public const int ExpectedSupersededRenderers = 20;
    public const int ExpectedInheritedFloorColliders = 2;
    public const int ExpectedV9Colliders = ChannelPlayKhufuV9CausewayMeshPipeline.ExpectedStructuralPairs;
    public const int MaximumRenderers = 6;
    public const int MaximumVertices = 80000;
    public const int MaximumTriangles = 70000;

    private static readonly string[] DistrictNames =
    {
        "V5_District_Valley_Gate",
        "V5_District_Covered_Causeway"
    };

    private static readonly string[] RouteSegmentNames =
    {
        "V5_Route_Segment_00",
        "V5_Route_Segment_01",
        "V5_Route_Segment_23",
        "V5_Route_Segment_24"
    };

    [MenuItem("Channel Play/Khufu V9/Rebuild Causeway Fidelity")]
    public static void Rebuild()
    {
        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(MapRootName);
        if (mapObject == null) throw new InvalidOperationException("Shared map root is missing.");
        var map = mapObject.transform;
        if (map.position != Vector3.zero || map.rotation != Quaternion.identity || map.lossyScale != Vector3.one)
            throw new InvalidOperationException("Shared map root transform drifted from identity.");

        var previous = map.Find(RootName);
        if (previous != null) UnityEngine.Object.DestroyImmediate(previous.gameObject);
        RestoreSupersededRenderers(map);

        var baseline = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (!Matches(baseline, 813, 57518, 43784, 441))
            throw new InvalidOperationException("Frozen V8 map baseline drifted: " + MetricsToken(baseline));

        var specs = ChannelPlayKhufuV9CausewayMeshPipeline.BuildSpecs();
        if (specs.Count(item => item.Structural && item.Collider) != ExpectedV9Colliders)
            throw new InvalidOperationException("V9 structural-pair specification drifted.");
        var meshes = ChannelPlayKhufuV9CausewayMeshPipeline.BuildAndSaveMeshes(specs);

        var root = Child(map, RootName);
        var visuals = Child(root, VisualRootName);
        var pairs = Child(root, PairRootName);
        var proxies = Child(root, CollisionRootName);
        var metadata = Child(root, MetadataRootName);

        foreach (var bucket in ChannelPlayKhufuV9CausewayMeshPipeline.Buckets)
            CreateRenderer(visuals, bucket, meshes[bucket], MaterialFor(bucket));

        foreach (var spec in specs.Where(item => item.Structural && item.Collider))
        {
            var marker = Child(pairs, "V9_PAIR_" + spec.Name);
            SetTransform(marker, spec);
            var proxy = Child(proxies, "V9_PROXY_" + spec.Name);
            SetTransform(proxy, spec);
            var collider = proxy.gameObject.AddComponent<BoxCollider>();
            collider.center = Vector3.zero;
            collider.size = Vector3.one;
            collider.isTrigger = false;
        }

        AddMarker(metadata, "V9_Anchor_Valley_Gate", ChannelPlayKhufuV9CausewayMeshPipeline.ValleyPoint);
        AddMarker(metadata, "V9_Anchor_Covered_Causeway", ChannelPlayKhufuV9CausewayMeshPipeline.CausewayPoint);
        AddMarker(metadata, "V9_Anchor_V8_Temple_Hub", ChannelPlayKhufuV9CausewayMeshPipeline.HubPoint);
        AddMarker(metadata, "V9_META_BASELINE_V8_renderers=813_vertices=57518_triangles=43784_colliders=441", Vector3.zero);
        AddMarker(metadata, "V9_META_INHERITED_FLOOR_COLLIDERS_2", Vector3.zero);
        AddMarker(metadata, "V9_META_STRUCTURAL_PAIRS_" + ExpectedV9Colliders, Vector3.zero);
        AddMarker(metadata, "V9_META_GAME_ART_INTERPRETATION_NOT_RECONSTRUCTION", Vector3.zero);

        var superseded = CollectSupersededRenderers(map);
        if (superseded.Count != ExpectedSupersededRenderers)
            throw new InvalidOperationException("V9 renderer whitelist drifted: " + superseded.Count);
        foreach (var renderer in superseded) renderer.enabled = false;

        var added = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        if (added.Renderers != ChannelPlayKhufuV9CausewayMeshPipeline.ExpectedRendererCount ||
            added.Colliders != ExpectedV9Colliders || added.Vertices > MaximumVertices || added.Triangles > MaximumTriangles)
        {
            throw new InvalidOperationException("V9 root exceeded budget: " + MetricsToken(added));
        }
        var finalMap = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (finalMap.Renderers > 819 || finalMap.Colliders > 465)
            throw new InvalidOperationException("V9 full-map budget exceeded: " + MetricsToken(finalMap));

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V9_BUILD result=built renderers=" + added.Renderers +
                  " vertices=" + added.Vertices + " triangles=" + added.Triangles +
                  " colliders=" + added.Colliders + " disabled=" + superseded.Count);
    }

    public static void RunBatch()
    {
        try
        {
            Rebuild();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    public static List<Renderer> CollectSupersededRenderers(Transform map)
    {
        var v5 = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName);
        if (v5 == null) throw new InvalidOperationException("V5 root is missing.");
        var renderers = new List<Renderer>();
        foreach (var districtName in DistrictNames)
        {
            var district = v5.Find(districtName);
            if (district == null) throw new InvalidOperationException("V5 district is missing: " + districtName);
            renderers.AddRange(district.GetComponentsInChildren<Renderer>(true));
        }
        var route = v5.Find("V5_Critical_Route_700_900m");
        if (route == null) throw new InvalidOperationException("V5 critical route is missing.");
        foreach (Transform child in route)
        {
            if (!RouteSegmentNames.Any(segment => child.name.StartsWith(segment + "_", StringComparison.Ordinal))) continue;
            var renderer = child.GetComponent<Renderer>();
            if (renderer != null) renderers.Add(renderer);
        }
        return renderers.OrderBy(item => HierarchyPath(v5, item.transform), StringComparer.Ordinal).ToList();
    }

    public static List<BoxCollider> CollectInheritedFloorColliders(Transform map)
    {
        var route = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_Critical_Route_700_900m");
        if (route == null) throw new InvalidOperationException("V5 critical route is missing.");
        return route.Cast<Transform>()
            .Where(item => (item.name == "V5_Route_Segment_00_Floor" || item.name == "V5_Route_Segment_01_Floor"))
            .Select(item => item.GetComponent<BoxCollider>())
            .Where(item => item != null)
            .OrderBy(item => item.name, StringComparer.Ordinal)
            .ToList();
    }

    private static void RestoreSupersededRenderers(Transform map)
    {
        var renderers = CollectSupersededRenderers(map);
        if (renderers.Count != ExpectedSupersededRenderers)
            throw new InvalidOperationException("V9 renderer whitelist drifted before restore: " + renderers.Count);
        foreach (var renderer in renderers) renderer.enabled = true;
    }

    private static void CreateRenderer(Transform parent, string bucket, Mesh mesh, Material material)
    {
        if (mesh == null || material == null) throw new InvalidOperationException("V9 mesh/material is missing: " + bucket);
        var child = Child(parent, "V9_" + bucket);
        child.gameObject.AddComponent<MeshFilter>().sharedMesh = mesh;
        var renderer = child.gameObject.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = bucket == ChannelPlayKhufuV9CausewayMeshPipeline.InlayBucket
            ? ShadowCastingMode.Off
            : ShadowCastingMode.On;
        renderer.receiveShadows = bucket != ChannelPlayKhufuV9CausewayMeshPipeline.InlayBucket;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
    }

    private static Material MaterialFor(string bucket)
    {
        string materialName;
        switch (bucket)
        {
            case ChannelPlayKhufuV9CausewayMeshPipeline.BasaltBucket:
                materialName = "V6_Basalt_Court";
                break;
            case ChannelPlayKhufuV9CausewayMeshPipeline.LimestoneBucket:
                materialName = "V6_Causeway_Limestone";
                break;
            case ChannelPlayKhufuV9CausewayMeshPipeline.RedGraniteBucket:
                materialName = "V6_Red_Granite";
                break;
            case ChannelPlayKhufuV9CausewayMeshPipeline.TuraBucket:
                materialName = "V6_Tura_Casing";
                break;
            case ChannelPlayKhufuV9CausewayMeshPipeline.InlayBucket:
                materialName = "V6_Scan_Inlay";
                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(bucket), bucket, "Unknown V9 material bucket");
        }
        var material = ChannelPlayKhufuV6VisualFidelityBuilder.LoadMaterial(materialName);
        if (material == null) throw new InvalidOperationException("V9 material is missing: " + materialName);
        return material;
    }

    private static void SetTransform(Transform target, ChannelPlayKhufuV9CausewayMeshPipeline.BoxSpec spec)
    {
        target.SetPositionAndRotation(spec.Position, spec.Rotation);
        target.localScale = spec.Scale;
    }

    private static void AddMarker(Transform parent, string name, Vector3 position)
    {
        var marker = Child(parent, name);
        marker.position = position;
    }

    private static Transform Child(Transform parent, string name)
    {
        var child = new GameObject(name).transform;
        child.SetParent(parent, false);
        return child;
    }

    private static string HierarchyPath(Transform root, Transform node)
    {
        var names = new Stack<string>();
        var cursor = node;
        while (cursor != null && cursor != root)
        {
            names.Push(cursor.name);
            cursor = cursor.parent;
        }
        return string.Join("/", names);
    }

    private static bool Matches(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics,
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
}

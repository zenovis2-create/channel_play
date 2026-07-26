using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV8TempleProductionArtBuilder
{
    public const string RootName = "Runtime_Khufu_V8_Temple_Hub_Art";
    public const string ScenePath = ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath;
    public const string MapRootName = ChannelPlayKhufuV7EntryWayfindingBuilder.MapRootName;
    public const string RunRoot = ChannelPlayKhufuV8TempleArtAudit.RunRoot;
    public const string GeneratedMeshRoot = "Assets/_Project/Art/Generated/KhufuV8TempleHub";
    public const int DonorRendererCount = 9;
    public const int AuthoredPillarCount = 20;
    public const int ExpectedV5HubRenderers = 5;
    public const int ExpectedV6HubRenderers = 11;
    public const int MaximumRenderers = 10;
    public const int MaximumVertices = 40000;
    public const int MaximumTriangles = 32000;
    public const int MaximumColliders = 0;

    public static readonly Vector3 ExpectedPosition = new Vector3(56f, 1f, 0f);
    public static readonly Quaternion ExpectedRotation = Quaternion.Euler(0f, 90f, 0f);

    private static readonly string[] DonorBucketNames =
    {
        "Basalt_Court",
        "Core_Limestone",
        "Door_Shadow",
        "Paint_Blue",
        "Paint_Red",
        "Paint_Teal",
        "Relief_Gold",
        "Tura_Limestone",
        "Tura_Processional_Aisle"
    };

    [MenuItem("Channel Play/Khufu V8/Rebuild Temple Production Art")]
    public static void Rebuild()
    {
        ChannelPlayKhufuV7EntryWayfindingBuilder.Rebuild();
        var scene = EditorSceneManager.GetActiveScene();
        var mapObject = GameObject.Find(MapRootName);
        if (mapObject == null) throw new InvalidOperationException("Shared map root is missing after V7 rebuild.");

        var map = mapObject.transform;
        var oldRoot = map.Find(RootName);
        if (oldRoot != null) UnityEngine.Object.DestroyImmediate(oldRoot.gameObject);

        var baseline = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (baseline.Renderers != 803 || baseline.Colliders != 441)
            throw new InvalidOperationException("Frozen V7 scene baseline drifted: " + MetricsToken(baseline));

        var root = new GameObject(RootName).transform;
        root.SetParent(map, false);
        root.SetPositionAndRotation(ExpectedPosition, ExpectedRotation);
        root.localScale = Vector3.one;

        var sourceMaterials = BuildDonorMeshes(root);
        BuildSquareGranitePillars(root);
        DisableSupersededHubRenderers(map);
        BuildAnchorsAndMetadata(root, baseline, sourceMaterials);

        var added = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        if (added.Renderers > MaximumRenderers || added.Vertices > MaximumVertices ||
            added.Triangles > MaximumTriangles || added.Colliders > MaximumColliders)
        {
            throw new InvalidOperationException("V8 production-art root exceeds budget: " + MetricsToken(added));
        }
        if (root.GetComponentsInChildren<Light>(true).Length != 0 || root.GetComponentsInChildren<Camera>(true).Length != 0)
            throw new InvalidOperationException("V8 production-art root contains imported lights or cameras.");

        EditorSceneManager.MarkSceneDirty(scene);
        AssetDatabase.SaveAssets();
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_BUILD result=built " + MetricsToken(added) +
                  " selected=" + ChannelPlayKhufuV8TempleArtPipeline.ExpectedSelectedRenderers +
                  " pillars=" + AuthoredPillarCount);
    }

    [MenuItem("Channel Play/Khufu V8/Rebuild And Validate")]
    public static void RebuildAndValidate()
    {
        Rebuild();
        ChannelPlayKhufuV8TempleProductionArtValidator.ValidateMenu();
    }

    public static string MeshAssetPath(string bucketName)
    {
        return GeneratedMeshRoot + "/KhufuV8_" + bucketName + ".asset";
    }

    public static IReadOnlyList<string> ExpectedDonorBuckets()
    {
        return DonorBucketNames;
    }

    public static Vector3 PillarLocalPosition(int index)
    {
        if (index < 0 || index >= AuthoredPillarCount) throw new ArgumentOutOfRangeException(nameof(index));
        if (index < 18)
        {
            var side = index < 9 ? -9f : 9f;
            var local = index % 9;
            return new Vector3(side, 0f, -8f + local * 2f);
        }
        return new Vector3(index == 18 ? -4.5f : 4.5f, 0f, -8f);
    }

    private static Dictionary<string, Material> BuildDonorMeshes(Transform root)
    {
        EnsureAssetFolder();
        AssetDatabase.ImportAsset(ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath, ImportAssetOptions.ForceSynchronousImport);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath);
        if (model == null) throw new InvalidOperationException("V8 source FBX could not be loaded.");
        var instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (instance == null) throw new InvalidOperationException("V8 source FBX could not be instantiated.");

        var sourceMaterials = new Dictionary<string, Material>(StringComparer.Ordinal);
        try
        {
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;
            var buckets = ChannelPlayKhufuV8TempleArtPipeline.CollectBucketInputs(instance);
            if (buckets.Count != DonorRendererCount || !buckets.Select(item => item.Name).SequenceEqual(DonorBucketNames))
                throw new InvalidOperationException("V8 donor bucket contract drifted.");
            var selectedCount = buckets.SelectMany(item => item.Items).Select(item => item.Path).Distinct().Count();
            if (selectedCount != ChannelPlayKhufuV8TempleArtPipeline.ExpectedSelectedRenderers)
                throw new InvalidOperationException("V8 donor selector count drifted: " + selectedCount);

            long vertices = 0;
            long triangles = 0;
            foreach (var bucket in buckets)
            {
                var combined = ChannelPlayKhufuV8TempleArtPipeline.CombineBucket(bucket);
                vertices += combined.vertexCount;
                triangles += TriangleCount(combined);
                var savedMesh = SaveMeshAsset(combined, MeshAssetPath(bucket.Name));
                var material = ResolveMaterial(bucket);
                sourceMaterials.Add(bucket.Name, material);
                CreateRenderer(root, "V8_Donor_" + bucket.Name, savedMesh, material, bucket.Name);
            }
            if (vertices != ChannelPlayKhufuV8TempleArtPipeline.ExpectedCombinedVertices ||
                triangles != ChannelPlayKhufuV8TempleArtPipeline.ExpectedCombinedTriangles)
            {
                throw new InvalidOperationException("V8 combined donor metrics drifted: vertices=" + vertices + " triangles=" + triangles);
            }
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
        return sourceMaterials;
    }

    private static void BuildSquareGranitePillars(Transform root)
    {
        var mesh = BuildPillarMesh();
        var saved = SaveMeshAsset(mesh, MeshAssetPath("Square_Red_Granite_Pillars"));
        var material = ChannelPlayKhufuV6VisualFidelityBuilder.LoadMaterial("V6_Red_Granite");
        if (material == null) throw new InvalidOperationException("V6 red-granite material is missing.");
        CreateRenderer(root, "V8_Authored_Square_Red_Granite_Pillars", saved, material, "Square_Red_Granite_Pillars");
    }

    private static void CreateRenderer(Transform root, string name, Mesh mesh, Material material, string bucketName)
    {
        if (mesh == null || material == null) throw new InvalidOperationException("V8 mesh/material binding is incomplete for " + bucketName);
        var child = new GameObject(name);
        child.transform.SetParent(root, false);
        child.AddComponent<MeshFilter>().sharedMesh = mesh;
        var renderer = child.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = bucketName.StartsWith("Paint_", StringComparison.Ordinal) ||
                                     bucketName == "Relief_Gold" || bucketName == "Door_Shadow"
            ? ShadowCastingMode.Off
            : ShadowCastingMode.On;
        renderer.receiveShadows = true;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
    }

    private static Material ResolveMaterial(ChannelPlayKhufuV8TempleArtPipeline.BucketInput bucket)
    {
        switch (bucket.Name)
        {
            case "Basalt_Court": return RequireV6Material("V6_Basalt_Court");
            case "Core_Limestone": return RequireV6Material("V6_Core_Limestone");
            case "Tura_Limestone": return RequireV6Material("V6_Tura_Casing");
            case "Tura_Processional_Aisle": return RequireV6Material("V6_Tura_Casing");
            default:
                var source = bucket.Items.Select(item => item.SourceMaterial).FirstOrDefault(item => item != null);
                if (source == null) throw new InvalidOperationException("Source material is missing for V8 bucket " + bucket.Name);
                return source;
        }
    }

    private static Material RequireV6Material(string name)
    {
        var material = ChannelPlayKhufuV6VisualFidelityBuilder.LoadMaterial(name);
        if (material == null) throw new InvalidOperationException("V6 material is missing: " + name);
        return material;
    }

    private static void DisableSupersededHubRenderers(Transform map)
    {
        var v5Hub = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_District_Pyramid_Temple_Hub");
        var v6Hub = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName + "/V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
        if (v5Hub == null || v6Hub == null) throw new InvalidOperationException("Superseded V5/V6 hub roots are missing.");
        var v5Renderers = v5Hub.GetComponentsInChildren<Renderer>(true);
        var v6Renderers = v6Hub.GetComponentsInChildren<Renderer>(true);
        if (v5Renderers.Length != ExpectedV5HubRenderers || v6Renderers.Length != ExpectedV6HubRenderers)
            throw new InvalidOperationException("Hub renderer whitelist drifted: V5=" + v5Renderers.Length + " V6=" + v6Renderers.Length);
        foreach (var renderer in v5Renderers.Concat(v6Renderers)) renderer.enabled = false;
    }

    private static void BuildAnchorsAndMetadata(Transform root, ChannelPlayKhufuV6VisualFidelityBuilder.Metrics baseline,
        IReadOnlyDictionary<string, Material> sourceMaterials)
    {
        Anchor(root, "V8_Anchor_Causeway_Threshold", new Vector3(0f, 0.6f, 19.65f));
        Anchor(root, "V8_Anchor_Open_Court", new Vector3(0f, 0.6f, 2f));
        Anchor(root, "V8_Anchor_Pyramid_Side_Exit", new Vector3(0f, 0.6f, -8f));
        Meta(root, "V8_META_SOURCE_FBX_SHA256_" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath));
        Meta(root, "V8_META_SOURCE_META_SHA256_" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath + ".meta"));
        Meta(root, "V8_META_SELECTOR_" + ChannelPlayKhufuV8TempleArtPipeline.ExpectedSelectedRenderers + "_" +
                   ChannelPlayKhufuV8TempleArtPipeline.ExpectedBucketCount + "_" +
                   ChannelPlayKhufuV8TempleArtPipeline.ExpectedCombinedVertices + "_" +
                   ChannelPlayKhufuV8TempleArtPipeline.ExpectedCombinedTriangles);
        Meta(root, "V8_META_FROZEN_V7_BASELINE_" + MetricsToken(baseline));
        Meta(root, "V8_META_HIDDEN_RENDERERS_V5_" + ExpectedV5HubRenderers + "_V6_" + ExpectedV6HubRenderers);
        Meta(root, "V8_META_MATERIAL_BUCKETS_" + sourceMaterials.Count);
        Meta(root, "V8_META_HISTORICALLY_INFORMED_GAME_ART_NOT_RECONSTRUCTION");
        Meta(root, "V8_META_DEEP_MAZE_TRAP_BURIAL_PYRAMID_CAP_EXCLUDED");
    }

    private static void Anchor(Transform parent, string name, Vector3 localPosition)
    {
        var anchor = new GameObject(name).transform;
        anchor.SetParent(parent, false);
        anchor.localPosition = localPosition;
    }

    private static void Meta(Transform parent, string name)
    {
        var child = new GameObject(name).transform;
        child.SetParent(parent, false);
    }

    private static Mesh BuildPillarMesh()
    {
        var vertices = new List<Vector3>();
        var normals = new List<Vector3>();
        var uvs = new List<Vector2>();
        var triangles = new List<int>();
        for (var index = 0; index < AuthoredPillarCount; index++)
        {
            var origin = PillarLocalPosition(index);
            AppendBox(vertices, normals, uvs, triangles, origin + new Vector3(0f, 0.31f, 0f), new Vector3(1.35f, 0.24f, 1.35f));
            AppendBox(vertices, normals, uvs, triangles, origin + new Vector3(0f, 2.35f, 0f), new Vector3(1.05f, 4f, 1.05f));
            AppendBox(vertices, normals, uvs, triangles, origin + new Vector3(0f, 4.49f, 0f), new Vector3(1.5f, 0.38f, 1.5f));
        }

        var mesh = new Mesh { name = "KhufuV8_Square_Red_Granite_Pillars", indexFormat = IndexFormat.UInt32 };
        mesh.SetVertices(vertices);
        mesh.SetNormals(normals);
        mesh.SetUVs(0, uvs);
        mesh.SetTriangles(triangles, 0, true);
        mesh.RecalculateBounds();
        return mesh;
    }

    private static void AppendBox(List<Vector3> vertices, List<Vector3> normals, List<Vector2> uvs,
        List<int> triangles, Vector3 center, Vector3 size)
    {
        var h = size * 0.5f;
        AppendFace(vertices, normals, uvs, triangles, center, Vector3.forward,
            new Vector3(-h.x, -h.y, h.z), new Vector3(h.x, -h.y, h.z), new Vector3(h.x, h.y, h.z), new Vector3(-h.x, h.y, h.z));
        AppendFace(vertices, normals, uvs, triangles, center, Vector3.back,
            new Vector3(h.x, -h.y, -h.z), new Vector3(-h.x, -h.y, -h.z), new Vector3(-h.x, h.y, -h.z), new Vector3(h.x, h.y, -h.z));
        AppendFace(vertices, normals, uvs, triangles, center, Vector3.right,
            new Vector3(h.x, -h.y, h.z), new Vector3(h.x, -h.y, -h.z), new Vector3(h.x, h.y, -h.z), new Vector3(h.x, h.y, h.z));
        AppendFace(vertices, normals, uvs, triangles, center, Vector3.left,
            new Vector3(-h.x, -h.y, -h.z), new Vector3(-h.x, -h.y, h.z), new Vector3(-h.x, h.y, h.z), new Vector3(-h.x, h.y, -h.z));
        AppendFace(vertices, normals, uvs, triangles, center, Vector3.up,
            new Vector3(-h.x, h.y, h.z), new Vector3(h.x, h.y, h.z), new Vector3(h.x, h.y, -h.z), new Vector3(-h.x, h.y, -h.z));
        AppendFace(vertices, normals, uvs, triangles, center, Vector3.down,
            new Vector3(-h.x, -h.y, -h.z), new Vector3(h.x, -h.y, -h.z), new Vector3(h.x, -h.y, h.z), new Vector3(-h.x, -h.y, h.z));
    }

    private static void AppendFace(List<Vector3> vertices, List<Vector3> normals, List<Vector2> uvs,
        List<int> triangles, Vector3 center, Vector3 normal, Vector3 a, Vector3 b, Vector3 c, Vector3 d)
    {
        var start = vertices.Count;
        vertices.Add(center + a);
        vertices.Add(center + b);
        vertices.Add(center + c);
        vertices.Add(center + d);
        for (var index = 0; index < 4; index++) normals.Add(normal);
        uvs.Add(new Vector2(0f, 0f));
        uvs.Add(new Vector2(1f, 0f));
        uvs.Add(new Vector2(1f, 1f));
        uvs.Add(new Vector2(0f, 1f));
        triangles.Add(start);
        triangles.Add(start + 1);
        triangles.Add(start + 2);
        triangles.Add(start);
        triangles.Add(start + 2);
        triangles.Add(start + 3);
    }

    private static Mesh SaveMeshAsset(Mesh generated, string path)
    {
        var existing = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (existing == null)
        {
            AssetDatabase.CreateAsset(generated, path);
            return generated;
        }
        EditorUtility.CopySerialized(generated, existing);
        existing.name = generated.name;
        EditorUtility.SetDirty(existing);
        UnityEngine.Object.DestroyImmediate(generated);
        return existing;
    }

    private static void EnsureAssetFolder()
    {
        var projectRoot = Directory.GetParent(Application.dataPath).FullName;
        Directory.CreateDirectory(Path.Combine(projectRoot, GeneratedMeshRoot));
        AssetDatabase.Refresh();
    }

    private static int TriangleCount(Mesh mesh)
    {
        var total = 0;
        for (var subMesh = 0; subMesh < mesh.subMeshCount; subMesh++) total += (int)mesh.GetIndexCount(subMesh) / 3;
        return total;
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }
}

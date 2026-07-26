using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV8TempleArtPipeline
{
    public const string SourceAssetPath = ChannelPlayKhufuV8TempleArtAudit.SourceAssetPath;
    public const string RunRoot = ChannelPlayKhufuV8TempleArtAudit.RunRoot;
    public const int ExpectedSelectedRenderers = 245;
    public const int ExpectedBucketCount = 9;
    public const int ExpectedCombinedVertices = 32110;
    public const int ExpectedCombinedTriangles = 26460;

    private static readonly string[] SelectedPrefixes =
    {
        "Exterior_Main_",
        "Exterior_Facade_Cornice",
        "Exterior_Facade_Painted_Band_",
        "Exterior_Left_Front_Relief_Panel",
        "Exterior_Right_Front_Relief_Panel",
        "Interior_Entrance_",
        "Interior_Hypostyle_Front_Wall_",
        "Interior_Hypostyle_Wall_Ritual_Scene_",
        "Interior_Hypostyle_Floor_Slab_Seam_",
        "Interior_Hypostyle_Floor_Cross_Seam_"
    };

    private static readonly HashSet<string> SelectedExactNames = new HashSet<string>(StringComparer.Ordinal)
    {
        "Exterior_Front_Court_Floor",
        "Interior_Hypostyle_Hall_Floor",
        "Interior_Hypostyle_Raised_Central_Aisle"
    };

    private static readonly string[] ForbiddenTokens =
    {
        "Collision",
        "Gameplay_",
        "Lighting_",
        "Camera_",
        "Pyramid_",
        "Trap_",
        "Burial_",
        "Rear_Exit",
        "Side_Room",
        "Service_Room",
        "Exterior_Main_Door_Shadow",
        "Exterior_Main_Podium",
        "Exterior_Main_Stair_",
        "Hypostyle_Column_",
        "Central_Aisle_Column_"
    };

    [MenuItem("Channel Play/Khufu V8/Run Combine Spike And Selector Dry Run")]
    public static void RunMenu()
    {
        var result = RunSpikeAndDryRun();
        if (!result.Passed) throw new InvalidOperationException("Khufu V8 art-pipeline spike failed: " + string.Join("; ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_PIPELINE_SPIKE result=passed selected=" + result.SelectedRenderers +
                  " combined_renderers=" + result.Buckets.Count + " vertices=" + result.CombinedVertices +
                  " triangles=" + result.CombinedTriangles);
    }

    public static void RunBatch()
    {
        try
        {
            RunMenu();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    public static bool IsSelectedRendererName(string name)
    {
        if (string.IsNullOrEmpty(name) || ForbiddenTokens.Any(token => name.IndexOf(token, StringComparison.Ordinal) >= 0))
            return false;
        return SelectedExactNames.Contains(name) || SelectedPrefixes.Any(prefix => name.StartsWith(prefix, StringComparison.Ordinal));
    }

    public static string BucketName(Renderer renderer, Material sourceMaterial)
    {
        var objectName = renderer == null ? string.Empty : renderer.name;
        if (objectName == "Exterior_Front_Court_Floor" || objectName == "Interior_Hypostyle_Hall_Floor")
            return "Basalt_Court";
        if (objectName == "Interior_Hypostyle_Raised_Central_Aisle") return "Tura_Processional_Aisle";

        var materialName = sourceMaterial == null ? string.Empty : sourceMaterial.name;
        if (materialName.IndexOf("Gold", StringComparison.OrdinalIgnoreCase) >= 0) return "Relief_Gold";
        if (materialName.IndexOf("Red", StringComparison.OrdinalIgnoreCase) >= 0) return "Paint_Red";
        if (materialName.IndexOf("Blue", StringComparison.OrdinalIgnoreCase) >= 0) return "Paint_Blue";
        if (materialName.IndexOf("Teal", StringComparison.OrdinalIgnoreCase) >= 0) return "Paint_Teal";
        if (materialName.IndexOf("Shadow", StringComparison.OrdinalIgnoreCase) >= 0) return "Door_Shadow";
        if (materialName.IndexOf("Block_Variant", StringComparison.OrdinalIgnoreCase) >= 0) return "Core_Limestone";
        if (materialName.IndexOf("Limestone", StringComparison.OrdinalIgnoreCase) >= 0) return "Tura_Limestone";
        if (materialName.IndexOf("Sand", StringComparison.OrdinalIgnoreCase) >= 0) return "Basalt_Court";
        return "Tura_Limestone";
    }

    public static List<BucketInput> CollectBucketInputs(GameObject sourceInstance)
    {
        var buckets = new Dictionary<string, BucketInput>(StringComparer.Ordinal);
        foreach (var renderer in sourceInstance.GetComponentsInChildren<Renderer>(true)
                     .Where(item => item.enabled && item.gameObject.activeInHierarchy && IsSelectedRendererName(item.name))
                     .OrderBy(item => HierarchyPath(sourceInstance.transform, item.transform), StringComparer.Ordinal))
        {
            var filter = renderer.GetComponent<MeshFilter>();
            var mesh = filter == null ? null : filter.sharedMesh;
            if (mesh == null) continue;
            var materials = renderer.sharedMaterials;
            for (var subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
            {
                var material = materials.Length == 0 ? null : materials[Math.Min(subMesh, materials.Length - 1)];
                var bucketName = BucketName(renderer, material);
                if (!buckets.TryGetValue(bucketName, out var bucket))
                {
                    bucket = new BucketInput { Name = bucketName };
                    buckets.Add(bucketName, bucket);
                }

                bucket.Items.Add(new CombineSource
                {
                    Path = HierarchyPath(sourceInstance.transform, renderer.transform),
                    ObjectName = renderer.name,
                    Mesh = mesh,
                    SubMeshIndex = subMesh,
                    Transform = renderer.transform.localToWorldMatrix,
                    SourceMaterial = material,
                    SourceMaterialName = material == null ? "<null>" : material.name
                });
            }
        }
        return buckets.Values.OrderBy(item => item.Name, StringComparer.Ordinal).ToList();
    }

    public static Mesh CombineBucket(BucketInput bucket)
    {
        var mesh = new Mesh
        {
            name = "KhufuV8_" + bucket.Name,
            indexFormat = IndexFormat.UInt32
        };
        var inputs = bucket.Items.Select(item => new CombineInstance
        {
            mesh = item.Mesh,
            subMeshIndex = item.SubMeshIndex,
            transform = item.Transform
        }).ToArray();
        mesh.CombineMeshes(inputs, true, true, false);
        mesh.RecalculateBounds();
        return mesh;
    }

    private static SpikeResult RunSpikeAndDryRun()
    {
        var projectRoot = Directory.GetParent(Application.dataPath).FullName;
        var outputRoot = Path.Combine(projectRoot, RunRoot);
        var sourceFullPath = Path.Combine(projectRoot, SourceAssetPath);
        var metaFullPath = sourceFullPath + ".meta";
        Directory.CreateDirectory(outputRoot);

        var result = new SpikeResult
        {
            SourceSha256Before = Sha256(sourceFullPath),
            MetaSha256Before = Sha256(metaFullPath)
        };

        AssetDatabase.ImportAsset(SourceAssetPath, ImportAssetOptions.ForceSynchronousImport);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(SourceAssetPath);
        if (model == null) throw new InvalidOperationException("Temple art FBX could not be loaded: " + SourceAssetPath);
        var importer = AssetImporter.GetAtPath(SourceAssetPath) as ModelImporter;
        result.ImporterReadable = importer != null && importer.isReadable;

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (instance == null) throw new InvalidOperationException("Temple art FBX could not be instantiated.");

        try
        {
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;
            var buckets = CollectBucketInputs(instance);
            result.SelectedRenderers = buckets.SelectMany(item => item.Items).Select(item => item.Path).Distinct().Count();
            result.SelectedSubMeshes = buckets.Sum(item => item.Items.Count);
            result.ForbiddenSelected = buckets.SelectMany(item => item.Items)
                .Count(item => ForbiddenTokens.Any(token => item.ObjectName.IndexOf(token, StringComparison.Ordinal) >= 0));

            var firstPair = buckets.SelectMany(item => item.Items).Take(2).ToArray();
            if (firstPair.Length != 2)
            {
                result.Failures.Add("Fewer than two donor submeshes were selected for the combine spike");
            }
            else
            {
                var spikeBucket = new BucketInput { Name = "Readability_Spike" };
                spikeBucket.Items.AddRange(firstPair);
                var expectedVertices = firstPair.Sum(item => item.Mesh.vertexCount);
                var spike = CombineBucket(spikeBucket);
                result.SpikeVertices = spike.vertexCount;
                result.SpikeTriangles = TriangleCount(spike);
                result.SpikeVertexRatio = expectedVertices == 0 ? 0f : (float)spike.vertexCount / expectedVertices;
                if (spike.vertexCount <= 0 || result.SpikeTriangles <= 0)
                    result.Failures.Add("Two-submesh readability spike produced an empty mesh");
                UnityEngine.Object.DestroyImmediate(spike);
            }

            foreach (var bucket in buckets)
            {
                var combined = CombineBucket(bucket);
                var audit = new BucketAudit
                {
                    Name = bucket.Name,
                    SourceRenderers = bucket.Items.Select(item => item.Path).Distinct().Count(),
                    SourceSubMeshes = bucket.Items.Count,
                    SourceVertexReferences = bucket.Items.Sum(item => (long)item.Mesh.vertexCount),
                    Vertices = combined.vertexCount,
                    Triangles = TriangleCount(combined),
                    BoundsCenter = combined.bounds.center,
                    BoundsSize = combined.bounds.size
                };
                result.Buckets.Add(audit);
                result.CombinedVertices += audit.Vertices;
                result.CombinedTriangles += audit.Triangles;
                UnityEngine.Object.DestroyImmediate(combined);
            }

            if (result.ForbiddenSelected != 0) result.Failures.Add("Forbidden donor geometry entered the selector");
            if (result.SelectedRenderers != ExpectedSelectedRenderers)
                result.Failures.Add("Selector renderer count drifted from " + ExpectedSelectedRenderers);
            if (result.Buckets.Count != ExpectedBucketCount)
                result.Failures.Add("Selector bucket count drifted from " + ExpectedBucketCount);
            if (result.CombinedVertices != ExpectedCombinedVertices)
                result.Failures.Add("Selector combined vertices drifted from " + ExpectedCombinedVertices);
            if (result.CombinedTriangles != ExpectedCombinedTriangles)
                result.Failures.Add("Selector combined triangles drifted from " + ExpectedCombinedTriangles);
            if (result.Buckets.Count > 10) result.Failures.Add("Material selector exceeded the 10 donor-bucket dry-run limit");
            if (result.CombinedVertices > 100000) result.Failures.Add("Selected donor meshes exceed 100,000 combined vertices before authored pillars");
            if (result.CombinedTriangles > 80000) result.Failures.Add("Selected donor meshes exceed 80,000 combined triangles before authored pillars");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
            result.SourceSha256After = Sha256(sourceFullPath);
            result.MetaSha256After = Sha256(metaFullPath);
        }

        if (result.SourceSha256Before != result.SourceSha256After) result.Failures.Add("FBX bytes changed during the dry run");
        if (result.MetaSha256Before != result.MetaSha256After) result.Failures.Add("FBX meta changed during the dry run");
        result.Passed = result.Failures.Count == 0;
        File.WriteAllText(Path.Combine(outputRoot, "pipeline-spike.json"), JsonUtility.ToJson(result, true));
        File.WriteAllText(Path.Combine(outputRoot, "pipeline-spike.md"), BuildMarkdown(result));
        return result;
    }

    private static string BuildMarkdown(SpikeResult result)
    {
        var text = new StringBuilder("# Khufu V8 Combine Spike And Selector Dry Run\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- ModelImporter Read/Write enabled: `" + result.ImporterReadable + "`");
        text.AppendLine("- FBX SHA256 before/after: `" + result.SourceSha256Before + "` / `" + result.SourceSha256After + "`");
        text.AppendLine("- FBX meta SHA256 before/after: `" + result.MetaSha256Before + "` / `" + result.MetaSha256After + "`");
        text.AppendLine("- Two-submesh spike: `" + result.SpikeVertices + " vertices / " + result.SpikeTriangles + " triangles / vertex ratio " + result.SpikeVertexRatio.ToString("0.###") + "`");
        text.AppendLine("- Selected renderers/submeshes: `" + result.SelectedRenderers + " / " + result.SelectedSubMeshes + "`");
        text.AppendLine("- Forbidden selected: `" + result.ForbiddenSelected + "`");
        text.AppendLine("- Combined donor metrics: `" + result.Buckets.Count + " renderers / " + result.CombinedVertices + " vertices / " + result.CombinedTriangles + " triangles`");
        text.AppendLine();
        text.AppendLine("| Bucket | Source renderers | Submeshes | Source vertex refs | Combined vertices | Triangles | Bounds size |");
        text.AppendLine("|---|---:|---:|---:|---:|---:|---|");
        foreach (var bucket in result.Buckets)
        {
            text.AppendLine("| `" + bucket.Name + "` | " + bucket.SourceRenderers + " | " + bucket.SourceSubMeshes + " | " + bucket.SourceVertexReferences + " | " + bucket.Vertices + " | " + bucket.Triangles + " | `" + VectorToken(bucket.BoundsSize) + "` |");
        }
        foreach (var failure in result.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V8_PIPELINE_SPIKE: " + (result.Passed ? "passed" : "failed"));
        return text.ToString();
    }

    private static long TriangleCount(Mesh mesh)
    {
        long total = 0;
        for (var subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
        {
            if (mesh.GetTopology(subMesh) == MeshTopology.Triangles) total += (long)mesh.GetIndexCount(subMesh) / 3L;
        }
        return total;
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

    private static string Sha256(string path)
    {
        if (!File.Exists(path)) return string.Empty;
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
        {
            return string.Concat(sha.ComputeHash(stream).Select(item => item.ToString("x2")));
        }
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("0.###") + ", " + value.y.ToString("0.###") + ", " + value.z.ToString("0.###");
    }

    public sealed class BucketInput
    {
        public string Name;
        public readonly List<CombineSource> Items = new List<CombineSource>();
    }

    public sealed class CombineSource
    {
        public string Path;
        public string ObjectName;
        public Mesh Mesh;
        public int SubMeshIndex;
        public Matrix4x4 Transform;
        public Material SourceMaterial;
        public string SourceMaterialName;
    }

    [Serializable]
    private sealed class SpikeResult
    {
        public bool Passed;
        public bool ImporterReadable;
        public string SourceSha256Before;
        public string SourceSha256After;
        public string MetaSha256Before;
        public string MetaSha256After;
        public int SpikeVertices;
        public long SpikeTriangles;
        public float SpikeVertexRatio;
        public int SelectedRenderers;
        public int SelectedSubMeshes;
        public int ForbiddenSelected;
        public long CombinedVertices;
        public long CombinedTriangles;
        public List<BucketAudit> Buckets = new List<BucketAudit>();
        public List<string> Failures = new List<string>();
    }

    [Serializable]
    private sealed class BucketAudit
    {
        public string Name;
        public int SourceRenderers;
        public int SourceSubMeshes;
        public long SourceVertexReferences;
        public int Vertices;
        public long Triangles;
        public Vector3 BoundsCenter;
        public Vector3 BoundsSize;
    }
}

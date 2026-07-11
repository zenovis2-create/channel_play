using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV8TempleArtAudit
{
    public const string SourceAssetPath = "Assets/_Project/Art/Maps/pyramid_temple_real/pyramid_temple_full_environment.fbx";
    public const string RunRoot = "runs/khufu-v8-temple-production-art";
    private static readonly HashSet<string> LandmarkNames = new HashSet<string>(StringComparer.Ordinal)
    {
        "Exterior_Desert_Foundation",
        "Exterior_Main_Door_Shadow",
        "Exterior_Top_Pyramid_Cap",
        "Interior_Hypostyle_Hall_Floor",
        "Interior_Burial_Chamber_Floor",
        "Exterior_Rear_Service_Door_Shadow",
        "Gameplay_PlayerSpawn_FrontCourt",
        "Gameplay_HypostyleHall_Center",
        "Gameplay_BurialChamber_Goal",
        "Gameplay_RearExit"
    };

    [MenuItem("Channel Play/Khufu V8/Audit Source Temple Art")]
    public static void AuditMenu()
    {
        var report = Audit();
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_ART_AUDIT result=passed renderers=" + report.Renderers +
                  " vertices=" + report.Vertices + " triangles=" + report.Triangles);
    }

    public static void RunBatch()
    {
        try
        {
            AuditMenu();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static AuditReport Audit()
    {
        var projectRoot = Directory.GetParent(Application.dataPath).FullName;
        var outputRoot = Path.Combine(projectRoot, RunRoot);
        Directory.CreateDirectory(outputRoot);

        AssetDatabase.ImportAsset(SourceAssetPath, ImportAssetOptions.ForceSynchronousImport);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(SourceAssetPath);
        if (model == null) throw new InvalidOperationException("Temple art FBX could not be loaded: " + SourceAssetPath);

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (instance == null) throw new InvalidOperationException("Temple art FBX could not be instantiated.");

        try
        {
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;
            var report = BuildReport(instance);
            File.WriteAllText(Path.Combine(outputRoot, "fbx-audit.json"), JsonUtility.ToJson(report, true));
            File.WriteAllText(Path.Combine(outputRoot, "fbx-audit.md"), BuildMarkdown(report));
            return report;
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static AuditReport BuildReport(GameObject instance)
    {
        var report = new AuditReport
        {
            SourceAssetPath = SourceAssetPath,
            SourceBytes = new FileInfo(Path.Combine(Directory.GetParent(Application.dataPath).FullName, SourceAssetPath)).Length,
            Transforms = instance.GetComponentsInChildren<Transform>(true).Length,
            Colliders = instance.GetComponentsInChildren<Collider>(true).Length,
            Lights = instance.GetComponentsInChildren<Light>(true).Length,
            Cameras = instance.GetComponentsInChildren<Camera>(true).Length
        };

        var renderers = instance.GetComponentsInChildren<Renderer>(true);
        var uniqueMeshes = new HashSet<Mesh>();
        var materialStats = new Dictionary<string, MaterialAudit>(StringComparer.Ordinal);
        var rendererAudits = new List<RendererAudit>();
        var combinedBounds = new Bounds();
        var hasBounds = false;

        foreach (var renderer in renderers)
        {
            var mesh = MeshFor(renderer);
            var vertices = mesh == null ? 0 : mesh.vertexCount;
            var triangles = TriangleCount(mesh);
            if (mesh != null) uniqueMeshes.Add(mesh);

            report.Renderers++;
            report.Vertices += vertices;
            report.Triangles += triangles;
            if (renderer.enabled) report.EnabledRenderers++;
            if (renderer.gameObject.activeInHierarchy && renderer.enabled)
            {
                report.VisibleCandidateRenderers++;
                if (!hasBounds)
                {
                    combinedBounds = renderer.bounds;
                    hasBounds = true;
                }
                else
                {
                    combinedBounds.Encapsulate(renderer.bounds);
                }
            }

            var materials = renderer.sharedMaterials;
            for (var subMesh = 0; subMesh < materials.Length; subMesh++)
            {
                var materialName = materials[subMesh] == null ? "<null>" : materials[subMesh].name;
                if (!materialStats.TryGetValue(materialName, out var stat))
                {
                    stat = new MaterialAudit { Name = materialName };
                    materialStats.Add(materialName, stat);
                }

                stat.RendererSlots++;
                stat.Vertices += vertices;
                stat.Triangles += TriangleCount(mesh, subMesh);
            }

            rendererAudits.Add(new RendererAudit
            {
                Path = RelativePath(instance.transform, renderer.transform),
                Enabled = renderer.enabled,
                Vertices = vertices,
                Triangles = triangles,
                MaterialSlots = materials.Length
            });
        }

        report.UniqueMeshes = uniqueMeshes.Count;
        report.Materials = materialStats.Values.OrderByDescending(item => item.Triangles).ThenBy(item => item.Name).ToList();
        report.HeaviestRenderers = rendererAudits.OrderByDescending(item => item.Triangles).ThenBy(item => item.Path).Take(30).ToList();
        if (hasBounds)
        {
            report.BoundsCenter = combinedBounds.center;
            report.BoundsSize = combinedBounds.size;
        }

        foreach (Transform child in instance.transform)
        {
            AddHierarchyAudit(report, instance.transform, child, 1);
        }

        report.Landmarks = instance.GetComponentsInChildren<Transform>(true)
            .Where(item => LandmarkNames.Contains(item.name))
            .Select(item => new LandmarkAudit
            {
                Name = item.name,
                Path = RelativePath(instance.transform, item),
                Position = item.position,
                LocalScale = item.lossyScale,
                Active = item.gameObject.activeInHierarchy
            })
            .OrderBy(item => item.Name)
            .ToList();

        return report;
    }

    private static void AddHierarchyAudit(AuditReport report, Transform root, Transform node, int depth)
    {
        if (depth <= 2)
        {
            var renderers = node.GetComponentsInChildren<Renderer>(true);
            report.Groups.Add(new GroupAudit
            {
                Path = RelativePath(root, node),
                Depth = depth,
                Transforms = node.GetComponentsInChildren<Transform>(true).Length,
                Renderers = renderers.Length,
                EnabledRenderers = renderers.Count(item => item.enabled && item.gameObject.activeInHierarchy),
                Vertices = renderers.Sum(item => MeshFor(item) == null ? 0L : MeshFor(item).vertexCount),
                Triangles = renderers.Sum(item => TriangleCount(MeshFor(item))),
                Colliders = node.GetComponentsInChildren<Collider>(true).Length
            });
        }

        if (depth >= 2) return;
        foreach (Transform child in node) AddHierarchyAudit(report, root, child, depth + 1);
    }

    private static Mesh MeshFor(Renderer renderer)
    {
        if (renderer is SkinnedMeshRenderer skinned) return skinned.sharedMesh;
        var filter = renderer.GetComponent<MeshFilter>();
        return filter == null ? null : filter.sharedMesh;
    }

    private static long TriangleCount(Mesh mesh, int onlySubMesh = -1)
    {
        if (mesh == null) return 0;
        var first = onlySubMesh < 0 ? 0 : onlySubMesh;
        var last = onlySubMesh < 0 ? mesh.subMeshCount : Math.Min(mesh.subMeshCount, onlySubMesh + 1);
        long triangles = 0;
        for (var index = first; index < last; index++)
        {
            if (mesh.GetTopology(index) == MeshTopology.Triangles) triangles += (long)mesh.GetIndexCount(index) / 3L;
        }
        return triangles;
    }

    private static string RelativePath(Transform root, Transform node)
    {
        if (node == root) return root.name;
        var names = new Stack<string>();
        var cursor = node;
        while (cursor != null && cursor != root)
        {
            names.Push(cursor.name);
            cursor = cursor.parent;
        }
        return string.Join("/", names);
    }

    private static string BuildMarkdown(AuditReport report)
    {
        var text = new StringBuilder("# Khufu V8 Source Temple Art Audit\n\n");
        text.AppendLine("- Source: `" + report.SourceAssetPath + "`");
        text.AppendLine("- Source bytes: `" + report.SourceBytes + "`");
        text.AppendLine("- Transforms: `" + report.Transforms + "`");
        text.AppendLine("- Renderers: `" + report.Renderers + "` (`" + report.EnabledRenderers + "` enabled, `" + report.VisibleCandidateRenderers + "` active candidates)");
        text.AppendLine("- Unique meshes: `" + report.UniqueMeshes + "`");
        text.AppendLine("- Vertices: `" + report.Vertices + "`");
        text.AppendLine("- Triangles: `" + report.Triangles + "`");
        text.AppendLine("- Colliders / lights / cameras: `" + report.Colliders + " / " + report.Lights + " / " + report.Cameras + "`");
        text.AppendLine("- Active renderer bounds center: `" + VectorToken(report.BoundsCenter) + "`");
        text.AppendLine("- Active renderer bounds size: `" + VectorToken(report.BoundsSize) + "`");
        text.AppendLine();
        text.AppendLine("## Hierarchy Groups");
        text.AppendLine();
        text.AppendLine("| Path | Depth | Transforms | Renderers | Enabled | Vertices | Triangles | Colliders |");
        text.AppendLine("|---|---:|---:|---:|---:|---:|---:|---:|");
        foreach (var group in report.Groups)
        {
            text.AppendLine("| `" + group.Path + "` | " + group.Depth + " | " + group.Transforms + " | " + group.Renderers + " | " + group.EnabledRenderers + " | " + group.Vertices + " | " + group.Triangles + " | " + group.Colliders + " |");
        }
        text.AppendLine();
        text.AppendLine("## Material Combine Buckets");
        text.AppendLine();
        text.AppendLine("| Material | Renderer slots | Vertex references | Triangles |");
        text.AppendLine("|---|---:|---:|---:|");
        foreach (var material in report.Materials)
        {
            text.AppendLine("| `" + material.Name + "` | " + material.RendererSlots + " | " + material.Vertices + " | " + material.Triangles + " |");
        }
        text.AppendLine();
        text.AppendLine("## Landmarks");
        text.AppendLine();
        text.AppendLine("| Name | Position | Scale | Active |");
        text.AppendLine("|---|---|---|---|");
        foreach (var landmark in report.Landmarks)
        {
            text.AppendLine("| `" + landmark.Name + "` | `" + VectorToken(landmark.Position) + "` | `" + VectorToken(landmark.LocalScale) + "` | `" + landmark.Active + "` |");
        }
        text.AppendLine();
        text.AppendLine("## Heaviest Renderers");
        text.AppendLine();
        foreach (var renderer in report.HeaviestRenderers)
        {
            text.AppendLine("- `" + renderer.Path + "`: " + renderer.Vertices + " vertices, " + renderer.Triangles + " triangles, " + renderer.MaterialSlots + " material slots, enabled=" + renderer.Enabled);
        }
        text.AppendLine();
        text.AppendLine("KHUFU_V8_SOURCE_ART_AUDIT: passed");
        return text.ToString();
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("0.###") + ", " + value.y.ToString("0.###") + ", " + value.z.ToString("0.###");
    }

    [Serializable]
    private sealed class AuditReport
    {
        public string SourceAssetPath;
        public long SourceBytes;
        public int Transforms;
        public int Renderers;
        public int EnabledRenderers;
        public int VisibleCandidateRenderers;
        public int UniqueMeshes;
        public long Vertices;
        public long Triangles;
        public int Colliders;
        public int Lights;
        public int Cameras;
        public Vector3 BoundsCenter;
        public Vector3 BoundsSize;
        public List<GroupAudit> Groups = new List<GroupAudit>();
        public List<MaterialAudit> Materials = new List<MaterialAudit>();
        public List<LandmarkAudit> Landmarks = new List<LandmarkAudit>();
        public List<RendererAudit> HeaviestRenderers = new List<RendererAudit>();
    }

    [Serializable]
    private sealed class GroupAudit
    {
        public string Path;
        public int Depth;
        public int Transforms;
        public int Renderers;
        public int EnabledRenderers;
        public long Vertices;
        public long Triangles;
        public int Colliders;
    }

    [Serializable]
    private sealed class MaterialAudit
    {
        public string Name;
        public int RendererSlots;
        public long Vertices;
        public long Triangles;
    }

    [Serializable]
    private sealed class RendererAudit
    {
        public string Path;
        public bool Enabled;
        public int Vertices;
        public long Triangles;
        public int MaterialSlots;
    }

    [Serializable]
    private sealed class LandmarkAudit
    {
        public string Name;
        public string Path;
        public Vector3 Position;
        public Vector3 LocalScale;
        public bool Active;
    }
}

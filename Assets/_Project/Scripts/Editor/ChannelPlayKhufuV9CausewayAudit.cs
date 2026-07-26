using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV9CausewayAudit
{
    public const string RunRoot = "runs/khufu-v9-causeway-fidelity";
    private const string ScenePath = ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath;
    private const string SourcePath = ChannelPlayKhufuV8TempleArtAudit.SourceAssetPath;
    private const int ExpectedTargetRenderers = 20;
    private const int ExpectedInheritedFloorColliders = 2;

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

    private static readonly string[] SourceTokens =
    {
        "Causeway",
        "Entrance",
        "Exterior_Main_",
        "Hypostyle"
    };

    [MenuItem("Channel Play/Khufu V9/Audit Causeway Sources And Scene")]
    public static void RunMenu()
    {
        var report = Audit();
        if (!report.Passed)
            throw new InvalidOperationException("Khufu V9 causeway audit failed: " + string.Join("; ", report.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V9_AUDIT result=passed target_renderers=" + report.TargetRenderers.Count +
                  " inherited_floor_colliders=" + report.InheritedFloorColliders.Count +
                  " source_candidates=" + report.SourceCandidates.Count);
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

    private static AuditReport Audit()
    {
        var projectRoot = Directory.GetParent(Application.dataPath).FullName;
        var outputRoot = Path.Combine(projectRoot, RunRoot);
        Directory.CreateDirectory(outputRoot);
        var report = new AuditReport();

        AuditScene(report);
        AuditSource(report);

        if (report.TargetRenderers.Count != ExpectedTargetRenderers)
            report.Failures.Add("Target renderer count drifted from " + ExpectedTargetRenderers);
        if (report.TargetRenderers.Count(item => item.Enabled) != ExpectedTargetRenderers)
            report.Failures.Add("One or more target renderers is already disabled");
        if (report.InheritedFloorColliders.Count != ExpectedInheritedFloorColliders)
            report.Failures.Add("Inherited floor collider count drifted from " + ExpectedInheritedFloorColliders);
        if (report.InheritedFloorColliders.Any(item => !item.Enabled || item.IsTrigger || item.Type != "BoxCollider"))
            report.Failures.Add("Inherited floor collider contract is invalid");
        if (report.SourceCandidates.Count == 0)
            report.Failures.Add("No source-art candidates matched the causeway selector tokens");

        report.Passed = report.Failures.Count == 0;
        File.WriteAllText(Path.Combine(outputRoot, "audit.json"), JsonUtility.ToJson(report, true));
        File.WriteAllText(Path.Combine(outputRoot, "audit.md"), BuildMarkdown(report));
        return report;
    }

    private static void AuditScene(AuditReport report)
    {
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        if (map == null) throw new InvalidOperationException("Shared map root is missing.");
        var v5 = map.transform.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName);
        if (v5 == null) throw new InvalidOperationException("V5 root is missing.");

        foreach (var districtName in DistrictNames)
        {
            var district = v5.Find(districtName);
            if (district == null)
            {
                report.Failures.Add("District is missing: " + districtName);
                continue;
            }
            foreach (var renderer in district.GetComponentsInChildren<Renderer>(true))
                report.TargetRenderers.Add(RendererRecord(v5, renderer));
        }

        var route = v5.Find("V5_Critical_Route_700_900m");
        if (route == null) throw new InvalidOperationException("V5 critical route is missing.");
        foreach (var segmentName in RouteSegmentNames)
        {
            foreach (Transform child in route)
            {
                if (!child.name.StartsWith(segmentName + "_", StringComparison.Ordinal)) continue;
                var renderer = child.GetComponent<Renderer>();
                if (renderer != null) report.TargetRenderers.Add(RendererRecord(v5, renderer));
                var collider = child.GetComponent<Collider>();
                if (collider != null && (segmentName == "V5_Route_Segment_00" || segmentName == "V5_Route_Segment_01") &&
                    child.name.EndsWith("_Floor", StringComparison.Ordinal))
                {
                    report.InheritedFloorColliders.Add(ColliderRecord(v5, collider));
                }
            }
        }

        report.TargetRenderers = report.TargetRenderers.OrderBy(item => item.Path, StringComparer.Ordinal).ToList();
        report.InheritedFloorColliders = report.InheritedFloorColliders.OrderBy(item => item.Path, StringComparer.Ordinal).ToList();
    }

    private static void AuditSource(AuditReport report)
    {
        AssetDatabase.ImportAsset(SourcePath, ImportAssetOptions.ForceSynchronousImport);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(SourcePath);
        if (model == null) throw new InvalidOperationException("Temple source FBX could not be loaded.");

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var instance = PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (instance == null) throw new InvalidOperationException("Temple source FBX could not be instantiated.");
        try
        {
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;
            report.SourceCandidates = instance.GetComponentsInChildren<Renderer>(true)
                .Where(item => SourceTokens.Any(token => item.name.IndexOf(token, StringComparison.OrdinalIgnoreCase) >= 0))
                .Select(item => RendererRecord(instance.transform, item))
                .OrderBy(item => item.Path, StringComparer.Ordinal)
                .ToList();
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static RendererAudit RendererRecord(Transform root, Renderer renderer)
    {
        var meshFilter = renderer.GetComponent<MeshFilter>();
        var mesh = meshFilter == null ? null : meshFilter.sharedMesh;
        return new RendererAudit
        {
            Path = RelativePath(root, renderer.transform),
            Name = renderer.name,
            Enabled = renderer.enabled,
            BoundsCenter = renderer.bounds.center,
            BoundsSize = renderer.bounds.size,
            Vertices = mesh == null ? 0 : mesh.vertexCount,
            Triangles = mesh == null ? 0 : mesh.triangles.Length / 3,
            Materials = string.Join(",", renderer.sharedMaterials.Select(item => item == null ? "<null>" : item.name))
        };
    }

    private static ColliderAudit ColliderRecord(Transform root, Collider collider)
    {
        return new ColliderAudit
        {
            Path = RelativePath(root, collider.transform),
            Type = collider.GetType().Name,
            Enabled = collider.enabled,
            IsTrigger = collider.isTrigger,
            BoundsCenter = collider.bounds.center,
            BoundsSize = collider.bounds.size
        };
    }

    private static string RelativePath(Transform root, Transform node)
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

    private static string BuildMarkdown(AuditReport report)
    {
        var text = new StringBuilder("# Khufu V9 Causeway Source And Scene Audit\n\n");
        text.AppendLine("- Verdict: **" + (report.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Target renderers: `" + report.TargetRenderers.Count + "`");
        text.AppendLine("- Inherited forward floor colliders: `" + report.InheritedFloorColliders.Count + "`");
        text.AppendLine("- Source candidates: `" + report.SourceCandidates.Count + "`");
        text.AppendLine();
        text.AppendLine("## Scene Targets");
        text.AppendLine();
        foreach (var item in report.TargetRenderers)
            text.AppendLine("- `" + item.Path + "`: enabled=" + item.Enabled + ", bounds=`" + VectorToken(item.BoundsSize) + "`");
        text.AppendLine();
        text.AppendLine("## Inherited Floor Colliders");
        text.AppendLine();
        foreach (var item in report.InheritedFloorColliders)
            text.AppendLine("- `" + item.Path + "`: " + item.Type + ", center=`" + VectorToken(item.BoundsCenter) + "`, size=`" + VectorToken(item.BoundsSize) + "`");
        text.AppendLine();
        text.AppendLine("## Source Candidates");
        text.AppendLine();
        foreach (var item in report.SourceCandidates.Take(160))
            text.AppendLine("- `" + item.Path + "`: " + item.Vertices + " vertices, " + item.Triangles + " triangles, materials=`" + item.Materials + "`");
        foreach (var failure in report.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V9_AUDIT: " + (report.Passed ? "passed" : "failed"));
        return text.ToString();
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("0.###") + ", " + value.y.ToString("0.###") + ", " + value.z.ToString("0.###");
    }

    [Serializable]
    private sealed class AuditReport
    {
        public bool Passed;
        public List<RendererAudit> TargetRenderers = new List<RendererAudit>();
        public List<ColliderAudit> InheritedFloorColliders = new List<ColliderAudit>();
        public List<RendererAudit> SourceCandidates = new List<RendererAudit>();
        public List<string> Failures = new List<string>();
    }

    [Serializable]
    private sealed class RendererAudit
    {
        public string Path;
        public string Name;
        public bool Enabled;
        public Vector3 BoundsCenter;
        public Vector3 BoundsSize;
        public int Vertices;
        public int Triangles;
        public string Materials;
    }

    [Serializable]
    private sealed class ColliderAudit
    {
        public string Path;
        public string Type;
        public bool Enabled;
        public bool IsTrigger;
        public Vector3 BoundsCenter;
        public Vector3 BoundsSize;
    }
}

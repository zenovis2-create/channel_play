using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV10InteriorAudit
{
    public const string RunRoot = "runs/khufu-v10-interior-spine";
    public const string ManifestPath = "docs/khufu-v10-interior-spine/disable-manifest.json";
    private const string ScenePath = ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath;
    private const int ExpectedTargetRenderers = 45;
    private const int ExpectedTargetColliders = 39;

    private static readonly string[] RequiredMarkers =
    {
        "V4_Route_Entrance",
        "V4_Route_Branch",
        "V4_Route_Subterranean_Approach",
        "V4_Route_Subterranean_Chamber",
        "V4_Route_Gallery_Foot",
        "V4_Route_Queens_Chamber",
        "V4_Route_Grand_Gallery_Top",
        "V4_Route_Kings_Chamber"
    };

    private static readonly string[] ForbiddenTargetTokens =
    {
        "V4_Descending_Bedrock",
        "V4_Subterranean_Level",
        "V4_Queens_Horizontal",
        "V4_Subterranean_Chamber",
        "V4_Queens_Chamber",
        "V4_Kings_Embedded_Suite",
        "V4_Antechamber",
        "V4_Portcullis",
        "V4_Relieving"
    };

    [MenuItem("Channel Play/Khufu V10/Audit Interior Pre-Write Contract")]
    public static void RunMenu()
    {
        var report = Audit();
        if (!report.Passed)
            throw new InvalidOperationException("Khufu V10 pre-write audit failed: " + string.Join("; ", report.Failures));

        Debug.Log("CHANNEL_PLAY_KHUFU_V10_AUDIT result=passed renderers=" + report.Transitions.Count +
                  " colliders=" + report.Transitions.Count(item => item.DisableCollider) +
                  " crown_dependencies=" + report.CrownDependencies.Count +
                  " crown_intersection=" + report.CrownIntersection.Count);
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

        var report = new AuditReport
        {
            ScenePath = ScenePath,
            SceneSha256 = Sha256(Path.Combine(projectRoot, ScenePath))
        };

        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        if (map == null) throw new InvalidOperationException("Shared map root is missing.");
        var v4 = map.transform.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        var v5 = map.transform.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName);
        if (v4 == null || v5 == null) throw new InvalidOperationException("V4 or V5 root is missing.");
        if (map.transform.Find("Runtime_Khufu_V10_Interior_Spine") != null)
            report.Failures.Add("V10 scene root already exists before the pre-write audit");

        var interior = v4.Find("V4_Embedded_Interior_Architecture");
        var entrance = interior == null ? null : interior.Find("V4_Entrance_Portal");
        var gallery = interior == null ? null : interior.Find("V4_Grand_Gallery_Corbelled");
        var district = v5.Find("V5_District_Authentic_Interior_Spine");
        var crown = v5.Find("V5_KeyRoute_Crown");
        if (interior == null || entrance == null || gallery == null || district == null || crown == null)
            throw new InvalidOperationException("One or more audited V4/V5 ownership roots are missing.");

        var targets = new List<Renderer>();
        targets.AddRange(interior.GetComponentsInChildren<Renderer>(true).Where(renderer =>
            renderer.transform.parent == interior &&
            (renderer.name.StartsWith("V4_Descending_Upper_", StringComparison.Ordinal) ||
             renderer.name.StartsWith("V4_Ascending_Passage_", StringComparison.Ordinal))));
        targets.AddRange(entrance.GetComponentsInChildren<Renderer>(true));
        targets.AddRange(gallery.GetComponentsInChildren<Renderer>(true));
        targets.AddRange(district.GetComponentsInChildren<Renderer>(true));

        report.Transitions = targets
            .Distinct()
            .Select(renderer => Transition(map.transform, renderer))
            .OrderBy(item => item.Path, StringComparer.Ordinal)
            .ToList();

        report.CrownDependencies = crown.GetComponentsInChildren<Transform>(true)
            .Select(item => RelativePath(map.transform, item))
            .OrderBy(item => item, StringComparer.Ordinal)
            .ToList();
        var crownSet = new HashSet<string>(report.CrownDependencies, StringComparer.Ordinal);
        report.CrownIntersection = report.Transitions.Select(item => item.Path)
            .Where(crownSet.Contains)
            .OrderBy(item => item, StringComparer.Ordinal)
            .ToList();

        var allV4Transforms = v4.GetComponentsInChildren<Transform>(true);
        foreach (var markerName in RequiredMarkers)
        {
            var marker = allV4Transforms.FirstOrDefault(item => item.name == markerName);
            if (marker == null)
            {
                report.Failures.Add("Required V4 marker is missing: " + markerName);
                continue;
            }
            report.Markers.Add(new MarkerRecord
            {
                Name = markerName,
                Path = RelativePath(map.transform, marker),
                Position = marker.position
            });
        }

        if (report.Transitions.Count != ExpectedTargetRenderers)
            report.Failures.Add("Target renderer count drifted from " + ExpectedTargetRenderers + " to " + report.Transitions.Count);
        if (report.Transitions.Count(item => item.DisableCollider) != ExpectedTargetColliders)
            report.Failures.Add("Target collider count drifted from " + ExpectedTargetColliders + " to " +
                                report.Transitions.Count(item => item.DisableCollider));
        if (report.Transitions.Any(item => !item.RendererEnabled))
            report.Failures.Add("One or more target renderers is already disabled");
        if (report.Transitions.Any(item => item.DisableCollider && (!item.ColliderEnabled || item.ColliderIsTrigger)))
            report.Failures.Add("One or more target collider has an unexpected pre-write state");
        if (report.Transitions.Any(item => ForbiddenTargetTokens.Any(token => item.Path.Contains(token))))
            report.Failures.Add("Transition manifest crosses a Royal or Subterranean ownership token");
        if (report.CrownIntersection.Count != 0)
            report.Failures.Add("Transition manifest intersects V5 Crown dependencies");
        if (report.Markers.Count != RequiredMarkers.Length)
            report.Failures.Add("V4 marker snapshot is incomplete");

        report.Passed = report.Failures.Count == 0;
        File.WriteAllText(Path.Combine(outputRoot, "audit.json"), JsonUtility.ToJson(report, true));
        File.WriteAllText(Path.Combine(outputRoot, "audit.md"), Markdown(report));
        File.WriteAllText(Path.Combine(projectRoot, ManifestPath), JsonUtility.ToJson(Manifest(report), true));
        return report;
    }

    private static TransitionRecord Transition(Transform map, Renderer renderer)
    {
        var collider = renderer.GetComponent<Collider>();
        return new TransitionRecord
        {
            Path = RelativePath(map, renderer.transform),
            Name = renderer.name,
            RendererEnabled = renderer.enabled,
            DisableRenderer = true,
            ColliderType = collider == null ? string.Empty : collider.GetType().Name,
            ColliderEnabled = collider != null && collider.enabled,
            ColliderIsTrigger = collider != null && collider.isTrigger,
            DisableCollider = collider != null,
            BoundsCenter = renderer.bounds.center,
            BoundsSize = renderer.bounds.size
        };
    }

    private static DisableManifest Manifest(AuditReport report)
    {
        return new DisableManifest
        {
            Schema = "khufu-v10-interior-disable-manifest-v1",
            BaselineCommit = "a7ba20fd24034a0c5cf115d21d8d955797abe011",
            ScenePath = report.ScenePath,
            SceneSha256 = report.SceneSha256,
            ExpectedRendererTransitions = ExpectedTargetRenderers,
            ExpectedColliderTransitions = ExpectedTargetColliders,
            CrownDependencyCount = report.CrownDependencies.Count,
            CrownIntersectionCount = report.CrownIntersection.Count,
            Transitions = report.Transitions,
            Markers = report.Markers.OrderBy(item => item.Name, StringComparer.Ordinal).ToList()
        };
    }

    private static string Markdown(AuditReport report)
    {
        var text = new StringBuilder("# Khufu V10 Interior Pre-Write Audit\n\n");
        text.AppendLine("- Verdict: **" + (report.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Scene SHA256: `" + report.SceneSha256 + "`");
        text.AppendLine("- Renderer transitions: `" + report.Transitions.Count + "`");
        text.AppendLine("- Collider transitions: `" + report.Transitions.Count(item => item.DisableCollider) + "`");
        text.AppendLine("- Crown dependencies: `" + report.CrownDependencies.Count + "`");
        text.AppendLine("- Crown intersection: `" + report.CrownIntersection.Count + "`");
        text.AppendLine();
        text.AppendLine("## Exact Transitions");
        text.AppendLine();
        foreach (var item in report.Transitions)
            text.AppendLine("- `" + item.Path + "`: renderer=True, collider=" + item.DisableCollider +
                            ", bounds=`" + VectorToken(item.BoundsCenter) + " / " + VectorToken(item.BoundsSize) + "`");
        text.AppendLine();
        text.AppendLine("## Preserved V4 Markers");
        text.AppendLine();
        foreach (var item in report.Markers.OrderBy(item => item.Name, StringComparer.Ordinal))
            text.AppendLine("- `" + item.Path + "`: `" + VectorToken(item.Position) + "`");
        foreach (var failure in report.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V10_PREWRITE_AUDIT: " + (report.Passed ? "passed" : "failed"));
        return text.ToString();
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

    private static string Sha256(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("0.###", CultureInfo.InvariantCulture) + ", " +
               value.y.ToString("0.###", CultureInfo.InvariantCulture) + ", " +
               value.z.ToString("0.###", CultureInfo.InvariantCulture);
    }

    [Serializable]
    private sealed class AuditReport
    {
        public bool Passed;
        public string ScenePath = string.Empty;
        public string SceneSha256 = string.Empty;
        public List<TransitionRecord> Transitions = new List<TransitionRecord>();
        public List<MarkerRecord> Markers = new List<MarkerRecord>();
        public List<string> CrownDependencies = new List<string>();
        public List<string> CrownIntersection = new List<string>();
        public List<string> Failures = new List<string>();
    }

    [Serializable]
    public sealed class DisableManifest
    {
        public string Schema = string.Empty;
        public string BaselineCommit = string.Empty;
        public string ScenePath = string.Empty;
        public string SceneSha256 = string.Empty;
        public int ExpectedRendererTransitions;
        public int ExpectedColliderTransitions;
        public int CrownDependencyCount;
        public int CrownIntersectionCount;
        public List<TransitionRecord> Transitions = new List<TransitionRecord>();
        public List<MarkerRecord> Markers = new List<MarkerRecord>();
    }

    [Serializable]
    public sealed class TransitionRecord
    {
        public string Path = string.Empty;
        public string Name = string.Empty;
        public bool RendererEnabled;
        public bool DisableRenderer;
        public string ColliderType = string.Empty;
        public bool ColliderEnabled;
        public bool ColliderIsTrigger;
        public bool DisableCollider;
        public Vector3 BoundsCenter;
        public Vector3 BoundsSize;
    }

    [Serializable]
    public sealed class MarkerRecord
    {
        public string Name = string.Empty;
        public string Path = string.Empty;
        public Vector3 Position;
    }
}

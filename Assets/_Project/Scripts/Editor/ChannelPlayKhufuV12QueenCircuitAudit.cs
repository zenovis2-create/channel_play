using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV12QueenCircuitAudit
{
    public const string RunRoot = "runs/khufu-v12-queen-circuit";
    public const string JsonPath = RunRoot + "/prewrite-audit.json";
    public const string ReceiptPath = RunRoot + "/prewrite-audit.md";
    public const string QueenGateProxyPath =
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Ownership_Gate";

    private static readonly string[] ThresholdProxyPaths =
    {
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Threshold_West_Post",
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Threshold_East_Post",
        ChannelPlayKhufuV10InteriorBuilder.CollisionRootName +
        "/V10_PROXY_Queen_Branch_Threshold_Queen_Threshold_Lintel"
    };

    private static readonly string[] V4QueenTargets =
    {
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_Floor",
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_East",
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_West",
        "V4_Embedded_Interior_Architecture/V4_Queens_Horizontal_Roof",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Floor",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Back",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_East",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_West",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Roof_East",
        "V4_Embedded_Interior_Architecture/V4_Queens_Chamber/V4_Queens_Roof_West"
    };

    [MenuItem("Channel Play/Khufu V12/Run Read-Only Prewrite Audit")]
    public static void RunMenu()
    {
        var sceneHashBefore = Hash(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath);
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath,
            OpenSceneMode.Single);

        var map = Require(GameObject.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName)?.transform,
            "shared map root");
        var v4 = Require(map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName), "V4 root");
        var v10 = Require(map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName), "V10 root");
        var v11 = Require(map.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.RootName), "V11 root");

        var audit = new AuditDocument
        {
            schema = "khufu-v12-prewrite-audit-v1",
            scene_sha256 = sceneHashBefore,
            v4_queen_target_count = V4QueenTargets.Length,
            v10_queen_gate_spec_count = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs()
                .Count(item => item.Name == "Queen_Ownership_Gate" &&
                               item.Bucket == ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket &&
                               item.Structural && item.Collider),
            v10_queen_gate_proxy_path = QueenGateProxyPath,
            v10_limestone_binding = MeshPath(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10LimestoneRendererPath),
            v10_granite_binding = MeshPath(v10, ChannelPlayKhufuV11RoyalCircuitBuilder.V10GraniteRendererPath),
            v10_queen_gate_proxy_enabled = Require(v10.Find(QueenGateProxyPath), "Queen gate proxy")
                .GetComponent<BoxCollider>().enabled,
            v10_great_step_proxy_enabled = Require(
                    v10.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.V10GreatStepBlockerPath),
                    "Great Step proxy")
                .GetComponent<BoxCollider>().enabled,
            v11_signature = ValidateV11(v11),
            map_metrics = Metrics(ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map))
        };

        foreach (var relativePath in ThresholdProxyPaths)
        {
            var proxy = Require(v10.Find(relativePath), relativePath);
            var colliders = proxy.GetComponents<BoxCollider>();
            audit.threshold_proxies.Add(new ProxyRecord
            {
                path = relativePath,
                active_self = proxy.gameObject.activeSelf,
                active_in_hierarchy = proxy.gameObject.activeInHierarchy,
                collider_count = colliders.Length,
                collider_enabled = colliders.Length == 1 && colliders[0].enabled,
                is_trigger = colliders.Length == 1 && colliders[0].isTrigger
            });
        }

        foreach (var relativePath in V4QueenTargets)
        {
            var target = Require(v4.Find(relativePath), relativePath);
            var renderers = target.GetComponents<Renderer>();
            var colliders = target.GetComponents<BoxCollider>();
            audit.v4_queen_targets.Add(new TransitionRecord
            {
                path = relativePath,
                active_self = target.gameObject.activeSelf,
                active_in_hierarchy = target.gameObject.activeInHierarchy,
                renderer_count = renderers.Length,
                collider_count = colliders.Length,
                renderer_enabled = renderers.Length == 1 && renderers[0].enabled,
                collider_enabled = colliders.Length == 1 && colliders[0].enabled,
                is_trigger = colliders.Length == 1 && colliders[0].isTrigger,
                local_position = target.localPosition,
                local_rotation = target.localRotation,
                local_scale = target.localScale
            });
        }

        var marker = Require(v4.Find("V4_Gameplay_Route/V4_Route_Queens_Chamber"), "Queen marker");
        audit.marker_position = marker.position;
        audit.marker_renderer_enabled = marker.GetComponent<Renderer>().enabled;
        audit.glow_renderer_enabled = Require(
            v4.Find("V4_Gameplay_Route/V4_Glow_Queens"), "Queen glow").GetComponent<Renderer>().enabled;
        audit.inherited_light_enabled = Require(
            v4.Find("V4_Lighting/V4_Light_Queens"), "Queen light").GetComponent<Light>().enabled;

        var sceneHashAfter = Hash(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath);
        audit.scene_unchanged = string.Equals(sceneHashBefore, sceneHashAfter, StringComparison.Ordinal);
        var passed = audit.scene_unchanged &&
                     audit.v4_queen_targets.Count == 10 &&
                     audit.v4_queen_targets.Select(item => item.path)
                         .Distinct(StringComparer.Ordinal).Count() == 10 &&
                     audit.v4_queen_targets.All(item =>
                         item.active_self && item.active_in_hierarchy &&
                         item.renderer_count == 1 && item.collider_count == 1 &&
                         item.renderer_enabled && item.collider_enabled && !item.is_trigger) &&
                     audit.v10_queen_gate_spec_count == 1 &&
                     audit.threshold_proxies.Count == 3 &&
                     audit.threshold_proxies.Select(item => item.path)
                         .Distinct(StringComparer.Ordinal).Count() == 3 &&
                     audit.threshold_proxies.All(item =>
                         item.active_self && item.active_in_hierarchy && item.collider_count == 1 &&
                         item.collider_enabled && !item.is_trigger) &&
                     audit.v10_queen_gate_proxy_enabled &&
                     !audit.v10_great_step_proxy_enabled &&
                     audit.v10_limestone_binding ==
                     ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath &&
                     audit.v10_granite_binding ==
                     ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath &&
                     Vector3.Distance(audit.marker_position, KhufuV10RouteContract.QueensChamber) <= 0.001f &&
                     !audit.marker_renderer_enabled &&
                     !audit.glow_renderer_enabled &&
                     audit.inherited_light_enabled &&
                     audit.map_metrics.renderers == 829 &&
                     audit.map_metrics.colliders == 567 &&
                     audit.v11_signature ==
                     "9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9";

        Directory.CreateDirectory(RunRoot);
        File.WriteAllText(JsonPath, JsonUtility.ToJson(audit, true) + "\n", new UTF8Encoding(false));
        WriteReceipt(audit, sceneHashAfter, passed);
        if (!passed) throw new InvalidOperationException("Khufu V12 prewrite audit failed.");
        Debug.Log("CHANNEL_PLAY_KHUFU_V12_PREWRITE_AUDIT result=passed targets=10 scene_unchanged=true");
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

    private static string ValidateV11(Transform v11)
    {
        if (v11 == null) throw new InvalidOperationException("V11 root missing.");
        var method = typeof(ChannelPlayKhufuV11RoyalCircuitValidator).GetMethod(
            "ValidateScene",
            BindingFlags.NonPublic | BindingFlags.Static);
        var result = method?.Invoke(null, new object[] { false });
        if (result == null) throw new InvalidOperationException("V11 validator result missing.");
        var type = result.GetType();
        var failures = type.GetField("Failures")?.GetValue(result) as System.Collections.ICollection;
        if (failures == null || failures.Count != 0)
            throw new InvalidOperationException("V11 validator did not pass in the baseline context.");
        return Convert.ToString(type.GetField("Signature")?.GetValue(result));
    }

    private static string MeshPath(Transform root, string relativePath)
    {
        var filter = Require(root.Find(relativePath), relativePath).GetComponent<MeshFilter>();
        if (filter == null || filter.sharedMesh == null)
            throw new InvalidOperationException("Mesh binding missing: " + relativePath);
        return AssetDatabase.GetAssetPath(filter.sharedMesh);
    }

    private static Transform Require(Transform target, string label)
    {
        if (target == null) throw new InvalidOperationException("Required audit target missing: " + label);
        return target;
    }

    private static MetricsRecord Metrics(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return new MetricsRecord
        {
            renderers = metrics.Renderers,
            vertices = metrics.Vertices,
            triangles = metrics.Triangles,
            colliders = metrics.Colliders
        };
    }

    private static void WriteReceipt(AuditDocument audit, string sceneHashAfter, bool passed)
    {
        var text = new StringBuilder("# Khufu V12 Read-Only Prewrite Audit\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Scene SHA256 before / after: `" + audit.scene_sha256 + " / " + sceneHashAfter + "`");
        text.AppendLine("- Scene bytes unchanged: `" + audit.scene_unchanged + "`");
        text.AppendLine("- V4 Queen targets: `" + audit.v4_queen_targets.Count + "`");
        text.AppendLine("- V10 Queen gate specs: `" + audit.v10_queen_gate_spec_count + "`");
        text.AppendLine("- Enabled threshold post/lintel proxies: `" +
                        audit.threshold_proxies.Count(item => item.collider_enabled && !item.is_trigger) + "/3`");
        text.AppendLine("- V10 bindings: `" + audit.v10_limestone_binding + " / " + audit.v10_granite_binding + "`");
        text.AppendLine("- Queen / Great Step proxy enabled: `" +
                        audit.v10_queen_gate_proxy_enabled + " / " + audit.v10_great_step_proxy_enabled + "`");
        text.AppendLine("- Marker / glow renderer enabled: `" +
                        audit.marker_renderer_enabled + " / " + audit.glow_renderer_enabled + "`");
        text.AppendLine("- Inherited Queen light enabled: `" + audit.inherited_light_enabled + "`");
        text.AppendLine("- Map metrics: `renderers=" + audit.map_metrics.renderers +
                        "_vertices=" + audit.map_metrics.vertices +
                        "_triangles=" + audit.map_metrics.triangles +
                        "_colliders=" + audit.map_metrics.colliders + "`");
        text.AppendLine("- V11 baseline signature: `" + audit.v11_signature + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V12_PREWRITE_AUDIT: " + (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), new UTF8Encoding(false));
    }

    private static string Hash(string path)
    {
        return ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
    }

    [Serializable]
    private sealed class AuditDocument
    {
        public string schema = string.Empty;
        public string scene_sha256 = string.Empty;
        public bool scene_unchanged;
        public int v4_queen_target_count;
        public List<TransitionRecord> v4_queen_targets = new List<TransitionRecord>();
        public int v10_queen_gate_spec_count;
        public string v10_queen_gate_proxy_path = string.Empty;
        public List<ProxyRecord> threshold_proxies = new List<ProxyRecord>();
        public bool v10_queen_gate_proxy_enabled;
        public bool v10_great_step_proxy_enabled;
        public string v10_limestone_binding = string.Empty;
        public string v10_granite_binding = string.Empty;
        public bool marker_renderer_enabled;
        public Vector3 marker_position;
        public bool glow_renderer_enabled;
        public bool inherited_light_enabled;
        public MetricsRecord map_metrics = new MetricsRecord();
        public string v11_signature = string.Empty;
    }

    [Serializable]
    private sealed class TransitionRecord
    {
        public string path = string.Empty;
        public bool active_self;
        public bool active_in_hierarchy;
        public int renderer_count;
        public int collider_count;
        public bool renderer_enabled;
        public bool collider_enabled;
        public bool is_trigger;
        public Vector3 local_position;
        public Quaternion local_rotation;
        public Vector3 local_scale;
    }

    [Serializable]
    private sealed class ProxyRecord
    {
        public string path = string.Empty;
        public bool active_self;
        public bool active_in_hierarchy;
        public int collider_count;
        public bool collider_enabled;
        public bool is_trigger;
    }

    [Serializable]
    private sealed class MetricsRecord
    {
        public int renderers;
        public int vertices;
        public int triangles;
        public int colliders;
    }
}

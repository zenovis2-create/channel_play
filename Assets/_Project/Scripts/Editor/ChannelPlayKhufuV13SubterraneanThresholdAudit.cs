using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV13SubterraneanThresholdAudit
{
    public const string RunRoot = "runs/khufu-v13-subterranean-threshold";
    public const string JsonPath = RunRoot + "/prewrite-audit.json";
    public const string ReceiptPath = RunRoot + "/prewrite-audit.md";

    private const string CanonicalSceneSha256 =
        "eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c";
    private const string V12StaticSignature =
        "6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd";
    private const string ProjectAssetRoot = "Assets/_Project";
    private const string V4InteriorPrefix = "V4_Embedded_Interior_Architecture/";
    private const float PositionTolerance = 0.0001f;
    private const float RotationToleranceDegrees = 0.001f;

    private static readonly Vector3 V4Branch = new Vector3(-2.5f, 1.2f, -18.3f);
    private static readonly Vector3 V10Branch = new Vector3(-2.5f, 3.8f, -19.2f);
    private static readonly Vector3 SubterraneanApproach = new Vector3(0f, -3.8f, -5.6f);
    private static readonly Vector3 SubterraneanChamber = new Vector3(1f, -3.6f, 1.5f);

    [MenuItem("Channel Play/Khufu V13/Run Read-Only Prewrite Audit")]
    public static void RunMenu()
    {
        var scenePath = ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath;
        var sceneHashBefore = HashFile(scenePath);
        var assetSignatureBefore = AssetTreeSignature(out var assetFileCountBefore);

        EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
        var map = Require(
            GameObject.Find(ChannelPlayKhufuV12QueenCircuitBuilder.MapRootName)?.transform,
            "shared map root");
        var v4 = Require(map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName), "V4 root");
        var v10 = Require(map.Find(ChannelPlayKhufuV10InteriorBuilder.RootName), "V10 root");
        var v12 = Require(map.Find(ChannelPlayKhufuV12QueenCircuitBuilder.RootName), "V12 root");

        var audit = new AuditDocument
        {
            schema = "khufu-v13-prewrite-audit-v1",
            canonical_scene_sha256 = CanonicalSceneSha256,
            scene_sha256 = sceneHashBefore,
            asset_tree_signature_before = assetSignatureBefore,
            asset_file_count_before = assetFileCountBefore,
            v4_subterranean_target_count = TargetSpecs().Count,
            preserved_observation_count = ObservationSpecs().Count,
            v12_root_active_self = v12.gameObject.activeSelf,
            v12_root_active_in_hierarchy = v12.gameObject.activeInHierarchy,
            v12_root_metrics = Metrics(
                ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v12)),
            v12_map_metrics = Metrics(
                ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map))
        };

        foreach (var spec in TargetSpecs())
            audit.v4_subterranean_targets.Add(RecordTarget(v4, spec));
        foreach (var spec in ObservationSpecs())
            audit.preserved_observations.Add(RecordObservation(v4, v10, spec));

        var v12Validation = ValidateV12();
        audit.v12_static_signature = v12Validation.Signature;
        audit.v12_validator_root_metrics = v12Validation.RootMetrics;
        audit.v12_validator_map_metrics = v12Validation.MapMetrics;
        audit.v12_validator_failures.AddRange(v12Validation.Failures);

        // Discard any temporary in-memory context changes made by predecessor validation.
        // This is an open-from-disk operation; this auditor never saves a scene or asset.
        EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);

        var sceneHashAfter = HashFile(scenePath);
        var assetSignatureAfter = AssetTreeSignature(out var assetFileCountAfter);
        audit.scene_sha256_after = sceneHashAfter;
        audit.scene_unchanged =
            string.Equals(sceneHashBefore, sceneHashAfter, StringComparison.Ordinal);
        audit.asset_tree_signature_after = assetSignatureAfter;
        audit.asset_file_count_after = assetFileCountAfter;
        audit.asset_tree_unchanged =
            assetFileCountBefore == assetFileCountAfter &&
            string.Equals(assetSignatureBefore, assetSignatureAfter, StringComparison.Ordinal);
        audit.no_scene_or_asset_writes = audit.scene_unchanged && audit.asset_tree_unchanged;

        var targetPaths = audit.v4_subterranean_targets.Select(item => item.path).ToList();
        var observationPaths = audit.preserved_observations.Select(item => item.path).ToList();
        audit.passed =
            sceneHashBefore == CanonicalSceneSha256 &&
            audit.no_scene_or_asset_writes &&
            audit.v4_subterranean_targets.Count == 13 &&
            targetPaths.Distinct(StringComparer.Ordinal).Count() == 13 &&
            targetPaths.SequenceEqual(
                TargetSpecs().Select(item => item.FullPath),
                StringComparer.Ordinal) &&
            audit.v4_subterranean_targets.All(item =>
                item.component_state_exact && item.transform_exact) &&
            audit.v4_subterranean_targets.Count(item => item.collider_count == 1) == 12 &&
            audit.v4_subterranean_targets.Count(item => item.collider_count == 0) == 1 &&
            audit.preserved_observations.Count == 7 &&
            observationPaths.Distinct(StringComparer.Ordinal).Count() == 7 &&
            observationPaths.SequenceEqual(
                ObservationSpecs().Select(item => item.FullPath),
                StringComparer.Ordinal) &&
            audit.preserved_observations.All(item => item.state_exact && item.transform_exact) &&
            audit.v12_root_active_self &&
            audit.v12_root_active_in_hierarchy &&
            MetricsMatch(audit.v12_root_metrics, 5, 1176, 588, 22) &&
            MetricsMatch(audit.v12_map_metrics, 834, 67070, 48560, 589) &&
            MetricsEqual(audit.v12_root_metrics, audit.v12_validator_root_metrics) &&
            MetricsEqual(audit.v12_map_metrics, audit.v12_validator_map_metrics) &&
            audit.v12_validator_failures.Count == 0 &&
            audit.v12_static_signature == V12StaticSignature;

        Directory.CreateDirectory(RunRoot);
        File.WriteAllText(JsonPath, JsonUtility.ToJson(audit, true) + "\n",
            new UTF8Encoding(false));
        WriteReceipt(audit);
        if (!audit.passed)
            throw new InvalidOperationException("Khufu V13 prewrite audit failed.");
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V13_PREWRITE_AUDIT result=passed targets=13 observations=7 " +
            "scene_unchanged=true assets_unchanged=true");
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

    private static List<TargetSpec> TargetSpecs()
    {
        var specs = new List<TargetSpec>();
        AddPassageSpecs(
            specs,
            "V4_Descending_Bedrock",
            V4Branch,
            SubterraneanApproach,
            2.35f,
            2.3f);
        AddPassageSpecs(
            specs,
            "V4_Subterranean_Level",
            SubterraneanApproach,
            new Vector3(1f, -3.6f, -1.6f),
            2.35f,
            2.3f);

        const string room = V4InteriorPrefix + "V4_Subterranean_Chamber/";
        specs.Add(new TargetSpec(
            room + "V4_Subterranean_Floor",
            new Vector3(1f, -4.15f, 1.5f),
            Quaternion.identity,
            new Vector3(8f, 0.28f, 6.8f),
            1));
        specs.Add(new TargetSpec(
            room + "V4_Subterranean_Back",
            new Vector3(1f, -2.25f, 4.9f),
            Quaternion.identity,
            new Vector3(8f, 3.8f, 0.38f),
            1));
        specs.Add(new TargetSpec(
            room + "V4_Subterranean_West",
            new Vector3(-3f, -2.25f, 1.5f),
            Quaternion.identity,
            new Vector3(0.38f, 3.8f, 6.8f),
            1));
        specs.Add(new TargetSpec(
            room + "V4_Subterranean_East",
            new Vector3(5f, -2.25f, 1.5f),
            Quaternion.identity,
            new Vector3(0.38f, 3.8f, 6.8f),
            1));
        specs.Add(new TargetSpec(
            room + "V4_Subterranean_Unfinished_Pit",
            new Vector3(2.6f, -4.75f, 2.2f),
            Quaternion.identity,
            new Vector3(2.2f, 1f, 2.1f),
            0));
        return specs;
    }

    private static void AddPassageSpecs(
        ICollection<TargetSpec> specs,
        string name,
        Vector3 start,
        Vector3 end,
        float width,
        float height)
    {
        var direction = end - start;
        var length = direction.magnitude;
        var rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        var midpoint = (start + end) * 0.5f;
        var up = rotation * Vector3.up;
        var right = rotation * Vector3.right;
        var prefix = V4InteriorPrefix + name;
        specs.Add(new TargetSpec(
            prefix + "_Floor",
            midpoint,
            rotation,
            new Vector3(width, 0.22f, length),
            1));
        specs.Add(new TargetSpec(
            prefix + "_East",
            midpoint + right * (width * 0.5f + 0.18f) + up * (height * 0.5f),
            rotation,
            new Vector3(0.36f, height, length),
            1));
        specs.Add(new TargetSpec(
            prefix + "_West",
            midpoint - right * (width * 0.5f + 0.18f) + up * (height * 0.5f),
            rotation,
            new Vector3(0.36f, height, length),
            1));
        specs.Add(new TargetSpec(
            prefix + "_Roof",
            midpoint + up * height,
            rotation,
            new Vector3(width + 0.72f, 0.24f, length),
            1));
    }

    private static List<ObservationSpec> ObservationSpecs()
    {
        var identity = Quaternion.identity;
        var markerScale = Vector3.one * 0.34f;
        var specs = new List<ObservationSpec>
        {
            new ObservationSpec(
                "V10",
                "V10_Metadata/V10_Anchor_Ascending_Branch",
                "Runtime_Khufu_V10_Interior_Spine/V10_Metadata/V10_Anchor_Ascending_Branch",
                "anchor",
                "V10",
                V10Branch,
                identity,
                Vector3.one,
                0,
                false,
                0,
                false),
            new ObservationSpec(
                "V4",
                "V4_Gameplay_Route/V4_Route_Branch",
                "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/V4_Route_Branch",
                "marker",
                "V10",
                V4Branch,
                identity,
                markerScale,
                1,
                false,
                0,
                false),
            new ObservationSpec(
                "V4",
                "V4_Gameplay_Route/V4_Route_Subterranean_Approach",
                "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/" +
                "V4_Route_Subterranean_Approach",
                "marker",
                "V10",
                SubterraneanApproach,
                identity,
                markerScale,
                1,
                false,
                0,
                false),
            new ObservationSpec(
                "V4",
                "V4_Gameplay_Route/V4_Route_Subterranean_Chamber",
                "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/" +
                "V4_Route_Subterranean_Chamber",
                "marker",
                "V10",
                SubterraneanChamber,
                identity,
                markerScale,
                1,
                false,
                0,
                false)
        };

        var routeOffset = Vector3.up * 0.22f + Vector3.back * 3f;
        specs.Add(BeamObservation(
            "V4_Gameplay_Route/V4_Glow_Descending",
            "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/V4_Glow_Descending",
            V4Branch + routeOffset,
            SubterraneanApproach + routeOffset));
        specs.Add(BeamObservation(
            "V4_Gameplay_Route/V4_Glow_Subterranean",
            "Runtime_Pyramid_Reference_Matched_V4/V4_Gameplay_Route/V4_Glow_Subterranean",
            SubterraneanApproach + routeOffset,
            SubterraneanChamber + routeOffset));
        specs.Add(new ObservationSpec(
            "V4",
            "V4_Lighting/V4_Light_Subterranean",
            "Runtime_Pyramid_Reference_Matched_V4/V4_Lighting/V4_Light_Subterranean",
            "light",
            "V4-inherited",
            new Vector3(1f, -2.4f, 1.5f),
            identity,
            Vector3.one,
            0,
            false,
            1,
            true));
        return specs;
    }

    private static ObservationSpec BeamObservation(
        string relativePath,
        string fullPath,
        Vector3 start,
        Vector3 end)
    {
        var direction = end - start;
        return new ObservationSpec(
            "V4",
            relativePath,
            fullPath,
            "glow",
            "V10",
            (start + end) * 0.5f,
            Quaternion.LookRotation(direction.normalized, Vector3.up),
            new Vector3(0.14f, 0.14f, direction.magnitude),
            1,
            false,
            0,
            false);
    }

    private static TransitionRecord RecordTarget(Transform v4, TargetSpec spec)
    {
        var target = Require(v4.Find(spec.RelativePath), spec.RelativePath);
        var renderers = target.GetComponents<Renderer>();
        var colliders = target.GetComponents<Collider>();
        var boxColliders = target.GetComponents<BoxCollider>();
        var stateExact =
            target.gameObject.activeSelf &&
            target.gameObject.activeInHierarchy &&
            renderers.Length == 1 &&
            renderers[0].enabled &&
            colliders.Length == spec.ColliderCount &&
            boxColliders.Length == spec.ColliderCount &&
            colliders.All(item => item.enabled && !item.isTrigger);
        return new TransitionRecord
        {
            path = spec.FullPath,
            active_self = target.gameObject.activeSelf,
            active_in_hierarchy = target.gameObject.activeInHierarchy,
            renderer_count = renderers.Length,
            collider_count = colliders.Length,
            box_collider_count = boxColliders.Length,
            renderer_enabled = renderers.Length == 1 && renderers[0].enabled,
            collider_enabled = colliders.Length == 1 && colliders[0].enabled,
            is_trigger = colliders.Length == 1 && colliders[0].isTrigger,
            local_position = target.localPosition,
            local_rotation = target.localRotation,
            local_scale = target.localScale,
            component_state_exact = stateExact,
            transform_exact = TransformMatches(target, spec.Position, spec.Rotation, spec.Scale)
        };
    }

    private static ObservationRecord RecordObservation(
        Transform v4,
        Transform v10,
        ObservationSpec spec)
    {
        var root = spec.Root == "V10" ? v10 : v4;
        var target = Require(root.Find(spec.RelativePath), spec.RelativePath);
        var renderers = target.GetComponents<Renderer>();
        var lights = target.GetComponents<Light>();
        var colliders = target.GetComponents<Collider>();
        var rendererEnabled = renderers.Length == 1 && renderers[0].enabled;
        var lightEnabled = lights.Length == 1 && lights[0].enabled;
        var stateExact =
            target.gameObject.activeSelf &&
            target.gameObject.activeInHierarchy &&
            renderers.Length == spec.RendererCount &&
            rendererEnabled == spec.RendererEnabled &&
            lights.Length == spec.LightCount &&
            lightEnabled == spec.LightEnabled &&
            colliders.Length == 0;
        return new ObservationRecord
        {
            path = spec.FullPath,
            kind = spec.Kind,
            owner = spec.Owner,
            active_self = target.gameObject.activeSelf,
            active_in_hierarchy = target.gameObject.activeInHierarchy,
            renderer_count = renderers.Length,
            renderer_enabled = rendererEnabled,
            light_count = lights.Length,
            light_enabled = lightEnabled,
            collider_count = colliders.Length,
            local_position = target.localPosition,
            local_rotation = target.localRotation,
            local_scale = target.localScale,
            world_position = target.position,
            state_exact = stateExact,
            transform_exact = TransformMatches(
                target,
                spec.Position,
                spec.Rotation,
                spec.Scale)
        };
    }

    private static V12ValidationRecord ValidateV12()
    {
        var method = typeof(ChannelPlayKhufuV12QueenCircuitValidator).GetMethod(
            "ValidateScene",
            BindingFlags.NonPublic | BindingFlags.Static);
        if (method == null)
            throw new InvalidOperationException("V12 private validation entry point is missing.");

        object raw;
        try
        {
            raw = method.Invoke(null, new object[] { false });
        }
        catch (TargetInvocationException exception)
        {
            throw exception.InnerException ?? exception;
        }
        if (raw == null)
            throw new InvalidOperationException("V12 validator result is missing.");

        var type = raw.GetType();
        var result = new V12ValidationRecord
        {
            Signature = Convert.ToString(type.GetField("Signature")?.GetValue(raw)),
            RootMetrics = ReadMetrics(type, raw, "RootMetrics"),
            MapMetrics = ReadMetrics(type, raw, "MapMetrics")
        };
        if (type.GetField("Failures")?.GetValue(raw) is IEnumerable failures)
            foreach (var failure in failures)
                result.Failures.Add(Convert.ToString(failure));
        return result;
    }

    private static MetricsRecord ReadMetrics(Type type, object raw, string fieldName)
    {
        var value = type.GetField(fieldName)?.GetValue(raw);
        if (!(value is ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics))
            throw new InvalidOperationException("V12 validator metrics are missing: " + fieldName);
        return Metrics(metrics);
    }

    private static bool TransformMatches(
        Transform target,
        Vector3 position,
        Quaternion rotation,
        Vector3 scale)
    {
        return Vector3.Distance(target.localPosition, position) <= PositionTolerance &&
               Quaternion.Angle(target.localRotation, rotation) <= RotationToleranceDegrees &&
               Vector3.Distance(target.localScale, scale) <= PositionTolerance;
    }

    private static bool MetricsMatch(
        MetricsRecord metrics,
        int renderers,
        int vertices,
        int triangles,
        int colliders)
    {
        return metrics.renderers == renderers &&
               metrics.vertices == vertices &&
               metrics.triangles == triangles &&
               metrics.colliders == colliders;
    }

    private static bool MetricsEqual(MetricsRecord left, MetricsRecord right)
    {
        return MetricsMatch(
            left,
            right.renderers,
            right.vertices,
            right.triangles,
            right.colliders);
    }

    private static MetricsRecord Metrics(
        ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return new MetricsRecord
        {
            renderers = metrics.Renderers,
            vertices = metrics.Vertices,
            triangles = metrics.Triangles,
            colliders = metrics.Colliders
        };
    }

    private static Transform Require(Transform target, string label)
    {
        if (target == null)
            throw new InvalidOperationException("Required V13 audit target missing: " + label);
        return target;
    }

    private static string AssetTreeSignature(out int fileCount)
    {
        var root = Path.GetFullPath(ProjectAssetRoot);
        var project = Path.GetFullPath(".");
        var lines = Directory.GetFiles(root, "*", SearchOption.AllDirectories)
            .Select(path => new
            {
                Path = path,
                Relative = path.Substring(project.Length)
                    .TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                    .Replace('\\', '/')
            })
            .OrderBy(item => item.Relative, StringComparer.Ordinal)
            .Select(item => item.Relative + "|" + HashFile(item.Path))
            .ToList();
        fileCount = lines.Count;
        return HashText(string.Join("\n", lines));
    }

    private static string HashFile(string path)
    {
        return ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
    }

    private static string HashText(string value)
    {
        using (var sha = SHA256.Create())
            return ToHex(sha.ComputeHash(Encoding.UTF8.GetBytes(value)));
    }

    private static string ToHex(byte[] bytes)
    {
        var builder = new StringBuilder(bytes.Length * 2);
        foreach (var value in bytes)
            builder.Append(value.ToString("x2"));
        return builder.ToString();
    }

    private static void WriteReceipt(AuditDocument audit)
    {
        var text = new StringBuilder("# Khufu V13 Read-Only Prewrite Audit\n\n");
        text.AppendLine("- Verdict: **" + (audit.passed ? "passed" : "failed") + "**");
        text.AppendLine("- Canonical V12 scene SHA256: `" + audit.canonical_scene_sha256 + "`");
        text.AppendLine("- Scene SHA256 before / after: `" + audit.scene_sha256 + " / " +
                        audit.scene_sha256_after + "`");
        text.AppendLine("- Scene bytes unchanged: `" + audit.scene_unchanged + "`");
        text.AppendLine("- Asset tree signature before / after: `" +
                        audit.asset_tree_signature_before + " / " +
                        audit.asset_tree_signature_after + "`");
        text.AppendLine("- Asset file count before / after: `" +
                        audit.asset_file_count_before + " / " +
                        audit.asset_file_count_after + "`");
        text.AppendLine("- Asset tree unchanged: `" + audit.asset_tree_unchanged + "`");
        text.AppendLine("- No scene or asset writes: `" + audit.no_scene_or_asset_writes + "`");
        text.AppendLine("- Exact V4 ownership targets: `" +
                        audit.v4_subterranean_targets.Count(item =>
                            item.component_state_exact && item.transform_exact) + "/13`");
        text.AppendLine("- Exact preserved observations: `" +
                        audit.preserved_observations.Count(item =>
                            item.state_exact && item.transform_exact) + "/7`");
        text.AppendLine("- V12 root metrics: `" + MetricsToken(audit.v12_root_metrics) + "`");
        text.AppendLine("- V12 map metrics: `" + MetricsToken(audit.v12_map_metrics) + "`");
        text.AppendLine("- V12 static signature: `" + audit.v12_static_signature + "`");
        text.AppendLine("- V12 validator failures: `" + audit.v12_validator_failures.Count + "`");
        foreach (var failure in audit.v12_validator_failures)
            text.AppendLine("- V12 failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("KHUFU_V13_PREWRITE_AUDIT: " +
                        (audit.passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), new UTF8Encoding(false));
    }

    private static string MetricsToken(MetricsRecord metrics)
    {
        return "renderers=" + metrics.renderers +
               "_vertices=" + metrics.vertices +
               "_triangles=" + metrics.triangles +
               "_colliders=" + metrics.colliders;
    }

    private sealed class TargetSpec
    {
        public readonly string RelativePath;
        public readonly string FullPath;
        public readonly Vector3 Position;
        public readonly Quaternion Rotation;
        public readonly Vector3 Scale;
        public readonly int ColliderCount;

        public TargetSpec(
            string relativePath,
            Vector3 position,
            Quaternion rotation,
            Vector3 scale,
            int colliderCount)
        {
            RelativePath = relativePath;
            FullPath = ChannelPlayPyramidReferenceMatchedV4Builder.RootName + "/" + relativePath;
            Position = position;
            Rotation = rotation;
            Scale = scale;
            ColliderCount = colliderCount;
        }
    }

    private sealed class ObservationSpec
    {
        public readonly string Root;
        public readonly string RelativePath;
        public readonly string FullPath;
        public readonly string Kind;
        public readonly string Owner;
        public readonly Vector3 Position;
        public readonly Quaternion Rotation;
        public readonly Vector3 Scale;
        public readonly int RendererCount;
        public readonly bool RendererEnabled;
        public readonly int LightCount;
        public readonly bool LightEnabled;

        public ObservationSpec(
            string root,
            string relativePath,
            string fullPath,
            string kind,
            string owner,
            Vector3 position,
            Quaternion rotation,
            Vector3 scale,
            int rendererCount,
            bool rendererEnabled,
            int lightCount,
            bool lightEnabled)
        {
            Root = root;
            RelativePath = relativePath;
            FullPath = fullPath;
            Kind = kind;
            Owner = owner;
            Position = position;
            Rotation = rotation;
            Scale = scale;
            RendererCount = rendererCount;
            RendererEnabled = rendererEnabled;
            LightCount = lightCount;
            LightEnabled = lightEnabled;
        }
    }

    private sealed class V12ValidationRecord
    {
        public readonly List<string> Failures = new List<string>();
        public string Signature = string.Empty;
        public MetricsRecord RootMetrics = new MetricsRecord();
        public MetricsRecord MapMetrics = new MetricsRecord();
    }

    [Serializable]
    private sealed class AuditDocument
    {
        public string schema = string.Empty;
        public bool passed;
        public string canonical_scene_sha256 = string.Empty;
        public string scene_sha256 = string.Empty;
        public string scene_sha256_after = string.Empty;
        public bool scene_unchanged;
        public string asset_tree_signature_before = string.Empty;
        public string asset_tree_signature_after = string.Empty;
        public int asset_file_count_before;
        public int asset_file_count_after;
        public bool asset_tree_unchanged;
        public bool no_scene_or_asset_writes;
        public int v4_subterranean_target_count;
        public List<TransitionRecord> v4_subterranean_targets =
            new List<TransitionRecord>();
        public int preserved_observation_count;
        public List<ObservationRecord> preserved_observations =
            new List<ObservationRecord>();
        public bool v12_root_active_self;
        public bool v12_root_active_in_hierarchy;
        public MetricsRecord v12_root_metrics = new MetricsRecord();
        public MetricsRecord v12_map_metrics = new MetricsRecord();
        public MetricsRecord v12_validator_root_metrics = new MetricsRecord();
        public MetricsRecord v12_validator_map_metrics = new MetricsRecord();
        public string v12_static_signature = string.Empty;
        public List<string> v12_validator_failures = new List<string>();
    }

    [Serializable]
    private sealed class TransitionRecord
    {
        public string path = string.Empty;
        public bool active_self;
        public bool active_in_hierarchy;
        public int renderer_count;
        public int collider_count;
        public int box_collider_count;
        public bool renderer_enabled;
        public bool collider_enabled;
        public bool is_trigger;
        public Vector3 local_position;
        public Quaternion local_rotation;
        public Vector3 local_scale;
        public bool component_state_exact;
        public bool transform_exact;
    }

    [Serializable]
    private sealed class ObservationRecord
    {
        public string path = string.Empty;
        public string kind = string.Empty;
        public string owner = string.Empty;
        public bool active_self;
        public bool active_in_hierarchy;
        public int renderer_count;
        public bool renderer_enabled;
        public int light_count;
        public bool light_enabled;
        public int collider_count;
        public Vector3 local_position;
        public Quaternion local_rotation;
        public Vector3 local_scale;
        public Vector3 world_position;
        public bool state_exact;
        public bool transform_exact;
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

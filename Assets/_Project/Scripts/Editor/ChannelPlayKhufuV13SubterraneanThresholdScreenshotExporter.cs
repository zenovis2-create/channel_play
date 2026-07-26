using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV13SubterraneanThresholdScreenshotExporter
{
    public const string OutputRoot =
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot + "/captures";
    private const int Width = 1600;
    private const int Height = 1000;

    [MenuItem("Channel Play/Khufu V13/Export Subterranean Threshold Screenshots")]
    public static void ExportScreenshots()
    {
        ChannelPlayKhufuV13SubterraneanThresholdValidator.ValidateMenu();
        EditorSceneManager.OpenScene(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath,
            OpenSceneMode.Single);
        var map = GameObject.Find(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.MapRootName)?.transform;
        var root = map == null ? null :
            map.Find(ChannelPlayKhufuV13SubterraneanThresholdBuilder.RootName);
        if (map == null || root == null)
            throw new InvalidOperationException("V13 map/root is missing.");
        Directory.CreateDirectory(OutputRoot);

        GameObject cameraObject = null;
        GameObject keyObject = null;
        GameObject fillObject = null;
        VisibilityScope visibility = null;
        var lightStates = new Dictionary<Light, bool>();
        var ambientMode = RenderSettings.ambientMode;
        var ambientLight = RenderSettings.ambientLight;
        var fog = RenderSettings.fog;
        var player = GameObject.Find("MVP_Player");
        var playerActive = player != null && player.activeSelf;
        try
        {
            cameraObject = new GameObject("KhufuV13_Proof_Camera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.025f, 0.028f, 0.032f, 1f);
            camera.nearClipPlane = 0.035f;
            camera.farClipPlane = 900f;
            camera.allowHDR = false;
            camera.allowMSAA = true;

            foreach (var light in UnityEngine.Object.FindObjectsByType<Light>(
                         FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                lightStates[light] = light.enabled;
                light.enabled = false;
            }
            var inherited = map.Find(
                ChannelPlayPyramidReferenceMatchedV4Builder.RootName +
                "/V4_Lighting/V4_Light_Subterranean")?.GetComponent<Light>();
            if (inherited == null)
                throw new InvalidOperationException(
                    "Inherited V4 subterranean light is missing.");
            inherited.enabled = true;

            RenderSettings.ambientMode =
                UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.31f, 0.29f, 0.27f);
            RenderSettings.fog = false;
            keyObject = Directional("KhufuV13_Proof_Key", 0.95f,
                new Color(0.92f, 0.77f, 0.60f),
                Quaternion.Euler(38f, 122f, 0f));
            fillObject = Directional("KhufuV13_Proof_Fill", 0.38f,
                new Color(0.42f, 0.55f, 0.70f),
                Quaternion.Euler(20f, -48f, 0f));
            if (player != null) player.SetActive(false);
            visibility = new VisibilityScope(map);

            var manifest =
                new StringBuilder("# Khufu V13 Subterranean Threshold Capture Manifest\n\n");
            manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
            manifest.AppendLine("- Resolution: `" + Width + "x" + Height + "`");
            manifest.AppendLine("- Required captures: `6`");
            manifest.AppendLine(
                "- Inherited `V4_Light_Subterranean`: `enabled and disclosed`");
            manifest.AppendLine(
                "- Junction cutaway: `V13 structure complete; V10 route inlay only`");
            manifest.AppendLine("- Scene SHA256: `" +
                                Sha256(
                                    ChannelPlayKhufuV13SubterraneanThresholdBuilder
                                        .ScenePath) + "`");
            manifest.AppendLine("- Static receipt SHA256: `" +
                                Sha256(
                                    ChannelPlayKhufuV13SubterraneanThresholdValidator
                                        .ValidationPath) + "`");
            AppendSourceHash(manifest, "Builder",
                "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdBuilder.cs");
            AppendSourceHash(manifest, "Mesh pipeline",
                "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.cs");
            AppendSourceHash(manifest, "Screenshot exporter",
                "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdScreenshotExporter.cs");
            AppendSourceHash(manifest, "Validator",
                "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdValidator.cs");
            manifest.AppendLine();

            var hashes = new HashSet<string>(StringComparer.Ordinal);
            var views = BuildViews();
            foreach (var view in views)
            {
                visibility.Apply(view.Profile);
                var path = Path.Combine(OutputRoot, view.Name + ".png");
                var stats = Capture(camera, view, path);
                var hash = Sha256(path);
                if (!hashes.Add(hash))
                    throw new InvalidOperationException(
                        "Duplicate V13 capture: " + view.Name);
                AppendView(manifest, view, path, hash, stats);
            }
            if (views.Count != 6)
                throw new InvalidOperationException("V13 capture count drifted.");
            manifest.AppendLine("CAPTURE_INTEGRITY: passed");
            manifest.AppendLine("KHUFU_V13_REQUIRED_CAPTURES: passed");
            File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"),
                manifest.ToString(), new UTF8Encoding(false));
        }
        finally
        {
            visibility?.Restore();
            if (player != null) player.SetActive(playerActive);
            RenderSettings.ambientMode = ambientMode;
            RenderSettings.ambientLight = ambientLight;
            RenderSettings.fog = fog;
            foreach (var item in lightStates)
                if (item.Key != null) item.Key.enabled = item.Value;
            if (fillObject != null)
                UnityEngine.Object.DestroyImmediate(fillObject);
            if (keyObject != null)
                UnityEngine.Object.DestroyImmediate(keyObject);
            if (cameraObject != null)
                UnityEngine.Object.DestroyImmediate(cameraObject);
        }
        AssetDatabase.Refresh();
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V13_CAPTURES result=exported count=6 path=\"" +
            OutputRoot + "\"");
    }

    public static void RunBatch()
    {
        try
        {
            ExportScreenshots();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static List<View> BuildViews()
    {
        var branch = KhufuV13SubterraneanRouteContract.V10BranchAnchor;
        var junction = KhufuV13SubterraneanRouteContract.JunctionEnd;
        var landing = KhufuV13SubterraneanRouteContract.SubterraneanLanding;
        var door = KhufuV13SubterraneanRouteContract.ChamberDoor;
        var chamber = KhufuV13SubterraneanRouteContract.ChamberCenter;
        var pit = KhufuV13SubterraneanRouteContract.PitInspection;
        var descentRotation = Quaternion.LookRotation(
            (landing - junction).normalized, Vector3.up);
        var descentForward = (landing - junction).normalized;
        var descentUp = descentRotation * Vector3.up;
        return new List<View>
        {
            new View("v10_v13_junction",
                Vector3.Lerp(branch, junction, 0.5f) + Vector3.up * 2.0f,
                Vector3.Lerp(branch, junction, 0.5f),
                80f, CaptureProfile.Transition, Vector3.forward),
            new View("descending_long_axis",
                junction + descentForward * 1.0f + descentUp * 1.15f,
                landing - descentForward * 0.5f + descentUp * 1.15f,
                66f, CaptureProfile.V13Only),
            new View("bedrock_landing",
                landing + new Vector3(0f, 1.15f, 2.25f),
                landing + new Vector3(0f, 1.10f, -0.30f),
                70f, CaptureProfile.V13Only),
            new View("chamber_doorway_release",
                door + new Vector3(0f, 1.15f, -2.55f),
                chamber + Vector3.up * 1.15f, 70f, CaptureProfile.V13Only),
            new View("subterranean_chamber_pit",
                chamber + new Vector3(0f, 1.55f, -1.55f),
                pit + Vector3.up * 0.08f, 66f, CaptureProfile.V13Only),
            new View("below_grade_integration",
                chamber + new Vector3(0f, 1.20f, -0.40f),
                landing + Vector3.up * 1.10f,
                74f, CaptureProfile.V13Only)
        };
    }

    private static GameObject Directional(string name, float intensity, Color color,
        Quaternion rotation)
    {
        var target = new GameObject(name);
        var light = target.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = intensity;
        light.color = color;
        light.shadows = LightShadows.None;
        target.transform.rotation = rotation;
        return target;
    }

    private static CaptureStats Capture(Camera camera, View view, string path)
    {
        camera.transform.position = view.Position;
        camera.transform.rotation =
            Quaternion.LookRotation(view.Target - view.Position, view.Up);
        camera.fieldOfView = view.FieldOfView;
        var previous = RenderTexture.active;
        var previousTarget = camera.targetTexture;
        RenderTexture target = null;
        Texture2D image = null;
        try
        {
            target = new RenderTexture(Width, Height, 24,
                RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            camera.targetTexture = target;
            camera.Render();
            RenderTexture.active = target;
            image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0f, 0f, Width, Height), 0, 0);
            image.Apply(false, false);
            var stats = Measure(image);
            File.WriteAllBytes(path, image.EncodeToPNG());
            var length = new FileInfo(path).Length;
            if (length < 60000 || stats.StandardDeviation < 0.025f ||
                stats.Range < 0.16f || stats.Mean > 0.82f ||
                stats.ClippedFraction > 0.24f)
                throw new InvalidOperationException(
                    "V13 capture appears blank/incomplete: " + path +
                    " bytes=" + length + " stats=" + stats);
            return stats;
        }
        finally
        {
            camera.targetTexture = previousTarget;
            RenderTexture.active = previous;
            if (image != null) UnityEngine.Object.DestroyImmediate(image);
            if (target != null)
            {
                if (target.IsCreated()) target.Release();
                UnityEngine.Object.DestroyImmediate(target);
            }
        }
    }

    private static CaptureStats Measure(Texture2D image)
    {
        var pixels = image.GetPixels32();
        var count = 0;
        double sum = 0;
        double squares = 0;
        double edges = 0;
        var clipped = 0;
        var minimum = 1f;
        var maximum = 0f;
        for (var y = 0; y < image.height - 1; y += 8)
        for (var x = 0; x < image.width - 1; x += 8)
        {
            var index = y * image.width + x;
            var value = Luminance(pixels[index]);
            var right = Luminance(pixels[index + 1]);
            var up = Luminance(pixels[index + image.width]);
            minimum = Mathf.Min(minimum, value);
            maximum = Mathf.Max(maximum, value);
            sum += value;
            squares += value * value;
            edges += (Mathf.Abs(value - right) + Mathf.Abs(value - up)) * 0.5f;
            if (value >= 0.97f) clipped++;
            count++;
        }
        var mean = count == 0 ? 0f : (float)(sum / count);
        var variance = count == 0 ? 0f :
            Mathf.Max(0f, (float)(squares / count) - mean * mean);
        return new CaptureStats
        {
            Mean = mean,
            StandardDeviation = Mathf.Sqrt(variance),
            Range = maximum - minimum,
            EdgeDensity = count == 0 ? 0f : (float)(edges / count),
            ClippedFraction = count == 0 ? 0f : (float)clipped / count
        };
    }

    private static void AppendView(StringBuilder manifest, View view, string path,
        string hash, CaptureStats stats)
    {
        manifest.AppendLine("## " + view.Name);
        manifest.AppendLine("- SHA256: `" + hash + "`");
        manifest.AppendLine("- Bytes: `" + new FileInfo(path).Length + "`");
        manifest.AppendLine("- Camera: `" + Format(view.Position) + "` -> `" +
                            Format(view.Target) + "`, fov `" +
                            view.FieldOfView.ToString("0.0",
                                CultureInfo.InvariantCulture) + "`");
        manifest.AppendLine("- Visibility: `" + view.Profile + "`");
        manifest.AppendLine("- Mean/stddev/range/edge/clipped: `" + stats + "`");
        manifest.AppendLine();
    }

    private static void AppendSourceHash(StringBuilder manifest, string label,
        string path)
    {
        if (!File.Exists(path))
            throw new FileNotFoundException("V13 capture source is missing.", path);
        manifest.AppendLine("- " + label + " SHA256: `" + Sha256(path) + "`");
    }

    private static float Luminance(Color32 color)
    {
        return (0.2126f * color.r + 0.7152f * color.g +
                0.0722f * color.b) / 255f;
    }

    private static string Sha256(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return string.Concat(sha.ComputeHash(stream)
                .Select(item => item.ToString("x2")));
    }

    private static string Format(Vector3 value)
    {
        return value.x.ToString("0.000", CultureInfo.InvariantCulture) + "," +
               value.y.ToString("0.000", CultureInfo.InvariantCulture) + "," +
               value.z.ToString("0.000", CultureInfo.InvariantCulture);
    }

    private sealed class View
    {
        public readonly string Name;
        public readonly Vector3 Position;
        public readonly Vector3 Target;
        public readonly float FieldOfView;
        public readonly CaptureProfile Profile;
        public readonly Vector3 Up;

        public View(string name, Vector3 position, Vector3 target,
            float fieldOfView, CaptureProfile profile)
            : this(name, position, target, fieldOfView, profile, Vector3.up)
        {
        }

        public View(string name, Vector3 position, Vector3 target,
            float fieldOfView, CaptureProfile profile, Vector3 up)
        {
            Name = name;
            Position = position;
            Target = target;
            FieldOfView = fieldOfView;
            Profile = profile;
            Up = up;
        }
    }

    private enum CaptureProfile
    {
        V13Only,
        Transition,
        Integration
    }

    private sealed class VisibilityScope
    {
        private readonly Transform map;
        private readonly Dictionary<GameObject, bool> states =
            new Dictionary<GameObject, bool>();

        public VisibilityScope(Transform root)
        {
            map = root;
        }

        public void Apply(CaptureProfile profile)
        {
            Restore();
            foreach (Transform child in map)
            {
                var keep =
                    child.name ==
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.RootName ||
                    child.name ==
                    ChannelPlayPyramidReferenceMatchedV4Builder.RootName ||
                    profile != CaptureProfile.V13Only &&
                    child.name == ChannelPlayKhufuV10InteriorBuilder.RootName ||
                    profile == CaptureProfile.Integration &&
                    (child.name == ChannelPlayKhufuV11RoyalCircuitBuilder.RootName ||
                     child.name == ChannelPlayKhufuV12QueenCircuitBuilder.RootName);
                SetActive(child.gameObject, keep);
            }
            var v4 = map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
            if (v4 == null)
                throw new InvalidOperationException(
                    "V4 root is missing for inherited subterranean light.");
            foreach (Transform child in v4)
            {
                var keep = child.name == "V4_Lighting" ||
                           profile == CaptureProfile.Integration &&
                           (child.name == "V4_Foundation_Bedrock_Cutaway" ||
                            child.name ==
                            "V4_Smooth_Casing_With_Tapered_Cutaway");
                SetActive(child.gameObject, keep);
            }
            if (profile == CaptureProfile.Transition)
            {
                var v10Visuals = map.Find(
                    ChannelPlayKhufuV10InteriorBuilder.RootName +
                    "/V10_Visuals");
                if (v10Visuals == null)
                    throw new InvalidOperationException(
                        "V10 visuals are missing for junction cutaway.");
                foreach (Transform child in v10Visuals)
                    SetActive(child.gameObject,
                        child.name == "V10_Route_Inlay");
            }
        }

        public void Restore()
        {
            foreach (var item in states)
                if (item.Key != null) item.Key.SetActive(item.Value);
        }

        private void SetActive(GameObject target, bool active)
        {
            if (!states.ContainsKey(target)) states[target] = target.activeSelf;
            target.SetActive(active);
        }
    }

    private sealed class CaptureStats
    {
        public float Mean;
        public float StandardDeviation;
        public float Range;
        public float EdgeDensity;
        public float ClippedFraction;

        public override string ToString()
        {
            return Mean.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
                   StandardDeviation.ToString("0.0000",
                       CultureInfo.InvariantCulture) + " / " +
                   Range.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
                   EdgeDensity.ToString("0.0000",
                       CultureInfo.InvariantCulture) + " / " +
                   ClippedFraction.ToString("0.0000",
                       CultureInfo.InvariantCulture);
        }
    }
}

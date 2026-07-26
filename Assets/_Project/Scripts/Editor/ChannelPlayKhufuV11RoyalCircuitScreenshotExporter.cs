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

public static class ChannelPlayKhufuV11RoyalCircuitScreenshotExporter
{
    public const string OutputRoot = ChannelPlayKhufuV11RoyalCircuitBuilder.RunRoot + "/captures";
    private const int Width = 1600;
    private const int Height = 1000;

    [MenuItem("Channel Play/Khufu V11/Export Royal Circuit Screenshots")]
    public static void ExportScreenshots()
    {
        ChannelPlayKhufuV11RoyalCircuitValidator.ValidateMenu();
        EditorSceneManager.OpenScene(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.MapRootName);
        var root = mapObject == null ? null : mapObject.transform.Find(ChannelPlayKhufuV11RoyalCircuitBuilder.RootName);
        if (root == null) throw new InvalidOperationException("Khufu V11 root is missing. Rebuild before capture.");

        Directory.CreateDirectory(OutputRoot);
        GameObject cameraObject = null;
        GameObject keyObject = null;
        GameObject fillObject = null;
        GameObject player = null;
        CaptureVisibilityScope visibility = null;
        var sceneLightStates = new Dictionary<Light, bool>();
        var previousAmbientMode = RenderSettings.ambientMode;
        var previousAmbientLight = RenderSettings.ambientLight;
        var previousFog = RenderSettings.fog;
        var playerWasActive = false;
        var captureCount = 0;

        try
        {
            cameraObject = new GameObject("KhufuV11_Proof_Camera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.065f, 0.075f, 1f);
            camera.nearClipPlane = 0.04f;
            camera.farClipPlane = 900f;
            camera.allowHDR = false;
            camera.allowMSAA = true;

            var sceneLights = UnityEngine.Object.FindObjectsByType<Light>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            sceneLightStates = sceneLights.ToDictionary(light => light, light => light.enabled);
            foreach (var sceneLight in sceneLights) sceneLight.enabled = false;

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.50f, 0.46f, 0.40f);
            RenderSettings.fog = false;

            keyObject = new GameObject("KhufuV11_Proof_Key");
            var key = keyObject.AddComponent<Light>();
            key.type = LightType.Directional;
            key.intensity = 1.1f;
            key.color = new Color(1.0f, 0.86f, 0.69f);
            key.shadows = LightShadows.None;
            keyObject.transform.rotation = Quaternion.Euler(38f, 142f, 0f);

            fillObject = new GameObject("KhufuV11_Proof_Fill");
            var fill = fillObject.AddComponent<Light>();
            fill.type = LightType.Directional;
            fill.intensity = 0.58f;
            fill.color = new Color(0.58f, 0.69f, 0.88f);
            fill.shadows = LightShadows.None;
            fillObject.transform.rotation = Quaternion.Euler(24f, -38f, 0f);

            player = GameObject.Find("MVP_Player");
            playerWasActive = player != null && player.activeSelf;
            if (player != null) player.SetActive(false);
            visibility = new CaptureVisibilityScope(mapObject.transform);

            var views = BuildViews();
            captureCount = views.Count;
            var manifest = new StringBuilder("# Khufu V11 Royal Circuit Capture Manifest\n\n");
            manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
            manifest.AppendLine("- Resolution: `" + Width + "x" + Height + "`");
            manifest.AppendLine("- Scene SHA256: `" + Sha256(ChannelPlayKhufuV11RoyalCircuitBuilder.ScenePath) + "`");
            manifest.AppendLine("- Builder SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitBuilder.cs") + "`");
            manifest.AppendLine("- Pipeline SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitMeshPipeline.cs") + "`");
            manifest.AppendLine("- Validator SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitValidator.cs") + "`");
            manifest.AppendLine("- Exporter SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV11RoyalCircuitScreenshotExporter.cs") + "`");
            manifest.AppendLine();
            var hashes = new HashSet<string>(StringComparer.Ordinal);
            foreach (var view in views)
            {
                visibility.Apply(view.Profile);
                var path = Path.Combine(OutputRoot, view.Name + ".png");
                var stats = Capture(camera, view, path);
                var hash = Sha256(path);
                if (!hashes.Add(hash)) throw new InvalidOperationException("Duplicate V11 capture: " + view.Name);
                AppendView(manifest, view, path, hash, stats);
            }
            manifest.AppendLine("CAPTURE_INTEGRITY: passed");
            manifest.AppendLine("KHUFU_V11_REQUIRED_CAPTURES: passed");
            File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"), manifest.ToString());
        }
        finally
        {
            if (visibility != null) visibility.Restore();
            if (player != null) player.SetActive(playerWasActive);
            RenderSettings.ambientMode = previousAmbientMode;
            RenderSettings.ambientLight = previousAmbientLight;
            RenderSettings.fog = previousFog;
            foreach (var pair in sceneLightStates)
                if (pair.Key != null) pair.Key.enabled = pair.Value;
            if (fillObject != null) UnityEngine.Object.DestroyImmediate(fillObject);
            if (keyObject != null) UnityEngine.Object.DestroyImmediate(keyObject);
            if (cameraObject != null) UnityEngine.Object.DestroyImmediate(cameraObject);
        }

        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V11_CAPTURES result=exported count=" + captureCount +
                  " path=\"" + OutputRoot + "\"");
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
        var forward = ChannelPlay.Gameplay.KhufuV11RoyalRouteContract.Forward;
        var right = ChannelPlay.Gameplay.KhufuV11RoyalRouteContract.Right;
        var greatStepStop = ChannelPlay.Gameplay.KhufuV10RouteContract.GreatStepStop();
        var antechamber = ChannelPlay.Gameplay.KhufuV11RoyalRouteContract.AntechamberCenter;
        var chamber = ChannelPlay.Gameplay.KhufuV11RoyalRouteContract.KingsChamberCenter;
        var sarcophagus = ChannelPlay.Gameplay.KhufuV11RoyalRouteContract.SarcophagusCenter;
        var stack = ChannelPlay.Gameplay.KhufuV11RoyalRouteContract.StackedDisplayCenter();
        var southShaft = chamber + forward * 2.68f - right * 2.15f + Vector3.up * 1.95f;
        return new List<View>
        {
            new View("great_step_open_axis",
                greatStepStop + Vector3.up * 1.08f,
                antechamber + Vector3.up * 1.08f,
                72f, CaptureProfile.Transition),
            new View("antechamber_portcullis_detail",
                antechamber - forward * 1.65f + right * 1.25f + Vector3.up * 1.45f,
                antechamber + forward * 0.48f + Vector3.up * 1.95f,
                62f, CaptureProfile.V11Only),
            new View("kings_chamber_wide",
                chamber + right * 3.25f - forward * 1.85f + Vector3.up * 2.35f,
                chamber - right * 0.75f + Vector3.up * 1.35f, 64f, CaptureProfile.V11Only),
            new View("sarcophagus_and_shaft_boundary",
                chamber + right * 2.6f - forward * 1.3f + Vector3.up * 2.1f,
                southShaft,
                58f, CaptureProfile.V11Only),
            new View("relieving_stack_cutaway",
                stack + right * 10.5f - forward * 5.8f + Vector3.up * 1.9f,
                stack - Vector3.up * 0.15f, 50f, CaptureProfile.V11Only),
            new View("pyramid_royal_circuit_integration",
                new Vector3(6f, 18.5f, -48f),
                chamber + Vector3.up * 3.6f, 46f, CaptureProfile.Integration)
        };
    }

    private static CaptureStats Capture(Camera camera, View view, string path)
    {
        camera.transform.position = view.Position;
        camera.transform.rotation = Quaternion.LookRotation(view.Target - view.Position, Vector3.up);
        camera.fieldOfView = view.FieldOfView;
        camera.orthographic = false;
        var previous = RenderTexture.active;
        var previousTarget = camera.targetTexture;
        RenderTexture renderTexture = null;
        Texture2D image = null;
        try
        {
            renderTexture = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            camera.targetTexture = renderTexture;
            camera.Render();
            RenderTexture.active = renderTexture;
            image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0f, 0f, Width, Height), 0, 0);
            image.Apply(false, false);
            var stats = Measure(image);
            File.WriteAllBytes(path, image.EncodeToPNG());

            var info = new FileInfo(path);
            if (info.Length < 65536 || stats.StandardDeviation < 0.03f || stats.Range < 0.18f ||
                stats.Mean > 0.78f || stats.ClippedFraction > 0.22f)
                throw new InvalidOperationException("V11 capture appears blank or incomplete: " + path +
                    " bytes=" + info.Length +
                    " mean=" + stats.Mean.ToString("0.0000", CultureInfo.InvariantCulture) +
                    " stddev=" + stats.StandardDeviation.ToString("0.0000", CultureInfo.InvariantCulture) +
                    " range=" + stats.Range.ToString("0.0000", CultureInfo.InvariantCulture) +
                    " clipped=" + stats.ClippedFraction.ToString("0.0000", CultureInfo.InvariantCulture));
            return stats;
        }
        finally
        {
            camera.targetTexture = previousTarget;
            RenderTexture.active = previous;
            if (image != null) UnityEngine.Object.DestroyImmediate(image);
            if (renderTexture != null)
            {
                if (renderTexture.IsCreated()) renderTexture.Release();
                UnityEngine.Object.DestroyImmediate(renderTexture);
            }
        }
    }

    private static CaptureStats Measure(Texture2D image)
    {
        var pixels = image.GetPixels32();
        var count = 0;
        double sum = 0d;
        double squareSum = 0d;
        double edgeSum = 0d;
        var clippedCount = 0;
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
            squareSum += value * value;
            edgeSum += (Mathf.Abs(value - right) + Mathf.Abs(value - up)) * 0.5f;
            if (value >= 0.97f) clippedCount++;
            count++;
        }
        var mean = count == 0 ? 0f : (float)(sum / count);
        var variance = count == 0 ? 0f : Mathf.Max(0f, (float)(squareSum / count) - mean * mean);
        return new CaptureStats
        {
            Mean = mean,
            StandardDeviation = Mathf.Sqrt(variance),
            Range = maximum - minimum,
            EdgeDensity = count == 0 ? 0f : (float)(edgeSum / count),
            ClippedFraction = count == 0 ? 0f : (float)clippedCount / count
        };
    }

    private static void AppendView(StringBuilder manifest, View view, string path, string hash, CaptureStats stats)
    {
        manifest.AppendLine("## " + view.Name);
        manifest.AppendLine("- SHA256: `" + hash + "`");
        manifest.AppendLine("- Bytes: `" + new FileInfo(path).Length + "`");
        manifest.AppendLine("- Camera: position `" + Format(view.Position) + "`, target `" + Format(view.Target) +
                            "`, fov `" + view.FieldOfView.ToString("0.0", CultureInfo.InvariantCulture) + "`");
        manifest.AppendLine("- Visibility profile: `" + view.Profile + "`");
        manifest.AppendLine("- Luminance mean/stddev/range/edge/clipped: `" +
                            stats.Mean.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
                            stats.StandardDeviation.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
                            stats.Range.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
                            stats.EdgeDensity.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
                            stats.ClippedFraction.ToString("0.0000", CultureInfo.InvariantCulture) + "`");
        manifest.AppendLine();
    }

    private static float Luminance(Color32 color)
    {
        return (0.2126f * color.r + 0.7152f * color.g + 0.0722f * color.b) / 255f;
    }

    private static string Sha256(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return string.Concat(sha.ComputeHash(stream).Select(item => item.ToString("x2")));
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

        public View(string name, Vector3 position, Vector3 target, float fieldOfView, CaptureProfile profile)
        {
            Name = name;
            Position = position;
            Target = target;
            FieldOfView = fieldOfView;
            Profile = profile;
        }
    }

    private enum CaptureProfile
    {
        V11Only,
        Transition,
        Integration
    }

    private sealed class CaptureVisibilityScope
    {
        private static readonly HashSet<string> IntegrationV4Children = new HashSet<string>(StringComparer.Ordinal)
        {
            "V4_Foundation_Bedrock_Cutaway",
            "V4_Smooth_Casing_With_Tapered_Cutaway"
        };

        private readonly Transform map;
        private readonly Dictionary<GameObject, bool> originalStates = new Dictionary<GameObject, bool>();

        public CaptureVisibilityScope(Transform mapRoot)
        {
            map = mapRoot;
        }

        public void Apply(CaptureProfile profile)
        {
            Restore();
            foreach (Transform child in map)
            {
                var keep = child.name == ChannelPlayKhufuV11RoyalCircuitBuilder.RootName ||
                           (profile == CaptureProfile.Transition || profile == CaptureProfile.Integration) &&
                           child.name == ChannelPlayKhufuV10InteriorBuilder.RootName ||
                           profile == CaptureProfile.Integration &&
                           child.name == ChannelPlayPyramidReferenceMatchedV4Builder.RootName;
                SetActive(child.gameObject, keep);
            }

            if (profile != CaptureProfile.Integration) return;
            var v4 = map.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
            if (v4 == null) throw new InvalidOperationException("V4 pyramid shell is missing for integration capture.");
            foreach (Transform child in v4)
                SetActive(child.gameObject, IntegrationV4Children.Contains(child.name));
        }

        public void Restore()
        {
            foreach (var pair in originalStates)
                if (pair.Key != null) pair.Key.SetActive(pair.Value);
        }

        private void SetActive(GameObject target, bool active)
        {
            if (!originalStates.ContainsKey(target)) originalStates.Add(target, target.activeSelf);
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
    }
}

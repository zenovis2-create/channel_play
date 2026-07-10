using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV6VisualSliceScreenshotExporter
{
    private const string OutputRoot = ChannelPlayKhufuV6VisualFidelityBuilder.RunRoot + "/captures";
    private const string V5CaptureRoot = "runs/khufu-mega-labyrinth-v5/captures";
    private const int Width = 1536;
    private const int Height = 1024;
    private const float MinimumPixelDelta = 0.018f;
    private const float MinimumRoiDelta = 0.020f;

    private static readonly View[] Views =
    {
        new View("hero_valley_to_pyramid", new Vector3(210f, 44f, -118f), new Vector3(20f, 4f, 0f), 34f,
            "hero_valley_to_pyramid.png", new Rect(0.12f, 0.08f, 0.72f, 0.82f), false),
        new View("player_temple_hub", new Vector3(76f, 4.2f, -17f), new Vector3(8f, 7f, 0f), 48f,
            "player_temple_hub.png", new Rect(0.08f, 0.05f, 0.84f, 0.90f), true),
        new View("dense_core", new Vector3(38f, 20f, -50f), new Vector3(0f, 8f, 0f), 44f,
            "dense_core.png", new Rect(0.05f, 0.04f, 0.90f, 0.92f), true),
        new View("temple_hub_detail", new Vector3(82f, 8f, -18f), new Vector3(62f, 3.2f, 0f), 45f,
            null, new Rect(0f, 0f, 1f, 1f), false),
    };

    [MenuItem("Channel Play/Khufu V6/Export Visual Fidelity Screenshots")]
    public static void ExportScreenshots()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath);
        if (GameObject.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName) == null)
            throw new InvalidOperationException("Khufu V6 root is missing. Rebuild the visual slice first.");

        Directory.CreateDirectory(OutputRoot);
        var cameraObject = new GameObject("KhufuV6_Proof_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.Skybox;
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 600f;
        camera.allowHDR = true;
        camera.allowMSAA = true;
        var manifest = new StringBuilder("# Khufu V6 Visual Slice Capture Manifest\n\n");
        manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
        manifest.AppendLine("- Resolution: `" + Width + "x" + Height + "`");
        manifest.AppendLine("- Generated UTC: `" + DateTime.UtcNow.ToString("O") + "`");
        manifest.AppendLine("- Scene SHA256: `" + Sha256(ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath) + "`");
        manifest.AppendLine("- Builder SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs") + "`");
        manifest.AppendLine("- Validator SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs") + "`");
        manifest.AppendLine("- Exporter SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceScreenshotExporter.cs") + "`");
        manifest.AppendLine("- Comparison: fixed V5 camera transforms and fixed render settings; no exposure-only acceptance");
        manifest.AppendLine();
        var hashes = new HashSet<string>(StringComparer.Ordinal);
        var comparedViews = 0;
        var requiredDeltaViews = 0;

        try
        {
            foreach (var view in Views)
            {
                camera.transform.position = view.Position;
                camera.transform.rotation = Quaternion.LookRotation(view.Target - view.Position, Vector3.up);
                camera.fieldOfView = view.FieldOfView;
                camera.orthographic = false;
                var path = Path.Combine(OutputRoot, view.Name + ".png").Replace('\\', '/');
                var capture = Render(camera, path, view);
                var info = new FileInfo(path);
                if (info.Length < 65536) throw new InvalidOperationException("Capture appears blank or incomplete: " + path);
                if (capture.Stats.LuminanceStandardDeviation < 0.045f || capture.Stats.LuminanceRange < 0.20f)
                    throw new InvalidOperationException("Capture lacks visual information: " + path);
                var hash = Sha256(path);
                if (!hashes.Add(hash)) throw new InvalidOperationException("Duplicate capture detected: " + path);

                manifest.AppendLine("## " + view.Name);
                manifest.AppendLine("- SHA256: `" + hash + "`");
                manifest.AppendLine("- Bytes: `" + info.Length + "`");
                manifest.AppendLine("- Camera: position `" + Format(view.Position) + "`, target `" + Format(view.Target) + "`, fov `" + view.FieldOfView.ToString("F1") + "`");
                manifest.AppendLine("- Luminance: mean `" + capture.Stats.LuminanceMean.ToString("F4") + "`, stddev `" + capture.Stats.LuminanceStandardDeviation.ToString("F4") + "`, range `" + capture.Stats.LuminanceRange.ToString("F4") + "`, edge `" + capture.Stats.EdgeDensity.ToString("F4") + "`");
                if (capture.Delta != null)
                {
                    comparedViews++;
                    manifest.AppendLine("- Baseline: `" + view.BaselineName + "`, SHA256 `" + capture.Delta.BaselineSha + "`");
                    manifest.AppendLine("- Mean absolute RGB delta: `" + capture.Delta.Global.ToString("F4") + "` (minimum `" + MinimumPixelDelta.ToString("F3") + "`)");
                    manifest.AppendLine("- Target ROI delta: `" + capture.Delta.Roi.ToString("F4") + "` (minimum `" + MinimumRoiDelta.ToString("F3") + "`)");
                    manifest.AppendLine("- Outside ROI delta: `" + capture.Delta.Outside.ToString("F4") + "`");
                    manifest.AppendLine("- Required delta gate: `" + view.RequireDelta + "`");
                    if (view.RequireDelta) requiredDeltaViews++;
                    if (view.RequireDelta && (capture.Delta.Global < MinimumPixelDelta || capture.Delta.Roi < MinimumRoiDelta))
                        throw new InvalidOperationException("Visual delta below acceptance threshold: " + view.Name);
                    if (view.RequireDelta && capture.Delta.Roi < capture.Delta.Outside * 0.65f)
                        throw new InvalidOperationException("Visual change is not concentrated on the target architecture: " + view.Name);
                }
                manifest.AppendLine();
            }
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(cameraObject);
        }

        if (comparedViews != 3) throw new InvalidOperationException("Expected three same-camera baseline comparisons, found " + comparedViews);
        if (requiredDeltaViews != 2) throw new InvalidOperationException("Expected two required visual-delta gates, found " + requiredDeltaViews);
        manifest.AppendLine("CAPTURE_INTEGRITY: passed");
        manifest.AppendLine("VISUAL_DELTA: passed");
        File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"), manifest.ToString());
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V6_CAPTURES result=exported count=" + Views.Length + " compared=" + comparedViews + " path=\"" + OutputRoot + "\"");
    }

    private static CaptureResult Render(Camera camera, string path, View view)
    {
        var texture = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32);
        texture.antiAliasing = 4;
        var previous = RenderTexture.active;
        camera.targetTexture = texture;
        camera.Render();
        RenderTexture.active = texture;
        var image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0f, 0f, Width, Height), 0, 0);
        image.Apply(false, false);
        var result = new CaptureResult { Stats = Measure(image) };
        if (!string.IsNullOrEmpty(view.BaselineName))
        {
            var baselinePath = Path.Combine(V5CaptureRoot, view.BaselineName).Replace('\\', '/');
            result.Delta = Compare(image, baselinePath, view.Roi);
        }
        File.WriteAllBytes(path, image.EncodeToPNG());
        camera.targetTexture = null;
        RenderTexture.active = previous;
        UnityEngine.Object.DestroyImmediate(image);
        texture.Release();
        UnityEngine.Object.DestroyImmediate(texture);
        return result;
    }

    private static CaptureStats Measure(Texture2D image)
    {
        var pixels = image.GetPixels32();
        var count = 0;
        double sum = 0d;
        double squareSum = 0d;
        double edgeSum = 0d;
        var minimum = 1f;
        var maximum = 0f;
        for (var y = 0; y < image.height - 1; y += 8)
        {
            for (var x = 0; x < image.width - 1; x += 8)
            {
                var index = y * image.width + x;
                var luminance = Luminance(pixels[index]);
                var right = Luminance(pixels[index + 1]);
                var up = Luminance(pixels[index + image.width]);
                minimum = Mathf.Min(minimum, luminance);
                maximum = Mathf.Max(maximum, luminance);
                sum += luminance;
                squareSum += luminance * luminance;
                edgeSum += (Mathf.Abs(luminance - right) + Mathf.Abs(luminance - up)) * 0.5f;
                count++;
            }
        }
        var mean = count == 0 ? 0f : (float)(sum / count);
        var variance = count == 0 ? 0f : Mathf.Max(0f, (float)(squareSum / count) - mean * mean);
        return new CaptureStats
        {
            LuminanceMean = mean,
            LuminanceStandardDeviation = Mathf.Sqrt(variance),
            LuminanceRange = maximum - minimum,
            EdgeDensity = count == 0 ? 0f : (float)(edgeSum / count),
        };
    }

    private static VisualDelta Compare(Texture2D current, string baselinePath, Rect roi)
    {
        if (!File.Exists(baselinePath)) throw new FileNotFoundException("V5 baseline capture missing", baselinePath);
        var baseline = new Texture2D(2, 2, TextureFormat.RGB24, false);
        if (!baseline.LoadImage(File.ReadAllBytes(baselinePath), false))
            throw new InvalidOperationException("Failed to decode baseline capture: " + baselinePath);
        if (baseline.width != current.width || baseline.height != current.height)
            throw new InvalidOperationException("Baseline dimensions do not match: " + baselinePath);

        var currentPixels = current.GetPixels32();
        var baselinePixels = baseline.GetPixels32();
        double global = 0d;
        double roiSum = 0d;
        double outsideSum = 0d;
        var globalCount = 0;
        var roiCount = 0;
        var outsideCount = 0;
        for (var y = 0; y < current.height; y += 4)
        {
            for (var x = 0; x < current.width; x += 4)
            {
                var index = y * current.width + x;
                var delta = ColorDelta(currentPixels[index], baselinePixels[index]);
                global += delta;
                globalCount++;
                var normalized = new Vector2((float)x / current.width, (float)y / current.height);
                if (roi.Contains(normalized))
                {
                    roiSum += delta;
                    roiCount++;
                }
                else
                {
                    outsideSum += delta;
                    outsideCount++;
                }
            }
        }
        UnityEngine.Object.DestroyImmediate(baseline);
        return new VisualDelta
        {
            BaselineSha = Sha256(baselinePath),
            Global = globalCount == 0 ? 0f : (float)(global / globalCount),
            Roi = roiCount == 0 ? 0f : (float)(roiSum / roiCount),
            Outside = outsideCount == 0 ? 0f : (float)(outsideSum / outsideCount),
        };
    }

    private static float ColorDelta(Color32 a, Color32 b)
    {
        return (Mathf.Abs(a.r - b.r) + Mathf.Abs(a.g - b.g) + Mathf.Abs(a.b - b.b)) / (3f * 255f);
    }

    private static float Luminance(Color32 color)
    {
        return (0.2126f * color.r + 0.7152f * color.g + 0.0722f * color.b) / 255f;
    }

    private static string Sha256(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
        {
            var bytes = sha.ComputeHash(stream);
            var builder = new StringBuilder(bytes.Length * 2);
            foreach (var value in bytes) builder.Append(value.ToString("x2"));
            return builder.ToString();
        }
    }

    private static string Format(Vector3 value)
    {
        return value.x.ToString("F2") + ", " + value.y.ToString("F2") + ", " + value.z.ToString("F2");
    }

    private sealed class View
    {
        public readonly string Name;
        public readonly Vector3 Position;
        public readonly Vector3 Target;
        public readonly float FieldOfView;
        public readonly string BaselineName;
        public readonly Rect Roi;
        public readonly bool RequireDelta;

        public View(string name, Vector3 position, Vector3 target, float fieldOfView, string baselineName, Rect roi, bool requireDelta)
        {
            Name = name;
            Position = position;
            Target = target;
            FieldOfView = fieldOfView;
            BaselineName = baselineName;
            Roi = roi;
            RequireDelta = requireDelta;
        }
    }

    private sealed class CaptureResult
    {
        public CaptureStats Stats;
        public VisualDelta Delta;
    }

    private sealed class VisualDelta
    {
        public string BaselineSha;
        public float Global;
        public float Roi;
        public float Outside;
    }

    private struct CaptureStats
    {
        public float LuminanceMean;
        public float LuminanceStandardDeviation;
        public float LuminanceRange;
        public float EdgeDensity;
    }
}

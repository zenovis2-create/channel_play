using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV8TempleProductionArtScreenshotExporter
{
    public const string OutputRoot = ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot + "/captures";
    private const int Width = 1536;
    private const int Height = 1024;

    private static readonly View[] Views =
    {
        new View("causeway_arrival", new Vector3(92f, 6f, -12f), new Vector3(58f, 2.2f, 0f), 48f),
        new View("court_wide", new Vector3(70f, 11f, -27f), new Vector3(56f, 2.2f, 0f), 48f),
        new View("court_to_pyramid", new Vector3(61f, 5.4f, 18f), new Vector3(8f, 8f, 0f), 46f),
        new View("temple_plan_oblique", new Vector3(84f, 35f, -31f), new Vector3(56f, 1.5f, 0f), 42f)
    };

    [MenuItem("Channel Play/Khufu V8/Export Temple Production Art Screenshots")]
    public static void ExportScreenshots()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath);
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        var root = map == null ? null : map.transform.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.RootName);
        if (root == null) throw new InvalidOperationException("Khufu V8 root is missing. Rebuild before capture.");

        Directory.CreateDirectory(OutputRoot);
        var cameraObject = new GameObject("KhufuV8_Proof_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.Skybox;
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 700f;
        camera.allowHDR = true;
        camera.allowMSAA = true;
        var manifest = new StringBuilder("# Khufu V8 Temple Production Art Capture Manifest\n\n");
        manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
        manifest.AppendLine("- Resolution: `" + Width + "x" + Height + "`");
        manifest.AppendLine("- Scene SHA256: `" + Sha256(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath) + "`");
        manifest.AppendLine("- Builder SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtBuilder.cs") + "`");
        manifest.AppendLine("- Validator SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs") + "`");
        manifest.AppendLine();
        var hashes = new HashSet<string>(StringComparer.Ordinal);

        try
        {
            foreach (var view in Views)
            {
                var stats = Capture(camera, view, Path.Combine(OutputRoot, view.Name + ".png"));
                var path = Path.Combine(OutputRoot, view.Name + ".png");
                var hash = Sha256(path);
                if (!hashes.Add(hash)) throw new InvalidOperationException("Duplicate V8 capture: " + view.Name);
                AppendView(manifest, view.Name, view, path, hash, stats, "normal");
            }

            var changed = SetGrayboxEnabled(map.transform, true);
            if (changed != ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedV5HubRenderers +
                           ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedV6HubRenderers)
                throw new InvalidOperationException("Graybox mutation renderer count drifted: " + changed);
            var mutationView = Views[0];
            var mutationPath = Path.Combine(OutputRoot, "mutation_graybox_overlap.png");
            var mutationStats = Capture(camera, mutationView, mutationPath);
            var mutationHash = Sha256(mutationPath);
            SetGrayboxEnabled(map.transform, false);
            if (mutationHash == Sha256(Path.Combine(OutputRoot, mutationView.Name + ".png")))
                throw new InvalidOperationException("Graybox mutation capture is identical to normal evidence.");
            AppendView(manifest, "mutation_graybox_overlap", mutationView, mutationPath, mutationHash, mutationStats, "negative-control");
        }
        finally
        {
            SetGrayboxEnabled(map.transform, false);
            UnityEngine.Object.DestroyImmediate(cameraObject);
        }

        manifest.AppendLine("CAPTURE_INTEGRITY: passed");
        manifest.AppendLine("GRAYBOX_MUTATION_CAPTURE: passed");
        File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"), manifest.ToString());
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_CAPTURES result=exported normal=" + Views.Length + " mutation=1 path=\"" + OutputRoot + "\"");
    }

    private static CaptureStats Capture(Camera camera, View view, string path)
    {
        camera.transform.position = view.Position;
        camera.transform.rotation = Quaternion.LookRotation(view.Target - view.Position, Vector3.up);
        camera.fieldOfView = view.FieldOfView;
        camera.orthographic = false;
        var renderTexture = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
        var previous = RenderTexture.active;
        camera.targetTexture = renderTexture;
        camera.Render();
        RenderTexture.active = renderTexture;
        var image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0f, 0f, Width, Height), 0, 0);
        image.Apply(false, false);
        var stats = Measure(image);
        File.WriteAllBytes(path, image.EncodeToPNG());
        camera.targetTexture = null;
        RenderTexture.active = previous;
        UnityEngine.Object.DestroyImmediate(image);
        renderTexture.Release();
        UnityEngine.Object.DestroyImmediate(renderTexture);
        var info = new FileInfo(path);
        if (info.Length < 65536 || stats.StandardDeviation < 0.035f || stats.Range < 0.20f)
            throw new InvalidOperationException("V8 capture appears blank or incomplete: " + path);
        return stats;
    }

    private static int SetGrayboxEnabled(Transform map, bool enabled)
    {
        var v5 = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_District_Pyramid_Temple_Hub");
        var v6 = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName + "/V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
        if (v5 == null || v6 == null) return 0;
        var renderers = v5.GetComponentsInChildren<Renderer>(true).Concat(v6.GetComponentsInChildren<Renderer>(true)).ToArray();
        foreach (var renderer in renderers) renderer.enabled = enabled;
        return renderers.Length;
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
            count++;
        }
        var mean = count == 0 ? 0f : (float)(sum / count);
        var variance = count == 0 ? 0f : Mathf.Max(0f, (float)(squareSum / count) - mean * mean);
        return new CaptureStats
        {
            Mean = mean,
            StandardDeviation = Mathf.Sqrt(variance),
            Range = maximum - minimum,
            EdgeDensity = count == 0 ? 0f : (float)(edgeSum / count)
        };
    }

    private static void AppendView(StringBuilder manifest, string name, View view, string path, string hash,
        CaptureStats stats, string state)
    {
        manifest.AppendLine("## " + name);
        manifest.AppendLine("- State: `" + state + "`");
        manifest.AppendLine("- SHA256: `" + hash + "`");
        manifest.AppendLine("- Bytes: `" + new FileInfo(path).Length + "`");
        manifest.AppendLine("- Camera: position `" + Format(view.Position) + "`, target `" + Format(view.Target) + "`, fov `" + view.FieldOfView.ToString("0.0") + "`");
        manifest.AppendLine("- Luminance mean/stddev/range/edge: `" + stats.Mean.ToString("0.0000") + " / " +
                            stats.StandardDeviation.ToString("0.0000") + " / " + stats.Range.ToString("0.0000") + " / " +
                            stats.EdgeDensity.ToString("0.0000") + "`");
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
        {
            return string.Concat(sha.ComputeHash(stream).Select(item => item.ToString("x2")));
        }
    }

    private static string Format(Vector3 value)
    {
        return value.x.ToString("0.00") + ", " + value.y.ToString("0.00") + ", " + value.z.ToString("0.00");
    }

    private sealed class View
    {
        public readonly string Name;
        public readonly Vector3 Position;
        public readonly Vector3 Target;
        public readonly float FieldOfView;

        public View(string name, Vector3 position, Vector3 target, float fieldOfView)
        {
            Name = name;
            Position = position;
            Target = target;
            FieldOfView = fieldOfView;
        }
    }

    private sealed class CaptureStats
    {
        public float Mean;
        public float StandardDeviation;
        public float Range;
        public float EdgeDensity;
    }
}

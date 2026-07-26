using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV9CausewayScreenshotExporter
{
    public const string OutputRoot = ChannelPlayKhufuV9CausewayFidelityBuilder.RunRoot + "/captures";
    private const int Width = 1600;
    private const int Height = 1000;

    private static readonly View[] Views =
    {
        new View("valley_gate_procession", new Vector3(166f, 8f, -15f), new Vector3(143f, 2.2f, 0f), 47f),
        new View("causeway_long_axis", new Vector3(137f, 11f, -20f), new Vector3(100f, 2.8f, 0f), 48f),
        new View("covered_causeway_rhythm", new Vector3(116f, 7.5f, -14f), new Vector3(91f, 2.8f, 0f), 46f),
        new View("hub_open_fanout", new Vector3(82f, 10f, -19f), new Vector3(62f, 2.3f, 0f), 47f),
        new View("processional_oblique", new Vector3(143f, 38f, -43f), new Vector3(103f, 2.5f, 0f), 43f)
    };

    [MenuItem("Channel Play/Khufu V9/Export Causeway Screenshots")]
    public static void ExportScreenshots()
    {
        ChannelPlayKhufuV9CausewayFidelityValidator.ValidateMenu();
        EditorSceneManager.OpenScene(ChannelPlayKhufuV9CausewayFidelityBuilder.ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.MapRootName);
        var root = mapObject == null ? null : mapObject.transform.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.RootName);
        if (root == null) throw new InvalidOperationException("Khufu V9 root is missing. Rebuild before capture.");

        Directory.CreateDirectory(OutputRoot);
        var cameraObject = new GameObject("KhufuV9_Proof_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.Skybox;
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 800f;
        camera.allowHDR = true;
        camera.allowMSAA = true;
        var manifest = new StringBuilder("# Khufu V9 Causeway Capture Manifest\n\n");
        manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
        manifest.AppendLine("- Resolution: `" + Width + "x" + Height + "`");
        manifest.AppendLine("- Scene SHA256: `" + Sha256(ChannelPlayKhufuV9CausewayFidelityBuilder.ScenePath) + "`");
        manifest.AppendLine("- Builder SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityBuilder.cs") + "`");
        manifest.AppendLine("- Pipeline SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayMeshPipeline.cs") + "`");
        manifest.AppendLine("- Validator SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV9CausewayFidelityValidator.cs") + "`");
        manifest.AppendLine();
        var hashes = new HashSet<string>(StringComparer.Ordinal);

        try
        {
            foreach (var view in Views)
            {
                var path = Path.Combine(OutputRoot, view.Name + ".png");
                var stats = Capture(camera, view, path);
                var hash = Sha256(path);
                if (!hashes.Add(hash)) throw new InvalidOperationException("Duplicate V9 capture: " + view.Name);
                AppendView(manifest, view.Name, view, path, hash, stats, "normal");
            }

            var changed = SetSupersededEnabled(mapObject.transform, true);
            if (changed != ChannelPlayKhufuV9CausewayFidelityBuilder.ExpectedSupersededRenderers)
                throw new InvalidOperationException("V9 graybox mutation renderer count drifted: " + changed);
            var mutationView = Views[1];
            var mutationPath = Path.Combine(OutputRoot, "mutation_superseded_overlap.png");
            var mutationStats = Capture(camera, mutationView, mutationPath);
            var mutationHash = Sha256(mutationPath);
            SetSupersededEnabled(mapObject.transform, false);
            if (mutationHash == Sha256(Path.Combine(OutputRoot, mutationView.Name + ".png")))
                throw new InvalidOperationException("V9 mutation capture is identical to normal evidence.");
            AppendView(manifest, "mutation_superseded_overlap", mutationView, mutationPath, mutationHash, mutationStats, "negative-control");
        }
        finally
        {
            SetSupersededEnabled(mapObject.transform, false);
            UnityEngine.Object.DestroyImmediate(cameraObject);
        }

        manifest.AppendLine("CAPTURE_INTEGRITY: passed");
        manifest.AppendLine("V9_GRAYBOX_MUTATION_CAPTURE: passed");
        File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"), manifest.ToString());
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V9_CAPTURES result=exported normal=" + Views.Length + " mutation=1 path=\"" + OutputRoot + "\"");
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
            throw new InvalidOperationException("V9 capture appears blank or incomplete: " + path);
        return stats;
    }

    private static int SetSupersededEnabled(Transform map, bool enabled)
    {
        var renderers = ChannelPlayKhufuV9CausewayFidelityBuilder.CollectSupersededRenderers(map);
        foreach (var renderer in renderers) renderer.enabled = enabled;
        return renderers.Count;
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
            return string.Concat(sha.ComputeHash(stream).Select(item => item.ToString("x2")));
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

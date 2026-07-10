using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuMegaLabyrinthV5ScreenshotExporter
{
    private const string OutputRoot = "runs/khufu-mega-labyrinth-v5/captures";

    private static readonly View[] Views =
    {
        new View("hero_valley_to_pyramid", new Vector3(210f, 44f, -118f), new Vector3(20f, 4f, 0f), 34f),
        new View("player_temple_hub", new Vector3(76f, 4.2f, -17f), new Vector3(8f, 7f, 0f), 48f),
        new View("operator_full_map", new Vector3(220f, 158f, -170f), new Vector3(20f, -3f, 0f), 42f),
        new View("top_down_route_graph", new Vector3(25f, 190f, 0f), new Vector3(25f, 0f, 0f), 50f, true, 105f),
        new View("side_elevation", new Vector3(25f, 38f, 230f), new Vector3(20f, 0f, 0f), 35f),
        new View("dense_core", new Vector3(38f, 20f, -50f), new Vector3(0f, 8f, 0f), 44f),
        new View("underworld_loops", new Vector3(-135f, 70f, 120f), new Vector3(-45f, -20f, 5f), 46f, true, 65f, ViewFilter.UnderworldCutaway),
        new View("truth_boundary", new Vector3(0f, 6.5f, -84f), new Vector3(0f, 2.8f, -62f), 42f, false, 0f, ViewFilter.TruthBoundary),
    };

    [MenuItem("Channel Play/Khufu V5/Export Screenshots")]
    public static void ExportScreenshots()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath);
        if (GameObject.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName) == null)
            throw new InvalidOperationException("Khufu V5 root is missing. Rebuild first.");

        Directory.CreateDirectory(OutputRoot);
        var cameraObject = new GameObject("KhufuV5_Proof_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.Skybox;
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 600f;
        camera.allowHDR = true;
        var manifest = new StringBuilder("# Khufu V5 Capture Manifest\n\n");
        manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
        manifest.AppendLine("- Resolution: `1536x1024`");
        manifest.AppendLine("- Generated UTC: `" + DateTime.UtcNow.ToString("O") + "`");
        manifest.AppendLine("- Git HEAD: `" + GitHead() + "`");
        manifest.AppendLine("- Scene SHA256: `" + Sha256(ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath) + "`");
        manifest.AppendLine("- Builder SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs") + "`");
        manifest.AppendLine("- Exporter SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5ScreenshotExporter.cs") + "`");
        manifest.AppendLine();
        var hashes = new HashSet<string>(StringComparer.Ordinal);

        try
        {
            foreach (var view in Views)
            {
                camera.transform.position = view.Position;
                camera.transform.rotation = Quaternion.LookRotation(view.Target - view.Position, Vector3.up);
                camera.clearFlags = view.Filter == ViewFilter.UnderworldCutaway ? CameraClearFlags.SolidColor : CameraClearFlags.Skybox;
                camera.backgroundColor = view.Filter == ViewFilter.UnderworldCutaway ? new Color(0.012f, 0.016f, 0.02f) : Color.gray;
                camera.fieldOfView = view.FieldOfView;
                camera.orthographic = view.Orthographic;
                camera.orthographicSize = view.OrthographicSize;
                var path = Path.Combine(OutputRoot, view.Name + ".png").Replace('\\', '/');
                var hidden = FilterRenderers(view.Filter);
                CaptureStats stats;
                try { stats = Render(camera, path); }
                finally { RestoreRenderers(hidden); }
                var info = new FileInfo(path);
                if (info.Length < 16384) throw new InvalidOperationException("Capture appears blank or incomplete: " + path);
                if (stats.LuminanceStandardDeviation < 0.045f || stats.LuminanceRange < 0.20f)
                    throw new InvalidOperationException("Capture lacks visual information: " + path);
                var hash = Sha256(path);
                if (!hashes.Add(hash)) throw new InvalidOperationException("Duplicate capture detected: " + path);
                manifest.AppendLine("## " + view.Name);
                manifest.AppendLine("- SHA256: `" + hash + "`");
                manifest.AppendLine("- Bytes: `" + info.Length + "`");
                manifest.AppendLine("- Camera: position `" + Format(view.Position) + "`, target `" + Format(view.Target) + "`");
                manifest.AppendLine("- Projection: `" + (view.Orthographic ? "orthographic size=" + view.OrthographicSize.ToString("F1") : "perspective fov=" + view.FieldOfView.ToString("F1")) + "`");
                manifest.AppendLine("- Luminance: mean `" + stats.LuminanceMean.ToString("F4") + "`, stddev `" + stats.LuminanceStandardDeviation.ToString("F4") + "`, range `" + stats.LuminanceRange.ToString("F4") + "`");
                manifest.AppendLine();
            }
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(cameraObject);
        }

        manifest.AppendLine("CAPTURE_INTEGRITY: passed");
        File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"), manifest.ToString());
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V5_CAPTURES result=exported count=" + Views.Length + " path=\"" + OutputRoot + "\"");
    }

    private static List<RendererState> FilterRenderers(ViewFilter filter)
    {
        if (filter == ViewFilter.None) return null;
        return filter == ViewFilter.UnderworldCutaway ? HideSurfaceRenderers() : HideUnrelatedTruthRenderers();
    }

    private static List<RendererState> HideSurfaceRenderers()
    {
        var states = new List<RendererState>();
        var v4 = GameObject.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName)?.transform;
        var v5 = GameObject.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName)?.transform;
        var bedrock = v5 == null ? null : v5.Find("V5_Underworld_Bedrock_Mass");
        foreach (var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
        {
            var belongsToV4 = v4 != null && renderer.transform.IsChildOf(v4);
            var belongsToBedrock = bedrock != null && renderer.transform.IsChildOf(bedrock);
            if (!belongsToV4 && !belongsToBedrock && renderer.bounds.max.y <= -5f) continue;
            states.Add(new RendererState(renderer, renderer.enabled));
            renderer.enabled = false;
        }
        return states;
    }

    private static List<RendererState> HideUnrelatedTruthRenderers()
    {
        var states = new List<RendererState>();
        var root = GameObject.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName)?.transform;
        var truth = root == null ? null : root.Find("V5_Truth_Boundary_FACT_TO_FICTION");
        if (root == null || truth == null) throw new InvalidOperationException("Truth boundary hierarchy is missing.");
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            if (renderer.transform.IsChildOf(truth)) continue;
            states.Add(new RendererState(renderer, renderer.enabled));
            renderer.enabled = false;
        }
        return states;
    }

    private static void RestoreRenderers(List<RendererState> states)
    {
        if (states == null) return;
        foreach (var state in states) if (state.Renderer != null) state.Renderer.enabled = state.Enabled;
    }

    private static CaptureStats Render(Camera camera, string path)
    {
        var texture = new RenderTexture(1536, 1024, 24, RenderTextureFormat.ARGB32);
        texture.antiAliasing = 4;
        var previous = RenderTexture.active;
        camera.targetTexture = texture;
        camera.Render();
        RenderTexture.active = texture;
        var image = new Texture2D(1536, 1024, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0f, 0f, 1536f, 1024f), 0, 0);
        image.Apply();
        var stats = Measure(image);
        File.WriteAllBytes(path, image.EncodeToPNG());
        camera.targetTexture = null;
        RenderTexture.active = previous;
        UnityEngine.Object.DestroyImmediate(image);
        texture.Release();
        UnityEngine.Object.DestroyImmediate(texture);
        return stats;
    }

    private static CaptureStats Measure(Texture2D image)
    {
        var pixels = image.GetPixels32();
        var count = 0;
        double sum = 0d;
        double squareSum = 0d;
        var minimum = 1f;
        var maximum = 0f;
        for (var i = 0; i < pixels.Length; i += 64)
        {
            var pixel = pixels[i];
            var luminance = (0.2126f * pixel.r + 0.7152f * pixel.g + 0.0722f * pixel.b) / 255f;
            minimum = Mathf.Min(minimum, luminance);
            maximum = Mathf.Max(maximum, luminance);
            sum += luminance;
            squareSum += luminance * luminance;
            count++;
        }
        var mean = (float)(sum / count);
        var variance = Math.Max(0d, squareSum / count - mean * mean);
        return new CaptureStats(mean, (float)Math.Sqrt(variance), maximum - minimum);
    }

    private static string Sha256(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var algorithm = SHA256.Create())
        {
            return BitConverter.ToString(algorithm.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
        }
    }

    private static string GitHead()
    {
        var headPath = Path.Combine(".git", "HEAD");
        if (!File.Exists(headPath)) return "unavailable";
        var head = File.ReadAllText(headPath).Trim();
        if (!head.StartsWith("ref: ", StringComparison.Ordinal)) return head;
        var reference = head.Substring(5).Trim().Replace('/', Path.DirectorySeparatorChar);
        var referencePath = Path.Combine(".git", reference);
        if (File.Exists(referencePath)) return File.ReadAllText(referencePath).Trim();
        var packedRefs = Path.Combine(".git", "packed-refs");
        if (!File.Exists(packedRefs)) return "unresolved:" + reference.Replace(Path.DirectorySeparatorChar, '/');
        foreach (var line in File.ReadAllLines(packedRefs))
        {
            if (line.StartsWith("#", StringComparison.Ordinal) || line.StartsWith("^", StringComparison.Ordinal)) continue;
            var parts = line.Split(' ');
            if (parts.Length == 2 && parts[1] == reference.Replace(Path.DirectorySeparatorChar, '/')) return parts[0];
        }
        return "unresolved:" + reference.Replace(Path.DirectorySeparatorChar, '/');
    }

    private static string Format(Vector3 value)
    {
        return value.x.ToString("F2") + "," + value.y.ToString("F2") + "," + value.z.ToString("F2");
    }

    private sealed class View
    {
        public readonly string Name;
        public readonly Vector3 Position;
        public readonly Vector3 Target;
        public readonly float FieldOfView;
        public readonly bool Orthographic;
        public readonly float OrthographicSize;
        public readonly ViewFilter Filter;
        public View(string name, Vector3 position, Vector3 target, float fieldOfView, bool orthographic = false, float orthographicSize = 0f, ViewFilter filter = ViewFilter.None)
        { Name = name; Position = position; Target = target; FieldOfView = fieldOfView; Orthographic = orthographic; OrthographicSize = orthographicSize; Filter = filter; }
    }

    private enum ViewFilter { None, UnderworldCutaway, TruthBoundary }

    private readonly struct CaptureStats
    {
        public readonly float LuminanceMean;
        public readonly float LuminanceStandardDeviation;
        public readonly float LuminanceRange;
        public CaptureStats(float mean, float standardDeviation, float range)
        { LuminanceMean = mean; LuminanceStandardDeviation = standardDeviation; LuminanceRange = range; }
    }

    private sealed class RendererState
    {
        public readonly Renderer Renderer;
        public readonly bool Enabled;
        public RendererState(Renderer renderer, bool enabled) { Renderer = renderer; Enabled = enabled; }
    }
}

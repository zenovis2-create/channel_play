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

public static class ChannelPlayKhufuV10InteriorScreenshotExporter
{
    public const string OutputRoot = ChannelPlayKhufuV10InteriorBuilder.RunRoot + "/captures";
    private const int Width = 1600;
    private const int Height = 1000;

    [MenuItem("Channel Play/Khufu V10/Export Interior Screenshots")]
    public static void ExportScreenshots()
    {
        ChannelPlayKhufuV10InteriorValidator.ValidateMenu();
        EditorSceneManager.OpenScene(ChannelPlayKhufuV10InteriorBuilder.ScenePath, OpenSceneMode.Single);
        var mapObject = GameObject.Find(ChannelPlayKhufuV10InteriorBuilder.MapRootName);
        var root = mapObject == null ? null : mapObject.transform.Find(ChannelPlayKhufuV10InteriorBuilder.RootName);
        if (root == null) throw new InvalidOperationException("Khufu V10 root is missing. Rebuild before capture.");

        Directory.CreateDirectory(OutputRoot);
        var cameraObject = new GameObject("KhufuV10_Proof_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.12f, 0.14f, 0.16f, 1f);
        camera.nearClipPlane = 0.05f;
        camera.farClipPlane = 900f;
        camera.allowHDR = false;
        camera.allowMSAA = true;

        var sceneLights = UnityEngine.Object.FindObjectsByType<Light>(
            FindObjectsInactive.Include, FindObjectsSortMode.None);
        var sceneLightStates = sceneLights.ToDictionary(light => light, light => light.enabled);
        foreach (var sceneLight in sceneLights) sceneLight.enabled = false;

        var previousAmbientMode = RenderSettings.ambientMode;
        var previousAmbientLight = RenderSettings.ambientLight;
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.38f, 0.36f, 0.33f);

        var keyObject = new GameObject("KhufuV10_Proof_Key");
        var key = keyObject.AddComponent<Light>();
        key.type = LightType.Directional;
        key.intensity = 0.65f;
        key.color = new Color(0.78f, 0.86f, 0.94f);
        key.shadows = LightShadows.None;
        keyObject.transform.rotation = Quaternion.Euler(25f, 154f, 0f);

        var player = GameObject.Find("MVP_Player");
        var playerWasActive = player != null && player.activeSelf;
        if (player != null) player.SetActive(false);

        var views = BuildViews();
        var manifest = new StringBuilder("# Khufu V10 Interior Capture Manifest\n\n");
        manifest.AppendLine("- Unity: `" + Application.unityVersion + "`");
        manifest.AppendLine("- Resolution: `" + Width + "x" + Height + "`");
        manifest.AppendLine("- Scene SHA256: `" + Sha256(ChannelPlayKhufuV10InteriorBuilder.ScenePath) + "`");
        manifest.AppendLine("- Builder SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorBuilder.cs") + "`");
        manifest.AppendLine("- Pipeline SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorMeshPipeline.cs") + "`");
        manifest.AppendLine("- Validator SHA256: `" + Sha256("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs") + "`");
        manifest.AppendLine();
        var hashes = new HashSet<string>(StringComparer.Ordinal);

        try
        {
            foreach (var view in views)
            {
                if (view.Name == "gallery_foot_queen_boundary")
                    ExportQueenOccluderDiagnostic(camera, root, view);
                var path = Path.Combine(OutputRoot, view.Name + ".png");
                var stats = Capture(camera, view, path);
                var hash = Sha256(path);
                if (!hashes.Add(hash)) throw new InvalidOperationException("Duplicate V10 capture: " + view.Name);
                AppendView(manifest, view.Name, view, path, hash, stats, "normal");
            }

            var manifestData = ChannelPlayKhufuV10InteriorBuilder.LoadDisableManifest();
            var superseded = ChannelPlayKhufuV10InteriorBuilder.CollectManifestRenderers(mapObject.transform, manifestData);
            foreach (var renderer in superseded) renderer.enabled = true;
            var mutationView = views.Single(item => item.Name == "grand_gallery_long_axis");
            var mutationPath = Path.Combine(OutputRoot, "mutation_superseded_overlap.png");
            var mutationStats = Capture(camera, mutationView, mutationPath);
            var mutationHash = Sha256(mutationPath);
            foreach (var renderer in superseded) renderer.enabled = false;
            if (superseded.Count != 60) throw new InvalidOperationException("V10 mutation renderer count drifted: " + superseded.Count);
            if (mutationHash == Sha256(Path.Combine(OutputRoot, mutationView.Name + ".png")))
                throw new InvalidOperationException("V10 mutation capture is identical to normal evidence.");
            AppendView(manifest, "mutation_superseded_overlap", mutationView, mutationPath, mutationHash,
                mutationStats, "negative-control");
        }
        finally
        {
            var manifestData = ChannelPlayKhufuV10InteriorBuilder.LoadDisableManifest();
            foreach (var renderer in ChannelPlayKhufuV10InteriorBuilder.CollectManifestRenderers(mapObject.transform, manifestData))
                renderer.enabled = false;
            if (player != null) player.SetActive(playerWasActive);
            RenderSettings.ambientMode = previousAmbientMode;
            RenderSettings.ambientLight = previousAmbientLight;
            foreach (var pair in sceneLightStates)
                if (pair.Key != null) pair.Key.enabled = pair.Value;
            UnityEngine.Object.DestroyImmediate(keyObject);
            UnityEngine.Object.DestroyImmediate(cameraObject);
        }

        manifest.AppendLine("CAPTURE_INTEGRITY: passed");
        manifest.AppendLine("V10_OVERLAP_MUTATION_CAPTURE: passed");
        File.WriteAllText(Path.Combine(OutputRoot, "manifest.md"), manifest.ToString());
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V10_CAPTURES result=exported normal=" + views.Count +
                  " mutation=1 path=\"" + OutputRoot + "\"");
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
        var frame = ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFrame();
        var foot = ChannelPlayKhufuV10InteriorMeshPipeline.GalleryFoot;
        var top = ChannelPlayKhufuV10InteriorMeshPipeline.GalleryTop;
        var step = ChannelPlayKhufuV10InteriorMeshPipeline.GreatStepStop();
        var ascending = ChannelPlayKhufuV10InteriorMeshPipeline.AscendingRoutePoints();
        var service = ChannelPlayKhufuV10InteriorMeshPipeline.HybridReturnPoints();
        var queenDirection = (ChannelPlayKhufuV10InteriorMeshPipeline.QueensChamber - foot).normalized;
        var queenThreshold = foot + queenDirection * 2.5f;
        return new List<View>
        {
            new View("north_entrance_approach",
                ChannelPlayKhufuV10InteriorMeshPipeline.Entrance + new Vector3(-5f, 2.8f, -10.5f),
                ChannelPlayKhufuV10InteriorMeshPipeline.Entrance + Vector3.up * 1.55f, 44f),
            new View("ascending_plug_girdle",
                RouteEye(ChannelPlayKhufuV10InteriorMeshPipeline.Entrance,
                    ChannelPlayKhufuV10InteriorMeshPipeline.Branch, 0.82f, 1.3f, 0f),
                Vector3.Lerp(ascending[0], ascending[1], 0.42f) + Vector3.up * 1.25f, 56f),
            new View("gallery_foot_queen_boundary",
                foot - frame.Forward * 0.75f + frame.Up * 1.25f - frame.Right * 0.2f,
                queenThreshold + Vector3.up * 1.05f, 48f),
            new View("grand_gallery_long_axis",
                RouteEye(foot, top, 0.13f, 1.48f, 0f),
                step + frame.Up * 1.72f, 50f),
            new View("gallery_corbel_slot_detail",
                RouteEye(foot, top, 0.43f, 1.58f, -0.38f),
                Vector3.Lerp(foot, top, 0.58f) + frame.Right * 1.5f + frame.Up * 1.9f, 53f),
            new View("great_step_boundary",
                step - frame.Forward * 3.15f + frame.Up * 1.52f,
                top + frame.Forward * 0.25f + frame.Up * 1.9f, 50f),
            new View("hybrid_service_return",
                RouteEye(service[2], service[3], 0.72f, 1.38f, 0f),
                RouteEye(service[2], service[3], 0.18f, 1.38f, 0f), 48f),
            new View("pyramid_cutaway_integration", new Vector3(15f, 17f, -62f),
                new Vector3(0.5f, 7f, -6f), 46f)
        };
    }

    private static Vector3 RouteEye(Vector3 start, Vector3 end, float t, float eyeHeight, float lateral)
    {
        var rotation = Quaternion.LookRotation((end - start).normalized, Vector3.up);
        return Vector3.Lerp(start, end, t) + rotation * Vector3.up * eyeHeight +
               rotation * Vector3.right * lateral;
    }

    private static void ExportQueenOccluderDiagnostic(Camera camera, Transform root, View view)
    {
        var debugRoot = Path.Combine(OutputRoot, "debug");
        Directory.CreateDirectory(debugRoot);
        var ray = new Ray(view.Position, (view.Target - view.Position).normalized);
        var renderers = UnityEngine.Object.FindObjectsByType<Renderer>(
                FindObjectsInactive.Include, FindObjectsSortMode.None)
            .Where(renderer => renderer.enabled && renderer.gameObject.activeInHierarchy)
            .ToArray();
        var hits = renderers.Select(renderer =>
            {
                var hit = renderer.bounds.IntersectRay(ray, out var distance);
                return new RendererHit(renderer, hit ? Mathf.Max(0f, distance) : float.PositiveInfinity,
                    renderer.transform.IsChildOf(root));
            })
            .Where(hit => !float.IsPositiveInfinity(hit.Distance))
            .OrderBy(hit => hit.Distance)
            .ThenBy(hit => FullPath(hit.Renderer.transform), StringComparer.Ordinal)
            .Take(24)
            .ToArray();

        var receipt = new StringBuilder("# Queen Camera Forward Renderer Hits\n\n");
        receipt.AppendLine("- Camera position: `" + Format(view.Position) + "`");
        receipt.AppendLine("- Camera target: `" + Format(view.Target) + "`");
        receipt.AppendLine("- Camera forward: `" + Format(ray.direction) + "`");
        receipt.AppendLine("- Near clip: `" + camera.nearClipPlane.ToString("0.000", CultureInfo.InvariantCulture) + "`");
        receipt.AppendLine();
        receipt.AppendLine("| Distance | V10 | Renderer path | Bounds center | Bounds size |");
        receipt.AppendLine("|---:|:---:|---|---|---|");
        foreach (var hit in hits)
            receipt.AppendLine("| " + hit.Distance.ToString("0.000", CultureInfo.InvariantCulture) + " | " +
                               (hit.IsV10 ? "yes" : "no") + " | `" + FullPath(hit.Renderer.transform) + "` | `" +
                               Format(hit.Renderer.bounds.center) + "` | `" + Format(hit.Renderer.bounds.size) + "` |");
        receipt.AppendLine();
        receipt.AppendLine("## Superseded Route Glow Candidates");
        receipt.AppendLine();
        foreach (var renderer in renderers.Where(renderer =>
                     renderer.name == "V4_Glow_Queens" || renderer.name == "V4_Glow_Grand")
                 .OrderBy(renderer => renderer.name, StringComparer.Ordinal))
            receipt.AppendLine("- `" + FullPath(renderer.transform) + "`: center=`" + Format(renderer.bounds.center) +
                               "`, size=`" + Format(renderer.bounds.size) + "`, collider=`" +
                               (renderer.GetComponent<Collider>() == null ? "none" : renderer.GetComponent<Collider>().GetType().Name) + "`");
        receipt.AppendLine();
        receipt.AppendLine("FORWARD_RENDERER_QUERY: passed");
        File.WriteAllText(Path.Combine(debugRoot, "queen-camera-forward-hits.md"), receipt.ToString());

        var hidden = renderers.Where(renderer => !renderer.transform.IsChildOf(root)).ToArray();
        try
        {
            foreach (var renderer in hidden) renderer.enabled = false;
            Capture(camera, view, Path.Combine(debugRoot, "queen-branch-v10-only.png"), false);
        }
        finally
        {
            foreach (var renderer in hidden)
                if (renderer != null) renderer.enabled = true;
        }
    }

    private static CaptureStats Capture(Camera camera, View view, string path, bool enforceQuality = true)
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
        if (enforceQuality && (info.Length < 65536 || stats.StandardDeviation < 0.035f || stats.Range < 0.20f ||
            stats.Mean > 0.72f || stats.ClippedFraction > 0.18f)
           )
            throw new InvalidOperationException("V10 capture appears blank or incomplete: " + path +
                " bytes=" + info.Length +
                " mean=" + stats.Mean.ToString("0.0000", CultureInfo.InvariantCulture) +
                " stddev=" + stats.StandardDeviation.ToString("0.0000", CultureInfo.InvariantCulture) +
                " range=" + stats.Range.ToString("0.0000", CultureInfo.InvariantCulture) +
                " clipped=" + stats.ClippedFraction.ToString("0.0000", CultureInfo.InvariantCulture));
        return stats;
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

    private static void AppendView(StringBuilder manifest, string name, View view, string path, string hash,
        CaptureStats stats, string state)
    {
        manifest.AppendLine("## " + name);
        manifest.AppendLine("- State: `" + state + "`");
        manifest.AppendLine("- SHA256: `" + hash + "`");
        manifest.AppendLine("- Bytes: `" + new FileInfo(path).Length + "`");
        manifest.AppendLine("- Camera: position `" + Format(view.Position) + "`, target `" + Format(view.Target) +
                            "`, fov `" + view.FieldOfView.ToString("0.0", CultureInfo.InvariantCulture) + "`");
        manifest.AppendLine("- Luminance mean/stddev/range/edge/clipped: `" + stats.Mean.ToString("0.0000", CultureInfo.InvariantCulture) +
                            " / " + stats.StandardDeviation.ToString("0.0000", CultureInfo.InvariantCulture) + " / " +
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
        return value.x.ToString("0.00", CultureInfo.InvariantCulture) + ", " +
               value.y.ToString("0.00", CultureInfo.InvariantCulture) + ", " +
               value.z.ToString("0.00", CultureInfo.InvariantCulture);
    }

    private static string FullPath(Transform transform)
    {
        var parts = new List<string>();
        for (var current = transform; current != null; current = current.parent) parts.Add(current.name);
        parts.Reverse();
        return string.Join("/", parts);
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
        public float ClippedFraction;
    }

    private sealed class RendererHit
    {
        public readonly Renderer Renderer;
        public readonly float Distance;
        public readonly bool IsV10;

        public RendererHit(Renderer renderer, float distance, bool isV10)
        {
            Renderer = renderer;
            Distance = distance;
            IsV10 = isV10;
        }
    }
}

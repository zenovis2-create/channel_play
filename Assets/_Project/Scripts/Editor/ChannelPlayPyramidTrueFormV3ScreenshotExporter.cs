using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayPyramidTrueFormV3ScreenshotExporter
{
    private const int Width = 1800;
    private const int Height = 1200;
    private const string RunRoot = "runs/pyramid-true-form-v3";

    public static void ExportScreenshots()
    {
        Directory.CreateDirectory(Path.Combine(RunRoot, "screenshots"));
        EditorSceneManager.OpenScene(ChannelPlayPyramidTrueFormV3Builder.ScenePath);

        var root = GameObject.Find(ChannelPlayPyramidTrueFormV3Builder.PyramidRootName);
        if (root == null)
        {
            Fail("pyramid root missing");
            return;
        }

        var renderers = root.GetComponentsInChildren<Renderer>(true)
            .Where(renderer => renderer.enabled && renderer.gameObject.activeInHierarchy)
            .ToArray();
        if (renderers.Length == 0)
        {
            Fail("pyramid root has no active renderers");
            return;
        }

        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers.Skip(1))
        {
            bounds.Encapsulate(renderer.bounds);
        }

        var cameraObject = new GameObject("CP_V3_Temp_Render_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.31f, 0.46f, 0.58f, 1f);
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 500f;
        camera.allowHDR = false;
        camera.allowMSAA = true;

        var fillObject = new GameObject("CP_V3_Temp_Render_Fill");
        var fill = fillObject.AddComponent<Light>();
        fill.type = LightType.Directional;
        fill.color = new Color(0.74f, 0.82f, 0.9f);
        fill.intensity = 0.42f;
        fillObject.transform.rotation = Quaternion.Euler(24f, 145f, 0f);

        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.28f, 0.27f, 0.25f);

        var outputs = new List<string>();
        RenderPerspective(
            camera,
            "exterior-northeast.png",
            new Vector3(70f, 45f, -70f),
            new Vector3(0f, 11.5f, -0.5f),
            33f,
            outputs);
        RenderPerspective(
            camera,
            "cutaway-northwest.png",
            new Vector3(-64f, 39f, -66f),
            new Vector3(0f, 10.5f, -1f),
            32f,
            outputs);
        RenderPerspective(
            camera,
            "cutaway-north.png",
            new Vector3(0f, 27f, -80f),
            new Vector3(0f, 10.5f, -1f),
            31f,
            outputs);
        RenderPerspective(
            camera,
            "smooth-east-silhouette.png",
            new Vector3(78f, 28f, 3f),
            new Vector3(0f, 12f, 0f),
            30f,
            outputs);
        RenderTop(camera, "top-cardinal.png", new Vector3(0f, 95f, 0f), 39f, outputs);

        var foundation = FindDescendant(root.transform, "V3_Foundation");
        var core = FindDescendant(root.transform, "V3_Exterior_Stepped_Core");
        var casing = FindDescendant(root.transform, "V3_Exterior_Smooth_Casing");
        var player = GameObject.Find("MVP_Player");
        var playerWasActive = player != null && player.activeSelf;
        SetActive(foundation, false);
        SetActive(core, false);
        SetActive(casing, false);
        if (player != null)
        {
            player.SetActive(false);
        }
        RenderPerspective(
            camera,
            "interior-route-xray.png",
            new Vector3(35f, 18f, -50f),
            new Vector3(0f, 4.2f, -0.5f),
            32f,
            outputs);
        if (player != null)
        {
            player.SetActive(playerWasActive);
        }
        SetActive(foundation, true);
        SetActive(core, true);
        SetActive(casing, true);

        UnityEngine.Object.DestroyImmediate(cameraObject);
        UnityEngine.Object.DestroyImmediate(fillObject);

        WriteReceipt(bounds, outputs);
        Debug.Log(
            "CHANNEL_PLAY_PYRAMID_TRUE_FORM_V3_SCREENSHOTS result=exported" +
            " count=" + outputs.Count +
            " dir=\"" + Path.Combine(RunRoot, "screenshots").Replace('\\', '/') + "\"");
    }

    private static void RenderPerspective(
        Camera camera,
        string filename,
        Vector3 position,
        Vector3 target,
        float fieldOfView,
        List<string> outputs)
    {
        camera.orthographic = false;
        camera.fieldOfView = fieldOfView;
        camera.transform.position = position;
        camera.transform.LookAt(target);
        Render(camera, filename, outputs);
    }

    private static void RenderTop(Camera camera, string filename, Vector3 position, float orthographicSize, List<string> outputs)
    {
        camera.orthographic = true;
        camera.orthographicSize = orthographicSize;
        camera.transform.position = position;
        camera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        Render(camera, filename, outputs);
    }

    private static void Render(Camera camera, string filename, List<string> outputs)
    {
        var relativePath = Path.Combine(RunRoot, "screenshots", filename).Replace('\\', '/');
        var renderTexture = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32)
        {
            antiAliasing = 4,
        };
        renderTexture.Create();

        var previous = RenderTexture.active;
        camera.targetTexture = renderTexture;
        RenderTexture.active = renderTexture;
        camera.Render();

        var texture = new Texture2D(Width, Height, TextureFormat.RGB24, false);
        texture.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
        texture.Apply();
        File.WriteAllBytes(relativePath, texture.EncodeToPNG());

        camera.targetTexture = null;
        RenderTexture.active = previous;
        UnityEngine.Object.DestroyImmediate(texture);
        UnityEngine.Object.DestroyImmediate(renderTexture);
        outputs.Add(relativePath);
    }

    private static void WriteReceipt(Bounds bounds, List<string> outputs)
    {
        var lines = new List<string>
        {
            "# Pyramid True Form V3 Screenshot Receipt",
            string.Empty,
            "Date: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            string.Empty,
            "## Result",
            string.Empty,
            "Status: `exported`",
            string.Empty,
            "## Scene",
            string.Empty,
            "- `" + ChannelPlayPyramidTrueFormV3Builder.ScenePath + "`",
            "- Root: `" + ChannelPlayPyramidTrueFormV3Builder.PyramidRootName + "`",
            "- Render size: `" + Width + "x" + Height + "`",
            "- Bounds center: `" + FormatVector(bounds.center) + "`",
            "- Bounds size: `" + FormatVector(bounds.size) + "`",
            string.Empty,
            "## Screenshots",
            string.Empty,
        };

        foreach (var output in outputs)
        {
            lines.Add("- `" + output + "`");
        }

        File.WriteAllLines(Path.Combine(RunRoot, "screenshot-receipt.md"), lines);
    }

    private static string FormatVector(Vector3 value)
    {
        return "(" + value.x.ToString("F2") + ", " + value.y.ToString("F2") + ", " + value.z.ToString("F2") + ")";
    }

    private static Transform FindDescendant(Transform parent, string name)
    {
        return parent.GetComponentsInChildren<Transform>(true).FirstOrDefault(child => child.name == name);
    }

    private static void SetActive(Transform target, bool active)
    {
        if (target != null)
        {
            target.gameObject.SetActive(active);
        }
    }

    private static void Fail(string reason)
    {
        Directory.CreateDirectory(RunRoot);
        File.WriteAllLines(
            Path.Combine(RunRoot, "screenshot-receipt.md"),
            new[]
            {
                "# Pyramid True Form V3 Screenshot Receipt",
                string.Empty,
                "Status: `failed`",
                string.Empty,
                "- " + reason,
            });
        Debug.LogError("CHANNEL_PLAY_PYRAMID_TRUE_FORM_V3_SCREENSHOTS result=failed reason=\"" + reason + "\"");
        if (Application.isBatchMode)
        {
            UnityEditor.EditorApplication.Exit(1);
        }
    }
}

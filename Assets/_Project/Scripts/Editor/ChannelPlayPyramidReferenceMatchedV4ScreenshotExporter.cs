using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayPyramidReferenceMatchedV4ScreenshotExporter
{
    private const int Width = 1536;
    private const int Height = 1024;
    private const string RunRoot = "runs/pyramid-reference-matched-v4";

    public static void ExportScreenshots()
    {
        Directory.CreateDirectory(Path.Combine(RunRoot, "screenshots"));
        EditorSceneManager.OpenScene(ChannelPlayPyramidTrueFormV3Builder.ScenePath);

        var root = GameObject.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        if (root == null)
        {
            Fail("reference-matched V4 pyramid root missing");
            return;
        }

        var renderers = root.GetComponentsInChildren<Renderer>(true)
            .Where(renderer => renderer.enabled && renderer.gameObject.activeInHierarchy)
            .ToArray();
        if (renderers.Length == 0)
        {
            Fail("reference-matched V4 pyramid has no active renderers");
            return;
        }

        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers.Skip(1))
        {
            bounds.Encapsulate(renderer.bounds);
        }

        var player = GameObject.Find("MVP_Player");
        var playerWasActive = player != null && player.activeSelf;
        var previousAmbientMode = RenderSettings.ambientMode;
        var previousAmbientLight = RenderSettings.ambientLight;
        var outputs = new List<string>();

        var cameraObject = new GameObject("CP_V4_Temp_Reference_Render_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.57f, 0.73f, 0.84f, 1f);
        camera.nearClipPlane = 0.1f;
        camera.farClipPlane = 500f;
        camera.allowHDR = false;
        camera.allowMSAA = true;

        var fillObject = new GameObject("CP_V4_Temp_Reference_Fill");
        var fill = fillObject.AddComponent<Light>();
        fill.type = LightType.Directional;
        fill.color = new Color(0.78f, 0.86f, 0.94f);
        fill.intensity = 0.38f;
        fill.shadows = LightShadows.None;
        fillObject.transform.rotation = Quaternion.Euler(25f, 154f, 0f);

        try
        {
            if (player != null)
            {
                player.SetActive(false);
            }

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.34f, 0.33f, 0.31f);

            RenderPerspective(
                camera,
                "reference-match-hero.png",
                new Vector3(15f, 13f, -81f),
                new Vector3(0f, 6.2f, -0.5f),
                42f,
                outputs);
            RenderPerspective(
                camera,
                "reference-match-front.png",
                new Vector3(0f, 13f, -85f),
                new Vector3(0f, 6.8f, -0.5f),
                46f,
                outputs);
            RenderPerspective(
                camera,
                "reference-match-side.png",
                new Vector3(85f, 13f, 0f),
                new Vector3(0f, 6.8f, 0f),
                46f,
                outputs);
            RenderTop(camera, "reference-match-top.png", new Vector3(0f, 96f, 0f), 35f, outputs);

            var casing = FindDescendant(root.transform, "V4_Smooth_Casing_With_Tapered_Cutaway");
            var core = FindDescendant(root.transform, "V4_Dense_Exposed_Core_Masonry");
            var section = FindDescendant(root.transform, "V4_Section_Poche");
            var casingWasActive = IsActive(casing);
            var coreWasActive = IsActive(core);
            var sectionWasActive = IsActive(section);

            SetActive(casing, false);
            SetActive(core, false);
            SetActive(section, false);
            RenderPerspective(
                camera,
                "reference-match-xray.png",
                new Vector3(30f, 13f, -78f),
                new Vector3(0f, 6.2f, -1f),
                47f,
                outputs);
            SetActive(casing, casingWasActive);
            SetActive(core, coreWasActive);
            SetActive(section, sectionWasActive);
        }
        finally
        {
            if (player != null)
            {
                player.SetActive(playerWasActive);
            }

            RenderSettings.ambientMode = previousAmbientMode;
            RenderSettings.ambientLight = previousAmbientLight;
            UnityEngine.Object.DestroyImmediate(cameraObject);
            UnityEngine.Object.DestroyImmediate(fillObject);
        }

        WriteReceipt(bounds, outputs);
        Debug.Log(
            "CHANNEL_PLAY_PYRAMID_REFERENCE_V4_SCREENSHOTS result=exported" +
            " count=" + outputs.Count +
            " size=" + Width + "x" + Height +
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

    private static void RenderTop(
        Camera camera,
        string filename,
        Vector3 position,
        float orthographicSize,
        List<string> outputs)
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
            "# Pyramid Reference-matched V4 Screenshot Receipt",
            string.Empty,
            "Date: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            "Status: `exported`",
            string.Empty,
            "- Scene: `" + ChannelPlayPyramidTrueFormV3Builder.ScenePath + "`",
            "- Root: `" + ChannelPlayPyramidReferenceMatchedV4Builder.RootName + "`",
            "- Golden comparison size: `" + Width + "x" + Height + "`",
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

    private static bool IsActive(Transform target)
    {
        return target != null && target.gameObject.activeSelf;
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
                "# Pyramid Reference-matched V4 Screenshot Receipt",
                string.Empty,
                "Status: `failed`",
                string.Empty,
                "- " + reason,
            });
        Debug.LogError("CHANNEL_PLAY_PYRAMID_REFERENCE_V4_SCREENSHOTS result=failed reason=\"" + reason + "\"");
    }
}

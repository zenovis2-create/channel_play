using System;
using System.IO;
using System.Linq;
using ChannelPlay.Gameplay;
using ChannelPlay.Player;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayProductionValidator
{
    private const string SchoolScene = "Assets/_Project/Scenes/School_MVP.unity";
    private const string PlayerPrefab = "Assets/_Project/Prefabs/MVP_Player.prefab";
    private const string FeedbackCaptureEnvironment =
        "CHANNEL_PLAY_FEEDBACK_CAPTURE_PATH";
    private const int FeedbackCaptureWidth = 1600;
    private const int FeedbackCaptureHeight = 900;
    private const string WindowsBuildPath = "builds/windows-dev/ChannelPlay.exe";
    private const string MacBuildPath = "builds/mac-dev/ChannelPlay.app";
    private const string LinuxServerBuildPath = "builds/linux-server/channel_play_server";

    public static void RunPlaytestSmoke()
    {
        var checks = new[]
        {
            CheckAsset(SchoolScene, "school scene"),
            CheckAsset(PlayerPrefab, "MVP player prefab"),
            CheckType(typeof(TraitorEscapeMvpSession), "Traitor Escape MVP session"),
            CheckType(typeof(ChannelPlayerController), "player controller"),
            CheckType(typeof(ChannelFollowCamera), "follow camera"),
            CheckType(typeof(ChannelCameraOccluderCutaway), "camera occluder cutaway"),
            CheckType(typeof(ChannelManualTraversalRecorder), "manual traversal recorder"),
            CheckBuildSettings(),
            CheckSceneLoad(),
        };

        var failed = checks.Where(item => !item.Passed).ToArray();
        foreach (var check in checks)
        {
            Debug.Log(
                $"CHANNEL_PLAY_PLAYTEST_CHECK name=\"{check.Name}\" " +
                $"passed={check.Passed} detail=\"{check.Detail}\"");
        }

        if (failed.Length > 0)
        {
            throw new InvalidOperationException(
                "Channel Play playtest smoke failed: " +
                string.Join(", ", failed.Select(item => item.Name)));
        }

        Debug.Log(
            $"CHANNEL_PLAY_PLAYTEST_SMOKE result=passed checks={checks.Length} " +
            $"scene=\"{SchoolScene}\"");
    }

    public static void BuildWindowsDev()
    {
        BuildDevelopmentPlayer(
            "windows-dev",
            BuildTarget.StandaloneWindows64,
            WindowsBuildPath);
    }

    public static void BuildMacDev()
    {
        BuildDevelopmentPlayer(
            "mac-dev",
            BuildTarget.StandaloneOSX,
            MacBuildPath);
    }

    public static void BuildLinuxServer()
    {
        BuildDevelopmentPlayer(
            "linux-server",
            BuildTarget.StandaloneLinux64,
            LinuxServerBuildPath,
            (int)StandaloneBuildSubtarget.Server);
    }

    public static void CaptureFeedbackFrame()
    {
        var outputPath = Environment.GetEnvironmentVariable(
            FeedbackCaptureEnvironment);
        if (string.IsNullOrWhiteSpace(outputPath))
        {
            throw new InvalidOperationException(
                $"{FeedbackCaptureEnvironment} is required.");
        }

        EditorSceneManager.OpenScene(SchoolScene, OpenSceneMode.Single);
        var cameraObject = GameObject.Find("Operator_Overview_Camera");
        var camera = cameraObject == null
            ? Camera.main
            : cameraObject.GetComponent<Camera>();
        if (camera == null)
        {
            throw new InvalidOperationException(
                "School_MVP feedback camera is missing.");
        }

        outputPath = Path.GetFullPath(outputPath);
        Directory.CreateDirectory(
            Path.GetDirectoryName(outputPath) ?? "reviews/captures");
        var previousTarget = camera.targetTexture;
        var previousActive = RenderTexture.active;
        RenderTexture renderTexture = null;
        Texture2D image = null;
        try
        {
            renderTexture = new RenderTexture(
                FeedbackCaptureWidth,
                FeedbackCaptureHeight,
                24,
                RenderTextureFormat.ARGB32)
            {
                antiAliasing = 4,
            };
            camera.targetTexture = renderTexture;
            camera.Render();
            RenderTexture.active = renderTexture;
            image = new Texture2D(
                FeedbackCaptureWidth,
                FeedbackCaptureHeight,
                TextureFormat.RGB24,
                false);
            image.ReadPixels(
                new Rect(
                    0f,
                    0f,
                    FeedbackCaptureWidth,
                    FeedbackCaptureHeight),
                0,
                0);
            image.Apply(false, false);
            File.WriteAllBytes(outputPath, image.EncodeToPNG());

            var bytes = new FileInfo(outputPath).Length;
            var luminanceRange = MeasureLuminanceRange(image);
            if (bytes < 20000 || luminanceRange < 0.08f)
            {
                throw new InvalidOperationException(
                    "Feedback capture appears blank or incomplete: " +
                    $"bytes={bytes} luminanceRange={luminanceRange:F4}");
            }

            Debug.Log(
                "CHANNEL_PLAY_FEEDBACK_CAPTURE result=passed " +
                $"camera=\"{camera.name}\" width={FeedbackCaptureWidth} " +
                $"height={FeedbackCaptureHeight} bytes={bytes} " +
                $"luminanceRange={luminanceRange:F4} " +
                $"output=\"{outputPath}\"");
        }
        finally
        {
            camera.targetTexture = previousTarget;
            RenderTexture.active = previousActive;
            if (image != null)
            {
                UnityEngine.Object.DestroyImmediate(image);
            }
            if (renderTexture != null)
            {
                if (renderTexture.IsCreated())
                {
                    renderTexture.Release();
                }
                UnityEngine.Object.DestroyImmediate(renderTexture);
            }
        }
    }

    private static float MeasureLuminanceRange(Texture2D image)
    {
        var pixels = image.GetPixels32();
        var minimum = 1f;
        var maximum = 0f;
        for (var index = 0; index < pixels.Length; index += 16)
        {
            var pixel = pixels[index];
            var luminance =
                (0.2126f * pixel.r +
                 0.7152f * pixel.g +
                 0.0722f * pixel.b) / 255f;
            minimum = Mathf.Min(minimum, luminance);
            maximum = Mathf.Max(maximum, luminance);
        }
        return maximum - minimum;
    }

    private static void BuildDevelopmentPlayer(
        string targetName,
        BuildTarget target,
        string outputPath,
        int subtarget = 0)
    {
        Directory.CreateDirectory(
            Path.GetDirectoryName(outputPath) ?? "builds");
        var options = new BuildPlayerOptions
        {
            scenes = EnabledScenes(),
            locationPathName = outputPath,
            target = target,
            subtarget = subtarget,
            options = BuildOptions.Development,
        };

        var report = BuildPipeline.BuildPlayer(options);
        var summary = report.summary;
        Debug.Log(
            $"CHANNEL_PLAY_BUILD_RESULT target={targetName} " +
            $"result={summary.result} size={summary.totalSize} " +
            $"output=\"{outputPath}\"");

        if (summary.result != BuildResult.Succeeded)
        {
            throw new InvalidOperationException(
                $"Channel Play {targetName} build failed: {summary.result}");
        }
    }

    private static string[] EnabledScenes()
    {
        var scenes = EditorBuildSettings.scenes
            .Where(scene => scene.enabled)
            .Select(scene => scene.path)
            .Where(path => !string.IsNullOrWhiteSpace(path))
            .ToArray();

        if (scenes.Length == 0)
        {
            throw new InvalidOperationException(
                "No enabled scenes in EditorBuildSettings.");
        }

        return scenes;
    }

    private static CheckResult CheckAsset(string path, string label)
    {
        var asset = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(path);
        return new CheckResult(label, asset != null, path);
    }

    private static CheckResult CheckType(Type type, string label)
    {
        return new CheckResult(label, type != null, type.FullName ?? label);
    }

    private static CheckResult CheckBuildSettings()
    {
        var enabledScenes = EditorBuildSettings.scenes
            .Where(scene => scene.enabled)
            .Select(scene => scene.path)
            .ToArray();
        return new CheckResult(
            "build settings",
            enabledScenes.Contains(SchoolScene),
            string.Join(",", enabledScenes));
    }

    private static CheckResult CheckSceneLoad()
    {
        var scene = EditorSceneManager.OpenScene(SchoolScene);
        return new CheckResult(
            "scene load",
            scene.IsValid() && scene.isLoaded,
            scene.path);
    }

    private readonly struct CheckResult
    {
        public CheckResult(string name, bool passed, string detail)
        {
            Name = name;
            Passed = passed;
            Detail = detail;
        }

        public string Name { get; }

        public bool Passed { get; }

        public string Detail { get; }
    }
}

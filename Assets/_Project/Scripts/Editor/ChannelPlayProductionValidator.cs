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
    private const float FeedbackViewportMargin = 0.03f;
    private const string WindowsBuildPath = "builds/windows-dev/ChannelPlay.exe";
    private const string MacBuildPath = "builds/mac-dev/ChannelPlay.app";
    private const string LinuxServerBuildPath = "builds/linux-server/channel_play_server";
    private static readonly string[] FeedbackLandmarks =
    {
        "MVP_Player",
        "V5_KeyRoute_Earth",
        "V5_KeyRoute_Sun",
        "V5_KeyRoute_Crown",
        "V5_Physical_Maze_Exit",
    };

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
            CheckOperatorOverviewCamera(),
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
            ? null
            : cameraObject.GetComponent<Camera>();
        if (camera == null)
        {
            throw new InvalidOperationException(
                "School_MVP Operator_Overview_Camera is missing.");
        }
        ChannelPlayBootstrap.ConfigureOperatorOverviewCamera(camera);

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
            var framing = CheckOperatorOverviewCamera();
            if (!framing.Passed)
            {
                throw new InvalidOperationException(
                    $"Feedback camera framing is invalid: {framing.Detail}");
            }
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
                $"framing=\"{framing.Detail}\" " +
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

    private static CheckResult CheckOperatorOverviewCamera()
    {
        var cameraObject = GameObject.Find("Operator_Overview_Camera");
        var camera = cameraObject == null
            ? null
            : cameraObject.GetComponent<Camera>();
        if (camera == null)
        {
            return new CheckResult(
                "operator overview camera",
                false,
                "Operator_Overview_Camera is missing");
        }

        camera.aspect = (float)FeedbackCaptureWidth / FeedbackCaptureHeight;
        var expectedDirection =
            (ChannelPlayBootstrap.OperatorOverviewTarget -
             ChannelPlayBootstrap.OperatorOverviewPosition).normalized;
        var positionMatches =
            Vector3.Distance(
                camera.transform.position,
                ChannelPlayBootstrap.OperatorOverviewPosition) < 0.01f;
        var directionMatches =
            Vector3.Dot(camera.transform.forward, expectedDirection) > 0.999f;
        var lensMatches =
            !camera.orthographic &&
            Mathf.Abs(
                camera.fieldOfView -
                ChannelPlayBootstrap.OperatorOverviewFieldOfView) < 0.01f;
        var landmarks = FeedbackLandmarks
            .Select(name => LandmarkViewportStatus(camera, name))
            .ToArray();
        var landmarksVisible = landmarks.All(item => item.Visible);
        var passed =
            !camera.enabled &&
            positionMatches &&
            directionMatches &&
            lensMatches &&
            landmarksVisible;
        var detail =
            $"position={FormatVector(camera.transform.position)} " +
            $"fov={camera.fieldOfView:F1} " +
            $"landmarks={string.Join(",", landmarks.Select(item => item.Detail))}";
        return new CheckResult("operator overview camera", passed, detail);
    }

    private static LandmarkStatus LandmarkViewportStatus(
        Camera camera,
        string objectName)
    {
        var gameObject = GameObject.Find(objectName);
        if (gameObject == null)
        {
            return new LandmarkStatus(
                false,
                $"{objectName}:missing");
        }

        var renderers = gameObject
            .GetComponentsInChildren<Renderer>(false)
            .Where(renderer => renderer.enabled)
            .ToArray();
        var worldPosition = gameObject.transform.position;
        if (renderers.Length > 0)
        {
            var bounds = renderers[0].bounds;
            for (var index = 1; index < renderers.Length; index++)
            {
                bounds.Encapsulate(renderers[index].bounds);
            }
            worldPosition = bounds.center;
        }

        var viewport = camera.WorldToViewportPoint(worldPosition);
        var visible =
            viewport.z > camera.nearClipPlane &&
            viewport.x >= FeedbackViewportMargin &&
            viewport.x <= 1f - FeedbackViewportMargin &&
            viewport.y >= FeedbackViewportMargin &&
            viewport.y <= 1f - FeedbackViewportMargin;
        return new LandmarkStatus(
            visible,
            $"{FormatLandmarkName(objectName)}:{viewport.x:F2}/{viewport.y:F2}");
    }

    private static string FormatLandmarkName(string objectName)
    {
        return objectName
            .Replace("MVP_Player", "Player")
            .Replace("V5_KeyRoute_", string.Empty)
            .Replace("V5_Physical_Maze_Exit", "Exit");
    }

    private static string FormatVector(Vector3 value)
    {
        return $"{value.x:F1}/{value.y:F1}/{value.z:F1}";
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

    private readonly struct LandmarkStatus
    {
        public LandmarkStatus(bool visible, string detail)
        {
            Visible = visible;
            Detail = detail;
        }

        public bool Visible { get; }

        public string Detail { get; }
    }
}

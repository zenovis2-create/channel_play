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

using System;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class ChannelPlayKhufuV6WindowsBuild
{
    public const string OutputPath = "Builds/KhufuV6/ChannelPlayKhufuV6.exe";
    public const string ReceiptPath = "runs/khufu-v6-visual-slice/windows-build.md";

    private const string ScenePath = "Assets/_Project/Scenes/School_MVP.unity";
    private const string PlayerSettingsPath = "ProjectSettings/ProjectSettings.asset";
    private const string BuildScriptPath = "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6WindowsBuild.cs";

    [MenuItem("Channel Play/Khufu V6/Build Windows Development Player")]
    public static void BuildWindowsDevelopmentPlayer()
    {
        ChannelPlayKhufuV6VisualSliceValidator.ValidateMenu();

        var outputDirectory = Path.GetDirectoryName(OutputPath);
        if (string.IsNullOrEmpty(outputDirectory))
        {
            throw new InvalidOperationException("V6 Windows output directory is invalid.");
        }

        Directory.CreateDirectory(outputDirectory);
        Directory.CreateDirectory(Path.GetDirectoryName(ReceiptPath) ?? ChannelPlayKhufuV6VisualFidelityBuilder.RunRoot);

        var originalFrameTiming = PlayerSettings.enableFrameTimingStats;
        var settingsBefore = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(PlayerSettingsPath);
        BuildReport report = null;
        string buildSettingsHash;

        try
        {
            PlayerSettings.enableFrameTimingStats = true;
            AssetDatabase.SaveAssets();
            buildSettingsHash = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(PlayerSettingsPath);

            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.Development | BuildOptions.DetailedBuildReport,
            };

            report = BuildPipeline.BuildPlayer(options);
        }
        finally
        {
            PlayerSettings.enableFrameTimingStats = originalFrameTiming;
            AssetDatabase.SaveAssets();
        }

        var settingsAfter = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(PlayerSettingsPath);
        if (!string.Equals(settingsBefore, settingsAfter, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "ProjectSettings.asset was not restored after the V6 Windows build: before=" + settingsBefore +
                " after=" + settingsAfter);
        }

        if (report == null)
        {
            throw new InvalidOperationException("Unity returned no BuildReport for the V6 Windows build.");
        }

        var summary = report.summary;
        WriteReceipt(summary, settingsBefore, buildSettingsHash, settingsAfter);
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V6_WINDOWS_BUILD result=" + summary.result.ToString().ToLowerInvariant() +
            " errors=" + summary.totalErrors + " warnings=" + summary.totalWarnings +
            " size=" + summary.totalSize + " output=\"" + OutputPath + "\"");

        if (summary.result != BuildResult.Succeeded || summary.totalErrors != 0)
        {
            throw new InvalidOperationException(
                "Khufu V6 Windows build failed: result=" + summary.result + " errors=" + summary.totalErrors);
        }
    }

    private static void WriteReceipt(
        BuildSummary summary,
        string settingsBefore,
        string buildSettingsHash,
        string settingsAfter)
    {
        var executableExists = File.Exists(OutputPath);
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? string.Empty;
        var unityPlayerPath = Path.Combine(buildRoot, "UnityPlayer.dll");
        var levelPath = Path.Combine(buildRoot, "ChannelPlayKhufuV6_Data", "level0");
        var passed = summary.result == BuildResult.Succeeded && summary.totalErrors == 0 && executableExists &&
                     settingsBefore == settingsAfter && !string.IsNullOrEmpty(buildSettingsHash);

        var text = new StringBuilder();
        text.AppendLine("# Khufu V6 Windows Development Player Build");
        text.AppendLine();
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Build target: `StandaloneWindows64` Development Player");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scene: `" + ScenePath + "`");
        text.AppendLine("- Output: `" + OutputPath + "`");
        text.AppendLine("- Duration: `" + summary.totalTime.TotalSeconds.ToString("F3", CultureInfo.InvariantCulture) + " seconds`");
        text.AppendLine("- Total size: `" + summary.totalSize + " bytes`");
        text.AppendLine("- Errors: `" + summary.totalErrors + "`");
        text.AppendLine("- Warnings: `" + summary.totalWarnings + "`");
        text.AppendLine("- Cache note: `incremental/unspecified; duration is not a clean-build benchmark`");
        text.AppendLine("- Frame Timing Stats in player: `enabled`");
        text.AppendLine("- Player executable SHA256: `" + HashOrMissing(OutputPath) + "`");
        text.AppendLine("- UnityPlayer SHA256: `" + HashOrMissing(unityPlayerPath) + "`");
        text.AppendLine("- Built level SHA256: `" + HashOrMissing(levelPath) + "`");
        text.AppendLine("- Scene source SHA256: `" + HashOrMissing(ScenePath) + "`");
        text.AppendLine("- Builder SHA256: `" + HashOrMissing("Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs") + "`");
        text.AppendLine("- Windows build script SHA256: `" + HashOrMissing(BuildScriptPath) + "`");
        text.AppendLine("- Player settings before SHA256: `" + settingsBefore + "`");
        text.AppendLine("- Player settings build-time SHA256: `" + buildSettingsHash + "`");
        text.AppendLine("- Player settings restored SHA256: `" + settingsAfter + "`");
        text.AppendLine();
        text.AppendLine("V6_WINDOWS_BUILD: " + (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), Encoding.UTF8);
    }

    private static string HashOrMissing(string path)
    {
        return File.Exists(path) ? ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path) : "missing";
    }
}

using System;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class ChannelPlayKhufuV7WindowsBuild
{
    public const string OutputPath = "Builds/KhufuV7/ChannelPlayKhufuV7.exe";
    public const string ReceiptPath = "runs/khufu-v7-entry-wayfinding/windows-build.md";

    private const string PlayerSettingsPath = "ProjectSettings/ProjectSettings.asset";
    private const string BuildScriptPath = "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7WindowsBuild.cs";

    [MenuItem("Channel Play/Khufu V7/Build Windows Development Player")]
    public static void BuildWindowsDevelopmentPlayer()
    {
        ChannelPlayKhufuV7EntryWayfindingValidator.ValidateMenu();
        Directory.CreateDirectory(Path.GetDirectoryName(OutputPath) ?? "Builds/KhufuV7");
        Directory.CreateDirectory(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot);

        var originalFrameTiming = PlayerSettings.enableFrameTimingStats;
        var settingsBefore = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(PlayerSettingsPath);
        string buildSettingsHash;
        BuildReport report = null;
        try
        {
            PlayerSettings.enableFrameTimingStats = true;
            AssetDatabase.SaveAssets();
            buildSettingsHash = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(PlayerSettingsPath);
            report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.Development | BuildOptions.DetailedBuildReport,
            });
        }
        finally
        {
            PlayerSettings.enableFrameTimingStats = originalFrameTiming;
            AssetDatabase.SaveAssets();
        }

        var settingsAfter = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(PlayerSettingsPath);
        if (settingsBefore != settingsAfter)
            throw new InvalidOperationException("ProjectSettings.asset was not restored after V7 build.");
        if (report == null) throw new InvalidOperationException("Unity returned no V7 BuildReport.");

        WriteReceipt(report.summary, settingsBefore, buildSettingsHash, settingsAfter);
        var summary = report.summary;
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_WINDOWS_BUILD result=" + summary.result.ToString().ToLowerInvariant() +
            " errors=" + summary.totalErrors + " warnings=" + summary.totalWarnings + " size=" + summary.totalSize);
        if (summary.result != BuildResult.Succeeded || summary.totalErrors != 0)
            throw new InvalidOperationException("Khufu V7 Windows build failed: " + summary.result);
    }

    private static void WriteReceipt(BuildSummary summary, string settingsBefore, string buildSettingsHash, string settingsAfter)
    {
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? string.Empty;
        var unityPlayer = Path.Combine(buildRoot, "UnityPlayer.dll");
        var level = Path.Combine(buildRoot, "ChannelPlayKhufuV7_Data", "level0");
        var passed = summary.result == BuildResult.Succeeded && summary.totalErrors == 0 &&
            File.Exists(OutputPath) && File.Exists(level) && settingsBefore == settingsAfter;
        var text = new StringBuilder("# Khufu V7 Windows Development Player Build\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Build target: `StandaloneWindows64` Development Player");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scene: `" + ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath + "`");
        text.AppendLine("- Output: `" + OutputPath + "`");
        text.AppendLine("- Duration: `" + summary.totalTime.TotalSeconds.ToString("F3", CultureInfo.InvariantCulture) + " seconds`");
        text.AppendLine("- Total size: `" + summary.totalSize + " bytes`");
        text.AppendLine("- Errors: `" + summary.totalErrors + "`");
        text.AppendLine("- Warnings: `" + summary.totalWarnings + "`");
        text.AppendLine("- Cache note: `incremental/unspecified; duration is not a clean-build benchmark`");
        text.AppendLine("- Frame Timing Stats in player: `enabled`");
        text.AppendLine("- Player executable SHA256: `" + Hash(OutputPath) + "`");
        text.AppendLine("- UnityPlayer SHA256: `" + Hash(unityPlayer) + "`");
        text.AppendLine("- Built level SHA256: `" + Hash(level) + "`");
        text.AppendLine("- Scene source SHA256: `" + Hash(ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath) + "`");
        AppendSource(text, "V7 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingBuilder.cs");
        AppendSource(text, "V7 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingValidator.cs");
        AppendSource(text, "V7 entry probe", "Assets/_Project/Scripts/Gameplay/KhufuV7EntryProofProbe.cs");
        AppendSource(text, "Follow camera", "Assets/_Project/Scripts/Player/ChannelFollowCamera.cs");
        AppendSource(text, "V7 camera profile", "Assets/_Project/Scripts/Player/KhufuV7EntryCameraProfile.cs");
        AppendSource(text, "Cutaway", "Assets/_Project/Scripts/Player/ChannelCameraOccluderCutaway.cs");
        AppendSource(text, "Windows build script", BuildScriptPath);
        text.AppendLine("- Player settings before SHA256: `" + settingsBefore + "`");
        text.AppendLine("- Player settings build-time SHA256: `" + buildSettingsHash + "`");
        text.AppendLine("- Player settings restored SHA256: `" + settingsAfter + "`");
        text.AppendLine();
        text.AppendLine("V7_WINDOWS_BUILD: " + (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), Encoding.UTF8);
    }

    private static void AppendSource(StringBuilder text, string label, string path)
    {
        text.AppendLine("- " + label + " SHA256: `" + Hash(path) + "`");
    }

    private static string Hash(string path)
    {
        return File.Exists(path) ? ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path) : "missing";
    }
}

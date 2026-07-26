using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class ChannelPlayKhufuV8WindowsBuild
{
    public const string OutputPath = "Builds/KhufuV8/ChannelPlayKhufuV8.exe";
    public const string ReceiptPath = ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot + "/windows-build.md";
    private const string PlayerSettingsPath = "ProjectSettings/ProjectSettings.asset";

    [MenuItem("Channel Play/Khufu V8/Build Windows Development Player")]
    public static void BuildWindowsDevelopmentPlayer()
    {
        ChannelPlayKhufuV8TempleProductionArtValidator.ValidateMenu();
        Directory.CreateDirectory(Path.GetDirectoryName(OutputPath) ?? "Builds/KhufuV8");
        Directory.CreateDirectory(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot);
        var originalFrameTiming = PlayerSettings.enableFrameTimingStats;
        var settingsBefore = Hash(PlayerSettingsPath);
        string settingsDuring;
        BuildReport report = null;
        try
        {
            PlayerSettings.enableFrameTimingStats = true;
            AssetDatabase.SaveAssets();
            settingsDuring = Hash(PlayerSettingsPath);
            report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.Development | BuildOptions.DetailedBuildReport
            });
        }
        finally
        {
            PlayerSettings.enableFrameTimingStats = originalFrameTiming;
            AssetDatabase.SaveAssets();
        }

        var settingsAfter = Hash(PlayerSettingsPath);
        if (settingsBefore != settingsAfter) throw new InvalidOperationException("ProjectSettings.asset was not restored after V8 build.");
        if (report == null) throw new InvalidOperationException("Unity returned no V8 BuildReport.");
        WriteReceipt(report.summary, settingsBefore, settingsDuring, settingsAfter);
        if (report.summary.result != BuildResult.Succeeded || report.summary.totalErrors != 0)
            throw new InvalidOperationException("Khufu V8 Windows build failed: " + report.summary.result);
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_WINDOWS_BUILD result=passed errors=" + report.summary.totalErrors +
                  " warnings=" + report.summary.totalWarnings + " size=" + report.summary.totalSize);
    }

    private static void WriteReceipt(BuildSummary summary, string settingsBefore, string settingsDuring, string settingsAfter)
    {
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? string.Empty;
        var player = Path.Combine(buildRoot, "UnityPlayer.dll");
        var level = Path.Combine(buildRoot, "ChannelPlayKhufuV8_Data", "level0");
        var passed = summary.result == BuildResult.Succeeded && summary.totalErrors == 0 && File.Exists(OutputPath) &&
                     File.Exists(player) && File.Exists(level) && settingsBefore == settingsAfter;
        var text = new StringBuilder("# Khufu V8 Windows Development Player Build\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Build target: `StandaloneWindows64` Development Player");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scene: `" + ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath + "`");
        text.AppendLine("- Output: `" + OutputPath + "`");
        text.AppendLine("- Duration: `" + summary.totalTime.TotalSeconds.ToString("F3", CultureInfo.InvariantCulture) + " seconds`");
        text.AppendLine("- Total size: `" + summary.totalSize + " bytes`");
        text.AppendLine("- Errors / warnings: `" + summary.totalErrors + " / " + summary.totalWarnings + "`");
        text.AppendLine("- Player executable SHA256: `" + Hash(OutputPath) + "`");
        text.AppendLine("- UnityPlayer SHA256: `" + Hash(player) + "`");
        text.AppendLine("- Built level SHA256: `" + Hash(level) + "`");
        text.AppendLine("- Scene source SHA256: `" + Hash(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath) + "`");
        AppendSource(text, "V8 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtBuilder.cs");
        AppendSource(text, "V8 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs");
        AppendSource(text, "V8 pipeline", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleArtPipeline.cs");
        AppendSource(text, "V8 proof probe", "Assets/_Project/Scripts/Gameplay/KhufuV8TempleProofProbe.cs");
        AppendSource(text, "V8 build script", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8WindowsBuild.cs");
        foreach (var bucket in ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedDonorBuckets().Concat(new[] { "Square_Red_Granite_Pillars" }))
            AppendSource(text, "Generated mesh " + bucket, ChannelPlayKhufuV8TempleProductionArtBuilder.MeshAssetPath(bucket));
        text.AppendLine("- Player settings before/build/restored SHA256: `" + settingsBefore + " / " + settingsDuring + " / " + settingsAfter + "`");
        text.AppendLine();
        text.AppendLine("V8_WINDOWS_BUILD: " + (passed ? "passed" : "failed"));
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

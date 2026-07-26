using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class ChannelPlayKhufuV10WindowsBuild
{
    public const string OutputPath = "Builds/KhufuV10/ChannelPlayKhufuV10.exe";
    public const string ReceiptPath = ChannelPlayKhufuV10InteriorBuilder.RunRoot + "/windows-build.md";
    private const string PlayerSettingsPath = "ProjectSettings/ProjectSettings.asset";

    [MenuItem("Channel Play/Khufu V10/Build Windows Development Player")]
    public static void BuildWindowsDevelopmentPlayer()
    {
        ChannelPlayKhufuV10InteriorValidator.ValidateMenu();
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? "Builds/KhufuV10";
        if (Directory.Exists(buildRoot)) Directory.Delete(buildRoot, true);
        Directory.CreateDirectory(buildRoot);
        Directory.CreateDirectory(ChannelPlayKhufuV10InteriorBuilder.RunRoot);
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
                scenes = new[] { ChannelPlayKhufuV10InteriorBuilder.ScenePath },
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
        if (settingsBefore != settingsAfter)
            throw new InvalidOperationException("ProjectSettings.asset was not restored after V10 build.");
        if (report == null) throw new InvalidOperationException("Unity returned no V10 BuildReport.");
        WriteReceipt(report, settingsBefore, settingsDuring, settingsAfter);
        if (report.summary.result != BuildResult.Succeeded || report.summary.totalErrors != 0)
            throw new InvalidOperationException("Khufu V10 Windows build failed: " + report.summary.result);
        Debug.Log("CHANNEL_PLAY_KHUFU_V10_WINDOWS_BUILD result=passed errors=" + report.summary.totalErrors +
                  " warnings=" + report.summary.totalWarnings + " size=" + report.summary.totalSize);
    }

    private static void WriteReceipt(BuildReport report, string settingsBefore, string settingsDuring,
        string settingsAfter)
    {
        var summary = report.summary;
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? string.Empty;
        var player = Path.Combine(buildRoot, "UnityPlayer.dll");
        var level = Path.Combine(buildRoot, "ChannelPlayKhufuV10_Data", "level0");
        var managed = Path.Combine(buildRoot, "ChannelPlayKhufuV10_Data", "Managed", "Assembly-CSharp.dll");
        var reportFiles = report.GetFiles().OrderBy(item => item.path, StringComparer.Ordinal).ToArray();
        var passed = summary.result == BuildResult.Succeeded && summary.totalErrors == 0 && File.Exists(OutputPath) &&
                     File.Exists(player) && File.Exists(level) && File.Exists(managed) && settingsBefore == settingsAfter &&
                     reportFiles.Length > 0 && reportFiles.All(item =>
                         File.Exists(item.path) && new FileInfo(item.path).Length == (long)item.size);
        var text = new StringBuilder("# Khufu V10 Windows Development Player Build\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Build target: `StandaloneWindows64` Development Player");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scene: `" + ChannelPlayKhufuV10InteriorBuilder.ScenePath + "`");
        text.AppendLine("- Output: `" + OutputPath + "`");
        text.AppendLine("- Duration: `" + summary.totalTime.TotalSeconds.ToString("F3", CultureInfo.InvariantCulture) + " seconds`");
        text.AppendLine("- Total size: `" + summary.totalSize + " bytes`");
        text.AppendLine("- Errors / warnings: `" + summary.totalErrors + " / " + summary.totalWarnings + "`");
        text.AppendLine("- BuildReport files: `" + reportFiles.Length + "`");
        text.AppendLine("- Player executable SHA256: `" + Hash(OutputPath) + "`");
        text.AppendLine("- UnityPlayer SHA256: `" + Hash(player) + "`");
        text.AppendLine("- Built level SHA256: `" + Hash(level) + "`");
        text.AppendLine("- Assembly-CSharp SHA256: `" + Hash(managed) + "`");
        text.AppendLine("- Scene source SHA256: `" + Hash(ChannelPlayKhufuV10InteriorBuilder.ScenePath) + "`");
        AppendSource(text, "V10 route contract", "Assets/_Project/Scripts/Gameplay/KhufuV10RouteContract.cs");
        AppendSource(text, "V10 traversal probe", "Assets/_Project/Scripts/Gameplay/KhufuV10TraversalProofProbe.cs");
        AppendSource(text, "V10 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorBuilder.cs");
        AppendSource(text, "V10 mesh pipeline", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorMeshPipeline.cs");
        AppendSource(text, "V10 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10InteriorValidator.cs");
        AppendSource(text, "V10 build script", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV10WindowsBuild.cs");
        AppendSource(text, "Shared performance probe", "Assets/_Project/Scripts/Gameplay/KhufuV5PerformanceProbe.cs");
        foreach (var bucket in ChannelPlayKhufuV10InteriorMeshPipeline.Buckets)
            AppendSource(text, "Generated mesh " + bucket,
                ChannelPlayKhufuV10InteriorMeshPipeline.GeneratedRoot + "/KhufuV10_" + bucket + ".asset");
        text.AppendLine();
        text.AppendLine("## BuildReport Payload");
        foreach (var file in reportFiles)
        {
            var relative = RelativeProjectPath(file.path);
            text.AppendLine("- `" + relative + "` / role `" + file.role + "` / bytes `" + file.size +
                            "` / SHA256 `" + Hash(file.path) + "`");
        }
        text.AppendLine("- Player settings before/build/restored SHA256: `" + settingsBefore + " / " +
                        settingsDuring + " / " + settingsAfter + "`");
        text.AppendLine();
        text.AppendLine("V10_WINDOWS_BUILD: " + (passed ? "passed" : "failed"));
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

    private static string RelativeProjectPath(string path)
    {
        var project = Path.GetFullPath(".").TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) +
                      Path.DirectorySeparatorChar;
        var full = Path.GetFullPath(path);
        return full.StartsWith(project, StringComparison.OrdinalIgnoreCase)
            ? full.Substring(project.Length).Replace('\\', '/')
            : full.Replace('\\', '/');
    }
}

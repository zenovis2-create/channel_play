using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class ChannelPlayKhufuV12WindowsBuild
{
    public const string OutputPath = "Builds/KhufuV12/ChannelPlayKhufuV12.exe";
    public const string ReceiptPath = ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot + "/windows-build.md";
    private const string PlayerSettingsPath = "ProjectSettings/ProjectSettings.asset";

    [MenuItem("Channel Play/Khufu V12/Build Windows Development Player")]
    public static void BuildWindowsDevelopmentPlayer()
    {
        ChannelPlayKhufuV12QueenCircuitValidator.ValidateMenu();
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? "Builds/KhufuV12";
        if (Directory.Exists(buildRoot)) Directory.Delete(buildRoot, true);
        Directory.CreateDirectory(buildRoot);
        Directory.CreateDirectory(ChannelPlayKhufuV12QueenCircuitBuilder.RunRoot);
        var originalFrameTiming = PlayerSettings.enableFrameTimingStats;
        var settingsBefore = Hash(PlayerSettingsPath);
        var protectedAssets = ProtectedAssetSnapshot.Capture();
        var protectedAssetsBefore = protectedAssets.Signature();
        string settingsDuring;
        BuildReport report = null;
        try
        {
            PlayerSettings.enableFrameTimingStats = true;
            AssetDatabase.SaveAssets();
            settingsDuring = Hash(PlayerSettingsPath);
            report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.Development | BuildOptions.DetailedBuildReport
            });
        }
        finally
        {
            PlayerSettings.enableFrameTimingStats = originalFrameTiming;
            AssetDatabase.SaveAssets();
            protectedAssets.Restore();
        }

        var settingsAfter = Hash(PlayerSettingsPath);
        var protectedAssetsAfter = ProtectedAssetSnapshot.Capture().Signature();
        if (settingsBefore != settingsAfter)
            throw new InvalidOperationException("ProjectSettings.asset was not restored after V12 build.");
        if (protectedAssetsBefore != protectedAssetsAfter)
            throw new InvalidOperationException("V12 generated/material assets were not restored after build.");
        if (report == null) throw new InvalidOperationException("Unity returned no V12 BuildReport.");
        WriteReceipt(report, settingsBefore, settingsDuring, settingsAfter,
            protectedAssetsBefore, protectedAssetsAfter);
        if (report.summary.result != BuildResult.Succeeded || report.summary.totalErrors != 0)
            throw new InvalidOperationException("Khufu V12 Windows build failed: " + report.summary.result);
        Debug.Log("CHANNEL_PLAY_KHUFU_V12_WINDOWS_BUILD result=passed errors=" + report.summary.totalErrors +
                  " warnings=" + report.summary.totalWarnings + " size=" + report.summary.totalSize);
    }

    public static void RunBatch()
    {
        try
        {
            BuildWindowsDevelopmentPlayer();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    private static void WriteReceipt(BuildReport report, string settingsBefore, string settingsDuring,
        string settingsAfter, string protectedAssetsBefore, string protectedAssetsAfter)
    {
        var summary = report.summary;
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? string.Empty;
        var player = Path.Combine(buildRoot, "UnityPlayer.dll");
        var level = Path.Combine(buildRoot, "ChannelPlayKhufuV12_Data", "level0");
        var assembly = Path.Combine(buildRoot, "ChannelPlayKhufuV12_Data", "Managed", "Assembly-CSharp.dll");
        var reportFiles = report.GetFiles().OrderBy(item => item.path, StringComparer.Ordinal).ToArray();
        var passed = summary.result == BuildResult.Succeeded && summary.totalErrors == 0 &&
                     File.Exists(OutputPath) && File.Exists(player) && File.Exists(level) &&
                     File.Exists(assembly) && settingsBefore == settingsAfter &&
                     protectedAssetsBefore == protectedAssetsAfter &&
                     reportFiles.Length > 0 && reportFiles.All(item =>
                         File.Exists(item.path) && new FileInfo(item.path).Length == (long)item.size);
        var text = new StringBuilder("# Khufu V12 Windows Development Player Build\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Build target: `StandaloneWindows64` Development Player");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scene: `" + ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath + "`");
        text.AppendLine("- Output: `" + OutputPath + "`");
        text.AppendLine("- Duration: `" +
                        summary.totalTime.TotalSeconds.ToString("F3", CultureInfo.InvariantCulture) + " seconds`");
        text.AppendLine("- Total size: `" + summary.totalSize + " bytes`");
        text.AppendLine("- Errors / warnings: `" + summary.totalErrors + " / " + summary.totalWarnings + "`");
        text.AppendLine("- Player executable SHA256: `" + Hash(OutputPath) + "`");
        text.AppendLine("- Built level SHA256: `" + Hash(level) + "`");
        text.AppendLine("- Assembly-CSharp SHA256: `" + Hash(assembly) + "`");
        text.AppendLine("- Scene source SHA256: `" +
                        Hash(ChannelPlayKhufuV12QueenCircuitBuilder.ScenePath) + "`");
        AppendSource(text, "V12 route contract",
            "Assets/_Project/Scripts/Gameplay/KhufuV12QueenRouteContract.cs");
        AppendSource(text, "V12 segment tag",
            "Assets/_Project/Scripts/Gameplay/KhufuV12SegmentTag.cs");
        AppendSource(text, "V12 transition control",
            "Assets/_Project/Scripts/Gameplay/KhufuV12TransitionControl.cs");
        AppendSource(text, "V12 hit recorder",
            "Assets/_Project/Scripts/Gameplay/KhufuV12ControllerHitRecorder.cs");
        AppendSource(text, "V12 traversal probe",
            "Assets/_Project/Scripts/Gameplay/KhufuV12TraversalProofProbe.cs");
        AppendSource(text, "V12 builder",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitBuilder.cs");
        AppendSource(text, "V12 pipeline",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitMeshPipeline.cs");
        AppendSource(text, "V12 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitValidator.cs");
        AppendSource(text, "V12 exporter",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitScreenshotExporter.cs");
        AppendSource(text, "V12 legacy regression",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12QueenCircuitLegacyRegression.cs");
        AppendSource(text, "V12 build script",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV12WindowsBuild.cs");
        text.AppendLine("- Player settings before/build/restored SHA256: `" + settingsBefore + " / " +
                        settingsDuring + " / " + settingsAfter + "`");
        text.AppendLine("- Protected V12 generated/material signature before/after: `" +
                        protectedAssetsBefore + " / " + protectedAssetsAfter + "`");
        text.AppendLine();
        text.AppendLine("V12_WINDOWS_BUILD: " + (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(), new UTF8Encoding(false));
    }

    private static void AppendSource(StringBuilder text, string label, string path)
    {
        text.AppendLine("- " + label + " SHA256: `" + Hash(path) + "`");
    }

    private static string Hash(string path)
    {
        return File.Exists(path) ? ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path) : "missing";
    }

    private sealed class ProtectedAssetSnapshot
    {
        private static readonly string[] Roots =
        {
            ChannelPlayKhufuV12QueenCircuitMeshPipeline.GeneratedRoot,
            ChannelPlayKhufuV12QueenCircuitBuilder.MaterialRoot
        };

        private readonly Dictionary<string, byte[]> files;

        private ProtectedAssetSnapshot(Dictionary<string, byte[]> files)
        {
            this.files = files;
        }

        public static ProtectedAssetSnapshot Capture()
        {
            return new ProtectedAssetSnapshot(ProtectedPaths().ToDictionary(
                path => path,
                File.ReadAllBytes,
                StringComparer.Ordinal));
        }

        public string Signature()
        {
            var lines = files.OrderBy(item => item.Key, StringComparer.Ordinal)
                .Select(item => item.Key.Replace('\\', '/') + "|" + HashBytes(item.Value));
            return HashBytes(Encoding.UTF8.GetBytes(string.Join("\n", lines)));
        }

        public void Restore()
        {
            foreach (var path in ProtectedPaths().Where(path => !files.ContainsKey(path)))
                File.Delete(path);
            foreach (var item in files)
            {
                var parent = Path.GetDirectoryName(item.Key);
                if (!string.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
                File.WriteAllBytes(item.Key, item.Value);
            }
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            var restored = Capture();
            if (Signature() != restored.Signature() ||
                !files.Keys.OrderBy(path => path, StringComparer.Ordinal)
                    .SequenceEqual(restored.files.Keys.OrderBy(path => path, StringComparer.Ordinal)))
                throw new InvalidOperationException("Protected V12 asset snapshot restore failed.");
        }

        private static IEnumerable<string> ProtectedPaths()
        {
            return Roots.Where(Directory.Exists)
                .SelectMany(root => Directory.GetFiles(root, "*", SearchOption.AllDirectories))
                .Concat(Roots.Select(root => root + ".meta").Where(File.Exists))
                .OrderBy(path => path, StringComparer.Ordinal);
        }

        private static string HashBytes(byte[] content)
        {
            using var sha = SHA256.Create();
            return string.Concat(sha.ComputeHash(content).Select(value => value.ToString("x2")));
        }
    }
}

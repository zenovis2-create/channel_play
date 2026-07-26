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

public static class ChannelPlayKhufuV13WindowsBuild
{
    public const string OutputPath =
        "Builds/KhufuV13/ChannelPlayKhufuV13.exe";
    public const string ReceiptPath =
        ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot +
        "/windows-build.md";
    private const string PlayerSettingsPath =
        "ProjectSettings/ProjectSettings.asset";

    private static readonly KeyValuePair<string, string>[] RequiredSources =
    {
        Source("V13 route contract",
            "Assets/_Project/Scripts/Gameplay/KhufuV13SubterraneanRouteContract.cs"),
        Source("V13 segment tag",
            "Assets/_Project/Scripts/Gameplay/KhufuV13SegmentTag.cs"),
        Source("V13 transition control",
            "Assets/_Project/Scripts/Gameplay/KhufuV13SubterraneanThresholdControl.cs"),
        Source("V13 hit recorder",
            "Assets/_Project/Scripts/Gameplay/KhufuV13ControllerHitRecorder.cs"),
        Source("V13 traversal probe",
            "Assets/_Project/Scripts/Gameplay/KhufuV13TraversalProofProbe.cs"),
        Source("V13 prewrite audit",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdAudit.cs"),
        Source("V13 builder",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdBuilder.cs"),
        Source("V13 pipeline",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.cs"),
        Source("V13 validator",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdValidator.cs"),
        Source("V13 exporter",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdScreenshotExporter.cs"),
        Source("V13 legacy regression",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13SubterraneanThresholdLegacyRegression.cs"),
        Source("V13 build script",
            "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV13WindowsBuild.cs")
    };

    [MenuItem("Channel Play/Khufu V13/Build Windows Development Player")]
    public static void BuildWindowsDevelopmentPlayer()
    {
        ChannelPlayKhufuV13SubterraneanThresholdBuilder
            .RestoreCanonicalMaterialKeywords();
        ChannelPlayKhufuV13SubterraneanThresholdValidator.ValidateMenu();
        if (RequiredSources.Any(item => !File.Exists(item.Value)))
            throw new FileNotFoundException("Required V13 build source is missing.",
                RequiredSources.First(item => !File.Exists(item.Value)).Value);
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? "Builds/KhufuV13";
        if (Directory.Exists(buildRoot)) Directory.Delete(buildRoot, true);
        Directory.CreateDirectory(buildRoot);
        Directory.CreateDirectory(
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.RunRoot);
        var originalFrameTiming = PlayerSettings.enableFrameTimingStats;
        var settingsSnapshot = File.ReadAllBytes(PlayerSettingsPath);
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
                scenes = new[]
                {
                    ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath
                },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.Development |
                          BuildOptions.DetailedBuildReport
            });
        }
        finally
        {
            PlayerSettings.enableFrameTimingStats = originalFrameTiming;
            AssetDatabase.SaveAssets();
            File.WriteAllBytes(PlayerSettingsPath, settingsSnapshot);
            AssetDatabase.ImportAsset(PlayerSettingsPath,
                ImportAssetOptions.ForceSynchronousImport |
                ImportAssetOptions.ForceUpdate);
            protectedAssets.Restore();
            ChannelPlayKhufuV13SubterraneanThresholdBuilder
                .RestoreCanonicalMaterialKeywords();
        }

        var settingsAfter = Hash(PlayerSettingsPath);
        var protectedAssetsAfter =
            ProtectedAssetSnapshot.Capture().Signature();
        if (settingsBefore != settingsAfter)
            throw new InvalidOperationException(
                "ProjectSettings.asset was not restored after V13 build.");
        if (protectedAssetsBefore != protectedAssetsAfter)
            throw new InvalidOperationException(
                "V13 generated/material assets were not restored after build.");
        if (report == null)
            throw new InvalidOperationException("Unity returned no V13 BuildReport.");
        var artifactGatePassed = WriteReceipt(report, settingsBefore,
            settingsDuring, settingsAfter,
            protectedAssetsBefore, protectedAssetsAfter);
        if (!artifactGatePassed)
            throw new InvalidOperationException(
                "Khufu V13 Windows build artifact gate failed; see " +
                ReceiptPath + ".");
        if (report.summary.result != BuildResult.Succeeded ||
            report.summary.totalErrors != 0)
            throw new InvalidOperationException(
                "Khufu V13 Windows build failed: " +
                report.summary.result);
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V13_WINDOWS_BUILD result=passed errors=" +
            report.summary.totalErrors + " warnings=" +
            report.summary.totalWarnings + " size=" +
            report.summary.totalSize);
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

    private static bool WriteReceipt(BuildReport report, string settingsBefore,
        string settingsDuring, string settingsAfter,
        string protectedAssetsBefore, string protectedAssetsAfter)
    {
        var summary = report.summary;
        var buildRoot = Path.GetDirectoryName(OutputPath) ?? string.Empty;
        var player = Path.Combine(buildRoot, "UnityPlayer.dll");
        var level = Path.Combine(buildRoot, "ChannelPlayKhufuV13_Data", "level0");
        var assembly = Path.Combine(buildRoot, "ChannelPlayKhufuV13_Data",
            "Managed", "Assembly-CSharp.dll");
        var reportFiles = report.GetFiles()
            .OrderBy(item => item.path, StringComparer.Ordinal).ToArray();
        var sourcesPresent =
            RequiredSources.All(item => File.Exists(item.Value));
        var passed = summary.result == BuildResult.Succeeded &&
                     summary.totalErrors == 0 &&
                     File.Exists(OutputPath) && File.Exists(player) &&
                     File.Exists(level) && File.Exists(assembly) &&
                     settingsBefore == settingsAfter &&
                     protectedAssetsBefore == protectedAssetsAfter &&
                     sourcesPresent && reportFiles.Length > 0 &&
                     reportFiles.All(item => File.Exists(item.path) &&
                         new FileInfo(item.path).Length == (long)item.size);
        var text =
            new StringBuilder("# Khufu V13 Windows Development Player Build\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine(
            "- Build target: `StandaloneWindows64` Development Player");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Scene: `" +
                        ChannelPlayKhufuV13SubterraneanThresholdBuilder.ScenePath +
                        "`");
        text.AppendLine("- Output: `" + OutputPath + "`");
        text.AppendLine("- Duration: `" +
                        summary.totalTime.TotalSeconds.ToString("F3",
                            CultureInfo.InvariantCulture) + " seconds`");
        text.AppendLine("- Total size: `" + summary.totalSize + " bytes`");
        text.AppendLine("- Errors / warnings: `" + summary.totalErrors + " / " +
                        summary.totalWarnings + "`");
        text.AppendLine("- Player executable SHA256: `" + Hash(OutputPath) + "`");
        text.AppendLine("- UnityPlayer.dll SHA256: `" + Hash(player) + "`");
        text.AppendLine("- Built level SHA256: `" + Hash(level) + "`");
        text.AppendLine("- Assembly-CSharp SHA256: `" + Hash(assembly) + "`");
        text.AppendLine("- Build output tree SHA256: `" +
                        TreeSignature(buildRoot) + "`");
        text.AppendLine("- Scene source SHA256: `" +
                        Hash(ChannelPlayKhufuV13SubterraneanThresholdBuilder
                            .ScenePath) + "`");
        foreach (var source in RequiredSources)
            AppendSource(text, source.Key, source.Value);
        text.AppendLine("- Combined V13 source SHA256: `" +
                        SourceSignature() + "`");
        text.AppendLine("- Player settings before/build/restored SHA256: `" +
                        settingsBefore + " / " + settingsDuring + " / " +
                        settingsAfter + "`");
        text.AppendLine(
            "- Protected V13 generated/material signature before/after: `" +
            protectedAssetsBefore + " / " + protectedAssetsAfter + "`");
        text.AppendLine();
        text.AppendLine("V13_WINDOWS_BUILD: " +
                        (passed ? "passed" : "failed"));
        File.WriteAllText(ReceiptPath, text.ToString(),
            new UTF8Encoding(false));
        return passed;
    }

    private static KeyValuePair<string, string> Source(string label, string path)
    {
        return new KeyValuePair<string, string>(label, path);
    }

    private static void AppendSource(StringBuilder text, string label, string path)
    {
        text.AppendLine("- " + label + " SHA256: `" + Hash(path) + "`");
    }

    private static string SourceSignature()
    {
        var payload = string.Join("\n", RequiredSources.Select(item =>
            item.Value.Replace('\\', '/') + "|" + Hash(item.Value)));
        return HashBytes(Encoding.UTF8.GetBytes(payload));
    }

    private static string TreeSignature(string root)
    {
        if (!Directory.Exists(root)) return "missing";
        var payload = string.Join("\n", Directory
            .GetFiles(root, "*", SearchOption.AllDirectories)
            .OrderBy(path => path, StringComparer.Ordinal)
            .Select(path => path.Replace('\\', '/') + "|" + Hash(path)));
        return HashBytes(Encoding.UTF8.GetBytes(payload));
    }

    private static string Hash(string path)
    {
        return File.Exists(path)
            ? ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path)
            : "missing";
    }

    private static string HashBytes(byte[] content)
    {
        using var sha = SHA256.Create();
        return string.Concat(sha.ComputeHash(content)
            .Select(value => value.ToString("x2")));
    }

    private sealed class ProtectedAssetSnapshot
    {
        private static readonly string[] Roots =
        {
            ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline.GeneratedRoot,
            ChannelPlayKhufuV13SubterraneanThresholdBuilder.MaterialRoot
        };

        private readonly Dictionary<string, byte[]> files;

        private ProtectedAssetSnapshot(Dictionary<string, byte[]> files)
        {
            this.files = files;
        }

        public static ProtectedAssetSnapshot Capture()
        {
            return new ProtectedAssetSnapshot(ProtectedPaths().ToDictionary(
                path => path, File.ReadAllBytes, StringComparer.Ordinal));
        }

        public string Signature()
        {
            var lines = files.OrderBy(item => item.Key, StringComparer.Ordinal)
                .Select(item => item.Key.Replace('\\', '/') + "|" +
                                HashBytes(item.Value));
            return HashBytes(Encoding.UTF8.GetBytes(string.Join("\n", lines)));
        }

        public void Restore()
        {
            foreach (var path in ProtectedPaths()
                         .Where(path => !files.ContainsKey(path)))
                File.Delete(path);
            foreach (var item in files)
            {
                var parent = Path.GetDirectoryName(item.Key);
                if (!string.IsNullOrEmpty(parent))
                    Directory.CreateDirectory(parent);
                File.WriteAllBytes(item.Key, item.Value);
            }
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            var restored = Capture();
            if (Signature() != restored.Signature() ||
                !files.Keys.OrderBy(path => path, StringComparer.Ordinal)
                    .SequenceEqual(restored.files.Keys.OrderBy(path => path,
                        StringComparer.Ordinal)))
                throw new InvalidOperationException(
                    "Protected V13 asset snapshot restore failed.");
        }

        private static IEnumerable<string> ProtectedPaths()
        {
            return Roots.Where(Directory.Exists)
                .SelectMany(root =>
                    Directory.GetFiles(root, "*", SearchOption.AllDirectories))
                .Concat(Roots.Select(root => root + ".meta")
                    .Where(File.Exists))
                .OrderBy(path => path, StringComparer.Ordinal);
        }
    }
}

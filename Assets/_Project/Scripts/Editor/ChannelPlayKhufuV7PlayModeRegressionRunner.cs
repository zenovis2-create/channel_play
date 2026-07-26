using System;
using System.IO;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class ChannelPlayKhufuV7PlayModeRegressionRunner
{
    private const string ActiveKey = "ChannelPlay.KhufuV7.PlayModeRegression.Active";
    private const string ResultKey = "ChannelPlay.KhufuV7.PlayModeRegression.Result";
    private const string StartedKey = "ChannelPlay.KhufuV7.PlayModeRegression.Started";
    private const string V5Receipt = "runs/khufu-mega-labyrinth-v5/playmode-probe.md";
    private const string OutputPath = ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot + "/v5-playmode-regression.md";
    private const double StartupTimeoutSeconds = 45d;

    static ChannelPlayKhufuV7PlayModeRegressionRunner()
    {
        if (SessionState.GetBool(ActiveKey, false)) EditorApplication.delayCall += Resume;
    }

    public static void Run()
    {
        if (!Application.isBatchMode) throw new InvalidOperationException("V7 PlayMode regression requires batch mode.");
        Directory.CreateDirectory(ChannelPlayKhufuV7EntryWayfindingBuilder.RunRoot);
        SessionState.SetBool(ActiveKey, true);
        SessionState.SetString(ResultKey, string.Empty);
        SessionState.SetString(StartedKey, DateTime.UtcNow.ToString("O"));
        EditorSceneManager.OpenScene(ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath);
        EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
        EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
        EditorApplication.isPlaying = true;
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_PLAYMODE_RUNNER result=starting");
    }

    private static void Resume()
    {
        if (!SessionState.GetBool(ActiveKey, false)) return;
        EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
        EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
        if (EditorApplication.isPlaying)
        {
            EditorApplication.update -= WaitForRuntime;
            EditorApplication.update += WaitForRuntime;
        }
    }

    private static void OnPlayModeStateChanged(PlayModeStateChange state)
    {
        if (!SessionState.GetBool(ActiveKey, false)) return;
        if (state == PlayModeStateChange.EnteredPlayMode)
        {
            EditorApplication.update -= WaitForRuntime;
            EditorApplication.update += WaitForRuntime;
        }
        else if (state == PlayModeStateChange.EnteredEditMode)
        {
            EditorApplication.update -= WaitForRuntime;
            FinishAndExit();
        }
    }

    private static void WaitForRuntime()
    {
        if (!EditorApplication.isPlaying) return;
        var session = UnityEngine.Object.FindFirstObjectByType<TraitorEscapeMvpSession>();
        if (session != null && session.DiagnosticHasAuthoredBindings && session.DiagnosticPlayer != null)
        {
            EditorApplication.update -= WaitForRuntime;
            ChannelPlayKhufuV5PlayModeProbe.Run();
            var passed = File.Exists(V5Receipt) && File.ReadAllText(V5Receipt).Contains("Verdict: **passed**");
            SessionState.SetString(ResultKey, passed ? "passed" : "failed: V5 probe receipt did not pass");
            EditorApplication.isPlaying = false;
            return;
        }

        if (!DateTime.TryParse(SessionState.GetString(StartedKey, string.Empty), out var started)) started = DateTime.UtcNow;
        if ((DateTime.UtcNow - started).TotalSeconds <= StartupTimeoutSeconds) return;
        EditorApplication.update -= WaitForRuntime;
        SessionState.SetString(ResultKey, "failed: runtime session did not become ready within " + StartupTimeoutSeconds + " seconds");
        EditorApplication.isPlaying = false;
    }

    private static void FinishAndExit()
    {
        var result = SessionState.GetString(ResultKey, "failed: missing runner result");
        var passed = result == "passed";
        var text = new StringBuilder("# Khufu V7 V5 PlayMode Regression\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Result: `" + result + "`");
        text.AppendLine("- Scene SHA256: `" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(ChannelPlayKhufuV7EntryWayfindingBuilder.ScenePath) + "`");
        text.AppendLine("- V5 probe SHA256: `" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(V5Receipt) + "`");
        text.AppendLine();
        text.AppendLine("V7_V5_PLAYMODE_REGRESSION: " + (passed ? "passed" : "failed"));
        File.WriteAllText(OutputPath, text.ToString());
        SessionState.EraseBool(ActiveKey);
        SessionState.EraseString(ResultKey);
        SessionState.EraseString(StartedKey);
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V7_PLAYMODE_RUNNER result=" + (passed ? "passed" : "failed"));
        EditorApplication.Exit(passed ? 0 : 1);
    }
}

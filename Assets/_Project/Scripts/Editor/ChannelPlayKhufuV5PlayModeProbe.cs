using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEngine;

public static class ChannelPlayKhufuV5PlayModeProbe
{
    private const string RunRoot = "runs/khufu-mega-labyrinth-v5";
    private const float StepDistance = 0.5f;
    private const float ControllerCenterAboveRoute = 1.25f;
    private const float MaximumRecoverableStepError = 0.4f;

    [MenuItem("Channel Play/Khufu V5/Run PlayMode Probe")]
    public static void Run()
    {
        var result = new ProbeResult();
        if (!Application.isPlaying)
        {
            result.Failures.Add("Probe must run while the Editor is in Play Mode");
            WriteReceipt(result);
            Debug.LogError("CHANNEL_PLAY_KHUFU_V5_PLAYMODE result=failed reason=\"not in play mode\"");
            return;
        }

        var session = UnityEngine.Object.FindFirstObjectByType<TraitorEscapeMvpSession>();
        if (session == null || !session.DiagnosticHasAuthoredBindings || session.DiagnosticPlayer == null)
        {
            result.Failures.Add("Authored V5 runtime session/player missing");
        }
        else
        {
            ValidateRuntimeObjectives(session, result);
            ValidateControllerTraversal(session, result);
            ValidateShortcutRuntime(result);
            if (!session.DiagnosticShopIsBound) result.Failures.Add("Shop terminal is not bound in Play Mode");
            if (Vector3.Distance(session.DiagnosticPlayer.position, session.DiagnosticPlayerSpawn) > 0.15f)
                Teleport(session.DiagnosticPlayer, session.DiagnosticPlayerSpawn);
        }

        result.Passed = result.Failures.Count == 0;
        WriteReceipt(result);
        if (result.Passed)
            Debug.Log("CHANNEL_PLAY_KHUFU_V5_PLAYMODE result=passed permutations=6 traversal_m=" + result.TraversalDistance.ToString("F1") + " steps=" + result.ControllerSteps + " max_error=" + result.MaxStepError.ToString("F3"));
        else
            Debug.LogError("CHANNEL_PLAY_KHUFU_V5_PLAYMODE result=failed reason=\"" + string.Join("; ", result.Failures.Take(10)) + "\"");
    }

    private static void ValidateRuntimeObjectives(TraitorEscapeMvpSession session, ProbeResult result)
    {
        var keys = new[] { KhufuKeyId.Sun, KhufuKeyId.Crown, KhufuKeyId.Earth };
        foreach (var first in keys)
        foreach (var second in keys.Where(key => key != first))
        {
            var third = keys.Single(key => key != first && key != second);
            session.DiagnosticResetObjectives();
            if (session.DiagnosticCanExtract || session.DiagnosticConfirmMissionTerminal()) result.Failures.Add("Runtime accepted empty objective state");
            if (!session.DiagnosticCollectKey(first) || session.DiagnosticCollectKey(first)) result.Failures.Add("Runtime duplicate handling failed for " + first);
            if (session.DiagnosticConfirmMissionTerminal() || session.DiagnosticCanExtract) result.Failures.Add("Runtime accepted one-key state");
            session.DiagnosticCollectKey(second);
            if (session.DiagnosticConfirmMissionTerminal() || session.DiagnosticCanExtract) result.Failures.Add("Runtime accepted two-key state");
            session.DiagnosticCollectKey(third);
            if (session.DiagnosticCanExtract) result.Failures.Add("Runtime exit opened before terminal confirmation");
            if (!session.DiagnosticConfirmMissionTerminal() || !session.DiagnosticCanExtract || session.DiagnosticPhysicalKeyCount != 3)
                result.Failures.Add("Runtime completed flow rejected: " + first + "," + second + "," + third);
            result.ObjectivePermutations++;
        }
        session.DiagnosticResetObjectives();
    }

    private static void ValidateControllerTraversal(TraitorEscapeMvpSession session, ProbeResult result)
    {
        var root = GameObject.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName)?.transform;
        if (root == null)
        {
            result.Failures.Add("V5 root missing in Play Mode");
            return;
        }

        var routes = new[]
        {
            new RouteProbe("Critical", root.Find("V5_Critical_Route_700_900m"), "V5_Route_"),
            new RouteProbe("Sun", root.Find("V5_KeyRoute_Sun"), "V5_Sun_Route_"),
            new RouteProbe("Crown", root.Find("V5_KeyRoute_Crown"), "V5_Crown_Route_"),
            new RouteProbe("Earth", root.Find("V5_KeyRoute_Earth"), "V5_Earth_Route_"),
        };
        var player = session.DiagnosticPlayer;
        var controller = player.GetComponent<CharacterController>();
        if (controller == null)
        {
            result.Failures.Add("CharacterController missing");
            return;
        }

        var dynamicColliders = GameObject.FindObjectsByType<Collider>(FindObjectsSortMode.None)
            .Where(collider => collider.name.StartsWith("Runtime_Bot_", StringComparison.Ordinal))
            .ToArray();
        foreach (var collider in dynamicColliders) collider.enabled = false;
        var gameplayController = player.GetComponent<ChannelPlay.Player.ChannelPlayerController>();
        var hitRecorder = player.GetComponent<KhufuControllerHitRecorder>();
        if (hitRecorder == null) hitRecorder = player.gameObject.AddComponent<KhufuControllerHitRecorder>();
        if (gameplayController != null) gameplayController.enabled = false;

        try
        {
            foreach (var route in routes)
            {
                if (route.Root == null)
                {
                    result.Failures.Add(route.Label + " route missing in Play Mode");
                    return;
                }

                var markers = route.Root.Cast<Transform>()
                    .Where(item => item.name.StartsWith(route.MarkerPrefix, StringComparison.Ordinal) && item.name.IndexOf("Segment", StringComparison.Ordinal) < 0)
                    .OrderBy(item => item.name)
                    .ToArray();
                Teleport(player, markers[0].position + Vector3.up * ControllerCenterAboveRoute);
                var routeDistance = 0f;
                for (var segment = 1; segment < markers.Length; segment++)
                {
                    var start = markers[segment - 1].position + Vector3.up * ControllerCenterAboveRoute;
                    var end = markers[segment].position + Vector3.up * ControllerCenterAboveRoute;
                    var distance = Vector3.Distance(start, end);
                    var steps = Mathf.Max(1, Mathf.CeilToInt(distance / StepDistance));
                    for (var step = 1; step <= steps; step++)
                    {
                        hitRecorder.Clear();
                        var target = Vector3.Lerp(start, end, step / (float)steps);
                        controller.Move(target - player.position);
                        var error = Vector3.Distance(player.position, target);
                        result.MaxStepError = Mathf.Max(result.MaxStepError, error);
                        result.ControllerSteps++;
                        if (error > MaximumRecoverableStepError)
                        {
                            result.Failures.Add(route.Label + " controller blocked on segment " + (segment - 1) + " step " + step + " error=" + error.ToString("F3") + " at " + Format(target) + " hit=" + (string.IsNullOrEmpty(hitRecorder.LastHitName) ? "none" : hitRecorder.LastHitName));
                            return;
                        }
                    }
                    routeDistance += distance;
                }
                result.RouteDistances[route.Label] = routeDistance;
                result.TraversalDistance += routeDistance;
            }
        }
        finally
        {
            foreach (var collider in dynamicColliders) if (collider != null) collider.enabled = true;
            if (gameplayController != null) gameplayController.enabled = true;
            Teleport(player, session.DiagnosticPlayerSpawn);
        }
    }

    private static void ValidateShortcutRuntime(ProbeResult result)
    {
        var gates = GameObject.FindObjectsByType<KhufuShortcutGate>(FindObjectsSortMode.None);
        if (gates.Length < 3) result.Failures.Add("Fewer than three runtime shortcut gates");
        foreach (var gate in gates)
        {
            if (!gate.IsLocked || !gate.gameObject.activeSelf) result.Failures.Add("Shortcut did not start locked: " + gate.name);
            gate.Unlock();
            if (gate.IsLocked || gate.gameObject.activeSelf) result.Failures.Add("Shortcut failed to unlock: " + gate.name);
            gate.ResetLocked();
        }
    }

    private static void Teleport(Transform player, Vector3 position)
    {
        var controller = player.GetComponent<CharacterController>();
        if (controller != null) controller.enabled = false;
        player.position = position;
        if (controller != null) controller.enabled = true;
        Physics.SyncTransforms();
    }

    private static void WriteReceipt(ProbeResult result)
    {
        Directory.CreateDirectory(RunRoot);
        var text = new StringBuilder("# Khufu V5 PlayMode Probe\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Objective permutations: " + result.ObjectivePermutations + "/6");
        text.AppendLine("- CharacterController distance: " + result.TraversalDistance.ToString("F1") + "m");
        text.AppendLine("- CharacterController steps: " + result.ControllerSteps);
        text.AppendLine("- Maximum step error: " + result.MaxStepError.ToString("F3") + "m");
        foreach (var route in result.RouteDistances) text.AppendLine("- " + route.Key + " controller route: " + route.Value.ToString("F1") + "m");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: " + failure);
        File.WriteAllText(Path.Combine(RunRoot, "playmode-probe.md"), text.ToString());
    }

    private static string Format(Vector3 value) { return "(" + value.x.ToString("F1") + "," + value.y.ToString("F1") + "," + value.z.ToString("F1") + ")"; }

    private sealed class ProbeResult
    {
        public bool Passed;
        public int ObjectivePermutations;
        public int ControllerSteps;
        public float TraversalDistance;
        public float MaxStepError;
        public readonly Dictionary<string, float> RouteDistances = new Dictionary<string, float>();
        public readonly List<string> Failures = new List<string>();
    }

    private sealed class RouteProbe
    {
        public readonly string Label;
        public readonly Transform Root;
        public readonly string MarkerPrefix;
        public RouteProbe(string label, Transform root, string markerPrefix) { Label = label; Root = root; MarkerPrefix = markerPrefix; }
    }
}

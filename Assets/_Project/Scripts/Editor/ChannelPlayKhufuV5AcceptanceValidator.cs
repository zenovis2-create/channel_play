using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV5AcceptanceValidator
{
    private const string MapRootName = "TraitorEscape_Runtime_Map";
    private const string RunRoot = "runs/khufu-mega-labyrinth-v5";
    private const float WalkSpeed = 4.5f;
    private const float MaxSlopeDegrees = 45f;

    [MenuItem("Channel Play/Khufu V5/Run Gate 4 Acceptance")]
    public static void Run()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuMegaLabyrinthV5Builder.ScenePath);
        var result = Validate();
        WriteReceipts(result);
        if (result.Failures.Count > 0)
        {
            Debug.LogError("CHANNEL_PLAY_KHUFU_V5_GATE4 result=failed reason=\"" + string.Join("; ", result.Failures.Take(12)) + "\"");
            return;
        }

        Debug.Log("CHANNEL_PLAY_KHUFU_V5_GATE4 result=passed objective_permutations=6 clearance_samples=" + result.ClearanceSamples + " key_routes=3 hub_proxies=8");
    }

    public static Gate4Result Validate()
    {
        var result = new Gate4Result();
        ValidateObjectivePermutations(result);
        ValidateScene(result);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static void ValidateObjectivePermutations(Gate4Result result)
    {
        var keys = new[] { KhufuKeyId.Sun, KhufuKeyId.Crown, KhufuKeyId.Earth };
        foreach (var first in keys)
        foreach (var second in keys.Where(key => key != first))
        {
            var third = keys.Single(key => key != first && key != second);
            var state = new KhufuObjectiveState();
            if (state.ConfirmAtMissionTerminal()) result.Failures.Add("Terminal accepted zero keys");
            if (state.CanExtract) result.Failures.Add("Exit accepted zero keys");
            if (!state.CollectPhysicalKey(first)) result.Failures.Add("First key rejected: " + first);
            if (state.CollectPhysicalKey(first)) result.Failures.Add("Duplicate key advanced state: " + first);
            if (state.ConfirmAtMissionTerminal()) result.Failures.Add("Terminal accepted one key");
            state.CollectPhysicalKey(second);
            if (state.ConfirmAtMissionTerminal()) result.Failures.Add("Terminal accepted two keys");
            state.CollectPhysicalKey(third);
            if (state.CanExtract) result.Failures.Add("Exit accepted before terminal confirmation");
            if (!state.ConfirmAtMissionTerminal() || !state.CanExtract) result.Failures.Add("Completed flow rejected: " + first + "," + second + "," + third);
            var readout = state.BuildTerminalReadout();
            if (!readout.Contains("Sun") || !readout.Contains("Crown") || !readout.Contains("Earth")) result.Failures.Add("Terminal readout omits named keys");
            result.ObjectivePermutations++;
        }
    }

    private static void ValidateScene(Gate4Result result)
    {
        var map = GameObject.Find(MapRootName);
        var root = map == null ? null : map.transform.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName);
        if (map == null || root == null)
        {
            result.Failures.Add("V5 scene roots missing");
            return;
        }

        Physics.SyncTransforms();
        ValidateRoute(root.Find("V5_Critical_Route_700_900m"), "Critical", 700f, 900f, result);
        ValidateRoute(root.Find("V5_KeyRoute_Sun"), "Sun", 45f * WalkSpeed, 75f * WalkSpeed, result);
        ValidateRoute(root.Find("V5_KeyRoute_Crown"), "Crown", 45f * WalkSpeed, 75f * WalkSpeed, result);
        ValidateRoute(root.Find("V5_KeyRoute_Earth"), "Earth", 45f * WalkSpeed, 75f * WalkSpeed, result);

        foreach (var keyName in new[] { "Sun", "Crown", "Earth" })
        {
            var route = root.Find("V5_KeyRoute_" + keyName);
            if (route == null || route.Find("V5_" + keyName + "_Public_Interaction") == null || route.Find("V5_" + keyName + "_Private_Risk") == null)
                result.Failures.Add(keyName + " route lacks public/private-risk tags");
        }

        var shortcuts = root.Cast<Transform>().Where(item => item.name.StartsWith("V5_Shortcut_", StringComparison.Ordinal)).ToArray();
        foreach (var shortcut in shortcuts)
        {
            var gate = shortcut.GetComponentInChildren<KhufuShortcutGate>(true);
            var trigger = shortcut.GetComponentInChildren<KhufuShortcutUnlockTrigger>(true);
            if (gate == null || trigger == null || trigger.gate != gate || !gate.IsLocked) result.Failures.Add("Shortcut contract invalid: " + shortcut.name);
        }

        ValidateOperatorBounds(map.GetComponent<TraitorEscapeMapBindings>(), root, result);
        ValidateHubProxyClearance(result);
        ValidateObservationSurfaces(root, result);
    }

    private static void ValidateRoute(Transform route, string label, float minimum, float maximum, Gate4Result result)
    {
        if (route == null)
        {
            result.Failures.Add(label + " route missing");
            return;
        }

        var markerPrefix = label == "Critical" ? "V5_Route_" : "V5_" + label + "_Route_";
        var markers = route.Cast<Transform>()
            .Where(item => item.name.StartsWith(markerPrefix, StringComparison.Ordinal) && item.name.IndexOf("Segment", StringComparison.Ordinal) < 0)
            .OrderBy(item => item.name)
            .ToArray();
        if (markers.Length < 2)
        {
            result.Failures.Add(label + " route has fewer than two markers");
            return;
        }

        var length = 0f;
        for (var index = 1; index < markers.Length; index++)
        {
            var a = markers[index - 1].position;
            var b = markers[index].position;
            var delta = b - a;
            length += delta.magnitude;
            var slope = Mathf.Abs(Mathf.Asin(delta.y / delta.magnitude) * Mathf.Rad2Deg);
            if (slope > MaxSlopeDegrees) result.Failures.Add(label + " segment " + (index - 1) + " slope " + slope.ToString("F1") + " exceeds CharacterController limit");

            var floorName = label == "Critical"
                ? "V5_Route_Segment_" + (index - 1).ToString("D2") + "_Floor"
                : "V5_" + label + "_Segment_" + (index - 1).ToString("D2") + "_Floor";
            var floor = route.Find(floorName);
            if (floor == null)
            {
                result.Failures.Add(label + " floor missing: " + floorName);
                continue;
            }

            if (floor.GetComponent<BoxCollider>() == null && !HasSharedCriticalFloor(route, floor))
            {
                result.Failures.Add(label + " floor has no collider or shared critical surface: " + floorName);
                continue;
            }

            if (Vector3.Dot(floor.forward.normalized, delta.normalized) < 0.999f) result.Failures.Add(label + " floor is not aligned in 3D: " + floorName);
            if (Mathf.Abs(floor.localScale.z - delta.magnitude) > 0.05f) result.Failures.Add(label + " floor length mismatch: " + floorName);
            SampleControllerClearance(route, floor, a, b, label, index - 1, result);
        }

        result.RouteLengths[label] = length;
        if (length < minimum || length > maximum) result.Failures.Add(label + " route length " + length.ToString("F1") + " outside " + minimum.ToString("F1") + "-" + maximum.ToString("F1") + "m");
    }

    private static bool HasSharedCriticalFloor(Transform route, Transform floor)
    {
        var critical = route.parent == null ? null : route.parent.Find("V5_Critical_Route_700_900m");
        if (critical == null) return false;
        return critical.Cast<Transform>().Any(candidate =>
            candidate.name.EndsWith("_Floor", StringComparison.Ordinal) &&
            candidate.GetComponent<BoxCollider>() != null &&
            Vector3.Distance(candidate.position, floor.position) < 0.05f &&
            Vector3.Distance(candidate.localScale, floor.localScale) < 0.05f &&
            Mathf.Abs(Vector3.Dot(candidate.forward, floor.forward)) > 0.999f);
    }

    private static void SampleControllerClearance(Transform route, Transform floor, Vector3 a, Vector3 b, string label, int segment, Gate4Result result)
    {
        var samples = Mathf.Max(2, Mathf.CeilToInt(Vector3.Distance(a, b) / 4f));
        for (var sample = 1; sample < samples; sample++)
        {
            var point = Vector3.Lerp(a, b, sample / (float)samples);
            var lower = point + Vector3.up * 0.58f;
            var upper = point + Vector3.up * 1.62f;
            var overlaps = Physics.OverlapCapsule(lower, upper, 0.42f, ~0, QueryTriggerInteraction.Ignore);
            var blockers = overlaps.Where(collider =>
                collider.transform != floor &&
                !collider.transform.IsChildOf(route) &&
                !collider.name.EndsWith("_Floor", StringComparison.Ordinal) &&
                !collider.name.StartsWith("Runtime_Bot_", StringComparison.Ordinal)).ToArray();
            if (blockers.Length > 0)
            {
                result.Failures.Add(label + " segment " + segment + " blocked by " + blockers[0].name + " near " + Format(point));
                return;
            }
            result.ClearanceSamples++;
        }
    }

    private static void ValidateOperatorBounds(TraitorEscapeMapBindings bindings, Transform root, Gate4Result result)
    {
        var reason = "binding component missing";
        if (bindings == null || !bindings.IsValid(out reason))
        {
            result.Failures.Add("Operator/runtime bindings invalid: " + reason);
            return;
        }

        foreach (var district in root.Cast<Transform>().Where(item => item.name.StartsWith("V5_District_", StringComparison.Ordinal)))
        {
            var p = district.GetChild(0).position;
            if (p.x < bindings.operatorXBounds.x || p.x > bindings.operatorXBounds.y || p.z < bindings.operatorZBounds.x || p.z > bindings.operatorZBounds.y)
                result.Failures.Add("Operator bounds exclude " + district.name);
        }
    }

    private static void ValidateHubProxyClearance(Gate4Result result)
    {
        var center = new Vector3(62f, 1.15f, 0f);
        for (var index = 0; index < 8; index++)
        {
            var angle = (index + 0.5f) * Mathf.PI * 0.25f;
            var p = center + new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle)) * 8f;
            var blockers = Physics.OverlapCapsule(p + Vector3.up * 0.55f, p + Vector3.up * 1.55f, 0.45f, ~0, QueryTriggerInteraction.Ignore)
                .Where(collider => !collider.name.EndsWith("_Floor", StringComparison.Ordinal) && !collider.name.StartsWith("Runtime_Bot_", StringComparison.Ordinal))
                .ToArray();
            if (blockers.Length > 0)
                result.Failures.Add("Hub proxy position blocked: " + index);
            else result.HubProxyPositions++;
        }
    }

    private static void ValidateObservationSurfaces(Transform root, Gate4Result result)
    {
        foreach (var item in root.GetComponentsInChildren<Transform>(true).Where(item => item.name.StartsWith("V5_Observation_Only_", StringComparison.Ordinal)))
            if (item.GetComponent<Collider>() != null) result.Failures.Add("Observation-only surface is collidable: " + item.name);
    }

    private static void WriteReceipts(Gate4Result result)
    {
        Directory.CreateDirectory(RunRoot);
        var text = new StringBuilder("# Khufu V5 Gate 4 Acceptance\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Unity: `" + Application.unityVersion + "`");
        text.AppendLine("- Objective permutations: " + result.ObjectivePermutations + "/6");
        text.AppendLine("- Controller-clearance samples: " + result.ClearanceSamples);
        text.AppendLine("- Hub proxy positions: " + result.HubProxyPositions + "/8");
        foreach (var route in result.RouteLengths) text.AppendLine("- " + route.Key + " route: " + route.Value.ToString("F1") + "m (" + (route.Value / WalkSpeed).ToString("F1") + "s at 4.5m/s)");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: " + failure);
        File.WriteAllText(Path.Combine(RunRoot, "gate4-acceptance.md"), text.ToString());
    }

    private static string Format(Vector3 value) { return "(" + value.x.ToString("F1") + "," + value.y.ToString("F1") + "," + value.z.ToString("F1") + ")"; }

    public sealed class Gate4Result
    {
        public bool Passed;
        public int ObjectivePermutations;
        public int ClearanceSamples;
        public int HubProxyPositions;
        public readonly Dictionary<string, float> RouteLengths = new Dictionary<string, float>();
        public readonly List<string> Failures = new List<string>();
    }
}

using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using ChannelPlay.Player;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    [DefaultExecutionOrder(300)]
    public sealed class KhufuV7EntryProofProbe : MonoBehaviour
    {
        private const double SettleSeconds = 3d;
        private const string RearPylon = "V5_Valley_Gate_Pylon_-1";
        private const string FrontPylon = "V5_Valley_Gate_Pylon_1";

        private TraitorEscapeMvpSession session;
        private ChannelCameraOccluderCutaway cutaway;
        private ChannelFollowCamera followCamera;
        private Camera gameplayCamera;
        private string outputRoot;
        private string label;
        private double readyAt = -1d;
        private bool mutated;
        private bool captureStarted;
        private int activeCutaways;
        private int activeValleyPylons;
        private int visibleOccluders;
        private Vector3 cameraPosition;
        private Vector3 playerPosition;
        private string viewportEnvironmentHits;
        private bool playerInFrame;
        private int guideViewportCount;
        private string centerEnvironmentHit = "none";
        private bool routeCenterClear;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v7-entry-proof")) return;
            var host = new GameObject("KhufuV7_Entry_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV7EntryProofProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            outputRoot = ArgumentValue("-khufu-v7-entry-proof-output", Path.Combine(Application.persistentDataPath, "khufu-v7-entry-proof"));
            label = Sanitize(ArgumentValue("-khufu-v7-entry-proof-label", "entry-final"));
            mutated = HasArgument("-khufu-v7-entry-proof-mutate-pylon-name");
            Directory.CreateDirectory(outputRoot);
            Debug.Log("CHANNEL_PLAY_KHUFU_V7_ENTRY_PROOF result=started label=" + label + " mutation=" + mutated);
        }

        private void LateUpdate()
        {
            if (captureStarted) return;
            if (!ResolveRuntime()) return;

            if (readyAt < 0d)
            {
                readyAt = Time.realtimeSinceStartupAsDouble;
                if (mutated) MutateValleyPylonNames();
                return;
            }

            if (Time.realtimeSinceStartupAsDouble - readyAt < SettleSeconds) return;
            activeCutaways = cutaway.ForceRefresh();
            activeValleyPylons = cutaway.DiagnosticActiveValleyGatePylonCount;
            visibleOccluders = cutaway.DiagnosticVisibleOccluderCount();
            cameraPosition = gameplayCamera.transform.position;
            playerPosition = session.DiagnosticPlayer.position;
            var playerViewport = gameplayCamera.WorldToViewportPoint(playerPosition + Vector3.up * 1.2f);
            playerInFrame = IsViewportPointVisible(playerViewport);
            guideViewportCount = CountGuidesInViewport();
            viewportEnvironmentHits = CaptureViewportEnvironmentHits();
            captureStarted = true;
            StartCoroutine(CaptureAndFinish());
        }

        private bool ResolveRuntime()
        {
            if (session == null) session = FindAnyObjectByType<TraitorEscapeMvpSession>();
            if (gameplayCamera == null) gameplayCamera = Camera.main;
            if (gameplayCamera != null)
            {
                if (cutaway == null) cutaway = gameplayCamera.GetComponent<ChannelCameraOccluderCutaway>();
                if (followCamera == null) followCamera = gameplayCamera.GetComponent<ChannelFollowCamera>();
            }
            return session != null && session.DiagnosticPlayer != null && gameplayCamera != null && cutaway != null &&
                followCamera != null && Vector3.Distance(followCamera.CurrentOffset, KhufuV7EntryCameraProfile.EntryOffset) < 0.01f &&
                Vector3.Distance(followCamera.CurrentLookAheadOffset, KhufuV7EntryCameraProfile.EntryLookAheadOffset) < 0.01f;
        }

        private IEnumerator CaptureAndFinish()
        {
            yield return new WaitForEndOfFrame();
            var screenshot = Path.Combine(outputRoot, label + "-participant-entry.png");
            ScreenCapture.CaptureScreenshot(screenshot, 1);
            var deadline = Time.realtimeSinceStartupAsDouble + 5d;
            while ((!File.Exists(screenshot) || new FileInfo(screenshot).Length < 65536) &&
                   Time.realtimeSinceStartupAsDouble < deadline)
            {
                yield return null;
            }

            var screenshotReady = File.Exists(screenshot) && new FileInfo(screenshot).Length >= 65536;
            var profileApplied = followCamera != null &&
                Vector3.Distance(followCamera.CurrentOffset, KhufuV7EntryCameraProfile.EntryOffset) < 0.01f &&
                Vector3.Distance(followCamera.CurrentLookAheadOffset, KhufuV7EntryCameraProfile.EntryLookAheadOffset) < 0.01f;
            var proofPassed = activeCutaways >= 1 && activeValleyPylons >= 1 && visibleOccluders == 0 && screenshotReady &&
                profileApplied && playerInFrame && guideViewportCount >= 2 && routeCenterClear;
            var harnessPassed = mutated ? !proofPassed && activeValleyPylons == 0 : proofPassed;
            WriteReceipt(screenshot, screenshotReady, proofPassed, harnessPassed);
            Debug.Log(
                "CHANNEL_PLAY_KHUFU_V7_ENTRY_PROOF result=" + (harnessPassed ? "passed" : "failed") +
                " mutation=" + mutated + " active=" + activeCutaways + " valley_pylons=" + activeValleyPylons +
                " visible_occluders=" + visibleOccluders + " screenshot=" + screenshotReady);
            Application.Quit(harnessPassed ? 0 : 1);
        }

        private void WriteReceipt(string screenshot, bool screenshotReady, bool proofPassed, bool harnessPassed)
        {
            var receiptName = label + (mutated ? "-blocked-pylon-mutation.md" : "-entry-proof.md");
            var text = new StringBuilder("# Khufu V7 Rendered Entry Proof\n\n");
            text.AppendLine("- Harness verdict: **" + (harnessPassed ? "passed" : "failed") + "**");
            text.AppendLine("- Entry proof: `" + (proofPassed ? "passed" : mutated ? "failed-as-expected" : "failed") + "`");
            text.AppendLine("- Mutation enabled: `" + mutated + "`");
            text.AppendLine("- Settle seconds: `" + SettleSeconds.ToString("F1", CultureInfo.InvariantCulture) + "`");
            text.AppendLine("- Active cutaways: `" + activeCutaways + "`");
            text.AppendLine("- Active Valley Gate pylons: `" + activeValleyPylons + "`");
            text.AppendLine("- Visible candidate occluders: `" + visibleOccluders + "`");
            text.AppendLine("- Camera position: `" + Vector(cameraPosition) + "`");
            text.AppendLine("- Player position: `" + Vector(playerPosition) + "`");
            text.AppendLine("- Follow offset: `" + Vector(followCamera == null ? Vector3.zero : followCamera.CurrentOffset) + "`");
            text.AppendLine("- Look-ahead offset: `" + Vector(followCamera == null ? Vector3.zero : followCamera.CurrentLookAheadOffset) + "`");
            text.AppendLine("- Player in frame: `" + playerInFrame + "`");
            text.AppendLine("- Guides in viewport: `" + guideViewportCount + "`");
            text.AppendLine("- Center environment hit: `" + centerEnvironmentHit + "`");
            text.AppendLine("- Route center clear: `" + routeCenterClear + "`");
            text.AppendLine("- Screenshot: `" + screenshot.Replace('\\', '/') + "`");
            text.AppendLine("- Screenshot ready: `" + screenshotReady + "`");
            text.AppendLine("- Resolution: `" + Screen.width + "x" + Screen.height + "`");
            text.AppendLine("- Viewport environment hits:");
            text.Append(viewportEnvironmentHits);
            text.AppendLine();
            text.AppendLine((mutated ? "V7_BLOCKED_PYLON_MUTATION" : "V7_ENTRY_PROOF") + ": " + (harnessPassed ? "passed" : "failed"));
            File.WriteAllText(Path.Combine(outputRoot, receiptName), text.ToString(), Encoding.UTF8);
        }

        private string CaptureViewportEnvironmentHits()
        {
            var samples = new[] { 0.25f, 0.5f, 0.75f };
            var renderers = FindObjectsByType<Renderer>(FindObjectsSortMode.None)
                .Where(item => item != null && item.enabled && item.gameObject.activeInHierarchy && !item.forceRenderingOff)
                .Where(item => session.DiagnosticPlayer == null || !item.transform.IsChildOf(session.DiagnosticPlayer))
                .ToArray();
            var text = new StringBuilder();

            foreach (var y in samples.Reverse())
            {
                foreach (var x in samples)
                {
                    var ray = gameplayCamera.ViewportPointToRay(new Vector3(x, y, 0f));
                    Renderer nearest = null;
                    var nearestDistance = float.PositiveInfinity;
                    foreach (var renderer in renderers)
                    {
                        if (!renderer.bounds.IntersectRay(ray, out var distance) || distance >= nearestDistance) continue;
                        nearest = renderer;
                        nearestDistance = distance;
                    }

                    var name = nearest == null ? "none" : nearest.name;
                    var state = nearest == null ? "none" : cutaway.DiagnosticCandidateState(nearest);
                    if (Mathf.Approximately(x, 0.5f) && Mathf.Approximately(y, 0.5f))
                    {
                        centerEnvironmentHit = name;
                        routeCenterClear = name.IndexOf("Floor", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            name.StartsWith("V7_Entry_Guide_", StringComparison.Ordinal);
                    }
                    text.AppendLine("  - `" + x.ToString("F2", CultureInfo.InvariantCulture) + "," +
                        y.ToString("F2", CultureInfo.InvariantCulture) + "`: `" + name + "` distance=`" +
                        (nearest == null ? "n/a" : nearestDistance.ToString("F2", CultureInfo.InvariantCulture)) +
                        "` cutaway=`" + state + "`");
                }
            }

            return text.ToString();
        }

        private int CountGuidesInViewport()
        {
            return FindObjectsByType<Renderer>(FindObjectsSortMode.None)
                .Where(item => item != null && item.enabled && !item.forceRenderingOff &&
                    item.name.StartsWith("V7_Entry_Guide_", StringComparison.Ordinal))
                .Count(item => IsViewportPointVisible(gameplayCamera.WorldToViewportPoint(item.bounds.center)));
        }

        private static bool IsViewportPointVisible(Vector3 point)
        {
            return point.z > 0f && point.x >= 0.05f && point.x <= 0.95f && point.y >= 0.05f && point.y <= 0.95f;
        }

        private void MutateValleyPylonNames()
        {
            foreach (var renderer in FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (renderer.name == RearPylon || renderer.name == FrontPylon)
                    renderer.name += "_MUTATED_BLOCKING_CONTROL";
            }
        }

        private static bool HasArgument(string key)
        {
            return Environment.GetCommandLineArgs().Any(item => string.Equals(item, key, StringComparison.OrdinalIgnoreCase));
        }

        private static string ArgumentValue(string key, string fallback)
        {
            var arguments = Environment.GetCommandLineArgs();
            for (var index = 0; index < arguments.Length - 1; index++)
                if (string.Equals(arguments[index], key, StringComparison.OrdinalIgnoreCase)) return arguments[index + 1];
            return fallback;
        }

        private static string Sanitize(string value)
        {
            var characters = value.Where(item => char.IsLetterOrDigit(item) || item == '-' || item == '_').ToArray();
            return characters.Length == 0 ? "entry" : new string(characters);
        }

        private static string Vector(Vector3 value)
        {
            return value.x.ToString("F3", CultureInfo.InvariantCulture) + "," +
                value.y.ToString("F3", CultureInfo.InvariantCulture) + "," +
                value.z.ToString("F3", CultureInfo.InvariantCulture);
        }
    }
}

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
    [DefaultExecutionOrder(320)]
    public sealed class KhufuV8TempleProofProbe : MonoBehaviour
    {
        private const string MapRootName = "TraitorEscape_Runtime_Map";
        private const string V5RootName = "Runtime_Khufu_Mega_Labyrinth_V5";
        private const string V6RootName = "Runtime_Khufu_V6_Visual_Fidelity_Slice";
        private const string V8RootName = "Runtime_Khufu_V8_Temple_Hub_Art";
        private const double SettleSeconds = 3d;
        private static readonly Vector3 ParticipantPosition = new Vector3(88f, 3.41f, 0f);
        private static readonly Vector3 CameraOffset = new Vector3(9f, 5.8f, -6.5f);
        private static readonly Vector3 CameraLookAhead = new Vector3(-17f, 0f, 0f);

        private TraitorEscapeMvpSession session;
        private ChannelFollowCamera followCamera;
        private Camera gameplayCamera;
        private Transform v8Root;
        private string outputRoot;
        private string label;
        private bool mutateGraybox;
        private bool configured;
        private bool captureStarted;
        private double readyAt = -1d;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v8-temple-proof")) return;
            var host = new GameObject("KhufuV8_Temple_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV8TempleProofProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            outputRoot = ArgumentValue("-khufu-v8-temple-proof-output",
                Path.Combine(Application.persistentDataPath, "khufu-v8-temple-proof"));
            label = Sanitize(ArgumentValue("-khufu-v8-temple-proof-label", "v8-temple-final"));
            mutateGraybox = HasArgument("-khufu-v8-temple-proof-mutate-graybox");
            Directory.CreateDirectory(outputRoot);
            Debug.Log("CHANNEL_PLAY_KHUFU_V8_TEMPLE_PROOF result=started label=" + label + " mutation=" + mutateGraybox);
        }

        private void LateUpdate()
        {
            if (captureStarted || !ResolveRuntime()) return;
            if (!configured)
            {
                ConfigureView();
                configured = true;
                readyAt = Time.realtimeSinceStartupAsDouble;
                return;
            }
            if (Time.realtimeSinceStartupAsDouble - readyAt < SettleSeconds) return;
            captureStarted = true;
            StartCoroutine(CaptureAndFinish());
        }

        private bool ResolveRuntime()
        {
            if (session == null) session = FindAnyObjectByType<TraitorEscapeMvpSession>();
            if (gameplayCamera == null) gameplayCamera = Camera.main;
            if (gameplayCamera != null && followCamera == null) followCamera = gameplayCamera.GetComponent<ChannelFollowCamera>();
            if (v8Root == null)
            {
                var root = GameObject.Find(V8RootName);
                v8Root = root == null ? null : root.transform;
            }
            return session != null && session.DiagnosticPlayer != null && gameplayCamera != null && followCamera != null && v8Root != null;
        }

        private void ConfigureView()
        {
            var player = session.DiagnosticPlayer;
            var controller = player.GetComponent<CharacterController>();
            if (controller != null) controller.enabled = false;
            player.SetPositionAndRotation(ParticipantPosition, Quaternion.Euler(0f, -90f, 0f));
            if (controller != null) controller.enabled = true;
            followCamera.SetTarget(player);
            followCamera.SetOffset(CameraOffset);
            followCamera.SetLookAheadOffset(CameraLookAhead);
            if (mutateGraybox) SetGrayboxEnabled(true);
        }

        private IEnumerator CaptureAndFinish()
        {
            yield return new WaitForEndOfFrame();
            var screenshot = Path.Combine(outputRoot, label + (mutateGraybox ? "-graybox-mutation.png" : "-participant-temple.png"));
            ScreenCapture.CaptureScreenshot(screenshot, 1);
            var deadline = Time.realtimeSinceStartupAsDouble + 6d;
            while ((!File.Exists(screenshot) || new FileInfo(screenshot).Length < 65536) &&
                   Time.realtimeSinceStartupAsDouble < deadline)
                yield return null;

            var screenshotReady = File.Exists(screenshot) && new FileInfo(screenshot).Length >= 65536;
            var playerViewport = gameplayCamera.WorldToViewportPoint(session.DiagnosticPlayer.position + Vector3.up * 1.1f);
            var playerInFrame = Visible(playerViewport);
            var v8InFrame = v8Root.GetComponentsInChildren<Renderer>(true)
                .Count(item => item.enabled && item.gameObject.activeInHierarchy && Visible(gameplayCamera.WorldToViewportPoint(item.bounds.center)));
            var grayboxEnabled = GrayboxEnabledCount();
            var cameraFacesTemple = Vector3.Dot(gameplayCamera.transform.forward, Vector3.left) > 0.70f;
            var proofPassed = screenshotReady && playerInFrame && v8InFrame >= 4 && grayboxEnabled == 0 && cameraFacesTemple;
            var harnessPassed = mutateGraybox
                ? screenshotReady && !proofPassed && grayboxEnabled == 16
                : proofPassed;
            WriteReceipt(screenshot, screenshotReady, playerInFrame, v8InFrame, grayboxEnabled,
                cameraFacesTemple, proofPassed, harnessPassed);
            Debug.Log("CHANNEL_PLAY_KHUFU_V8_TEMPLE_PROOF result=" + (harnessPassed ? "passed" : "failed") +
                      " mutation=" + mutateGraybox + " v8_in_frame=" + v8InFrame + " graybox=" + grayboxEnabled);
            Application.Quit(harnessPassed ? 0 : 1);
        }

        private void WriteReceipt(string screenshot, bool screenshotReady, bool playerInFrame, int v8InFrame,
            int grayboxEnabled, bool cameraFacesTemple, bool proofPassed, bool harnessPassed)
        {
            var receipt = new StringBuilder("# Khufu V8 Windows Player Temple Proof\n\n");
            receipt.AppendLine("- Harness verdict: **" + (harnessPassed ? "passed" : "failed") + "**");
            receipt.AppendLine("- Temple proof: `" + (proofPassed ? "passed" : mutateGraybox ? "failed-as-expected" : "failed") + "`");
            receipt.AppendLine("- Graybox mutation: `" + mutateGraybox + "`");
            receipt.AppendLine("- Participant position: `" + Vector(session.DiagnosticPlayer.position) + "`");
            receipt.AppendLine("- Camera position: `" + Vector(gameplayCamera.transform.position) + "`");
            receipt.AppendLine("- Camera offset: `" + Vector(followCamera.CurrentOffset) + "`");
            receipt.AppendLine("- Camera look-ahead: `" + Vector(followCamera.CurrentLookAheadOffset) + "`");
            receipt.AppendLine("- Player in frame: `" + playerInFrame + "`");
            receipt.AppendLine("- V8 renderer centers in frame: `" + v8InFrame + "`");
            receipt.AppendLine("- Enabled V5/V6 graybox renderers: `" + grayboxEnabled + "`");
            receipt.AppendLine("- Camera faces temple: `" + cameraFacesTemple + "`");
            receipt.AppendLine("- Screenshot: `" + screenshot.Replace('\\', '/') + "`");
            receipt.AppendLine("- Screenshot ready: `" + screenshotReady + "`");
            receipt.AppendLine("- Resolution: `" + Screen.width + "x" + Screen.height + "`");
            receipt.AppendLine();
            receipt.AppendLine((mutateGraybox ? "V8_GRAYBOX_PLAYER_MUTATION" : "V8_WINDOWS_PLAYER_TEMPLE_PROOF") +
                               ": " + (harnessPassed ? "passed" : "failed"));
            File.WriteAllText(Path.Combine(outputRoot, label +
                (mutateGraybox ? "-graybox-mutation.md" : "-temple-proof.md")), receipt.ToString(), Encoding.UTF8);
        }

        private static void SetGrayboxEnabled(bool enabled)
        {
            var mapObject = GameObject.Find(MapRootName);
            if (mapObject == null) return;
            var v5 = mapObject.transform.Find(V5RootName + "/V5_District_Pyramid_Temple_Hub");
            var v6 = mapObject.transform.Find(V6RootName + "/V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
            if (v5 == null || v6 == null) return;
            foreach (var renderer in v5.GetComponentsInChildren<Renderer>(true).Concat(v6.GetComponentsInChildren<Renderer>(true)))
                renderer.enabled = enabled;
        }

        private static int GrayboxEnabledCount()
        {
            var mapObject = GameObject.Find(MapRootName);
            if (mapObject == null) return -1;
            var v5 = mapObject.transform.Find(V5RootName + "/V5_District_Pyramid_Temple_Hub");
            var v6 = mapObject.transform.Find(V6RootName + "/V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
            if (v5 == null || v6 == null) return -1;
            return v5.GetComponentsInChildren<Renderer>(true).Concat(v6.GetComponentsInChildren<Renderer>(true))
                .Count(item => item.enabled && item.gameObject.activeInHierarchy);
        }

        private static bool Visible(Vector3 viewport)
        {
            return viewport.z > 0f && viewport.x >= 0.03f && viewport.x <= 0.97f && viewport.y >= 0.03f && viewport.y <= 0.97f;
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
            return characters.Length == 0 ? "v8-temple" : new string(characters);
        }

        private static string Vector(Vector3 value)
        {
            return value.x.ToString("F3", CultureInfo.InvariantCulture) + "," +
                   value.y.ToString("F3", CultureInfo.InvariantCulture) + "," +
                   value.z.ToString("F3", CultureInfo.InvariantCulture);
        }
    }
}

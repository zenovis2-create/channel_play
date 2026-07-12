using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using ChannelPlay.Player;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    [DefaultExecutionOrder(330)]
    public sealed class KhufuV9CausewayProofProbe : MonoBehaviour
    {
        private const string MapRootName = "TraitorEscape_Runtime_Map";
        private const string V5RootName = "Runtime_Khufu_Mega_Labyrinth_V5";
        private const string V9RootName = "Runtime_Khufu_V9_Causeway_Fidelity";
        private const float StepDistance = 0.5f;
        private const float MaximumStepError = 0.4f;
        private const float RouteAnchorPlayerHeight = 1.25f;
        private const float ErrorMetricMutationOffset = 0.75f;
        private const string ErrorMetricMutationHit = "V9_ERROR_METRIC_OFFSET";
        private const double RuntimeTimeoutSeconds = 20d;

        private static readonly Vector3[] Route =
        {
            new Vector3(150f, 1.4f, 0f),
            new Vector3(105f, 4.4f, 0f),
            new Vector3(62f, 2.4f, 0f)
        };

        private readonly List<CaptureRecord> captures = new List<CaptureRecord>();
        private TraitorEscapeMvpSession session;
        private CharacterController controller;
        private ChannelPlayerController playerController;
        private KhufuControllerHitRecorder hitRecorder;
        private ChannelFollowCamera followCamera;
        private Camera gameplayCamera;
        private Transform v9Root;
        private Collider[] dynamicColliders = Array.Empty<Collider>();
        private Transform mutationProxy;
        private Renderer mutationGraybox;
        private string outputRoot;
        private string label;
        private bool mutateProxy;
        private bool mutateErrorMetric;
        private bool errorMetricMutationObserved;
        private bool routeAnchorsValid;
        private bool started;
        private double startedAt;
        private float maximumError;
        private float traversedDistance;
        private bool blocked;
        private string blockedHit = string.Empty;
        private Vector3 blockedAt;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v9-causeway-proof")) return;
            var host = new GameObject("KhufuV9_Causeway_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV9CausewayProofProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            outputRoot = ArgumentValue("-khufu-v9-causeway-proof-output",
                Path.Combine(Application.persistentDataPath, "khufu-v9-causeway-proof"));
            label = Sanitize(ArgumentValue("-khufu-v9-causeway-proof-label", "v9-causeway-final"));
            mutateProxy = HasArgument("-khufu-v9-causeway-proof-mutate-proxy");
            mutateErrorMetric = HasArgument("-khufu-v9-causeway-proof-mutate-error-metric");
            Directory.CreateDirectory(outputRoot);
            startedAt = Time.realtimeSinceStartupAsDouble;
            if (mutateProxy && mutateErrorMetric)
            {
                FailAndQuit("proxy and error-metric mutations are mutually exclusive");
                return;
            }
            Debug.Log("CHANNEL_PLAY_KHUFU_V9_CAUSEWAY_PROOF result=started label=" + label + " mode=" + ProofMode());
        }

        private void LateUpdate()
        {
            if (started) return;
            if (!ResolveRuntime())
            {
                if (Time.realtimeSinceStartupAsDouble - startedAt > RuntimeTimeoutSeconds)
                    FailAndQuit("runtime did not become ready");
                return;
            }
            started = true;
            StartCoroutine(RunProof());
        }

        private bool ResolveRuntime()
        {
            if (session == null) session = FindAnyObjectByType<TraitorEscapeMvpSession>();
            if (gameplayCamera == null) gameplayCamera = Camera.main;
            if (gameplayCamera != null && followCamera == null) followCamera = gameplayCamera.GetComponent<ChannelFollowCamera>();
            if (v9Root == null)
            {
                var root = GameObject.Find(V9RootName);
                v9Root = root == null ? null : root.transform;
            }
            if (session == null || session.DiagnosticPlayer == null || gameplayCamera == null || followCamera == null || v9Root == null)
                return false;
            controller = session.DiagnosticPlayer.GetComponent<CharacterController>();
            return controller != null;
        }

        private IEnumerator RunProof()
        {
            var player = session.DiagnosticPlayer;
            playerController = player.GetComponent<ChannelPlayerController>();
            hitRecorder = player.GetComponent<KhufuControllerHitRecorder>();
            if (hitRecorder == null) hitRecorder = player.gameObject.AddComponent<KhufuControllerHitRecorder>();
            dynamicColliders = FindObjectsByType<Collider>(FindObjectsSortMode.None)
                .Where(item => item.name.StartsWith("Runtime_Bot_", StringComparison.Ordinal)).ToArray();
            foreach (var item in dynamicColliders) item.enabled = false;
            if (playerController != null) playerController.enabled = false;

            Teleport(player, Route[0]);
            player.rotation = Quaternion.Euler(0f, -90f, 0f);
            followCamera.SetTarget(player);
            followCamera.SetOffset(new Vector3(10f, 6.2f, -7.5f));
            followCamera.SetLookAheadOffset(new Vector3(-15f, 0f, 0f));
            routeAnchorsValid = ValidateRouteAnchors();
            if (mutateProxy) ApplyProxyMutation();

            yield return new WaitForSecondsRealtime(1.5f);
            if (!mutateErrorMetric) yield return Capture("valley_gate_start");

            for (var segment = 1; segment < Route.Length && !blocked; segment++)
            {
                var start = Route[segment - 1];
                var end = Route[segment];
                var steps = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(start, end) / StepDistance));
                for (var step = 1; step <= steps; step++)
                {
                    var target = Vector3.Lerp(start, end, step / (float)steps);
                    var before = player.position;
                    hitRecorder.Clear();
                    controller.Move(target - player.position);
                    traversedDistance += Vector3.Distance(before, player.position);
                    var evaluationTarget = target;
                    if (mutateErrorMetric && !errorMetricMutationObserved)
                        evaluationTarget += Vector3.forward * ErrorMetricMutationOffset;
                    var error = Vector3.Distance(player.position, evaluationTarget);
                    maximumError = Mathf.Max(maximumError, error);
                    if (error > MaximumStepError)
                    {
                        blocked = true;
                        if (mutateErrorMetric)
                        {
                            errorMetricMutationObserved = true;
                            blockedHit = ErrorMetricMutationHit;
                        }
                        else
                        {
                            blockedHit = hitRecorder.LastHitName;
                        }
                        blockedAt = evaluationTarget;
                        break;
                    }
                    yield return null;
                }
                if (!blocked && segment == 1)
                {
                    yield return new WaitForSecondsRealtime(0.5f);
                    yield return Capture("covered_causeway_midpoint");
                }
            }

            if (!blocked)
            {
                followCamera.SetOffset(new Vector3(-10f, 6.5f, -9f));
                followCamera.SetLookAheadOffset(new Vector3(14f, 0f, 0f));
            }
            yield return new WaitForSecondsRealtime(blocked ? 0.75f : 1.25f);
            if (!mutateErrorMetric) yield return Capture(blocked ? "mutation_blocked" : "v8_hub_arrival");
            FinishAndQuit();
        }

        private void ApplyProxyMutation()
        {
            mutationProxy = v9Root.Find("V9_Collision_Proxies/V9_PROXY_Valley_To_Causeway_East_Parapet");
            if (mutationProxy != null)
            {
                var position = mutationProxy.position;
                position.z = 0f;
                mutationProxy.position = position;
            }
            var v5 = GameObject.Find(V5RootName);
            var route = v5 == null ? null : v5.transform.Find("V5_Critical_Route_700_900m");
            var graybox = route == null ? null : route.Find("V5_Route_Segment_00_East_Wall");
            mutationGraybox = graybox == null ? null : graybox.GetComponent<Renderer>();
            if (mutationGraybox != null && mutationProxy != null)
            {
                mutationGraybox.transform.SetPositionAndRotation(mutationProxy.position, mutationProxy.rotation);
                mutationGraybox.transform.localScale = mutationProxy.lossyScale;
                mutationGraybox.enabled = true;
            }
            Physics.SyncTransforms();
        }

        private IEnumerator Capture(string stage)
        {
            yield return new WaitForEndOfFrame();
            var mode = mutateProxy ? "mutation" : mutateErrorMetric ? "error-metric-mutation" : "normal";
            var path = Path.Combine(outputRoot, label + "-" + mode + "-" + stage + ".png");
            if (File.Exists(path)) File.Delete(path);
            var requestedAt = DateTime.UtcNow;
            ScreenCapture.CaptureScreenshot(path, 1);
            var deadline = Time.realtimeSinceStartupAsDouble + 8d;
            while ((!File.Exists(path) || new FileInfo(path).Length < 65536) && Time.realtimeSinceStartupAsDouble < deadline)
                yield return null;
            var info = File.Exists(path) ? new FileInfo(path) : null;
            var fresh = info != null && info.LastWriteTimeUtc >= requestedAt.AddSeconds(-2d);
            var standardDeviation = 0f;
            var range = 0f;
            var semantic = fresh && ValidatePngPixels(path, out standardDeviation, out range);
            var ready = info != null && info.Length >= 65536 && fresh && semantic;
            captures.Add(new CaptureRecord(stage, path, ready, fresh, semantic,
                ready ? Sha256(path) : "missing", standardDeviation, range));
        }

        private void FinishAndQuit()
        {
            var finalError = Vector3.Distance(session.DiagnosticPlayer.position, Route[Route.Length - 1]);
            var v9Colliders = v9Root.GetComponentsInChildren<BoxCollider>(true).Length;
            var v9Renderers = v9Root.GetComponentsInChildren<Renderer>(true).Count(item => item.enabled && item.gameObject.activeInHierarchy);
            var grayboxEnabled = mutationGraybox != null && mutationGraybox.enabled ? 1 : 0;
            var capturesReady = captures.All(item => item.Ready);
            var expectedCaptureCount = mutateErrorMetric ? 0 : mutateProxy ? 2 : 3;
            var expectedRouteDistance = ExpectedRouteDistance();
            var normalPassed = !mutateProxy && !mutateErrorMetric && !blocked && finalError <= MaximumStepError && maximumError <= MaximumStepError &&
                               traversedDistance >= expectedRouteDistance - MaximumStepError && routeAnchorsValid &&
                               capturesReady && captures.Count == expectedCaptureCount && v9Colliders == 23 && v9Renderers == 5 && grayboxEnabled == 0;
            var proxyMutationPassed = mutateProxy && blocked && mutationProxy != null &&
                                      blockedHit.StartsWith("V9_PROXY_", StringComparison.Ordinal) && capturesReady &&
                                      routeAnchorsValid && captures.Count == expectedCaptureCount && v9Colliders == 23 && grayboxEnabled == 1;
            var errorMetricMutationPassed = mutateErrorMetric && blocked && errorMetricMutationObserved &&
                                            maximumError > MaximumStepError && blockedHit == ErrorMetricMutationHit &&
                                            routeAnchorsValid && captures.Count == expectedCaptureCount && v9Colliders == 23 && grayboxEnabled == 0;
            var harnessPassed = mutateErrorMetric ? errorMetricMutationPassed : mutateProxy ? proxyMutationPassed : normalPassed;
            WriteReceipt(harnessPassed, normalPassed, proxyMutationPassed, errorMetricMutationPassed, finalError,
                v9Colliders, v9Renderers, grayboxEnabled, null);
            Debug.Log("CHANNEL_PLAY_KHUFU_V9_CAUSEWAY_PROOF result=" + (harnessPassed ? "passed" : "failed") +
                      " mode=" + ProofMode() + " blocked=" + blocked + " hit=" + blockedHit +
                      " max_error=" + maximumError.ToString("F3", CultureInfo.InvariantCulture));
            Application.Quit(harnessPassed ? 0 : 1);
        }

        private void FailAndQuit(string reason)
        {
            if (started) return;
            started = true;
            WriteReceipt(false, false, false, false, float.PositiveInfinity, 0, 0, 0, reason);
            Debug.LogError("CHANNEL_PLAY_KHUFU_V9_CAUSEWAY_PROOF result=failed reason=\"" + reason + "\"");
            Application.Quit(1);
        }

        private void WriteReceipt(bool harnessPassed, bool normalPassed, bool proxyMutationPassed,
            bool errorMetricMutationPassed, float finalError, int v9Colliders, int v9Renderers,
            int grayboxEnabled, string failure)
        {
            var text = new StringBuilder("# Khufu V9 Windows Player Causeway Proof\n\n");
            text.AppendLine("- Harness verdict: **" + (harnessPassed ? "passed" : "failed") + "**");
            text.AppendLine("- Mode: `" + ProofMode() + "`");
            text.AppendLine("- Normal traversal proof: `" + (normalPassed ? "passed" : mutateProxy || mutateErrorMetric ? "not-applicable" : "failed") + "`");
            text.AppendLine("- Proxy mutation proof: `" + (proxyMutationPassed ? "passed" : mutateProxy ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Error metric mutation proof: `" + (errorMetricMutationPassed ? "passed" : mutateErrorMetric ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Route: `Valley Gate -> Covered Causeway -> V8 Temple Hub`");
            text.AppendLine("- Serialized route anchors match probe: `" + routeAnchorsValid + "`");
            text.AppendLine("- Expected route distance: `" + ExpectedRouteDistance().ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- CharacterController traversed distance: `" + traversedDistance.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Maximum step error: `" + maximumError.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Final target error: `" + finalError.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Blocked: `" + blocked + "`");
            text.AppendLine("- Blocked collider: `" + (string.IsNullOrEmpty(blockedHit) ? "none" : blockedHit) + "`");
            text.AppendLine("- Blocked target: `" + Vector(blockedAt) + "`");
            text.AppendLine("- V9 renderers / BoxColliders: `" + v9Renderers + " / " + v9Colliders + "`");
            text.AppendLine("- Enabled mutation graybox renderers: `" + grayboxEnabled + "`");
            text.AppendLine("- Resolution: `" + Screen.width + "x" + Screen.height + "`");
            foreach (var capture in captures)
                text.AppendLine("- Capture " + capture.Stage + ": `" + capture.Path.Replace('\\', '/') + "` / ready `" + capture.Ready +
                                "` / fresh `" + capture.Fresh + "` / semantic `" + capture.Semantic + "` / stddev/range `" +
                                capture.StandardDeviation.ToString("F4", CultureInfo.InvariantCulture) + " / " +
                                capture.Range.ToString("F4", CultureInfo.InvariantCulture) + "` / SHA256 `" + capture.Hash + "`");
            if (!string.IsNullOrEmpty(failure)) text.AppendLine("- Failure: `" + failure + "`");
            text.AppendLine();
            text.AppendLine((mutateErrorMetric ? "V9_WINDOWS_PLAYER_ERROR_METRIC_MUTATION" :
                mutateProxy ? "V9_WINDOWS_PLAYER_PROXY_MUTATION" : "V9_WINDOWS_PLAYER_CAUSEWAY_TRAVERSAL") +
                            ": " + (harnessPassed ? "passed" : "failed"));
            var suffix = mutateErrorMetric ? "-error-metric-mutation.md" :
                mutateProxy ? "-proxy-mutation.md" : "-causeway-traversal.md";
            File.WriteAllText(Path.Combine(outputRoot, label + suffix), text.ToString(), Encoding.UTF8);
        }

        private string ProofMode()
        {
            if (mutateErrorMetric) return "error-metric-negative-control";
            return mutateProxy ? "proxy-mutation-negative-control" : "normal-traversal";
        }

        private bool ValidateRouteAnchors()
        {
            var metadata = v9Root.Find("V9_Metadata");
            if (metadata == null) return false;
            var names = new[] { "V9_Anchor_Valley_Gate", "V9_Anchor_Covered_Causeway", "V9_Anchor_V8_Temple_Hub" };
            for (var index = 0; index < names.Length; index++)
            {
                var anchor = metadata.Find(names[index]);
                if (anchor == null || Vector3.Distance(anchor.position + Vector3.up * RouteAnchorPlayerHeight, Route[index]) > 0.001f)
                    return false;
            }
            return true;
        }

        private static float ExpectedRouteDistance()
        {
            var distance = 0f;
            for (var index = 1; index < Route.Length; index++) distance += Vector3.Distance(Route[index - 1], Route[index]);
            return distance;
        }

        private static bool ValidatePngPixels(string path, out float standardDeviation, out float range)
        {
            standardDeviation = 0f;
            range = 0f;
            var texture = new Texture2D(2, 2, TextureFormat.RGB24, false);
            try
            {
                if (!ImageConversion.LoadImage(texture, File.ReadAllBytes(path), false)) return false;
                var pixels = texture.GetPixels32();
                var count = 0;
                double sum = 0d;
                double squareSum = 0d;
                var minimum = 1f;
                var maximum = 0f;
                for (var y = 0; y < texture.height; y += 8)
                for (var x = 0; x < texture.width; x += 8)
                {
                    var color = pixels[y * texture.width + x];
                    var value = (0.2126f * color.r + 0.7152f * color.g + 0.0722f * color.b) / 255f;
                    minimum = Mathf.Min(minimum, value);
                    maximum = Mathf.Max(maximum, value);
                    sum += value;
                    squareSum += value * value;
                    count++;
                }
                var mean = count == 0 ? 0f : (float)(sum / count);
                var variance = count == 0 ? 0f : Mathf.Max(0f, (float)(squareSum / count) - mean * mean);
                standardDeviation = Mathf.Sqrt(variance);
                range = maximum - minimum;
                return texture.width >= 1280 && texture.height >= 720 && standardDeviation >= 0.03f && range >= 0.20f;
            }
            catch (Exception)
            {
                return false;
            }
            finally
            {
                Destroy(texture);
            }
        }

        private void Teleport(Transform player, Vector3 position)
        {
            controller.enabled = false;
            player.position = position;
            controller.enabled = true;
            Physics.SyncTransforms();
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
            return characters.Length == 0 ? "v9-causeway" : new string(characters);
        }

        private static string Sha256(string path)
        {
            using (var stream = File.OpenRead(path))
            using (var sha = SHA256.Create())
                return string.Concat(sha.ComputeHash(stream).Select(item => item.ToString("x2")));
        }

        private static string Vector(Vector3 value)
        {
            return value.x.ToString("F3", CultureInfo.InvariantCulture) + "," +
                   value.y.ToString("F3", CultureInfo.InvariantCulture) + "," +
                   value.z.ToString("F3", CultureInfo.InvariantCulture);
        }

        private sealed class CaptureRecord
        {
            public readonly string Stage;
            public readonly string Path;
            public readonly bool Ready;
            public readonly bool Fresh;
            public readonly bool Semantic;
            public readonly string Hash;
            public readonly float StandardDeviation;
            public readonly float Range;

            public CaptureRecord(string stage, string path, bool ready, bool fresh, bool semantic, string hash,
                float standardDeviation, float range)
            {
                Stage = stage;
                Path = path;
                Ready = ready;
                Fresh = fresh;
                Semantic = semantic;
                Hash = hash;
                StandardDeviation = standardDeviation;
                Range = range;
            }
        }
    }
}

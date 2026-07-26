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
    [DefaultExecutionOrder(335)]
    public sealed class KhufuV10TraversalProofProbe : MonoBehaviour
    {
        private const string V10RootName = "Runtime_Khufu_V10_Interior_Spine";
        private const string ExpectedBoundaryCollider =
            "V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary";
        private const string ErrorMetricMutationHit = "V10_ERROR_METRIC_OFFSET";
        private const float StepDistance = 0.28f;
        private const float MaximumStepError = 0.4f;
        private const float ErrorMetricMutationOffset = 0.75f;
        private const float FloorOffset = 0.08f;
        private const float GroundingStepCap = 0.35f;
        private const double RuntimeTimeoutSeconds = 25d;

        private readonly List<CaptureRecord> captures = new List<CaptureRecord>();
        private readonly List<MovementTraceRecord> movementTrace = new List<MovementTraceRecord>();
        private IReadOnlyList<Vector3> route;
        private TraitorEscapeMvpSession session;
        private CharacterController controller;
        private ChannelPlayerController playerController;
        private KhufuControllerHitRecorder hitRecorder;
        private ChannelFollowCamera followCamera;
        private Camera gameplayCamera;
        private Transform v10Root;
        private Collider[] dynamicColliders = Array.Empty<Collider>();
        private string outputRoot;
        private string label;
        private bool boundaryControl;
        private bool mutateErrorMetric;
        private bool errorMetricMutationObserved;
        private bool routeAnchorsValid;
        private bool started;
        private double startedAt;
        private float maximumError;
        private float traversedDistance;
        private float boundaryAttemptDistance;
        private float boundaryAdvance;
        private float maximumGroundingRequest;
        private float maximumGroundingApplied;
        private int reachedAnchors;
        private bool blocked;
        private string blockedHit = string.Empty;
        private string blockedGroundHit = string.Empty;
        private string blockedAmbiguousHit = string.Empty;
        private Vector3 blockedAt;
        private CollisionFlags blockedHorizontalFlags;
        private CollisionFlags blockedGroundingFlags;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v10-traversal-proof")) return;
            var host = new GameObject("KhufuV10_Traversal_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV10TraversalProofProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            route = KhufuV10RouteContract.NormalRoute();
            outputRoot = ArgumentValue("-khufu-v10-traversal-proof-output",
                Path.Combine(Application.persistentDataPath, "khufu-v10-traversal-proof"));
            label = Sanitize(ArgumentValue("-khufu-v10-traversal-proof-label", "v10-interior-final"));
            boundaryControl = HasArgument("-khufu-v10-traversal-proof-negative-boundary");
            mutateErrorMetric = HasArgument("-khufu-v10-traversal-proof-mutate-error-metric");
            Directory.CreateDirectory(outputRoot);
            startedAt = Time.realtimeSinceStartupAsDouble;
            if (boundaryControl && mutateErrorMetric)
            {
                FailAndQuit("boundary and error-metric controls are mutually exclusive");
                return;
            }
            Debug.Log("CHANNEL_PLAY_KHUFU_V10_TRAVERSAL_PROOF result=started label=" + label +
                      " mode=" + ProofMode());
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
            if (gameplayCamera != null && followCamera == null)
                followCamera = gameplayCamera.GetComponent<ChannelFollowCamera>();
            if (v10Root == null)
            {
                var root = GameObject.Find(V10RootName);
                v10Root = root == null ? null : root.transform;
            }
            if (session == null || session.DiagnosticPlayer == null || gameplayCamera == null ||
                followCamera == null || v10Root == null) return false;
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
            routeAnchorsValid = ValidateRouteAnchors();
            followCamera.SetTarget(player);

            if (boundaryControl) yield return RunBoundaryControl(player);
            else if (mutateErrorMetric) yield return RunErrorMetricControl(player);
            else yield return RunNormalTraversal(player);
            FinishAndQuit();
        }

        private IEnumerator RunNormalTraversal(Transform player)
        {
            Teleport(player, PlayerPoint(route[0], route[1], 0f));
            player.rotation = UprightLookRotation(route[1] - route[0]);
            followCamera.SetOffset(new Vector3(-4f, 3.2f, -6.5f));
            followCamera.SetLookAheadOffset(new Vector3(1.5f, 0.8f, 4f));
            reachedAnchors = 1;
            yield return new WaitForSecondsRealtime(1.25f);
            yield return Capture("north_entrance_start");

            for (var segment = 1; segment < route.Count && !blocked; segment++)
            {
                var start = route[segment - 1];
                var end = route[segment];
                var steps = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(start, end) / StepDistance));
                for (var step = 1; step <= steps; step++)
                {
                    var target = PlayerPoint(start, end, step / (float)steps);
                    var movement = MoveTowardRouteTarget(player, target, segment, step);
                    if (movement.Error > MaximumStepError)
                    {
                        blocked = true;
                        blockedHit = movement.BlockingHitName;
                        blockedGroundHit = movement.GroundHitName;
                        blockedAmbiguousHit = movement.AmbiguousHitName;
                        blockedAt = target;
                        blockedHorizontalFlags = movement.HorizontalFlags;
                        blockedGroundingFlags = movement.GroundingFlags;
                        break;
                    }
                    yield return null;
                }

                if (blocked) break;
                reachedAnchors++;
                if (segment == 6)
                {
                    followCamera.SetOffset(new Vector3(-1.5f, 3.8f, -4.5f));
                    followCamera.SetLookAheadOffset(new Vector3(0.9f, 1.1f, 2.6f));
                    yield return new WaitForSecondsRealtime(0.65f);
                    yield return Capture("great_step_stop");
                }
            }

            if (!blocked)
            {
                followCamera.SetOffset(new Vector3(4f, 3.2f, -6.5f));
                followCamera.SetLookAheadOffset(new Vector3(0f, 0.8f, 3f));
                yield return new WaitForSecondsRealtime(1f);
                yield return Capture("return_to_north_exit");
            }
        }

        private IEnumerator RunBoundaryControl(Transform player)
        {
            var rotation = KhufuV10RouteContract.GalleryRotation();
            var forward = rotation * Vector3.forward;
            var start = KhufuV10RouteContract.GreatStepStop() - forward * 0.35f;
            var end = KhufuV10RouteContract.GalleryTop + forward * 0.95f;
            var playerStart = PlayerPoint(start, end, 0f);
            var playerEnd = PlayerPoint(start, end, 1f);
            Teleport(player, playerStart);
            player.rotation = UprightLookRotation(forward);
            followCamera.SetOffset(new Vector3(-1.5f, 3.8f, -4.5f));
            followCamera.SetLookAheadOffset(new Vector3(0.9f, 1.1f, 2.6f));
            boundaryAttemptDistance = Vector3.Distance(playerStart, playerEnd);
            yield return new WaitForSecondsRealtime(1.25f);
            yield return Capture("great_step_control_start");

            var steps = Mathf.Max(1, Mathf.CeilToInt(boundaryAttemptDistance / 0.12f));
            for (var step = 1; step <= steps; step++)
            {
                var target = Vector3.Lerp(playerStart, playerEnd, step / (float)steps);
                var movement = MoveTowardRouteTarget(player, target, -1, step);
                if (movement.Error > MaximumStepError)
                {
                    blocked = true;
                    blockedHit = movement.BlockingHitName;
                    blockedGroundHit = movement.GroundHitName;
                    blockedAmbiguousHit = movement.AmbiguousHitName;
                    blockedAt = target;
                    blockedHorizontalFlags = movement.HorizontalFlags;
                    blockedGroundingFlags = movement.GroundingFlags;
                    break;
                }
                yield return null;
            }
            boundaryAdvance = Mathf.Max(0f, Vector3.Dot(player.position - playerStart, forward));
            yield return new WaitForSecondsRealtime(0.75f);
            yield return Capture("great_step_named_blocker");
        }

        private IEnumerator RunErrorMetricControl(Transform player)
        {
            var start = route[0];
            var end = route[1];
            Teleport(player, PlayerPoint(start, end, 0f));
            var movementTarget = PlayerPoint(start, end, 0.08f);
            MoveTowardRouteTarget(player, movementTarget, -2, 1);
            var evaluationTarget = movementTarget + Vector3.right * ErrorMetricMutationOffset;
            maximumError = Vector3.Distance(player.position, evaluationTarget);
            errorMetricMutationObserved = maximumError > MaximumStepError;
            blocked = errorMetricMutationObserved;
            blockedHit = errorMetricMutationObserved ? ErrorMetricMutationHit : string.Empty;
            blockedAt = evaluationTarget;
            yield return null;
        }

        private void FinishAndQuit()
        {
            var player = session.DiagnosticPlayer;
            var finalTarget = PlayerPoint(route[route.Count - 2], route[route.Count - 1], 1f);
            var finalError = Vector3.Distance(player.position, finalTarget);
            var v10Colliders = v10Root.GetComponentsInChildren<BoxCollider>(true).Count(item => item.enabled);
            var v10Renderers = v10Root.GetComponentsInChildren<Renderer>(true)
                .Count(item => item.enabled && item.gameObject.activeInHierarchy);
            var capturesReady = captures.All(item => item.Ready);
            var expectedCaptureCount = mutateErrorMetric ? 0 : boundaryControl ? 2 : 3;
            var expectedDistance = ExpectedRouteDistance();
            var normalPassed = !boundaryControl && !mutateErrorMetric && !blocked &&
                               finalError <= MaximumStepError && maximumError <= MaximumStepError &&
                               traversedDistance >= expectedDistance - 1f && reachedAnchors == route.Count &&
                               routeAnchorsValid && capturesReady && captures.Count == expectedCaptureCount &&
                               maximumGroundingRequest <= GroundingStepCap + 0.001f &&
                               v10Colliders == 70 && v10Renderers == 6;
            var boundaryPassed = boundaryControl && blocked && blockedHit == ExpectedBoundaryCollider &&
                                 (blockedHorizontalFlags & CollisionFlags.Sides) != 0 &&
                                 maximumError > MaximumStepError && boundaryAdvance < boundaryAttemptDistance - MaximumStepError &&
                                 routeAnchorsValid && capturesReady && captures.Count == expectedCaptureCount &&
                                 maximumGroundingRequest <= GroundingStepCap + 0.001f &&
                                 v10Colliders == 70 && v10Renderers == 6;
            var errorMetricPassed = mutateErrorMetric && blocked && errorMetricMutationObserved &&
                                    maximumError > MaximumStepError && blockedHit == ErrorMetricMutationHit &&
                                    routeAnchorsValid && captures.Count == expectedCaptureCount &&
                                    v10Colliders == 70 && v10Renderers == 6;
            var harnessPassed = mutateErrorMetric ? errorMetricPassed : boundaryControl ? boundaryPassed : normalPassed;
            WriteReceipt(harnessPassed, normalPassed, boundaryPassed, errorMetricPassed, finalError,
                v10Colliders, v10Renderers, null);
            Debug.Log("CHANNEL_PLAY_KHUFU_V10_TRAVERSAL_PROOF result=" +
                      (harnessPassed ? "passed" : "failed") + " mode=" + ProofMode() +
                      " blocked=" + blocked + " hit=" + blockedHit + " reached=" + reachedAnchors +
                      " max_error=" + maximumError.ToString("F3", CultureInfo.InvariantCulture));
            Application.Quit(harnessPassed ? 0 : 1);
        }

        private void FailAndQuit(string reason)
        {
            if (started) return;
            started = true;
            WriteReceipt(false, false, false, false, float.PositiveInfinity, 0, 0, reason);
            Debug.LogError("CHANNEL_PLAY_KHUFU_V10_TRAVERSAL_PROOF result=failed reason=\"" + reason + "\"");
            Application.Quit(1);
        }

        private void WriteReceipt(bool harnessPassed, bool normalPassed, bool boundaryPassed,
            bool errorMetricPassed, float finalError, int v10Colliders, int v10Renderers, string failure)
        {
            var text = new StringBuilder("# Khufu V10 Windows Player Traversal Proof\n\n");
            text.AppendLine("- Harness verdict: **" + (harnessPassed ? "passed" : "failed") + "**");
            text.AppendLine("- Mode: `" + ProofMode() + "`");
            text.AppendLine("- Normal round-trip proof: `" +
                            (normalPassed ? "passed" : boundaryControl || mutateErrorMetric ? "not-applicable" : "failed") + "`");
            text.AppendLine("- Great Step boundary control: `" +
                            (boundaryPassed ? "passed" : boundaryControl ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Error metric mutation proof: `" +
                            (errorMetricPassed ? "passed" : mutateErrorMetric ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Route: `North Entrance -> Gallery Foot -> Great Step -> Gallery Foot -> HYBRID Service Return -> North Exit`");
            text.AppendLine("- Serialized route anchors match runtime contract: `" + routeAnchorsValid + "`");
            text.AppendLine("- Reached route anchors: `" + reachedAnchors + "/" + route.Count + "`");
            text.AppendLine("- Expected route distance: `" + ExpectedRouteDistance().ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- CharacterController traversed distance: `" + traversedDistance.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Maximum step error: `" + maximumError.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Final target error: `" + finalError.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Boundary attempted / advanced: `" +
                            boundaryAttemptDistance.ToString("F3", CultureInfo.InvariantCulture) + " / " +
                            boundaryAdvance.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Grounding correction cap / maximum requested / maximum applied: `" +
                            GroundingStepCap.ToString("F3", CultureInfo.InvariantCulture) + " / " +
                            maximumGroundingRequest.ToString("F3", CultureInfo.InvariantCulture) + " / " +
                            maximumGroundingApplied.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Blocked: `" + blocked + "`");
            text.AppendLine("- Blocked collider: `" + (string.IsNullOrEmpty(blockedHit) ? "none" : blockedHit) + "`");
            text.AppendLine("- Blocked ground collider: `" +
                            (string.IsNullOrEmpty(blockedGroundHit) ? "none" : blockedGroundHit) + "`");
            text.AppendLine("- Blocked ambiguous collider: `" +
                            (string.IsNullOrEmpty(blockedAmbiguousHit) ? "none" : blockedAmbiguousHit) + "`");
            text.AppendLine("- Blocked horizontal / grounding flags: `" + blockedHorizontalFlags + " / " +
                            blockedGroundingFlags + "`");
            text.AppendLine("- Blocked target: `" + Vector(blockedAt) + "`");
            text.AppendLine("- V10 renderers / BoxColliders: `" + v10Renderers + " / " + v10Colliders + "`");
            text.AppendLine("- Resolution: `" + Screen.width + "x" + Screen.height + "`");
            var tracePath = WriteMovementTrace();
            text.AppendLine("- Movement trace: `" + tracePath.Replace('\\', '/') + "` / records `" +
                            movementTrace.Count + "` / SHA256 `" + Sha256(tracePath) + "`");
            foreach (var capture in captures)
                text.AppendLine("- Capture " + capture.Stage + ": `" + capture.Path.Replace('\\', '/') +
                                "` / ready `" + capture.Ready + "` / fresh `" + capture.Fresh +
                                "` / semantic `" + capture.Semantic + "` / stddev/range `" +
                                capture.StandardDeviation.ToString("F4", CultureInfo.InvariantCulture) + " / " +
                                capture.Range.ToString("F4", CultureInfo.InvariantCulture) + "` / SHA256 `" + capture.Hash + "`");
            if (!string.IsNullOrEmpty(failure)) text.AppendLine("- Failure: `" + failure + "`");
            text.AppendLine();
            text.AppendLine((mutateErrorMetric ? "V10_WINDOWS_PLAYER_ERROR_METRIC_MUTATION" :
                boundaryControl ? "V10_WINDOWS_PLAYER_BOUNDARY_CONTROL" : "V10_WINDOWS_PLAYER_TRAVERSAL") +
                            ": " + (harnessPassed ? "passed" : "failed"));
            var suffix = mutateErrorMetric ? "-error-metric-mutation.md" :
                boundaryControl ? "-boundary-control.md" : "-round-trip.md";
            File.WriteAllText(Path.Combine(outputRoot, label + suffix), text.ToString(), Encoding.UTF8);
        }

        private string ProofMode()
        {
            if (mutateErrorMetric) return "error-metric-negative-control";
            return boundaryControl ? "great-step-boundary-control" : "normal-round-trip";
        }

        private bool ValidateRouteAnchors()
        {
            var metadata = v10Root.Find("V10_Metadata");
            if (metadata == null) return false;
            var anchors = new Dictionary<string, Vector3>(StringComparer.Ordinal)
            {
                { "V10_Anchor_North_Entrance", KhufuV10RouteContract.Entrance },
                { "V10_Anchor_Ascending_Branch", KhufuV10RouteContract.Branch },
                { "V10_Anchor_Grand_Gallery_Foot", KhufuV10RouteContract.GalleryFoot },
                { "V10_Anchor_Great_Step_Stop", KhufuV10RouteContract.GreatStepStop() },
                { "V10_Anchor_Historic_Service_Mouth", KhufuV10RouteContract.HistoricServiceMouth() }
            };
            var returnPoints = KhufuV10RouteContract.HybridReturnPoints();
            for (var index = 0; index < returnPoints.Count; index++)
                anchors.Add("V10_Anchor_HYBRID_Return_" + index.ToString("D2"), returnPoints[index]);
            return anchors.All(item =>
            {
                var anchor = metadata.Find(item.Key);
                return anchor != null && Vector3.Distance(anchor.position, item.Value) <= 0.001f;
            });
        }

        private float ExpectedRouteDistance()
        {
            var distance = 0f;
            for (var index = 1; index < route.Count; index++)
                distance += Vector3.Distance(route[index - 1], route[index]);
            return distance;
        }

        private IEnumerator Capture(string stage)
        {
            yield return new WaitForEndOfFrame();
            var path = Path.Combine(outputRoot, label + "-" + ProofMode() + "-" + stage + ".png");
            if (File.Exists(path)) File.Delete(path);
            var requestedAt = DateTime.UtcNow;
            ScreenCapture.CaptureScreenshot(path, 1);
            var deadline = Time.realtimeSinceStartupAsDouble + 8d;
            while ((!File.Exists(path) || new FileInfo(path).Length < 65536) &&
                   Time.realtimeSinceStartupAsDouble < deadline) yield return null;
            var info = File.Exists(path) ? new FileInfo(path) : null;
            var fresh = info != null && info.LastWriteTimeUtc >= requestedAt.AddSeconds(-2d);
            var standardDeviation = 0f;
            var range = 0f;
            var semantic = fresh && ValidatePngPixels(path, out standardDeviation, out range);
            var ready = info != null && info.Length >= 65536 && fresh && semantic;
            captures.Add(new CaptureRecord(stage, path, ready, fresh, semantic,
                ready ? Sha256(path) : "missing", standardDeviation, range));
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

        private Vector3 PlayerPoint(Vector3 start, Vector3 end, float t)
        {
            var halfHeight = controller == null ? 1f : controller.height * 0.5f;
            return Vector3.Lerp(start, end, t) + Vector3.up * (halfHeight + FloorOffset);
        }

        private MovementResult MoveTowardRouteTarget(Transform player, Vector3 target, int segment, int step)
        {
            var before = player.position;
            var horizontalDelta = target - player.position;
            horizontalDelta.y = 0f;
            hitRecorder.Clear();
            var horizontalFlags = controller.Move(horizontalDelta);
            var horizontalSideHit = hitRecorder.LastSideHitName;
            var horizontalGroundHit = hitRecorder.LastGroundHitName;
            var horizontalAmbiguousHit = hitRecorder.LastAmbiguousHitName;
            var horizontalHit = !string.IsNullOrEmpty(horizontalSideHit)
                ? horizontalSideHit
                : !string.IsNullOrEmpty(horizontalAmbiguousHit) ? horizontalAmbiguousHit : hitRecorder.LastHitName;
            var afterHorizontal = player.position;

            var groundingRequest = Mathf.Min(GroundingStepCap, Mathf.Max(0f, player.position.y - target.y));
            hitRecorder.Clear();
            var groundingFlags = groundingRequest > 0f
                ? controller.Move(Vector3.down * groundingRequest)
                : CollisionFlags.None;
            var groundingSideHit = hitRecorder.LastSideHitName;
            var groundingGroundHit = hitRecorder.LastGroundHitName;
            var groundingAmbiguousHit = hitRecorder.LastAmbiguousHitName;
            var groundingHit = !string.IsNullOrEmpty(groundingGroundHit)
                ? groundingGroundHit
                : hitRecorder.LastHitName;
            var groundingApplied = Mathf.Max(0f, afterHorizontal.y - player.position.y);
            maximumGroundingRequest = Mathf.Max(maximumGroundingRequest, groundingRequest);
            maximumGroundingApplied = Mathf.Max(maximumGroundingApplied, groundingApplied);

            traversedDistance += Vector3.Distance(before, player.position);
            var error = Vector3.Distance(player.position, target);
            maximumError = Mathf.Max(maximumError, error);
            var blockingHitName = (horizontalFlags & CollisionFlags.Sides) != 0 ? horizontalHit : groundingHit;
            var groundHitName = !string.IsNullOrEmpty(groundingGroundHit)
                ? groundingGroundHit
                : horizontalGroundHit;
            var ambiguousHitName = !string.IsNullOrEmpty(horizontalAmbiguousHit)
                ? horizontalAmbiguousHit
                : groundingAmbiguousHit;
            movementTrace.Add(new MovementTraceRecord(segment, step, before, target, player.position, error,
                groundingRequest, groundingApplied, horizontalFlags, groundingFlags,
                horizontalSideHit, horizontalGroundHit, horizontalAmbiguousHit,
                groundingSideHit, groundingGroundHit, groundingAmbiguousHit));
            return new MovementResult(error, horizontalFlags, groundingFlags, blockingHitName,
                groundHitName, ambiguousHitName);
        }

        private string WriteMovementTrace()
        {
            var path = Path.Combine(outputRoot, label + "-" + ProofMode() + "-movement-trace.csv");
            var text = new StringBuilder();
            text.AppendLine("segment,step,before,target,after,error,grounding_requested,grounding_applied," +
                            "horizontal_flags,grounding_flags,horizontal_side_hit,horizontal_ground_hit," +
                            "horizontal_ambiguous_hit,grounding_side_hit,grounding_ground_hit," +
                            "grounding_ambiguous_hit");
            foreach (var item in movementTrace) text.AppendLine(item.ToCsv());
            File.WriteAllText(path, text.ToString(), Encoding.UTF8);
            return path;
        }

        private static Quaternion UprightLookRotation(Vector3 direction)
        {
            var horizontal = Vector3.ProjectOnPlane(direction, Vector3.up);
            return horizontal.sqrMagnitude > 0.0001f
                ? Quaternion.LookRotation(horizontal.normalized, Vector3.up)
                : Quaternion.identity;
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
            return Environment.GetCommandLineArgs()
                .Any(item => string.Equals(item, key, StringComparison.OrdinalIgnoreCase));
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
            return characters.Length == 0 ? "v10-interior" : new string(characters);
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

        private sealed class MovementResult
        {
            public readonly float Error;
            public readonly CollisionFlags HorizontalFlags;
            public readonly CollisionFlags GroundingFlags;
            public readonly string BlockingHitName;
            public readonly string GroundHitName;
            public readonly string AmbiguousHitName;

            public MovementResult(float error, CollisionFlags horizontalFlags, CollisionFlags groundingFlags,
                string blockingHitName, string groundHitName, string ambiguousHitName)
            {
                Error = error;
                HorizontalFlags = horizontalFlags;
                GroundingFlags = groundingFlags;
                BlockingHitName = blockingHitName;
                GroundHitName = groundHitName;
                AmbiguousHitName = ambiguousHitName;
            }
        }

        private sealed class MovementTraceRecord
        {
            private readonly int segment;
            private readonly int step;
            private readonly Vector3 before;
            private readonly Vector3 target;
            private readonly Vector3 after;
            private readonly float error;
            private readonly float groundingRequest;
            private readonly float groundingApplied;
            private readonly CollisionFlags horizontalFlags;
            private readonly CollisionFlags groundingFlags;
            private readonly string horizontalSideHit;
            private readonly string horizontalGroundHit;
            private readonly string horizontalAmbiguousHit;
            private readonly string groundingSideHit;
            private readonly string groundingGroundHit;
            private readonly string groundingAmbiguousHit;

            public MovementTraceRecord(int segment, int step, Vector3 before, Vector3 target, Vector3 after,
                float error, float groundingRequest, float groundingApplied, CollisionFlags horizontalFlags,
                CollisionFlags groundingFlags, string horizontalSideHit, string horizontalGroundHit,
                string horizontalAmbiguousHit, string groundingSideHit, string groundingGroundHit,
                string groundingAmbiguousHit)
            {
                this.segment = segment;
                this.step = step;
                this.before = before;
                this.target = target;
                this.after = after;
                this.error = error;
                this.groundingRequest = groundingRequest;
                this.groundingApplied = groundingApplied;
                this.horizontalFlags = horizontalFlags;
                this.groundingFlags = groundingFlags;
                this.horizontalSideHit = horizontalSideHit;
                this.horizontalGroundHit = horizontalGroundHit;
                this.horizontalAmbiguousHit = horizontalAmbiguousHit;
                this.groundingSideHit = groundingSideHit;
                this.groundingGroundHit = groundingGroundHit;
                this.groundingAmbiguousHit = groundingAmbiguousHit;
            }

            public string ToCsv()
            {
                return segment + "," + step + ",\"" + Vector(before) + "\",\"" + Vector(target) + "\",\"" +
                       Vector(after) + "\"," + error.ToString("F4", CultureInfo.InvariantCulture) + "," +
                       groundingRequest.ToString("F4", CultureInfo.InvariantCulture) + "," +
                       groundingApplied.ToString("F4", CultureInfo.InvariantCulture) + ",\"" + horizontalFlags +
                       "\",\"" + groundingFlags + "\",\"" + Csv(horizontalSideHit) + "\",\"" +
                       Csv(horizontalGroundHit) + "\",\"" + Csv(horizontalAmbiguousHit) + "\",\"" +
                       Csv(groundingSideHit) + "\",\"" + Csv(groundingGroundHit) + "\",\"" +
                       Csv(groundingAmbiguousHit) + "\"";
            }

            private static string Csv(string value)
            {
                return value.Replace("\"", "\"\"");
            }
        }
    }
}

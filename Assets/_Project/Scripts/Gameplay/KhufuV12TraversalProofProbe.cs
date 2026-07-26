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
    [DefaultExecutionOrder(337)]
    public sealed class KhufuV12TraversalProofProbe : MonoBehaviour
    {
        private const string RootName = "Runtime_Khufu_V12_Queen_Circuit";
        private const string ExpectedGate =
            "V10_PROXY_Queen_Branch_Threshold_Queen_Ownership_Gate";
        private const string NorthMouth =
            "V12_PROXY_Narrow_Mouth_Boundaries_North_Narrow_Mouth_Boundary";
        private const string SouthMouth =
            "V12_PROXY_Narrow_Mouth_Boundaries_South_Narrow_Mouth_Boundary";
        private const float NormalStep = 0.16f;
        private const float ControlStep = 0.08f;
        private const float MaximumError = 0.40f;
        private const float FloorOffset = 0.08f;
        private const double TimeoutSeconds = 25d;

        private readonly List<TraceRecord> trace = new List<TraceRecord>();
        private TraitorEscapeMvpSession session;
        private Transform root;
        private CharacterController controller;
        private ChannelPlayerController playerController;
        private KhufuV12ControllerHitRecorder hitRecorder;
        private KhufuV12TransitionControl transition;
        private ColliderState[] dynamicColliderStates = Array.Empty<ColliderState>();
        private IReadOnlyList<Vector3> route;
        private string outputRoot;
        private string label;
        private bool boundaryControl;
        private bool started;
        private double startedAt;
        private int reachedAnchors;
        private int movementSteps;
        private int groundedSteps;
        private float maximumError;
        private float traversedDistance;
        private float maximumRequestedStep;
        private bool blocked;
        private string blockedHit = string.Empty;
        private CollisionFlags blockedFlags;
        private bool preMoveOverlapEmpty;
        private float boundaryStartDistance;
        private int boundaryMoveFrame = -1;
        private int boundaryCallbackFrame = -1;
        private bool controlPredecessorBound;
        private bool controlGateEnabled;
        private bool northMouthSealed;
        private bool southMouthSealed;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v12-traversal-proof")) return;
            var host = new GameObject("KhufuV12_Traversal_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV12TraversalProofProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            route = KhufuV12QueenRouteContract.RoundTripRoute();
            outputRoot = ArgumentValue("-khufu-v12-traversal-proof-output",
                Path.Combine(Application.persistentDataPath, "khufu-v12-traversal-proof"));
            label = Sanitize(ArgumentValue("-khufu-v12-traversal-proof-label", "v12-queen-final"));
            boundaryControl = HasArgument("-khufu-v12-traversal-proof-negative-boundary");
            Directory.CreateDirectory(outputRoot);
            startedAt = Time.realtimeSinceStartupAsDouble;
            Debug.Log("CHANNEL_PLAY_KHUFU_V12_TRAVERSAL_PROOF result=started mode=" + Mode());
        }

        private void LateUpdate()
        {
            if (started) return;
            if (!ResolveRuntime())
            {
                if (Time.realtimeSinceStartupAsDouble - startedAt > TimeoutSeconds)
                    FailAndQuit("runtime did not become ready");
                return;
            }
            started = true;
            StartCoroutine(RunProof());
        }

        private bool ResolveRuntime()
        {
            if (session == null) session = FindAnyObjectByType<TraitorEscapeMvpSession>();
            if (root == null)
            {
                var target = GameObject.Find(RootName);
                root = target == null ? null : target.transform;
            }
            if (session == null || session.DiagnosticPlayer == null || root == null) return false;
            controller = session.DiagnosticPlayer.GetComponent<CharacterController>();
            transition = root.GetComponentInChildren<KhufuV12TransitionControl>(true);
            return controller != null && transition != null && transition.GraniteFilter != null &&
                   transition.PredecessorGranite != null && transition.SuccessorGranite != null &&
                   transition.QueenGate != null;
        }

        private IEnumerator RunProof()
        {
            var player = session.DiagnosticPlayer;
            playerController = player.GetComponent<ChannelPlayerController>();
            hitRecorder = player.GetComponent<KhufuV12ControllerHitRecorder>();
            if (hitRecorder == null) hitRecorder = player.gameObject.AddComponent<KhufuV12ControllerHitRecorder>();
            dynamicColliderStates = FindObjectsByType<Collider>(FindObjectsSortMode.None)
                .Where(item => item.name.StartsWith("Runtime_Bot_", StringComparison.Ordinal))
                .Select(item => new ColliderState(item, item.enabled)).ToArray();
            foreach (var item in dynamicColliderStates) item.Collider.enabled = false;
            if (playerController != null) playerController.enabled = false;

            var originalGranite = transition.GraniteFilter.sharedMesh;
            var originalGate = transition.QueenGate.enabled;
            try
            {
                transition.GraniteFilter.sharedMesh = boundaryControl
                    ? transition.PredecessorGranite
                    : transition.SuccessorGranite;
                transition.QueenGate.enabled = boundaryControl;
                Physics.SyncTransforms();
                if (boundaryControl) yield return RunBoundaryControl(player);
                else yield return RunNormal(player);
            }
            finally
            {
                transition.GraniteFilter.sharedMesh = originalGranite;
                transition.QueenGate.enabled = originalGate;
                Physics.SyncTransforms();
            }
            FinishAndQuit();
        }

        private IEnumerator RunNormal(Transform player)
        {
            Teleport(player, PlayerPoint(route[0]));
            player.rotation = UprightLookRotation(route[1] - route[0]);
            reachedAnchors = 1;
            yield return new WaitForSecondsRealtime(0.35f);
            for (var segment = 1; segment < route.Count && !blocked; segment++)
            {
                var start = route[segment - 1];
                var end = route[segment];
                var steps = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(start, end) / NormalStep));
                for (var step = 1; step <= steps; step++)
                {
                    var target = PlayerPoint(Vector3.Lerp(start, end, step / (float)steps));
                    var before = player.position;
                    var request = target - player.position;
                    request.y = 0f;
                    if (request.magnitude > NormalStep) request = request.normalized * NormalStep;
                    maximumRequestedStep = Mathf.Max(maximumRequestedStep, request.magnitude);
                    hitRecorder.ClearFrame();
                    var frame = Time.frameCount;
                    var flags = controller.Move(request);
                    var sideHit = hitRecorder.LastSideHitName;
                    var callbackFrame = hitRecorder.LastSideHitFrame;
                    var grounding = Mathf.Min(0.25f, Mathf.Max(0.08f, player.position.y - target.y));
                    var groundFlags = controller.Move(Vector3.down * grounding);
                    if ((groundFlags & CollisionFlags.Below) != 0 || controller.isGrounded) groundedSteps++;
                    movementSteps++;
                    traversedDistance += Vector3.Distance(before, player.position);
                    var error = Vector3.Distance(player.position, target);
                    maximumError = Mathf.Max(maximumError, error);
                    trace.Add(new TraceRecord(segment, step, frame, before, target, player.position,
                        request.magnitude, error, flags, sideHit, callbackFrame));
                    if (error > MaximumError)
                    {
                        blocked = true;
                        blockedHit = sideHit;
                        blockedFlags = flags;
                        break;
                    }
                    yield return null;
                }
                if (!blocked) reachedAnchors++;
            }
            ValidateMouthBoundaries();
        }

        private IEnumerator RunBoundaryControl(Transform player)
        {
            controlPredecessorBound = transition.GraniteFilter.sharedMesh == transition.PredecessorGranite;
            controlGateEnabled = transition.QueenGate.enabled;
            var direction = KhufuV12QueenRouteContract.ThresholdDirection;
            var offset = KhufuV12QueenRouteContract.ThresholdRight * 0.30f;
            var start = KhufuV12QueenRouteContract.ThresholdCenter - direction * 1.70f + offset;
            var end = KhufuV12QueenRouteContract.ThresholdCenter + direction * 0.65f + offset;
            boundaryStartDistance = Vector3.Distance(start, KhufuV12QueenRouteContract.ThresholdCenter);
            Teleport(player, PlayerPoint(start));
            player.rotation = UprightLookRotation(direction);
            yield return new WaitForSecondsRealtime(0.25f);

            ControllerCapsule(out var top, out var bottom, out var radius);
            var overlaps = Physics.OverlapCapsule(top, bottom, radius, ~0, QueryTriggerInteraction.Ignore)
                .Where(item => item != controller).Select(item => item.name)
                .Distinct(StringComparer.Ordinal).ToArray();
            preMoveOverlapEmpty = overlaps.Length == 0;

            var maximumSteps = Mathf.CeilToInt(Vector3.Distance(start, end) / ControlStep) + 2;
            for (var step = 1; step <= maximumSteps && !blocked; step++)
            {
                var remaining = Vector3.ProjectOnPlane(PlayerPoint(end) - player.position, Vector3.up);
                if (remaining.magnitude <= 0.001f) break;
                var request = remaining.normalized * Mathf.Min(ControlStep, remaining.magnitude);
                maximumRequestedStep = Mathf.Max(maximumRequestedStep, request.magnitude);
                var before = player.position;
                hitRecorder.ClearFrame();
                var moveFrame = Time.frameCount;
                var flags = controller.Move(request);
                var error = Vector3.Distance(player.position, PlayerPoint(end));
                trace.Add(new TraceRecord(1, step, moveFrame, before, PlayerPoint(end), player.position,
                    request.magnitude, error, flags, hitRecorder.LastSideHitName,
                    hitRecorder.LastSideHitFrame));
                if ((flags & CollisionFlags.Sides) != 0)
                {
                    blocked = true;
                    blockedHit = hitRecorder.LastSideHitName;
                    blockedFlags = flags;
                    boundaryMoveFrame = moveFrame;
                    boundaryCallbackFrame = hitRecorder.LastSideHitFrame;
                }
                yield return null;
            }
        }

        private void ValidateMouthBoundaries()
        {
            northMouthSealed = CastMouth(new Vector3(-3.15f, 5.35f, -2.0f), NorthMouth);
            southMouthSealed = CastMouth(new Vector3(-0.45f, 5.35f, -2.0f), SouthMouth);
        }

        private bool CastMouth(Vector3 floorPoint, string expected)
        {
            var center = PlayerPoint(floorPoint);
            CapsuleAt(center, out var top, out var bottom, out var radius);
            var overlapEmpty = !Physics.OverlapCapsule(top, bottom, radius, ~0,
                    QueryTriggerInteraction.Ignore)
                .Any(item => item != controller);
            var hits = Physics.CapsuleCastAll(top, bottom, radius, Vector3.forward, 1.65f, ~0,
                    QueryTriggerInteraction.Ignore)
                .Where(item => item.collider != controller)
                .OrderBy(item => item.distance).ToArray();
            return overlapEmpty && hits.Length > 0 && hits[0].collider.name == expected;
        }

        private void FinishAndQuit()
        {
            var groundedFraction = movementSteps == 0 ? 0f : groundedSteps / (float)movementSteps;
            var anchorsValid = ValidateAnchors();
            var rootColliders = root.GetComponentsInChildren<BoxCollider>(true).Count(item => item.enabled);
            var rootRenderers = root.GetComponentsInChildren<Renderer>(true)
                .Count(item => item.enabled && item.gameObject.activeInHierarchy);
            var finalError = boundaryControl ? float.NaN :
                Vector3.Distance(session.DiagnosticPlayer.position, PlayerPoint(route[route.Count - 1]));
            var normalPassed = !boundaryControl && !blocked && reachedAnchors == route.Count &&
                               maximumError <= MaximumError && finalError <= MaximumError &&
                               groundedFraction >= 0.90f && anchorsValid &&
                               rootColliders == 22 && rootRenderers == 5 &&
                               northMouthSealed && southMouthSealed &&
                               !hitRecorder.SeenHitNames.Contains(ExpectedGate);
            var boundaryPassed = boundaryControl && blocked && blockedHit == ExpectedGate &&
                                 (blockedFlags & CollisionFlags.Sides) != 0 &&
                                 boundaryStartDistance >= 1.5f && preMoveOverlapEmpty &&
                                 maximumRequestedStep <= 0.1001f &&
                                 boundaryMoveFrame >= 0 &&
                                 boundaryCallbackFrame == boundaryMoveFrame &&
                                 controlPredecessorBound && controlGateEnabled;
            var passed = boundaryControl ? boundaryPassed : normalPassed;
            WriteReceipt(passed, normalPassed, boundaryPassed, finalError, groundedFraction,
                anchorsValid, rootColliders, rootRenderers, null);
            RestoreRuntime();
            Debug.Log("CHANNEL_PLAY_KHUFU_V12_TRAVERSAL_PROOF result=" +
                      (passed ? "passed" : "failed") + " mode=" + Mode() +
                      " reached=" + reachedAnchors + "/" + route.Count + " hit=" + blockedHit +
                      " callback_frame=" + boundaryCallbackFrame);
            Application.Quit(passed ? 0 : 1);
        }

        private void FailAndQuit(string reason)
        {
            if (started) return;
            started = true;
            WriteReceipt(false, false, false, float.PositiveInfinity, 0f,
                false, 0, 0, reason);
            RestoreRuntime();
            Debug.LogError("CHANNEL_PLAY_KHUFU_V12_TRAVERSAL_PROOF result=failed reason=\"" + reason + "\"");
            Application.Quit(1);
        }

        private void WriteReceipt(bool passed, bool normalPassed, bool boundaryPassed, float finalError,
            float groundedFraction, bool anchorsValid, int rootColliders, int rootRenderers, string failure)
        {
            var tracePath = WriteTrace();
            var text = new StringBuilder("# Khufu V12 Windows Player Traversal Proof\n\n");
            text.AppendLine("- Harness verdict: **" + (passed ? "passed" : "failed") + "**");
            text.AppendLine("- Mode: `" + Mode() + "`");
            text.AppendLine("- Normal Queen round trip: `" +
                            (normalPassed ? "passed" : boundaryControl ? "not-applicable" : "failed") + "`");
            text.AppendLine("- V11-granite Queen-gate control: `" +
                            (boundaryPassed ? "passed" : boundaryControl ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Reached route anchors: `" + reachedAnchors + "/" + route.Count + "`");
            text.AppendLine("- Serialized anchors match: `" + anchorsValid + "`");
            text.AppendLine("- Traversed distance / max error / final error: `" +
                            Float(traversedDistance) + " / " + Float(maximumError) + " / " + Float(finalError) + "`");
            text.AppendLine("- Grounded steps/fraction: `" + groundedSteps + "/" + movementSteps + " / " +
                            Float(groundedFraction) + "`");
            text.AppendLine("- Root renderers / enabled colliders: `" + rootRenderers + " / " + rootColliders + "`");
            text.AppendLine("- CharacterController radius / height / stepOffset / skinWidth: `" +
                            Float(controller.radius) + " / " + Float(controller.height) + " / " +
                            Float(controller.stepOffset) + " / " + Float(controller.skinWidth) + "`");
            text.AppendLine("- Queen gate seen during normal route: `" +
                            hitRecorder.SeenHitNames.Contains(ExpectedGate) + "`");
            text.AppendLine("- Narrow mouths sealed (north/south): `" +
                            northMouthSealed + " / " + southMouthSealed + "`");
            text.AppendLine("- Control boundary start distance: `" + Float(boundaryStartDistance) + " m`");
            text.AppendLine("- Control pre-Move overlap empty: `" + preMoveOverlapEmpty + "`");
            text.AppendLine("- Control maximum requested step: `" + Float(maximumRequestedStep) + " m`");
            text.AppendLine("- Control blocked collider / flags: `" + Empty(blockedHit) + " / " + blockedFlags + "`");
            text.AppendLine("- Control Move / callback frame: `" +
                            boundaryMoveFrame + " / " + boundaryCallbackFrame + "`");
            text.AppendLine("- Control predecessor granite rebound: `" +
                            controlPredecessorBound + "`");
            text.AppendLine("- Control Queen proxy enabled: `" + controlGateEnabled + "`");
            text.AppendLine("- Movement trace: `" + tracePath.Replace('\\', '/') + "` / records `" +
                            trace.Count + "` / SHA256 `" + Sha256(tracePath) + "`");
            text.AppendLine("- Assembly-CSharp SHA256: `" +
                            Sha256(Path.Combine(Application.dataPath, "Managed", "Assembly-CSharp.dll")) + "`");
            if (!string.IsNullOrEmpty(failure)) text.AppendLine("- Failure: `" + failure + "`");
            text.AppendLine();
            text.AppendLine((boundaryControl ? "V12_WINDOWS_PLAYER_BOUNDARY_CONTROL" :
                "V12_WINDOWS_PLAYER_TRAVERSAL") + ": " + (passed ? "passed" : "failed"));
            var suffix = boundaryControl ? "-boundary-control.md" : "-round-trip.md";
            File.WriteAllText(Path.Combine(outputRoot, label + suffix), text.ToString(), Encoding.UTF8);
        }

        private bool ValidateAnchors()
        {
            var metadata = root.Find("V12_Metadata");
            if (metadata == null) return false;
            var anchors = new Dictionary<string, Vector3>(StringComparer.Ordinal)
            {
                { "V12_Anchor_Gallery_Foot", KhufuV12QueenRouteContract.GalleryFoot },
                { "V12_Anchor_Queen_Threshold", KhufuV12QueenRouteContract.ThresholdCenter },
                { "V12_Anchor_Passage_Turn", KhufuV12QueenRouteContract.PassageTurn },
                { "V12_Anchor_Chamber_Door", KhufuV12QueenRouteContract.ChamberDoor },
                { "V12_Anchor_Queens_Chamber", KhufuV12QueenRouteContract.ChamberCenter },
                { "V12_Anchor_East_Wall_Niche", KhufuV12QueenRouteContract.NicheStop }
            };
            return anchors.All(item =>
            {
                var anchor = metadata.Find(item.Key);
                return anchor != null && Vector3.Distance(anchor.position, item.Value) <= 0.001f;
            });
        }

        private Vector3 PlayerPoint(Vector3 floorPoint)
        {
            return floorPoint + Vector3.up * (controller.height * 0.5f + FloorOffset);
        }

        private void Teleport(Transform player, Vector3 position)
        {
            controller.enabled = false;
            player.position = position;
            controller.enabled = true;
            Physics.SyncTransforms();
        }

        private void ControllerCapsule(out Vector3 top, out Vector3 bottom, out float radius)
        {
            CapsuleAt(controller.transform.position, out top, out bottom, out radius);
        }

        private void CapsuleAt(Vector3 centerPosition, out Vector3 top, out Vector3 bottom, out float radius)
        {
            var scale = controller.transform.lossyScale;
            radius = controller.radius * Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z));
            var height = Mathf.Max(controller.height * Mathf.Abs(scale.y), radius * 2f);
            var centerOffset = controller.transform.rotation *
                               Vector3.Scale(controller.center, controller.transform.lossyScale);
            var center = centerPosition + centerOffset;
            var halfSegment = Mathf.Max(0f, height * 0.5f - radius);
            top = center + Vector3.up * halfSegment;
            bottom = center - Vector3.up * halfSegment;
        }

        private string WriteTrace()
        {
            var path = Path.Combine(outputRoot, label + "-" + Mode() + "-movement-trace.csv");
            var text = new StringBuilder(
                "segment,step,move_frame,before,target,after,request,error,flags,side_hit,callback_frame\n");
            foreach (var item in trace) text.AppendLine(item.ToCsv());
            File.WriteAllText(path, text.ToString(), Encoding.UTF8);
            return path;
        }

        private void RestoreRuntime()
        {
            foreach (var item in dynamicColliderStates)
                if (item.Collider != null) item.Collider.enabled = item.Enabled;
            if (playerController != null) playerController.enabled = true;
        }

        private string Mode()
        {
            return boundaryControl ? "queen-boundary-control" : "normal-round-trip";
        }

        private static Quaternion UprightLookRotation(Vector3 direction)
        {
            var horizontal = Vector3.ProjectOnPlane(direction, Vector3.up);
            return horizontal.sqrMagnitude > 0.0001f
                ? Quaternion.LookRotation(horizontal.normalized, Vector3.up)
                : Quaternion.identity;
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
                if (string.Equals(arguments[index], key, StringComparison.OrdinalIgnoreCase))
                    return arguments[index + 1];
            return fallback;
        }

        private static string Sanitize(string value)
        {
            var invalid = Path.GetInvalidFileNameChars();
            return new string(value.Select(character => invalid.Contains(character) ? '_' : character).ToArray());
        }

        private static string Sha256(string path)
        {
            if (!File.Exists(path)) return "missing";
            using (var stream = File.OpenRead(path))
            using (var hash = SHA256.Create())
                return string.Concat(hash.ComputeHash(stream).Select(item => item.ToString("x2")));
        }

        private static string Float(float value)
        {
            return value.ToString("F3", CultureInfo.InvariantCulture);
        }

        private static string Empty(string value)
        {
            return string.IsNullOrEmpty(value) ? "none" : value;
        }

        private readonly struct ColliderState
        {
            public readonly Collider Collider;
            public readonly bool Enabled;

            public ColliderState(Collider collider, bool enabled)
            {
                Collider = collider;
                Enabled = enabled;
            }
        }

        private readonly struct TraceRecord
        {
            private readonly int segment;
            private readonly int step;
            private readonly int moveFrame;
            private readonly Vector3 before;
            private readonly Vector3 target;
            private readonly Vector3 after;
            private readonly float request;
            private readonly float error;
            private readonly CollisionFlags flags;
            private readonly string sideHit;
            private readonly int callbackFrame;

            public TraceRecord(int segment, int step, int moveFrame, Vector3 before, Vector3 target,
                Vector3 after, float request, float error, CollisionFlags flags, string sideHit,
                int callbackFrame)
            {
                this.segment = segment;
                this.step = step;
                this.moveFrame = moveFrame;
                this.before = before;
                this.target = target;
                this.after = after;
                this.request = request;
                this.error = error;
                this.flags = flags;
                this.sideHit = sideHit;
                this.callbackFrame = callbackFrame;
            }

            public string ToCsv()
            {
                return string.Join(",",
                    segment.ToString(CultureInfo.InvariantCulture),
                    step.ToString(CultureInfo.InvariantCulture),
                    moveFrame.ToString(CultureInfo.InvariantCulture),
                    Quote(before), Quote(target), Quote(after),
                    request.ToString("F4", CultureInfo.InvariantCulture),
                    error.ToString("F4", CultureInfo.InvariantCulture),
                    Quote(flags.ToString()), Quote(sideHit),
                    callbackFrame.ToString(CultureInfo.InvariantCulture));
            }

            private static string Quote(Vector3 value)
            {
                return Quote(value.x.ToString("F4", CultureInfo.InvariantCulture) + "|" +
                             value.y.ToString("F4", CultureInfo.InvariantCulture) + "|" +
                             value.z.ToString("F4", CultureInfo.InvariantCulture));
            }

            private static string Quote(string value)
            {
                return "\"" + (value ?? string.Empty).Replace("\"", "\"\"") + "\"";
            }
        }
    }
}

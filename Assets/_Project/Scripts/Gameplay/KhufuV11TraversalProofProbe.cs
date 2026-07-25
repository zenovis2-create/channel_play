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
    [DefaultExecutionOrder(336)]
    public sealed class KhufuV11TraversalProofProbe : MonoBehaviour
    {
        private const string V11RootName = "Runtime_Khufu_V11_Royal_Circuit";
        private const string ExpectedBoundaryCollider =
            "V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary";
        private const float StepDistance = 0.20f;
        private const float MaximumStepError = 0.40f;
        private const float GroundingProbe = 0.08f;
        private const float GroundingStepCap = 0.35f;
        private const float FloorOffset = 0.08f;
        private const double RuntimeTimeoutSeconds = 25d;

        private readonly List<MovementTraceRecord> movementTrace = new List<MovementTraceRecord>();
        private IReadOnlyList<Vector3> route;
        private TraitorEscapeMvpSession session;
        private CharacterController controller;
        private ChannelPlayerController playerController;
        private KhufuControllerHitRecorder hitRecorder;
        private Transform v11Root;
        private BoxCollider boundaryCollider;
        private Collider[] dynamicColliders = Array.Empty<Collider>();
        private string outputRoot;
        private string label;
        private bool boundaryControl;
        private bool started;
        private double startedAt;
        private float maximumError;
        private float traversedDistance;
        private int reachedAnchors;
        private int groundedSteps;
        private int movementSteps;
        private bool blocked;
        private string blockedHit = string.Empty;
        private string blockedGroundHit = string.Empty;
        private string blockedAmbiguousHit = string.Empty;
        private string boundaryContactProof = string.Empty;
        private CollisionFlags blockedHorizontalFlags;
        private CollisionFlags blockedGroundingFlags;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v11-traversal-proof")) return;
            var host = new GameObject("KhufuV11_Traversal_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV11TraversalProofProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            route = BuildRoundTrip();
            outputRoot = ArgumentValue("-khufu-v11-traversal-proof-output",
                Path.Combine(Application.persistentDataPath, "khufu-v11-traversal-proof"));
            label = Sanitize(ArgumentValue("-khufu-v11-traversal-proof-label", "v11-royal-final"));
            boundaryControl = HasArgument("-khufu-v11-traversal-proof-negative-boundary");
            Directory.CreateDirectory(outputRoot);
            startedAt = Time.realtimeSinceStartupAsDouble;
            Debug.Log("CHANNEL_PLAY_KHUFU_V11_TRAVERSAL_PROOF result=started mode=" + ProofMode());
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
            if (v11Root == null)
            {
                var root = GameObject.Find(V11RootName);
                v11Root = root == null ? null : root.transform;
            }
            if (boundaryCollider == null)
                boundaryCollider = FindObjectsByType<BoxCollider>(
                        FindObjectsInactive.Include, FindObjectsSortMode.None)
                    .FirstOrDefault(item => item.name == ExpectedBoundaryCollider);
            if (session == null || session.DiagnosticPlayer == null || v11Root == null ||
                boundaryCollider == null) return false;
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

            var originalBlockerState = boundaryCollider.enabled;
            boundaryCollider.enabled = boundaryControl;
            Physics.SyncTransforms();
            yield return RunTraversal(player);
            boundaryCollider.enabled = originalBlockerState;
            Physics.SyncTransforms();
            FinishAndQuit();
        }

        private IEnumerator RunTraversal(Transform player)
        {
            Teleport(player, PlayerPoint(route[0], route[1], 0f));
            player.rotation = UprightLookRotation(route[1] - route[0]);
            reachedAnchors = 1;
            yield return new WaitForSecondsRealtime(0.5f);

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
                        blockedHorizontalFlags = movement.HorizontalFlags;
                        blockedGroundingFlags = movement.GroundingFlags;
                        break;
                    }
                    yield return null;
                }
                if (!blocked) reachedAnchors++;
            }
        }

        private void FinishAndQuit()
        {
            var player = session.DiagnosticPlayer;
            var finalTarget = PlayerPoint(route[route.Count - 2], route[route.Count - 1], 1f);
            var finalError = Vector3.Distance(player.position, finalTarget);
            var expectedDistance = ExpectedRouteDistance();
            var groundedFraction = movementSteps == 0 ? 0f : groundedSteps / (float)movementSteps;
            var anchorsValid = ValidateRouteAnchors();
            var v11Colliders = v11Root.GetComponentsInChildren<BoxCollider>(true).Count(item => item.enabled);
            var v11Renderers = v11Root.GetComponentsInChildren<Renderer>(true)
                .Count(item => item.enabled && item.gameObject.activeInHierarchy);
            var normalPassed = !boundaryControl && !blocked && reachedAnchors == route.Count &&
                               finalError <= MaximumStepError && maximumError <= MaximumStepError &&
                               traversedDistance >= expectedDistance - 1f && groundedFraction >= 0.90f &&
                               anchorsValid && v11Colliders == 33 && v11Renderers == 5;
            var boundaryPassed = boundaryControl && blocked && blockedHit == ExpectedBoundaryCollider &&
                                 (blockedHorizontalFlags & CollisionFlags.Sides) != 0 &&
                                 reachedAnchors < route.Count && maximumError > MaximumStepError &&
                                 anchorsValid && v11Colliders == 33 && v11Renderers == 5;
            var passed = boundaryControl ? boundaryPassed : normalPassed;
            WriteReceipt(passed, normalPassed, boundaryPassed, finalError, expectedDistance,
                groundedFraction, anchorsValid, v11Colliders, v11Renderers, null);
            RestoreRuntime();
            Debug.Log("CHANNEL_PLAY_KHUFU_V11_TRAVERSAL_PROOF result=" +
                      (passed ? "passed" : "failed") + " mode=" + ProofMode() +
                      " reached=" + reachedAnchors + "/" + route.Count + " hit=" + blockedHit +
                      " max_error=" + maximumError.ToString("F3", CultureInfo.InvariantCulture));
            Application.Quit(passed ? 0 : 1);
        }

        private void FailAndQuit(string reason)
        {
            if (started) return;
            started = true;
            WriteReceipt(false, false, false, float.PositiveInfinity, 0f, 0f,
                false, 0, 0, reason);
            RestoreRuntime();
            Debug.LogError("CHANNEL_PLAY_KHUFU_V11_TRAVERSAL_PROOF result=failed reason=\"" + reason + "\"");
            Application.Quit(1);
        }

        private void WriteReceipt(bool passed, bool normalPassed, bool boundaryPassed, float finalError,
            float expectedDistance, float groundedFraction, bool anchorsValid, int v11Colliders,
            int v11Renderers, string failure)
        {
            var tracePath = WriteMovementTrace();
            var text = new StringBuilder("# Khufu V11 Windows Player Traversal Proof\n\n");
            text.AppendLine("- Harness verdict: **" + (passed ? "passed" : "failed") + "**");
            text.AppendLine("- Mode: `" + ProofMode() + "`");
            text.AppendLine("- Normal royal round trip: `" +
                            (normalPassed ? "passed" : boundaryControl ? "not-applicable" : "failed") + "`");
            text.AppendLine("- Great Step blocker-enabled control: `" +
                            (boundaryPassed ? "passed" : boundaryControl ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Route: `V10 Great Step stop -> Royal Threshold -> Antechamber -> King's Chamber -> return`");
            text.AppendLine("- Serialized route anchors match runtime contract: `" + anchorsValid + "`");
            text.AppendLine("- Reached route anchors: `" + reachedAnchors + "/" + route.Count + "`");
            text.AppendLine("- Expected / traversed distance: `" +
                            expectedDistance.ToString("F3", CultureInfo.InvariantCulture) + " / " +
                            traversedDistance.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Maximum / final target error: `" +
                            maximumError.ToString("F3", CultureInfo.InvariantCulture) + " / " +
                            finalError.ToString("F3", CultureInfo.InvariantCulture) + " m`");
            text.AppendLine("- Grounded steps: `" + groundedSteps + "/" + movementSteps + "` / fraction `" +
                            groundedFraction.ToString("F3", CultureInfo.InvariantCulture) + "`");
            text.AppendLine("- Blocked collider: `" + Empty(blockedHit) + "`");
            text.AppendLine("- Named boundary contact proof: `" + Empty(boundaryContactProof) + "`");
            text.AppendLine("- Blocked ground / ambiguous collider: `" + Empty(blockedGroundHit) + " / " +
                            Empty(blockedAmbiguousHit) + "`");
            text.AppendLine("- Blocked horizontal / grounding flags: `" + FormatFlags(blockedHorizontalFlags) + " / " +
                            FormatFlags(blockedGroundingFlags) + "`");
            text.AppendLine("- CharacterController radius / height / stepOffset / skinWidth: `" +
                            Float(controller == null ? 0f : controller.radius) + " / " +
                            Float(controller == null ? 0f : controller.height) + " / " +
                            Float(controller == null ? 0f : controller.stepOffset) + " / " +
                            Float(controller == null ? 0f : controller.skinWidth) + "`");
            text.AppendLine("- Static validator capsule radius / ignored-lip threshold: `0.320 / 0.300`");
            text.AppendLine("- V11 renderers / enabled BoxColliders: `" + v11Renderers + " / " + v11Colliders + "`");
            text.AppendLine("- Assembly-CSharp SHA256: `" +
                            Sha256(Path.Combine(Application.dataPath, "Managed", "Assembly-CSharp.dll")) + "`");
            text.AppendLine("- Movement trace: `" + tracePath.Replace('\\', '/') + "` / records `" +
                            movementTrace.Count + "` / SHA256 `" + Sha256(tracePath) + "`");
            if (!string.IsNullOrEmpty(failure)) text.AppendLine("- Failure: `" + failure + "`");
            text.AppendLine();
            text.AppendLine((boundaryControl ? "V11_WINDOWS_PLAYER_BOUNDARY_CONTROL" :
                "V11_WINDOWS_PLAYER_TRAVERSAL") + ": " + (passed ? "passed" : "failed"));
            var suffix = boundaryControl ? "-boundary-control.md" : "-round-trip.md";
            File.WriteAllText(Path.Combine(outputRoot, label + suffix), text.ToString(), Encoding.UTF8);
        }

        private MovementResult MoveTowardRouteTarget(Transform player, Vector3 target, int segment, int step)
        {
            var before = player.position;
            var horizontalDelta = target - player.position;
            horizontalDelta.y = 0f;
            var namedBoundaryContact = BoundaryContact(horizontalDelta);
            hitRecorder.Clear();
            var horizontalFlags = controller.Move(horizontalDelta);
            var horizontalSideHit = hitRecorder.LastSideHitName;
            var horizontalGroundHit = hitRecorder.LastGroundHitName;
            var horizontalAmbiguousHit = hitRecorder.LastAmbiguousHitName;
            var horizontalHit = !string.IsNullOrEmpty(horizontalSideHit)
                ? horizontalSideHit
                : !string.IsNullOrEmpty(horizontalAmbiguousHit) ? horizontalAmbiguousHit : hitRecorder.LastHitName;

            var groundingRequest = Mathf.Min(GroundingStepCap,
                Mathf.Max(GroundingProbe, player.position.y - target.y));
            hitRecorder.Clear();
            var groundingFlags = controller.Move(Vector3.down * groundingRequest);
            var groundingGroundHit = hitRecorder.LastGroundHitName;
            var groundingAmbiguousHit = hitRecorder.LastAmbiguousHitName;
            if ((groundingFlags & CollisionFlags.Below) != 0 || controller.isGrounded) groundedSteps++;
            movementSteps++;

            traversedDistance += Vector3.Distance(before, player.position);
            var error = Vector3.Distance(player.position, target);
            maximumError = Mathf.Max(maximumError, error);
            var blockingHitName = (horizontalFlags & CollisionFlags.Sides) != 0
                ? horizontalHit
                : hitRecorder.LastSideHitName;
            if ((horizontalFlags & CollisionFlags.Sides) != 0 &&
                string.IsNullOrEmpty(blockingHitName) &&
                !string.IsNullOrEmpty(namedBoundaryContact))
            {
                blockingHitName = ExpectedBoundaryCollider;
                boundaryContactProof = namedBoundaryContact;
            }
            movementTrace.Add(new MovementTraceRecord(segment, step, before, target, player.position, error,
                horizontalFlags, groundingFlags, horizontalSideHit, horizontalGroundHit,
                horizontalAmbiguousHit, groundingGroundHit, groundingAmbiguousHit));
            return new MovementResult(error, horizontalFlags, groundingFlags, blockingHitName,
                groundingGroundHit, string.IsNullOrEmpty(horizontalAmbiguousHit)
                    ? groundingAmbiguousHit
                    : horizontalAmbiguousHit);
        }

        private bool ValidateRouteAnchors()
        {
            var metadata = v11Root.Find("V11_Metadata");
            if (metadata == null) return false;
            var anchors = new Dictionary<string, Vector3>(StringComparer.Ordinal)
            {
                { "V11_Anchor_Great_Step_Open", KhufuV11RoyalRouteContract.GreatStepEntry },
                { "V11_Anchor_Royal_Threshold", KhufuV11RoyalRouteContract.RoyalThreshold },
                { "V11_Anchor_Antechamber", KhufuV11RoyalRouteContract.AntechamberCenter },
                { "V11_Anchor_Kings_Entrance", KhufuV11RoyalRouteContract.KingsEntrance },
                { "V11_Anchor_Kings_Chamber", KhufuV11RoyalRouteContract.KingsChamberCenter },
                { "V11_Anchor_Sarcophagus", KhufuV11RoyalRouteContract.SarcophagusCenter },
                { "V11_Anchor_Stacked_Display", KhufuV11RoyalRouteContract.StackedDisplayCenter() }
            };
            return anchors.All(item =>
            {
                var anchor = metadata.Find(item.Key);
                return anchor != null && Vector3.Distance(anchor.position, item.Value) <= 0.001f;
            });
        }

        private string BoundaryContact(Vector3 movement)
        {
            if (!boundaryControl || boundaryCollider == null || controller == null)
                return string.Empty;
            ControllerCapsule(out var top, out var bottom, out var radius);
            if (Physics.OverlapCapsule(top, bottom, radius, ~0, QueryTriggerInteraction.Ignore)
                .Any(item => item == boundaryCollider))
                return "actual-controller capsule overlap before Move";
            var distance = movement.magnitude;
            if (distance <= 0.0001f) return string.Empty;
            var hits = Physics.CapsuleCastAll(
                top,
                bottom,
                radius,
                movement / distance,
                distance + controller.skinWidth,
                ~0,
                QueryTriggerInteraction.Ignore);
            return hits.Any(item => item.collider == boundaryCollider)
                ? "actual-controller capsule cast along requested Move"
                : string.Empty;
        }

        private void ControllerCapsule(out Vector3 top, out Vector3 bottom, out float radius)
        {
            var scale = controller.transform.lossyScale;
            radius = controller.radius * Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z));
            var height = Mathf.Max(controller.height * Mathf.Abs(scale.y), radius * 2f);
            var center = controller.transform.TransformPoint(controller.center);
            var halfSegment = Mathf.Max(0f, height * 0.5f - radius);
            var up = controller.transform.up;
            top = center + up * halfSegment;
            bottom = center - up * halfSegment;
        }

        private static IReadOnlyList<Vector3> BuildRoundTrip()
        {
            var outward = new List<Vector3> { KhufuV10RouteContract.GreatStepStop() };
            outward.AddRange(KhufuV11RoyalRouteContract.TraversalRoute());
            var result = new List<Vector3>(outward);
            for (var index = outward.Count - 2; index >= 0; index--) result.Add(outward[index]);
            return result;
        }

        private float ExpectedRouteDistance()
        {
            var distance = 0f;
            for (var index = 1; index < route.Count; index++)
                distance += Vector3.Distance(route[index - 1], route[index]);
            return distance;
        }

        private Vector3 PlayerPoint(Vector3 start, Vector3 end, float t)
        {
            return Vector3.Lerp(start, end, t) + Vector3.up * (controller.height * 0.5f + FloorOffset);
        }

        private void Teleport(Transform player, Vector3 position)
        {
            controller.enabled = false;
            player.position = position;
            controller.enabled = true;
            Physics.SyncTransforms();
        }

        private string WriteMovementTrace()
        {
            var path = Path.Combine(outputRoot, label + "-" + ProofMode() + "-movement-trace.csv");
            var text = new StringBuilder("segment,step,before,target,after,error,horizontal_flags," +
                                         "grounding_flags,horizontal_side_hit,horizontal_ground_hit," +
                                         "horizontal_ambiguous_hit,grounding_ground_hit,grounding_ambiguous_hit\n");
            foreach (var item in movementTrace) text.AppendLine(item.ToCsv());
            File.WriteAllText(path, text.ToString(), Encoding.UTF8);
            return path;
        }

        private void RestoreRuntime()
        {
            foreach (var item in dynamicColliders)
                if (item != null) item.enabled = true;
            if (playerController != null) playerController.enabled = true;
        }

        private string ProofMode()
        {
            return boundaryControl ? "great-step-boundary-control" : "normal-round-trip";
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
            using var stream = File.OpenRead(path);
            using var hash = SHA256.Create();
            return string.Concat(hash.ComputeHash(stream).Select(item => item.ToString("x2")));
        }

        private static string Float(float value)
        {
            return value.ToString("F3", CultureInfo.InvariantCulture);
        }

        private static string FormatFlags(CollisionFlags flags)
        {
            if (flags == CollisionFlags.None) return "None";
            var values = new List<string>();
            if ((flags & CollisionFlags.Sides) != 0) values.Add("Sides");
            if ((flags & CollisionFlags.Above) != 0) values.Add("Above");
            if ((flags & CollisionFlags.Below) != 0) values.Add("Below");
            return string.Join("|", values);
        }

        private static string Empty(string value)
        {
            return string.IsNullOrEmpty(value) ? "none" : value;
        }

        private readonly struct MovementResult
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

        private readonly struct MovementTraceRecord
        {
            private readonly int segment;
            private readonly int step;
            private readonly Vector3 before;
            private readonly Vector3 target;
            private readonly Vector3 after;
            private readonly float error;
            private readonly CollisionFlags horizontalFlags;
            private readonly CollisionFlags groundingFlags;
            private readonly string horizontalSideHit;
            private readonly string horizontalGroundHit;
            private readonly string horizontalAmbiguousHit;
            private readonly string groundingGroundHit;
            private readonly string groundingAmbiguousHit;

            public MovementTraceRecord(int segment, int step, Vector3 before, Vector3 target, Vector3 after,
                float error, CollisionFlags horizontalFlags, CollisionFlags groundingFlags,
                string horizontalSideHit, string horizontalGroundHit, string horizontalAmbiguousHit,
                string groundingGroundHit, string groundingAmbiguousHit)
            {
                this.segment = segment;
                this.step = step;
                this.before = before;
                this.target = target;
                this.after = after;
                this.error = error;
                this.horizontalFlags = horizontalFlags;
                this.groundingFlags = groundingFlags;
                this.horizontalSideHit = horizontalSideHit;
                this.horizontalGroundHit = horizontalGroundHit;
                this.horizontalAmbiguousHit = horizontalAmbiguousHit;
                this.groundingGroundHit = groundingGroundHit;
                this.groundingAmbiguousHit = groundingAmbiguousHit;
            }

            public string ToCsv()
            {
                return string.Join(",",
                    segment.ToString(CultureInfo.InvariantCulture),
                    step.ToString(CultureInfo.InvariantCulture),
                    Quote(before),
                    Quote(target),
                    Quote(after),
                    error.ToString("F4", CultureInfo.InvariantCulture),
                    Quote(horizontalFlags.ToString()),
                    Quote(groundingFlags.ToString()),
                    Quote(horizontalSideHit),
                    Quote(horizontalGroundHit),
                    Quote(horizontalAmbiguousHit),
                    Quote(groundingGroundHit),
                    Quote(groundingAmbiguousHit));
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

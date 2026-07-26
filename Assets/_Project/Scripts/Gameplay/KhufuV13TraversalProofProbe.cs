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
    [DefaultExecutionOrder(338)]
    public sealed class KhufuV13TraversalProofProbe : MonoBehaviour
    {
        private const string RootName = "Runtime_Khufu_V13_Subterranean_Threshold";
        private const string ExpectedBoundaryCollider = "V13_Proxy_Chamber_East_Wall";
        private const string ExpectedCallback = "OnControllerColliderHit";
        private const float NormalStep = 0.16f;
        private const float ControlStep = 0.08f;
        private const double RuntimeResolveTimeoutSeconds = 25d;
        private const double AnchorTimeoutSeconds = 15d;
        private const double OverallProofTimeoutSeconds = 90d;

        private readonly List<TraceRecord> trace = new List<TraceRecord>();
        private TraitorEscapeMvpSession session;
        private Transform root;
        private CharacterController controller;
        private ChannelPlayerController playerController;
        private KhufuV13ControllerHitRecorder hitRecorder;
        private KhufuV13SubterraneanThresholdControl control;
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
        private int outboundMovementSteps;
        private int outboundGroundedSteps;
        private int returnMovementSteps;
        private int returnGroundedSteps;
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
        private bool exactCallback;
        private bool pitOverlapSolid;
        private bool pitCastSolid;
        private bool originalRunInBackground;
        private bool runtimeStateSaved;
        private bool originalControllerEnabled;
        private bool originalPlayerControllerEnabled;
        private bool hitRecorderAdded;
        private Vector3 originalPlayerPosition;
        private Quaternion originalPlayerRotation;
        private double proofStartedAt;
        private string executionFailure = string.Empty;
        private bool finalizing;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (!HasArgument("-khufu-v13-traversal-proof")) return;
            var host = new GameObject("KhufuV13_Traversal_Proof_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV13TraversalProofProbe>();
        }

        private void Start()
        {
            originalRunInBackground = Application.runInBackground;
            Application.runInBackground = true;
            route = KhufuV13SubterraneanRouteContract.RoundTripRoute();
            outputRoot = ArgumentValue("-khufu-v13-traversal-proof-output",
                Path.Combine(Application.persistentDataPath, "khufu-v13-traversal-proof"));
            label = Sanitize(ArgumentValue("-khufu-v13-traversal-proof-label",
                "v13-subterranean-final"));
            boundaryControl = HasArgument("-khufu-v13-traversal-proof-negative-boundary");
            Directory.CreateDirectory(outputRoot);
            startedAt = Time.realtimeSinceStartupAsDouble;
            Debug.Log("CHANNEL_PLAY_KHUFU_V13_TRAVERSAL_PROOF result=started mode=" + Mode());
        }

        private void LateUpdate()
        {
            if (started) return;
            if (!ResolveRuntime())
            {
                if (Time.realtimeSinceStartupAsDouble - startedAt >
                    RuntimeResolveTimeoutSeconds)
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
            control = root.GetComponentInChildren<KhufuV13SubterraneanThresholdControl>(true);
            return controller != null && control != null && control.RouteAnchors != null &&
                   control.CollisionProxies != null && control.SolidPitBacking != null;
        }

        private IEnumerator RunProof()
        {
            var player = session.DiagnosticPlayer;
            IEnumerator routine = null;
            var routineCompleted = false;
            proofStartedAt = Time.realtimeSinceStartupAsDouble;
            try
            {
                try
                {
                    SaveAndPrepareRuntime(player);
                    routine = boundaryControl
                        ? RunBoundaryControl(player)
                        : RunNormal(player);
                }
                catch (Exception exception)
                {
                    executionFailure =
                        "runtime setup exception: " + ExceptionToken(exception);
                }

                while (routine != null &&
                       string.IsNullOrEmpty(executionFailure))
                {
                    if (!WithinDeadline("overall proof", proofStartedAt,
                            OverallProofTimeoutSeconds))
                        break;
                    bool moveNext;
                    object current = null;
                    try
                    {
                        moveNext = routine.MoveNext();
                        if (moveNext) current = routine.Current;
                    }
                    catch (Exception exception)
                    {
                        executionFailure =
                            "proof exception: " + ExceptionToken(exception);
                        break;
                    }
                    if (!moveNext)
                    {
                        routineCompleted = true;
                        break;
                    }
                    yield return current;
                }
                if (string.IsNullOrEmpty(executionFailure) &&
                    !routineCompleted)
                    executionFailure = "proof stopped before completion";
            }
            finally
            {
                (routine as IDisposable)?.Dispose();
                CompleteAndQuit(executionFailure);
            }
        }

        private IEnumerator RunNormal(Transform player)
        {
            Teleport(player, PlayerPoint(route[0]));
            player.rotation = UprightLookRotation(route[1] - route[0]);
            reachedAnchors = 1;
            yield return new WaitForSecondsRealtime(0.35f);
            for (var segment = 1; segment < route.Count && !blocked; segment++)
            {
                var anchorStartedAt = Time.realtimeSinceStartupAsDouble;
                var start = route[segment - 1];
                var end = route[segment];
                var steps = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(start, end) / NormalStep));
                for (var step = 1; step <= steps; step++)
                {
                    if (!WithinDeadline("route anchor " + segment,
                            anchorStartedAt, AnchorTimeoutSeconds))
                        yield break;
                    var target = PlayerPoint(Vector3.Lerp(start, end, step / (float)steps));
                    var before = player.position;
                    var request = target - player.position;
                    if (request.magnitude > NormalStep)
                        request = request.normalized * NormalStep;
                    maximumRequestedStep = Mathf.Max(maximumRequestedStep, request.magnitude);
                    hitRecorder.ClearFrame();
                    var frame = Time.frameCount;
                    var flags = controller.Move(request);
                    hitRecorder.RecordMove(flags);
                    var sideHit = hitRecorder.LastSideHitName;
                    var callbackFrame = hitRecorder.LastSideHitFrame;
                    var grounding = Mathf.Min(0.25f,
                        Mathf.Max(0.04f, player.position.y - target.y + 0.04f));
                    var groundFlags = controller.Move(Vector3.down * grounding);
                    var grounded =
                        (groundFlags & CollisionFlags.Below) != 0 ||
                        controller.isGrounded;
                    if (grounded)
                        groundedSteps++;
                    movementSteps++;
                    if (segment <= route.Count / 2)
                    {
                        outboundMovementSteps++;
                        if (grounded) outboundGroundedSteps++;
                    }
                    else
                    {
                        returnMovementSteps++;
                        if (grounded) returnGroundedSteps++;
                    }
                    traversedDistance += Vector3.Distance(before, player.position);
                    var error = Vector3.Distance(player.position, target);
                    maximumError = Mathf.Max(maximumError, error);
                    trace.Add(new TraceRecord(segment, step, frame, before, target, player.position,
                        request.magnitude, error, flags, sideHit, callbackFrame));
                    if (error > KhufuV13SubterraneanRouteContract.MaximumAnchorError)
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
            ValidatePitBacking();
        }

        private IEnumerator RunBoundaryControl(Transform player)
        {
            var outward = KhufuV13SubterraneanRouteContract.BoundaryOutward.normalized;
            var start = KhufuV13SubterraneanRouteContract.BoundaryPoint +
                        outward * (KhufuV13SubterraneanRouteContract.BoundaryStartDistance + 0.20f);
            var end = KhufuV13SubterraneanRouteContract.BoundaryPoint - outward * 0.65f;
            boundaryStartDistance =
                Vector3.Distance(start, KhufuV13SubterraneanRouteContract.BoundaryPoint);
            Teleport(player, PlayerPoint(start));
            player.rotation = UprightLookRotation(-outward);
            yield return new WaitForSecondsRealtime(0.25f);
            var anchorStartedAt = Time.realtimeSinceStartupAsDouble;

            ControllerCapsule(out var top, out var bottom, out var radius);
            var overlaps = Physics.OverlapCapsule(top, bottom, radius, ~0,
                    QueryTriggerInteraction.Ignore)
                .Where(item => item != controller)
                .Select(item => item.name)
                .Distinct(StringComparer.Ordinal)
                .ToArray();
            preMoveOverlapEmpty = overlaps.Length == 0;

            var maximumSteps = Mathf.CeilToInt(Vector3.Distance(start, end) / ControlStep) + 2;
            for (var step = 1; step <= maximumSteps && !blocked; step++)
            {
                if (!WithinDeadline("outside-wall control", anchorStartedAt,
                        AnchorTimeoutSeconds))
                    yield break;
                var remaining = Vector3.ProjectOnPlane(PlayerPoint(end) - player.position,
                    Vector3.up);
                if (remaining.magnitude <= 0.001f) break;
                var request = remaining.normalized * Mathf.Min(ControlStep, remaining.magnitude);
                maximumRequestedStep = Mathf.Max(maximumRequestedStep, request.magnitude);
                var before = player.position;
                hitRecorder.ClearFrame();
                var moveFrame = Time.frameCount;
                var flags = controller.Move(request);
                hitRecorder.RecordMove(flags);
                var error = Vector3.Distance(player.position, PlayerPoint(end));
                trace.Add(new TraceRecord(1, step, moveFrame, before, PlayerPoint(end),
                    player.position, request.magnitude, error, flags,
                    hitRecorder.LastSideHitName, hitRecorder.LastSideHitFrame));
                if ((flags & CollisionFlags.Sides) != 0)
                {
                    blocked = true;
                    blockedHit = hitRecorder.LastSideHitName;
                    blockedFlags = flags;
                    boundaryMoveFrame = hitRecorder.LastMoveFrame;
                    boundaryCallbackFrame = hitRecorder.LastSideHitFrame;
                    exactCallback = KhufuV13ControllerHitRecorder.CallbackName == ExpectedCallback;
                }
                yield return null;
            }
        }

        private void ValidatePitBacking()
        {
            var backing = control.SolidPitBacking.GetComponent<BoxCollider>();
            if (backing == null || !backing.enabled || backing.isTrigger) return;
            var center = PlayerPoint(KhufuV13SubterraneanRouteContract.PitInspection);
            CapsuleAt(center + Vector3.down * 0.12f, out var overlapTop,
                out var overlapBottom, out var radius);
            pitOverlapSolid = Physics.OverlapCapsule(overlapTop, overlapBottom, radius, ~0,
                    QueryTriggerInteraction.Ignore)
                .Any(item => item == backing);
            CapsuleAt(center + Vector3.up * 0.35f, out var castTop, out var castBottom,
                out radius);
            pitCastSolid = Physics.CapsuleCastAll(castTop, castBottom, radius, Vector3.down,
                    0.75f, ~0, QueryTriggerInteraction.Ignore)
                .Where(item => item.collider != controller)
                .OrderBy(item => item.distance)
                .Any(item => item.collider == backing);
        }

        private void CompleteAndQuit(string failure)
        {
            if (finalizing) return;
            finalizing = true;
            var passed = false;
            var exitCode = 1;
            try
            {
                var groundedFraction = Fraction(groundedSteps, movementSteps);
                var outboundGroundedFraction =
                    Fraction(outboundGroundedSteps, outboundMovementSteps);
                var returnGroundedFraction =
                    Fraction(returnGroundedSteps, returnMovementSteps);
                var anchorsValid = control != null && ValidateAnchors();
                var rootColliders = root == null ? 0 :
                    root.GetComponentsInChildren<BoxCollider>(true)
                        .Count(item => item.enabled);
                var rootRenderers = root == null ? 0 :
                    root.GetComponentsInChildren<Renderer>(true)
                        .Count(item => item.enabled &&
                                       item.gameObject.activeInHierarchy);
                var finalError =
                    boundaryControl || session == null ||
                    session.DiagnosticPlayer == null || controller == null
                        ? float.NaN
                        : Vector3.Distance(session.DiagnosticPlayer.position,
                            PlayerPoint(route[route.Count - 1]));
                var normalPassed =
                    string.IsNullOrEmpty(failure) && !boundaryControl &&
                    !blocked && reachedAnchors == route.Count &&
                    maximumError <=
                    KhufuV13SubterraneanRouteContract.MaximumAnchorError &&
                    finalError <=
                    KhufuV13SubterraneanRouteContract.MaximumAnchorError &&
                    groundedFraction >=
                    KhufuV13SubterraneanRouteContract.MinimumGroundedRatio &&
                    outboundGroundedFraction >=
                    KhufuV13SubterraneanRouteContract.MinimumGroundedRatio &&
                    returnGroundedFraction >=
                    KhufuV13SubterraneanRouteContract.MinimumGroundedRatio &&
                    anchorsValid && rootColliders == 20 && rootRenderers == 5 &&
                    pitOverlapSolid && pitCastSolid;
                var boundaryPassed =
                    string.IsNullOrEmpty(failure) && boundaryControl && blocked &&
                    blockedHit == ExpectedBoundaryCollider &&
                    (blockedFlags & CollisionFlags.Sides) != 0 &&
                    boundaryStartDistance >=
                    KhufuV13SubterraneanRouteContract.BoundaryStartDistance &&
                    preMoveOverlapEmpty &&
                    maximumRequestedStep <=
                    KhufuV13SubterraneanRouteContract.MaximumControlStep +
                    0.0001f &&
                    boundaryMoveFrame >= 0 &&
                    boundaryCallbackFrame == boundaryMoveFrame &&
                    hitRecorder != null &&
                    hitRecorder.HasSameFrameSideProof && exactCallback;
                passed = boundaryControl ? boundaryPassed : normalPassed;
                WriteReceipt(passed, normalPassed, boundaryPassed, finalError,
                    groundedFraction, outboundGroundedFraction,
                    returnGroundedFraction, anchorsValid, rootColliders,
                    rootRenderers, failure);
                exitCode = passed ? 0 : 1;
            }
            catch (Exception exception)
            {
                failure = JoinFailure(failure,
                    "completion exception: " + ExceptionToken(exception));
                Debug.LogException(exception);
                TryWriteEmergencyReceipt(failure);
                passed = false;
                exitCode = 1;
            }
            finally
            {
                try
                {
                    RestoreRuntime();
                }
                catch (Exception exception)
                {
                    failure = JoinFailure(failure,
                        "runtime restore exception: " +
                        ExceptionToken(exception));
                    Debug.LogException(exception);
                    TryWriteEmergencyReceipt(failure);
                    passed = false;
                    exitCode = 1;
                }
                Debug.Log("CHANNEL_PLAY_KHUFU_V13_TRAVERSAL_PROOF result=" +
                          (passed ? "passed" : "failed") + " mode=" + Mode() +
                          " reached=" + reachedAnchors + "/" + route.Count +
                          " hit=" + blockedHit + " callback=" +
                          ExpectedCallback + " callback_frame=" +
                          boundaryCallbackFrame + " failure=\"" +
                          Empty(failure) + "\"");
                Application.Quit(exitCode);
            }
        }

        private void FailAndQuit(string reason)
        {
            started = true;
            CompleteAndQuit(reason);
        }

        private void WriteReceipt(bool passed, bool normalPassed, bool boundaryPassed,
            float finalError, float groundedFraction,
            float outboundGroundedFraction, float returnGroundedFraction,
            bool anchorsValid, int rootColliders, int rootRenderers,
            string failure)
        {
            var tracePath = WriteTrace();
            var text = new StringBuilder("# Khufu V13 Windows Player Traversal Proof\n\n");
            text.AppendLine("- Harness verdict: **" + (passed ? "passed" : "failed") + "**");
            text.AppendLine("- Mode: `" + Mode() + "`");
            text.AppendLine("- V10 branch -> landing -> door -> chamber/pit -> return: `" +
                            (normalPassed ? "passed" :
                                boundaryControl ? "not-applicable" : "failed") + "`");
            text.AppendLine("- Outside-wall control: `" +
                            (boundaryPassed ? "passed" :
                                boundaryControl ? "failed" : "not-applicable") + "`");
            text.AppendLine("- Reached route anchors: `" + reachedAnchors + "/" +
                            route.Count + "`");
            text.AppendLine("- Serialized anchors match: `" + anchorsValid + "`");
            text.AppendLine("- Traversed distance / max error / final error: `" +
                            Float(traversedDistance) + " / " + Float(maximumError) +
                            " / " + Float(finalError) + "`");
            text.AppendLine("- Grounded steps/fraction: `" + groundedSteps + "/" +
                            movementSteps + " / " + Float(groundedFraction) + "`");
            text.AppendLine("- Outbound grounded steps/fraction: `" +
                            outboundGroundedSteps + "/" +
                            outboundMovementSteps + " / " +
                            Float(outboundGroundedFraction) + "`");
            text.AppendLine("- Return grounded steps/fraction: `" +
                            returnGroundedSteps + "/" +
                            returnMovementSteps + " / " +
                            Float(returnGroundedFraction) + "`");
            text.AppendLine("- Root renderers / enabled colliders: `" + rootRenderers +
                            " / " + rootColliders + "`");
            text.AppendLine("- Pit overlap / cast solid backing: `" + pitOverlapSolid +
                            " / " + pitCastSolid + "`");
            text.AppendLine("- Control boundary start distance: `" +
                            Float(boundaryStartDistance) + " m`");
            text.AppendLine("- Control pre-Move overlap empty: `" + preMoveOverlapEmpty + "`");
            text.AppendLine("- Control maximum requested step: `" +
                            Float(maximumRequestedStep) + " m`");
            text.AppendLine("- Control blocked collider / flags: `" + Empty(blockedHit) +
                            " / " + blockedFlags + "`");
            text.AppendLine("- Control Move / callback frame: `" + boundaryMoveFrame +
                            " / " + boundaryCallbackFrame + "`");
            text.AppendLine("- Control callback: `" + ExpectedCallback +
                            "` / exact `" + exactCallback + "`");
            text.AppendLine("- Movement trace: `" + tracePath.Replace('\\', '/') +
                            "` / records `" + trace.Count + "` / SHA256 `" +
                            Sha256(tracePath) + "`");
            text.AppendLine("- Assembly-CSharp SHA256: `" +
                            Sha256(Path.Combine(Application.dataPath, "Managed",
                                "Assembly-CSharp.dll")) + "`");
            if (!string.IsNullOrEmpty(failure))
                text.AppendLine("- Failure: `" + failure + "`");
            text.AppendLine();
            text.AppendLine((boundaryControl ? "V13_WINDOWS_PLAYER_BOUNDARY_CONTROL" :
                "V13_WINDOWS_PLAYER_TRAVERSAL") + ": " +
                            (passed ? "passed" : "failed"));
            var suffix = boundaryControl ? "-boundary-control.md" : "-round-trip.md";
            File.WriteAllText(Path.Combine(outputRoot, label + suffix), text.ToString(),
                Encoding.UTF8);
        }

        private bool ValidateAnchors()
        {
            var expected = KhufuV13SubterraneanRouteContract.ForwardRoute();
            return control.RouteAnchors.Count == expected.Count &&
                   control.RouteAnchors.Select((anchor, index) =>
                           anchor != null &&
                           Vector3.Distance(anchor.position, expected[index]) <= 0.001f)
                       .All(item => item);
        }

        private Vector3 PlayerPoint(Vector3 floorPoint)
        {
            if (controller == null)
                return floorPoint +
                       Vector3.up *
                       KhufuV13SubterraneanRouteContract.TraversalFloorOffset;
            var scaleY = Mathf.Abs(controller.transform.lossyScale.y);
            var bottomFromOrigin =
                (controller.center.y - controller.height * 0.5f) * scaleY;
            return floorPoint + Vector3.up *
                (KhufuV13SubterraneanRouteContract.TraversalFloorOffset -
                 bottomFromOrigin);
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

        private void CapsuleAt(Vector3 centerPosition, out Vector3 top, out Vector3 bottom,
            out float radius)
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
            var path = Path.Combine(outputRoot, label + "-" + Mode() +
                                                "-movement-trace.csv");
            var text = new StringBuilder(
                "segment,step,move_frame,before,target,after,request,error,flags,side_hit,callback_frame\n");
            foreach (var item in trace) text.AppendLine(item.ToCsv());
            File.WriteAllText(path, text.ToString(), Encoding.UTF8);
            return path;
        }

        private void SaveAndPrepareRuntime(Transform player)
        {
            playerController = player.GetComponent<ChannelPlayerController>();
            originalPlayerControllerEnabled =
                playerController != null && playerController.enabled;
            originalControllerEnabled = controller.enabled;
            originalPlayerPosition = player.position;
            originalPlayerRotation = player.rotation;
            runtimeStateSaved = true;

            hitRecorder = player.GetComponent<KhufuV13ControllerHitRecorder>();
            if (hitRecorder == null)
            {
                hitRecorder =
                    player.gameObject.AddComponent<KhufuV13ControllerHitRecorder>();
                hitRecorderAdded = true;
            }
            dynamicColliderStates =
                FindObjectsByType<Collider>(FindObjectsSortMode.None)
                    .Where(item => item.name.StartsWith("Runtime_Bot_",
                        StringComparison.Ordinal))
                    .Select(item => new ColliderState(item, item.enabled))
                    .ToArray();
            foreach (var item in dynamicColliderStates)
                item.Collider.enabled = false;
            if (playerController != null) playerController.enabled = false;
            if (!controller.enabled) controller.enabled = true;
            Physics.SyncTransforms();
        }

        private void RestoreRuntime()
        {
            try
            {
                if (!runtimeStateSaved) return;
                foreach (var item in dynamicColliderStates)
                    if (item.Collider != null)
                        item.Collider.enabled = item.Enabled;
                var player = session == null ? null : session.DiagnosticPlayer;
                if (controller != null) controller.enabled = false;
                if (player != null)
                {
                    player.position = originalPlayerPosition;
                    player.rotation = originalPlayerRotation;
                }
                Physics.SyncTransforms();
                if (controller != null)
                    controller.enabled = originalControllerEnabled;
                if (playerController != null)
                    playerController.enabled = originalPlayerControllerEnabled;
                if (hitRecorderAdded && hitRecorder != null)
                    Destroy(hitRecorder);
                Physics.SyncTransforms();
            }
            finally
            {
                runtimeStateSaved = false;
                Application.runInBackground = originalRunInBackground;
            }
        }

        private bool WithinDeadline(string phase, double phaseStartedAt,
            double phaseBudgetSeconds)
        {
            var now = Time.realtimeSinceStartupAsDouble;
            var overallElapsed = now - proofStartedAt;
            if (overallElapsed > OverallProofTimeoutSeconds)
            {
                executionFailure = "overall timeout after " +
                                   overallElapsed.ToString("F3",
                                       CultureInfo.InvariantCulture) +
                                   " seconds during " + phase;
                return false;
            }
            var phaseElapsed = now - phaseStartedAt;
            if (phaseElapsed <= phaseBudgetSeconds) return true;
            executionFailure = phase + " timeout after " +
                               phaseElapsed.ToString("F3",
                                   CultureInfo.InvariantCulture) +
                               " seconds";
            return false;
        }

        private void TryWriteEmergencyReceipt(string failure)
        {
            try
            {
                Directory.CreateDirectory(outputRoot);
                var suffix = boundaryControl
                    ? "-boundary-control.md"
                    : "-round-trip.md";
                var text =
                    new StringBuilder(
                        "# Khufu V13 Windows Player Traversal Proof\n\n");
                text.AppendLine("- Harness verdict: **failed**");
                text.AppendLine("- Mode: `" + Mode() + "`");
                text.AppendLine("- Failure: `" + Empty(failure) + "`");
                text.AppendLine();
                text.AppendLine((boundaryControl
                    ? "V13_WINDOWS_PLAYER_BOUNDARY_CONTROL"
                    : "V13_WINDOWS_PLAYER_TRAVERSAL") + ": failed");
                File.WriteAllText(Path.Combine(outputRoot, label + suffix),
                    text.ToString(), Encoding.UTF8);
            }
            catch (Exception exception)
            {
                Debug.LogError(
                    "CHANNEL_PLAY_KHUFU_V13_TRAVERSAL_RECEIPT result=failed " +
                    ExceptionToken(exception));
            }
        }

        private static float Fraction(int numerator, int denominator)
        {
            return denominator == 0 ? 0f : numerator / (float)denominator;
        }

        private static string JoinFailure(string current, string next)
        {
            return string.IsNullOrEmpty(current)
                ? next
                : current + " | " + next;
        }

        private static string ExceptionToken(Exception exception)
        {
            var source = exception.GetBaseException();
            return source.GetType().Name + ": " +
                   (source.Message ?? string.Empty)
                   .Replace('\r', ' ').Replace('\n', ' ');
        }

        private string Mode()
        {
            return boundaryControl ? "outside-wall-control" : "normal-round-trip";
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
                if (string.Equals(arguments[index], key,
                        StringComparison.OrdinalIgnoreCase))
                    return arguments[index + 1];
            return fallback;
        }

        private static string Sanitize(string value)
        {
            var invalid = Path.GetInvalidFileNameChars();
            return new string(value.Select(character =>
                invalid.Contains(character) ? '_' : character).ToArray());
        }

        private static string Sha256(string path)
        {
            if (!File.Exists(path)) return "missing";
            using (var stream = File.OpenRead(path))
            using (var hash = SHA256.Create())
                return string.Concat(hash.ComputeHash(stream)
                    .Select(item => item.ToString("x2")));
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

            public TraceRecord(int segment, int step, int moveFrame, Vector3 before,
                Vector3 target, Vector3 after, float request, float error,
                CollisionFlags flags, string sideHit, int callbackFrame)
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

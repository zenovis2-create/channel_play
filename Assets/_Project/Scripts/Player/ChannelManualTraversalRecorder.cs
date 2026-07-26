using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;

namespace ChannelPlay.Player
{
    public sealed class ChannelManualTraversalRecorder : MonoBehaviour
    {
        private const string DefaultOutputRoot = "runs/manual-traversal-review";
        private static readonly string[] RequiredRouteLabels =
        {
            "entrance-threshold",
            "djoser-gallery",
            "khufu-grand-gallery",
            "hawara-labyrinth-core",
            "burial-chamber",
            "rear-service-exit",
        };

        [SerializeField] private Transform player;
        [SerializeField] private Camera captureCamera;
        [SerializeField] private ChannelCameraOccluderCutaway cameraCutaway;
        [SerializeField] private string outputRoot = DefaultOutputRoot;
        [SerializeField] private KeyCode captureKey = KeyCode.F9;
        [SerializeField] private KeyCode writeReportKey = KeyCode.F10;
        [SerializeField] private bool showOperatorHud = true;

        private readonly List<TraversalCheckpoint> checkpoints = new List<TraversalCheckpoint>();

        private string runDirectory;
        private int captureIndex;
        private string statusLine = "Manual traversal capture ready: F9 capture / F10 report";

        public int CheckpointCount => checkpoints.Count;
        public int CompletedRequiredCheckpointCount => CountCompletedRequiredCheckpoints();
        public bool RequiredRouteComplete => CompletedRequiredCheckpointCount >= RequiredRouteLabels.Length;
        public string CurrentRunDirectory => runDirectory ?? string.Empty;
        public string StatusLine => statusLine;
        public string NextRequiredRouteLabel => NextRouteLabel();
        public string OperatorHudText => BuildOperatorHudText();

        public void Configure(Transform newPlayer, Camera newCaptureCamera, ChannelCameraOccluderCutaway newCameraCutaway)
        {
            player = newPlayer;
            captureCamera = newCaptureCamera;
            cameraCutaway = newCameraCutaway;
            statusLine = BuildRouteStatusLine("Manual traversal capture ready");
        }

        public void SetOutputRoot(string newOutputRoot)
        {
            if (string.IsNullOrWhiteSpace(newOutputRoot))
            {
                outputRoot = DefaultOutputRoot;
                return;
            }

            outputRoot = NormalizeProjectPath(newOutputRoot.Trim());
            runDirectory = null;
        }

        public void SetOperatorHudVisible(bool visible)
        {
            showOperatorHud = visible;
        }

        public string CaptureCheckpoint()
        {
            EnsureRunDirectory();

            var label = GuessLocationLabel();
            var fileName = $"manual_traversal_{captureIndex:000}_{SanitizeLabel(label)}.png";
            var screenshotPath = NormalizeProjectPath(Path.Combine(runDirectory, fileName));
            Directory.CreateDirectory(ProjectAbsolutePath(runDirectory));
            ScreenCapture.CaptureScreenshot(screenshotPath, 1);
            AddCheckpoint(label, screenshotPath);

            statusLine = BuildRouteStatusLine($"Manual capture queued #{captureIndex}: {label}");
            return screenshotPath;
        }

        public string RecordCheckpointForValidation(string label, string screenshotPath)
        {
            EnsureRunDirectory();
            var normalizedPath = NormalizeProjectPath(screenshotPath);
            AddCheckpoint(label, normalizedPath);
            statusLine = BuildRouteStatusLine($"Validation checkpoint #{captureIndex}: {label}");
            return normalizedPath;
        }

        public string WriteSessionReceipt()
        {
            EnsureRunDirectory();

            var receiptPath = NormalizeProjectPath(Path.Combine(runDirectory, "manual_traversal_session.md"));
            var absolutePath = ProjectAbsolutePath(receiptPath);
            Directory.CreateDirectory(Path.GetDirectoryName(absolutePath) ?? ProjectRoot());
            File.WriteAllText(absolutePath, BuildReceipt(), Encoding.UTF8);

            statusLine = $"Manual traversal report saved: {receiptPath}";
            return absolutePath;
        }

        private void Update()
        {
            if (Input.GetKeyDown(captureKey))
            {
                CaptureCheckpoint();
            }

            if (Input.GetKeyDown(writeReportKey))
            {
                WriteSessionReceipt();
            }
        }

        private void OnGUI()
        {
            if (!showOperatorHud)
            {
                return;
            }

            var hudWidth = Mathf.Min(380f, Screen.width - 24f);
            var scoreboardWidth = Mathf.Min(300f, Screen.width - 24f);
            var availableLeft = 12f + hudWidth + 12f;
            var availableRight = Screen.width - scoreboardWidth - 24f;
            var availableWidth = availableRight - availableLeft;
            if (availableWidth < 280f)
            {
                return;
            }

            var width = Mathf.Min(620f, availableWidth);
            var left = availableLeft + (availableWidth - width) * 0.5f;
            var rect = new Rect(left, Mathf.Max(20f, Screen.height - 168f), width, 148f);
            GUI.Box(rect, string.Empty);
            GUI.Label(new Rect(rect.x + 14f, rect.y + 12f, rect.width - 28f, 22f), "Channel Play Manual Capture");
            GUI.Label(new Rect(rect.x + 14f, rect.y + 40f, rect.width - 28f, 22f), "Route: " + CompletedRequiredCheckpointCount.ToString(CultureInfo.InvariantCulture) + "/" + RequiredRouteLabels.Length.ToString(CultureInfo.InvariantCulture));
            GUI.Label(new Rect(rect.x + 14f, rect.y + 66f, rect.width - 28f, 22f), "Current: " + GuessLocationLabel() + " | Next: " + NextRouteLabel());
            GUI.Label(new Rect(rect.x + 14f, rect.y + 92f, rect.width - 28f, 22f), "F9 capture checkpoint | F10 write review receipt");
            GUI.Label(new Rect(rect.x + 14f, rect.y + 118f, rect.width - 28f, 22f), statusLine);
        }

        private void AddCheckpoint(string label, string screenshotPath)
        {
            var normalizedLabel = string.IsNullOrWhiteSpace(label) ? "manual" : SanitizeLabel(label);
            checkpoints.Add(
                new TraversalCheckpoint
                {
                    Index = captureIndex,
                    Label = normalizedLabel,
                    RouteStepIndex = MatchRequiredRouteIndex(normalizedLabel),
                    TimeSeconds = Time.time,
                    Frame = Time.frameCount,
                    PlayerPosition = player == null ? Vector3.zero : player.position,
                    PlayerEuler = player == null ? Vector3.zero : player.eulerAngles,
                    CameraPosition = captureCamera == null ? transform.position : captureCamera.transform.position,
                    CameraEuler = captureCamera == null ? transform.eulerAngles : captureCamera.transform.eulerAngles,
                    ActiveCutawayCount = cameraCutaway == null ? 0 : cameraCutaway.ActiveCutawayCount,
                    ScreenshotPath = screenshotPath,
                });
            captureIndex++;
        }

        private string BuildReceipt()
        {
            var builder = new StringBuilder();
            builder.AppendLine("# Manual Pyramid Traversal Session");
            builder.AppendLine();
            builder.AppendLine("Date: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss zzz", CultureInfo.InvariantCulture));
            builder.AppendLine();
            builder.AppendLine("## Result");
            builder.AppendLine();
            builder.AppendLine("Status: `" + (RequiredRouteComplete ? "manual_capture_session_ready_for_review" : "manual_capture_session_incomplete") + "`");
            builder.AppendLine();
            builder.AppendLine("This receipt is for human-operated Play Mode traversal capture. Screenshots are queued only when the operator presses F9 during Play Mode.");
            builder.AppendLine();
            builder.AppendLine("## Controls");
            builder.AppendLine();
            builder.AppendLine("- `F9`: queue screenshot and checkpoint metadata");
            builder.AppendLine("- `F10`: write this session receipt");
            builder.AppendLine();
            builder.AppendLine("## Run Directory");
            builder.AppendLine();
            builder.AppendLine("- `" + NormalizeProjectPath(runDirectory) + "`");
            builder.AppendLine();
            builder.AppendLine("## Required Route Gate");
            builder.AppendLine();
            builder.AppendLine("- Required order: `" + string.Join(" -> ", RequiredRouteLabels) + "`");
            builder.AppendLine("- Completed required checkpoints: `" + CompletedRequiredCheckpointCount.ToString(CultureInfo.InvariantCulture) + "/" + RequiredRouteLabels.Length.ToString(CultureInfo.InvariantCulture) + "`");
            builder.AppendLine("- Ready for visual review: `" + RequiredRouteComplete.ToString().ToLowerInvariant() + "`");
            builder.AppendLine();
            builder.AppendLine("| order | label | status |");
            builder.AppendLine("|---:|---|---|");
            for (var routeIndex = 0; routeIndex < RequiredRouteLabels.Length; routeIndex++)
            {
                builder.AppendLine(
                    "| " + (routeIndex + 1).ToString(CultureInfo.InvariantCulture) +
                    " | " + RequiredRouteLabels[routeIndex] +
                    " | " + (routeIndex < CompletedRequiredCheckpointCount ? "captured" : "missing") +
                    " |");
            }

            builder.AppendLine();
            builder.AppendLine("## Checkpoints");
            builder.AppendLine();

            if (checkpoints.Count == 0)
            {
                builder.AppendLine("- No manual checkpoints recorded yet.");
            }
            else
            {
                builder.AppendLine("| # | label | route | frame | time | player | camera | cutaways | screenshot |");
                builder.AppendLine("|---|---|---:|---:|---:|---|---|---:|---|");
                foreach (var checkpoint in checkpoints)
                {
                    builder.AppendLine(
                        "| " + checkpoint.Index +
                        " | " + EscapeTable(checkpoint.Label) +
                        " | " + FormatRouteStep(checkpoint.RouteStepIndex) +
                        " | " + checkpoint.Frame.ToString(CultureInfo.InvariantCulture) +
                        " | " + checkpoint.TimeSeconds.ToString("0.00", CultureInfo.InvariantCulture) +
                        " | " + FormatVector(checkpoint.PlayerPosition) +
                        " | " + FormatVector(checkpoint.CameraPosition) +
                        " | " + checkpoint.ActiveCutawayCount.ToString(CultureInfo.InvariantCulture) +
                        " | `" + checkpoint.ScreenshotPath + "` |");
                }
            }

            builder.AppendLine();
            builder.AppendLine("## Scope");
            builder.AppendLine();
            if (RequiredRouteComplete)
            {
                builder.AppendLine("This receipt proves that checkpoint metadata was captured in the required route order. Human review still needs to confirm that the saved screenshots are visually acceptable.");
            }
            else
            {
                builder.AppendLine("This receipt is incomplete. Continue the Play Mode session and capture the missing required route checkpoints before visual review.");
            }

            return builder.ToString();
        }

        private void EnsureRunDirectory()
        {
            if (!string.IsNullOrEmpty(runDirectory))
            {
                Directory.CreateDirectory(ProjectAbsolutePath(runDirectory));
                return;
            }

            var timestamp = DateTime.Now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture);
            runDirectory = NormalizeProjectPath(Path.Combine(outputRoot, "session-" + timestamp));
            Directory.CreateDirectory(ProjectAbsolutePath(runDirectory));
        }

        private string GuessLocationLabel()
        {
            if (player == null)
            {
                return "unknown";
            }

            var position = player.position;
            if (position.z < -10f)
            {
                return "entrance-threshold";
            }

            if (position.z < 2f)
            {
                return "djoser-gallery";
            }

            if (position.z < 11f)
            {
                return "khufu-grand-gallery";
            }

            if (position.z < 22f)
            {
                return "hawara-labyrinth-core";
            }

            if (position.z < 32f)
            {
                return "burial-chamber";
            }

            return "rear-service-exit";
        }

        private int CountCompletedRequiredCheckpoints()
        {
            var completed = 0;
            foreach (var checkpoint in checkpoints)
            {
                if (checkpoint.RouteStepIndex == completed)
                {
                    completed++;
                    if (completed >= RequiredRouteLabels.Length)
                    {
                        return completed;
                    }
                }
            }

            return completed;
        }

        private string BuildRouteStatusLine(string prefix)
        {
            var completed = CompletedRequiredCheckpointCount;
            var nextLabel = NextRouteLabel();
            return prefix + " | Route " + completed.ToString(CultureInfo.InvariantCulture) + "/" +
                RequiredRouteLabels.Length.ToString(CultureInfo.InvariantCulture) + " | Next " + nextLabel;
        }

        private string BuildOperatorHudText()
        {
            return "Channel Play Manual Capture" +
                "\nRoute: " + CompletedRequiredCheckpointCount.ToString(CultureInfo.InvariantCulture) + "/" + RequiredRouteLabels.Length.ToString(CultureInfo.InvariantCulture) +
                "\nCurrent: " + GuessLocationLabel() +
                "\nNext: " + NextRouteLabel() +
                "\nF9 capture checkpoint | F10 write review receipt" +
                "\n" + statusLine;
        }

        private string NextRouteLabel()
        {
            var completed = CompletedRequiredCheckpointCount;
            return completed >= RequiredRouteLabels.Length ? "press F10 for visual review" : RequiredRouteLabels[completed];
        }

        private static int MatchRequiredRouteIndex(string label)
        {
            for (var index = 0; index < RequiredRouteLabels.Length; index++)
            {
                if (string.Equals(label, RequiredRouteLabels[index], StringComparison.OrdinalIgnoreCase))
                {
                    return index;
                }
            }

            return -1;
        }

        private static string ProjectRoot()
        {
            return Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
        }

        private static string ProjectAbsolutePath(string projectRelativePath)
        {
            return Path.Combine(ProjectRoot(), NormalizeProjectPath(projectRelativePath));
        }

        private static string NormalizeProjectPath(string value)
        {
            return value.Replace('\\', '/');
        }

        private static string SanitizeLabel(string value)
        {
            var builder = new StringBuilder();
            foreach (var character in value.ToLowerInvariant())
            {
                if ((character >= 'a' && character <= 'z') ||
                    (character >= '0' && character <= '9') ||
                    character == '-')
                {
                    builder.Append(character);
                }
                else if (character == '_' || char.IsWhiteSpace(character))
                {
                    builder.Append('-');
                }
            }

            return builder.Length == 0 ? "manual" : builder.ToString();
        }

        private static string FormatVector(Vector3 value)
        {
            return value.x.ToString("0.00", CultureInfo.InvariantCulture) + ", " +
                value.y.ToString("0.00", CultureInfo.InvariantCulture) + ", " +
                value.z.ToString("0.00", CultureInfo.InvariantCulture);
        }

        private static string FormatRouteStep(int routeStepIndex)
        {
            return routeStepIndex < 0 ? "extra" : (routeStepIndex + 1).ToString(CultureInfo.InvariantCulture);
        }

        private static string EscapeTable(string value)
        {
            return value.Replace("|", "/");
        }

        private sealed class TraversalCheckpoint
        {
            public int Index;
            public string Label;
            public int RouteStepIndex;
            public float TimeSeconds;
            public int Frame;
            public Vector3 PlayerPosition;
            public Vector3 PlayerEuler;
            public Vector3 CameraPosition;
            public Vector3 CameraEuler;
            public int ActiveCutawayCount;
            public string ScreenshotPath;
        }
    }
}

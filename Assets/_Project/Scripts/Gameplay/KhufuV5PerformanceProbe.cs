using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.Profiling;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuV5PerformanceProbe : MonoBehaviour
    {
        private const float WarmupSeconds = 5f;
        private const float ParticipantSampleSeconds = 15f;
        private const float OperatorSampleSeconds = 15f;

        private static readonly Vector3[] ParticipantRoute =
        {
            new Vector3(150f, 1.2f, 0f),
            new Vector3(105f, 4.2f, 0f),
            new Vector3(62f, 2.2f, 0f),
            new Vector3(35f, 1.2f, 42f),
            new Vector3(20f, 1.2f, 60f),
            new Vector3(-80f, 1.2f, 80f),
        };

        private readonly List<double> frameMilliseconds = new List<double>();
        private readonly List<double> cpuMilliseconds = new List<double>();
        private readonly List<double> mainThreadMilliseconds = new List<double>();
        private readonly List<double> renderThreadMilliseconds = new List<double>();
        private readonly List<double> gpuMilliseconds = new List<double>();
        private readonly FrameTiming[] timingBuffer = new FrameTiming[1];

        private TraitorEscapeMvpSession session;
        private string outputRoot;
        private string runLabel;
        private string initialScreenshotPath;
        private string operatorScreenshotPath;
        private double startedAt;
        private bool initialCaptureQueued;
        private bool operatorPrepared;
        private bool operatorCaptureQueued;
        private bool finished;
        private long maximumAllocatedBytes;
        private long maximumReservedBytes;
        private long maximumMonoBytes;
        private int visibleRendererCount;
        private long visibleVertices;
        private long visibleTriangles;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            var arguments = Environment.GetCommandLineArgs();
            if (!arguments.Any(argument => string.Equals(argument, "-khufu-v5-profile", StringComparison.OrdinalIgnoreCase)))
            {
                return;
            }

            var host = new GameObject("KhufuV5_Performance_Probe");
            DontDestroyOnLoad(host);
            host.AddComponent<KhufuV5PerformanceProbe>();
        }

        private void Start()
        {
            Application.runInBackground = true;
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = 120;
            outputRoot = ArgumentValue("-khufu-v5-profile-output", Path.Combine(Application.persistentDataPath, "khufu-v5-profile"));
            runLabel = Sanitize(ArgumentValue("-khufu-v5-profile-label", "baseline"));
            Directory.CreateDirectory(outputRoot);
            initialScreenshotPath = Path.Combine(outputRoot, runLabel + "-windows-player-initial.png");
            operatorScreenshotPath = Path.Combine(outputRoot, runLabel + "-windows-player-operator.png");
            startedAt = Time.realtimeSinceStartupAsDouble;
            MeasureVisibleScene();
            Debug.Log("CHANNEL_PLAY_KHUFU_V5_PROFILE result=started label=" + runLabel + " output=\"" + outputRoot + "\"");
        }

        private void Update()
        {
            if (finished)
            {
                return;
            }

            if (session == null)
            {
                session = FindAnyObjectByType<TraitorEscapeMvpSession>();
            }

            var elapsed = Time.realtimeSinceStartupAsDouble - startedAt;
            if (!initialCaptureQueued && elapsed >= 2d)
            {
                ScreenCapture.CaptureScreenshot(initialScreenshotPath, 1);
                initialCaptureQueued = true;
            }

            if (elapsed < WarmupSeconds)
            {
                return;
            }

            var sampleElapsed = elapsed - WarmupSeconds;
            if (sampleElapsed < ParticipantSampleSeconds)
            {
                MoveParticipant((float)(sampleElapsed / ParticipantSampleSeconds));
            }
            else
            {
                PrepareOperator(sampleElapsed - ParticipantSampleSeconds);
            }

            CaptureSample();
            if (sampleElapsed >= ParticipantSampleSeconds + OperatorSampleSeconds)
            {
                Finish();
            }
        }

        private void LateUpdate()
        {
            if (!operatorPrepared || session == null || Camera.main == null)
            {
                return;
            }

            var elapsed = (float)(Time.realtimeSinceStartupAsDouble - startedAt - WarmupSeconds - ParticipantSampleSeconds);
            var normalized = Mathf.Clamp01(elapsed / OperatorSampleSeconds);
            Camera.main.transform.position = new Vector3(Mathf.Lerp(-55f, 105f, normalized), 135f, Mathf.Sin(normalized * Mathf.PI * 2f) * 55f);
            Camera.main.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        }

        private void MoveParticipant(float normalized)
        {
            if (session == null || session.DiagnosticPlayer == null)
            {
                return;
            }

            var scaled = Mathf.Clamp01(normalized) * (ParticipantRoute.Length - 1);
            var segment = Mathf.Min(Mathf.FloorToInt(scaled), ParticipantRoute.Length - 2);
            var position = Vector3.Lerp(ParticipantRoute[segment], ParticipantRoute[segment + 1], scaled - segment);
            session.DiagnosticPlayer.position = position;
        }

        private void PrepareOperator(double operatorElapsed)
        {
            if (!operatorPrepared && session != null)
            {
                session.DiagnosticPrepareVisualProof(true, false, true);
                operatorPrepared = true;
            }

            if (!operatorCaptureQueued && operatorElapsed >= 2d)
            {
                ScreenCapture.CaptureScreenshot(operatorScreenshotPath, 1);
                operatorCaptureQueued = true;
            }
        }

        private void CaptureSample()
        {
            frameMilliseconds.Add(Time.unscaledDeltaTime * 1000d);
            FrameTimingManager.CaptureFrameTimings();
            if (FrameTimingManager.GetLatestTimings(1, timingBuffer) > 0)
            {
                AddPositive(cpuMilliseconds, timingBuffer[0].cpuFrameTime);
                AddPositive(mainThreadMilliseconds, timingBuffer[0].cpuMainThreadFrameTime);
                AddPositive(renderThreadMilliseconds, timingBuffer[0].cpuRenderThreadFrameTime);
                AddPositive(gpuMilliseconds, timingBuffer[0].gpuFrameTime);
            }

            maximumAllocatedBytes = Math.Max(maximumAllocatedBytes, Profiler.GetTotalAllocatedMemoryLong());
            maximumReservedBytes = Math.Max(maximumReservedBytes, Profiler.GetTotalReservedMemoryLong());
            maximumMonoBytes = Math.Max(maximumMonoBytes, Profiler.GetMonoUsedSizeLong());
        }

        private void Finish()
        {
            finished = true;
            var receipt = BuildReceipt();
            var receiptPath = Path.Combine(outputRoot, runLabel + "-performance.md");
            File.WriteAllText(receiptPath, receipt, Encoding.UTF8);
            Debug.Log("CHANNEL_PLAY_KHUFU_V5_PROFILE result=recorded label=" + runLabel + " samples=" + frameMilliseconds.Count + " receipt=\"" + receiptPath + "\"");
            Application.Quit(0);
        }

        private string BuildReceipt()
        {
            var builder = new StringBuilder();
            builder.AppendLine("# Khufu V5 Windows Player Performance " + runLabel);
            builder.AppendLine();
            builder.AppendLine("- Result: **recorded**");
            builder.AppendLine("- Unity: `" + Application.unityVersion + "`");
            builder.AppendLine("- OS: `" + SystemInfo.operatingSystem + "`");
            builder.AppendLine("- CPU: `" + SystemInfo.processorType + "` (" + SystemInfo.processorCount + " logical)");
            builder.AppendLine("- GPU: `" + SystemInfo.graphicsDeviceName + "` / `" + SystemInfo.graphicsDeviceVersion + "`");
            builder.AppendLine("- RAM: `" + SystemInfo.systemMemorySize + " MB`; reported VRAM: `" + SystemInfo.graphicsMemorySize + " MB`");
            builder.AppendLine("- Resolution: `" + Screen.width + "x" + Screen.height + "`, quality `" + QualitySettings.names[QualitySettings.GetQualityLevel()] + "`");
            builder.AppendLine("- Frame pacing: target `120 fps`, vSync `0`");
            builder.AppendLine("- Procedure: `5s warm-up + 15s participant route + 15s operator route`");
            builder.AppendLine("- Samples: `" + frameMilliseconds.Count + "`");
            AppendMetric(builder, "Frame time", frameMilliseconds);
            AppendMetric(builder, "CPU frame", cpuMilliseconds);
            AppendMetric(builder, "Main thread", mainThreadMilliseconds);
            AppendMetric(builder, "Render thread", renderThreadMilliseconds);
            AppendMetric(builder, "GPU frame", gpuMilliseconds);
            builder.AppendLine("- Maximum total allocated memory: `" + Megabytes(maximumAllocatedBytes) + " MB`");
            builder.AppendLine("- Maximum total reserved memory: `" + Megabytes(maximumReservedBytes) + " MB`");
            builder.AppendLine("- Maximum managed memory: `" + Megabytes(maximumMonoBytes) + " MB`");
            builder.AppendLine("- Visible renderers: `" + visibleRendererCount + "`");
            builder.AppendLine("- Visible mesh vertices: `" + visibleVertices + "`");
            builder.AppendLine("- Visible mesh triangles: `" + visibleTriangles + "`");
            builder.AppendLine();
            builder.AppendLine("PROFILE_RESULT: recorded");
            return builder.ToString();
        }

        private void MeasureVisibleScene()
        {
            foreach (var renderer in FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!renderer.enabled || !renderer.gameObject.activeInHierarchy)
                {
                    continue;
                }

                visibleRendererCount++;
                Mesh mesh = null;
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter != null)
                {
                    mesh = filter.sharedMesh;
                }
                else if (renderer is SkinnedMeshRenderer skinned)
                {
                    mesh = skinned.sharedMesh;
                }

                if (mesh == null)
                {
                    continue;
                }

                visibleVertices += mesh.vertexCount;
                visibleTriangles += mesh.triangles.LongLength / 3L;
            }
        }

        private static void AppendMetric(StringBuilder builder, string name, List<double> values)
        {
            if (values.Count == 0)
            {
                builder.AppendLine("- " + name + ": `unavailable`");
                return;
            }

            var sorted = values.OrderBy(value => value).ToArray();
            builder.AppendLine("- " + name + " median: `" + Percentile(sorted, 0.50d).ToString("F3", CultureInfo.InvariantCulture) + " ms`; p95: `" + Percentile(sorted, 0.95d).ToString("F3", CultureInfo.InvariantCulture) + " ms`");
        }

        private static double Percentile(IReadOnlyList<double> sorted, double percentile)
        {
            if (sorted.Count == 0)
            {
                return 0d;
            }

            var index = Math.Min(sorted.Count - 1, Math.Max(0, (int)Math.Ceiling(percentile * sorted.Count) - 1));
            return sorted[index];
        }

        private static void AddPositive(List<double> target, double value)
        {
            if (value > 0d && !double.IsNaN(value) && !double.IsInfinity(value))
            {
                target.Add(value);
            }
        }

        private static string ArgumentValue(string key, string fallback)
        {
            var arguments = Environment.GetCommandLineArgs();
            for (var index = 0; index < arguments.Length - 1; index++)
            {
                if (string.Equals(arguments[index], key, StringComparison.OrdinalIgnoreCase))
                {
                    return arguments[index + 1];
                }
            }
            return fallback;
        }

        private static string Sanitize(string value)
        {
            var characters = value.Where(character => char.IsLetterOrDigit(character) || character == '-' || character == '_').ToArray();
            return characters.Length == 0 ? "run" : new string(characters);
        }

        private static string Megabytes(long bytes)
        {
            return (bytes / 1048576d).ToString("F1", CultureInfo.InvariantCulture);
        }
    }
}

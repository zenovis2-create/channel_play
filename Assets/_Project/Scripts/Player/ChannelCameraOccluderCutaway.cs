using System.Collections.Generic;
using UnityEngine;

namespace ChannelPlay.Player
{
    [DefaultExecutionOrder(200)]
    public sealed class ChannelCameraOccluderCutaway : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private Transform occluderRoot;
        [SerializeField] private float lookHeight = 1.35f;
        [SerializeField] private float scanInterval = 0.08f;
        [SerializeField] private float minCutawayDistance = 0.45f;
        [SerializeField] private float valleyGatePylonCameraPadding = 1.5f;

        private readonly List<Renderer> rendererCache = new List<Renderer>();
        private readonly HashSet<Renderer> activeCutaways = new HashSet<Renderer>();
        private readonly HashSet<Renderer> nextCutaways = new HashSet<Renderer>();
        private readonly Dictionary<Renderer, bool> originalForceRenderingOff = new Dictionary<Renderer, bool>();
        private readonly Dictionary<Renderer, bool> originalEnabled = new Dictionary<Renderer, bool>();

        private float nextScanTime;

        public int ActiveCutawayCount => activeCutaways.Count;

        public int DiagnosticActiveValleyGatePylonCount
        {
            get
            {
                var count = 0;
                foreach (var renderer in activeCutaways)
                {
                    if (renderer != null && IsValleyGatePylon(renderer.gameObject.name))
                    {
                        count++;
                    }
                }

                return count;
            }
        }

        public void Configure(Transform newTarget, Transform newOccluderRoot)
        {
            target = newTarget;
            occluderRoot = newOccluderRoot;
            RefreshRendererCache();
            ForceRefresh();
        }

        public int ForceRefresh()
        {
            if (target == null || occluderRoot == null)
            {
                RestoreAll();
                return 0;
            }

            if (rendererCache.Count == 0)
            {
                RefreshRendererCache();
            }

            var cameraPosition = transform.position;
            var targetPoint = target.position + Vector3.up * lookHeight;
            var delta = targetPoint - cameraPosition;
            var distance = delta.magnitude;
            if (distance <= minCutawayDistance)
            {
                RestoreAll();
                return 0;
            }

            var ray = new Ray(cameraPosition, delta / distance);
            nextCutaways.Clear();
            foreach (var candidate in rendererCache)
            {
                if (ShouldCutaway(candidate, ray, distance))
                {
                    nextCutaways.Add(candidate);
                }
            }

            foreach (var renderer in activeCutaways)
            {
                if (!nextCutaways.Contains(renderer))
                {
                    Restore(renderer);
                }
            }

            foreach (var renderer in nextCutaways)
            {
                if (!activeCutaways.Contains(renderer))
                {
                    Cutaway(renderer);
                }
            }

            activeCutaways.Clear();
            foreach (var renderer in nextCutaways)
            {
                activeCutaways.Add(renderer);
            }

            return activeCutaways.Count;
        }

        public int DiagnosticVisibleOccluderCount()
        {
            if (target == null || occluderRoot == null)
            {
                return 0;
            }

            if (rendererCache.Count == 0)
            {
                RefreshRendererCache();
            }

            var cameraPosition = transform.position;
            var targetPoint = target.position + Vector3.up * lookHeight;
            var delta = targetPoint - cameraPosition;
            var distance = delta.magnitude;
            if (distance <= minCutawayDistance)
            {
                return 0;
            }

            var ray = new Ray(cameraPosition, delta / distance);
            var visible = 0;
            foreach (var candidate in rendererCache)
            {
                if (ShouldCutaway(candidate, ray, distance) && candidate.enabled && !candidate.forceRenderingOff)
                {
                    visible++;
                }
            }

            return visible;
        }

        public string DiagnosticCandidateState(Renderer renderer)
        {
            if (target == null || occluderRoot == null) return "unconfigured";
            var cameraPosition = transform.position;
            var targetPoint = target.position + Vector3.up * lookHeight;
            var delta = targetPoint - cameraPosition;
            var distance = delta.magnitude;
            if (distance <= minCutawayDistance) return "view-distance-too-small";
            EvaluateCandidate(renderer, new Ray(cameraPosition, delta / distance), distance, out var state);
            return state;
        }

        private void LateUpdate()
        {
            if (Time.time < nextScanTime)
            {
                return;
            }

            nextScanTime = Time.time + scanInterval;
            ForceRefresh();
        }

        private void OnDisable()
        {
            RestoreAll();
        }

        private void OnDestroy()
        {
            RestoreAll();
        }

        private void RefreshRendererCache()
        {
            rendererCache.Clear();
            if (occluderRoot == null)
            {
                return;
            }

            occluderRoot.GetComponentsInChildren(true, rendererCache);
        }

        private bool ShouldCutaway(Renderer renderer, Ray ray, float distance)
        {
            return EvaluateCandidate(renderer, ray, distance, out _);
        }

        private bool EvaluateCandidate(Renderer renderer, Ray ray, float distance, out string state)
        {
            if (renderer == null || renderer.transform == null || !renderer.gameObject.activeInHierarchy)
            {
                state = "reject:inactive-or-null";
                return false;
            }

            if (target != null && renderer.transform.IsChildOf(target))
            {
                state = "reject:target-child";
                return false;
            }

            if (!IsCutawayCandidate(renderer.gameObject.name))
            {
                state = "reject:non-candidate";
                return false;
            }

            var bounds = renderer.bounds;
            if (bounds.size.sqrMagnitude < 0.08f)
            {
                state = "reject:tiny-bounds";
                return false;
            }

            if (IsValleyGatePylon(renderer.gameObject.name))
            {
                var cameraClearance = bounds;
                cameraClearance.Expand(valleyGatePylonCameraPadding * 2f);
                if (cameraClearance.Contains(ray.origin))
                {
                    state = "accept:pylon-camera-clearance";
                    return true;
                }

            }

            if (!bounds.IntersectRay(ray, out var hitDistance))
            {
                state = "reject:ray-miss";
                return false;
            }

            var accepted = hitDistance > minCutawayDistance && hitDistance < distance - minCutawayDistance;
            state = accepted ? "accept:ray" : "reject:hit-outside-segment";
            return accepted;
        }

        private static bool IsCutawayCandidate(string objectName)
        {
            if (string.IsNullOrEmpty(objectName))
            {
                return false;
            }

            if (objectName.StartsWith("Collision_") ||
                objectName.StartsWith("Gameplay_") ||
                objectName.StartsWith("Lighting_") ||
                objectName.StartsWith("CP_Temp"))
            {
                return false;
            }

            if (IsValleyGatePylon(objectName))
            {
                return true;
            }

            var lower = objectName.ToLowerInvariant();
            if (lower.Contains("floor") ||
                lower.Contains("stair") ||
                lower.Contains("plate") ||
                lower.Contains("rubble") ||
                lower.Contains("pot") ||
                lower.Contains("jar"))
            {
                return false;
            }

            return lower.Contains("roof") ||
                lower.Contains("ceiling") ||
                lower.Contains("beam") ||
                lower.Contains("wall") ||
                lower.Contains("pyramid") ||
                lower.Contains("column") ||
                lower.Contains("pillar") ||
                lower.Contains("lintel") ||
                lower.Contains("tier") ||
                lower.Contains("course");
        }

        private static bool IsValleyGatePylon(string objectName)
        {
            return string.Equals(objectName, "V5_Valley_Gate_Pylon_-1", System.StringComparison.Ordinal) ||
                string.Equals(objectName, "V5_Valley_Gate_Pylon_1", System.StringComparison.Ordinal);
        }

        private void Cutaway(Renderer renderer)
        {
            if (renderer == null)
            {
                return;
            }

            if (IsValleyGatePylon(renderer.gameObject.name))
            {
                if (!originalEnabled.ContainsKey(renderer))
                {
                    originalEnabled[renderer] = renderer.enabled;
                }

                renderer.enabled = false;
                return;
            }

            if (!originalForceRenderingOff.ContainsKey(renderer))
            {
                originalForceRenderingOff[renderer] = renderer.forceRenderingOff;
            }

            renderer.forceRenderingOff = true;
        }

        private void Restore(Renderer renderer)
        {
            if (renderer == null)
            {
                return;
            }

            if (originalEnabled.TryGetValue(renderer, out var originalEnabledValue))
            {
                renderer.enabled = originalEnabledValue;
                originalEnabled.Remove(renderer);
                return;
            }

            if (originalForceRenderingOff.TryGetValue(renderer, out var originalValue))
            {
                renderer.forceRenderingOff = originalValue;
                originalForceRenderingOff.Remove(renderer);
            }
            else
            {
                renderer.forceRenderingOff = false;
            }
        }

        private void RestoreAll()
        {
            foreach (var renderer in activeCutaways)
            {
                Restore(renderer);
            }

            activeCutaways.Clear();
            nextCutaways.Clear();
        }
    }
}

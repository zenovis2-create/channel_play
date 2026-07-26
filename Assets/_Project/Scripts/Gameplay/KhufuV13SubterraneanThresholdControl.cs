using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuV13SubterraneanThresholdControl : MonoBehaviour
    {
        [SerializeField] private GameObject[] predecessorTargets = Array.Empty<GameObject>();
        [SerializeField] private BoxCollider[] collisionProxies = Array.Empty<BoxCollider>();
        [SerializeField] private Transform[] routeAnchors = Array.Empty<Transform>();
        [SerializeField] private Transform solidPitBacking;

        public IReadOnlyList<GameObject> PredecessorTargets => predecessorTargets;
        public IReadOnlyList<BoxCollider> CollisionProxies => collisionProxies;
        public IReadOnlyList<Transform> RouteAnchors => routeAnchors;
        public Transform SolidPitBacking => solidPitBacking;

        public void Configure(IEnumerable<GameObject> targets, IEnumerable<BoxCollider> proxies,
            IEnumerable<Transform> anchors, Transform pitBacking)
        {
            predecessorTargets = targets.Where(item => item != null)
                .Distinct()
                .OrderBy(item => item.name, StringComparer.Ordinal)
                .ToArray();
            collisionProxies = proxies.Where(item => item != null)
                .Distinct()
                .OrderBy(item => item.name, StringComparer.Ordinal)
                .ToArray();
            routeAnchors = anchors.Where(item => item != null).ToArray();
            solidPitBacking = pitBacking;
        }
    }
}

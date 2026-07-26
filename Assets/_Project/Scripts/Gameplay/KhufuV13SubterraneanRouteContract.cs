using System.Collections.Generic;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public static class KhufuV13SubterraneanRouteContract
    {
        public const float PassageClearWidth = 2.50f;
        public const float PassageClearHeight = 2.40f;
        public const float JunctionTransitionEndRelease = 1.45f;
        public const float JunctionInnerWallRelease = 1.80f;
        public const float LandingRoofEndRelease = 1.55f;
        public const float MaximumAnchorError = 0.40f;
        public const float MinimumGroundedRatio = 0.90f;
        public const float BoundaryStartDistance = 1.50f;
        public const float MaximumControlStep = 0.10f;

        public static readonly Vector3 V10BranchAnchor =
            new Vector3(-2.5f, 3.8f, -19.2f);
        public static readonly Vector3 SubterraneanLanding =
            new Vector3(0f, -3.8f, -5.6f);
        public static readonly Vector3 JunctionEnd =
            new Vector3(1.45f, 3.8f, -19.2f);
        public static readonly Vector3 ChamberDoor =
            new Vector3(0f, -3.8f, -1.6f);
        public static readonly Vector3 ChamberCenter =
            new Vector3(0f, -3.8f, 1.5f);
        public static readonly Vector3 PitInspection =
            new Vector3(0f, -3.8f, 2.35f);
        public static readonly Vector3 BoundaryPoint =
            new Vector3(2.5f, -3.8f, 1.5f);
        public static readonly Vector3 BoundaryOutward = Vector3.right;

        public static float DescentAngleDegrees
        {
            get
            {
                var delta = SubterraneanLanding - JunctionEnd;
                var horizontal = new Vector2(delta.x, delta.z).magnitude;
                return Mathf.Atan2(Mathf.Abs(delta.y), horizontal) * Mathf.Rad2Deg;
            }
        }

        public static IReadOnlyList<Vector3> ForwardRoute()
        {
            return new[]
            {
                V10BranchAnchor,
                JunctionEnd,
                SubterraneanLanding,
                ChamberDoor,
                ChamberCenter,
                PitInspection
            };
        }

        public static IReadOnlyList<Vector3> RoundTripRoute()
        {
            return new[]
            {
                V10BranchAnchor,
                JunctionEnd,
                SubterraneanLanding,
                ChamberDoor,
                ChamberCenter,
                PitInspection,
                ChamberCenter,
                ChamberDoor,
                SubterraneanLanding,
                JunctionEnd,
                V10BranchAnchor
            };
        }
    }
}

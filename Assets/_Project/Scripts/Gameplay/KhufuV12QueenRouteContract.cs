using System.Collections.Generic;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public static class KhufuV12QueenRouteContract
    {
        public static readonly Vector3 GalleryFoot = KhufuV10RouteContract.GalleryFoot;
        public static readonly Vector3 ChamberCenter = KhufuV10RouteContract.QueensChamber;
        public static readonly Vector3 ThresholdDirection =
            (ChamberCenter - GalleryFoot).normalized;
        public static readonly Quaternion ThresholdRotation =
            Quaternion.LookRotation(ThresholdDirection, Vector3.up);
        public static readonly Vector3 ThresholdRight = ThresholdRotation * Vector3.right;
        public static readonly Vector3 ThresholdCenter =
            GalleryFoot + ThresholdDirection * 2.82f;
        public static readonly Vector3 ThresholdApproach =
            GalleryFoot + ThresholdDirection * 0.55f + ThresholdRight * 0.30f;
        public static readonly Vector3 ThresholdCrossing =
            ThresholdCenter + ThresholdRight * 0.30f;
        public static readonly Vector3 ChamberDoor =
            new Vector3(-1.8f, 5.35f, -5.05f);
        public static readonly Vector3 PassageTurn =
            Vector3.Lerp(ThresholdCenter, ChamberDoor, 0.55f);
        public static readonly Vector3 NicheStop =
            new Vector3(0.05f, 5.35f, -2.8f);

        public static IReadOnlyList<Vector3> ForwardRoute()
        {
            return new[]
            {
                GalleryFoot,
                ThresholdCenter,
                PassageTurn,
                ChamberDoor,
                ChamberCenter,
                NicheStop
            };
        }

        public static IReadOnlyList<Vector3> RoundTripRoute()
        {
            return new[]
            {
                GalleryFoot,
                ThresholdApproach,
                ThresholdCrossing,
                ThresholdCenter,
                PassageTurn,
                ChamberDoor,
                ChamberCenter,
                NicheStop,
                ChamberCenter,
                ChamberDoor,
                PassageTurn,
                ThresholdCenter,
                ThresholdCrossing,
                ThresholdApproach,
                GalleryFoot
            };
        }
    }
}

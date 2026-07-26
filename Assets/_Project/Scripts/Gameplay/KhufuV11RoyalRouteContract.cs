using System.Collections.Generic;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public static class KhufuV11RoyalRouteContract
    {
        public static readonly Vector3 Forward = Vector3.forward;
        public static readonly Quaternion Rotation = Quaternion.LookRotation(Forward, Vector3.up);
        public static readonly Vector3 Right = Rotation * Vector3.right;

        public static readonly Vector3 GreatStepEntry = KhufuV10RouteContract.GalleryTop + HorizontalGalleryForward() * 0.35f;
        public static readonly Vector3 RoyalThreshold = new Vector3(6.3f, 10.85f, 5.2f);
        public static readonly Vector3 EntryEnd = new Vector3(6.3f, 10.85f, 5.45f);
        public static readonly Vector3 AntechamberCenter = new Vector3(6.3f, 10.85f, 5.7f);
        public static readonly Vector3 KingsEntrance = new Vector3(6.3f, 10.85f, 6.8f);
        public static readonly Vector3 KingsChamberCenter = new Vector3(6.3f, 10.85f, 9.5f);
        public static readonly Vector3 SarcophagusCenter = KingsChamberCenter - Right * 2.65f + Forward * 0.55f;

        public static IReadOnlyList<Vector3> TraversalRoute()
        {
            return new[]
            {
                GreatStepEntry,
                RoyalThreshold,
                EntryEnd,
                AntechamberCenter,
                KingsEntrance,
                KingsChamberCenter,
                SarcophagusCenter + Right * 1.55f
            };
        }

        public static Vector3 StackedDisplayCenter()
        {
            return KingsChamberCenter + Vector3.up * 9.15f;
        }

        private static Vector3 HorizontalGalleryForward()
        {
            var direction = KhufuV10RouteContract.GalleryTop - KhufuV10RouteContract.GalleryFoot;
            direction.y = 0f;
            return direction.normalized;
        }
    }
}

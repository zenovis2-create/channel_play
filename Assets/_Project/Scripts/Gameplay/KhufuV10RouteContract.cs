using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public static class KhufuV10RouteContract
    {
        public static readonly Vector3 Entrance = new Vector3(-3.5f, 5f, -23.3f);
        public static readonly Vector3 Branch = new Vector3(-2.5f, 3.8f, -19.2f);
        public static readonly Vector3 GalleryFoot = new Vector3(3.2f, 5.4f, -7.4f);
        public static readonly Vector3 GalleryTop = new Vector3(7f, 10.5f, 4.4f);
        public static readonly Vector3 QueensChamber = new Vector3(-1.8f, 5.35f, -2.8f);

        public static IReadOnlyList<Vector3> NormalRoute()
        {
            var ascending = AscendingRoutePoints();
            var result = new List<Vector3> { Entrance, Branch };
            result.AddRange(ascending.Skip(1));
            result.Add(GreatStepStop());
            result.Add(GalleryFoot);
            result.AddRange(HybridReturnPoints());
            result.Add(Branch);
            result.Add(Entrance);
            return result;
        }

        public static IReadOnlyList<Vector3> AscendingRoutePoints()
        {
            return new[]
            {
                Branch,
                new Vector3(3.3f, 3.95f, -18.1f),
                new Vector3(8.4f, 4.2f, -14.3f),
                new Vector3(6f, 4.65f, -10.8f),
                GalleryFoot
            };
        }

        public static IReadOnlyList<Vector3> HybridReturnPoints()
        {
            var rotation = GalleryRotation();
            var right = rotation * Vector3.right;
            var forward = rotation * Vector3.forward;
            var sideDoor = GalleryFoot + right * 3.2f - forward * 2f;
            var startOffset = GalleryFoot + right * 8.5f + forward * 2f;
            var start = new Vector3(startOffset.x, sideDoor.y, startOffset.z);
            return new[]
            {
                sideDoor,
                start,
                new Vector3(14f, 4f, -13f),
                new Vector3(14f, 2.2f, -18f),
                new Vector3(13f, 1.6f, -22f),
                new Vector3(4f, 3.8f, -22f)
            };
        }

        public static Vector3 GreatStepStop()
        {
            var forward = GalleryRotation() * Vector3.forward;
            return GalleryTop - forward * 0.9f;
        }

        public static Vector3 HistoricServiceMouth()
        {
            var rotation = GalleryRotation();
            return GalleryFoot - rotation * Vector3.right * 2.8f + rotation * Vector3.up * 0.9f +
                   rotation * Vector3.forward * 0.85f;
        }

        public static Quaternion GalleryRotation()
        {
            return Quaternion.LookRotation((GalleryTop - GalleryFoot).normalized, Vector3.up);
        }
    }
}

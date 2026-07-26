using System.Collections.Generic;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuV13ControllerHitRecorder : MonoBehaviour
    {
        public const string CallbackName = "OnControllerColliderHit";

        private readonly HashSet<string> seenHitNames = new HashSet<string>();

        public string LastHitName { get; private set; } = string.Empty;
        public string LastSideHitName { get; private set; } = string.Empty;
        public string LastGroundHitName { get; private set; } = string.Empty;
        public int LastHitFrame { get; private set; } = -1;
        public int LastSideHitFrame { get; private set; } = -1;
        public int LastMoveFrame { get; private set; } = -1;
        public CollisionFlags LastMoveFlags { get; private set; }
        public IReadOnlyCollection<string> SeenHitNames => seenHitNames;
        public bool HasSameFrameSideProof =>
            (LastMoveFlags & CollisionFlags.Sides) != 0 &&
            LastMoveFrame >= 0 &&
            LastMoveFrame == LastSideHitFrame;

        public void RecordMove(CollisionFlags flags)
        {
            LastMoveFlags = flags;
            LastMoveFrame = Time.frameCount;
        }

        public void ClearFrame()
        {
            LastHitName = string.Empty;
            LastSideHitName = string.Empty;
            LastGroundHitName = string.Empty;
            LastHitFrame = -1;
            LastSideHitFrame = -1;
            LastMoveFrame = -1;
            LastMoveFlags = CollisionFlags.None;
        }

        private void OnControllerColliderHit(ControllerColliderHit hit)
        {
            LastHitName = hit.collider == null ? string.Empty : hit.collider.name;
            LastHitFrame = Time.frameCount;
            if (!string.IsNullOrEmpty(LastHitName)) seenHitNames.Add(LastHitName);
            if (hit.normal.y < 0.3f)
            {
                LastSideHitName = LastHitName;
                LastSideHitFrame = Time.frameCount;
            }
            else if (hit.normal.y > 0.7f)
            {
                LastGroundHitName = LastHitName;
            }
        }
    }
}

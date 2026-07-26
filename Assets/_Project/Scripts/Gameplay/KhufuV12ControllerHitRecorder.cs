using System.Collections.Generic;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuV12ControllerHitRecorder : MonoBehaviour
    {
        private readonly HashSet<string> seenHitNames = new HashSet<string>();

        public string LastHitName { get; private set; } = string.Empty;
        public string LastSideHitName { get; private set; } = string.Empty;
        public string LastGroundHitName { get; private set; } = string.Empty;
        public int LastHitFrame { get; private set; } = -1;
        public int LastSideHitFrame { get; private set; } = -1;
        public IReadOnlyCollection<string> SeenHitNames => seenHitNames;

        public void ClearFrame()
        {
            LastHitName = string.Empty;
            LastSideHitName = string.Empty;
            LastGroundHitName = string.Empty;
            LastHitFrame = -1;
            LastSideHitFrame = -1;
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

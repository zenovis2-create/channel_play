using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuControllerHitRecorder : MonoBehaviour
    {
        public string LastHitName { get; private set; } = string.Empty;
        public Vector3 LastHitPoint { get; private set; }
        public string LastSideHitName { get; private set; } = string.Empty;
        public Vector3 LastSideHitNormal { get; private set; }
        public string LastGroundHitName { get; private set; } = string.Empty;
        public Vector3 LastGroundHitNormal { get; private set; }
        public string LastAmbiguousHitName { get; private set; } = string.Empty;
        public Vector3 LastAmbiguousHitNormal { get; private set; }

        public void Clear()
        {
            LastHitName = string.Empty;
            LastHitPoint = Vector3.zero;
            LastSideHitName = string.Empty;
            LastSideHitNormal = Vector3.zero;
            LastGroundHitName = string.Empty;
            LastGroundHitNormal = Vector3.zero;
            LastAmbiguousHitName = string.Empty;
            LastAmbiguousHitNormal = Vector3.zero;
        }

        private void OnControllerColliderHit(ControllerColliderHit hit)
        {
            LastHitName = hit.collider == null ? string.Empty : hit.collider.name;
            LastHitPoint = hit.point;
            if (hit.normal.y < 0.3f)
            {
                LastSideHitName = LastHitName;
                LastSideHitNormal = hit.normal;
            }
            else if (hit.normal.y > 0.7f)
            {
                LastGroundHitName = LastHitName;
                LastGroundHitNormal = hit.normal;
            }
            else
            {
                LastAmbiguousHitName = LastHitName;
                LastAmbiguousHitNormal = hit.normal;
            }
        }
    }
}

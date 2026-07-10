using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuControllerHitRecorder : MonoBehaviour
    {
        public string LastHitName { get; private set; } = string.Empty;
        public Vector3 LastHitPoint { get; private set; }

        public void Clear()
        {
            LastHitName = string.Empty;
            LastHitPoint = Vector3.zero;
        }

        private void OnControllerColliderHit(ControllerColliderHit hit)
        {
            LastHitName = hit.collider == null ? string.Empty : hit.collider.name;
            LastHitPoint = hit.point;
        }
    }
}

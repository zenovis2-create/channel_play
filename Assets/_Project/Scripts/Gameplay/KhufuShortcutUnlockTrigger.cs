using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuShortcutUnlockTrigger : MonoBehaviour
    {
        public KhufuShortcutGate gate;

        private void OnTriggerEnter(Collider other)
        {
            if (gate != null && other.GetComponent<CharacterController>() != null)
            {
                gate.Unlock();
            }
        }
    }
}

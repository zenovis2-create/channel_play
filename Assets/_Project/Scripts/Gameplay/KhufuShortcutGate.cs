using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuShortcutGate : MonoBehaviour
    {
        [SerializeField] private bool locked = true;

        public bool IsLocked => locked;

        public void Unlock()
        {
            locked = false;
            gameObject.SetActive(false);
        }

        public void ResetLocked()
        {
            locked = true;
            gameObject.SetActive(true);
        }
    }

}

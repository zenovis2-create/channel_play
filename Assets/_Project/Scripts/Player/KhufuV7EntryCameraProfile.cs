using UnityEngine;

namespace ChannelPlay.Player
{
    [DefaultExecutionOrder(50)]
    public sealed class KhufuV7EntryCameraProfile : MonoBehaviour
    {
        public static readonly Vector3 EntryOffset = new Vector3(3f, 7f, -12f);
        public static readonly Vector3 EntryLookAheadOffset = new Vector3(-7f, 0f, 0f);

        public bool Applied { get; private set; }

        private void Update()
        {
            if (Applied) return;
            var camera = Camera.main;
            var follow = camera == null ? null : camera.GetComponent<ChannelFollowCamera>();
            if (follow == null) return;
            follow.SetOffset(EntryOffset);
            follow.SetLookAheadOffset(EntryLookAheadOffset);
            Applied = true;
            Debug.Log("CHANNEL_PLAY_KHUFU_V7_CAMERA_PROFILE result=applied offset=" + EntryOffset +
                " look_ahead=" + EntryLookAheadOffset);
        }
    }
}

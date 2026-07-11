using UnityEngine;

namespace ChannelPlay.Player
{
    [DefaultExecutionOrder(100)]
    public sealed class ChannelFollowCamera : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private Vector3 offset = new Vector3(0f, 6f, -8f);
        [SerializeField] private float followSpeed = 7f;
        [SerializeField] private float lookHeight = 1.4f;
        [SerializeField] private Vector3 lookAheadOffset;

        public Vector3 CurrentOffset => offset;
        public Vector3 CurrentLookAheadOffset => lookAheadOffset;

        public void SetTarget(Transform newTarget)
        {
            target = newTarget;
        }

        public void SetOffset(Vector3 newOffset)
        {
            offset = newOffset;
        }

        public void SetLookAheadOffset(Vector3 newLookAheadOffset)
        {
            lookAheadOffset = newLookAheadOffset;
        }

        private void LateUpdate()
        {
            if (target == null)
            {
                return;
            }

            var desiredPosition = target.position + offset;
            transform.position = Vector3.Lerp(transform.position, desiredPosition, followSpeed * Time.deltaTime);
            transform.LookAt(target.position + Vector3.up * lookHeight + lookAheadOffset);
        }
    }
}

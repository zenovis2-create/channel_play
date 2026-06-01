using UnityEngine;

namespace ChannelPlay.Player
{
    [RequireComponent(typeof(CharacterController))]
    public sealed class ChannelPlayerController : MonoBehaviour
    {
        [SerializeField] private float walkSpeed = 4.5f;
        [SerializeField] private float sprintSpeed = 7.0f;
        [SerializeField] private float jumpHeight = 1.2f;
        [SerializeField] private float gravity = -18.0f;

        private CharacterController controller;
        private Vector3 verticalVelocity;

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
        }

        private void Update()
        {
            var input = new Vector3(Input.GetAxisRaw("Horizontal"), 0f, Input.GetAxisRaw("Vertical"));
            input = Vector3.ClampMagnitude(input, 1f);

            var speed = Input.GetKey(KeyCode.LeftShift) ? sprintSpeed : walkSpeed;
            var movement = input * speed;

            if (controller.isGrounded && verticalVelocity.y < 0f)
            {
                verticalVelocity.y = -2f;
            }

            if (controller.isGrounded && Input.GetButtonDown("Jump"))
            {
                verticalVelocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);
            }

            verticalVelocity.y += gravity * Time.deltaTime;
            controller.Move((movement + verticalVelocity) * Time.deltaTime);

            var planar = new Vector3(movement.x, 0f, movement.z);
            if (planar.sqrMagnitude > 0.001f)
            {
                transform.rotation = Quaternion.LookRotation(planar);
            }
        }
    }
}

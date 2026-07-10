using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class TraitorEscapeMapBindings : MonoBehaviour
    {
        [Header("Authored gameplay objects")]
        public Transform playerSpawn;
        public Transform missionTerminal;
        public Transform shopTerminal;
        public Transform exitDoor;
        public Transform scannerBeacon;
        public Transform sunKey;
        public Transform crownKey;
        public Transform earthKey;

        [Header("Operator camera")]
        public Vector3 operatorStart = new Vector3(25f, 72f, 0f);
        public Vector2 operatorXBounds = new Vector2(-105f, 165f);
        public Vector2 operatorZBounds = new Vector2(-100f, 100f);
        public Vector2 operatorHeightBounds = new Vector2(12f, 90f);

        public bool IsValid(out string reason)
        {
            if (playerSpawn == null || missionTerminal == null || shopTerminal == null ||
                exitDoor == null || scannerBeacon == null || sunKey == null || crownKey == null ||
                earthKey == null)
            {
                reason = "One or more authored gameplay bindings are missing.";
                return false;
            }

            var mapRoot = transform;
            var values = new[] { playerSpawn, missionTerminal, shopTerminal, exitDoor, scannerBeacon, sunKey, crownKey, earthKey };
            foreach (var value in values)
            {
                if (!value.IsChildOf(mapRoot))
                {
                    reason = value.name + " is outside the bound map root.";
                    return false;
                }
            }

            reason = string.Empty;
            return true;
        }
    }
}

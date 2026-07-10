using System;
using System.Collections.Generic;
using System.Linq;

namespace ChannelPlay.Gameplay
{
    public enum KhufuKeyId
    {
        Sun,
        Crown,
        Earth,
    }

    public sealed class KhufuObjectiveState
    {
        private static readonly KhufuKeyId[] RequiredKeys =
        {
            KhufuKeyId.Sun,
            KhufuKeyId.Crown,
            KhufuKeyId.Earth,
        };

        private readonly HashSet<KhufuKeyId> physicalKeys = new HashSet<KhufuKeyId>();

        public int PhysicalKeyCount => physicalKeys.Count;
        public bool HasAllPhysicalKeys => physicalKeys.Count == RequiredKeys.Length;
        public bool TerminalConfirmed { get; private set; }
        public bool CanExtract => HasAllPhysicalKeys && TerminalConfirmed;

        public bool CollectPhysicalKey(KhufuKeyId key)
        {
            return physicalKeys.Add(key);
        }

        public bool HasPhysicalKey(KhufuKeyId key)
        {
            return physicalKeys.Contains(key);
        }

        public bool ConfirmAtMissionTerminal()
        {
            TerminalConfirmed = HasAllPhysicalKeys;
            return TerminalConfirmed;
        }

        public string BuildTerminalReadout()
        {
            if (HasAllPhysicalKeys)
            {
                return TerminalConfirmed
                    ? "Mission terminal confirmed Sun, Crown, and Earth. Valley Gate authorized"
                    : "Sun, Crown, and Earth detected. Confirm at mission terminal";
            }

            return "Mission terminal missing " + string.Join(", ", MissingKeys().Select(key => key.ToString()));
        }

        public IReadOnlyList<KhufuKeyId> MissingKeys()
        {
            return RequiredKeys.Where(key => !physicalKeys.Contains(key)).ToArray();
        }

        public void Reset()
        {
            physicalKeys.Clear();
            TerminalConfirmed = false;
        }

        public static bool TryParseKeyName(string objectName, out KhufuKeyId key)
        {
            foreach (var candidate in RequiredKeys)
            {
                if (objectName.EndsWith("_" + candidate, StringComparison.OrdinalIgnoreCase))
                {
                    key = candidate;
                    return true;
                }
            }

            key = default;
            return false;
        }
    }
}

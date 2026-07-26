using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuV12SegmentTag : MonoBehaviour
    {
        [SerializeField] private string truthClass = string.Empty;
        [SerializeField] private bool factualShape;
        [SerializeField] private bool gameplayScale;
        [SerializeField] private string[] segmentIds = Array.Empty<string>();

        public string TruthClass => truthClass;
        public bool FactualShape => factualShape;
        public bool GameplayScale => gameplayScale;
        public IReadOnlyList<string> SegmentIds => segmentIds;

        public void Configure(IEnumerable<string> ids, string evidenceClass, bool hasFactualShape,
            bool usesGameplayScale)
        {
            segmentIds = ids.Where(item => !string.IsNullOrWhiteSpace(item))
                .Distinct(StringComparer.Ordinal)
                .OrderBy(item => item, StringComparer.Ordinal)
                .ToArray();
            truthClass = evidenceClass;
            factualShape = hasFactualShape;
            gameplayScale = usesGameplayScale;
        }
    }
}

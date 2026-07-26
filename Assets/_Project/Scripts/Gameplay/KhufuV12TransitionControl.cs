using UnityEngine;

namespace ChannelPlay.Gameplay
{
    public sealed class KhufuV12TransitionControl : MonoBehaviour
    {
        [SerializeField] private Mesh predecessorGranite;
        [SerializeField] private Mesh successorGranite;
        [SerializeField] private MeshFilter graniteFilter;
        [SerializeField] private BoxCollider queenGate;

        public Mesh PredecessorGranite => predecessorGranite;
        public Mesh SuccessorGranite => successorGranite;
        public MeshFilter GraniteFilter => graniteFilter;
        public BoxCollider QueenGate => queenGate;

        public void Configure(Mesh predecessor, Mesh successor, MeshFilter filter, BoxCollider gate)
        {
            predecessorGranite = predecessor;
            successorGranite = successor;
            graniteFilter = filter;
            queenGate = gate;
        }
    }
}

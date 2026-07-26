using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using ChannelPlay.Gameplay;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV13SubterraneanThresholdMeshPipeline
{
    public const string GeneratedRoot =
        "Assets/_Project/Art/Generated/KhufuV13SubterraneanThreshold";
    public const string StructureBucket = "Bedrock_Structure";
    public const string DetailBucket = "Passage_Detail";
    public const string ShadowBucket = "Subterranean_Shadow";
    public const string AccentBucket = "Evidence_Limit_Accent";
    public const string InlayBucket = "Subterranean_Route_Inlay";
    public const int ExpectedRendererCount = 5;
    public const int ExpectedColliderCount = 20;
    public const int ExpectedPassageShellCount = 3;

    public const string TransitionSegment = "V10_Branch_Transition";
    public const string DescendingSegment = "Descending_Bedrock_Passage";
    public const string ApproachSegment = "Subterranean_Level_Approach";
    public const string ChamberSegment = "Subterranean_Chamber";
    public const string PitSegment = "Unfinished_Pit_Boundary";
    public const string InlaySegment = "HYBRID_Subterranean_Route_Inlay";

    public const string TransitionShell = "Junction_Transition_Shell";
    public const string DescendingShell = "Descending_Bedrock_Shell";
    public const string ApproachShell = "Subterranean_Level_Approach_Shell";
    public const string ChamberShell = "Subterranean_Chamber_Shell";
    public const string SolidPitBackingName = "Chamber_Floor_Solid_Pit_Backing";

    private const float WallThickness = 0.25f;
    private const float ChamberWidth = 5.0f;
    private const float ChamberLength = 6.2f;
    private const float ChamberHeight = 3.4f;
    private const float DoorWidth = 2.5f;
    private const float DoorHeight = 2.4f;

    public static readonly string[] Buckets =
    {
        StructureBucket, DetailBucket, ShadowBucket, AccentBucket, InlayBucket
    };

    public static readonly string[] Segments =
    {
        TransitionSegment, DescendingSegment, ApproachSegment,
        ChamberSegment, PitSegment, InlaySegment
    };

    public static readonly string[] PassageShells =
    {
        TransitionShell, DescendingShell, ApproachShell
    };

    public static List<BoxSpec> BuildSpecs()
    {
        var specs = new List<BoxSpec>();
        AddPassageShell(specs, TransitionSegment, TransitionShell,
            KhufuV13SubterraneanRouteContract.V10BranchAnchor,
            KhufuV13SubterraneanRouteContract.JunctionEnd, 0f,
            KhufuV13SubterraneanRouteContract.JunctionTransitionEndRelease,
            KhufuV13SubterraneanRouteContract.JunctionTransitionEndRelease);
        AddPassageShell(specs, DescendingSegment, DescendingShell,
            KhufuV13SubterraneanRouteContract.JunctionEnd,
            KhufuV13SubterraneanRouteContract.SubterraneanLanding,
            KhufuV13SubterraneanRouteContract.JunctionInnerWallRelease,
            0f, 0f,
            KhufuV13SubterraneanRouteContract.LandingRoofEndRelease);
        AddPassageShell(specs, ApproachSegment, ApproachShell,
            KhufuV13SubterraneanRouteContract.SubterraneanLanding,
            KhufuV13SubterraneanRouteContract.ChamberDoor);
        AddChamberShell(specs);
        AddPassageDetails(specs);
        AddPitPresentation(specs);
        AddRouteInlay(specs);
        ValidateSpecs(specs);
        return specs;
    }

    public static Mesh BuildTransientMesh(IReadOnlyList<BoxSpec> specs, string bucket, string name)
    {
        if (!Buckets.Contains(bucket, StringComparer.Ordinal))
            throw new InvalidOperationException("Unknown V13 renderer bucket: " + bucket);
        var selected = specs.Where(item => item.Bucket == bucket).ToArray();
        if (selected.Length == 0)
            throw new InvalidOperationException("V13 renderer bucket is empty: " + bucket);
        var builder = new BoxMeshBuilder(name);
        foreach (var spec in selected) builder.Add(spec);
        return builder.Build();
    }

    public static string GeometrySignature(Mesh mesh)
    {
        if (mesh == null) return string.Empty;
        using (var stream = new MemoryStream())
        using (var writer = new BinaryWriter(stream))
        {
            writer.Write(mesh.vertexCount);
            writer.Write(mesh.subMeshCount);
            foreach (var vertex in mesh.vertices) Write(writer, vertex);
            foreach (var normal in mesh.normals) Write(writer, normal);
            foreach (var uv in mesh.uv)
            {
                writer.Write(uv.x);
                writer.Write(uv.y);
            }
            for (var subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
            foreach (var index in mesh.GetIndices(subMesh)) writer.Write(index);
            writer.Flush();
            stream.Position = 0;
            using (var sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty)
                    .ToLowerInvariant();
        }
    }

    public static int TriangleCount(Mesh mesh)
    {
        if (mesh == null) return 0;
        var triangles = 0;
        for (var index = 0; index < mesh.subMeshCount; index++)
            triangles += (int)mesh.GetIndexCount(index) / 3;
        return triangles;
    }

    private static void AddPassageShell(List<BoxSpec> specs, string segment, string shell,
        Vector3 start, Vector3 end, float innerWallStartRelease = 0f,
        float floorEndRelease = 0f, float innerWallEndRelease = 0f,
        float roofEndRelease = 0f)
    {
        var routeDelta = end - start;
        var routeLength = routeDelta.magnitude;
        if (innerWallStartRelease < 0f || floorEndRelease < 0f ||
            innerWallEndRelease < 0f || roofEndRelease < 0f ||
            innerWallStartRelease + innerWallEndRelease >=
            routeLength - WallThickness ||
            floorEndRelease >= routeLength - WallThickness ||
            roofEndRelease >=
            routeLength - WallThickness)
            throw new InvalidOperationException(
                "V13 shell release is outside the passage span: " + shell);
        var frame = Frame(start, end);
        var width = KhufuV13SubterraneanRouteContract.PassageClearWidth;
        var height = KhufuV13SubterraneanRouteContract.PassageShellHeight;
        var fullLength = frame.Length + WallThickness;
        var floorEnd =
            end - routeDelta.normalized * floorEndRelease;
        var floorFrame = Frame(start, floorEnd);
        var floorFullLength = floorFrame.Length + WallThickness;
        var innerStart =
            start + routeDelta.normalized * innerWallStartRelease;
        var innerEnd =
            end - routeDelta.normalized * innerWallEndRelease;
        var innerFrame = Frame(innerStart, innerEnd);
        var innerFullLength = innerFrame.Length + WallThickness;
        var roofEnd =
            end - routeDelta.normalized * roofEndRelease;
        var roofFrame = Frame(start, roofEnd);
        var roofFullLength = roofFrame.Length + WallThickness;
        AddStructural(specs, segment, shell, shell + "_Floor",
            floorFrame.Center -
            floorFrame.Up * (WallThickness * 0.5f), floorFrame.Rotation,
            new Vector3(width + WallThickness * 2f, WallThickness,
                floorFullLength));
        AddStructural(specs, segment, shell, shell + "_West_Wall",
            innerFrame.Center -
            innerFrame.Right * (width * 0.5f + WallThickness * 0.5f) +
            innerFrame.Up * (height * 0.5f), innerFrame.Rotation,
            new Vector3(WallThickness, height, innerFullLength));
        AddStructural(specs, segment, shell, shell + "_East_Wall",
            frame.Center + frame.Right * (width * 0.5f + WallThickness * 0.5f) +
            frame.Up * (height * 0.5f), frame.Rotation,
            new Vector3(WallThickness, height, fullLength));
        AddStructural(specs, segment, shell, shell + "_Roof",
            roofFrame.Center +
            roofFrame.Up * (height + WallThickness * 0.5f),
            roofFrame.Rotation,
            new Vector3(width + WallThickness * 2f, WallThickness,
                roofFullLength));
    }

    private static void AddChamberShell(List<BoxSpec> specs)
    {
        var floorY = KhufuV13SubterraneanRouteContract.ChamberCenter.y;
        var center = KhufuV13SubterraneanRouteContract.ChamberCenter;
        var wallY = floorY + ChamberHeight * 0.5f;
        var halfWidth = ChamberWidth * 0.5f;
        var halfLength = ChamberLength * 0.5f;
        var outerWidth = ChamberWidth + WallThickness * 2f;
        var outerLength = ChamberLength + WallThickness * 2f;
        var southZ = center.z - halfLength - WallThickness * 0.5f;
        var northZ = center.z + halfLength + WallThickness * 0.5f;
        var jambWidth = (ChamberWidth - DoorWidth) * 0.5f;
        var jambOffset = DoorWidth * 0.5f + jambWidth * 0.5f;

        AddStructural(specs, ChamberSegment, ChamberShell, SolidPitBackingName,
            new Vector3(center.x, floorY - WallThickness * 0.5f, center.z),
            Quaternion.identity, new Vector3(outerWidth, WallThickness, outerLength));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_Ceiling",
            new Vector3(center.x, floorY + ChamberHeight + WallThickness * 0.5f, center.z),
            Quaternion.identity, new Vector3(outerWidth, WallThickness, outerLength));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_North_Wall",
            new Vector3(center.x, wallY, northZ), Quaternion.identity,
            new Vector3(outerWidth, ChamberHeight, WallThickness));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_West_Wall",
            new Vector3(center.x - halfWidth - WallThickness * 0.5f, wallY, center.z),
            Quaternion.identity, new Vector3(WallThickness, ChamberHeight, outerLength));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_East_Wall",
            new Vector3(center.x + halfWidth + WallThickness * 0.5f, wallY, center.z),
            Quaternion.identity, new Vector3(WallThickness, ChamberHeight, outerLength));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_South_West_Jamb",
            new Vector3(center.x - jambOffset, wallY, southZ), Quaternion.identity,
            new Vector3(jambWidth, ChamberHeight, WallThickness));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_South_East_Jamb",
            new Vector3(center.x + jambOffset, wallY, southZ), Quaternion.identity,
            new Vector3(jambWidth, ChamberHeight, WallThickness));
        AddStructural(specs, ChamberSegment, ChamberShell, "Chamber_South_Lintel",
            new Vector3(center.x, floorY + DoorHeight + (ChamberHeight - DoorHeight) * 0.5f,
                southZ),
            Quaternion.identity,
            new Vector3(DoorWidth, ChamberHeight - DoorHeight, WallThickness));
    }

    private static void AddPassageDetails(List<BoxSpec> specs)
    {
        AddDetailRib(specs, TransitionSegment, "Junction_Threshold_Rib",
            KhufuV13SubterraneanRouteContract.V10BranchAnchor,
            KhufuV13SubterraneanRouteContract.JunctionEnd);
        AddDetailRib(specs, DescendingSegment, "Bedrock_Landing_Rib",
            KhufuV13SubterraneanRouteContract.JunctionEnd,
            KhufuV13SubterraneanRouteContract.SubterraneanLanding);
        AddDetailRib(specs, ApproachSegment, "Chamber_Doorway_Rib",
            KhufuV13SubterraneanRouteContract.SubterraneanLanding,
            KhufuV13SubterraneanRouteContract.ChamberDoor);
    }

    private static void AddDetailRib(List<BoxSpec> specs, string segment, string name,
        Vector3 start, Vector3 end)
    {
        var frame = Frame(start, end);
        Add(specs, segment, name, DetailBucket,
            end + frame.Up *
            (KhufuV13SubterraneanRouteContract.PassageShellHeight - 0.08f),
            frame.Rotation,
            new Vector3(KhufuV13SubterraneanRouteContract.PassageClearWidth, 0.10f, 0.10f),
            string.Empty, false);
    }

    private static void AddPitPresentation(List<BoxSpec> specs)
    {
        var center = KhufuV13SubterraneanRouteContract.PitInspection;
        Add(specs, PitSegment, "Unfinished_Pit_Shadow", ShadowBucket,
            center + Vector3.up * 0.012f, Quaternion.identity,
            new Vector3(1.35f, 0.024f, 1.05f), string.Empty, false);
        Add(specs, PitSegment, "Unfinished_Pit_North_Evidence_Limit", AccentBucket,
            center + new Vector3(0f, 0.035f, 0.58f), Quaternion.identity,
            new Vector3(1.55f, 0.07f, 0.10f), string.Empty, false);
        Add(specs, PitSegment, "Unfinished_Pit_South_Evidence_Limit", AccentBucket,
            center + new Vector3(0f, 0.035f, -0.58f), Quaternion.identity,
            new Vector3(1.55f, 0.07f, 0.10f), string.Empty, false);
        Add(specs, PitSegment, "Unfinished_Pit_West_Evidence_Limit", AccentBucket,
            center + new Vector3(-0.73f, 0.035f, 0f), Quaternion.identity,
            new Vector3(0.10f, 0.07f, 1.05f), string.Empty, false);
        Add(specs, PitSegment, "Unfinished_Pit_East_Evidence_Limit", AccentBucket,
            center + new Vector3(0.73f, 0.035f, 0f), Quaternion.identity,
            new Vector3(0.10f, 0.07f, 1.05f), string.Empty, false);
    }

    private static void AddRouteInlay(List<BoxSpec> specs)
    {
        var route = KhufuV13SubterraneanRouteContract.ForwardRoute();
        for (var index = 1; index < route.Count; index++)
        {
            var frame = Frame(route[index - 1], route[index]);
            Add(specs, InlaySegment, "Subterranean_Route_" + (index - 1).ToString("D2"),
                InlayBucket, frame.Center + frame.Up * 0.025f, frame.Rotation,
                new Vector3(0.08f, 0.035f, Mathf.Max(0.18f, frame.Length - 0.12f)),
                string.Empty, false);
        }
    }

    private static void AddStructural(List<BoxSpec> specs, string segment, string shell,
        string name, Vector3 position, Quaternion rotation, Vector3 scale)
    {
        Add(specs, segment, name, StructureBucket, position, rotation, scale, shell, true);
    }

    private static void Add(List<BoxSpec> specs, string segment, string name, string bucket,
        Vector3 position, Quaternion rotation, Vector3 scale, string shell, bool collider)
    {
        specs.Add(new BoxSpec(segment, name, bucket, position, rotation, scale, shell, collider));
    }

    private static RouteFrame Frame(Vector3 start, Vector3 end)
    {
        var delta = end - start;
        if (delta.sqrMagnitude < 0.0001f)
            throw new InvalidOperationException("Zero-length V13 route frame.");
        var rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
        return new RouteFrame
        {
            Center = (start + end) * 0.5f,
            Length = delta.magnitude,
            Rotation = rotation,
            Right = rotation * Vector3.right,
            Up = rotation * Vector3.up
        };
    }

    private static void ValidateSpecs(IReadOnlyList<BoxSpec> specs)
    {
        if (Mathf.Abs(KhufuV13SubterraneanRouteContract.DescentAngleDegrees - 29f) > 0.5f)
            throw new InvalidOperationException("V13 descent angle must remain approximately 29 degrees.");
        if (specs.Count(item => item.Collider) != ExpectedColliderCount)
            throw new InvalidOperationException("V13 must own exactly 20 collider proxies.");
        if (specs.Where(item => item.Collider).Any(item => item.ColliderIsTrigger))
            throw new InvalidOperationException("V13 collider proxies must remain non-trigger.");
        if (specs.Select(item => item.Name).Distinct(StringComparer.Ordinal).Count() != specs.Count)
            throw new InvalidOperationException("V13 geometry names must remain unique.");
        var colliderNames = specs.Where(item => item.Collider).Select(item => item.ColliderName).ToArray();
        if (colliderNames.Any(string.IsNullOrEmpty) ||
            colliderNames.Distinct(StringComparer.Ordinal).Count() != ExpectedColliderCount)
            throw new InvalidOperationException("V13 collider proxy names must remain unique and non-empty.");
        if (Buckets.Any(bucket => specs.All(item => item.Bucket != bucket)))
            throw new InvalidOperationException("Every V13 renderer bucket must contain geometry.");
        foreach (var shell in PassageShells)
        {
            if (specs.Count(item => item.Shell == shell && item.Collider) != 4)
                throw new InvalidOperationException("V13 passage shell is not enclosed: " + shell);
        }
        if (specs.Count(item => item.Shell == ChamberShell && item.Collider) != 8)
            throw new InvalidOperationException("V13 chamber shell must own exactly eight colliders.");
        var backing = specs.SingleOrDefault(item => item.Name == SolidPitBackingName);
        if (backing == null || !backing.Collider || backing.ColliderIsTrigger)
            throw new InvalidOperationException("V13 unfinished pit requires a solid collider backing.");
    }

    private static void Write(BinaryWriter writer, Vector3 value)
    {
        writer.Write(value.x);
        writer.Write(value.y);
        writer.Write(value.z);
    }

    public sealed class BoxSpec
    {
        public readonly string SegmentId;
        public readonly string Name;
        public readonly string Bucket;
        public readonly Vector3 Position;
        public readonly Quaternion Rotation;
        public readonly Vector3 Scale;
        public readonly string Shell;
        public readonly bool Collider;
        public readonly string ColliderName;
        public readonly bool ColliderIsTrigger;

        public BoxSpec(string segmentId, string name, string bucket, Vector3 position,
            Quaternion rotation, Vector3 scale, string shell, bool collider)
        {
            SegmentId = segmentId;
            Name = name;
            Bucket = bucket;
            Position = position;
            Rotation = rotation;
            Scale = scale;
            Shell = shell;
            Collider = collider;
            ColliderName = collider ? "V13_Proxy_" + name : string.Empty;
            ColliderIsTrigger = false;
        }
    }

    private sealed class RouteFrame
    {
        public Vector3 Center;
        public float Length;
        public Quaternion Rotation;
        public Vector3 Right;
        public Vector3 Up;
    }

    private sealed class BoxMeshBuilder
    {
        private static readonly Vector3[] FaceNormals =
        {
            Vector3.forward, Vector3.back, Vector3.right,
            Vector3.left, Vector3.up, Vector3.down
        };

        private static readonly int[,] FaceCorners =
        {
            { 4, 5, 6, 7 }, { 1, 0, 3, 2 }, { 5, 1, 2, 6 },
            { 0, 4, 7, 3 }, { 7, 6, 2, 3 }, { 0, 1, 5, 4 }
        };

        private readonly string meshName;
        private readonly List<Vector3> vertices = new List<Vector3>();
        private readonly List<Vector3> normals = new List<Vector3>();
        private readonly List<Vector2> uvs = new List<Vector2>();
        private readonly List<int> triangles = new List<int>();

        public BoxMeshBuilder(string name)
        {
            meshName = name;
        }

        public void Add(BoxSpec spec)
        {
            var half = spec.Scale * 0.5f;
            var corners = new[]
            {
                new Vector3(-half.x, -half.y, -half.z),
                new Vector3(half.x, -half.y, -half.z),
                new Vector3(half.x, half.y, -half.z),
                new Vector3(-half.x, half.y, -half.z),
                new Vector3(-half.x, -half.y, half.z),
                new Vector3(half.x, -half.y, half.z),
                new Vector3(half.x, half.y, half.z),
                new Vector3(-half.x, half.y, half.z)
            };
            var matrix = Matrix4x4.TRS(spec.Position, spec.Rotation, Vector3.one);
            for (var face = 0; face < 6; face++)
            {
                var start = vertices.Count;
                for (var corner = 0; corner < 4; corner++)
                {
                    vertices.Add(matrix.MultiplyPoint3x4(corners[FaceCorners[face, corner]]));
                    normals.Add(spec.Rotation * FaceNormals[face]);
                }
                var tile = FaceTile(spec.Scale, face);
                uvs.Add(Vector2.zero);
                uvs.Add(new Vector2(tile.x, 0f));
                uvs.Add(tile);
                uvs.Add(new Vector2(0f, tile.y));
                triangles.Add(start);
                triangles.Add(start + 1);
                triangles.Add(start + 2);
                triangles.Add(start);
                triangles.Add(start + 2);
                triangles.Add(start + 3);
            }
        }

        public Mesh Build()
        {
            var mesh = new Mesh { name = meshName, indexFormat = IndexFormat.UInt32 };
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(triangles, 0, true);
            mesh.RecalculateBounds();
            return mesh;
        }

        private static Vector2 FaceTile(Vector3 scale, int face)
        {
            Vector2 dimensions;
            if (face <= 1) dimensions = new Vector2(scale.x, scale.y);
            else if (face <= 3) dimensions = new Vector2(scale.z, scale.y);
            else dimensions = new Vector2(scale.x, scale.z);
            return new Vector2(Mathf.Max(1f, dimensions.x / 2.2f),
                Mathf.Max(1f, dimensions.y / 2.2f));
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV9CausewayMeshPipeline
{
    public const string GeneratedRoot = "Assets/_Project/Art/Generated/KhufuV9CausewayFidelity";
    public const string BasaltBucket = "Basalt_Floor";
    public const string LimestoneBucket = "Limestone_Structure";
    public const string RedGraniteBucket = "Red_Granite_Rhythm";
    public const string TuraBucket = "Tura_Trim";
    public const string InlayBucket = "Route_Inlay";
    public const int ExpectedRendererCount = 5;
    public const int ExpectedStructuralPairs = 23;

    public static readonly Vector3 ValleyPoint = new Vector3(150f, 0.15f, 0f);
    public static readonly Vector3 CausewayPoint = new Vector3(105f, 3.15f, 0f);
    public static readonly Vector3 HubPoint = new Vector3(62f, 1.15f, 0f);

    private static readonly string[] BucketOrder =
    {
        BasaltBucket,
        LimestoneBucket,
        RedGraniteBucket,
        TuraBucket,
        InlayBucket
    };

    public static IReadOnlyList<string> Buckets => BucketOrder;

    public static List<BoxSpec> BuildSpecs()
    {
        var specs = new List<BoxSpec>();
        AddRouteSegment(specs, "Valley_To_Causeway", ValleyPoint, CausewayPoint, 0f);
        AddRouteSegment(specs, "Causeway_To_Hub", CausewayPoint, HubPoint, 12f);
        AddPortal(specs, "Valley_Gate", ValleyPoint, ValleyPoint - CausewayPoint);
        AddPortal(specs, "Covered_Causeway", CausewayPoint, CausewayPoint - HubPoint);
        AddStation(specs, "Valley_Station_A", ValleyPoint, CausewayPoint, 0.32f);
        AddStation(specs, "Valley_Station_B", ValleyPoint, CausewayPoint, 0.68f);
        AddStation(specs, "Causeway_Station_A", CausewayPoint, HubPoint, 0.32f);
        AddStation(specs, "Causeway_Station_B", CausewayPoint, HubPoint, 0.68f);
        return specs;
    }

    public static Dictionary<string, Mesh> BuildAndSaveMeshes(IReadOnlyList<BoxSpec> specs)
    {
        EnsureFolder();
        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal);
        foreach (var bucket in BucketOrder)
        {
            var builder = new BoxMeshBuilder("KhufuV9_" + bucket);
            foreach (var spec in specs.Where(item => item.Bucket == bucket)) builder.Add(spec);
            var mesh = builder.Build();
            var path = GeneratedRoot + "/KhufuV9_" + bucket + ".asset";
            result.Add(bucket, SaveMesh(mesh, path));
        }
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        return result;
    }

    public static int TriangleCount(Mesh mesh)
    {
        var triangles = 0;
        if (mesh == null) return triangles;
        for (var index = 0; index < mesh.subMeshCount; index++) triangles += (int)mesh.GetIndexCount(index) / 3;
        return triangles;
    }

    private static void AddRouteSegment(List<BoxSpec> specs, string name, Vector3 a, Vector3 b, float hubOpeningLength)
    {
        var frame = CreateRouteFrame(a, b);
        specs.Add(new BoxSpec(name + "_Floor", BasaltBucket,
            frame.Center + frame.Up * 0.02f, frame.Rotation, new Vector3(6f, 0.18f, frame.Length), false, false));

        var parapetEnd = Vector3.MoveTowards(b, a, hubOpeningLength);
        var parapetFrame = CreateRouteFrame(a, parapetEnd);
        for (var side = -1; side <= 1; side += 2)
        {
            specs.Add(new BoxSpec(name + (side < 0 ? "_West_Parapet" : "_East_Parapet"), LimestoneBucket,
                parapetFrame.Center + parapetFrame.Right * (3.25f * side) + parapetFrame.Up * 0.62f,
                parapetFrame.Rotation, new Vector3(0.36f, 1.24f, parapetFrame.Length), true, true));
        }
        if (hubOpeningLength > 0f)
        {
            specs.Add(new BoxSpec(name + "_Roof", TuraBucket,
                parapetFrame.Center + parapetFrame.Up * 5.85f, parapetFrame.Rotation,
                new Vector3(7.25f, 0.38f, parapetFrame.Length), true, true));
        }

        for (var index = 1; index <= 9; index++)
        {
            var t = index / 10f;
            var point = Vector3.Lerp(a, b, t) + frame.Up * 0.125f;
            specs.Add(new BoxSpec(name + "_Paver_" + index.ToString("D2"), InlayBucket,
                point, frame.Rotation, new Vector3(5.55f, 0.025f, 0.08f), false, false));
        }
        specs.Add(new BoxSpec(name + "_Center_Inlay", InlayBucket,
            frame.Center + frame.Up * 0.13f, frame.Rotation, new Vector3(0.08f, 0.025f, frame.Length - 1f), false, false));
    }

    private static void AddPortal(List<BoxSpec> specs, string name, Vector3 point, Vector3 routeDirection)
    {
        var rotation = Quaternion.LookRotation(routeDirection.normalized, Vector3.up);
        var right = rotation * Vector3.right;
        var up = rotation * Vector3.up;
        for (var side = -1; side <= 1; side += 2)
        {
            var suffix = side < 0 ? "_West_Post" : "_East_Post";
            var position = point + right * (3.6f * side) + up * 2.8f;
            specs.Add(new BoxSpec(name + suffix, RedGraniteBucket, position, rotation,
                new Vector3(0.9f, 5.6f, 1.2f), true, true));
            specs.Add(new BoxSpec(name + suffix + "_Cap", TuraBucket, position + up * 3.02f, rotation,
                new Vector3(1.25f, 0.42f, 1.55f), false, false));
        }
        specs.Add(new BoxSpec(name + "_Lintel", LimestoneBucket, point + up * 5.75f, rotation,
            new Vector3(8f, 0.62f, 1.25f), true, true));
        specs.Add(new BoxSpec(name + "_Lintel_Inlay", InlayBucket, point + up * 5.76f - rotation * Vector3.forward * 0.64f,
            rotation, new Vector3(5.4f, 0.18f, 0.035f), false, false));
    }

    private static void AddStation(List<BoxSpec> specs, string name, Vector3 a, Vector3 b, float t)
    {
        var frame = CreateRouteFrame(a, b);
        var point = Vector3.Lerp(a, b, t);
        for (var side = -1; side <= 1; side += 2)
        {
            var suffix = side < 0 ? "_West_Post" : "_East_Post";
            var position = point + frame.Right * (3.25f * side) + frame.Up * 2.4f;
            specs.Add(new BoxSpec(name + suffix, RedGraniteBucket, position, frame.Rotation,
                new Vector3(0.62f, 4.8f, 0.62f), true, true));
            specs.Add(new BoxSpec(name + suffix + "_Cap", TuraBucket, position + frame.Up * 2.62f, frame.Rotation,
                new Vector3(0.92f, 0.4f, 0.92f), false, false));
        }
        specs.Add(new BoxSpec(name + "_Beam", LimestoneBucket, point + frame.Up * 4.95f, frame.Rotation,
            new Vector3(7.1f, 0.45f, 0.72f), true, true));
        specs.Add(new BoxSpec(name + "_Beam_Inlay", InlayBucket,
            point + frame.Up * 4.96f - frame.Rotation * Vector3.forward * 0.37f,
            frame.Rotation, new Vector3(4.8f, 0.14f, 0.03f), false, false));
    }

    private static RouteFrame CreateRouteFrame(Vector3 a, Vector3 b)
    {
        var delta = b - a;
        var rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
        return new RouteFrame
        {
            Center = (a + b) * 0.5f,
            Length = delta.magnitude,
            Rotation = rotation,
            Right = rotation * Vector3.right,
            Up = rotation * Vector3.up
        };
    }

    private static Mesh SaveMesh(Mesh generated, string path)
    {
        var existing = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (existing == null)
        {
            AssetDatabase.CreateAsset(generated, path);
            return generated;
        }
        EditorUtility.CopySerialized(generated, existing);
        existing.name = generated.name;
        EditorUtility.SetDirty(existing);
        UnityEngine.Object.DestroyImmediate(generated);
        return existing;
    }

    private static void EnsureFolder()
    {
        var projectRoot = Directory.GetParent(Application.dataPath).FullName;
        Directory.CreateDirectory(Path.Combine(projectRoot, GeneratedRoot));
        AssetDatabase.Refresh();
    }

    public sealed class BoxSpec
    {
        public readonly string Name;
        public readonly string Bucket;
        public readonly Vector3 Position;
        public readonly Quaternion Rotation;
        public readonly Vector3 Scale;
        public readonly bool Structural;
        public readonly bool Collider;

        public BoxSpec(string name, string bucket, Vector3 position, Quaternion rotation, Vector3 scale,
            bool structural, bool collider)
        {
            Name = name;
            Bucket = bucket;
            Position = position;
            Rotation = rotation;
            Scale = scale;
            Structural = structural;
            Collider = collider;
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
            Vector3.forward, Vector3.back, Vector3.right, Vector3.left, Vector3.up, Vector3.down
        };

        private static readonly int[,] FaceCorners =
        {
            { 4, 5, 6, 7 }, { 1, 0, 3, 2 }, { 5, 1, 2, 6 },
            { 0, 4, 7, 3 }, { 7, 6, 2, 3 }, { 0, 1, 5, 4 }
        };

        private readonly string name;
        private readonly List<Vector3> vertices = new List<Vector3>();
        private readonly List<Vector3> normals = new List<Vector3>();
        private readonly List<Vector2> uvs = new List<Vector2>();
        private readonly List<int> triangles = new List<int>();

        public BoxMeshBuilder(string nameValue)
        {
            name = nameValue;
        }

        public void Add(BoxSpec spec)
        {
            var half = spec.Scale * 0.5f;
            var corners = new[]
            {
                new Vector3(-half.x, -half.y, -half.z), new Vector3(half.x, -half.y, -half.z),
                new Vector3(half.x, half.y, -half.z), new Vector3(-half.x, half.y, -half.z),
                new Vector3(-half.x, -half.y, half.z), new Vector3(half.x, -half.y, half.z),
                new Vector3(half.x, half.y, half.z), new Vector3(-half.x, half.y, half.z)
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
                triangles.Add(start); triangles.Add(start + 1); triangles.Add(start + 2);
                triangles.Add(start); triangles.Add(start + 2); triangles.Add(start + 3);
            }
        }

        public Mesh Build()
        {
            var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 };
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
            return new Vector2(Mathf.Max(1f, dimensions.x / 4f), Mathf.Max(1f, dimensions.y / 4f));
        }
    }
}

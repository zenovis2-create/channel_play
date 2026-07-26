using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV12QueenCircuitMeshPipeline
{
    public const string GeneratedRoot = "Assets/_Project/Art/Generated/KhufuV12QueenCircuit";
    public const string LimestoneBucket = "Limestone_Structure";
    public const string DetailBucket = "Limestone_Detail";
    public const string ShadowBucket = "Shadow_Recess";
    public const string AccentBucket = "Queen_Inspection_Accent";
    public const string InlayBucket = "Queen_Route_Inlay";
    public const int ExpectedRendererCount = 5;
    public const int ExpectedColliderCount = 22;

    public const string ThresholdSegment = "Queen_Threshold_Transition";
    public const string PassageSegment = "Horizontal_Passage";
    public const string ChamberSegment = "Queens_Chamber";
    public const string NicheSegment = "East_Wall_Niche";
    public const string MouthSegment = "Narrow_Mouth_Boundaries";
    public const string InlaySegment = "HYBRID_Queen_Route_Inlay";

    public const string V12OpenLimestonePath = GeneratedRoot + "/KhufuV12_V10_Limestone_Open.asset";
    public const string V12OpenGranitePath = GeneratedRoot + "/KhufuV12_V10_Red_Granite_Open.asset";
    public const string V11LimestoneSha256 =
        "1ae211817170a9ae846853b6313c4bdb1277553b7bcd6bc7f30760762a980e67";
    public const string V11LimestoneMetaSha256 =
        "2a579b2efd062b16370fe7e5a6f1aedc233fbd057b67de7c9a9fb8d3c8d2dd6c";
    public const string V11GraniteSha256 =
        "1c2cca3af61aaf68e003f813274fd5890d9a88078147e2cd8abb5012481f7d02";
    public const string V11GraniteMetaSha256 =
        "4aa71b58e1cdccdc27409da5149aa936095be87c247fb9c5163205cafe652bda";

    public static readonly string[] Buckets =
    {
        LimestoneBucket, DetailBucket, ShadowBucket, AccentBucket, InlayBucket
    };

    public static readonly string[] Segments =
    {
        ThresholdSegment, PassageSegment, ChamberSegment, NicheSegment, MouthSegment, InlaySegment
    };

    public static List<BoxSpec> BuildSpecs()
    {
        var specs = new List<BoxSpec>();
        AddHorizontalPassage(specs);
        AddQueensChamber(specs);
        AddEastWallNiche(specs);
        AddNarrowMouths(specs);
        AddRouteInlay(specs);
        return specs;
    }

    public static Dictionary<string, Mesh> BuildAndSaveMeshes(IReadOnlyList<BoxSpec> specs)
    {
        EnsureFolder();
        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal);
        foreach (var bucket in Buckets)
        {
            var generated = BuildTransientMesh(specs, bucket, "KhufuV12_" + bucket);
            result.Add(bucket, SaveMesh(generated, GeneratedRoot + "/KhufuV12_" + bucket + ".asset"));
        }
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        return result;
    }

    public static Dictionary<string, Mesh> BuildAndSaveSuccessorVariants()
    {
        EnsureFolder();
        ValidateFrozenV11Inputs();
        var v11Limestone = AssetDatabase.LoadAssetAtPath<Mesh>(
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath);
        var v11Granite = AssetDatabase.LoadAssetAtPath<Mesh>(
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath);
        if (v11Limestone == null || v11Granite == null)
            throw new InvalidOperationException("Frozen V11 successor inputs are missing.");

        var specs = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs();
        ValidateOmissionInventory(specs);
        var expectedV11Granite = BuildTransientV10Mesh(FilterV10Specs(specs,
            ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket, false), "Expected_V11_Granite");
        try
        {
            if (GeometrySignature(expectedV11Granite) != GeometrySignature(v11Granite))
                throw new InvalidOperationException("Frozen V11 granite geometry drifted.");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(expectedV11Granite);
        }

        var limestoneCopy = UnityEngine.Object.Instantiate(v11Limestone);
        limestoneCopy.name = "KhufuV12_V10_Limestone_Open";
        var granite = BuildTransientV10Mesh(FilterV10Specs(specs,
            ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket, true),
            "KhufuV12_V10_Red_Granite_Open");
        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal)
        {
            { LimestoneBucket, SaveMesh(limestoneCopy, V12OpenLimestonePath) },
            { ShadowBucket, SaveMesh(granite, V12OpenGranitePath) }
        };
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        ValidateSuccessorAssets();
        return result;
    }

    public static void ValidateSuccessorAssets()
    {
        ValidateFrozenV11Inputs();
        var v11Limestone = AssetDatabase.LoadAssetAtPath<Mesh>(
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath);
        var v11Granite = AssetDatabase.LoadAssetAtPath<Mesh>(
            ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath);
        var v12Limestone = AssetDatabase.LoadAssetAtPath<Mesh>(V12OpenLimestonePath);
        var v12Granite = AssetDatabase.LoadAssetAtPath<Mesh>(V12OpenGranitePath);
        if (v11Limestone == null || v11Granite == null || v12Limestone == null || v12Granite == null)
            throw new InvalidOperationException("V11/V12 transition mesh asset is missing.");
        if (GeometrySignature(v11Limestone) != GeometrySignature(v12Limestone))
            throw new InvalidOperationException("V12 limestone is not geometry-identical to V11 limestone.");

        var specs = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs();
        ValidateOmissionInventory(specs);
        var expected = BuildTransientV10Mesh(FilterV10Specs(specs,
            ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket, true), "Expected_V12_Granite");
        try
        {
            if (GeometrySignature(expected) != GeometrySignature(v12Granite))
                throw new InvalidOperationException("V12 granite omission set drifted.");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(expected);
        }
        if (v11Granite.vertexCount - v12Granite.vertexCount != 24 ||
            TriangleCount(v11Granite) - TriangleCount(v12Granite) != 12)
            throw new InvalidOperationException("V12 granite must remove exactly one Queen gate box.");
    }

    public static Mesh BuildTransientMesh(IReadOnlyList<BoxSpec> specs, string bucket, string name)
    {
        var builder = new BoxMeshBuilder(name);
        foreach (var spec in specs.Where(item => item.Bucket == bucket)) builder.Add(spec);
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
                return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
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

    private static void AddHorizontalPassage(List<BoxSpec> specs)
    {
        AddPassage(specs, ThresholdSegment, "Threshold_Approach",
            KhufuV12QueenRouteContract.GalleryFoot + KhufuV12QueenRouteContract.ThresholdDirection * 0.35f,
            KhufuV12QueenRouteContract.ThresholdCenter, 1.72f, 2.75f);
        AddPassage(specs, PassageSegment, "Chamber_Approach",
            KhufuV12QueenRouteContract.ThresholdCenter, KhufuV12QueenRouteContract.ChamberDoor,
            1.72f, 2.75f, 1.35f);
    }

    private static void AddQueensChamber(List<BoxSpec> specs)
    {
        Add(specs, ChamberSegment, "Chamber_Floor", LimestoneBucket,
            new Vector3(-1.8f, 5.20f, -2.8f), Quaternion.identity, new Vector3(5.2f, 0.26f, 4.4f), true, true);
        Add(specs, ChamberSegment, "Chamber_Back_Wall", LimestoneBucket,
            new Vector3(-1.8f, 6.95f, -0.60f), Quaternion.identity, new Vector3(5.2f, 3.5f, 0.34f), true, true);
        Add(specs, ChamberSegment, "Chamber_West_Wall", LimestoneBucket,
            new Vector3(-4.40f, 6.95f, -2.8f), Quaternion.identity, new Vector3(0.34f, 3.5f, 4.4f), true, true);

        Add(specs, ChamberSegment, "Chamber_East_South_Wall", LimestoneBucket,
            new Vector3(0.80f, 6.95f, -4.0f), Quaternion.identity, new Vector3(0.34f, 3.5f, 1.0f), true, true);
        Add(specs, ChamberSegment, "Chamber_East_North_Wall", LimestoneBucket,
            new Vector3(0.80f, 6.95f, -1.35f), Quaternion.identity, new Vector3(0.34f, 3.5f, 1.5f), true, true);
        Add(specs, ChamberSegment, "Chamber_East_Above_Niche", LimestoneBucket,
            new Vector3(0.80f, 8.28f, -2.8f), Quaternion.identity, new Vector3(0.34f, 0.84f, 1.4f), true, true);
        Add(specs, NicheSegment, "Niche_Back_Boundary", LimestoneBucket,
            new Vector3(1.10f, 6.68f, -2.8f), Quaternion.identity, new Vector3(0.24f, 2.36f, 1.4f), true, true);

        Add(specs, ChamberSegment, "Chamber_Roof_East", LimestoneBucket,
            new Vector3(-0.55f, 8.75f, -2.8f), Quaternion.Euler(0f, 0f, -29f),
            new Vector3(2.9f, 0.28f, 4.5f), true, true);
        Add(specs, ChamberSegment, "Chamber_Roof_West", LimestoneBucket,
            new Vector3(-3.05f, 8.75f, -2.8f), Quaternion.Euler(0f, 0f, 29f),
            new Vector3(2.9f, 0.28f, 4.5f), true, true);
        AddGableInfill(specs, "Back_Gable", -0.60f);
        AddGableInfill(specs, "Entry_Gable", -5.0f);

        Add(specs, ChamberSegment, "Entry_Wall_West", LimestoneBucket,
            new Vector3(-3.475f, 6.95f, -5.0f), Quaternion.identity, new Vector3(1.85f, 3.5f, 0.34f), true, true);
        Add(specs, ChamberSegment, "Entry_Wall_East", LimestoneBucket,
            new Vector3(0.675f, 6.95f, -4.75f), Quaternion.identity, new Vector3(0.25f, 3.5f, 0.24f), true, true);
        Add(specs, ChamberSegment, "Entry_Wall_Lintel", LimestoneBucket,
            new Vector3(-1.20f, 8.20f, -5.0f), Quaternion.identity, new Vector3(2.7f, 1.0f, 0.34f), true, true);
    }

    private static void AddGableInfill(List<BoxSpec> specs, string name, float z)
    {
        var courses = new[]
        {
            new Vector3(3.00f, 0.20f, 0.28f),
            new Vector3(2.20f, 0.20f, 0.28f),
            new Vector3(1.40f, 0.20f, 0.28f),
            new Vector3(0.55f, 0.20f, 0.28f)
        };
        for (var index = 0; index < courses.Length; index++)
        {
            Add(specs, ChamberSegment, name + "_Course_" + index.ToString("D2"), LimestoneBucket,
                new Vector3(-1.8f, 8.80f + index * 0.20f, z), Quaternion.identity,
                courses[index], false, false);
        }
    }

    private static void AddEastWallNiche(List<BoxSpec> specs)
    {
        Add(specs, NicheSegment, "Niche_South_Jamb", DetailBucket,
            new Vector3(0.62f, 6.65f, -3.58f), Quaternion.identity, new Vector3(0.28f, 2.55f, 0.18f), false, false);
        Add(specs, NicheSegment, "Niche_North_Jamb", DetailBucket,
            new Vector3(0.62f, 6.65f, -2.02f), Quaternion.identity, new Vector3(0.28f, 2.55f, 0.18f), false, false);
        Add(specs, NicheSegment, "Niche_Lintel", DetailBucket,
            new Vector3(0.62f, 7.96f, -2.8f), Quaternion.identity, new Vector3(0.28f, 0.18f, 1.74f), false, false);
        Add(specs, NicheSegment, "Niche_Crown_South", DetailBucket,
            new Vector3(0.58f, 8.08f, -3.20f), Quaternion.identity, new Vector3(0.32f, 0.16f, 0.74f), false, false);
        Add(specs, NicheSegment, "Niche_Crown_North", DetailBucket,
            new Vector3(0.58f, 8.18f, -2.45f), Quaternion.identity, new Vector3(0.32f, 0.16f, 0.58f), false, false);
        Add(specs, NicheSegment, "Niche_Recess", ShadowBucket,
            new Vector3(0.965f, 6.68f, -2.8f), Quaternion.identity, new Vector3(0.025f, 2.2f, 1.22f), false, false);
        Add(specs, NicheSegment, "Niche_Sill_Accent", AccentBucket,
            new Vector3(0.54f, 5.48f, -2.8f), Quaternion.identity, new Vector3(0.42f, 0.10f, 1.48f), false, false);
    }

    private static void AddNarrowMouths(List<BoxSpec> specs)
    {
        AddMouth(specs, "North_Narrow_Mouth", new Vector3(-3.15f, 6.32f, -0.79f));
        AddMouth(specs, "South_Narrow_Mouth", new Vector3(-0.45f, 6.32f, -0.79f));
    }

    private static void AddMouth(List<BoxSpec> specs, string name, Vector3 center)
    {
        Add(specs, MouthSegment, name + "_West_Jamb", DetailBucket,
            center + Vector3.left * 0.38f, Quaternion.identity, new Vector3(0.16f, 1.2f, 0.20f), false, false);
        Add(specs, MouthSegment, name + "_East_Jamb", DetailBucket,
            center + Vector3.right * 0.38f, Quaternion.identity, new Vector3(0.16f, 1.2f, 0.20f), false, false);
        Add(specs, MouthSegment, name + "_Lintel", DetailBucket,
            center + Vector3.up * 0.58f, Quaternion.identity, new Vector3(0.92f, 0.16f, 0.20f), false, false);
        Add(specs, MouthSegment, name + "_Boundary", ShadowBucket,
            center + Vector3.forward * 0.015f, Quaternion.identity, new Vector3(0.68f, 1.02f, 0.18f), true, true);
    }

    private static void AddRouteInlay(List<BoxSpec> specs)
    {
        var route = KhufuV12QueenRouteContract.ForwardRoute();
        for (var index = 1; index < route.Count; index++)
        {
            AddRouteStrip(specs, "Queen_Route_" + (index - 1).ToString("D2"), route[index - 1], route[index]);
        }
        Add(specs, NicheSegment, "Chamber_Center_Inspection", AccentBucket,
            KhufuV12QueenRouteContract.ChamberCenter + Vector3.up * 0.025f,
            Quaternion.identity, new Vector3(0.72f, 0.035f, 0.72f), false, false);
    }

    private static void AddPassage(List<BoxSpec> specs, string segment, string name,
        Vector3 start, Vector3 end, float width, float height, float eastWallEndTrim = 0f)
    {
        var frame = Frame(start, end);
        var wall = 0.24f;
        var fullLength = frame.Length + 0.18f;
        var eastWallLength = fullLength - eastWallEndTrim;
        if (eastWallLength <= 0.18f)
            throw new InvalidOperationException("V12 passage east-wall trim removes the wall: " + name);
        Add(specs, segment, name + "_Floor", LimestoneBucket,
            frame.Center - frame.Up * 0.11f, frame.Rotation,
            new Vector3(width + wall * 2f, 0.22f, fullLength), true, true);
        Add(specs, segment, name + "_West_Wall", LimestoneBucket,
            frame.Center - frame.Right * (width * 0.5f + wall * 0.5f) + frame.Up * (height * 0.5f),
            frame.Rotation, new Vector3(wall, height, fullLength), true, true);
        Add(specs, segment, name + "_East_Wall", LimestoneBucket,
            frame.Center + frame.Right * (width * 0.5f + wall * 0.5f) +
            frame.Up * (height * 0.5f) - frame.Forward * (eastWallEndTrim * 0.5f),
            frame.Rotation, new Vector3(wall, height, eastWallLength), true, true);
        Add(specs, segment, name + "_Roof", LimestoneBucket,
            frame.Center + frame.Up * height, frame.Rotation,
            new Vector3(width + wall * 2f, 0.22f, fullLength), true, true);
    }

    private static void AddRouteStrip(List<BoxSpec> specs, string name, Vector3 start, Vector3 end)
    {
        var frame = Frame(start, end);
        Add(specs, InlaySegment, name, InlayBucket, frame.Center + Vector3.up * 0.025f,
            frame.Rotation, new Vector3(0.07f, 0.035f, Mathf.Max(0.18f, frame.Length - 0.18f)), false, false);
    }

    private static void Add(List<BoxSpec> specs, string segment, string name, string bucket,
        Vector3 position, Quaternion rotation, Vector3 scale, bool structural, bool collider)
    {
        specs.Add(new BoxSpec(segment, name, bucket, position, rotation, scale, structural, collider));
    }

    private static RouteFrame Frame(Vector3 start, Vector3 end)
    {
        var delta = end - start;
        if (delta.sqrMagnitude < 0.0001f) throw new InvalidOperationException("Zero-length V12 route frame.");
        var rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
        return new RouteFrame
        {
            Center = (start + end) * 0.5f,
            Length = delta.magnitude,
            Rotation = rotation,
            Right = rotation * Vector3.right,
            Up = rotation * Vector3.up,
            Forward = rotation * Vector3.forward
        };
    }

    private static void ValidateOmissionInventory(
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs)
    {
        if (specs.Count(item => item.Name == "Great_Step_Diegetic_Boundary" &&
                                item.Bucket == ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket) != 1)
            throw new InvalidOperationException("V10 Great Step limestone omission contract drifted.");
        var expectedBars = new HashSet<string>(Enumerable.Range(0, 5)
            .Select(item => "Great_Step_Granite_Bar_" + item.ToString("D2")), StringComparer.Ordinal);
        var actualBars = new HashSet<string>(specs.Where(item =>
                item.Name.StartsWith("Great_Step_Granite_Bar_", StringComparison.Ordinal) &&
                item.Bucket == ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket)
            .Select(item => item.Name), StringComparer.Ordinal);
        if (!expectedBars.SetEquals(actualBars))
            throw new InvalidOperationException("V10 Great Step granite omission contract drifted.");
        if (specs.Count(item => item.Name == "Queen_Ownership_Gate" &&
                                item.Bucket == ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket) != 1)
            throw new InvalidOperationException("V10 Queen gate omission contract drifted.");
    }

    private static IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> FilterV10Specs(
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, string bucket, bool omitQueen)
    {
        var bars = new HashSet<string>(Enumerable.Range(0, 5)
            .Select(item => "Great_Step_Granite_Bar_" + item.ToString("D2")), StringComparer.Ordinal);
        return specs.Where(item => item.Bucket == bucket &&
                                   item.Name != "Great_Step_Diegetic_Boundary" &&
                                   !bars.Contains(item.Name) &&
                                   (!omitQueen || item.Name != "Queen_Ownership_Gate")).ToArray();
    }

    private static Mesh BuildTransientV10Mesh(
        IEnumerable<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, string name)
    {
        var builder = new BoxMeshBuilder(name);
        foreach (var spec in specs) builder.Add(spec.Position, spec.Rotation, spec.Scale);
        return builder.Build();
    }

    private static void ValidateFrozenV11Inputs()
    {
        ValidateFileHash(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath,
            V11LimestoneSha256);
        ValidateFileHash(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenLimestonePath + ".meta",
            V11LimestoneMetaSha256);
        ValidateFileHash(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath,
            V11GraniteSha256);
        ValidateFileHash(ChannelPlayKhufuV11RoyalCircuitMeshPipeline.V10OpenGranitePath + ".meta",
            V11GraniteMetaSha256);
    }

    private static void ValidateFileHash(string path, string expected)
    {
        if (!File.Exists(path)) throw new FileNotFoundException("Frozen V11 input is missing.", path);
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
        {
            var actual = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty).ToLowerInvariant();
            if (actual != expected) throw new InvalidOperationException("Frozen V11 input hash drifted: " + path);
        }
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

    private static void Write(BinaryWriter writer, Vector3 value)
    {
        writer.Write(value.x);
        writer.Write(value.y);
        writer.Write(value.z);
    }

    private static void EnsureFolder()
    {
        var parts = GeneratedRoot.Split('/');
        var current = parts[0];
        for (var index = 1; index < parts.Length; index++)
        {
            var next = current + "/" + parts[index];
            if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(current, parts[index]);
            current = next;
        }
    }

    public sealed class BoxSpec
    {
        public readonly string SegmentId;
        public readonly string Name;
        public readonly string Bucket;
        public readonly Vector3 Position;
        public readonly Quaternion Rotation;
        public readonly Vector3 Scale;
        public readonly bool Structural;
        public readonly bool Collider;

        public BoxSpec(string segmentId, string name, string bucket, Vector3 position, Quaternion rotation,
            Vector3 scale, bool structural, bool collider)
        {
            SegmentId = segmentId;
            Name = name;
            Bucket = bucket;
            Position = position;
            Rotation = rotation;
            Scale = scale;
            Structural = structural;
            Collider = collider;
        }
    }

    public sealed class RouteFrame
    {
        public Vector3 Center;
        public float Length;
        public Quaternion Rotation;
        public Vector3 Right;
        public Vector3 Up;
        public Vector3 Forward;
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
            Add(spec.Position, spec.Rotation, spec.Scale);
        }

        public void Add(Vector3 position, Quaternion rotation, Vector3 scale)
        {
            var half = scale * 0.5f;
            var corners = new[]
            {
                new Vector3(-half.x, -half.y, -half.z), new Vector3(half.x, -half.y, -half.z),
                new Vector3(half.x, half.y, -half.z), new Vector3(-half.x, half.y, -half.z),
                new Vector3(-half.x, -half.y, half.z), new Vector3(half.x, -half.y, half.z),
                new Vector3(half.x, half.y, half.z), new Vector3(-half.x, half.y, half.z)
            };
            var matrix = Matrix4x4.TRS(position, rotation, Vector3.one);
            for (var face = 0; face < 6; face++)
            {
                var start = vertices.Count;
                for (var corner = 0; corner < 4; corner++)
                {
                    vertices.Add(matrix.MultiplyPoint3x4(corners[FaceCorners[face, corner]]));
                    normals.Add(rotation * FaceNormals[face]);
                }
                var tile = FaceTile(scale, face);
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

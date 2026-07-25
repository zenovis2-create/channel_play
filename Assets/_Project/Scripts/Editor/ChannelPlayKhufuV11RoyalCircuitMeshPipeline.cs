using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV11RoyalCircuitMeshPipeline
{
    public const string GeneratedRoot = "Assets/_Project/Art/Generated/KhufuV11RoyalCircuit";
    public const string LimestoneBucket = "Limestone_Structure";
    public const string GraniteBucket = "Red_Granite_Royal";
    public const string ShadowBucket = "Shadow_Recess";
    public const string DisplayBucket = "Stacked_Chamber_Display";
    public const string InlayBucket = "Royal_Route_Inlay";
    public const int ExpectedRendererCount = 5;

    public const string GreatStepSegment = "Great_Step_Transition";
    public const string EntrySegment = "Royal_Entry_Passage";
    public const string AntechamberSegment = "Antechamber_Portcullis";
    public const string KingsChamberSegment = "Kings_Chamber";
    public const string SarcophagusSegment = "Granite_Sarcophagus";
    public const string ShaftSegment = "Shaft_Mouth_Boundaries";
    public const string StackedDisplaySegment = "Stacked_Chamber_Display";
    public const string RouteInlaySegment = "HYBRID_Royal_Route_Inlay";

    public const string V10OpenLimestonePath = GeneratedRoot + "/KhufuV11_V10_Limestone_Open.asset";
    public const string V10OpenGranitePath = GeneratedRoot + "/KhufuV11_V10_Red_Granite_Open.asset";
    public const string V10ClosedLimestonePath =
        "Assets/_Project/Art/Generated/KhufuV10InteriorSpine/KhufuV10_Limestone_Structure.asset";
    public const string V10ClosedGranitePath =
        "Assets/_Project/Art/Generated/KhufuV10InteriorSpine/KhufuV10_Red_Granite_Boundary.asset";
    public const string V10ClosedLimestoneSha256 =
        "0d8f1bd4344e3308e2bd6cb881359400796ba8bdd5a2d410665b591ff4d04cd1";
    public const string V10ClosedLimestoneMetaSha256 =
        "4123715868c6fc596cc57b74227a6ee74a6d458927c0348a31879027a51d2e2f";
    public const string V10ClosedGraniteSha256 =
        "e75e0101e120748489d756012eeb846588143de8f64552566dc9eb308c4e5916";
    public const string V10ClosedGraniteMetaSha256 =
        "492531fbb372dd5ec908a005f50e0b342805aba2abf6efd66147a2cd0fdc6161";

    public static readonly string[] Buckets =
    {
        LimestoneBucket, GraniteBucket, ShadowBucket, DisplayBucket, InlayBucket
    };

    public static readonly string[] Segments =
    {
        GreatStepSegment, EntrySegment, AntechamberSegment, KingsChamberSegment,
        SarcophagusSegment, ShaftSegment, StackedDisplaySegment, RouteInlaySegment
    };

    public static List<BoxSpec> BuildSpecs()
    {
        var specs = new List<BoxSpec>();
        AddGreatStepTransition(specs);
        AddEntryPassage(specs);
        AddAntechamber(specs);
        AddKingsChamber(specs);
        AddSarcophagus(specs);
        AddStackedDisplay(specs);
        AddRouteInlay(specs);
        return specs;
    }

    public static Dictionary<string, Mesh> BuildAndSaveMeshes(IReadOnlyList<BoxSpec> specs)
    {
        EnsureFolder();
        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal);
        foreach (var bucket in Buckets)
        {
            var generated = BuildTransientMesh(specs, bucket, "KhufuV11_" + bucket);
            result.Add(bucket, SaveMesh(generated, GeneratedRoot + "/KhufuV11_" + bucket + ".asset"));
        }
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        return result;
    }

    public static Dictionary<string, Mesh> BuildAndSaveV10OpenVariants()
    {
        EnsureFolder();
        var specs = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs();
        ValidateFrozenV10Sources(specs);
        var limestoneSpecs = FilterV10OpenSpecs(specs,
            ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket);
        var graniteSpecs = FilterV10OpenSpecs(specs,
            ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket);
        var limestone = BuildTransientV10Mesh(limestoneSpecs, "KhufuV11_V10_Limestone_Open");
        var granite = BuildTransientV10Mesh(graniteSpecs, "KhufuV11_V10_Red_Granite_Open");

        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal)
        {
            { LimestoneBucket, SaveMesh(limestone, V10OpenLimestonePath) },
            { GraniteBucket, SaveMesh(granite, V10OpenGranitePath) }
        };
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        ValidateMeshMatches(result[LimestoneBucket], BuildTransientV10Mesh(limestoneSpecs, "Expected_V10_Limestone_Open"),
            "V10 limestone open variant");
        ValidateMeshMatches(result[GraniteBucket], BuildTransientV10Mesh(graniteSpecs, "Expected_V10_Granite_Open"),
            "V10 granite open variant");
        ValidateFrozenV10Sources(specs);
        return result;
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

    public static void ValidateV10TransitionAssets()
    {
        var specs = ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs();
        ValidateFrozenV10Sources(specs);
        ValidateAssetGeometry(V10OpenLimestonePath,
            FilterV10OpenSpecs(specs, ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket),
            "V10 limestone open variant");
        ValidateAssetGeometry(V10OpenGranitePath,
            FilterV10OpenSpecs(specs, ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket),
            "V10 granite open variant");
    }

    public static void ValidateFrozenV10Sources()
    {
        ValidateFrozenV10Sources(ChannelPlayKhufuV10InteriorMeshPipeline.BuildSpecs());
    }

    public static int TriangleCount(Mesh mesh)
    {
        if (mesh == null) return 0;
        var triangles = 0;
        for (var index = 0; index < mesh.subMeshCount; index++)
            triangles += (int)mesh.GetIndexCount(index) / 3;
        return triangles;
    }

    private static void AddGreatStepTransition(List<BoxSpec> specs)
    {
        AddPassage(specs, GreatStepSegment, "Great_Step_Open_Connector",
            KhufuV11RoyalRouteContract.GreatStepEntry,
            KhufuV11RoyalRouteContract.RoyalThreshold,
            2.8f, 2.9f, LimestoneBucket, true);
        Add(specs, GreatStepSegment, "Great_Step_Threshold_Block", GraniteBucket,
            KhufuV11RoyalRouteContract.RoyalThreshold - Vector3.up * 0.05f,
            KhufuV11RoyalRouteContract.Rotation, new Vector3(3.1f, 0.22f, 0.65f), true, false);
    }

    private static void AddEntryPassage(List<BoxSpec> specs)
    {
        AddPassage(specs, EntrySegment, "Royal_Entry",
            KhufuV11RoyalRouteContract.RoyalThreshold,
            KhufuV11RoyalRouteContract.EntryEnd,
            2.75f, 2.7f, LimestoneBucket, true);
    }

    private static void AddAntechamber(List<BoxSpec> specs)
    {
        var center = KhufuV11RoyalRouteContract.AntechamberCenter;
        var rotation = KhufuV11RoyalRouteContract.Rotation;
        var right = KhufuV11RoyalRouteContract.Right;
        var forward = KhufuV11RoyalRouteContract.Forward;
        const float width = 3.4f;
        const float depth = 2.2f;
        const float height = 3.6f;

        Add(specs, AntechamberSegment, "Antechamber_Floor", GraniteBucket,
            center - Vector3.up * 0.22f, rotation, new Vector3(width, 0.28f, depth), true, true);
        Add(specs, AntechamberSegment, "Antechamber_West_Wall", GraniteBucket,
            center - right * (width * 0.5f + 0.22f) + Vector3.up * (height * 0.5f),
            rotation, new Vector3(0.44f, height, depth), true, true);
        Add(specs, AntechamberSegment, "Antechamber_East_Wall", GraniteBucket,
            center + right * (width * 0.5f + 0.22f) + Vector3.up * (height * 0.5f),
            rotation, new Vector3(0.44f, height, depth), true, true);
        Add(specs, AntechamberSegment, "Antechamber_Ceiling", GraniteBucket,
            center + Vector3.up * height, rotation, new Vector3(width + 0.9f, 0.35f, depth), true, true);

        for (var index = 0; index < 3; index++)
        {
            var trackCenter = center + forward * (-0.82f + index * 0.82f);
            Add(specs, AntechamberSegment, "Portcullis_Track_West_" + index.ToString("D2"), LimestoneBucket,
                trackCenter - right * 1.42f + Vector3.up * 1.8f,
                rotation, new Vector3(0.18f, 3.25f, 0.24f), false, false);
            Add(specs, AntechamberSegment, "Portcullis_Track_East_" + index.ToString("D2"), LimestoneBucket,
                trackCenter + right * 1.42f + Vector3.up * 1.8f,
                rotation, new Vector3(0.18f, 3.25f, 0.24f), false, false);
            Add(specs, AntechamberSegment, "Portcullis_Raised_Slab_" + index.ToString("D2"), GraniteBucket,
                trackCenter + Vector3.up * 3.15f,
                rotation, new Vector3(2.6f, 0.72f, 0.22f), false, false);
            Add(specs, AntechamberSegment, "Portcullis_Shadow_" + index.ToString("D2"), ShadowBucket,
                trackCenter + Vector3.up * 3.05f - forward * 0.13f,
                rotation, new Vector3(2.2f, 0.45f, 0.05f), false, false);
        }

        AddPassage(specs, EntrySegment, "Antechamber_To_Kings_Entry",
            center + forward * (depth * 0.5f - 0.15f),
            KhufuV11RoyalRouteContract.KingsEntrance,
            2.55f, 2.7f, LimestoneBucket, true);
    }

    private static void AddKingsChamber(List<BoxSpec> specs)
    {
        var center = KhufuV11RoyalRouteContract.KingsChamberCenter;
        var rotation = KhufuV11RoyalRouteContract.Rotation;
        var right = KhufuV11RoyalRouteContract.Right;
        var forward = KhufuV11RoyalRouteContract.Forward;
        const float width = 9f;
        const float depth = 5.4f;
        const float height = 4.85f;
        const float wall = 0.48f;

        Add(specs, KingsChamberSegment, "Kings_Chamber_Floor", GraniteBucket,
            center - Vector3.up * 0.16f, rotation, new Vector3(width, 0.32f, depth), true, true);
        Add(specs, KingsChamberSegment, "Kings_Chamber_West_Wall", GraniteBucket,
            center - right * (width * 0.5f + wall * 0.5f) + Vector3.up * (height * 0.5f),
            rotation, new Vector3(wall, height, depth + wall), true, true);
        Add(specs, KingsChamberSegment, "Kings_Chamber_East_Wall", GraniteBucket,
            center + right * (width * 0.5f + wall * 0.5f) + Vector3.up * (height * 0.5f),
            rotation, new Vector3(wall, height, depth + wall), true, true);
        Add(specs, KingsChamberSegment, "Kings_Chamber_South_Wall", GraniteBucket,
            center + forward * (depth * 0.5f + wall * 0.5f) + Vector3.up * (height * 0.5f),
            rotation, new Vector3(width + wall, height, wall), true, true);

        var north = center - forward * (depth * 0.5f + wall * 0.5f);
        Add(specs, KingsChamberSegment, "Kings_Chamber_North_Wall_West", GraniteBucket,
            north - right * 3.25f + Vector3.up * (height * 0.5f),
            rotation, new Vector3(2.5f, height, wall), true, true);
        Add(specs, KingsChamberSegment, "Kings_Chamber_North_Wall_East", GraniteBucket,
            north + right * 3.25f + Vector3.up * (height * 0.5f),
            rotation, new Vector3(2.5f, height, wall), true, true);
        Add(specs, KingsChamberSegment, "Kings_Chamber_North_Lintel", GraniteBucket,
            north + Vector3.up * 3.8f,
            rotation, new Vector3(4f, 2.1f, wall), true, true);

        for (var beam = 0; beam < 9; beam++)
        {
            var offset = -4f + beam;
            Add(specs, KingsChamberSegment, "Kings_Ceiling_Beam_" + beam.ToString("D2"), GraniteBucket,
                center + right * offset + Vector3.up * height,
                rotation, new Vector3(0.94f, 0.42f, depth + 0.72f), true, true);
        }

        var northShaftMouth = north + right * 2.25f + forward * 0.26f + Vector3.up * 1.95f;
        var southShaftMouth = center + forward * (depth * 0.5f + wall * 0.5f - 0.26f) -
                              right * 2.15f + Vector3.up * 1.95f;
        Add(specs, ShaftSegment, "North_Shaft_Mouth_Recess", ShadowBucket,
            northShaftMouth,
            rotation, new Vector3(0.68f, 0.68f, 0.06f), false, false);
        Add(specs, ShaftSegment, "South_Shaft_Mouth_Recess", ShadowBucket,
            southShaftMouth,
            rotation, new Vector3(0.68f, 0.68f, 0.06f), false, false);
        AddShaftMouthFrame(specs, "North_Shaft_Mouth", northShaftMouth, rotation, right);
        AddShaftMouthFrame(specs, "South_Shaft_Mouth", southShaftMouth, rotation, right);
    }

    private static void AddShaftMouthFrame(List<BoxSpec> specs, string prefix, Vector3 center,
        Quaternion rotation, Vector3 right)
    {
        const float outer = 0.92f;
        const float edge = 0.1f;
        const float depth = 0.09f;
        Add(specs, ShaftSegment, prefix + "_Frame_West", LimestoneBucket,
            center - right * (outer * 0.5f), rotation, new Vector3(edge, outer, depth), false, false);
        Add(specs, ShaftSegment, prefix + "_Frame_East", LimestoneBucket,
            center + right * (outer * 0.5f), rotation, new Vector3(edge, outer, depth), false, false);
        Add(specs, ShaftSegment, prefix + "_Frame_Lintel", LimestoneBucket,
            center + Vector3.up * (outer * 0.5f), rotation, new Vector3(outer + edge, edge, depth), false, false);
        Add(specs, ShaftSegment, prefix + "_Frame_Sill", LimestoneBucket,
            center - Vector3.up * (outer * 0.5f), rotation, new Vector3(outer + edge, edge, depth), false, false);
    }

    private static void AddSarcophagus(List<BoxSpec> specs)
    {
        var center = KhufuV11RoyalRouteContract.SarcophagusCenter;
        var rotation = KhufuV11RoyalRouteContract.Rotation;
        var right = KhufuV11RoyalRouteContract.Right;
        var forward = KhufuV11RoyalRouteContract.Forward;

        Add(specs, SarcophagusSegment, "Sarcophagus_Base", GraniteBucket,
            center + Vector3.up * 0.12f, rotation, new Vector3(2.45f, 0.24f, 1.2f), true, true);
        Add(specs, SarcophagusSegment, "Sarcophagus_West_Rim", GraniteBucket,
            center - right * 1.12f + Vector3.up * 0.67f,
            rotation, new Vector3(0.22f, 1.1f, 1.2f), false, false);
        Add(specs, SarcophagusSegment, "Sarcophagus_East_Rim", GraniteBucket,
            center + right * 1.12f + Vector3.up * 0.67f,
            rotation, new Vector3(0.22f, 1.1f, 1.2f), false, false);
        Add(specs, SarcophagusSegment, "Sarcophagus_North_Rim", GraniteBucket,
            center - forward * 0.5f + Vector3.up * 0.67f,
            rotation, new Vector3(2.05f, 1.1f, 0.2f), false, false);
        Add(specs, SarcophagusSegment, "Sarcophagus_South_Rim", GraniteBucket,
            center + forward * 0.5f + Vector3.up * 0.67f,
            rotation, new Vector3(2.05f, 1.1f, 0.2f), false, false);
        Add(specs, SarcophagusSegment, "Sarcophagus_Interior_Shadow", ShadowBucket,
            center + Vector3.up * 1.18f, rotation, new Vector3(1.85f, 0.05f, 0.72f), false, false);
    }

    private static void AddStackedDisplay(List<BoxSpec> specs)
    {
        var center = KhufuV11RoyalRouteContract.KingsChamberCenter;
        var rotation = KhufuV11RoyalRouteContract.Rotation;
        var right = KhufuV11RoyalRouteContract.Right;
        const float width = 9f;
        const float depth = 4.2f;
        const float firstY = 5.45f;
        const float levelStep = 0.72f;

        for (var level = 0; level < 5; level++)
        {
            var y = firstY + level * levelStep;
            var suffix = (level + 1).ToString("D2");
            Add(specs, StackedDisplaySegment, "Display_Level_" + suffix + "_Beam", DisplayBucket,
                center + Vector3.up * y, rotation, new Vector3(width + 0.4f, 0.3f, depth + 0.4f), false, false);
            Add(specs, StackedDisplaySegment, "Display_Level_" + suffix + "_West_Edge", DisplayBucket,
                center - right * 4.63f + Vector3.up * (y + 0.54f),
                rotation, new Vector3(0.26f, 0.9f, depth), false, false);
            Add(specs, StackedDisplaySegment, "Display_Level_" + suffix + "_East_Edge", DisplayBucket,
                center + right * 4.63f + Vector3.up * (y + 0.54f),
                rotation, new Vector3(0.26f, 0.9f, depth), false, false);
        }

        var capY = firstY + 5f * levelStep + 0.45f;
        const float capDepth = 3f;
        var leftRotation = rotation * Quaternion.Euler(0f, 0f, 28f);
        var rightRotation = rotation * Quaternion.Euler(0f, 0f, -28f);
        Add(specs, StackedDisplaySegment, "Display_Gabled_Cap_West", DisplayBucket,
            center - right * 2.18f + Vector3.up * capY,
            leftRotation, new Vector3(5.2f, 0.34f, capDepth), false, false);
        Add(specs, StackedDisplaySegment, "Display_Gabled_Cap_East", DisplayBucket,
            center + right * 2.18f + Vector3.up * capY,
            rightRotation, new Vector3(5.2f, 0.34f, capDepth), false, false);
    }

    private static void AddRouteInlay(List<BoxSpec> specs)
    {
        var route = KhufuV11RoyalRouteContract.TraversalRoute();
        for (var index = 1; index < route.Count; index++)
        {
            var frame = Frame(route[index - 1], route[index]);
            Add(specs, RouteInlaySegment, "Royal_Route_" + (index - 1).ToString("D2"), InlayBucket,
                frame.Center + frame.Up * 0.025f,
                frame.Rotation, new Vector3(0.09f, 0.035f, frame.Length), false, false);
        }
    }

    private static void AddPassage(List<BoxSpec> specs, string segment, string name, Vector3 start, Vector3 end,
        float clearWidth, float clearHeight, string bucket, bool collider)
    {
        var frame = Frame(start, end);
        const float wall = 0.38f;
        const float floor = 0.24f;
        Add(specs, segment, name + "_Floor", bucket,
            frame.Center - frame.Up * (floor * 0.5f), frame.Rotation,
            new Vector3(clearWidth + wall * 2f, floor, frame.Length), true, collider);
        Add(specs, segment, name + "_West_Wall", bucket,
            frame.Center - frame.Right * (clearWidth * 0.5f + wall * 0.5f) + frame.Up * (clearHeight * 0.5f),
            frame.Rotation, new Vector3(wall, clearHeight, frame.Length), true, collider);
        Add(specs, segment, name + "_East_Wall", bucket,
            frame.Center + frame.Right * (clearWidth * 0.5f + wall * 0.5f) + frame.Up * (clearHeight * 0.5f),
            frame.Rotation, new Vector3(wall, clearHeight, frame.Length), true, collider);
        Add(specs, segment, name + "_Ceiling", bucket,
            frame.Center + frame.Up * clearHeight, frame.Rotation,
            new Vector3(clearWidth + wall * 2f, floor, frame.Length), true, collider);
    }

    private static void Add(List<BoxSpec> specs, string segment, string name, string bucket,
        Vector3 position, Quaternion rotation, Vector3 scale, bool structural, bool collider)
    {
        specs.Add(new BoxSpec(segment, name, bucket, position, rotation, scale, structural, collider));
    }

    private static RouteFrame Frame(Vector3 start, Vector3 end)
    {
        var delta = end - start;
        if (delta.sqrMagnitude < 0.0001f) throw new InvalidOperationException("V11 frame length is zero.");
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

    private static IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> FilterV10OpenSpecs(
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, string bucket)
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

        return specs.Where(item => item.Bucket == bucket &&
                                   item.Name != "Great_Step_Diegetic_Boundary" &&
                                   !expectedBars.Contains(item.Name)).ToArray();
    }

    private static Mesh BuildTransientV10Mesh(
        IEnumerable<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, string name)
    {
        var builder = new BoxMeshBuilder(name);
        foreach (var spec in specs) builder.Add(spec.Position, spec.Rotation, spec.Scale);
        return builder.Build();
    }

    private static void ValidateFrozenV10Sources(
        IReadOnlyList<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs)
    {
        ValidateFileHash(V10ClosedLimestonePath, V10ClosedLimestoneSha256);
        ValidateFileHash(V10ClosedLimestonePath + ".meta", V10ClosedLimestoneMetaSha256);
        ValidateFileHash(V10ClosedGranitePath, V10ClosedGraniteSha256);
        ValidateFileHash(V10ClosedGranitePath + ".meta", V10ClosedGraniteMetaSha256);
        ValidateAssetGeometry(V10ClosedLimestonePath,
            specs.Where(item => item.Bucket == ChannelPlayKhufuV10InteriorMeshPipeline.LimestoneBucket),
            "frozen V10 limestone source");
        ValidateAssetGeometry(V10ClosedGranitePath,
            specs.Where(item => item.Bucket == ChannelPlayKhufuV10InteriorMeshPipeline.RedGraniteBucket),
            "frozen V10 granite source");
    }

    private static void ValidateAssetGeometry(string path,
        IEnumerable<ChannelPlayKhufuV10InteriorMeshPipeline.BoxSpec> specs, string label)
    {
        var actual = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (actual == null) throw new InvalidOperationException(label + " asset is missing: " + path);
        var expected = BuildTransientV10Mesh(specs, "Expected_" + label.Replace(" ", "_"));
        ValidateMeshMatches(actual, expected, label);
    }

    private static void ValidateMeshMatches(Mesh actual, Mesh expected, string label)
    {
        try
        {
            if (GeometrySignature(actual) != GeometrySignature(expected))
                throw new InvalidOperationException(label + " geometry signature drifted.");
        }
        finally
        {
            if (expected != null) UnityEngine.Object.DestroyImmediate(expected);
        }
    }

    private static void ValidateFileHash(string path, string expected)
    {
        if (!File.Exists(path)) throw new FileNotFoundException("Frozen V10 source is missing.", path);
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
        {
            var actual = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty)
                .ToLowerInvariant();
            if (actual != expected) throw new InvalidOperationException("Frozen V10 source hash drifted: " + path);
        }
    }

    private static void Write(BinaryWriter writer, Vector3 value)
    {
        writer.Write(value.x);
        writer.Write(value.y);
        writer.Write(value.z);
    }

    private static void EnsureFolder()
    {
        var segments = GeneratedRoot.Split('/');
        var current = segments[0];
        for (var index = 1; index < segments.Length; index++)
        {
            var next = current + "/" + segments[index];
            if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(current, segments[index]);
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
                triangles.Add(start); triangles.Add(start + 1); triangles.Add(start + 2);
                triangles.Add(start); triangles.Add(start + 2); triangles.Add(start + 3);
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
            return new Vector2(Mathf.Max(1f, dimensions.x / 2.2f), Mathf.Max(1f, dimensions.y / 2.2f));
        }
    }
}

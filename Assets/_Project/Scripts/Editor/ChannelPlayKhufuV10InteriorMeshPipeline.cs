using System;
using System.Collections.Generic;
using System.Linq;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV10InteriorMeshPipeline
{
    public const string GeneratedRoot = "Assets/_Project/Art/Generated/KhufuV10InteriorSpine";
    public const string LimestoneBucket = "Limestone_Structure";
    public const string GalleryDetailBucket = "Gallery_Detail";
    public const string RedGraniteBucket = "Red_Granite_Boundary";
    public const string HybridBucket = "Hybrid_Service_Return";
    public const string ShadowBucket = "Shadow_Recess";
    public const string InlayBucket = "Route_Inlay";
    public const int ExpectedRendererCount = 6;

    public const string NorthApproachSegment = "North_Approach";
    public const string EntranceBranchSegment = "Entrance_To_Branch";
    public const string BranchGallerySegment = "Branch_To_Gallery_Foot";
    public const string GrandGallerySegment = "Grand_Gallery";
    public const string QueenThresholdSegment = "Queen_Branch_Threshold";
    public const string GreatStepSegment = "Great_Step_Boundary";
    public const string HistoricServiceSegment = "Historic_Service_Mouth";
    public const string HybridReturnSegment = "HYBRID_Service_Return";

    public static readonly Vector3 Entrance = KhufuV10RouteContract.Entrance;
    public static readonly Vector3 Branch = KhufuV10RouteContract.Branch;
    public static readonly Vector3 GalleryFoot = KhufuV10RouteContract.GalleryFoot;
    public static readonly Vector3 GalleryTop = KhufuV10RouteContract.GalleryTop;
    public static readonly Vector3 QueensChamber = KhufuV10RouteContract.QueensChamber;

    private static readonly string[] BucketOrder =
    {
        LimestoneBucket,
        GalleryDetailBucket,
        RedGraniteBucket,
        HybridBucket,
        ShadowBucket,
        InlayBucket
    };

    private static readonly string[] SegmentOrder =
    {
        NorthApproachSegment,
        EntranceBranchSegment,
        BranchGallerySegment,
        GrandGallerySegment,
        QueenThresholdSegment,
        GreatStepSegment,
        HistoricServiceSegment,
        HybridReturnSegment
    };

    public static IReadOnlyList<string> Buckets => BucketOrder;
    public static IReadOnlyList<string> Segments => SegmentOrder;

    public static List<BoxSpec> BuildSpecs()
    {
        var specs = new List<BoxSpec>();
        AddNorthEntrance(specs);
        AddDescendingAndJunction(specs);
        AddAscendingPassageAndBypass(specs);
        AddGrandGallery(specs);
        AddOwnershipBoundaries(specs);
        AddHybridReturn(specs);
        return specs.OrderBy(item => Array.IndexOf(BucketOrder, item.Bucket))
            .ThenBy(item => Array.IndexOf(SegmentOrder, item.SegmentId))
            .ThenBy(item => item.Name, StringComparer.Ordinal)
            .ToList();
    }

    public static IReadOnlyList<Vector3> NormalRoute()
    {
        return KhufuV10RouteContract.NormalRoute();
    }

    public static IReadOnlyList<Vector3> AscendingRoutePoints()
    {
        return KhufuV10RouteContract.AscendingRoutePoints();
    }

    public static IReadOnlyList<Vector3> HybridReturnPoints()
    {
        return KhufuV10RouteContract.HybridReturnPoints();
    }

    public static Vector3 GreatStepStop()
    {
        return KhufuV10RouteContract.GreatStepStop();
    }

    public static Vector3 HistoricServiceMouth()
    {
        return KhufuV10RouteContract.HistoricServiceMouth();
    }

    public static RouteFrame GalleryFrame()
    {
        return Frame(GalleryFoot, GalleryTop);
    }

    public static Dictionary<string, Mesh> BuildAndSaveMeshes(IReadOnlyList<BoxSpec> specs)
    {
        EnsureFolder();
        var result = new Dictionary<string, Mesh>(StringComparer.Ordinal);
        foreach (var bucket in BucketOrder)
        {
            var builder = new BoxMeshBuilder("KhufuV10_" + bucket);
            foreach (var spec in specs.Where(item => item.Bucket == bucket)) builder.Add(spec);
            var path = GeneratedRoot + "/KhufuV10_" + bucket + ".asset";
            result.Add(bucket, SaveMesh(builder.Build(), path));
        }
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        return result;
    }

    public static int TriangleCount(Mesh mesh)
    {
        if (mesh == null) return 0;
        var triangles = 0;
        for (var index = 0; index < mesh.subMeshCount; index++) triangles += (int)mesh.GetIndexCount(index) / 3;
        return triangles;
    }

    private static void AddNorthEntrance(List<BoxSpec> specs)
    {
        var segment = EntranceBranchSegment;
        Add(specs, segment, "Entrance_West_Jamb", LimestoneBucket, Entrance + new Vector3(-1.55f, 1.25f, -0.15f),
            Quaternion.identity, new Vector3(0.55f, 2.5f, 1.1f), true);
        Add(specs, segment, "Entrance_East_Jamb", LimestoneBucket, Entrance + new Vector3(1.55f, 1.25f, -0.15f),
            Quaternion.identity, new Vector3(0.55f, 2.5f, 1.1f), true);
        Add(specs, segment, "Entrance_Lintel", LimestoneBucket, Entrance + new Vector3(0f, 2.58f, -0.15f),
            Quaternion.identity, new Vector3(3.65f, 0.42f, 1.15f), true);
        Add(specs, segment, "Entrance_Chevron_West", GalleryDetailBucket, Entrance + new Vector3(-0.95f, 3.35f, -0.12f),
            Quaternion.Euler(0f, 0f, 34f), new Vector3(2.45f, 0.42f, 1.2f), true);
        Add(specs, segment, "Entrance_Chevron_East", GalleryDetailBucket, Entrance + new Vector3(0.95f, 3.35f, -0.12f),
            Quaternion.Euler(0f, 0f, -34f), new Vector3(2.45f, 0.42f, 1.2f), true);
        Add(specs, segment, "Entrance_Shadow", ShadowBucket, Entrance + new Vector3(0f, 0.85f, 0.43f),
            Quaternion.identity, new Vector3(2.5f, 2.2f, 0.15f), false);
        Add(specs, NorthApproachSegment, "Approach_Threshold_Inlay", InlayBucket,
            Entrance + new Vector3(0f, 0.18f, -1.2f), Quaternion.identity, new Vector3(2.25f, 0.025f, 0.08f), false);
    }

    private static void AddDescendingAndJunction(List<BoxSpec> specs)
    {
        var descendEnd = Vector3.Lerp(Entrance, Branch, 0.9f);
        AddPassage(specs, EntranceBranchSegment, "Descending_Upper", Entrance, descendEnd, 2.6f, 2.8f,
            LimestoneBucket, true, 2f);
        Add(specs, EntranceBranchSegment, "Branch_Junction_Floor", LimestoneBucket,
            Branch + Vector3.down * 0.11f, Quaternion.identity, new Vector3(5.2f, 0.22f, 5.2f), true);
        for (var index = 0; index < 4; index++)
        {
            var angle = 45f + index * 90f;
            var offset = Quaternion.Euler(0f, angle, 0f) * new Vector3(2.8f, 0f, 0f);
            Add(specs, EntranceBranchSegment, "Branch_Pier_" + index.ToString("D2"), LimestoneBucket,
                Branch + offset + Vector3.up * 1.5f, Quaternion.identity, new Vector3(0.48f, 3f, 0.48f), false);
        }
    }

    private static void AddAscendingPassageAndBypass(List<BoxSpec> specs)
    {
        var rejoin = AscendingRejoin();
        var blockedEnd = BlockedStubEnd();
        var stubStart = Vector3.Lerp(Branch, blockedEnd, 0.4f);
        var stubEnd = Vector3.Lerp(Branch, blockedEnd, 0.92f);
        AddPassage(specs, BranchGallerySegment, "Ascending_Blocked_Stub", stubStart, stubEnd, 2.6f, 2.8f,
            LimestoneBucket, false);
        var stubFrame = Frame(stubStart, stubEnd);
        for (var plug = 0; plug < 3; plug++)
        {
            var point = Vector3.Lerp(stubStart, stubEnd, 0.32f + plug * 0.24f);
            Add(specs, BranchGallerySegment, "Granite_Plug_" + plug.ToString("D2"), RedGraniteBucket,
                point + stubFrame.Up * 1.3f, stubFrame.Rotation, new Vector3(2.48f, 2.6f, 0.52f), true);
        }

        var ascending = AscendingRoutePoints();
        AddPassage(specs, BranchGallerySegment, "Plug_Bypass_A", ascending[0], ascending[1], 2.6f, 2.8f,
            LimestoneBucket, true, 2f, false);
        AddPassage(specs, BranchGallerySegment, "Plug_Bypass_B", ascending[1], ascending[2], 2.6f, 2.8f, LimestoneBucket);
        AddPassage(specs, BranchGallerySegment, "Plug_Bypass_C", ascending[2], ascending[3], 2.6f, 2.8f,
            LimestoneBucket, true, 2f);
        AddPassage(specs, BranchGallerySegment, "Ascending_Upper", Vector3.Lerp(rejoin, GalleryFoot, 0.06f), GalleryFoot,
            2.6f, 2.8f, LimestoneBucket, true, 2f, false);

        var upperFrame = Frame(rejoin, GalleryFoot);
        for (var frameIndex = 0; frameIndex < 4; frameIndex++)
        {
            var point = Vector3.Lerp(rejoin, GalleryFoot, 0.2f + frameIndex * 0.2f);
            AddFrame(specs, BranchGallerySegment, "Girdle_Frame_" + frameIndex.ToString("D2"), point, upperFrame,
                2.6f, 2.8f, LimestoneBucket, false);
        }
    }

    private static void AddGrandGallery(List<BoxSpec> specs)
    {
        var frame = Frame(GalleryFoot, GalleryTop);
        // Keep the Gallery Foot open so the adapted Queen passage reads as a distinct lower junction.
        var structuralStart = GalleryFoot + frame.Forward * 2.65f;
        var galleryFrame = Frame(structuralStart, GalleryTop);
        var floorFrame = Frame(GalleryFoot, GalleryTop + frame.Forward * 1.1f);
        Add(specs, GrandGallerySegment, "Gallery_Floor_Ramp", LimestoneBucket,
            floorFrame.Center - floorFrame.Up * 0.12f,
            floorFrame.Rotation, new Vector3(4.8f, 0.24f, floorFrame.Length), true);
        Add(specs, GrandGallerySegment, "Gallery_West_Bench", GalleryDetailBucket,
            galleryFrame.Center - galleryFrame.Right * 1.52f + galleryFrame.Up * 0.4f,
            galleryFrame.Rotation, new Vector3(0.78f, 0.8f, galleryFrame.Length), true);
        Add(specs, GrandGallerySegment, "Gallery_East_Bench", GalleryDetailBucket,
            galleryFrame.Center + galleryFrame.Right * 1.52f + galleryFrame.Up * 0.4f,
            galleryFrame.Rotation, new Vector3(0.78f, 0.8f, galleryFrame.Length), true);
        Add(specs, GrandGallerySegment, "Gallery_West_Lower_Wall", LimestoneBucket,
            galleryFrame.Center - galleryFrame.Right * 2.34f + galleryFrame.Up * 2.1f,
            galleryFrame.Rotation, new Vector3(0.42f, 4.2f, galleryFrame.Length), true);
        Add(specs, GrandGallerySegment, "Gallery_East_Lower_Wall", LimestoneBucket,
            galleryFrame.Center + galleryFrame.Right * 2.34f + galleryFrame.Up * 2.1f,
            galleryFrame.Rotation, new Vector3(0.42f, 4.2f, galleryFrame.Length), true);

        for (var band = 0; band < 7; band++)
        {
            var x = 2.12f - band * 0.16f;
            var y = 2.65f + band * 0.5f;
            Add(specs, GrandGallerySegment, "Gallery_Corbel_West_" + band.ToString("D2"), LimestoneBucket,
                galleryFrame.Center - galleryFrame.Right * x + galleryFrame.Up * y,
                galleryFrame.Rotation, new Vector3(0.38f, 0.72f, galleryFrame.Length), true);
            Add(specs, GrandGallerySegment, "Gallery_Corbel_East_" + band.ToString("D2"), LimestoneBucket,
                galleryFrame.Center + galleryFrame.Right * x + galleryFrame.Up * y,
                galleryFrame.Rotation, new Vector3(0.38f, 0.72f, galleryFrame.Length), true);
        }
        Add(specs, GrandGallerySegment, "Gallery_Ceiling", LimestoneBucket,
            galleryFrame.Center + galleryFrame.Up * 6.15f, galleryFrame.Rotation,
            new Vector3(2.2f, 0.34f, galleryFrame.Length), true);

        for (var stair = 0; stair < 18; stair++)
        {
            var point = Vector3.Lerp(GalleryFoot, GalleryTop, (stair + 0.5f) / 18f);
            Add(specs, GrandGallerySegment, "Gallery_Tread_" + stair.ToString("D2"), GalleryDetailBucket,
                point + frame.Up * 0.14f, frame.Rotation, new Vector3(2.18f, 0.08f, 0.42f), false);
        }

        for (var side = -1; side <= 1; side += 2)
        for (var slot = 0; slot < 27; slot++)
        {
            var t = (slot + 0.65f) / 27.6f;
            var point = Vector3.Lerp(structuralStart, GalleryTop - frame.Forward * 0.65f, t);
            var suffix = side < 0 ? "West" : "East";
            Add(specs, GrandGallerySegment, "Gallery_Bench_Slot_" + suffix + "_" + slot.ToString("D2"), ShadowBucket,
                point + frame.Right * (1.52f * side) + frame.Up * 0.815f,
                frame.Rotation, new Vector3(0.28f, 0.045f, 0.18f), false);
        }
        Add(specs, GrandGallerySegment, "Gallery_Groove_West", InlayBucket,
            galleryFrame.Center - galleryFrame.Right * 1.72f + galleryFrame.Up * 3.58f,
            galleryFrame.Rotation, new Vector3(0.035f, 0.13f, galleryFrame.Length), false);
        Add(specs, GrandGallerySegment, "Gallery_Groove_East", InlayBucket,
            galleryFrame.Center + galleryFrame.Right * 1.72f + galleryFrame.Up * 3.58f,
            galleryFrame.Rotation, new Vector3(0.035f, 0.13f, galleryFrame.Length), false);
    }

    private static void AddOwnershipBoundaries(List<BoxSpec> specs)
    {
        var gallery = Frame(GalleryFoot, GalleryTop);
        var queenDirection = (QueensChamber - GalleryFoot).normalized;
        var queenRotation = Quaternion.LookRotation(queenDirection, Vector3.up);
        var queenRight = queenRotation * Vector3.right;
        var queenThreshold = GalleryFoot + queenDirection * 2.5f;
        Add(specs, QueenThresholdSegment, "Queen_Threshold_West_Post", LimestoneBucket,
            queenThreshold - queenRight * 1.5f + Vector3.up * 1.3f, queenRotation, new Vector3(0.42f, 2.6f, 0.62f), true);
        Add(specs, QueenThresholdSegment, "Queen_Threshold_East_Post", LimestoneBucket,
            queenThreshold + queenRight * 1.5f + Vector3.up * 1.3f, queenRotation, new Vector3(0.42f, 2.6f, 0.62f), true);
        Add(specs, QueenThresholdSegment, "Queen_Threshold_Lintel", LimestoneBucket,
            queenThreshold + Vector3.up * 2.65f, queenRotation, new Vector3(3.4f, 0.38f, 0.64f), true);
        Add(specs, QueenThresholdSegment, "Queen_Ownership_Gate", RedGraniteBucket,
            queenThreshold + queenDirection * 0.32f + Vector3.up * 1.15f, queenRotation,
            new Vector3(2.5f, 2.3f, 0.26f), true);

        var boundaryPosition = GalleryTop + gallery.Forward * 0.38f + gallery.Up * 2.25f;
        Add(specs, GreatStepSegment, "Great_Step_Diegetic_Boundary", LimestoneBucket,
            boundaryPosition, gallery.Rotation, new Vector3(4.8f, 4.5f, 0.48f), true);
        for (var bar = -2; bar <= 2; bar++)
        {
            Add(specs, GreatStepSegment, "Great_Step_Granite_Bar_" + (bar + 2).ToString("D2"), RedGraniteBucket,
                boundaryPosition - gallery.Forward * 0.26f + gallery.Right * (bar * 0.62f),
                gallery.Rotation, new Vector3(0.22f, 3.55f, 0.18f), false);
        }
        Add(specs, GreatStepSegment, "Great_Step_West_Slot", ShadowBucket,
            GalleryTop - gallery.Right * 1.52f + gallery.Up * 0.82f - gallery.Forward * 0.32f,
            gallery.Rotation, new Vector3(0.3f, 0.05f, 0.2f), false);
        Add(specs, GreatStepSegment, "Great_Step_East_Slot", ShadowBucket,
            GalleryTop + gallery.Right * 1.52f + gallery.Up * 0.82f - gallery.Forward * 0.32f,
            gallery.Rotation, new Vector3(0.3f, 0.05f, 0.2f), false);
        Add(specs, GreatStepSegment, "Great_Step_Amber_Line", InlayBucket,
            GalleryTop - gallery.Forward * 0.62f + gallery.Up * 0.2f,
            gallery.Rotation, new Vector3(2.2f, 0.035f, 0.09f), false);

        var mouth = HistoricServiceMouth();
        Add(specs, HistoricServiceSegment, "Historic_Service_Mouth_Recess", ShadowBucket,
            mouth, gallery.Rotation, new Vector3(1.05f, 1.35f, 0.16f), false);
        Add(specs, HistoricServiceSegment, "Historic_Service_Mouth_West_Frame", LimestoneBucket,
            mouth - gallery.Right * 0.72f, gallery.Rotation, new Vector3(0.3f, 1.7f, 0.44f), true);
        Add(specs, HistoricServiceSegment, "Historic_Service_Mouth_East_Frame", LimestoneBucket,
            mouth + gallery.Right * 0.72f, gallery.Rotation, new Vector3(0.3f, 1.7f, 0.44f), true);
        Add(specs, HistoricServiceSegment, "Historic_Service_Mouth_Lintel", LimestoneBucket,
            mouth + gallery.Up * 0.93f, gallery.Rotation, new Vector3(1.75f, 0.28f, 0.44f), true);
    }

    private static void AddHybridReturn(List<BoxSpec> specs)
    {
        var route = new List<Vector3> { GalleryFoot };
        route.AddRange(HybridReturnPoints());
        route.Add(Branch);
        for (var index = 1; index < route.Count; index++)
        {
            var name = "Service_Return_" + (index - 1).ToString("D2");
            if (index <= 2 || index == route.Count - 1)
                AddOpenConnector(specs, HybridReturnSegment, name, route[index - 1], route[index], 2.75f, HybridBucket);
            else
                AddPassage(specs, HybridReturnSegment, name, route[index - 1], route[index], 2.75f, 2.9f, HybridBucket);
        }
        var frame = Frame(route[1], route[2]);
        for (var rib = 0; rib < 5; rib++)
        {
            var point = Vector3.Lerp(route[1], route[2], (rib + 1f) / 6f);
            AddFrame(specs, HybridReturnSegment, "Service_Return_Rib_" + rib.ToString("D2"), point, frame,
                2.75f, 2.9f, HybridBucket, false);
        }
    }

    private static Vector3 AscendingRejoin()
    {
        return new Vector3(6f, 4.65f, -10.8f);
    }

    private static Vector3 BlockedStubEnd()
    {
        return Vector3.Lerp(Branch, GalleryFoot, 0.36f);
    }

    private static void AddPassage(List<BoxSpec> specs, string segment, string name, Vector3 start, Vector3 end,
        float width, float height, string bucket, bool structural = true, float shellTrimOverride = -1f,
        bool shellCollision = true)
    {
        var frame = Frame(start, end);
        var requestedTrim = shellTrimOverride > 0f ? shellTrimOverride : Mathf.Min(1.1f, frame.Length * 0.22f);
        var shellTrim = Mathf.Min(requestedTrim, frame.Length * 0.42f);
        var shell = Frame(start + frame.Forward * shellTrim, end - frame.Forward * shellTrim);
        Add(specs, segment, name + "_Floor", bucket, frame.Center - frame.Up * 0.1f, frame.Rotation,
            new Vector3(width, 0.2f, frame.Length), structural);
        Add(specs, segment, name + "_West_Wall", bucket,
            shell.Center - shell.Right * (width * 0.5f + 0.2f) + shell.Up * (height * 0.5f),
            shell.Rotation, new Vector3(0.4f, height, shell.Length), structural && shellCollision);
        Add(specs, segment, name + "_East_Wall", bucket,
            shell.Center + shell.Right * (width * 0.5f + 0.2f) + shell.Up * (height * 0.5f),
            shell.Rotation, new Vector3(0.4f, height, shell.Length), structural && shellCollision);
        Add(specs, segment, name + "_Roof", bucket, shell.Center + shell.Up * height,
            shell.Rotation, new Vector3(width + 0.8f, 0.28f, shell.Length), structural && shellCollision);
        Add(specs, segment, name + "_Route_Inlay", InlayBucket, frame.Center + frame.Up * 0.015f,
            frame.Rotation, new Vector3(0.08f, 0.025f, Mathf.Max(0.25f, frame.Length - 0.35f)), false);
    }

    private static void AddOpenConnector(List<BoxSpec> specs, string segment, string name, Vector3 start, Vector3 end,
        float width, string bucket)
    {
        var frame = Frame(start, end);
        Add(specs, segment, name + "_Floor", bucket, frame.Center - frame.Up * 0.1f, frame.Rotation,
            new Vector3(width, 0.2f, frame.Length), true);
        Add(specs, segment, name + "_Route_Inlay", InlayBucket, frame.Center + frame.Up * 0.015f,
            frame.Rotation, new Vector3(0.08f, 0.025f, Mathf.Max(0.25f, frame.Length - 0.35f)), false);
    }

    private static void AddFrame(List<BoxSpec> specs, string segment, string name, Vector3 point, RouteFrame frame,
        float width, float height, string bucket = LimestoneBucket, bool structural = true)
    {
        Add(specs, segment, name + "_West_Post", bucket,
            point - frame.Right * (width * 0.5f + 0.22f) + frame.Up * (height * 0.5f),
            frame.Rotation, new Vector3(0.34f, height, 0.42f), structural);
        Add(specs, segment, name + "_East_Post", bucket,
            point + frame.Right * (width * 0.5f + 0.22f) + frame.Up * (height * 0.5f),
            frame.Rotation, new Vector3(0.34f, height, 0.42f), structural);
        Add(specs, segment, name + "_Lintel", bucket, point + frame.Up * height,
            frame.Rotation, new Vector3(width + 0.9f, 0.34f, 0.42f), structural);
    }

    private static void Add(List<BoxSpec> specs, string segment, string name, string bucket, Vector3 position,
        Quaternion rotation, Vector3 scale, bool structural)
    {
        specs.Add(new BoxSpec(segment, name, bucket, position, rotation, scale, structural, structural));
    }

    private static RouteFrame Frame(Vector3 start, Vector3 end)
    {
        var delta = end - start;
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

        private readonly string name;
        private readonly List<Vector3> vertices = new List<Vector3>();
        private readonly List<Vector3> normals = new List<Vector3>();
        private readonly List<Vector2> uvs = new List<Vector2>();
        private readonly List<int> triangles = new List<int>();

        public BoxMeshBuilder(string meshName)
        {
            name = meshName;
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
            return new Vector2(Mathf.Max(1f, dimensions.x / 2.2f), Mathf.Max(1f, dimensions.y / 2.2f));
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayPyramidReferenceMatchedV4Builder
{
    public const string RootName = "Runtime_Pyramid_Reference_Matched_V4";
    public const float BaseSize = 56f;
    public const float PyramidHeight = BaseSize * 7f / 11f;
    public const float CutTopY = 28.7f;
    public const float CutBaseWidth = 34f;
    public const float CutTopWidth = 0.9f;

    private const string ScenePath = "Assets/_Project/Scenes/School_MVP.unity";
    private const string MapRootName = "TraitorEscape_Runtime_Map";
    private const string MaterialsRoot = "Assets/_Project/Materials";
    private const string MeshesRoot = "Assets/_Project/Art/Generated/PyramidReferenceMatchedV4/Meshes";
    private const string RunRoot = "runs/pyramid-reference-matched-v4";
    private const float HalfBase = BaseSize * 0.5f;
    private const float EnvelopeTolerance = 0.55f;
    private const float FloorLevelTolerance = 0.12f;
    private const float PyramidHeightCubits = 280f;
    private const float QueensFloorCubits = 41f;
    private const float KingsFloorCubits = 82f;

    private static readonly Vector3 Entrance = new Vector3(-3.5f, 5f, -23.3f);
    private static readonly Vector3 Branch = new Vector3(-2.5f, 1.2f, -18.3f);
    private static readonly Vector3 SubterraneanApproach = new Vector3(0f, -3.8f, -5.6f);
    private static readonly Vector3 SubterraneanChamber = new Vector3(1f, -3.6f, 1.5f);
    private static readonly Vector3 GalleryFoot = new Vector3(0f, 5.4f, -7f);
    private static readonly Vector3 QueensChamber = new Vector3(-1.8f, 5.35f, -2.8f);
    private static readonly Vector3 GrandGalleryTop = new Vector3(3.5f, 10.5f, 4.5f);
    private static readonly Vector3 Antechamber = new Vector3(1f, 10.5f, 6.4f);
    private static readonly Vector3 KingsChamber = new Vector3(-2f, 12.45f, 7.5f);

    private static readonly string[] RequiredMarkers =
    {
        "V4_Route_Entrance",
        "V4_Route_Branch",
        "V4_Route_Subterranean_Approach",
        "V4_Route_Subterranean_Chamber",
        "V4_Route_Gallery_Foot",
        "V4_Route_Queens_Chamber",
        "V4_Route_Grand_Gallery_Top",
        "V4_Route_Kings_Chamber",
    };

    [MenuItem("Channel Play/Rebuild Pyramid Reference Matched V4")]
    public static void Rebuild()
    {
        ChannelPlayPyramidTrueFormV3Builder.RebuildPyramidTrueFormV3();
        Directory.CreateDirectory(MeshesRoot);
        CreateV4Materials();

        var scene = EditorSceneManager.OpenScene(ScenePath);
        var mapRoot = GameObject.Find(MapRootName);
        if (mapRoot == null)
        {
            throw new InvalidOperationException("Map root missing after V3 bootstrap.");
        }

        var root = GameObject.Find(ChannelPlayPyramidTrueFormV3Builder.PyramidRootName);
        if (root == null)
        {
            throw new InvalidOperationException("V3 bootstrap root missing.");
        }

        root.name = RootName;
        ClearChildren(root.transform);

        BuildFoundation(root.transform);
        BuildSectionPoche(root.transform);
        BuildCasing(root.transform);
        BuildDenseCore(root.transform);
        BuildInterior(root.transform);
        BuildRouteMarkers(root.transform);
        BuildLighting(root.transform);
        PositionPlayerAndCamera();

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log(
            "CHANNEL_PLAY_PYRAMID_REFERENCE_V4_BUILD result=built" +
            " root=\"" + RootName + "\"" +
            " cut_ratio=" + (CutTopWidth / CutBaseWidth).ToString("F3"));
    }

    [MenuItem("Channel Play/Rebuild Validate Render Pyramid Reference Matched V4")]
    public static void RebuildValidateRender()
    {
        Rebuild();
        Validate();
        ChannelPlayPyramidReferenceMatchedV4ScreenshotExporter.ExportScreenshots();
    }

    [MenuItem("Channel Play/Validate Pyramid Reference Matched V4")]
    public static void Validate()
    {
        EditorSceneManager.OpenScene(ScenePath);
        var result = ValidateScene();
        WriteReceipt(result);
        if (!result.Passed)
        {
            Debug.LogError(
                "CHANNEL_PLAY_PYRAMID_REFERENCE_V4 result=failed reason=\"" +
                string.Join("; ", result.Failures) + "\"");
            if (Application.isBatchMode)
            {
                EditorApplication.Exit(1);
            }

            return;
        }

        Debug.Log(
            "CHANNEL_PLAY_PYRAMID_REFERENCE_V4 result=passed" +
            " core_blocks=" + result.CoreBlocks +
            " casing_panels=" + result.CasingPanels +
            " cut_ratio=" + result.CutRatio.ToString("F3") +
            " corbels=" + result.CorbelBands +
            " relieving=" + result.RelievingChambers +
            " envelope_violations=" + result.EnvelopeViolations.Count);
    }

    public static float EnvelopeHalfWidth(float y)
    {
        if (y <= 0f)
        {
            return HalfBase;
        }

        return HalfBase * Mathf.Clamp01(1f - y / PyramidHeight);
    }

    private static void BuildFoundation(Transform root)
    {
        var foundation = ChildRoot(root, "V4_Foundation_Bedrock_Cutaway");
        var desert = Mat("PyramidV3_Desert");
        var bedrock = Mat("PyramidV3_Subterranean_Rock");
        var platform = Mat("PyramidV3_Platform");

        Cube("V4_Desert_Horizon", foundation, new Vector3(0f, -7.9f, 8f), new Vector3(220f, 0.5f, 220f), desert);

        Cube("V4_Bedrock_Left", foundation, new Vector3(-19.5f, -3.75f, 0f), new Vector3(33f, 7.5f, 72f), bedrock);
        Cube("V4_Bedrock_Right", foundation, new Vector3(19.5f, -3.75f, 0f), new Vector3(33f, 7.5f, 72f), bedrock);
        Cube("V4_Bedrock_Center_Rear", foundation, new Vector3(1f, -3.75f, 22f), new Vector3(10f, 7.5f, 28f), bedrock);

        Cube("V4_Platform_Left", foundation, new Vector3(-19.5f, 0.08f, 0f), new Vector3(33f, 0.26f, 72f), platform);
        Cube("V4_Platform_Right", foundation, new Vector3(19.5f, 0.08f, 0f), new Vector3(33f, 0.26f, 72f), platform);
        Cube("V4_Platform_Center_Rear", foundation, new Vector3(1f, 0.08f, 22f), new Vector3(10f, 0.26f, 28f), platform);

        Cube("V4_Trench_West_Cut_Line", foundation, new Vector3(-3.15f, -3.75f, -12f), new Vector3(0.3f, 7.5f, 40f), Mat("PyramidV3_Dark_Granite"), Quaternion.identity, false);
        Cube("V4_Trench_East_Cut_Line", foundation, new Vector3(3.15f, -3.75f, -12f), new Vector3(0.3f, 7.5f, 40f), Mat("PyramidV3_Dark_Granite"), Quaternion.identity, false);

        var lowerPortal = ChildRoot(foundation, "V4_Gameplay_Lower_Access_Portal");
        Cube("V4_Gameplay_Portal_West_Jamb", lowerPortal, new Vector3(-2.65f, -5.35f, -36.15f), new Vector3(0.55f, 3.2f, 0.7f), platform);
        Cube("V4_Gameplay_Portal_East_Jamb", lowerPortal, new Vector3(2.65f, -5.35f, -36.15f), new Vector3(0.55f, 3.2f, 0.7f), platform);
        Cube("V4_Gameplay_Portal_Lintel", lowerPortal, new Vector3(0f, -3.75f, -36.15f), new Vector3(5.85f, 0.55f, 0.7f), platform);
        Cube("V4_Gameplay_Portal_Shadow", lowerPortal, new Vector3(0f, -5.35f, -35.8f), new Vector3(4.8f, 2.65f, 0.2f), Mat("PyramidV3_Interior_Shadow"), Quaternion.identity, false);
        for (var step = 0; step < 5; step++)
        {
            Cube(
                "V4_Gameplay_Portal_Step_" + step.ToString("D2"),
                lowerPortal,
                new Vector3(0f, -7.45f + step * 0.48f, -38.2f + step * 0.62f),
                new Vector3(4.2f, 0.34f, 0.82f),
                platform);
        }

        var approach = ChildRoot(foundation, "V4_Entrance_Approach");
        for (var step = 0; step < 8; step++)
        {
            var t = step / 7f;
            Cube(
                "V4_Approach_Step_" + step.ToString("D2"),
                approach,
                new Vector3(Entrance.x, 0.22f + t * 4.45f, -30f + t * 6.2f),
                new Vector3(2.65f, 0.38f, 0.95f),
                platform);
        }
    }

    private static void BuildSectionPoche(Transform root)
    {
        var section = ChildRoot(root, "V4_Section_Poche");
        var topHalf = EnvelopeHalfWidth(CutTopY);
        var vertices = new[]
        {
            new Vector3(-CutBaseWidth * 0.5f, 0f, HalfBase - 1.5f),
            new Vector3(CutBaseWidth * 0.5f, 0f, HalfBase - 1.5f),
            new Vector3(CutTopWidth * 0.5f, CutTopY, topHalf - 1f),
            new Vector3(-CutTopWidth * 0.5f, CutTopY, topHalf - 1f),
        };
        var mesh = SaveDoubleSidedMesh(
            "PyramidV4_Section_Poche_Mesh",
            vertices,
            new[] { 0, 1, 2, 0, 2, 3 },
            QuadUvs());
        MeshObject("V4_Section_Poche_Filled_Mass", section, mesh, Mat("PyramidV4_Section_Mass"), false);

        CreateBeam(
            "V4_Cut_Profile_West",
            section,
            new Vector3(-CutBaseWidth * 0.5f, 0f, -HalfBase + 0.2f),
            new Vector3(-CutTopWidth * 0.5f, CutTopY, -topHalf + 0.2f),
            0.48f,
            Mat("PyramidV3_Dark_Granite"),
            false);
        CreateBeam(
            "V4_Cut_Profile_East",
            section,
            new Vector3(CutBaseWidth * 0.5f, 0f, -HalfBase + 0.2f),
            new Vector3(CutTopWidth * 0.5f, CutTopY, -topHalf + 0.2f),
            0.48f,
            Mat("PyramidV3_Dark_Granite"),
            false);
    }

    private static void BuildCasing(Transform root)
    {
        var casing = ChildRoot(root, "V4_Smooth_Casing_With_Tapered_Cutaway");
        var material = Mat("PyramidV4_Tura_Casing");
        var apex = new Vector3(0f, PyramidHeight, 0f);
        var topHalf = EnvelopeHalfWidth(CutTopY);
        var northZ = -HalfBase;
        var topZ = -topHalf;

        MeshObject(
            "V4_Casing_East_Full_Face",
            casing,
            TriangleAsset("PyramidV4_Casing_East", new Vector3(HalfBase, 0f, northZ), new Vector3(HalfBase, 0f, HalfBase), apex),
            material,
            true);
        MeshObject(
            "V4_Casing_West_Full_Face",
            casing,
            TriangleAsset("PyramidV4_Casing_West", new Vector3(-HalfBase, 0f, HalfBase), new Vector3(-HalfBase, 0f, northZ), apex),
            material,
            true);
        MeshObject(
            "V4_Casing_South_Full_Face",
            casing,
            TriangleAsset("PyramidV4_Casing_South", new Vector3(HalfBase, 0f, HalfBase), new Vector3(-HalfBase, 0f, HalfBase), apex),
            material,
            true);

        var leftVertices = new[]
        {
            new Vector3(-HalfBase, 0f, northZ),
            new Vector3(-CutBaseWidth * 0.5f, 0f, northZ),
            new Vector3(-CutTopWidth * 0.5f, CutTopY, topZ),
            new Vector3(-topHalf, CutTopY, topZ),
        };
        MeshObject(
            "V4_Casing_North_Left_Panel",
            casing,
            SaveDoubleSidedMesh("PyramidV4_Casing_North_Left", leftVertices, new[] { 0, 1, 2, 0, 2, 3 }, QuadUvs()),
            material,
            true);

        var rightVertices = new[]
        {
            new Vector3(CutBaseWidth * 0.5f, 0f, northZ),
            new Vector3(HalfBase, 0f, northZ),
            new Vector3(topHalf, CutTopY, topZ),
            new Vector3(CutTopWidth * 0.5f, CutTopY, topZ),
        };
        MeshObject(
            "V4_Casing_North_Right_Panel",
            casing,
            SaveDoubleSidedMesh("PyramidV4_Casing_North_Right", rightVertices, new[] { 0, 1, 2, 0, 2, 3 }, QuadUvs()),
            material,
            true);
        MeshObject(
            "V4_Casing_North_Upper_Cap",
            casing,
            TriangleAsset(
                "PyramidV4_Casing_North_Upper",
                new Vector3(-topHalf, CutTopY, topZ),
                new Vector3(topHalf, CutTopY, topZ),
                apex),
            material,
            true);

        CreateBeam(
            "V4_Casing_Cut_Trim_Left",
            casing,
            new Vector3(-CutBaseWidth * 0.5f, 0f, northZ - 0.04f),
            new Vector3(-CutTopWidth * 0.5f, CutTopY, topZ - 0.04f),
            0.38f,
            Mat("PyramidV4_Casing_Trim"),
            false);
        CreateBeam(
            "V4_Casing_Cut_Trim_Right",
            casing,
            new Vector3(CutBaseWidth * 0.5f, 0f, northZ - 0.04f),
            new Vector3(CutTopWidth * 0.5f, CutTopY, topZ - 0.04f),
            0.38f,
            Mat("PyramidV4_Casing_Trim"),
            false);
    }

    private static void BuildDenseCore(Transform root)
    {
        var core = ChildRoot(root, "V4_Dense_Exposed_Core_Masonry");
        const int courses = 42;
        const float blockWidth = 1.05f;
        var courseHeight = CutTopY / courses;

        for (var course = 0; course < courses; course++)
        {
            var y = (course + 0.5f) * courseHeight;
            var t = y / CutTopY;
            var left = Mathf.Lerp(-CutBaseWidth * 0.5f + 0.18f, -CutTopWidth * 0.5f + 0.08f, t);
            var right = Mathf.Lerp(-4.8f, -0.08f, t * t);
            var span = Mathf.Max(0.35f, right - left);
            var count = Mathf.Max(1, Mathf.FloorToInt(span / blockWidth) + (course % 2));
            var actualWidth = span / count;
            var frontZ = -EnvelopeHalfWidth(y) + 0.4f;

            for (var block = 0; block < count; block++)
            {
                var x = left + actualWidth * (block + 0.5f);
                var material = Mat((course + block) % 4 == 0
                    ? "PyramidV4_Core_Shadow"
                    : "PyramidV4_Core_Limestone");
                Cube(
                    "V4_Core_Block_C" + course.ToString("D2") + "_B" + block.ToString("D2"),
                    core,
                    new Vector3(x, y, frontZ),
                    new Vector3(actualWidth * 0.96f, courseHeight * 0.94f, 0.74f),
                    material);
            }
        }
    }

    private static void BuildInterior(Transform root)
    {
        var interior = ChildRoot(root, "V4_Embedded_Interior_Architecture");

        BuildEnclosedPassage(interior, "V4_Descending_Upper", Entrance, Branch, 2.35f, 2.3f);
        BuildEnclosedPassage(interior, "V4_Descending_Bedrock", Branch, SubterraneanApproach, 2.35f, 2.3f);
        BuildEnclosedPassage(interior, "V4_Subterranean_Level", SubterraneanApproach, new Vector3(1f, -3.6f, -1.6f), 2.35f, 2.3f);
        BuildEnclosedPassage(interior, "V4_Ascending_Passage", Branch, GalleryFoot, 2.45f, 2.45f);
        BuildEnclosedPassage(interior, "V4_Queens_Horizontal", GalleryFoot, QueensChamber + new Vector3(1.1f, 0f, -1f), 2.35f, 2.35f);

        BuildSubterraneanChamber(interior);
        BuildQueensChamber(interior);
        BuildGrandGallery(interior);
        BuildKingsSuite(interior);
        BuildEntrancePortal(interior);
    }

    private static void BuildSubterraneanChamber(Transform parent)
    {
        var room = ChildRoot(parent, "V4_Subterranean_Chamber");
        var rock = Mat("PyramidV3_Subterranean_Rock");
        Cube("V4_Subterranean_Floor", room, new Vector3(1f, -4.15f, 1.5f), new Vector3(8f, 0.28f, 6.8f), rock);
        Cube("V4_Subterranean_Back", room, new Vector3(1f, -2.25f, 4.9f), new Vector3(8f, 3.8f, 0.38f), rock);
        Cube("V4_Subterranean_West", room, new Vector3(-3f, -2.25f, 1.5f), new Vector3(0.38f, 3.8f, 6.8f), rock);
        Cube("V4_Subterranean_East", room, new Vector3(5f, -2.25f, 1.5f), new Vector3(0.38f, 3.8f, 6.8f), rock);
        Cube("V4_Subterranean_Unfinished_Pit", room, new Vector3(2.6f, -4.75f, 2.2f), new Vector3(2.2f, 1f, 2.1f), Mat("PyramidV3_Interior_Shadow"), Quaternion.identity, false);
    }

    private static void BuildQueensChamber(Transform parent)
    {
        var room = ChildRoot(parent, "V4_Queens_Chamber");
        var wall = Mat("PyramidV4_Interior_Limestone");
        var center = QueensChamber;
        var floorY = center.y - 0.15f;
        var wallY = floorY + 1.7f;
        var roofY = floorY + 3.55f;
        Cube("V4_Queens_Floor", room, new Vector3(center.x, floorY, center.z), new Vector3(5.2f, 0.26f, 4.4f), wall);
        Cube("V4_Queens_Back", room, new Vector3(center.x, wallY, center.z + 2.2f), new Vector3(5.2f, 3.4f, 0.36f), wall);
        Cube("V4_Queens_East", room, new Vector3(center.x + 2.6f, wallY, center.z), new Vector3(0.36f, 3.4f, 4.4f), wall);
        Cube("V4_Queens_West", room, new Vector3(center.x - 2.6f, wallY, center.z), new Vector3(0.36f, 3.4f, 4.4f), wall);
        Cube("V4_Queens_Roof_East", room, new Vector3(center.x + 1.25f, roofY, center.z), new Vector3(2.9f, 0.28f, 4.5f), wall, Quaternion.Euler(0f, 0f, -29f));
        Cube("V4_Queens_Roof_West", room, new Vector3(center.x - 1.25f, roofY, center.z), new Vector3(2.9f, 0.28f, 4.5f), wall, Quaternion.Euler(0f, 0f, 29f));
    }

    private static void BuildGrandGallery(Transform parent)
    {
        var gallery = ChildRoot(parent, "V4_Grand_Gallery_Corbelled");
        var direction = GrandGalleryTop - GalleryFoot;
        var length = direction.magnitude;
        var rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        var midpoint = (GalleryFoot + GrandGalleryTop) * 0.5f;
        var localUp = rotation * Vector3.up;
        var localRight = rotation * Vector3.right;
        var wall = Mat("PyramidV4_Interior_Limestone");

        Cube("V4_Grand_Floor_Ramp", gallery, midpoint, new Vector3(3.5f, 0.25f, length), Mat("PyramidV3_Passage_Floor"), rotation);
        Cube("V4_Grand_Center_Trench", gallery, midpoint + localUp * 0.14f, new Vector3(0.82f, 0.16f, length), Mat("PyramidV3_Interior_Shadow"), rotation, false);

        for (var step = 0; step < 12; step++)
        {
            var t = (step + 0.5f) / 12f;
            var point = Vector3.Lerp(GalleryFoot, GrandGalleryTop, t);
            Cube(
                "V4_Grand_Stair_" + step.ToString("D2"),
                gallery,
                point + Vector3.up * 0.08f,
                new Vector3(3.2f, 0.22f, 1.35f),
                wall,
                Quaternion.identity);
        }

        for (var band = 0; band < 7; band++)
        {
            var x = 1.85f - band * 0.16f;
            var y = 0.45f + band * 0.38f;
            Cube(
                "V4_Grand_Corbel_West_" + band.ToString("D2"),
                gallery,
                midpoint - localRight * x + localUp * y,
                new Vector3(0.32f, 0.34f, length),
                wall,
                rotation);
            Cube(
                "V4_Grand_Corbel_East_" + band.ToString("D2"),
                gallery,
                midpoint + localRight * x + localUp * y,
                new Vector3(0.32f, 0.34f, length),
                wall,
                rotation);
        }
        Cube("V4_Grand_Ceiling", gallery, midpoint + localUp * 3.2f, new Vector3(1.45f, 0.28f, length), wall, rotation);
    }

    private static void BuildKingsSuite(Transform parent)
    {
        var suite = ChildRoot(parent, "V4_Kings_Embedded_Suite");
        var granite = Mat("PyramidV3_Red_Granite");
        var dark = Mat("PyramidV3_Dark_Granite");
        var limestone = Mat("PyramidV4_Interior_Limestone");
        var roomCenter = KingsChamber;
        var roomEntry = Antechamber;

        BuildEnclosedPassage(suite, "V4_Antechamber_Passage", GrandGalleryTop, roomEntry, 2.2f, 2.3f);
        var gateDirection = (roomEntry - GrandGalleryTop).normalized;
        var gateRotation = Quaternion.LookRotation(gateDirection, Vector3.up);
        for (var gate = 0; gate < 3; gate++)
        {
            var t = (gate + 1f) / 4f;
            var gatePosition = Vector3.Lerp(GrandGalleryTop, roomEntry, t) + Vector3.up * 1.05f;
            Cube(
                "V4_Portcullis_" + gate.ToString("D2"),
                suite,
                gatePosition,
                new Vector3(2.35f, 2.45f, 0.18f),
                granite,
                gateRotation);
        }

        var room = ChildRoot(suite, "V4_Kings_Chamber");
        Cube("V4_Kings_Floor", room, new Vector3(roomCenter.x, roomCenter.y - 1.95f, roomCenter.z), new Vector3(6f, 0.3f, 3f), granite);
        Cube("V4_Kings_Back", room, new Vector3(roomCenter.x, roomCenter.y - 0.1f, roomCenter.z + 1.5f), new Vector3(6f, 3.7f, 0.38f), granite);
        Cube("V4_Kings_West", room, new Vector3(roomCenter.x - 3f, roomCenter.y - 0.1f, roomCenter.z), new Vector3(0.38f, 3.7f, 3f), granite);
        Cube("V4_Kings_East", room, new Vector3(roomCenter.x + 3f, roomCenter.y - 0.1f, roomCenter.z), new Vector3(0.38f, 3.7f, 3f), granite);
        Cube("V4_Kings_Ceiling", room, new Vector3(roomCenter.x, roomCenter.y + 1.75f, roomCenter.z), new Vector3(6.2f, 0.38f, 3.1f), granite);
        Cube("V4_Kings_Sarcophagus", room, roomCenter + new Vector3(1.15f, -1.42f, -0.05f), new Vector3(2.3f, 0.82f, 1.05f), dark);

        var relieving = ChildRoot(suite, "V4_Relieving_System");
        for (var chamber = 0; chamber < 5; chamber++)
        {
            var chamberRoot = ChildRoot(relieving, "V4_Relieving_Chamber_" + chamber.ToString("D2"));
            var y = roomCenter.y + 2.3f + chamber * 0.78f;
            Cube("Floor", chamberRoot, new Vector3(roomCenter.x, y, roomCenter.z), new Vector3(6.1f, 0.24f, 2.8f), chamber % 2 == 0 ? granite : dark);
            Cube("WestPier", chamberRoot, new Vector3(roomCenter.x - 3f, y + 0.34f, roomCenter.z), new Vector3(0.25f, 0.82f, 2.8f), dark);
            Cube("EastPier", chamberRoot, new Vector3(roomCenter.x + 3f, y + 0.34f, roomCenter.z), new Vector3(0.25f, 0.82f, 2.8f), dark);
            Cube("Back", chamberRoot, new Vector3(roomCenter.x, y + 0.34f, roomCenter.z + 1.35f), new Vector3(6.1f, 0.82f, 0.22f), dark, Quaternion.identity, false);
        }
        var gableY = roomCenter.y + 6.1f;
        Cube("V4_Relieving_Gable_West", relieving, new Vector3(roomCenter.x - 1.35f, gableY, roomCenter.z - 0.2f), new Vector3(3.15f, 0.28f, 2.2f), limestone, Quaternion.Euler(0f, 0f, 31f));
        Cube("V4_Relieving_Gable_East", relieving, new Vector3(roomCenter.x + 1.35f, gableY, roomCenter.z - 0.2f), new Vector3(3.15f, 0.28f, 2.2f), limestone, Quaternion.Euler(0f, 0f, -31f));
    }

    private static void BuildEntrancePortal(Transform parent)
    {
        var portal = ChildRoot(parent, "V4_Entrance_Portal");
        var stone = Mat("PyramidV4_Casing_Trim");
        Cube("V4_Entrance_West_Jamb", portal, Entrance + new Vector3(-1.35f, 0.15f, -0.2f), new Vector3(0.45f, 2.8f, 0.7f), stone);
        Cube("V4_Entrance_East_Jamb", portal, Entrance + new Vector3(1.35f, 0.15f, -0.2f), new Vector3(0.45f, 2.8f, 0.7f), stone);
        Cube("V4_Entrance_Lintel", portal, Entrance + new Vector3(0f, 1.58f, -0.2f), new Vector3(3.15f, 0.45f, 0.72f), stone);
        Cube("V4_Entrance_Shadow", portal, Entrance + new Vector3(0f, 0f, 0.2f), new Vector3(2.2f, 2.25f, 0.24f), Mat("PyramidV3_Interior_Shadow"), Quaternion.identity, false);
    }

    private static void BuildGameAdaptationNiche(Transform parent)
    {
        var niche = ChildRoot(parent, "V4_Gameplay_Junction_Niche");
        var stone = Mat("PyramidV4_Interior_Limestone");
        Cube("V4_Niche_Floor", niche, new Vector3(-5.6f, 7.65f, -7.2f), new Vector3(3.2f, 0.24f, 2.8f), stone);
        Cube("V4_Niche_West", niche, new Vector3(-7.2f, 8.8f, -7.2f), new Vector3(0.3f, 2.3f, 2.8f), stone);
        Cube("V4_Niche_East", niche, new Vector3(-4f, 8.8f, -7.2f), new Vector3(0.3f, 2.3f, 2.8f), stone);
        Cube("V4_Niche_Roof_West", niche, new Vector3(-6.3f, 10.15f, -7.2f), new Vector3(2f, 0.24f, 2.9f), stone, Quaternion.Euler(0f, 0f, 31f));
        Cube("V4_Niche_Roof_East", niche, new Vector3(-4.9f, 10.15f, -7.2f), new Vector3(2f, 0.24f, 2.9f), stone, Quaternion.Euler(0f, 0f, -31f));
    }

    private static void BuildRouteMarkers(Transform root)
    {
        var route = ChildRoot(root, "V4_Gameplay_Route");
        Marker(route, RequiredMarkers[0], Entrance);
        Marker(route, RequiredMarkers[1], Branch);
        Marker(route, RequiredMarkers[2], SubterraneanApproach);
        Marker(route, RequiredMarkers[3], SubterraneanChamber);
        Marker(route, RequiredMarkers[4], GalleryFoot);
        Marker(route, RequiredMarkers[5], QueensChamber);
        Marker(route, RequiredMarkers[6], GrandGalleryTop);
        Marker(route, RequiredMarkers[7], KingsChamber);

        var glow = Mat("PyramidV3_Route_Glow");
        var routeDisplayOffset = Vector3.up * 0.22f + Vector3.back * 3f;
        CreateBeam("V4_Glow_Entrance", route, Entrance + routeDisplayOffset, Branch + routeDisplayOffset, 0.14f, glow, false);
        CreateBeam("V4_Glow_Descending", route, Branch + routeDisplayOffset, SubterraneanApproach + routeDisplayOffset, 0.14f, glow, false);
        CreateBeam("V4_Glow_Subterranean", route, SubterraneanApproach + routeDisplayOffset, SubterraneanChamber + routeDisplayOffset, 0.14f, glow, false);
        CreateBeam("V4_Glow_Ascending", route, Branch + routeDisplayOffset, GalleryFoot + routeDisplayOffset, 0.14f, glow, false);
        CreateBeam("V4_Glow_Queens", route, GalleryFoot + routeDisplayOffset, QueensChamber + routeDisplayOffset, 0.14f, glow, false);
        CreateBeam("V4_Glow_Grand", route, GalleryFoot + routeDisplayOffset, GrandGalleryTop + routeDisplayOffset, 0.14f, glow, false);
        CreateBeam("V4_Glow_Kings", route, GrandGalleryTop + routeDisplayOffset, KingsChamber + routeDisplayOffset, 0.14f, glow, false);
    }

    private static void BuildLighting(Transform root)
    {
        var lighting = ChildRoot(root, "V4_Lighting");
        var sunObject = new GameObject("V4_Desert_Sun");
        sunObject.transform.SetParent(lighting, false);
        sunObject.transform.rotation = Quaternion.Euler(38f, -42f, 0f);
        var sun = sunObject.AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(1f, 0.96f, 0.88f);
        sun.intensity = 0.82f;
        sun.shadows = LightShadows.Soft;

        PointLight(lighting, "V4_Light_Subterranean", new Vector3(1f, -2.4f, 1.5f), new Color(0.18f, 0.72f, 0.66f), 4.8f, 9f);
        PointLight(lighting, "V4_Light_Queens", QueensChamber + Vector3.up * 1.7f, new Color(0.28f, 0.72f, 0.66f), 2.3f, 7f);
        PointLight(lighting, "V4_Light_Grand", Vector3.Lerp(GalleryFoot, GrandGalleryTop, 0.58f) + Vector3.up * 2f, new Color(0.95f, 0.55f, 0.22f), 4.6f, 11f);
        PointLight(lighting, "V4_Light_Kings", KingsChamber, new Color(0.82f, 0.25f, 0.16f), 4.2f, 8f);

        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.24f, 0.23f, 0.21f);
    }

    private static void BuildEnclosedPassage(Transform parent, string name, Vector3 start, Vector3 end, float width, float height)
    {
        var direction = end - start;
        var length = direction.magnitude;
        var rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        var midpoint = (start + end) * 0.5f;
        var up = rotation * Vector3.up;
        var right = rotation * Vector3.right;
        var wall = Mat("PyramidV4_Interior_Limestone");

        Cube(name + "_Floor", parent, midpoint, new Vector3(width, 0.22f, length), Mat("PyramidV3_Passage_Floor"), rotation);
        Cube(name + "_West", parent, midpoint - right * (width * 0.5f + 0.18f) + up * (height * 0.5f), new Vector3(0.36f, height, length), wall, rotation);
        Cube(name + "_East", parent, midpoint + right * (width * 0.5f + 0.18f) + up * (height * 0.5f), new Vector3(0.36f, height, length), wall, rotation);
        Cube(name + "_Roof", parent, midpoint + up * height, new Vector3(width + 0.72f, 0.24f, length), wall, rotation);
    }

    private static void PositionPlayerAndCamera()
    {
        var player = GameObject.Find("MVP_Player");
        if (player != null)
        {
            player.transform.position = new Vector3(-3.5f, 1.05f, -33f);
            player.transform.rotation = Quaternion.identity;
        }

        var cameraObject = GameObject.Find("Gameplay_Camera") ?? GameObject.Find("Main_Camera");
        if (cameraObject != null)
        {
            cameraObject.transform.position = new Vector3(-3.5f, 5.8f, -34f);
            cameraObject.transform.LookAt(Entrance + Vector3.up * 0.25f);
            var camera = cameraObject.GetComponent<Camera>();
            if (camera != null)
            {
                camera.fieldOfView = 42f;
                camera.farClipPlane = 500f;
            }
        }
    }

    private static ValidationResult ValidateScene()
    {
        var result = new ValidationResult
        {
            ReceiptPath = Path.Combine(RunRoot, "validation-receipt.md").Replace('\\', '/'),
            CutRatio = CutTopWidth / CutBaseWidth,
        };
        var rootObject = GameObject.Find(RootName);
        if (rootObject == null)
        {
            result.Failures.Add("V4 root missing");
            return result;
        }

        var transforms = rootObject.GetComponentsInChildren<Transform>(true);
        result.CoreBlocks = transforms.Count(item => item.name.StartsWith("V4_Core_Block_", StringComparison.Ordinal));
        result.CasingPanels = transforms.Count(item => item.name.StartsWith("V4_Casing_", StringComparison.Ordinal) && item.GetComponent<MeshRenderer>() != null);
        result.RouteMarkers = RequiredMarkers.Count(name => transforms.Any(item => item.name == name));
        result.CorbelBands = transforms.Count(item => item.name.StartsWith("V4_Grand_Corbel_", StringComparison.Ordinal));
        result.RelievingChambers = transforms.Count(item => item.name.StartsWith("V4_Relieving_Chamber_", StringComparison.Ordinal));
        result.FoundationSections = transforms.Count(item => item.name.StartsWith("V4_Bedrock_", StringComparison.Ordinal));
        result.HasFilledSection = transforms.Any(item => item.name == "V4_Section_Poche_Filled_Mass");
        result.QueensFloorTarget = PyramidHeight * QueensFloorCubits / PyramidHeightCubits;
        result.KingsFloorTarget = PyramidHeight * KingsFloorCubits / PyramidHeightCubits;

        var queensFloor = transforms.FirstOrDefault(item => item.name == "V4_Queens_Floor");
        var kingsFloor = transforms.FirstOrDefault(item => item.name == "V4_Kings_Floor");
        if (queensFloor == null || kingsFloor == null)
        {
            result.Failures.Add("researched chamber floor markers missing");
        }
        else
        {
            result.QueensFloorY = rootObject.transform.InverseTransformPoint(queensFloor.position).y;
            result.KingsFloorY = rootObject.transform.InverseTransformPoint(kingsFloor.position).y;
            if (Mathf.Abs(result.QueensFloorY - result.QueensFloorTarget) > FloorLevelTolerance)
            {
                result.Failures.Add("Queen's Chamber floor level drifted from 41/280 height ratio");
            }
            if (Mathf.Abs(result.KingsFloorY - result.KingsFloorTarget) > FloorLevelTolerance)
            {
                result.Failures.Add("King's Chamber floor level drifted from 82/280 height ratio");
            }
        }

        if (result.CutRatio > 0.3f)
        {
            result.Failures.Add("cutaway is not tapered enough");
        }
        if (result.CoreBlocks < 160)
        {
            result.Failures.Add("dense core requires at least 160 blocks");
        }
        if (result.CasingPanels < 6)
        {
            result.Failures.Add("casing context is incomplete");
        }
        if (!result.HasFilledSection)
        {
            result.Failures.Add("filled section poche missing");
        }
        if (result.RouteMarkers != RequiredMarkers.Length)
        {
            result.Failures.Add("route markers missing");
        }
        if (result.CorbelBands != 14)
        {
            result.Failures.Add("Grand Gallery must have seven corbels per side");
        }
        if (result.RelievingChambers != 5)
        {
            result.Failures.Add("five bounded relieving chambers required");
        }
        if (result.FoundationSections < 3 || SubterraneanChamber.y >= 0f)
        {
            result.Failures.Add("bedrock/subterranean cutaway incomplete");
        }

        ValidateRouteEnvelope(result);
        ValidateInteriorEnvelope(rootObject.transform, result);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static void ValidateRouteEnvelope(ValidationResult result)
    {
        var points = new[] { Branch, GalleryFoot, QueensChamber, GrandGalleryTop, Antechamber, KingsChamber };
        foreach (var point in points)
        {
            var allowed = EnvelopeHalfWidth(point.y) + EnvelopeTolerance;
            if (Mathf.Abs(point.x) > allowed || Mathf.Abs(point.z) > allowed || point.y > PyramidHeight)
            {
                result.Failures.Add("route point outside pyramid envelope: " + point);
            }
        }
    }

    private static void ValidateInteriorEnvelope(Transform root, ValidationResult result)
    {
        var interior = FindDescendant(root, "V4_Embedded_Interior_Architecture");
        if (interior == null)
        {
            result.Failures.Add("embedded interior root missing");
            return;
        }

        var violations = new HashSet<string>();
        foreach (var renderer in interior.GetComponentsInChildren<Renderer>(true))
        {
            if (renderer.gameObject.name.StartsWith("V4_Entrance_", StringComparison.Ordinal) ||
                renderer.gameObject.name.StartsWith("V4_Descending_Upper_", StringComparison.Ordinal))
            {
                continue;
            }

            var filter = renderer.GetComponent<MeshFilter>();
            if (filter == null || filter.sharedMesh == null)
            {
                continue;
            }

            foreach (var vertex in filter.sharedMesh.vertices)
            {
                var local = root.InverseTransformPoint(renderer.transform.TransformPoint(vertex));
                if (local.y < 0f)
                {
                    if (Mathf.Abs(local.x) > HalfBase + EnvelopeTolerance || Mathf.Abs(local.z) > HalfBase + EnvelopeTolerance)
                    {
                        violations.Add(renderer.gameObject.name);
                    }
                    continue;
                }

                var allowed = EnvelopeHalfWidth(local.y) + EnvelopeTolerance;
                if (Mathf.Abs(local.x) > allowed || Mathf.Abs(local.z) > allowed || local.y > PyramidHeight + EnvelopeTolerance)
                {
                    violations.Add(renderer.gameObject.name);
                }
            }
        }

        result.EnvelopeViolations = violations.OrderBy(name => name).ToList();
        if (result.EnvelopeViolations.Count > 0)
        {
            result.Failures.Add("interior envelope violations: " + string.Join(", ", result.EnvelopeViolations.Take(8)));
        }
    }

    private static void WriteReceipt(ValidationResult result)
    {
        Directory.CreateDirectory(RunRoot);
        var text = new StringBuilder();
        text.AppendLine("# Pyramid Reference-matched V4 Validation Receipt");
        text.AppendLine();
        text.AppendLine("Date: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
        text.AppendLine("Status: `" + (result.Passed ? "passed" : "failed") + "`");
        text.AppendLine();
        text.AppendLine("- Cutaway top/base ratio: `" + result.CutRatio.ToString("F3") + "`");
        text.AppendLine("- Dense core blocks: `" + result.CoreBlocks + "`");
        text.AppendLine("- Casing panels/faces: `" + result.CasingPanels + "`");
        text.AppendLine("- Filled section poche: `" + result.HasFilledSection + "`");
        text.AppendLine("- Route markers: `" + result.RouteMarkers + "`");
        text.AppendLine("- Corbel bands: `" + result.CorbelBands + "`");
        text.AppendLine("- Relieving chambers: `" + result.RelievingChambers + "`");
        text.AppendLine("- Foundation sections: `" + result.FoundationSections + "`");
        text.AppendLine("- Queen's floor actual/target: `" + result.QueensFloorY.ToString("F3") + " / " + result.QueensFloorTarget.ToString("F3") + " m`");
        text.AppendLine("- King's floor actual/target: `" + result.KingsFloorY.ToString("F3") + " / " + result.KingsFloorTarget.ToString("F3") + " m`");
        text.AppendLine("- Envelope violations: `" + result.EnvelopeViolations.Count + "`");
        if (result.Failures.Count > 0)
        {
            text.AppendLine();
            text.AppendLine("## Failures");
            foreach (var failure in result.Failures)
            {
                text.AppendLine("- " + failure);
            }
        }
        File.WriteAllText(result.ReceiptPath, text.ToString());
    }

    private static Transform ChildRoot(Transform parent, string name)
    {
        var child = new GameObject(name);
        child.transform.SetParent(parent, false);
        return child.transform;
    }

    private static void ClearChildren(Transform parent)
    {
        for (var index = parent.childCount - 1; index >= 0; index--)
        {
            UnityEngine.Object.DestroyImmediate(parent.GetChild(index).gameObject);
        }
    }

    private static Transform FindDescendant(Transform parent, string name)
    {
        return parent.GetComponentsInChildren<Transform>(true).FirstOrDefault(child => child.name == name);
    }

    private static GameObject Cube(
        string name,
        Transform parent,
        Vector3 position,
        Vector3 scale,
        Material material,
        Quaternion? rotation = null,
        bool collider = true)
    {
        var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube.name = name;
        cube.transform.SetParent(parent, false);
        cube.transform.localPosition = position;
        cube.transform.localRotation = rotation ?? Quaternion.identity;
        cube.transform.localScale = scale;
        cube.GetComponent<Renderer>().sharedMaterial = material;
        if (!collider)
        {
            var existingCollider = cube.GetComponent<Collider>();
            if (existingCollider != null)
            {
                UnityEngine.Object.DestroyImmediate(existingCollider);
            }
        }
        return cube;
    }

    private static void Marker(Transform parent, string name, Vector3 position)
    {
        var marker = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        marker.name = name;
        marker.transform.SetParent(parent, false);
        marker.transform.localPosition = position;
        marker.transform.localScale = Vector3.one * 0.34f;
        marker.GetComponent<Renderer>().sharedMaterial = Mat("PyramidV3_Route_Glow");
        UnityEngine.Object.DestroyImmediate(marker.GetComponent<Collider>());
    }

    private static void CreateBeam(string name, Transform parent, Vector3 start, Vector3 end, float width, Material material, bool collider)
    {
        var direction = end - start;
        Cube(
            name,
            parent,
            (start + end) * 0.5f,
            new Vector3(width, width, direction.magnitude),
            material,
            Quaternion.LookRotation(direction.normalized, Vector3.up),
            collider);
    }

    private static void PointLight(Transform parent, string name, Vector3 position, Color color, float intensity, float range)
    {
        var lightObject = new GameObject(name);
        lightObject.transform.SetParent(parent, false);
        lightObject.transform.localPosition = position;
        var light = lightObject.AddComponent<Light>();
        light.type = LightType.Point;
        light.color = color;
        light.intensity = intensity;
        light.range = range;
        light.shadows = LightShadows.Soft;
    }

    private static Material Mat(string name)
    {
        var material = AssetDatabase.LoadAssetAtPath<Material>(MaterialsRoot + "/" + name + ".mat");
        if (material == null)
        {
            throw new InvalidOperationException("Missing material: " + name);
        }
        return material;
    }

    private static void CreateV4Materials()
    {
        CloneMaterial("PyramidV3_Tura_Casing", "PyramidV4_Tura_Casing", Color.white);
        CloneMaterial("PyramidV3_Casing_Trim", "PyramidV4_Casing_Trim", new Color(0.72f, 0.68f, 0.58f));
        CloneMaterial("PyramidV3_Core_Limestone", "PyramidV4_Core_Limestone", new Color(0.49f, 0.39f, 0.27f));
        CloneMaterial("PyramidV3_Core_Shadow", "PyramidV4_Core_Shadow", new Color(0.34f, 0.29f, 0.23f));
        CloneMaterial("PyramidV3_Interior_Limestone", "PyramidV4_Interior_Limestone", new Color(0.38f, 0.37f, 0.34f));
        CreateUnlitMaterial("PyramidV4_Section_Mass", new Color(0.18f, 0.18f, 0.17f));
    }

    private static void CloneMaterial(string sourceName, string targetName, Color color)
    {
        var source = Mat(sourceName);
        var path = MaterialsRoot + "/" + targetName + ".mat";
        var target = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (target == null)
        {
            target = new Material(source) { name = targetName };
            AssetDatabase.CreateAsset(target, path);
        }
        else
        {
            target.CopyPropertiesFromMaterial(source);
        }

        target.color = color;
        if (target.HasProperty("_BaseColor"))
        {
            target.SetColor("_BaseColor", color);
        }
        EditorUtility.SetDirty(target);
    }

    private static void CreateUnlitMaterial(string targetName, Color color)
    {
        var shader = Shader.Find("Universal Render Pipeline/Unlit") ?? Shader.Find("Unlit/Color");
        if (shader == null)
        {
            throw new InvalidOperationException("No unlit shader is available for " + targetName + ".");
        }

        var path = MaterialsRoot + "/" + targetName + ".mat";
        var target = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (target == null)
        {
            target = new Material(shader) { name = targetName };
            AssetDatabase.CreateAsset(target, path);
        }
        else
        {
            target.shader = shader;
        }

        target.color = color;
        if (target.HasProperty("_BaseColor"))
        {
            target.SetColor("_BaseColor", color);
        }
        EditorUtility.SetDirty(target);
    }

    private static Mesh TriangleAsset(string name, Vector3 a, Vector3 b, Vector3 c)
    {
        return SaveDoubleSidedMesh(
            name,
            new[] { a, b, c },
            new[] { 0, 1, 2 },
            new[] { new Vector2(0f, 0f), new Vector2(4f, 0f), new Vector2(2f, 4f) });
    }

    private static Mesh SaveDoubleSidedMesh(string name, Vector3[] sourceVertices, int[] sourceTriangles, Vector2[] sourceUvs)
    {
        Directory.CreateDirectory(MeshesRoot);
        var vertices = sourceVertices.Concat(sourceVertices).ToArray();
        var uvs = sourceUvs.Concat(sourceUvs).ToArray();
        var triangles = new List<int>(sourceTriangles);
        for (var index = 0; index < sourceTriangles.Length; index += 3)
        {
            triangles.Add(sourceTriangles[index] + sourceVertices.Length);
            triangles.Add(sourceTriangles[index + 2] + sourceVertices.Length);
            triangles.Add(sourceTriangles[index + 1] + sourceVertices.Length);
        }

        var path = MeshesRoot + "/" + name + ".asset";
        var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if (mesh == null)
        {
            mesh = new Mesh { name = name };
            AssetDatabase.CreateAsset(mesh, path);
        }
        else
        {
            mesh.Clear();
        }
        mesh.vertices = vertices;
        mesh.triangles = triangles.ToArray();
        mesh.uv = uvs;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        EditorUtility.SetDirty(mesh);
        return mesh;
    }

    private static Vector2[] QuadUvs()
    {
        return new[]
        {
            new Vector2(0f, 0f),
            new Vector2(4f, 0f),
            new Vector2(3f, 4f),
            new Vector2(1f, 4f),
        };
    }

    private static void MeshObject(string name, Transform parent, Mesh mesh, Material material, bool collider)
    {
        var target = new GameObject(name);
        target.transform.SetParent(parent, false);
        target.AddComponent<MeshFilter>().sharedMesh = mesh;
        target.AddComponent<MeshRenderer>().sharedMaterial = material;
        if (collider)
        {
            target.AddComponent<MeshCollider>().sharedMesh = mesh;
        }
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public string ReceiptPath;
        public float CutRatio;
        public int CoreBlocks;
        public int CasingPanels;
        public int RouteMarkers;
        public int CorbelBands;
        public int RelievingChambers;
        public int FoundationSections;
        public bool HasFilledSection;
        public float QueensFloorY;
        public float QueensFloorTarget;
        public float KingsFloorY;
        public float KingsFloorTarget;
        public readonly List<string> Failures = new List<string>();
        public List<string> EnvelopeViolations = new List<string>();
    }
}

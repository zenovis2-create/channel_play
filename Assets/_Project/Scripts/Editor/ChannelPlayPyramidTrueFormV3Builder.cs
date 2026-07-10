using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayPyramidTrueFormV3Builder
{
    public const string ScenePath = "Assets/_Project/Scenes/School_MVP.unity";
    public const string MapRootName = "TraitorEscape_Runtime_Map";
    public const string PyramidRootName = "Runtime_Pyramid_True_Form_V3";
    public const float BaseSize = 56f;
    public const float PyramidHeight = BaseSize * 7f / 11f;
    public const int CoreCourseCount = 14;

    private const string MaterialsRoot = "Assets/_Project/Materials";
    private const string MeshesRoot = "Assets/_Project/Art/Generated/PyramidTrueFormV3/Meshes";
    private const string TextureRoot = "Assets/_Project/Art/Maps/pyramid_temple_real/Textures";
    private const string RunRoot = "runs/pyramid-true-form-v3";
    private const float HalfBase = BaseSize * 0.5f;
    private const float EnvelopeTolerance = 0.35f;

    private static readonly Vector3 NorthThreshold = new Vector3(1.9f, 4.1f, -24.7f);
    private static readonly Vector3 RisingBranch = new Vector3(1.6f, 1.9f, -20.3f);
    private static readonly Vector3 SubterraneanApproach = new Vector3(0.4f, -6.5f, -3.4f);
    private static readonly Vector3 SubterraneanChamber = new Vector3(0f, -6.5f, 4.5f);
    private static readonly Vector3 GalleryJunction = new Vector3(0f, 8.1f, -7.6f);
    private static readonly Vector3 QueensChamber = new Vector3(0f, 8.1f, 0.5f);
    private static readonly Vector3 GrandGalleryTop = new Vector3(0f, 14.7f, 5.9f);
    private static readonly Vector3 Antechamber = new Vector3(0f, 14.7f, 7.2f);
    private static readonly Vector3 KingsChamber = new Vector3(0f, 16.6f, 8f);

    private static readonly string[] RequiredRouteMarkers =
    {
        "V3_Route_North_Threshold",
        "V3_Route_Rising_Branch",
        "V3_Route_Subterranean_Approach",
        "V3_Route_Subterranean_Chamber",
        "V3_Route_Gallery_Junction",
        "V3_Route_Queens_Chamber",
        "V3_Route_Grand_Gallery_Top",
        "V3_Route_Antechamber",
        "V3_Route_Kings_Chamber",
    };

    [MenuItem("Channel Play/Rebuild Pyramid True Form V3")]
    public static void RebuildPyramidTrueFormV3()
    {
        Directory.CreateDirectory(MaterialsRoot);
        Directory.CreateDirectory(MeshesRoot);
        EnsureMaterials();

        var scene = EditorSceneManager.OpenScene(ScenePath);
        DeleteIfExists(MapRootName);
        HideLegacySceneMarkers();

        var mapRoot = new GameObject(MapRootName);
        var pyramidRoot = new GameObject(PyramidRootName);
        pyramidRoot.transform.SetParent(mapRoot.transform, false);

        BuildFoundation(pyramidRoot.transform);
        BuildSteppedCore(pyramidRoot.transform);
        BuildCasing(pyramidRoot.transform);
        BuildInterior(pyramidRoot.transform);
        BuildRouteMarkers(pyramidRoot.transform);
        BuildLighting(pyramidRoot.transform);
        PositionPlayerAndGameplayCamera();

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log(
            "CHANNEL_PLAY_PYRAMID_TRUE_FORM_V3_BUILD result=built" +
            " base=" + BaseSize.ToString("F2") +
            " height=" + PyramidHeight.ToString("F2") +
            " slope=" + FaceSlopeDegrees().ToString("F2") +
            " root=\"" + PyramidRootName + "\"");
    }

    [MenuItem("Channel Play/Rebuild Validate Render Pyramid True Form V3")]
    public static void RebuildValidateAndRenderPyramidTrueFormV3()
    {
        RebuildPyramidTrueFormV3();
        ValidatePyramidTrueFormV3();
        ChannelPlayPyramidTrueFormV3ScreenshotExporter.ExportScreenshots();
    }

    [MenuItem("Channel Play/Validate Pyramid True Form V3")]
    public static void ValidatePyramidTrueFormV3()
    {
        EditorSceneManager.OpenScene(ScenePath);
        var result = ValidateScene();
        WriteValidationReceipt(result);

        if (!result.Passed)
        {
            Debug.LogError(
                "CHANNEL_PLAY_PYRAMID_TRUE_FORM_V3 result=failed reason=\"" +
                string.Join("; ", result.Failures) + "\" receipt=\"" + result.ReceiptPath + "\"");
            if (Application.isBatchMode)
            {
                EditorApplication.Exit(1);
            }

            return;
        }

        Debug.Log(
            "CHANNEL_PLAY_PYRAMID_TRUE_FORM_V3 result=passed" +
            " core_courses=" + result.CoreCourses +
            " casing_faces=" + result.CasingFaces +
            " route_markers=" + result.RouteMarkers +
            " corbel_bands=" + result.CorbelBands +
            " relieving_chambers=" + result.RelievingChambers +
            " receipt=\"" + result.ReceiptPath + "\"");
    }

    public static float EnvelopeHalfWidth(float y)
    {
        if (y <= 0f)
        {
            return HalfBase;
        }

        return HalfBase * Mathf.Clamp01(1f - y / PyramidHeight);
    }

    public static float FaceSlopeDegrees()
    {
        return Mathf.Atan2(PyramidHeight, HalfBase) * Mathf.Rad2Deg;
    }

    private static void BuildFoundation(Transform root)
    {
        var foundation = new GameObject("V3_Foundation");
        foundation.transform.SetParent(root, false);

        Cube(
            "V3_Desert_Foundation",
            foundation.transform,
            new Vector3(0f, -0.45f, 0f),
            new Vector3(72f, 0.9f, 72f),
            Mat("PyramidV3_Desert"));
        Cube(
            "V3_Level_Platform",
            foundation.transform,
            new Vector3(0f, -0.08f, 0f),
            new Vector3(60f, 0.42f, 60f),
            Mat("PyramidV3_Platform"));

        var approach = new GameObject("V3_Gameplay_North_Approach");
        approach.transform.SetParent(foundation.transform, false);
        for (var step = 0; step < 12; step++)
        {
            var t = step / 11f;
            Cube(
                "V3_Approach_Step_" + step.ToString("D2"),
                approach.transform,
                new Vector3(1.9f, 0.18f + t * 3.75f, -32f + t * 7.1f),
                new Vector3(3.6f, 0.36f, 1.15f),
                Mat("PyramidV3_Platform"));
        }
    }

    private static void BuildSteppedCore(Transform root)
    {
        var core = new GameObject("V3_Exterior_Stepped_Core");
        core.transform.SetParent(root, false);
        var courseHeight = PyramidHeight / CoreCourseCount;
        var inset = HalfBase / CoreCourseCount;

        for (var course = 0; course < CoreCourseCount - 1; course++)
        {
            var courseRoot = new GameObject("V3_Core_Course_" + course.ToString("D2"));
            courseRoot.transform.SetParent(core.transform, false);

            var outerHalf = HalfBase - course * inset;
            var coreHalf = Mathf.Max(0.4f, outerHalf - inset - 0.12f);
            var width = coreHalf * 2f;
            var y = course * courseHeight + courseHeight * 0.5f;
            var thickness = 1.15f;
            var material = Mat(course % 2 == 0 ? "PyramidV3_Core_Limestone" : "PyramidV3_Core_Shadow");

            Cube(
                "V3_Core_South_" + course.ToString("D2"),
                courseRoot.transform,
                new Vector3(0f, y, coreHalf - thickness * 0.5f),
                new Vector3(width, courseHeight * 0.94f, thickness),
                material);
            Cube(
                "V3_Core_East_" + course.ToString("D2"),
                courseRoot.transform,
                new Vector3(coreHalf - thickness * 0.5f, y, 0f),
                new Vector3(thickness, courseHeight * 0.94f, width - thickness * 2f),
                material);
            Cube(
                "V3_Core_West_" + course.ToString("D2"),
                courseRoot.transform,
                new Vector3(-coreHalf + thickness * 0.5f, y, 0f),
                new Vector3(thickness, courseHeight * 0.94f, width - thickness * 2f),
                material);

            BuildNorthCutawayCourse(courseRoot.transform, course, coreHalf, y, courseHeight, thickness, material);
        }

        var capBaseY = (CoreCourseCount - 1) * courseHeight;
        var capHalf = EnvelopeHalfWidth(capBaseY);
        var capMesh = CreatePyramidMeshAsset(
            "PyramidV3_Core_Course_13_Mesh",
            capHalf,
            capBaseY,
            PyramidHeight);
        MeshObject(
            "V3_Core_Course_13_Pyramidion",
            core.transform,
            capMesh,
            Mat("PyramidV3_Core_Limestone"),
            true);
    }

    private static void BuildNorthCutawayCourse(
        Transform parent,
        int course,
        float outerHalf,
        float y,
        float courseHeight,
        float thickness,
        Material material)
    {
        var cutawayHalf = course <= 8 ? Mathf.Min(7.2f, outerHalf - 1.4f) : 0f;
        if (cutawayHalf <= 0.1f)
        {
            Cube(
                "V3_Core_North_" + course.ToString("D2"),
                parent,
                new Vector3(0f, y, -outerHalf + thickness * 0.5f),
                new Vector3(outerHalf * 2f, courseHeight * 0.94f, thickness),
                material);
            return;
        }

        var segmentWidth = outerHalf - cutawayHalf;
        var centerOffset = (outerHalf + cutawayHalf) * 0.5f;
        Cube(
            "V3_Core_North_West_" + course.ToString("D2"),
            parent,
            new Vector3(-centerOffset, y, -outerHalf + thickness * 0.5f),
            new Vector3(segmentWidth, courseHeight * 0.94f, thickness),
            material);
        Cube(
            "V3_Core_North_East_" + course.ToString("D2"),
            parent,
            new Vector3(centerOffset, y, -outerHalf + thickness * 0.5f),
            new Vector3(segmentWidth, courseHeight * 0.94f, thickness),
            material);
    }

    private static void BuildCasing(Transform root)
    {
        var casing = new GameObject("V3_Exterior_Smooth_Casing");
        casing.transform.SetParent(root, false);
        var material = Mat("PyramidV3_Tura_Casing");
        var apex = new Vector3(0f, PyramidHeight, 0f);

        MeshObject(
            "V3_Casing_South_Face",
            casing.transform,
            CreateTriangleMeshAsset(
                "PyramidV3_Casing_South_Mesh",
                new Vector3(-HalfBase, 0f, HalfBase),
                new Vector3(HalfBase, 0f, HalfBase),
                apex),
            material,
            true);
        MeshObject(
            "V3_Casing_East_Face",
            casing.transform,
            CreateTriangleMeshAsset(
                "PyramidV3_Casing_East_Mesh",
                new Vector3(HalfBase, 0f, HalfBase),
                new Vector3(HalfBase, 0f, -HalfBase),
                apex),
            material,
            true);

        var northCapY = 20f;
        var northCapHalf = EnvelopeHalfWidth(northCapY);
        MeshObject(
            "V3_Casing_North_Upper_Cap",
            casing.transform,
            CreateTriangleMeshAsset(
                "PyramidV3_Casing_North_Upper_Mesh",
                new Vector3(northCapHalf, northCapY, -northCapHalf),
                new Vector3(-northCapHalf, northCapY, -northCapHalf),
                apex),
            material,
            false);

    }

    private static void BuildInterior(Transform root)
    {
        var interior = new GameObject("V3_Interior_Architecture");
        interior.transform.SetParent(root, false);

        var passage = new GameObject("V3_Descending_And_Ascending_Passages");
        passage.transform.SetParent(interior.transform, false);
        BuildTunnelSegment(passage.transform, "V3_Descending_Upper", NorthThreshold, RisingBranch, 2.8f, 2.7f);
        BuildTunnelSegment(passage.transform, "V3_Descending_Lower", RisingBranch, SubterraneanApproach, 2.8f, 2.7f);
        BuildTunnelSegment(
            passage.transform,
            "V3_Subterranean_Level_Passage",
            SubterraneanApproach,
            new Vector3(0f, -6.5f, 1.3f),
            2.8f,
            2.7f);
        BuildTunnelSegment(passage.transform, "V3_Ascending_Passage", RisingBranch, GalleryJunction, 2.9f, 2.8f);

        BuildSubterraneanRoom(interior.transform);
        BuildQueensRoom(interior.transform);
        BuildGrandGallery(interior.transform);
        BuildKingsRoom(interior.transform);
        BuildEntrancePortal(interior.transform);
    }

    private static void BuildSubterraneanRoom(Transform parent)
    {
        var room = new GameObject("V3_Subterranean_Chamber");
        room.transform.SetParent(parent, false);
        var floorY = -6.65f;
        var centerZ = SubterraneanChamber.z;
        var material = Mat("PyramidV3_Subterranean_Rock");

        Cube("V3_Subterranean_Floor", room.transform, new Vector3(0f, floorY, centerZ), new Vector3(8f, 0.3f, 7f), material);
        Cube("V3_Subterranean_Back_Wall", room.transform, new Vector3(0f, -4.6f, centerZ + 3.5f), new Vector3(8f, 4.2f, 0.45f), material);
        Cube("V3_Subterranean_West_Wall", room.transform, new Vector3(-4f, -4.6f, centerZ), new Vector3(0.45f, 4.2f, 7f), material);
        Cube("V3_Subterranean_East_Wall", room.transform, new Vector3(4f, -4.6f, centerZ), new Vector3(0.45f, 4.2f, 7f), material);
        Cube("V3_Subterranean_Unfinished_Pit", room.transform, new Vector3(1.8f, -7.15f, centerZ + 1.1f), new Vector3(2.2f, 0.8f, 2.3f), Mat("PyramidV3_Interior_Shadow"));
        Cube("V3_Subterranean_Blind_Passage", room.transform, new Vector3(0f, -5.8f, centerZ + 5.2f), new Vector3(2.2f, 1.7f, 3.4f), Mat("PyramidV3_Interior_Shadow"));
    }

    private static void BuildQueensRoom(Transform parent)
    {
        var room = new GameObject("V3_Queens_Chamber");
        room.transform.SetParent(parent, false);
        var floorY = 7.95f;
        var centerZ = QueensChamber.z;
        var wall = Mat("PyramidV3_Interior_Limestone");

        BuildTunnelSegment(
            room.transform,
            "V3_Queens_Horizontal_Passage",
            GalleryJunction,
            new Vector3(0f, GalleryJunction.y, centerZ - 2.7f),
            2.8f,
            2.7f);
        Cube("V3_Queens_Floor", room.transform, new Vector3(0f, floorY, centerZ), new Vector3(7.4f, 0.3f, 5.4f), wall);
        Cube("V3_Queens_Back_Wall", room.transform, new Vector3(0f, 10.05f, centerZ + 2.7f), new Vector3(7.4f, 4.2f, 0.4f), wall);
        Cube("V3_Queens_West_Wall", room.transform, new Vector3(-3.7f, 10.05f, centerZ), new Vector3(0.4f, 4.2f, 5.4f), wall);
        Cube("V3_Queens_East_Wall", room.transform, new Vector3(3.7f, 10.05f, centerZ), new Vector3(0.4f, 4.2f, 5.4f), wall);
        Cube(
            "V3_Queens_Gabled_Roof_West",
            room.transform,
            new Vector3(-1.75f, 12.45f, centerZ),
            new Vector3(4.15f, 0.3f, 5.5f),
            wall,
            Quaternion.Euler(0f, 0f, 28f));
        Cube(
            "V3_Queens_Gabled_Roof_East",
            room.transform,
            new Vector3(1.75f, 12.45f, centerZ),
            new Vector3(4.15f, 0.3f, 5.5f),
            wall,
            Quaternion.Euler(0f, 0f, -28f));
        Cube("V3_Queens_East_Niche", room.transform, new Vector3(3.45f, 10.25f, centerZ + 0.5f), new Vector3(0.55f, 2.1f, 1.4f), Mat("PyramidV3_Interior_Shadow"), Quaternion.identity, false);
    }

    private static void BuildGrandGallery(Transform parent)
    {
        var gallery = new GameObject("V3_Grand_Gallery");
        gallery.transform.SetParent(parent, false);
        var direction = GrandGalleryTop - GalleryJunction;
        var length = direction.magnitude;
        var rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        var midpoint = (GalleryJunction + GrandGalleryTop) * 0.5f;
        var localUp = rotation * Vector3.up;
        var localRight = rotation * Vector3.right;
        var limestone = Mat("PyramidV3_Interior_Limestone");

        Cube("V3_Grand_Gallery_Floor", gallery.transform, midpoint, new Vector3(4.8f, 0.24f, length), limestone, rotation);
        Cube("V3_Grand_Gallery_Center_Trench", gallery.transform, midpoint + localUp * 0.13f, new Vector3(1.2f, 0.16f, length), Mat("PyramidV3_Interior_Shadow"), rotation, false);

        for (var band = 0; band < 7; band++)
        {
            var x = 2.55f - band * 0.25f;
            var y = 0.65f + band * 0.72f;
            var bandScale = new Vector3(0.34f, 0.64f, length);
            Cube(
                "V3_Grand_Corbel_West_" + band.ToString("D2"),
                gallery.transform,
                midpoint - localRight * x + localUp * y,
                bandScale,
                limestone,
                rotation);
            Cube(
                "V3_Grand_Corbel_East_" + band.ToString("D2"),
                gallery.transform,
                midpoint + localRight * x + localUp * y,
                bandScale,
                limestone,
                rotation);
        }

        Cube("V3_Grand_Gallery_Ceiling", gallery.transform, midpoint + localUp * 5.55f, new Vector3(1.8f, 0.3f, length), limestone, rotation);
        for (var slot = 0; slot < 9; slot++)
        {
            var t = (slot + 0.5f) / 9f;
            var point = Vector3.Lerp(GalleryJunction, GrandGalleryTop, t) + localUp * 0.3f;
            Cube("V3_Grand_Ramp_Slot_West_" + slot.ToString("D2"), gallery.transform, point - localRight * 1.85f, new Vector3(0.42f, 0.22f, 0.32f), Mat("PyramidV3_Route_Glow"), rotation, false);
            Cube("V3_Grand_Ramp_Slot_East_" + slot.ToString("D2"), gallery.transform, point + localRight * 1.85f, new Vector3(0.42f, 0.22f, 0.32f), Mat("PyramidV3_Route_Glow"), rotation, false);
        }
    }

    private static void BuildKingsRoom(Transform parent)
    {
        var suite = new GameObject("V3_Kings_Suite");
        suite.transform.SetParent(parent, false);
        var granite = Mat("PyramidV3_Red_Granite");
        var darkGranite = Mat("PyramidV3_Dark_Granite");

        BuildTunnelSegment(
            suite.transform,
            "V3_Antechamber_Passage",
            GrandGalleryTop,
            new Vector3(0f, 14.7f, 6.75f),
            2.5f,
            2.6f);

        var antechamberRoot = new GameObject("V3_Antechamber");
        antechamberRoot.transform.SetParent(suite.transform, false);
        Cube("V3_Antechamber_Floor", antechamberRoot.transform, new Vector3(0f, 14.58f, 7.1f), new Vector3(3.4f, 0.24f, 2.2f), darkGranite);
        for (var gate = 0; gate < 3; gate++)
        {
            Cube(
                "V3_Portcullis_" + gate.ToString("D2"),
                antechamberRoot.transform,
                new Vector3(-0.9f + gate * 0.9f, 16.15f, 7.1f),
                new Vector3(0.28f, 3.1f, 1.75f),
                granite);
        }

        var room = new GameObject("V3_Kings_Chamber");
        room.transform.SetParent(suite.transform, false);
        var floorY = 14.65f;
        Cube("V3_Kings_Floor", room.transform, new Vector3(0f, floorY, KingsChamber.z), new Vector3(8f, 0.3f, 5f), granite);
        Cube("V3_Kings_Back_Wall", room.transform, new Vector3(0f, 16.7f, 10.5f), new Vector3(8f, 4.1f, 0.42f), granite);
        Cube("V3_Kings_West_Wall", room.transform, new Vector3(-4f, 16.7f, KingsChamber.z), new Vector3(0.42f, 4.1f, 5f), granite);
        Cube("V3_Kings_East_Wall", room.transform, new Vector3(4f, 16.7f, KingsChamber.z), new Vector3(0.42f, 4.1f, 5f), granite);
        Cube("V3_Kings_Granite_Ceiling", room.transform, new Vector3(0f, 18.75f, KingsChamber.z), new Vector3(8.2f, 0.38f, 5f), granite);
        Cube("V3_Kings_Sarcophagus", room.transform, new Vector3(1.5f, 15.2f, 8.5f), new Vector3(2.7f, 0.9f, 1.25f), darkGranite);

        var relieving = new GameObject("V3_Relieving_Chambers");
        relieving.transform.SetParent(suite.transform, false);
        for (var chamber = 0; chamber < 5; chamber++)
        {
            Cube(
                "V3_Relieving_Chamber_" + chamber.ToString("D2"),
                relieving.transform,
                new Vector3(0f, 19.3f + chamber * 0.65f, KingsChamber.z),
                new Vector3(8.6f, 0.28f, 4.4f),
                chamber % 2 == 0 ? granite : darkGranite);
        }
    }

    private static void BuildEntrancePortal(Transform parent)
    {
        var portal = new GameObject("V3_North_Entrance_Portal");
        portal.transform.SetParent(parent, false);
        var stone = Mat("PyramidV3_Casing_Trim");
        Cube("V3_Entrance_West_Jamb", portal.transform, NorthThreshold + new Vector3(-1.7f, 0.1f, -0.15f), new Vector3(0.55f, 3.1f, 0.75f), stone);
        Cube("V3_Entrance_East_Jamb", portal.transform, NorthThreshold + new Vector3(1.7f, 0.1f, -0.15f), new Vector3(0.55f, 3.1f, 0.75f), stone);
        Cube("V3_Entrance_Lintel", portal.transform, NorthThreshold + new Vector3(0f, 1.65f, -0.15f), new Vector3(3.95f, 0.55f, 0.8f), stone);
        Cube("V3_Entrance_Shadow", portal.transform, NorthThreshold + new Vector3(0f, 0f, 0.2f), new Vector3(2.7f, 2.55f, 0.3f), Mat("PyramidV3_Interior_Shadow"), Quaternion.identity, false);
    }

    private static void BuildRouteMarkers(Transform parent)
    {
        var route = new GameObject("V3_Gameplay_Route_Markers");
        route.transform.SetParent(parent, false);
        Marker(route.transform, RequiredRouteMarkers[0], NorthThreshold);
        Marker(route.transform, RequiredRouteMarkers[1], RisingBranch);
        Marker(route.transform, RequiredRouteMarkers[2], SubterraneanApproach);
        Marker(route.transform, RequiredRouteMarkers[3], SubterraneanChamber);
        Marker(route.transform, RequiredRouteMarkers[4], GalleryJunction);
        Marker(route.transform, RequiredRouteMarkers[5], QueensChamber);
        Marker(route.transform, RequiredRouteMarkers[6], GrandGalleryTop);
        Marker(route.transform, RequiredRouteMarkers[7], Antechamber);
        Marker(route.transform, RequiredRouteMarkers[8], KingsChamber);

        CreateBeam("V3_Route_Descending_Glow_A", route.transform, NorthThreshold, RisingBranch, 0.11f, Mat("PyramidV3_Route_Glow"), false);
        CreateBeam("V3_Route_Descending_Glow_B", route.transform, RisingBranch, SubterraneanApproach, 0.11f, Mat("PyramidV3_Route_Glow"), false);
        CreateBeam("V3_Route_Lower_Glow", route.transform, SubterraneanApproach, SubterraneanChamber, 0.11f, Mat("PyramidV3_Route_Glow"), false);
        CreateBeam("V3_Route_Ascending_Glow", route.transform, RisingBranch, GalleryJunction, 0.11f, Mat("PyramidV3_Route_Glow"), false);
        CreateBeam("V3_Route_Queens_Glow", route.transform, GalleryJunction, QueensChamber, 0.11f, Mat("PyramidV3_Route_Glow"), false);
        CreateBeam("V3_Route_Grand_Glow", route.transform, GalleryJunction, GrandGalleryTop, 0.11f, Mat("PyramidV3_Route_Glow"), false);
        CreateBeam("V3_Route_Kings_Glow", route.transform, GrandGalleryTop, KingsChamber, 0.11f, Mat("PyramidV3_Route_Glow"), false);
    }

    private static void BuildLighting(Transform parent)
    {
        var lighting = new GameObject("V3_Presentation_Lighting");
        lighting.transform.SetParent(parent, false);

        var sunObject = new GameObject("V3_Desert_Sun");
        sunObject.transform.SetParent(lighting.transform, false);
        sunObject.transform.rotation = Quaternion.Euler(42f, -32f, 0f);
        var sun = sunObject.AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(1f, 0.86f, 0.68f);
        sun.intensity = 0.86f;
        sun.shadows = LightShadows.Soft;

        PointLight(lighting.transform, "V3_Light_Subterranean", new Vector3(0f, -4.7f, 3.5f), new Color(0.25f, 0.75f, 0.72f), 5.5f, 9f);
        PointLight(lighting.transform, "V3_Light_Queens", new Vector3(0f, 10.5f, 0.5f), new Color(0.35f, 0.72f, 0.68f), 5f, 10f);
        PointLight(lighting.transform, "V3_Light_Grand", new Vector3(0f, 13f, 1.5f), new Color(0.95f, 0.58f, 0.25f), 6f, 13f);
        PointLight(lighting.transform, "V3_Light_Kings", new Vector3(0f, 17f, 8f), new Color(0.78f, 0.28f, 0.18f), 5.5f, 9f);

        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.22f, 0.21f, 0.19f);
    }

    private static void BuildTunnelSegment(Transform parent, string name, Vector3 start, Vector3 end, float width, float height)
    {
        var direction = end - start;
        var length = direction.magnitude;
        if (length <= 0.01f)
        {
            return;
        }

        var rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        var midpoint = (start + end) * 0.5f;
        var localUp = rotation * Vector3.up;
        var localRight = rotation * Vector3.right;
        var floor = Mat("PyramidV3_Passage_Floor");
        var wall = Mat("PyramidV3_Interior_Limestone");

        Cube(name + "_Floor", parent, midpoint, new Vector3(width, 0.22f, length), floor, rotation);
        Cube(name + "_West_Wall", parent, midpoint - localRight * (width * 0.5f + 0.2f) + localUp * (height * 0.5f), new Vector3(0.4f, height, length), wall, rotation);
        Cube(name + "_East_Wall", parent, midpoint + localRight * (width * 0.5f + 0.2f) + localUp * (height * 0.5f), new Vector3(0.4f, height, length), wall, rotation);
    }

    private static void CreateBeam(string name, Transform parent, Vector3 start, Vector3 end, float width, Material material, bool collider)
    {
        var direction = end - start;
        var length = direction.magnitude;
        if (length <= 0.01f)
        {
            return;
        }

        Cube(
            name,
            parent,
            (start + end) * 0.5f,
            new Vector3(width, width, length),
            material,
            Quaternion.LookRotation(direction.normalized, Vector3.up),
            collider);
    }

    private static void Marker(Transform parent, string name, Vector3 position)
    {
        var marker = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        marker.name = name;
        marker.transform.SetParent(parent, false);
        marker.transform.localPosition = position;
        marker.transform.localScale = Vector3.one * 0.48f;
        marker.GetComponent<Renderer>().sharedMaterial = Mat("PyramidV3_Route_Glow");
        var collider = marker.GetComponent<Collider>();
        if (collider != null)
        {
            UnityEngine.Object.DestroyImmediate(collider);
        }
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
            var cubeCollider = cube.GetComponent<Collider>();
            if (cubeCollider != null)
            {
                UnityEngine.Object.DestroyImmediate(cubeCollider);
            }
        }

        return cube;
    }

    private static void MeshObject(string name, Transform parent, Mesh mesh, Material material, bool collider)
    {
        var meshObject = new GameObject(name);
        meshObject.transform.SetParent(parent, false);
        meshObject.AddComponent<MeshFilter>().sharedMesh = mesh;
        meshObject.AddComponent<MeshRenderer>().sharedMaterial = material;
        if (collider)
        {
            meshObject.AddComponent<MeshCollider>().sharedMesh = mesh;
        }
    }

    private static Mesh CreateTriangleMeshAsset(string name, Vector3 a, Vector3 b, Vector3 c)
    {
        var vertices = new[] { a, b, c, a, c, b };
        var triangles = new[] { 0, 1, 2, 3, 4, 5 };
        var uvs = new[]
        {
            new Vector2(0f, 0f), new Vector2(4f, 0f), new Vector2(2f, 4f),
            new Vector2(0f, 0f), new Vector2(2f, 4f), new Vector2(4f, 0f),
        };
        return SaveMeshAsset(name, vertices, triangles, uvs);
    }

    private static Mesh CreatePyramidMeshAsset(string name, float halfWidth, float baseY, float apexY)
    {
        var southWest = new Vector3(-halfWidth, baseY, halfWidth);
        var southEast = new Vector3(halfWidth, baseY, halfWidth);
        var northEast = new Vector3(halfWidth, baseY, -halfWidth);
        var northWest = new Vector3(-halfWidth, baseY, -halfWidth);
        var apex = new Vector3(0f, apexY, 0f);
        var vertices = new[]
        {
            southWest, southEast, apex,
            southEast, northEast, apex,
            northEast, northWest, apex,
            northWest, southWest, apex,
            northWest, northEast, southEast, southWest,
        };
        var triangles = new[]
        {
            0, 1, 2,
            3, 4, 5,
            6, 7, 8,
            9, 10, 11,
            12, 13, 14,
            12, 14, 15,
        };
        return SaveMeshAsset(name, vertices, triangles);
    }

    private static Mesh SaveMeshAsset(string name, Vector3[] vertices, int[] triangles, Vector2[] uvs = null)
    {
        Directory.CreateDirectory(MeshesRoot);
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
        mesh.triangles = triangles;
        if (uvs != null && uvs.Length == vertices.Length)
        {
            mesh.uv = uvs;
        }
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        EditorUtility.SetDirty(mesh);
        return mesh;
    }

    private static ValidationResult ValidateScene()
    {
        var result = new ValidationResult();
        result.ReceiptPath = Path.Combine(RunRoot, "validation-receipt.md").Replace('\\', '/');
        var rootObject = GameObject.Find(PyramidRootName);
        if (rootObject == null)
        {
            result.Failures.Add("pyramid root missing");
            return result;
        }

        var transforms = rootObject.GetComponentsInChildren<Transform>(true);
        result.CoreCourses = transforms.Count(item => item.name.StartsWith("V3_Core_Course_", StringComparison.Ordinal) && item.parent != null && item.parent.name == "V3_Exterior_Stepped_Core");
        result.CasingFaces = transforms.Count(item => item.name.StartsWith("V3_Casing_", StringComparison.Ordinal));
        result.RouteMarkers = RequiredRouteMarkers.Count(marker => transforms.Any(item => item.name == marker));
        result.CorbelBands = transforms.Count(item => item.name.StartsWith("V3_Grand_Corbel_", StringComparison.Ordinal));
        result.RelievingChambers = transforms.Count(item => item.name.StartsWith("V3_Relieving_Chamber_", StringComparison.Ordinal));
        result.HeightToBaseRatio = PyramidHeight / BaseSize;
        result.FaceSlope = FaceSlopeDegrees();
        result.GrandGallerySlope = Mathf.Atan2(
            GrandGalleryTop.y - GalleryJunction.y,
            Vector2.Distance(
                new Vector2(GrandGalleryTop.x, GrandGalleryTop.z),
                new Vector2(GalleryJunction.x, GalleryJunction.z))) * Mathf.Rad2Deg;

        if (Mathf.Abs(result.HeightToBaseRatio - 7f / 11f) > 0.001f)
        {
            result.Failures.Add("height/base ratio drifted from 7/11");
        }

        if (result.CoreCourses < CoreCourseCount)
        {
            result.Failures.Add("expected at least 14 core courses");
        }

        if (result.CasingFaces < 3)
        {
            result.Failures.Add("smooth casing presentation is incomplete");
        }

        if (result.RouteMarkers != RequiredRouteMarkers.Length)
        {
            result.Failures.Add("one or more route markers are missing");
        }

        if (result.CorbelBands < 14)
        {
            result.Failures.Add("Grand Gallery requires seven corbel bands per side");
        }

        if (result.RelievingChambers != 5)
        {
            result.Failures.Add("King's Chamber requires five relieving chambers");
        }

        if (result.GrandGallerySlope < 25f || result.GrandGallerySlope > 27f)
        {
            result.Failures.Add("Grand Gallery slope is outside 26 +/- 1 degrees");
        }

        if (NorthThreshold.y <= 0f || NorthThreshold.z >= 0f || NorthThreshold.x <= 0f)
        {
            result.Failures.Add("north entrance orientation or offset is invalid");
        }

        ValidateRouteVerticalOrder(result);
        ValidateInteriorEnvelope(rootObject.transform, result);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static void ValidateRouteVerticalOrder(ValidationResult result)
    {
        if (SubterraneanChamber.y >= 0f)
        {
            result.Failures.Add("subterranean chamber must remain below ground");
        }

        if (QueensChamber.y <= 0f || QueensChamber.y >= KingsChamber.y)
        {
            result.Failures.Add("Queen's Chamber must remain between ground and King's Chamber");
        }

        if (KingsChamber.y >= PyramidHeight)
        {
            result.Failures.Add("King's Chamber must remain below the apex");
        }
    }

    private static void ValidateInteriorEnvelope(Transform pyramidRoot, ValidationResult result)
    {
        var interior = FindDescendant(pyramidRoot, "V3_Interior_Architecture");
        if (interior == null)
        {
            result.Failures.Add("interior architecture root missing");
            return;
        }

        var violations = new List<string>();
        foreach (var renderer in interior.GetComponentsInChildren<Renderer>(true))
        {
            if (!renderer.enabled)
            {
                continue;
            }

            if (renderer.gameObject.name.StartsWith("V3_Entrance_", StringComparison.Ordinal) ||
                renderer.gameObject.name.StartsWith("V3_Descending_Upper_", StringComparison.Ordinal))
            {
                continue;
            }

            foreach (var worldPoint in RendererGeometryPoints(renderer))
            {
                var local = pyramidRoot.InverseTransformPoint(worldPoint);
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

        result.EnvelopeViolations = violations.Distinct().OrderBy(name => name).ToList();
        if (result.EnvelopeViolations.Count > 0)
        {
            result.Failures.Add("interior exceeds pyramid envelope: " + string.Join(", ", result.EnvelopeViolations.Take(8)));
        }
    }

    private static IEnumerable<Vector3> RendererGeometryPoints(Renderer renderer)
    {
        var meshFilter = renderer.GetComponent<MeshFilter>();
        if (meshFilter != null && meshFilter.sharedMesh != null)
        {
            foreach (var vertex in meshFilter.sharedMesh.vertices)
            {
                yield return renderer.transform.TransformPoint(vertex);
            }

            yield break;
        }

        foreach (var corner in BoundsCorners(renderer.bounds))
        {
            yield return corner;
        }
    }

    private static IEnumerable<Vector3> BoundsCorners(Bounds bounds)
    {
        var min = bounds.min;
        var max = bounds.max;
        yield return new Vector3(min.x, min.y, min.z);
        yield return new Vector3(min.x, min.y, max.z);
        yield return new Vector3(min.x, max.y, min.z);
        yield return new Vector3(min.x, max.y, max.z);
        yield return new Vector3(max.x, min.y, min.z);
        yield return new Vector3(max.x, min.y, max.z);
        yield return new Vector3(max.x, max.y, min.z);
        yield return new Vector3(max.x, max.y, max.z);
    }

    private static void WriteValidationReceipt(ValidationResult result)
    {
        Directory.CreateDirectory(RunRoot);
        var builder = new StringBuilder();
        builder.AppendLine("# Pyramid True Form V3 Validation Receipt");
        builder.AppendLine();
        builder.AppendLine("Date: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
        builder.AppendLine();
        builder.AppendLine("## Result");
        builder.AppendLine();
        builder.AppendLine("Status: `" + (result.Passed ? "passed" : "failed") + "`");
        builder.AppendLine();
        builder.AppendLine("## Geometry");
        builder.AppendLine();
        builder.AppendLine("- Base: `" + BaseSize.ToString("F3") + " m`");
        builder.AppendLine("- Height: `" + PyramidHeight.ToString("F3") + " m`");
        builder.AppendLine("- Height/base: `" + result.HeightToBaseRatio.ToString("F6") + "`");
        builder.AppendLine("- Face slope: `" + result.FaceSlope.ToString("F3") + " deg`");
        builder.AppendLine("- Grand Gallery slope: `" + result.GrandGallerySlope.ToString("F3") + " deg`");
        builder.AppendLine("- Core courses: `" + result.CoreCourses + "`");
        builder.AppendLine("- Casing faces/caps: `" + result.CasingFaces + "`");
        builder.AppendLine("- Route markers: `" + result.RouteMarkers + "`");
        builder.AppendLine("- Corbel bands: `" + result.CorbelBands + "`");
        builder.AppendLine("- Relieving chambers: `" + result.RelievingChambers + "`");
        builder.AppendLine("- Envelope violations: `" + result.EnvelopeViolations.Count + "`");

        if (result.Failures.Count > 0)
        {
            builder.AppendLine();
            builder.AppendLine("## Failures");
            builder.AppendLine();
            foreach (var failure in result.Failures)
            {
                builder.AppendLine("- " + failure);
            }
        }

        File.WriteAllText(result.ReceiptPath, builder.ToString());
    }

    private static Transform FindDescendant(Transform parent, string childName)
    {
        return parent.GetComponentsInChildren<Transform>(true).FirstOrDefault(child => child.name == childName);
    }

    private static void PositionPlayerAndGameplayCamera()
    {
        var player = GameObject.Find("MVP_Player");
        if (player != null)
        {
            player.transform.position = new Vector3(1.9f, 1.1f, -34f);
            player.transform.rotation = Quaternion.identity;
        }

        var cameraObject = GameObject.Find("Gameplay_Camera") ?? GameObject.Find("Main_Camera");
        if (cameraObject != null)
        {
            cameraObject.transform.position = new Vector3(1.9f, 5.5f, -35f);
            cameraObject.transform.LookAt(NorthThreshold + Vector3.up * 0.4f);
            var camera = cameraObject.GetComponent<Camera>();
            if (camera != null)
            {
                camera.fieldOfView = 44f;
                camera.backgroundColor = new Color(0.28f, 0.42f, 0.52f);
                camera.farClipPlane = 500f;
            }

            var activeListener = UnityEngine.Object
                .FindObjectsByType<AudioListener>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .FirstOrDefault(listener => listener.enabled && listener.gameObject.activeInHierarchy);
            if (activeListener == null)
            {
                cameraObject.AddComponent<AudioListener>();
            }
        }
    }

    private static void HideLegacySceneMarkers()
    {
        var names = new[]
        {
            "Scene_Marker_School_MVP",
            "School_MVP_Floor",
            "Blue_Team_Spawn",
            "Red_Team_Spawn",
            "Shop_Terminal_Blockout",
            "Mission_Terminal_Blockout",
            "Exit_Door_Blockout",
        };

        foreach (var name in names)
        {
            var item = GameObject.Find(name);
            if (item != null)
            {
                item.SetActive(false);
            }
        }
    }

    private static void DeleteIfExists(string name)
    {
        var existing = GameObject.Find(name);
        if (existing != null)
        {
            UnityEngine.Object.DestroyImmediate(existing);
        }
    }

    private static void EnsureMaterials()
    {
        CreateMaterial("PyramidV3_Desert", new Color(0.58f, 0.46f, 0.29f), 0.04f, null, "pyramid_sandstone", 0.2f);
        CreateMaterial("PyramidV3_Platform", new Color(0.66f, 0.58f, 0.43f), 0.12f, null, "pyramid_limestone", 0.24f);
        CreateMaterial("PyramidV3_Core_Limestone", new Color(0.54f, 0.42f, 0.28f), 0.08f, null, "pyramid_sandstone", 0.34f);
        CreateMaterial("PyramidV3_Core_Shadow", new Color(0.39f, 0.31f, 0.23f), 0.06f, null, "pyramid_relic", 0.28f);
        CreateMaterial("PyramidV3_Tura_Casing", new Color(0.74f, 0.72f, 0.64f), 0.2f, null, "pyramid_limestone", 0.2f);
        CreateMaterial("PyramidV3_Casing_Trim", new Color(0.69f, 0.64f, 0.52f), 0.16f, null, "pyramid_limestone", 0.25f);
        CreateMaterial("PyramidV3_Interior_Limestone", new Color(0.47f, 0.42f, 0.34f), 0.09f, null, "pyramid_limestone", 0.3f);
        CreateMaterial("PyramidV3_Passage_Floor", new Color(0.33f, 0.29f, 0.24f), 0.08f, null, "pyramid_relic", 0.25f);
        CreateMaterial("PyramidV3_Subterranean_Rock", new Color(0.23f, 0.22f, 0.19f), 0.04f, null, "pyramid_relic", 0.35f);
        CreateMaterial("PyramidV3_Interior_Shadow", new Color(0.035f, 0.04f, 0.045f), 0.01f);
        CreateMaterial("PyramidV3_Red_Granite", new Color(0.43f, 0.16f, 0.13f), 0.22f);
        CreateMaterial("PyramidV3_Dark_Granite", new Color(0.18f, 0.12f, 0.12f), 0.16f);
        CreateMaterial("PyramidV3_Route_Glow", new Color(0.05f, 0.58f, 0.52f), 0.2f, new Color(0.02f, 0.7f, 0.62f));
    }

    private static void CreateMaterial(
        string name,
        Color color,
        float smoothness,
        Color? emission = null,
        string textureSet = null,
        float normalScale = 0.3f)
    {
        var path = MaterialsRoot + "/" + name + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            material = new Material(shader) { name = name };
            AssetDatabase.CreateAsset(material, path);
        }

        if (material.HasProperty("_BaseColor"))
        {
            material.SetColor("_BaseColor", color);
        }

        if (material.HasProperty("_Color"))
        {
            material.SetColor("_Color", color);
        }

        if (material.HasProperty("_Smoothness"))
        {
            material.SetFloat("_Smoothness", smoothness);
        }

        if (material.HasProperty("_Glossiness"))
        {
            material.SetFloat("_Glossiness", smoothness);
        }

        if (emission.HasValue)
        {
            material.EnableKeyword("_EMISSION");
            if (material.HasProperty("_EmissionColor"))
            {
                material.SetColor("_EmissionColor", emission.Value);
            }
        }

        if (!string.IsNullOrEmpty(textureSet))
        {
            ApplyTexture(material, "_BaseMap", "_MainTex", TextureRoot + "/" + textureSet + "_albedo.png", false, normalScale);
            ApplyTexture(material, "_BumpMap", null, TextureRoot + "/" + textureSet + "_normal.png", true, normalScale);
        }

        EditorUtility.SetDirty(material);
    }

    private static void ApplyTexture(
        Material material,
        string primaryProperty,
        string fallbackProperty,
        string texturePath,
        bool normalMap,
        float normalScale)
    {
        if (!File.Exists(texturePath))
        {
            return;
        }

        var importer = AssetImporter.GetAtPath(texturePath) as TextureImporter;
        if (importer != null)
        {
            var expectedType = normalMap ? TextureImporterType.NormalMap : TextureImporterType.Default;
            if (importer.textureType != expectedType)
            {
                importer.textureType = expectedType;
                importer.SaveAndReimport();
            }
        }

        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
        if (texture == null)
        {
            return;
        }

        if (material.HasProperty(primaryProperty))
        {
            material.SetTexture(primaryProperty, texture);
        }
        else if (!string.IsNullOrEmpty(fallbackProperty) && material.HasProperty(fallbackProperty))
        {
            material.SetTexture(fallbackProperty, texture);
        }

        if (normalMap && material.HasProperty("_BumpScale"))
        {
            material.SetFloat("_BumpScale", normalScale);
            material.EnableKeyword("_NORMALMAP");
        }
    }

    private static Material Mat(string name)
    {
        var material = AssetDatabase.LoadAssetAtPath<Material>(MaterialsRoot + "/" + name + ".mat");
        if (material == null)
        {
            throw new InvalidOperationException("Missing Pyramid V3 material: " + name);
        }

        return material;
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public string ReceiptPath;
        public int CoreCourses;
        public int CasingFaces;
        public int RouteMarkers;
        public int CorbelBands;
        public int RelievingChambers;
        public float HeightToBaseRatio;
        public float FaceSlope;
        public float GrandGallerySlope;
        public readonly List<string> Failures = new List<string>();
        public List<string> EnvelopeViolations = new List<string>();
    }
}

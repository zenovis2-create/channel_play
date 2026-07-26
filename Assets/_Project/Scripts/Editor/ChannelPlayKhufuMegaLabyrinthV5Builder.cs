using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using ChannelPlay.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuMegaLabyrinthV5Builder
{
    public const string RootName = "Runtime_Khufu_Mega_Labyrinth_V5";
    public const string ScenePath = "Assets/_Project/Scenes/School_MVP.unity";
    private const string MapRootName = "TraitorEscape_Runtime_Map";
    private const string MaterialRoot = "Assets/_Project/Materials/KhufuV5";
    private const string RunRoot = "runs/khufu-mega-labyrinth-v5";

    private static readonly District[] Districts =
    {
        new District("Valley_Gate", new Vector3(150f, 0f, 0f), "HYBRID"),
        new District("Covered_Causeway", new Vector3(105f, 3f, 0f), "HYBRID"),
        new District("Pyramid_Temple_Hub", new Vector3(62f, 1f, 0f), "HYPOTHESIS"),
        new District("Boat_Pits_Eastern_Court", new Vector3(35f, 0f, 42f), "FACT"),
        new District("North_Face_Scan_Court", new Vector3(0f, 0f, -48f), "UNKNOWN"),
        new District("Authentic_Interior_Spine", new Vector3(0f, 8f, 0f), "FACT"),
        new District("Royal_Chamber_Circuit", new Vector3(-18f, 12f, 22f), "HYBRID"),
        new District("Subterranean_Threshold", new Vector3(0f, -5f, 18f), "FACT"),
        new District("Underworld_Outer_Breach", new Vector3(-38f, -12f, 42f), "FICTION"),
        new District("Underworld_False_Door_Loop", new Vector3(-72f, -19f, 2f), "FICTION"),
        new District("Underworld_Deep_Vault", new Vector3(-35f, -26f, -55f), "FICTION"),
    };

    private static readonly Vector3[] CriticalRoute =
    {
        new Vector3(150f, 0.15f, 0f), new Vector3(105f, 3.15f, 0f), new Vector3(62f, 1.15f, 0f),
        new Vector3(35f, 0.15f, 42f), new Vector3(20f, 0.15f, 60f), new Vector3(-80f, 0.15f, 80f),
        new Vector3(-80f, 4f, 40f), new Vector3(-74.25f, 4f, 38.33f),
        new Vector3(-23.75f, 12.15f, 23.67f),
        new Vector3(-18f, 12.15f, 22f), new Vector3(-21f, 12.15f, 27f),
        new Vector3(-38f, 2f, 58f), new Vector3(-48f, -11.85f, 76f), new Vector3(-54f, -11.85f, 88f),
        new Vector3(-20f, -11.85f, 88f), new Vector3(-20f, -11.85f, 42f), new Vector3(-38f, -11.85f, 42f),
        new Vector3(-72f, -18.85f, 2f), new Vector3(-35f, -25.85f, -55f),
        new Vector3(-6f, 0.15f, -49.2f), new Vector3(0f, 0.15f, -48f),
        new Vector3(45f, 0.15f, -48f), new Vector3(50f, 1.15f, -35f),
        new Vector3(62f, 1.15f, 0f), new Vector3(105f, 3.15f, 0f), new Vector3(150f, 0.15f, 0f),
    };

    [MenuItem("Channel Play/Khufu V5/Rebuild")]
    public static void Rebuild()
    {
        ChannelPlayPyramidReferenceMatchedV4Builder.Rebuild();
        var scene = EditorSceneManager.OpenScene(ScenePath);
        var mapRoot = GameObject.Find(MapRootName);
        if (mapRoot == null) throw new InvalidOperationException("Shared map root missing after V4 rebuild.");

        var old = mapRoot.transform.Find(RootName);
        if (old != null) UnityEngine.Object.DestroyImmediate(old.gameObject);

        CreateMaterials();
        var root = new GameObject(RootName).transform;
        root.SetParent(mapRoot.transform, false);
        ConfigureV5TraversalThroughV4Foundation(mapRoot.transform);
        var districtRoots = BuildDistricts(root);
        BuildCriticalRoute(root);
        BuildKeyRoutes(root);
        BuildLoopsAndShortcuts(root);
        BuildPhysicalMazeGalleries(root);
        BuildTruthBoundary(root);
        BuildUnderworldMass(root);
        BuildGameplay(mapRoot.transform, districtRoots);
        BuildLighting(root);

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("CHANNEL_PLAY_KHUFU_V5_BUILD result=built districts=" + Districts.Length);
    }

    private static void ConfigureV5TraversalThroughV4Foundation(Transform mapRoot)
    {
        var v4 = mapRoot.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        var desert = v4 == null ? null : v4.GetComponentsInChildren<Transform>(true).FirstOrDefault(item => item.name == "V4_Desert_Horizon");
        var collider = desert == null ? null : desert.GetComponent<Collider>();
        if (collider != null) collider.enabled = false;
    }

    [MenuItem("Channel Play/Khufu V5/Validate")]
    public static void Validate()
    {
        EditorSceneManager.OpenScene(ScenePath);
        var result = ValidateScene();
        WriteReceipt(result);
        if (!result.Passed)
        {
            Debug.LogError("CHANNEL_PLAY_KHUFU_V5 result=failed reason=\"" + string.Join("; ", result.Failures) + "\"");
            return;
        }
        Debug.Log("CHANNEL_PLAY_KHUFU_V5 result=passed districts=" + result.DistrictCount + " route_m=" + result.RouteLength.ToString("F1") + " loops=" + result.LoopCount + " shortcuts=" + result.ShortcutCount);
    }

    [MenuItem("Channel Play/Khufu V5/Rebuild Validate Render")]
    public static void RebuildValidateRender()
    {
        Rebuild();
        ChannelPlayPyramidReferenceMatchedV4Builder.Validate();
        Validate();
        ChannelPlayKhufuMegaLabyrinthV5ScreenshotExporter.ExportScreenshots();
    }

    private static Dictionary<string, Transform> BuildDistricts(Transform root)
    {
        var result = new Dictionary<string, Transform>();
        foreach (var district in Districts)
        {
            var districtRoot = Child(root, "V5_District_" + district.Name);
            result.Add(district.Name, districtRoot);
            Marker("V5_Evidence_" + district.EvidenceClass, districtRoot, district.Center + Vector3.up * 0.3f);
            BuildDistrictLandmark(districtRoot, district);
        }
        return result;
    }

    private static void BuildDistrictLandmark(Transform parent, District district)
    {
        var floor = Mat(district.EvidenceClass == "FACT" ? "V5_Limestone" : district.EvidenceClass == "FICTION" ? "V5_Underworld" : "V5_Sandstone");
        Cube("V5_" + district.Name + "_Floor", parent, district.Center + Vector3.down * 0.1f, new Vector3(24f, 0.25f, 24f), floor, false);
        var eastWestGate = district.Name == "Valley_Gate" || district.Name == "Covered_Causeway" || district.Name == "Pyramid_Temple_Hub";
        for (var side = -1; side <= 1; side += 2)
        {
            var pylonPosition = eastWestGate
                ? district.Center + new Vector3(0f, 3f, side * 7f)
                : district.Center + new Vector3(side * 8f, 3f, 0f);
            var pylonScale = eastWestGate ? new Vector3(5f, 6f, 2f) : new Vector3(2.2f, 6f, 5f);
            Cube("V5_" + district.Name + "_Pylon_" + side, parent, pylonPosition, pylonScale, floor, false);
        }
        var lintelScale = eastWestGate ? new Vector3(5f, 1.2f, 16f) : new Vector3(18f, 1.2f, 5f);
        Cube("V5_" + district.Name + "_Lintel", parent, district.Center + new Vector3(0f, 6f, 0f), lintelScale, floor, false);

        if (district.EvidenceClass == "FICTION")
        {
            BuildMazeChamber(parent, district.Center, district.Name, floor);
        }

        if (district.EvidenceClass == "UNKNOWN" || district.EvidenceClass == "HYPOTHESIS")
        {
            Cube("V5_Observation_Only_" + district.Name, parent, district.Center + new Vector3(0f, 3f, 7f), new Vector3(12f, 5f, 0.12f), Mat("V5_Scan"), false);
        }
        else if (district.EvidenceClass == "FICTION")
        {
            for (var i = 0; i < 5; i++)
            {
                Cube("V5_Fiction_Column_" + i, parent, district.Center + new Vector3(-7f + i * 3.5f, 2.2f, 6f), new Vector3(1f, 4.4f, 1f), floor, false);
            }
        }
    }

    private static void BuildMazeChamber(Transform parent, Vector3 center, string districtName, Material material)
    {
        var maze = Child(parent, "V5_Maze_" + districtName);
        var wallHeight = districtName.StartsWith("Underworld", StringComparison.Ordinal) ? 3.8f : 2.8f;
        Cube("V5_Maze_North_Boundary", maze, center + new Vector3(0f, wallHeight * 0.5f, -11.5f), new Vector3(23f, wallHeight, 0.45f), material, false);
        Cube("V5_Maze_South_Boundary", maze, center + new Vector3(0f, wallHeight * 0.5f, 11.5f), new Vector3(23f, wallHeight, 0.45f), material, false);
        Cube("V5_Maze_West_Boundary", maze, center + new Vector3(-11.5f, wallHeight * 0.5f, 0f), new Vector3(0.45f, wallHeight, 23f), material, false);
        Cube("V5_Maze_East_Boundary", maze, center + new Vector3(11.5f, wallHeight * 0.5f, 0f), new Vector3(0.45f, wallHeight, 23f), material, false);
        for (var lane = 0; lane < 5; lane++)
        {
            var z = -8f + lane * 4f;
            var gapRight = lane % 2 == 0;
            Cube("V5_Maze_Row_" + lane + "_West", maze, center + new Vector3(-8f, wallHeight * 0.5f, z), new Vector3(7f, wallHeight, 0.5f), material, false);
            Cube("V5_Maze_Row_" + lane + "_East", maze, center + new Vector3(8f, wallHeight * 0.5f, z), new Vector3(7f, wallHeight, 0.5f), material, false);
            if (lane < 4)
            {
                var connectorX = gapRight ? 7.5f : -7.5f;
                Cube("V5_Maze_Connector_" + lane, maze, center + new Vector3(connectorX, wallHeight * 0.5f, z + 2f), new Vector3(0.5f, wallHeight, 4f), material, false);
            }
        }
    }

    private static void BuildPhysicalMazeGalleries(Transform root)
    {
        BuildPhysicalMazeGallery(root, "Surface_East", new Vector3(122f, 0f, 68f), Mat("V5_Sandstone"));
        BuildPhysicalMazeGallery(root, "Underworld_West", new Vector3(-82f, -12f, 78f), Mat("V5_Underworld"));
    }

    private static void BuildPhysicalMazeGallery(Transform root, string name, Vector3 center, Material material)
    {
        var gallery = Child(root, "V5_Physical_Maze_Gallery_" + name);
        var floorMaterial = center.y < -5f ? Mat("V5_UnderworldPath") : Mat("V5_Path");
        Cube("V5_Physical_Maze_Floor", gallery, center + Vector3.down * 0.1f, new Vector3(34f, 0.25f, 26f), floorMaterial);
        for (var lane = 0; lane < 6; lane++)
        {
            var z = -10f + lane * 4f;
            var gapOnEast = lane % 2 == 0;
            var wallCenterX = gapOnEast ? -3f : 3f;
            Cube("V5_Physical_Maze_Wall_" + lane, gallery, center + new Vector3(wallCenterX, 1.5f, z), new Vector3(23f, 3f, 0.5f), material);
        }
        Marker("V5_Physical_Maze_Entrance", gallery, center + new Vector3(-15f, 0.2f, -12f));
        Marker("V5_Physical_Maze_Exit", gallery, center + new Vector3(15f, 0.2f, 12f));
    }

    private static void BuildTruthBoundary(Transform root)
    {
        var boundary = Child(root, "V5_Truth_Boundary_FACT_TO_FICTION");
        Cube("V5_Truth_FACT_Plinth", boundary, new Vector3(-9f, 0.5f, -62f), new Vector3(12f, 1f, 10f), Mat("V5_Limestone"), false);
        Cube("V5_Truth_FACT_Stele", boundary, new Vector3(-9f, 3.4f, -62f), new Vector3(4f, 5.8f, 1.4f), Mat("V5_Limestone"), false);
        Cube("V5_Truth_FACT_Crown", boundary, new Vector3(-9f, 6.55f, -62f), new Vector3(5.2f, 0.5f, 2f), Mat("V5_Gold"), false);
        WorldLabel("V5_Truth_FACT_Label", boundary, "FACT", new Vector3(-9f, 3.5f, -61.25f), new Color(0.16f, 0.12f, 0.08f));
        Cube("V5_Truth_UNKNOWN_Scan_Veil", boundary, new Vector3(0f, 3f, -62f), new Vector3(0.18f, 6f, 10f), Mat("V5_Scan"), false);
        Cube("V5_Truth_UNKNOWN_Base", boundary, new Vector3(0f, 0.35f, -62f), new Vector3(2.2f, 0.7f, 10f), Mat("V5_Scan"), false);
        WorldLabel("V5_Truth_UNKNOWN_Label", boundary, "UNKNOWN", new Vector3(0f, 7f, -61.8f), new Color(0.02f, 0.22f, 0.24f));
        Cube("V5_Truth_FICTION_Plinth", boundary, new Vector3(9f, 0.5f, -62f), new Vector3(12f, 1f, 10f), Mat("V5_Underworld"), false);
        Cube("V5_Truth_FICTION_Arch_West", boundary, new Vector3(4.5f, 3f, -62f), new Vector3(1f, 5f, 1f), Mat("V5_RouteWall"), false);
        Cube("V5_Truth_FICTION_Arch_East", boundary, new Vector3(13.5f, 3f, -62f), new Vector3(1f, 5f, 1f), Mat("V5_RouteWall"), false);
        Cube("V5_Truth_FICTION_Arch_Lintel", boundary, new Vector3(9f, 5.5f, -62f), new Vector3(10f, 1f, 1f), Mat("V5_RouteWall"), false);
        Cube("V5_Truth_FICTION_Threshold", boundary, new Vector3(9f, 0.85f, -62f), new Vector3(8f, 0.18f, 4f), Mat("V5_Red"), false);
        WorldLabel("V5_Truth_FICTION_Label", boundary, "FICTION", new Vector3(9f, 5.5f, -61.4f), new Color(0.95f, 0.62f, 0.16f));
    }

    private static void BuildUnderworldMass(Transform root)
    {
        var mass = Child(root, "V5_Underworld_Bedrock_Mass");
        var rock = Mat("V5_Underworld");
        Cube("V5_Underworld_Upper_Bedrock", mass, new Vector3(-55f, -15f, 48f), new Vector3(92f, 5f, 76f), rock, false);
        Cube("V5_Underworld_Middle_Bedrock", mass, new Vector3(-66f, -22f, 2f), new Vector3(72f, 5f, 76f), rock, false);
        Cube("V5_Underworld_Deep_Bedrock", mass, new Vector3(-34f, -29f, -55f), new Vector3(78f, 5f, 58f), rock, false);
        Cube("V5_Underworld_Back_Wall", mass, new Vector3(-95f, -15f, 10f), new Vector3(3f, 26f, 150f), rock, false);
    }

    private static void BuildCriticalRoute(Transform root)
    {
        var route = Child(root, "V5_Critical_Route_700_900m");
        for (var i = 0; i < CriticalRoute.Length; i++)
        {
            Marker("V5_Route_" + i.ToString("D2"), route, CriticalRoute[i]);
            if (i > 0)
            {
                var shared = Enumerable.Range(1, i - 1).Any(previous => SameUndirectedSegment(CriticalRoute[i - 1], CriticalRoute[i], CriticalRoute[previous - 1], CriticalRoute[previous]));
                BuildCorridor(route, "V5_Route_Segment_" + (i - 1).ToString("D2"), CriticalRoute[i - 1], CriticalRoute[i], !shared);
            }
        }
    }

    private static bool SameUndirectedSegment(Vector3 a, Vector3 b, Vector3 otherA, Vector3 otherB)
    {
        return (Vector3.Distance(a, otherA) < 0.01f && Vector3.Distance(b, otherB) < 0.01f) ||
               (Vector3.Distance(a, otherB) < 0.01f && Vector3.Distance(b, otherA) < 0.01f);
    }

    private static void BuildKeyRoutes(Transform root)
    {
        BuildNamedRoute(root, "Sun", new[]
        {
            new Vector3(62f, 1.15f, 0f), new Vector3(70f, 1.15f, 12f), new Vector3(80f, 0.15f, 50f),
            new Vector3(100f, 0.15f, 50f), new Vector3(100f, 0.15f, 80f), new Vector3(40f, 0.15f, 80f),
            new Vector3(40f, 0.15f, 60f), new Vector3(25f, 0.15f, 60f), new Vector3(34f, 0.15f, 45f),
        });
        BuildNamedRoute(root, "Crown", new[]
        {
            new Vector3(62f, 1.15f, 0f), new Vector3(90f, 2f, -45f),
            new Vector3(30f, 3f, -60f), new Vector3(-10f, 5f, -45f),
            new Vector3(-76.2f, 4f, 35.4f), new Vector3(-80f, 4f, 40f),
            new Vector3(-74.25f, 4f, 38.33f), new Vector3(-23.75f, 12.15f, 23.67f),
            new Vector3(-18f, 12.15f, 22f),
        });
        BuildNamedRoute(root, "Earth", new[]
        {
            new Vector3(62f, 1.15f, 0f), new Vector3(45f, 1.15f, -15f), new Vector3(45f, -5f, -70f),
            new Vector3(10f, -8f, -85f), new Vector3(-20f, -12f, -70f), new Vector3(-60f, -16f, -85f),
            new Vector3(-85f, -19f, -55f), new Vector3(-65f, -22f, -25f), new Vector3(-35f, -26f, -55f),
        });
    }

    private static void BuildNamedRoute(Transform root, string keyName, IReadOnlyList<Vector3> points)
    {
        var route = Child(root, "V5_KeyRoute_" + keyName);
        for (var i = 0; i < points.Count; i++)
        {
            Marker("V5_" + keyName + "_Route_" + i.ToString("D2"), route, points[i]);
            if (i > 0)
            {
                var sharedWithCritical = keyName == "Crown" && i >= points.Count - 3;
                BuildCorridor(route, "V5_" + keyName + "_Segment_" + (i - 1).ToString("D2"), points[i - 1], points[i], !sharedWithCritical);
            }
        }
        Marker("V5_" + keyName + "_Public_Interaction", route, points[Mathf.Min(2, points.Count - 1)] + Vector3.up * 0.4f);
        Marker("V5_" + keyName + "_Private_Risk", route, points[Mathf.Min(6, points.Count - 1)] + Vector3.up * 0.4f);
    }

    private static void BuildLoopsAndShortcuts(Transform root)
    {
        var centres = new[]
        {
            new Vector3(90f, 1.15f, -25f), new Vector3(60f, 0.15f, 85f),
            new Vector3(-10f, 0.15f, -90f), new Vector3(0f, 0f, 60f),
            new Vector3(-70f, -20f, 70f), new Vector3(-5f, -25.85f, -80f),
        };
        var anchors = new[]
        {
            new Vector3(62f, 1.15f, 0f), new Vector3(35f, 0.15f, 42f),
            new Vector3(0f, 0.15f, -48f), new Vector3(-18f, 12.15f, 22f),
            new Vector3(-38f, -11.85f, 42f), new Vector3(-35f, -25.85f, -55f),
        };
        for (var loopIndex = 0; loopIndex < centres.Length; loopIndex++)
        {
            var loop = Child(root, "V5_Loop_" + (loopIndex + 1).ToString("D2"));
            var c = centres[loopIndex];
            var points = new[] { c + new Vector3(-12f,0f,-8f), c + new Vector3(12f,0f,-8f), c + new Vector3(12f,0f,8f), c + new Vector3(-12f,0f,8f) };
            for (var i = 0; i < points.Length; i++) BuildCorridor(loop, "V5_Loop_Path_" + i, points[i], points[(i + 1) % points.Length]);
            BuildCorridor(loop, "V5_Loop_Connector", anchors[loopIndex], c);
        }
        var shortcuts = new[] { new Vector3(92f,2f,22f), new Vector3(-8f,6f,55f), new Vector3(-92f,-18f,15f) };
        for (var i = 0; i < shortcuts.Length; i++)
        {
            var shortcut = Child(root, "V5_Shortcut_" + (i + 1).ToString("D2") + "_Locked_FarSideUnlock");
            var gateObject = Cube("V5_Shortcut_Gate", shortcut, shortcuts[i] + Vector3.up * 1.5f, new Vector3(4f, 3f, 0.4f), Mat("V5_Scan"));
            var gate = gateObject.AddComponent<KhufuShortcutGate>();
            var triggerObject = Cube("V5_Shortcut_FarSide_Unlock", shortcut, shortcuts[i] + new Vector3(0f, 1f, 3f), new Vector3(4f, 2f, 1f), Mat("V5_Scan"), false);
            var triggerCollider = triggerObject.AddComponent<BoxCollider>();
            triggerCollider.isTrigger = true;
            triggerObject.GetComponent<Renderer>().enabled = false;
            triggerObject.AddComponent<KhufuShortcutUnlockTrigger>().gate = gate;
        }
    }

    private static void BuildGameplay(Transform mapRoot, Dictionary<string, Transform> districts)
    {
        foreach (Transform child in mapRoot.Cast<Transform>().Where(x => x.name.StartsWith("Runtime_", StringComparison.Ordinal) && x.name != ChannelPlayPyramidReferenceMatchedV4Builder.RootName && x.name != RootName).ToArray())
            UnityEngine.Object.DestroyImmediate(child.gameObject);

        var spawn = Marker("Gameplay_PlayerSpawn_ValleyGate", mapRoot, new Vector3(150f, 1.2f, 0f));
        var mission = Cube("Runtime_Mission_Terminal", mapRoot, new Vector3(62f, 1.2f, 8f), new Vector3(1.4f, 2.4f, 1.2f), Mat("V5_Gold")).transform;
        var shop = Cube("Runtime_Shop_Terminal", mapRoot, new Vector3(62f, 1.2f, -8f), new Vector3(1.4f, 2.4f, 1.2f), Mat("V5_Scan")).transform;
        var exit = Cube("Runtime_Final_Exit_Door", mapRoot, new Vector3(154f, 2f, 0f), new Vector3(0.6f, 4f, 7f), Mat("V5_Gold")).transform;
        var scanner = Cube("Runtime_Scanner_Beacon", mapRoot, new Vector3(0f, 1.2f, -42f), new Vector3(1f, 0.1f, 1f), Mat("V5_Scan"), false).transform;
        scanner.gameObject.SetActive(false);
        var sun = Pickup("Runtime_Key_Sun", mapRoot, new Vector3(34f, 1.2f, 45f), Mat("V5_Gold"));
        var crown = Pickup("Runtime_Key_Crown", mapRoot, new Vector3(-18f, 13.2f, 22f), Mat("V5_Gold"));
        var earth = Pickup("Runtime_Key_Earth", mapRoot, new Vector3(-35f, -24.8f, -55f), Mat("V5_Gold"));
        Pickup("Runtime_Point_Hub", mapRoot, new Vector3(62f, 1.2f, 8f), Mat("V5_Scan"));
        for (var i = 2; i <= 8; i++)
        {
            var angle = (i - 1.5f) * Mathf.PI * 0.25f;
            var botPosition = new Vector3(62f + Mathf.Cos(angle) * 8f, 1.1f, Mathf.Sin(angle) * 8f);
            Pickup("Runtime_Bot_P" + i, mapRoot, botPosition, Mat(i < 5 ? "V5_Scan" : "V5_Red"), true);
        }

        var bindings = mapRoot.GetComponent<TraitorEscapeMapBindings>();
        if (bindings == null) bindings = mapRoot.gameObject.AddComponent<TraitorEscapeMapBindings>();
        bindings.playerSpawn = spawn;
        bindings.missionTerminal = mission;
        bindings.shopTerminal = shop;
        bindings.exitDoor = exit;
        bindings.scannerBeacon = scanner;
        bindings.sunKey = sun;
        bindings.crownKey = crown;
        bindings.earthKey = earth;
        bindings.operatorStart = new Vector3(25f, 135f, 0f);
        bindings.operatorXBounds = new Vector2(-105f, 165f);
        bindings.operatorZBounds = new Vector2(-100f, 100f);
        bindings.operatorHeightBounds = new Vector2(12f, 160f);
    }

    private static void BuildLighting(Transform root)
    {
        var lightObject = new GameObject("V5_Key_Light");
        lightObject.transform.SetParent(root, false);
        lightObject.transform.rotation = Quaternion.Euler(48f, -35f, 0f);
        var light = lightObject.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 0.55f;
        light.color = new Color(1f, 0.86f, 0.68f);
        AddPointLight(root, "V5_Underworld_Light_Outer", new Vector3(-38f, -7f, 42f), new Color(0.18f, 0.62f, 0.68f));
        AddPointLight(root, "V5_Underworld_Light_FalseDoor", new Vector3(-72f, -14f, 2f), new Color(0.72f, 0.36f, 0.12f));
        AddPointLight(root, "V5_Underworld_Light_Deep", new Vector3(-35f, -21f, -55f), new Color(0.12f, 0.52f, 0.62f));
    }

    private static void AddPointLight(Transform root, string name, Vector3 position, Color color)
    {
        var lightObject = new GameObject(name);
        lightObject.transform.SetParent(root, false);
        lightObject.transform.position = position;
        var light = lightObject.AddComponent<Light>();
        light.type = LightType.Point;
        light.range = 32f;
        light.intensity = 1.8f;
        light.color = color;
        light.shadows = LightShadows.None;
    }

    private static ValidationResult ValidateScene()
    {
        var r = new ValidationResult();
        var map = GameObject.Find(MapRootName);
        if (map == null) { r.Failures.Add("Map root missing"); return r; }
        var v4 = map.transform.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        var v5 = map.transform.Find(RootName);
        if (v4 == null) r.Failures.Add("V4 root missing");
        if (v5 == null) { r.Failures.Add("V5 root missing"); return r; }
        r.DistrictCount = v5.Cast<Transform>().Count(x => x.name.StartsWith("V5_District_", StringComparison.Ordinal));
        r.LoopCount = v5.Cast<Transform>().Count(x => x.name.StartsWith("V5_Loop_", StringComparison.Ordinal));
        r.ShortcutCount = v5.Cast<Transform>().Count(x => x.name.StartsWith("V5_Shortcut_", StringComparison.Ordinal));
        r.RouteLength = CriticalRoute.Zip(CriticalRoute.Skip(1), Vector3.Distance).Sum();
        if (r.DistrictCount < 8) r.Failures.Add("Fewer than eight districts");
        if (r.LoopCount < 6) r.Failures.Add("Fewer than six loops");
        if (r.ShortcutCount < 3) r.Failures.Add("Fewer than three shortcuts");
        if (r.RouteLength < 700f || r.RouteLength > 900f) r.Failures.Add("Critical route outside 700-900m: " + r.RouteLength.ToString("F1"));
        foreach (var district in Districts)
        {
            var root = v5.Find("V5_District_" + district.Name);
            if (root == null || root.Find("V5_Evidence_" + district.EvidenceClass) == null) r.Failures.Add("District/evidence missing: " + district.Name);
        }
        var bindings = map.GetComponent<TraitorEscapeMapBindings>();
        var reason = "binding component missing";
        if (bindings == null || !bindings.IsValid(out reason)) r.Failures.Add("Invalid runtime bindings: " + reason);
        var forbidden = new[] { "Djoser", "Hawara", "SP-BV", "SP-NFC", "Queens_Shaft" };
        foreach (var transform in v5.GetComponentsInChildren<Transform>(true))
            if (forbidden.Any(x => transform.name.IndexOf(x, StringComparison.OrdinalIgnoreCase) >= 0)) r.Failures.Add("Forbidden archaeology claim: " + transform.name);
        r.Passed = r.Failures.Count == 0;
        return r;
    }

    private static void WriteReceipt(ValidationResult result)
    {
        Directory.CreateDirectory(RunRoot);
        var b = new StringBuilder("# Khufu Mega-Labyrinth V5 Validation\n\n");
        b.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        b.AppendLine("- Unity: `" + Application.unityVersion + "`");
        b.AppendLine("- Districts: " + result.DistrictCount);
        b.AppendLine("- Major loops: " + result.LoopCount);
        b.AppendLine("- Shortcuts: " + result.ShortcutCount);
        b.AppendLine("- Critical route metres: " + result.RouteLength.ToString("F1"));
        foreach (var failure in result.Failures) b.AppendLine("- Failure: " + failure);
        File.WriteAllText(Path.Combine(RunRoot, "validation.md"), b.ToString());
    }

    private static void BuildCorridor(Transform parent, string name, Vector3 a, Vector3 b, bool floorCollider = true)
    {
        var delta = b - a;
        var centre = (a + b) * 0.5f;
        if (delta.sqrMagnitude < 0.001f) return;
        var rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
        var floorMaterial = centre.y < -5f ? Mat("V5_UnderworldPath") : Mat("V5_Path");
        Cube(name + "_Floor", parent, centre, new Vector3(6f, 0.22f, delta.magnitude), floorMaterial, floorCollider, rotation);
        var right = rotation * Vector3.right;
        var up = rotation * Vector3.up;
        var wallMaterial = centre.y < -5f ? Mat("V5_Underworld") : Mat("V5_RouteWall");
        Cube(name + "_West_Wall", parent, centre - right * 3.1f + up * 0.3f, new Vector3(0.25f, 0.6f, delta.magnitude), wallMaterial, false, rotation);
        Cube(name + "_East_Wall", parent, centre + right * 3.1f + up * 0.3f, new Vector3(0.25f, 0.6f, delta.magnitude), wallMaterial, false, rotation);
        if (centre.y > 2.5f)
        {
            Cube(name + "_Bridge_Support", parent, new Vector3(centre.x, centre.y * 0.5f, centre.z), new Vector3(1.1f, centre.y, 1.1f), wallMaterial, false);
        }
    }

    private static Transform Pickup(string name, Transform parent, Vector3 position, Material material, bool collider = false)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        go.name = name; go.transform.SetParent(parent, false); go.transform.position = position; go.transform.localScale = new Vector3(0.65f, 0.18f, 0.65f);
        go.GetComponent<Renderer>().sharedMaterial = material;
        var pickupCollider = go.GetComponent<Collider>();
        if (!collider && pickupCollider != null) UnityEngine.Object.DestroyImmediate(pickupCollider);
        return go.transform;
    }

    private static Transform Marker(string name, Transform parent, Vector3 position)
    {
        var go = new GameObject(name); go.transform.SetParent(parent, false); go.transform.position = position; return go.transform;
    }

    private static void WorldLabel(string name, Transform parent, string text, Vector3 position, Color color)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.position = position;
        go.transform.rotation = Quaternion.identity;
        var label = go.AddComponent<TextMesh>();
        label.text = text;
        label.anchor = TextAnchor.MiddleCenter;
        label.alignment = TextAlignment.Center;
        label.fontSize = 96;
        label.characterSize = 0.055f;
        label.color = color;
    }

    private static GameObject Cube(string name, Transform parent, Vector3 position, Vector3 scale, Material material, bool collider = true, Quaternion? rotation = null)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.name = name; go.transform.SetParent(parent, false); go.transform.position = position; go.transform.localScale = scale; go.transform.rotation = rotation ?? Quaternion.identity;
        go.GetComponent<Renderer>().sharedMaterial = material;
        var c = go.GetComponent<Collider>(); if (!collider && c != null) UnityEngine.Object.DestroyImmediate(c);
        return go;
    }

    private static Transform Child(Transform parent, string name) { var go = new GameObject(name); go.transform.SetParent(parent, false); return go.transform; }

    private static void CreateMaterials()
    {
        Directory.CreateDirectory(MaterialRoot);
        SaveMat("V5_Limestone", new Color(0.68f, 0.61f, 0.48f), 0.05f);
        SaveMat("V5_Sandstone", new Color(0.43f, 0.32f, 0.22f), 0.02f);
        SaveMat("V5_Underworld", new Color(0.065f, 0.075f, 0.085f), 0.12f);
        SaveMat("V5_UnderworldPath", new Color(0.13f, 0.095f, 0.065f), 0.04f);
        SaveMat("V5_Path", new Color(0.48f, 0.38f, 0.27f), 0.02f);
        SaveMat("V5_RouteWall", new Color(0.34f, 0.29f, 0.23f), 0.03f);
        SaveMat("V5_Scan", new Color(0.02f, 0.78f, 0.85f), 0.55f);
        SaveMat("V5_Gold", new Color(0.92f, 0.61f, 0.12f), 0.5f);
        SaveMat("V5_Red", new Color(0.65f, 0.08f, 0.06f), 0.25f);
    }

    private static void SaveMat(string name, Color color, float metallic)
    {
        var path = MaterialRoot + "/" + name + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null) { material = new Material(Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard")); AssetDatabase.CreateAsset(material, path); }
        material.color = color; material.SetFloat("_Metallic", metallic); material.SetFloat("_Smoothness", 0.25f);
        EditorUtility.SetDirty(material);
    }

    private static Material Mat(string name) { return AssetDatabase.LoadAssetAtPath<Material>(MaterialRoot + "/" + name + ".mat"); }

    private sealed class District { public readonly string Name; public readonly Vector3 Center; public readonly string EvidenceClass; public District(string name, Vector3 center, string evidenceClass) { Name = name; Center = center; EvidenceClass = evidenceClass; } }
    private sealed class ValidationResult { public bool Passed; public int DistrictCount; public int LoopCount; public int ShortcutCount; public float RouteLength; public readonly List<string> Failures = new List<string>(); }
}

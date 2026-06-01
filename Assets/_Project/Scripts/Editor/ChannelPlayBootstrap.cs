using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using ChannelPlay.Player;

public static class ChannelPlayBootstrap
{
    private const string ProjectRoot = "Assets/_Project";
    private const string ScenesRoot = ProjectRoot + "/Scenes";
    private const string MaterialsRoot = ProjectRoot + "/Materials";

    private static readonly string[] SceneNames =
    {
        "Boot",
        "MainMenu",
        "Lobby",
        "School_MVP",
        "OperatorView",
        "OverlayTest"
    };

    public static void CreateInitialScenes()
    {
        EnsureFolders();
        CreateMaterials();

        foreach (var sceneName in SceneNames)
        {
            CreateScene(sceneName);
        }

        var buildScenes = new List<EditorBuildSettingsScene>();
        foreach (var sceneName in SceneNames)
        {
            buildScenes.Add(new EditorBuildSettingsScene($"{ScenesRoot}/{sceneName}.unity", true));
        }

        EditorBuildSettings.scenes = buildScenes.ToArray();
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("channel_play bootstrap scenes created.");
    }

    public static void CreateFirstPlayableSlice()
    {
        EnsureFolders();
        CreateMaterials();

        var scenePath = $"{ScenesRoot}/School_MVP.unity";
        var scene = EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);

        DestroyIfExists("Main_Camera");
        DestroyIfExists("MVP_Player");
        DestroyIfExists("Gameplay_Camera");
        DestroyIfExists("Operator_Overview_Camera");

        var player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        player.name = "MVP_Player";
        player.transform.position = new Vector3(0f, 1f, -4f);
        player.transform.localScale = new Vector3(1f, 1f, 1f);
        ApplyMaterial(player, "Team_Blue");

        var primitiveCollider = player.GetComponent<Collider>();
        if (primitiveCollider != null)
        {
            UnityEngine.Object.DestroyImmediate(primitiveCollider);
        }

        var controller = player.AddComponent<CharacterController>();
        controller.height = 2f;
        controller.radius = 0.45f;
        controller.center = new Vector3(0f, 1f, 0f);
        player.AddComponent<ChannelPlayerController>();

        var gameplayCamera = new GameObject("Gameplay_Camera");
        gameplayCamera.tag = "MainCamera";
        var camera = gameplayCamera.AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.08f, 0.1f, 0.12f);
        gameplayCamera.transform.position = new Vector3(0f, 7f, -12f);
        gameplayCamera.transform.rotation = Quaternion.Euler(35f, 0f, 0f);
        gameplayCamera.AddComponent<ChannelFollowCamera>().SetTarget(player.transform);

        var operatorCamera = new GameObject("Operator_Overview_Camera");
        var overviewCamera = operatorCamera.AddComponent<Camera>();
        overviewCamera.enabled = false;
        overviewCamera.clearFlags = CameraClearFlags.SolidColor;
        overviewCamera.backgroundColor = new Color(0.04f, 0.06f, 0.07f);
        operatorCamera.transform.position = new Vector3(0f, 18f, -3f);
        operatorCamera.transform.rotation = Quaternion.Euler(70f, 0f, 0f);

        var prefabPath = $"{ProjectRoot}/Prefabs/MVP_Player.prefab";
        PrefabUtility.SaveAsPrefabAsset(player, prefabPath);

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("channel_play first playable slice created.");
    }

    private static void EnsureFolders()
    {
        Directory.CreateDirectory(ScenesRoot);
        Directory.CreateDirectory(MaterialsRoot);
    }

    private static void CreateMaterials()
    {
        CreateMaterial("MVP_Floor", new Color(0.33f, 0.37f, 0.34f));
        CreateMaterial("Team_Blue", new Color(0.13f, 0.35f, 0.88f));
        CreateMaterial("Team_Red", new Color(0.82f, 0.18f, 0.16f));
        CreateMaterial("Operator_Green", new Color(0.12f, 0.56f, 0.32f));
        CreateMaterial("Point_Gold", new Color(0.95f, 0.64f, 0.16f));
    }

    private static void CreateMaterial(string name, Color color)
    {
        var path = $"{MaterialsRoot}/{name}.mat";
        if (File.Exists(path))
        {
            return;
        }

        var shader = Shader.Find("Standard");
        if (shader == null)
        {
            shader = Shader.Find("Universal Render Pipeline/Lit");
        }

        var material = new Material(shader)
        {
            name = name,
            color = color
        };

        AssetDatabase.CreateAsset(material, path);
    }

    private static void CreateScene(string sceneName)
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        scene.name = sceneName;

        AddCamera(sceneName);
        AddLight();
        AddSceneMarker(sceneName);

        if (sceneName == "School_MVP")
        {
            AddSchoolBlockout();
        }

        if (sceneName == "OperatorView")
        {
            AddOperatorBlockout();
        }

        EditorSceneManager.SaveScene(scene, $"{ScenesRoot}/{sceneName}.unity");
    }

    private static void AddCamera(string sceneName)
    {
        var cameraObject = new GameObject(sceneName == "OperatorView" ? "Operator_Camera" : "Main_Camera");
        var camera = cameraObject.AddComponent<Camera>();
        cameraObject.tag = "MainCamera";
        cameraObject.transform.position = sceneName == "School_MVP"
            ? new Vector3(0f, 8f, -10f)
            : new Vector3(0f, 3f, -7f);
        cameraObject.transform.rotation = Quaternion.Euler(sceneName == "School_MVP" ? 38f : 22f, 0f, 0f);
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.08f, 0.1f, 0.12f);
    }

    private static void DestroyIfExists(string objectName)
    {
        var existing = GameObject.Find(objectName);
        if (existing != null)
        {
            UnityEngine.Object.DestroyImmediate(existing);
        }
    }

    private static void AddLight()
    {
        var lightObject = new GameObject("Key_Light");
        var light = lightObject.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.3f;
        lightObject.transform.rotation = Quaternion.Euler(48f, -35f, 0f);
    }

    private static void AddSceneMarker(string sceneName)
    {
        var marker = GameObject.CreatePrimitive(PrimitiveType.Cube);
        marker.name = $"Scene_Marker_{sceneName}";
        marker.transform.position = Vector3.zero;
        marker.transform.localScale = new Vector3(1.4f, 1.4f, 1.4f);
        ApplyMaterial(marker, "Point_Gold");
    }

    private static void AddSchoolBlockout()
    {
        var floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        floor.name = "School_MVP_Floor";
        floor.transform.position = new Vector3(0f, -0.55f, 0f);
        floor.transform.localScale = new Vector3(18f, 0.2f, 14f);
        ApplyMaterial(floor, "MVP_Floor");

        AddTeamSpawn("Blue_Team_Spawn", new Vector3(-5f, 0f, -3f), "Team_Blue");
        AddTeamSpawn("Red_Team_Spawn", new Vector3(5f, 0f, -3f), "Team_Red");
        AddTerminal("Shop_Terminal_Blockout", new Vector3(-6f, 0f, 4f));
        AddTerminal("Mission_Terminal_Blockout", new Vector3(6f, 0f, 4f));
        AddTerminal("Exit_Door_Blockout", new Vector3(0f, 0f, 6f));
    }

    private static void AddOperatorBlockout()
    {
        var desk = GameObject.CreatePrimitive(PrimitiveType.Cube);
        desk.name = "Operator_Control_Desk_Blockout";
        desk.transform.position = new Vector3(0f, 0f, 1.5f);
        desk.transform.localScale = new Vector3(4f, 0.4f, 1.4f);
        ApplyMaterial(desk, "Operator_Green");
    }

    private static void AddTeamSpawn(string name, Vector3 position, string materialName)
    {
        var spawn = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        spawn.name = name;
        spawn.transform.position = position;
        spawn.transform.localScale = new Vector3(1.5f, 0.1f, 1.5f);
        ApplyMaterial(spawn, materialName);
    }

    private static void AddTerminal(string name, Vector3 position)
    {
        var terminal = GameObject.CreatePrimitive(PrimitiveType.Cube);
        terminal.name = name;
        terminal.transform.position = position;
        terminal.transform.localScale = new Vector3(1.4f, 2f, 0.4f);
        ApplyMaterial(terminal, "Operator_Green");
    }

    private static void ApplyMaterial(GameObject target, string materialName)
    {
        var material = AssetDatabase.LoadAssetAtPath<Material>($"{MaterialsRoot}/{materialName}.mat");
        var renderer = target.GetComponent<Renderer>();
        if (material != null && renderer != null)
        {
            renderer.sharedMaterial = material;
        }
    }
}

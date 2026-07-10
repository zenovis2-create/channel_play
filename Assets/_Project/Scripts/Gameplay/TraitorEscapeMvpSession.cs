using System;
using System.Collections.Generic;
using ChannelPlay.Player;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ChannelPlay.Gameplay
{
    public static class TraitorEscapeMvpRuntimeBootstrap
    {
        private const string SessionObjectName = "TraitorEscape_MVP_Runtime";

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Initialize()
        {
            EnsureSession();
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private static void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            EnsureSession();
        }

        private static void EnsureSession()
        {
            var root = GameObject.Find(SessionObjectName);
            if (root == null)
            {
                root = new GameObject(SessionObjectName);
            }

            if (root.GetComponent<TraitorEscapeMvpSession>() == null)
            {
                root.AddComponent<TraitorEscapeMvpSession>();
            }
        }
    }

    public sealed class TraitorEscapeMvpSession : MonoBehaviour
    {
        private const string MapRootName = "TraitorEscape_Runtime_Map";
        private const int StartingPoints = 40;
        private const int TruthPenCost = 30;
        private const int ScannerCost = 25;
        private const int SerumCost = 35;
        private const float SessionLengthSeconds = 35f * 60f;
        private const float MissionCooldownSeconds = 20f;
        private const float ScannerBeaconSeconds = 14f;
        private const float DoppelgangerSeconds = 20f;
        private const float OperatorMoveSpeed = 9f;
        private const float OperatorFastMoveSpeed = 18f;
        private const float OperatorZoomSpeed = 18f;
        private const float OperatorMinHeight = 9f;
        private const float OperatorMaxHeight = 28f;
        private const float ParticipantFieldOfView = 60f;
        private const float KhufuOperatorFieldOfView = 75f;
        private static readonly Vector3 LocalPlayerSpawn = new Vector3(0f, 1f, -8.6f);

        private readonly List<RuntimeMarker> pickups = new List<RuntimeMarker>();
        private readonly List<ParticipantState> participants = new List<ParticipantState>();
        private readonly List<RuntimeBot> bots = new List<RuntimeBot>();
        private readonly List<Transform> labels = new List<Transform>();
        private readonly List<RuntimeLabelBinding> labelBindings = new List<RuntimeLabelBinding>();

        private Transform player;
        private ChannelPlayerController playerController;
        private ChannelFollowCamera followCamera;
        private ChannelCameraOccluderCutaway cameraCutaway;
        private ChannelManualTraversalRecorder manualTraversalRecorder;
        private Camera gameplayCamera;
        private AudioSource sfxSource;
        private Transform shopTerminal;
        private Transform missionTerminal;
        private Transform exitDoor;
        private Transform scannerBeacon;
        private Transform lastScannerTarget;
        private TraitorEscapeMapBindings mapBindings;
        private Vector3 playerSpawn = LocalPlayerSpawn;
        private Vector3 exitClosedPosition = new Vector3(0f, 1.6f, 8.45f);
        private Vector3 exitOpenPosition = new Vector3(0f, 3.9f, 7.65f);

        private Material floorMaterial;
        private Material wallMaterial;
        private Material propMaterial;
        private Material teamBlueMaterial;
        private Material teamRedMaterial;
        private Material operatorMaterial;
        private Material pointMaterial;
        private Material keyMaterial;
        private Material exitMaterial;
        private Material openExitMaterial;
        private Material scannerMaterial;

        private GUIStyle labelStyle;
        private GUIStyle smallStyle;
        private GUIStyle titleStyle;

        private int points = StartingPoints;
        private int keysCollected;
        private readonly KhufuObjectiveState khufuObjectives = new KhufuObjectiveState();
        private int truthPens;
        private int scanners;
        private int serums;
        private float timeRemaining = SessionLengthSeconds;
        private float doppelgangerUntil;
        private float scannerBeaconUntil;
        private float nextMissionAvailableAt;
        private bool shopOpen;
        private bool operatorView;
        private bool exitOpened;
        private string scannerReadout = "Scanner idle";
        private string truthReadout = "Truth Pen idle";
        private string objectiveReadout = "Collect 3 keys, buy items, open the final door";
        private string interactionHint = "Move to pickups or terminals";
        private string lastEvent = "Session ready";
        private bool pilotMoved;
        private bool pilotCollectedPoints;
        private bool pilotOpenedShop;
        private bool pilotBoughtItem;
        private bool pilotUsedTruthPen;
        private bool pilotUsedScanner;
        private bool pilotUsedSerum;
        private bool pilotRanMission;
        private bool pilotVisitedOperator;
        private bool pilotOperatorGrantedPoints;
        private bool pilotOperatorGrantedItems;

        private void Awake()
        {
            BuildMaterials();
            BuildRoster();
            BuildRuntimeMap();
            EnsurePlayer();
            EnsureCamera();
            EnsureAudio();
            PlaySfx(ChannelPlayAssetRuntime.RoundStartEvent);
        }

        private void Update()
        {
            if (timeRemaining > 0f)
            {
                timeRemaining = Mathf.Max(0f, timeRemaining - Time.deltaTime);
            }

            if (player == null)
            {
                EnsurePlayer();
            }

            HandlePickups();
            HandleInteractionInput();
            HandleOperatorCameraInput();
            HandleItemInput();
            UpdatePilotReadiness();
            AnimatePickups();
            AnimateBots();
            UpdateScannerBeacon();
            UpdateExitDoor();
            FaceLabelsToCamera();
            RefreshPlayerVisual();
            SyncLocalParticipant();
            if (manualTraversalRecorder != null)
            {
                manualTraversalRecorder.SetOperatorHudVisible(!shopOpen && !operatorView);
            }
        }

        private void OnGUI()
        {
            EnsureGuiStyles();
            DrawHud();
            DrawScoreboard();

            if (shopOpen)
            {
                DrawShop();
            }

            if (operatorView)
            {
                DrawOperatorPanel();
            }
        }

        private void BuildMaterials()
        {
            floorMaterial = CreateRuntimeMaterial("Pyramid_Sandstone_Floor_Runtime", new Color(0.58f, 0.45f, 0.28f));
            wallMaterial = CreateRuntimeMaterial("Pyramid_Limestone_Wall_Runtime", new Color(0.72f, 0.62f, 0.42f));
            propMaterial = CreateRuntimeMaterial("Pyramid_Relic_Prop_Runtime", new Color(0.43f, 0.32f, 0.2f));
            teamBlueMaterial = CreateRuntimeMaterial("Team_Blue_Runtime", new Color(0.12f, 0.34f, 0.9f));
            teamRedMaterial = CreateRuntimeMaterial("Team_Red_Runtime", new Color(0.86f, 0.18f, 0.15f));
            operatorMaterial = CreateRuntimeMaterial("Operator_Green_Runtime", new Color(0.1f, 0.5f, 0.3f));
            pointMaterial = CreateRuntimeMaterial("Point_Gold_Runtime", new Color(0.95f, 0.66f, 0.16f));
            keyMaterial = CreateRuntimeMaterial("Key_Cyan_Runtime", new Color(0.2f, 0.85f, 0.95f));
            exitMaterial = CreateRuntimeMaterial("Exit_Door_Runtime", new Color(0.55f, 0.28f, 0.85f));
            openExitMaterial = CreateRuntimeMaterial("Exit_Open_Runtime", new Color(0.16f, 0.75f, 0.38f));
            scannerMaterial = CreateRuntimeMaterial("Scanner_Beacon_Runtime", new Color(0.15f, 0.9f, 1f, 0.85f));
        }

        private void BuildRoster()
        {
            participants.Clear();
            participants.Add(new ParticipantState("P1", "Blue", false, "Active", points, LocalPlayerSpawn));
            participants.Add(new ParticipantState("P2", "Blue", false, "Searching", 30, new Vector3(-7.5f, 1f, 2.4f)));
            participants.Add(new ParticipantState("P3", "Blue", false, "At shop", 30, new Vector3(7.2f, 1f, 5.2f)));
            participants.Add(new ParticipantState("P4", "Blue", true, "Hidden", 30, new Vector3(-1.6f, 1f, 2.2f)));
            participants.Add(new ParticipantState("P5", "Red", false, "Searching", 30, new Vector3(7.5f, 1f, -1.7f)));
            participants.Add(new ParticipantState("P6", "Red", false, "Guarding", 30, new Vector3(2.8f, 1f, -4.8f)));
            participants.Add(new ParticipantState("P7", "Red", false, "Searching", 30, new Vector3(-6.6f, 1f, -1.7f)));
            participants.Add(new ParticipantState("P8", "Red", false, "Watching exit", 30, new Vector3(0f, 1f, 7.2f)));
        }

        private void BuildRuntimeMap()
        {
            var existingRoot = GameObject.Find(MapRootName);
            if (existingRoot != null)
            {
                CacheExistingRuntimeObjects(existingRoot.transform);
                return;
            }

            HideLegacySchoolBlockout();

            var root = new GameObject(MapRootName);

            BuildPyramidTempleShell(root.transform);
            BuildPyramidTempleInterior(root.transform);
            BuildPyramidTempleProps(root.transform);

            missionTerminal = CreateCube("Runtime_Mission_Terminal", root.transform, new Vector3(-7.8f, 1f, 5.2f), new Vector3(1.2f, 2f, 0.8f), operatorMaterial).transform;
            shopTerminal = CreateCube("Runtime_Shop_Terminal", root.transform, new Vector3(7.8f, 1f, 5.2f), new Vector3(1.2f, 2f, 0.8f), operatorMaterial).transform;
            exitDoor = CreateCube("Runtime_Final_Exit_Door", root.transform, new Vector3(0f, 1.6f, 8.45f), new Vector3(3.2f, 3.2f, 0.45f), exitMaterial).transform;
            scannerBeacon = CreateCube("Runtime_Scanner_Beacon", root.transform, Vector3.zero, new Vector3(0.8f, 0.08f, 0.8f), scannerMaterial).transform;
            scannerBeacon.gameObject.SetActive(false);

            CreateLabel(root.transform, "Runtime_Label_Mission", "ORACLE OBELISK +20", missionTerminal.position + Vector3.up * 1.6f, Color.white);
            CreateLabel(root.transform, "Runtime_Label_Shop", "RELIC BAZAAR", shopTerminal.position + Vector3.up * 1.6f, Color.white);
            CreateLabel(root.transform, "Runtime_Label_Exit", "KING'S SEAL", exitDoor.position + Vector3.up * 2f + Vector3.back * 0.3f, Color.white);

            CreatePickup(root.transform, MarkerKind.Key, "Runtime_Key_A", new Vector3(-7.2f, 0.65f, -1.6f), 0);
            CreatePickup(root.transform, MarkerKind.Key, "Runtime_Key_B", new Vector3(0f, 0.65f, 2.7f), 0);
            CreatePickup(root.transform, MarkerKind.Key, "Runtime_Key_C", new Vector3(7.2f, 0.65f, -1.6f), 0);
            CreatePickup(root.transform, MarkerKind.Point, "Runtime_Point_A", new Vector3(-3.6f, 0.55f, -5.5f), 10);
            CreatePickup(root.transform, MarkerKind.Point, "Runtime_Point_B", new Vector3(3.6f, 0.55f, -5.5f), 10);
            CreatePickup(root.transform, MarkerKind.Point, "Runtime_Point_C", new Vector3(0f, 0.55f, 5.4f), 15);
            CreateRuntimeParticipants(root.transform);

            CacheExistingRuntimeObjects(root.transform);
        }

        private void BuildPyramidTempleShell(Transform root)
        {
            CreateCube("Runtime_Floor", root, new Vector3(0f, -0.1f, 0f), new Vector3(26f, 0.2f, 22f), floorMaterial);
            CreateCube("Runtime_Entrance_Ramp", root, new Vector3(0f, 0.08f, -9.8f), new Vector3(4.6f, 0.16f, 2.4f), floorMaterial);

            for (var tier = 0; tier < 6; tier++)
            {
                var width = 26f - tier * 3f;
                var depth = 22f - tier * 2.5f;
                var y = 0.45f + tier * 0.55f;
                var strip = 0.75f;
                var z = depth * 0.5f;
                var x = width * 0.5f;
                var gap = Mathf.Max(3.4f - tier * 0.25f, 1.7f);
                var sideWidth = Mathf.Max((width - gap) * 0.5f, 1f);

                CreateCube("Runtime_Pyramid_Tier_" + tier + "_Front_L", root, new Vector3(-(gap + sideWidth) * 0.5f, y, -z), new Vector3(sideWidth, 0.9f, strip), wallMaterial);
                CreateCube("Runtime_Pyramid_Tier_" + tier + "_Front_R", root, new Vector3((gap + sideWidth) * 0.5f, y, -z), new Vector3(sideWidth, 0.9f, strip), wallMaterial);
                CreateCube("Runtime_Pyramid_Tier_" + tier + "_Back", root, new Vector3(0f, y, z), new Vector3(width, 0.9f, strip), wallMaterial);
                CreateCube("Runtime_Pyramid_Tier_" + tier + "_Left", root, new Vector3(-x, y, 0f), new Vector3(strip, 0.9f, Mathf.Max(depth - 1.4f, 1f)), wallMaterial);
                CreateCube("Runtime_Pyramid_Tier_" + tier + "_Right", root, new Vector3(x, y, 0f), new Vector3(strip, 0.9f, Mathf.Max(depth - 1.4f, 1f)), wallMaterial);
            }

            CreateCube("Runtime_Pyramid_Capstone", root, new Vector3(0f, 4.05f, 0.6f), new Vector3(4.2f, 0.8f, 3.6f), pointMaterial);
            CreateCube("Runtime_Entrance_Header", root, new Vector3(0f, 2.2f, -9.55f), new Vector3(4.3f, 1.1f, 0.65f), wallMaterial);
        }

        private void BuildPyramidTempleInterior(Transform root)
        {
            CreateCube("Runtime_Central_Corridor_Floor", root, new Vector3(0f, 0.02f, -3.6f), new Vector3(4f, 0.08f, 11.4f), floorMaterial);
            CreateCube("Runtime_Burial_Chamber_Floor", root, new Vector3(0f, 0.03f, 3.9f), new Vector3(8f, 0.08f, 4.2f), floorMaterial);
            CreateCube("Runtime_West_Relic_Room_Floor", root, new Vector3(-7.1f, 0.03f, -1.4f), new Vector3(4.6f, 0.08f, 5f), floorMaterial);
            CreateCube("Runtime_East_Trap_Room_Floor", root, new Vector3(7.1f, 0.03f, -1.4f), new Vector3(4.6f, 0.08f, 5f), floorMaterial);

            CreateCube("Runtime_Corridor_Wall_West_A", root, new Vector3(-2.35f, 1f, -4.8f), new Vector3(0.35f, 2f, 5.6f), wallMaterial);
            CreateCube("Runtime_Corridor_Wall_East_A", root, new Vector3(2.35f, 1f, -4.8f), new Vector3(0.35f, 2f, 5.6f), wallMaterial);
            CreateCube("Runtime_Corridor_Wall_West_B", root, new Vector3(-2.35f, 1f, 2.2f), new Vector3(0.35f, 2f, 2.4f), wallMaterial);
            CreateCube("Runtime_Corridor_Wall_East_B", root, new Vector3(2.35f, 1f, 2.2f), new Vector3(0.35f, 2f, 2.4f), wallMaterial);
            CreateCube("Runtime_Relic_Room_Back_Wall", root, new Vector3(-7.1f, 1f, 1.2f), new Vector3(5.2f, 2f, 0.35f), wallMaterial);
            CreateCube("Runtime_Trap_Room_Back_Wall", root, new Vector3(7.1f, 1f, 1.2f), new Vector3(5.2f, 2f, 0.35f), wallMaterial);
            CreateCube("Runtime_West_Room_Outer_Wall", root, new Vector3(-9.75f, 1f, -1.4f), new Vector3(0.35f, 2f, 5.2f), wallMaterial);
            CreateCube("Runtime_East_Room_Outer_Wall", root, new Vector3(9.75f, 1f, -1.4f), new Vector3(0.35f, 2f, 5.2f), wallMaterial);

            AddPillar(root, "Runtime_Pillar_Front_L", new Vector3(-1.6f, 0.85f, -6.2f), 1.7f);
            AddPillar(root, "Runtime_Pillar_Front_R", new Vector3(1.6f, 0.85f, -6.2f), 1.7f);
            AddPillar(root, "Runtime_Pillar_Chamber_L", new Vector3(-3.2f, 0.95f, 4.1f), 1.9f);
            AddPillar(root, "Runtime_Pillar_Chamber_R", new Vector3(3.2f, 0.95f, 4.1f), 1.9f);

            CreateCube("Runtime_Blue_Spawn", root, new Vector3(-1.4f, 0.04f, -8.1f), new Vector3(2.1f, 0.08f, 1.7f), teamBlueMaterial);
            CreateCube("Runtime_Red_Spawn", root, new Vector3(1.4f, 0.04f, -8.1f), new Vector3(2.1f, 0.08f, 1.7f), teamRedMaterial);
        }

        private void BuildPyramidTempleProps(Transform root)
        {
            CreateCube("Runtime_Sarcophagus", root, new Vector3(0f, 0.55f, 3.7f), new Vector3(2.4f, 1.1f, 1.05f), propMaterial);
            CreateCube("Runtime_Sarcophagus_Lid", root, new Vector3(0f, 1.18f, 3.7f), new Vector3(2.7f, 0.25f, 1.25f), wallMaterial);
            CreateCube("Runtime_Treasure_Altar", root, new Vector3(0f, 0.6f, 5.6f), new Vector3(2.6f, 1.2f, 0.9f), pointMaterial);
            CreateCube("Runtime_Stone_Block_West", root, new Vector3(-5.1f, 0.65f, -4.3f), new Vector3(1.5f, 1.3f, 1f), propMaterial);
            CreateCube("Runtime_Stone_Block_East", root, new Vector3(5.1f, 0.65f, -4.3f), new Vector3(1.5f, 1.3f, 1f), propMaterial);
            CreateCube("Runtime_Pressure_Plate_A", root, new Vector3(0f, 0.09f, -2.2f), new Vector3(1.5f, 0.1f, 1.1f), operatorMaterial);
            CreateCube("Runtime_Pressure_Plate_B", root, new Vector3(6.9f, 0.09f, -2.8f), new Vector3(1.4f, 0.1f, 1.1f), operatorMaterial);
            CreateCube("Runtime_Spike_Trap_West", root, new Vector3(-6.8f, 0.28f, -3.2f), new Vector3(2.2f, 0.55f, 0.35f), exitMaterial);
            CreateCube("Runtime_Spike_Trap_East", root, new Vector3(6.8f, 0.28f, -3.2f), new Vector3(2.2f, 0.55f, 0.35f), exitMaterial);

            for (var index = 0; index < 5; index++)
            {
                AddVase(root, "Runtime_Canopic_Jar_West_" + index, new Vector3(-8.4f + index * 0.6f, 0.45f, 0.15f));
                AddVase(root, "Runtime_Canopic_Jar_East_" + index, new Vector3(5.9f + index * 0.6f, 0.45f, 0.15f));
            }

            CreateCube("Runtime_Wall_Relief_West", root, new Vector3(-2.55f, 1.55f, 0.2f), new Vector3(0.08f, 1.2f, 2.6f), pointMaterial);
            CreateCube("Runtime_Wall_Relief_East", root, new Vector3(2.55f, 1.55f, 0.2f), new Vector3(0.08f, 1.2f, 2.6f), pointMaterial);
            CreateLabel(root, "Runtime_Label_Map_Title", "PYRAMID TEMPLE", new Vector3(0f, 3.1f, -7.8f), Color.white);
        }

        private void HideLegacySchoolBlockout()
        {
            var names = new[]
            {
                "Scene_Marker_School_MVP",
                "School_MVP_Floor",
                "Blue_Team_Spawn",
                "Red_Team_Spawn",
                "Shop_Terminal_Blockout",
                "Mission_Terminal_Blockout",
                "Exit_Door_Blockout"
            };

            foreach (var objectName in names)
            {
                var target = GameObject.Find(objectName);
                if (target != null)
                {
                    target.SetActive(false);
                }
            }
        }

        private void CacheExistingRuntimeObjects(Transform root)
        {
            pickups.Clear();
            bots.Clear();
            labels.Clear();
            labelBindings.Clear();

            mapBindings = root.GetComponent<TraitorEscapeMapBindings>();
            if (mapBindings != null)
            {
                if (!mapBindings.IsValid(out var reason))
                {
                    throw new InvalidOperationException("Invalid authored map bindings: " + reason);
                }

                playerSpawn = mapBindings.playerSpawn.position;
                missionTerminal = mapBindings.missionTerminal;
                shopTerminal = mapBindings.shopTerminal;
                exitDoor = mapBindings.exitDoor;
                scannerBeacon = mapBindings.scannerBeacon;
                exitClosedPosition = exitDoor.position;
                exitOpenPosition = exitClosedPosition + Vector3.up * 3.2f;
            }
            else
            {
                playerSpawn = LocalPlayerSpawn;
                missionTerminal = root.Find("Runtime_Mission_Terminal");
                shopTerminal = root.Find("Runtime_Shop_Terminal");
                exitDoor = root.Find("Runtime_Final_Exit_Door");
                scannerBeacon = root.Find("Runtime_Scanner_Beacon");
                exitClosedPosition = exitDoor == null ? new Vector3(0f, 1.6f, 8.45f) : exitDoor.position;
                exitOpenPosition = new Vector3(0f, 3.9f, 7.65f);
            }

            for (var index = 0; index < root.childCount; index++)
            {
                var child = root.GetChild(index);
                if (child.name.StartsWith("Runtime_Key_", StringComparison.Ordinal))
                {
                    pickups.Add(new RuntimeMarker(child, MarkerKind.Key, 0, ParseKhufuKey(child.name)));
                }
                else if (child.name.StartsWith("Runtime_Point_", StringComparison.Ordinal))
                {
                    var pointValue = child.name.EndsWith("_C", StringComparison.Ordinal) ? 15 : 10;
                    pickups.Add(new RuntimeMarker(child, MarkerKind.Point, pointValue));
                }
                else if (child.name.StartsWith("Runtime_Bot_", StringComparison.Ordinal))
                {
                    var participant = FindParticipant(child.name.Replace("Runtime_Bot_", string.Empty));
                    if (participant != null)
                    {
                        bots.Add(new RuntimeBot(child, participant, index * 0.37f));
                    }
                }
                else if (child.name.StartsWith("Runtime_Label_", StringComparison.Ordinal))
                {
                    labels.Add(child);
                }
            }

            BindParticipantLabels(root);
            BindPickupLabels(root);
        }

        private void EnsurePlayer()
        {
            var playerObject = GameObject.Find("MVP_Player");
            if (playerObject == null)
            {
                playerObject = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                playerObject.name = "MVP_Player";
                var capsuleCollider = playerObject.GetComponent<CapsuleCollider>();
                if (capsuleCollider != null)
                {
                    Destroy(capsuleCollider);
                }
            }

            player = playerObject.transform;
            if (mapBindings != null || player.position == Vector3.zero)
            {
                player.position = playerSpawn;
            }

            var controller = playerObject.GetComponent<CharacterController>();
            if (controller == null)
            {
                controller = playerObject.AddComponent<CharacterController>();
            }

            controller.height = 2f;
            controller.radius = 0.45f;
            controller.center = Vector3.zero;
            controller.slopeLimit = 45f;
            controller.stepOffset = 0.3f;
            controller.skinWidth = 0.05f;
            controller.minMoveDistance = 0f;

            playerController = playerObject.GetComponent<ChannelPlayerController>();
            if (playerController == null)
            {
                playerController = playerObject.AddComponent<ChannelPlayerController>();
            }

            ChannelPlayAssetRuntime.AttachPlayerVisual(playerObject.transform, teamBlueMaterial);
        }

        private void EnsureCamera()
        {
            gameplayCamera = Camera.main;
            if (gameplayCamera == null)
            {
                var cameraObject = new GameObject("Gameplay_Camera");
                cameraObject.tag = "MainCamera";
                gameplayCamera = cameraObject.AddComponent<Camera>();
                gameplayCamera.clearFlags = CameraClearFlags.SolidColor;
                gameplayCamera.backgroundColor = new Color(0.06f, 0.08f, 0.1f);
            }

            followCamera = gameplayCamera.GetComponent<ChannelFollowCamera>();
            if (followCamera == null)
            {
                followCamera = gameplayCamera.gameObject.AddComponent<ChannelFollowCamera>();
            }

            followCamera.SetTarget(player);

            cameraCutaway = gameplayCamera.GetComponent<ChannelCameraOccluderCutaway>();
            if (cameraCutaway == null)
            {
                cameraCutaway = gameplayCamera.gameObject.AddComponent<ChannelCameraOccluderCutaway>();
            }

            var mapRoot = GameObject.Find("TraitorEscape_Runtime_Map");
            cameraCutaway.Configure(player, mapRoot == null ? null : mapRoot.transform);

            manualTraversalRecorder = gameplayCamera.GetComponent<ChannelManualTraversalRecorder>();
            if (manualTraversalRecorder == null)
            {
                manualTraversalRecorder = gameplayCamera.gameObject.AddComponent<ChannelManualTraversalRecorder>();
            }

            manualTraversalRecorder.Configure(player, gameplayCamera, cameraCutaway);
        }

        private void EnsureAudio()
        {
            sfxSource = ChannelPlayAssetRuntime.EnsureAudioSource(gameObject);
        }

        private void HandlePickups()
        {
            if (player == null)
            {
                return;
            }

            foreach (var marker in pickups)
            {
                if (marker.Collected || marker.Transform == null)
                {
                    continue;
                }

                var distance = Vector3.Distance(player.position, marker.Transform.position);
                if (distance > 1.1f)
                {
                    continue;
                }

                marker.Collected = true;
                marker.Transform.gameObject.SetActive(false);

                if (marker.Kind == MarkerKind.Key)
                {
                    if (mapBindings != null && marker.KhufuKey.HasValue)
                    {
                        khufuObjectives.CollectPhysicalKey(marker.KhufuKey.Value);
                        keysCollected = khufuObjectives.PhysicalKeyCount;
                        objectiveReadout = khufuObjectives.BuildTerminalReadout();
                        lastEvent = marker.KhufuKey.Value + " key secured";
                    }
                    else
                    {
                        keysCollected = Mathf.Min(3, keysCollected + 1);
                        objectiveReadout = keysCollected >= 3 ? "All keys found. Go to the final door" : "Key secured. " + (3 - keysCollected) + " key(s) left";
                        lastEvent = "Key secured";
                    }
                    PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
                }
                else
                {
                    points += marker.PointValue;
                    pilotCollectedPoints = true;
                    objectiveReadout = "Points collected. Shop items are available";
                    lastEvent = "+" + marker.PointValue + " points";
                    PlaySfx(ChannelPlayAssetRuntime.PointGainEvent);
                }

                SyncLocalParticipant();
            }
        }

        private void HandleInteractionInput()
        {
            if (player == null)
            {
                return;
            }

            if (Input.GetKeyDown(KeyCode.Tab))
            {
                ToggleOperatorView();
            }

            if (operatorView)
            {
                if (Input.GetKeyDown(KeyCode.R))
                {
                    ResetSessionState();
                }

                if (Input.GetKeyDown(KeyCode.Escape))
                {
                    ToggleOperatorView();
                }

                return;
            }

            if (Input.GetKeyDown(KeyCode.B))
            {
                shopOpen = !shopOpen;
                pilotOpenedShop = pilotOpenedShop || shopOpen;
                PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
            }

            if (!Input.GetKeyDown(KeyCode.E))
            {
                return;
            }

            if (IsNear(shopTerminal, 2.2f))
            {
                shopOpen = !shopOpen;
                pilotOpenedShop = pilotOpenedShop || shopOpen;
                lastEvent = shopOpen ? "Shop opened" : "Shop closed";
                PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
            }
            else if (IsNear(missionTerminal, 2.2f))
            {
                AwardMissionPoints();
            }
            else if (IsNear(exitDoor, 2.5f))
            {
                TryOpenExit();
            }
        }

        private void HandleItemInput()
        {
            if (operatorView)
            {
                return;
            }

            if (shopOpen)
            {
                if (Input.GetKeyDown(KeyCode.Alpha1))
                {
                    BuyTruthPen();
                }

                if (Input.GetKeyDown(KeyCode.Alpha2))
                {
                    BuyScanner();
                }

                if (Input.GetKeyDown(KeyCode.Alpha3))
                {
                    BuySerum();
                }

                if (Input.GetKeyDown(KeyCode.Escape))
                {
                    shopOpen = false;
                    lastEvent = "Shop closed";
                }

                return;
            }

            if (Input.GetKeyDown(KeyCode.Alpha1))
            {
                UseTruthPen();
            }

            if (Input.GetKeyDown(KeyCode.Alpha2))
            {
                UseScanner();
            }

            if (Input.GetKeyDown(KeyCode.Alpha3))
            {
                UseDoppelgangerSerum();
            }
        }

        private void HandleOperatorCameraInput()
        {
            if (!operatorView || gameplayCamera == null)
            {
                return;
            }

            var pan = new Vector3(Input.GetAxisRaw("Horizontal"), 0f, Input.GetAxisRaw("Vertical"));
            pan = Vector3.ClampMagnitude(pan, 1f);

            var speed = Input.GetKey(KeyCode.LeftShift) ? OperatorFastMoveSpeed : OperatorMoveSpeed;
            var position = gameplayCamera.transform.position + pan * speed * Time.deltaTime;

            var keyboardZoom = 0f;
            if (Input.GetKey(KeyCode.Q))
            {
                keyboardZoom += 1f;
            }

            if (Input.GetKey(KeyCode.E))
            {
                keyboardZoom -= 1f;
            }

            var scrollZoom = -Input.GetAxis("Mouse ScrollWheel") * OperatorZoomSpeed;
            var heightBounds = mapBindings == null ? new Vector2(OperatorMinHeight, OperatorMaxHeight) : mapBindings.operatorHeightBounds;
            var xBounds = mapBindings == null ? new Vector2(-13f, 13f) : mapBindings.operatorXBounds;
            var zBounds = mapBindings == null ? new Vector2(-11f, 10f) : mapBindings.operatorZBounds;
            position.y = Mathf.Clamp(position.y + keyboardZoom * OperatorZoomSpeed * Time.deltaTime + scrollZoom, heightBounds.x, heightBounds.y);
            position.x = Mathf.Clamp(position.x, xBounds.x, xBounds.y);
            position.z = Mathf.Clamp(position.z, zBounds.x, zBounds.y);

            gameplayCamera.transform.position = position;
            gameplayCamera.transform.rotation = mapBindings == null
                ? Quaternion.Euler(70f, 0f, 0f)
                : Quaternion.Euler(90f, 0f, 0f);
        }

        private void AwardMissionPoints()
        {
            if (Time.time < nextMissionAvailableAt)
            {
                var secondsLeft = Mathf.CeilToInt(nextMissionAvailableAt - Time.time);
                lastEvent = "Mission terminal cooling down: " + secondsLeft + "s";
                return;
            }

            points += 20;
            pilotCollectedPoints = true;
            pilotRanMission = true;
            nextMissionAvailableAt = Time.time + MissionCooldownSeconds;
            objectiveReadout = "Mission clear. Spend points or keep searching keys";
            if (mapBindings != null)
            {
                khufuObjectives.ConfirmAtMissionTerminal();
                objectiveReadout = khufuObjectives.BuildTerminalReadout();
            }
            lastEvent = "Mission cleared: +20 points";
            PlaySfx(ChannelPlayAssetRuntime.PointGainEvent);
            SyncLocalParticipant();
        }

        private void TryOpenExit()
        {
            var extractionAuthorized = mapBindings == null ? keysCollected >= 3 : khufuObjectives.CanExtract;
            if (extractionAuthorized)
            {
                if (!exitOpened)
                {
                    exitOpened = true;
                    points += 50;
                    objectiveReadout = "Exit opened. Pilot objective complete";
                    ApplyMaterial(exitDoor.gameObject, openExitMaterial);
                    PlaySfx(ChannelPlayAssetRuntime.RoundEndEvent);
                    SyncLocalParticipant();
                }

                lastEvent = "Exit opened: pilot objective complete";
            }
            else
            {
                objectiveReadout = mapBindings == null
                    ? "Find " + (3 - keysCollected) + " more key(s)"
                    : khufuObjectives.BuildTerminalReadout();
                lastEvent = mapBindings != null && khufuObjectives.HasAllPhysicalKeys
                    ? "Exit locked: mission terminal confirmation required"
                    : "Exit locked: " + (3 - keysCollected) + " keys missing";
                PlaySfx(ChannelPlayAssetRuntime.WarningEvent);
            }
        }

        private void GrantPilotKeyAssist()
        {
            if (mapBindings != null)
            {
                lastEvent = "Operator key assist disabled for Khufu V5 physical-key acceptance";
                return;
            }

            if (keysCollected >= 3)
            {
                lastEvent = "All keys already secured";
                return;
            }

            keysCollected = Mathf.Min(3, keysCollected + 1);
            objectiveReadout = keysCollected >= 3 ? "Operator key assist complete. Go to final door" : "Operator key assist. " + (3 - keysCollected) + " key(s) left";
            lastEvent = "Operator granted key assist " + keysCollected + "/3";
            SyncLocalParticipant();
        }

        private void BuyTruthPen()
        {
            if (!SpendPoints(TruthPenCost))
            {
                return;
            }

            truthPens++;
            pilotBoughtItem = true;
            lastEvent = "Truth Pen purchased";
            PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
        }

        private void BuyScanner()
        {
            if (!SpendPoints(ScannerCost))
            {
                return;
            }

            scanners++;
            pilotBoughtItem = true;
            lastEvent = "Location Scanner purchased";
            PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
        }

        private void BuySerum()
        {
            if (!SpendPoints(SerumCost))
            {
                return;
            }

            serums++;
            pilotBoughtItem = true;
            lastEvent = "Doppelganger Serum purchased";
            PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
        }

        private bool SpendPoints(int cost)
        {
            if (points < cost)
            {
                lastEvent = "Not enough points";
                return false;
            }

            points -= cost;
            SyncLocalParticipant();
            return true;
        }

        private void UseTruthPen()
        {
            if (truthPens <= 0)
            {
                lastEvent = "No Truth Pen";
                return;
            }

            truthPens--;
            pilotUsedTruthPen = true;
            var suspect = participants[UnityEngine.Random.Range(1, participants.Count)];
            suspect.Revealed = true;
            truthReadout = suspect.Name + " is " + (suspect.IsTraitor ? "Traitor" : "Clear");
            lastEvent = "Truth Pen used";
            PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
        }

        private void UseScanner()
        {
            if (scanners <= 0)
            {
                lastEvent = "No Location Scanner";
                return;
            }

            scanners--;
            pilotUsedScanner = true;
            scannerReadout = BuildScannerReadout();
            ActivateScannerBeacon(lastScannerTarget);
            lastEvent = "Location Scanner used";
            PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
        }

        private void UseDoppelgangerSerum()
        {
            if (serums <= 0)
            {
                lastEvent = "No Doppelganger Serum";
                return;
            }

            serums--;
            pilotUsedSerum = true;
            doppelgangerUntil = Time.time + DoppelgangerSeconds;
            objectiveReadout = "Doppelganger disguise active for " + Mathf.RoundToInt(DoppelgangerSeconds) + "s";
            lastEvent = "Doppelganger active";
            PlaySfx(ChannelPlayAssetRuntime.InteractEvent);
        }

        private string BuildScannerReadout()
        {
            lastScannerTarget = null;

            if (player == null)
            {
                return "No player signal";
            }

            Transform closest = null;
            var closestDistance = float.MaxValue;

            foreach (var marker in pickups)
            {
                if (marker.Collected || marker.Kind != MarkerKind.Key || marker.Transform == null)
                {
                    continue;
                }

                var distance = Vector3.Distance(player.position, marker.Transform.position);
                if (distance < closestDistance)
                {
                    closestDistance = distance;
                    closest = marker.Transform;
                }
            }

            if (closest == null)
            {
                closest = exitDoor;
                closestDistance = exitDoor == null ? 0f : Vector3.Distance(player.position, exitDoor.position);
            }

            if (closest == null)
            {
                return "No target found";
            }

            lastScannerTarget = closest;
            var direction = closest.position - player.position;
            return closest.name + " " + closestDistance.ToString("0.0") + "m " + CardinalDirection(direction);
        }

        private static string CardinalDirection(Vector3 direction)
        {
            if (Mathf.Abs(direction.x) > Mathf.Abs(direction.z))
            {
                return direction.x >= 0f ? "East" : "West";
            }

            return direction.z >= 0f ? "North" : "South";
        }

        private void ToggleOperatorView()
        {
            operatorView = !operatorView;

            if (playerController != null)
            {
                playerController.enabled = !operatorView;
            }

            if (followCamera == null || gameplayCamera == null)
            {
                return;
            }

            if (operatorView)
            {
                pilotVisitedOperator = true;
                followCamera.SetTarget(null);
                gameplayCamera.transform.position = mapBindings == null ? new Vector3(0f, 20f, -2f) : mapBindings.operatorStart;
                gameplayCamera.transform.rotation = mapBindings == null
                    ? Quaternion.Euler(70f, 0f, 0f)
                    : Quaternion.Euler(90f, 0f, 0f);
                if (mapBindings != null)
                {
                    gameplayCamera.fieldOfView = KhufuOperatorFieldOfView;
                }
                lastEvent = "Operator view";
            }
            else
            {
                gameplayCamera.fieldOfView = ParticipantFieldOfView;
                followCamera.SetTarget(player);
                RespawnLocalPlayerIfNeeded();
                lastEvent = "Participant view";
            }
        }

        private void ResetSessionState()
        {
            points = StartingPoints;
            keysCollected = 0;
            khufuObjectives.Reset();
            truthPens = 0;
            scanners = 0;
            serums = 0;
            timeRemaining = SessionLengthSeconds;
            doppelgangerUntil = 0f;
            scannerBeaconUntil = 0f;
            nextMissionAvailableAt = 0f;
            shopOpen = false;
            exitOpened = false;
            scannerReadout = "Scanner idle";
            truthReadout = "Truth Pen idle";
            objectiveReadout = "Collect 3 keys, buy items, open the final door";
            interactionHint = "Move to pickups or terminals";
            pilotMoved = false;
            pilotCollectedPoints = false;
            pilotOpenedShop = false;
            pilotBoughtItem = false;
            pilotUsedTruthPen = false;
            pilotUsedScanner = false;
            pilotUsedSerum = false;
            pilotRanMission = false;
            pilotVisitedOperator = false;
            pilotOperatorGrantedPoints = false;
            pilotOperatorGrantedItems = false;

            foreach (var marker in pickups)
            {
                marker.Collected = false;
                if (marker.Transform != null)
                {
                    marker.Transform.gameObject.SetActive(true);
                    marker.Transform.position = marker.BasePosition;
                }
            }

            ResetParticipantStates();
            RespawnLocalPlayerIfNeeded(forceSpawn: true);

            if (exitDoor != null)
            {
                exitDoor.position = exitClosedPosition;
                ApplyMaterial(exitDoor.gameObject, exitMaterial);
            }

            if (scannerBeacon != null)
            {
                scannerBeacon.gameObject.SetActive(false);
            }

            SyncLocalParticipant();
            lastEvent = "Session reset";
        }

        private void ResetParticipantStates()
        {
            for (var index = 0; index < participants.Count; index++)
            {
                var participant = participants[index];
                participant.Revealed = false;
                participant.Points = index == 0 ? StartingPoints : 30;
            }

            if (participants.Count > 0)
            {
                participants[0].Status = "Active";
            }

            if (participants.Count > 1)
            {
                participants[1].Status = "Searching";
            }

            if (participants.Count > 2)
            {
                participants[2].Status = "At shop";
            }

            if (participants.Count > 3)
            {
                participants[3].Status = "Hidden";
            }

            if (participants.Count > 4)
            {
                participants[4].Status = "Searching";
            }

            if (participants.Count > 5)
            {
                participants[5].Status = "Guarding";
            }

            if (participants.Count > 6)
            {
                participants[6].Status = "Searching";
            }

            if (participants.Count > 7)
            {
                participants[7].Status = "Watching exit";
            }
        }

        private void RespawnLocalPlayerIfNeeded(bool forceSpawn = false)
        {
            if (player == null)
            {
                return;
            }

            if (!forceSpawn && player.position.y > -2f)
            {
                return;
            }

            var controller = player.GetComponent<CharacterController>();
            if (controller != null)
            {
                controller.enabled = false;
            }

            player.position = playerSpawn;

            if (controller != null)
            {
                controller.enabled = true;
            }
        }

        private void UpdatePilotReadiness()
        {
            if (player == null)
            {
                interactionHint = "Waiting for local player";
                return;
            }

            if (Vector3.Distance(player.position, playerSpawn) > 1.6f)
            {
                pilotMoved = true;
            }

            interactionHint = BuildInteractionHint();
        }

        private string BuildInteractionHint()
        {
            if (operatorView)
            {
                return "Operator view active";
            }

            if (IsNear(missionTerminal, 2.2f))
            {
                return Time.time < nextMissionAvailableAt ? "Mission terminal cooling down" : "Press E for mission +20";
            }

            if (IsNear(shopTerminal, 2.2f))
            {
                return shopOpen ? "Shop open: press 1/2/3 to buy" : "Press E to open shop";
            }

            if (IsNear(exitDoor, 2.5f))
            {
                return keysCollected >= 3 ? "Press E to open final door" : "Final door needs " + (3 - keysCollected) + " key(s)";
            }

            var nearbyMarker = FindNearbyUncollectedMarker(2.4f);
            if (nearbyMarker != null)
            {
                return nearbyMarker.Kind == MarkerKind.Key ? "Key nearby" : "Point pickup nearby";
            }

            return "Find keys, earn points, or visit terminals";
        }

        private RuntimeMarker FindNearbyUncollectedMarker(float radius)
        {
            RuntimeMarker closest = null;
            var closestDistance = radius;

            foreach (var marker in pickups)
            {
                if (marker.Collected || marker.Transform == null)
                {
                    continue;
                }

                var distance = Vector3.Distance(player.position, marker.Transform.position);
                if (distance <= closestDistance)
                {
                    closest = marker;
                    closestDistance = distance;
                }
            }

            return closest;
        }

        private void RefreshPlayerVisual()
        {
            if (player == null)
            {
                return;
            }

            var renderer = player.GetComponentInChildren<Renderer>();
            if (renderer == null)
            {
                return;
            }

            renderer.sharedMaterial = Time.time < doppelgangerUntil ? teamRedMaterial : teamBlueMaterial;
        }

        private void AnimatePickups()
        {
            foreach (var marker in pickups)
            {
                if (marker.Collected || marker.Transform == null)
                {
                    continue;
                }

                marker.Transform.Rotate(Vector3.up, 70f * Time.deltaTime, Space.World);
                var basePosition = marker.BasePosition;
                basePosition.y += Mathf.Sin(Time.time * 2.5f) * 0.12f;
                marker.Transform.position = basePosition;
            }
        }

        private void AnimateBots()
        {
            foreach (var bot in bots)
            {
                if (bot.Transform == null)
                {
                    continue;
                }

                var offset = new Vector3(Mathf.Sin(Time.time * 0.55f + bot.Phase) * 0.45f, 0f, Mathf.Cos(Time.time * 0.45f + bot.Phase) * 0.35f);
                bot.Transform.position = bot.BasePosition + offset;
                bot.Participant.LastKnownPosition = bot.Transform.position;

                var look = new Vector3(offset.x, 0f, offset.z);
                if (look.sqrMagnitude > 0.01f)
                {
                    bot.Transform.rotation = Quaternion.LookRotation(look);
                }
            }
        }

        private void UpdateScannerBeacon()
        {
            if (scannerBeacon == null)
            {
                return;
            }

            var active = Time.time < scannerBeaconUntil;
            if (scannerBeacon.gameObject.activeSelf != active)
            {
                scannerBeacon.gameObject.SetActive(active);
            }

            if (!active)
            {
                return;
            }

            var pulse = 0.8f + Mathf.Sin(Time.time * 8f) * 0.18f;
            scannerBeacon.localScale = new Vector3(pulse, 0.08f, pulse);
        }

        private void UpdateExitDoor()
        {
            if (exitDoor == null || !exitOpened)
            {
                return;
            }

            exitDoor.position = Vector3.Lerp(exitDoor.position, exitOpenPosition, Time.deltaTime * 2.2f);
        }

        private void FaceLabelsToCamera()
        {
            if (gameplayCamera == null)
            {
                return;
            }

            foreach (var binding in labelBindings)
            {
                if (binding.Label == null || binding.Target == null)
                {
                    continue;
                }

                binding.Label.position = binding.Target.position + binding.Offset;
            }

            foreach (var label in labels)
            {
                if (label == null)
                {
                    continue;
                }

                label.rotation = Quaternion.LookRotation(label.position - gameplayCamera.transform.position);
            }
        }

        private void BindParticipantLabels(Transform root)
        {
            foreach (var bot in bots)
            {
                var label = root.Find("Runtime_Label_" + bot.Participant.Name);
                if (label != null)
                {
                    labelBindings.Add(new RuntimeLabelBinding(label, bot.Transform, Vector3.up * 1.35f));
                }
            }
        }

        private void BindPickupLabels(Transform root)
        {
            foreach (var marker in pickups)
            {
                if (marker.Transform == null)
                {
                    continue;
                }

                var label = root.Find("Runtime_Label_" + marker.Transform.name);
                if (label != null)
                {
                    labelBindings.Add(new RuntimeLabelBinding(label, marker.Transform, Vector3.up * 0.75f));
                }
            }
        }

        private void ActivateScannerBeacon(Transform target)
        {
            if (scannerBeacon == null || target == null)
            {
                return;
            }

            scannerBeacon.position = new Vector3(target.position.x, 0.12f, target.position.z);
            scannerBeaconUntil = Time.time + ScannerBeaconSeconds;
            scannerBeacon.gameObject.SetActive(true);
        }

        private bool IsNear(Transform target, float radius)
        {
            return target != null && player != null && Vector3.Distance(player.position, target.position) <= radius;
        }

        private void SyncLocalParticipant()
        {
            if (participants.Count == 0)
            {
                return;
            }

            participants[0].Points = points;
            participants[0].Status = keysCollected >= 3 ? "Exit-ready" : "Active";
            participants[0].LastKnownPosition = player == null ? participants[0].LastKnownPosition : player.position;

            if (exitOpened)
            {
                participants[0].Status = "Escaped";
            }
        }

        private ParticipantState FindParticipant(string participantName)
        {
            foreach (var participant in participants)
            {
                if (participant.Name == participantName)
                {
                    return participant;
                }
            }

            return null;
        }

        private bool IsPilotReady()
        {
            return pilotMoved
                && pilotCollectedPoints
                && keysCollected >= 3
                && pilotOpenedShop
                && pilotBoughtItem
                && HasUsedAllItems()
                && pilotRanMission
                && exitOpened
                && pilotVisitedOperator
                && pilotOperatorGrantedPoints
                && pilotOperatorGrantedItems;
        }

        private bool HasUsedAllItems()
        {
            return pilotUsedTruthPen && pilotUsedScanner && pilotUsedSerum;
        }

        private string BuildPilotNextStep()
        {
            if (!pilotMoved)
            {
                return "Next: move in the 3D map";
            }

            if (!pilotCollectedPoints)
            {
                return "Next: earn points from pickups or mission";
            }

            if (keysCollected < 3)
            {
                return "Next: collect " + (3 - keysCollected) + " key(s)";
            }

            if (!pilotOpenedShop)
            {
                return "Next: open shop";
            }

            if (!pilotBoughtItem)
            {
                return "Next: buy at least one shop item";
            }

            if (!pilotUsedTruthPen)
            {
                return "Next: use Truth Pen";
            }

            if (!pilotUsedScanner)
            {
                return "Next: use Location Scanner";
            }

            if (!pilotUsedSerum)
            {
                return "Next: use Doppelganger Serum";
            }

            if (!pilotRanMission)
            {
                return "Next: run mission terminal";
            }

            if (!exitOpened)
            {
                return "Next: open final door";
            }

            if (!pilotVisitedOperator)
            {
                return "Next: switch to operator view";
            }

            if (!pilotOperatorGrantedPoints)
            {
                return "Next: operator grant points";
            }

            if (!pilotOperatorGrantedItems)
            {
                return "Next: operator grant item pack";
            }

            return "Ready: OBS pilot take can be recorded";
        }

        private void DrawHud()
        {
            var width = Mathf.Min(380f, Screen.width - 24f);
            var height = 354f;
            GUI.Box(new Rect(12f, 12f, width, height), "Traitor Escape MVP");
            GUI.Label(new Rect(24f, 42f, width - 24f, 22f), "Time " + FormatTime(timeRemaining), titleStyle);
            GUI.Label(new Rect(24f, 68f, width - 24f, 22f), "Team Blue / Role Participant", labelStyle);
            GUI.Label(new Rect(24f, 92f, width - 24f, 22f), "Points " + points + " / Keys " + keysCollected + "/3 / Exit " + (exitOpened ? "OPEN" : "LOCKED"), labelStyle);
            GUI.Label(new Rect(24f, 116f, width - 24f, 22f), "Items 1:TP " + truthPens + " / 2:Scan " + scanners + " / 3:Serum " + serums, labelStyle);
            GUI.Label(new Rect(24f, 140f, width - 24f, 22f), "Pilot Ready " + (IsPilotReady() ? "YES" : "NO"), labelStyle);
            GUI.Label(new Rect(24f, 164f, width - 24f, 22f), "E interact / B shop / Tab operator / Shift sprint", smallStyle);
            GUI.Label(new Rect(24f, 188f, width - 24f, 22f), objectiveReadout, smallStyle);
            GUI.Label(new Rect(24f, 212f, width - 24f, 22f), scannerReadout, smallStyle);
            GUI.Label(new Rect(24f, 236f, width - 24f, 22f), truthReadout, smallStyle);
            GUI.Label(new Rect(24f, 260f, width - 24f, 22f), lastEvent, smallStyle);
            GUI.Label(new Rect(24f, 284f, width - 24f, 22f), BuildPilotNextStep(), smallStyle);
            GUI.Label(new Rect(24f, 308f, width - 24f, 22f), interactionHint, smallStyle);
            GUI.Label(new Rect(24f, 332f, width - 24f, 22f), BuildManualTraversalRecorderStatus(), smallStyle);
        }

        private string BuildManualTraversalRecorderStatus()
        {
            return manualTraversalRecorder == null ? "Manual traversal capture waiting for camera" : manualTraversalRecorder.StatusLine;
        }

        private void DrawScoreboard()
        {
            var width = Mathf.Min(300f, Screen.width - 24f);
            var left = Mathf.Max(12f, Screen.width - width - 12f);
            GUI.Box(new Rect(left, 12f, width, 536f), "Scoreboard / Pilot Check");

            for (var index = 0; index < participants.Count; index++)
            {
                var participant = participants[index];
                var y = 42f + index * 24f;
                var role = participant.Revealed ? (participant.IsTraitor ? " Traitor" : " Clear") : string.Empty;
                GUI.Label(new Rect(left + 12f, y, width - 24f, 22f), participant.Name + " " + participant.Team + " " + participant.Points + "p " + participant.Status + role, smallStyle);
            }

            var checklistTop = 244f;
            DrawChecklistLine(left + 12f, checklistTop, pilotMoved, "Move in 3D map");
            DrawChecklistLine(left + 12f, checklistTop + 20f, pilotCollectedPoints, "Earn points");
            DrawChecklistLine(left + 12f, checklistTop + 40f, keysCollected >= 3, "Collect 3 keys");
            DrawChecklistLine(left + 12f, checklistTop + 60f, pilotOpenedShop, "Open shop");
            DrawChecklistLine(left + 12f, checklistTop + 80f, pilotBoughtItem, "Buy an item");
            DrawChecklistLine(left + 12f, checklistTop + 100f, pilotUsedTruthPen, "Use Truth Pen");
            DrawChecklistLine(left + 12f, checklistTop + 120f, pilotUsedScanner, "Use Scanner");
            DrawChecklistLine(left + 12f, checklistTop + 140f, pilotUsedSerum, "Use Serum");
            DrawChecklistLine(left + 12f, checklistTop + 160f, pilotRanMission, "Run mission");
            DrawChecklistLine(left + 12f, checklistTop + 180f, exitOpened, "Open final door");
            DrawChecklistLine(left + 12f, checklistTop + 200f, pilotVisitedOperator, "Check operator view");
            DrawChecklistLine(left + 12f, checklistTop + 220f, pilotOperatorGrantedPoints, "Operator grant points");
            DrawChecklistLine(left + 12f, checklistTop + 240f, pilotOperatorGrantedItems, "Operator grant items");
            DrawChecklistLine(left + 12f, checklistTop + 260f, IsPilotReady(), "Pilot ready for OBS");
        }

        private void DrawChecklistLine(float left, float top, bool complete, string text)
        {
            GUI.Label(new Rect(left, top, 260f, 18f), (complete ? "[x] " : "[ ] ") + text, smallStyle);
        }

        private void DrawShop()
        {
            var width = Mathf.Min(360f, Screen.width - 24f);
            var left = SecondaryPanelLeft(width);
            var top = 12f;
            GUI.Box(new Rect(left, top, width, 202f), "Shop");
            GUI.Label(new Rect(left + 16f, top + 18f, width - 32f, 18f), "Press 1/2/3 or click to buy", smallStyle);

            if (GUI.Button(new Rect(left + 16f, top + 36f, width - 32f, 34f), "Buy Truth Pen - " + TruthPenCost))
            {
                BuyTruthPen();
            }

            if (GUI.Button(new Rect(left + 16f, top + 78f, width - 32f, 34f), "Buy Location Scanner - " + ScannerCost))
            {
                BuyScanner();
            }

            if (GUI.Button(new Rect(left + 16f, top + 120f, width - 32f, 34f), "Buy Doppelganger Serum - " + SerumCost))
            {
                BuySerum();
            }

            if (GUI.Button(new Rect(left + 16f, top + 162f, width - 32f, 28f), "Close"))
            {
                shopOpen = false;
            }
        }

        private void DrawOperatorPanel()
        {
            var width = Mathf.Min(300f, Screen.width - 24f);
            var left = SecondaryPanelLeft(width);
            var height = 314f;
            var top = 12f;
            GUI.Box(new Rect(left, top, width, height), "Operator");
            GUI.Label(new Rect(left + 16f, top + 18f, width - 32f, 18f), "WASD pan / Q E zoom / R reset", smallStyle);

            if (GUI.Button(new Rect(left + 16f, top + 36f, width - 32f, 32f), "Grant P1 +25"))
            {
                points += 25;
                pilotOperatorGrantedPoints = true;
                lastEvent = "Operator granted +25";
                SyncLocalParticipant();
            }

            if (GUI.Button(new Rect(left + 16f, top + 76f, width - 32f, 32f), "Grant P1 Key Assist"))
            {
                GrantPilotKeyAssist();
            }

            if (GUI.Button(new Rect(left + 16f, top + 116f, width - 32f, 32f), "Grant Item Pack"))
            {
                truthPens++;
                scanners++;
                serums++;
                pilotOperatorGrantedItems = true;
                lastEvent = "Operator granted item pack";
            }

            if (GUI.Button(new Rect(left + 16f, top + 156f, width - 32f, 32f), "Reveal Roles"))
            {
                foreach (var participant in participants)
                {
                    participant.Revealed = true;
                }

                truthReadout = "Operator revealed all roles";
                lastEvent = "Roles revealed";
            }

            if (GUI.Button(new Rect(left + 16f, top + 196f, width - 32f, 32f), "Reset 35m Timer"))
            {
                timeRemaining = SessionLengthSeconds;
                lastEvent = "Timer reset";
            }

            if (GUI.Button(new Rect(left + 16f, top + 236f, width - 32f, 28f), "Return Participant Camera"))
            {
                ToggleOperatorView();
            }

            if (GUI.Button(new Rect(left + 16f, top + 272f, width - 32f, 28f), "Reset MVP Session"))
            {
                ResetSessionState();
            }
        }

        private static float SecondaryPanelLeft(float panelWidth)
        {
            var hudWidth = Mathf.Min(380f, Screen.width - 24f);
            var scoreboardWidth = Mathf.Min(300f, Screen.width - 24f);
            var availableLeft = 12f + hudWidth + 12f;
            var availableRight = Screen.width - scoreboardWidth - 24f;
            var availableWidth = availableRight - availableLeft;
            return availableWidth >= panelWidth
                ? availableLeft + (availableWidth - panelWidth) * 0.5f
                : Mathf.Max(12f, (Screen.width - panelWidth) * 0.5f);
        }

        private void EnsureGuiStyles()
        {
            if (labelStyle != null)
            {
                return;
            }

            labelStyle = new GUIStyle(GUI.skin.label);
            labelStyle.fontSize = 14;
            labelStyle.normal.textColor = Color.white;

            smallStyle = new GUIStyle(GUI.skin.label);
            smallStyle.fontSize = 12;
            smallStyle.normal.textColor = Color.white;

            titleStyle = new GUIStyle(GUI.skin.label);
            titleStyle.fontSize = 16;
            titleStyle.fontStyle = FontStyle.Bold;
            titleStyle.normal.textColor = Color.white;
        }

        private static string FormatTime(float seconds)
        {
            var span = TimeSpan.FromSeconds(Mathf.Max(0f, seconds));
            return span.Minutes.ToString("00") + ":" + span.Seconds.ToString("00");
        }

        private static GameObject CreateCube(string name, Transform parent, Vector3 position, Vector3 scale, Material material)
        {
            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = name;
            cube.transform.SetParent(parent);
            cube.transform.position = position;
            cube.transform.localScale = scale;
            ApplyMaterial(cube, material);
            return cube;
        }

        private void AddPillar(Transform parent, string name, Vector3 position, float height)
        {
            var pillar = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            pillar.name = name;
            pillar.transform.SetParent(parent);
            pillar.transform.position = position;
            pillar.transform.localScale = new Vector3(0.42f, height * 0.5f, 0.42f);
            ApplyMaterial(pillar, wallMaterial);

            CreateCube(name + "_Base", parent, position + Vector3.down * (height * 0.5f - 0.12f), new Vector3(1.05f, 0.24f, 1.05f), propMaterial);
            CreateCube(name + "_Cap", parent, position + Vector3.up * (height * 0.5f + 0.12f), new Vector3(1.05f, 0.24f, 1.05f), propMaterial);
        }

        private void AddVase(Transform parent, string name, Vector3 position)
        {
            var vase = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            vase.name = name;
            vase.transform.SetParent(parent);
            vase.transform.position = position;
            vase.transform.localScale = new Vector3(0.22f, 0.45f, 0.22f);
            ApplyMaterial(vase, propMaterial);
        }

        private void CreateRuntimeParticipants(Transform parent)
        {
            bots.Clear();

            for (var index = 1; index < participants.Count; index++)
            {
                var participant = participants[index];
                var bot = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                bot.name = "Runtime_Bot_" + participant.Name;
                bot.transform.SetParent(parent);
                bot.transform.position = participant.LastKnownPosition;
                bot.transform.localScale = new Vector3(0.8f, 1f, 0.8f);
                ApplyMaterial(bot, participant.Team == "Blue" ? teamBlueMaterial : teamRedMaterial);
                ChannelPlayAssetRuntime.AttachContestantVisual(bot.transform, participant.Team == "Blue" ? teamBlueMaterial : teamRedMaterial);

                var collider = bot.GetComponent<Collider>();
                if (collider != null)
                {
                    collider.isTrigger = true;
                }

                CreateLabel(parent, "Runtime_Label_" + participant.Name, participant.Name, participant.LastKnownPosition + Vector3.up * 1.35f, Color.white, bot.transform);
                bots.Add(new RuntimeBot(bot.transform, participant, index * 0.61f));
            }
        }

        private void CreateLabel(Transform parent, string name, string text, Vector3 position, Color color, Transform followTarget = null, Vector3? followOffset = null)
        {
            var labelObject = new GameObject(name);
            labelObject.transform.SetParent(parent);
            labelObject.transform.position = position;

            var textMesh = labelObject.AddComponent<TextMesh>();
            textMesh.text = text;
            textMesh.anchor = TextAnchor.MiddleCenter;
            textMesh.alignment = TextAlignment.Center;
            textMesh.characterSize = 0.28f;
            textMesh.fontSize = 48;
            textMesh.color = color;

            if (followTarget != null)
            {
                labelBindings.Add(new RuntimeLabelBinding(labelObject.transform, followTarget, followOffset ?? Vector3.up * 1.35f));
            }

            labels.Add(labelObject.transform);
        }

        private void CreatePickup(Transform parent, MarkerKind kind, string name, Vector3 position, int pointValue)
        {
            var primitiveType = kind == MarkerKind.Key ? PrimitiveType.Cylinder : PrimitiveType.Sphere;
            var pickup = GameObject.CreatePrimitive(primitiveType);
            pickup.name = name;
            pickup.transform.SetParent(parent);
            pickup.transform.position = position;
            pickup.transform.localScale = kind == MarkerKind.Key ? new Vector3(0.28f, 0.18f, 0.28f) : new Vector3(0.55f, 0.55f, 0.55f);

            var collider = pickup.GetComponent<Collider>();
            if (collider != null)
            {
                collider.isTrigger = true;
            }

            ApplyMaterial(pickup, kind == MarkerKind.Key ? keyMaterial : pointMaterial);
            CreateLabel(parent, "Runtime_Label_" + name, kind == MarkerKind.Key ? "KEY" : "+" + pointValue, position + Vector3.up * 0.75f, Color.white, pickup.transform, Vector3.up * 0.75f);
            pickups.Add(new RuntimeMarker(pickup.transform, kind, pointValue, ParseKhufuKey(name)));
        }

        public int DiagnosticPhysicalKeyCount => mapBindings == null ? keysCollected : khufuObjectives.PhysicalKeyCount;
        public bool DiagnosticTerminalConfirmed => mapBindings != null && khufuObjectives.TerminalConfirmed;
        public bool DiagnosticCanExtract => mapBindings == null ? keysCollected >= 3 : khufuObjectives.CanExtract;
        public Transform DiagnosticPlayer => player;
        public bool DiagnosticHasAuthoredBindings => mapBindings != null;
        public bool DiagnosticShopIsBound => shopTerminal != null;
        public Vector3 DiagnosticPlayerSpawn => playerSpawn;

        public void DiagnosticResetObjectives()
        {
            keysCollected = 0;
            khufuObjectives.Reset();
            exitOpened = false;
        }

        public bool DiagnosticCollectKey(KhufuKeyId key)
        {
            if (mapBindings == null)
            {
                return false;
            }

            var changed = khufuObjectives.CollectPhysicalKey(key);
            keysCollected = khufuObjectives.PhysicalKeyCount;
            return changed;
        }

        public bool DiagnosticConfirmMissionTerminal()
        {
            return mapBindings != null && khufuObjectives.ConfirmAtMissionTerminal();
        }

        public void DiagnosticPrepareVisualProof(bool completedObjectives, bool showShop, bool showOperator)
        {
            if (operatorView != showOperator)
            {
                ToggleOperatorView();
            }

            DiagnosticResetObjectives();
            if (completedObjectives && mapBindings != null)
            {
                DiagnosticCollectKey(KhufuKeyId.Sun);
                DiagnosticCollectKey(KhufuKeyId.Crown);
                DiagnosticCollectKey(KhufuKeyId.Earth);
                DiagnosticConfirmMissionTerminal();
                TryOpenExit();
                pilotRanMission = true;
            }

            shopOpen = showShop;
            pilotOpenedShop = pilotOpenedShop || showShop;
        }

        private static KhufuKeyId? ParseKhufuKey(string objectName)
        {
            return KhufuObjectiveState.TryParseKeyName(objectName, out var key) ? key : (KhufuKeyId?)null;
        }

        private void PlaySfx(string eventName)
        {
            ChannelPlayAssetRuntime.PlaySfx(sfxSource, eventName);
        }

        private static void ApplyMaterial(GameObject target, Material material)
        {
            var renderer = target.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.sharedMaterial = material;
            }
        }

        private static Material CreateRuntimeMaterial(string name, Color color)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }

            if (shader == null)
            {
                shader = Shader.Find("Diffuse");
            }

            var material = new Material(shader)
            {
                name = name
            };

            if (material.HasProperty("_BaseColor"))
            {
                material.SetColor("_BaseColor", color);
            }

            if (material.HasProperty("_Color"))
            {
                material.color = color;
            }

            return material;
        }

        private enum MarkerKind
        {
            Key,
            Point
        }

        private sealed class RuntimeMarker
        {
            public RuntimeMarker(Transform transform, MarkerKind kind, int pointValue, KhufuKeyId? khufuKey = null)
            {
                Transform = transform;
                Kind = kind;
                PointValue = pointValue;
                BasePosition = transform.position;
                KhufuKey = khufuKey;
            }

            public Transform Transform { get; }
            public MarkerKind Kind { get; }
            public int PointValue { get; }
            public Vector3 BasePosition { get; }
            public KhufuKeyId? KhufuKey { get; }
            public bool Collected { get; set; }
        }

        private sealed class RuntimeBot
        {
            public RuntimeBot(Transform transform, ParticipantState participant, float phase)
            {
                Transform = transform;
                Participant = participant;
                BasePosition = transform.position;
                Phase = phase;
            }

            public Transform Transform { get; }
            public ParticipantState Participant { get; }
            public Vector3 BasePosition { get; }
            public float Phase { get; }
        }

        private sealed class RuntimeLabelBinding
        {
            public RuntimeLabelBinding(Transform label, Transform target, Vector3 offset)
            {
                Label = label;
                Target = target;
                Offset = offset;
            }

            public Transform Label { get; }
            public Transform Target { get; }
            public Vector3 Offset { get; }
        }

        private sealed class ParticipantState
        {
            public ParticipantState(string name, string team, bool isTraitor, string status, int points, Vector3 lastKnownPosition)
            {
                Name = name;
                Team = team;
                IsTraitor = isTraitor;
                Status = status;
                Points = points;
                LastKnownPosition = lastKnownPosition;
            }

            public string Name { get; }
            public string Team { get; }
            public bool IsTraitor { get; }
            public string Status { get; set; }
            public int Points { get; set; }
            public bool Revealed { get; set; }
            public Vector3 LastKnownPosition { get; set; }
        }
    }
}

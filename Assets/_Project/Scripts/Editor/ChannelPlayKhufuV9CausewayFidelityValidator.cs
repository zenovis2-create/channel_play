using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV9CausewayFidelityValidator
{
    private const string FrozenV5BuilderSha = "0a9f7a1f071db40fbab05e955e41acfbfa98c6b22aa7ee9d059f454392184faf";
    private const string FrozenV5ValidatorSha = "405573071d52ef12fa816cf230e51bab11e2f2cda2f7dfe7e708a7b99fbc5ebd";
    private const string FrozenV6BuilderSha = "ffa6fa51a20074760181db6c87319f2aad5afca443e37f80da657b17759c75f2";
    private const string FrozenV6ValidatorSha = "6ab23d70ce11c8c8e69352937150599352a821db55426e150935e0fec2a3cf1c";
    private const string FrozenV7BuilderSha = "3d7cd2f0542d2b3755ce449433b2c00e5a2261bcbe2df050401a0b8af77429f6";
    private const string FrozenV7ValidatorSha = "746130bbd87310bcad04be5914d5622cbed7a8cf3c84d29d95fb0002bf802a08";
    private const string FrozenV8PipelineSha = "4c87062eb1ecc9e3b64580cb5c705dfd952f07fb94961f18cf51058c158ef163";
    private const string FrozenV8BuilderSha = "abf2726a9e7e1730f39bebf4b190b7ed97a7675c3c3af35142cf9044cf53c55b";
    private const string FrozenV8ValidatorSha = "87c2fda947d591896d5a1813625be03424f6d79cea482cc6179162eb3bf3e68e";
    private const string FrozenV8ProbeSha = "81a7617eed79e0f189af606b7aa0985387ada61ba3e2767d3c1749153e4c0f59";
    private const string FrozenManifestSha = "7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38";
    private const string FrozenLockSha = "d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e";
    private const string FrozenSourceSha = "234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d";
    private const string FrozenSourceMetaSha = "6457410564068ea13f962237a9178321e5e608f4f5a482f68eeea4b064e2d094";
    private const string FrozenV6RootSignature = "b41580ea2636838635ac54cacf2f20f34224b39bb32a506d223bbcfc2476d530";
    private const string FrozenV7RootSignature = "9730013ededc08da590b99de5d2bd1ae91c485b25d67e6c591117d4431c2d321";
    private const string FrozenV8Signature = "be64fa8b33e798093d55087fc279377446e6e5556e059ad273aeaf1d87ccdfa4";

    private const int ExpectedRootRenderers = 5;
    private const int ExpectedRootVertices = 1512;
    private const int ExpectedRootTriangles = 756;
    private const int ExpectedRootColliders = 23;
    private const int ExpectedMapRenderers = 818;
    private const int ExpectedMapVertices = 59030;
    private const int ExpectedMapTriangles = 44540;
    private const int ExpectedMapColliders = 464;
    private const float PairTolerance = 0.05f;

    private static readonly Dictionary<string, string> ExpectedMaterials = new Dictionary<string, string>(StringComparer.Ordinal)
    {
        { ChannelPlayKhufuV9CausewayMeshPipeline.BasaltBucket, "V6_Basalt_Court" },
        { ChannelPlayKhufuV9CausewayMeshPipeline.LimestoneBucket, "V6_Causeway_Limestone" },
        { ChannelPlayKhufuV9CausewayMeshPipeline.RedGraniteBucket, "V6_Red_Granite" },
        { ChannelPlayKhufuV9CausewayMeshPipeline.TuraBucket, "V6_Tura_Casing" },
        { ChannelPlayKhufuV9CausewayMeshPipeline.InlayBucket, "V6_Scan_Inlay" }
    };

    [MenuItem("Channel Play/Khufu V9/Run All Static Gates")]
    public static void RunAllStaticGates()
    {
        ValidateMenu();
        ValidateIdempotence();
        ValidatePairMutation();
        ValidateGrayboxMutation();
        Debug.Log("CHANNEL_PLAY_KHUFU_V9_STATIC_GATES result=passed");
    }

    public static void RunAllStaticGatesBatch()
    {
        try
        {
            RunAllStaticGates();
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }

    [MenuItem("Channel Play/Khufu V9/Validate Causeway Fidelity")]
    public static void ValidateMenu()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV9CausewayFidelityBuilder.ScenePath, OpenSceneMode.Single);
        var result = ValidateScene();
        WriteValidation(result);
        if (!result.Passed)
            throw new InvalidOperationException("Khufu V9 validation failed: " + string.Join("; ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V9_VALIDATE result=passed signature=" + result.Signature);
    }

    [MenuItem("Channel Play/Khufu V9/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV9CausewayFidelityBuilder.RunRoot);
        ChannelPlayKhufuV9CausewayFidelityBuilder.Rebuild();
        var first = ValidateScene();
        var firstAssets = GeneratedAssetBindings();
        ChannelPlayKhufuV9CausewayFidelityBuilder.Rebuild();
        var second = ValidateScene();
        var secondAssets = GeneratedAssetBindings();
        var passed = first.Passed && second.Passed && first.Signature == second.Signature &&
                     Same(first.RootMetrics, second.RootMetrics) && firstAssets.SequenceEqual(secondAssets);

        var text = new StringBuilder("# Khufu V9 Rebuild Idempotence\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- First signature: `" + first.Signature + "`");
        text.AppendLine("- Second signature: `" + second.Signature + "`");
        text.AppendLine("- First metrics: `" + MetricsToken(first.RootMetrics) + "`");
        text.AppendLine("- Second metrics: `" + MetricsToken(second.RootMetrics) + "`");
        text.AppendLine("- Stable generated mesh bindings: `" + firstAssets.Count + "`");
        text.AppendLine();
        text.AppendLine("V9_IDEMPOTENCE: " + (passed ? "passed" : "failed"));
        File.WriteAllText(RunPath("idempotence.md"), text.ToString());
        if (!passed) throw new InvalidOperationException("Khufu V9 idempotence failed.");
    }

    [MenuItem("Channel Play/Khufu V9/Validate Structural Pair Mutation")]
    public static void ValidatePairMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV9CausewayFidelityBuilder.ScenePath, OpenSceneMode.Single);
        var root = FindRoot();
        var proxies = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.CollisionRootName);
        var target = proxies.Cast<Transform>().OrderBy(item => item.name, StringComparer.Ordinal).First();
        var original = target.position;
        target.position += Vector3.forward * 0.25f;
        var mutated = ValidateScene(false);
        target.position = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("pair bounds", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("pair-mutation.md", "Offset " + target.name + " by +0.25m world Z", mutated.Failures, rejected, "V9_PAIR_MUTATION");
        if (!rejected) throw new InvalidOperationException("V9 structural-pair mutation was not rejected.");
    }

    [MenuItem("Channel Play/Khufu V9/Validate Graybox Mutation")]
    public static void ValidateGrayboxMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV9CausewayFidelityBuilder.ScenePath, OpenSceneMode.Single);
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName).transform;
        var target = ChannelPlayKhufuV9CausewayFidelityBuilder.CollectSupersededRenderers(map).First();
        var original = target.enabled;
        target.enabled = true;
        var mutated = ValidateScene(false);
        target.enabled = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("superseded graybox", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("graybox-mutation.md", "Re-enable " + target.name, mutated.Failures, rejected, "V9_GRAYBOX_MUTATION");
        if (!rejected) throw new InvalidOperationException("V9 graybox mutation was not rejected.");
    }

    private static ValidationResult ValidateScene(bool validateFrozenAssets = true)
    {
        var result = new ValidationResult();
        if (validateFrozenAssets) ValidateFrozenInputs(result);
        var mapObject = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        if (mapObject == null)
        {
            result.Failures.Add("Shared map root missing");
            return Finish(result, null);
        }

        var map = mapObject.transform;
        var roots = map.Cast<Transform>().Where(item => item.name == ChannelPlayKhufuV9CausewayFidelityBuilder.RootName).ToArray();
        if (roots.Length != 1)
        {
            result.Failures.Add("Expected exactly one V9 root, found " + roots.Length);
            return Finish(result, null);
        }

        var root = roots[0];
        if (!TransformMatches(root, Vector3.zero, Quaternion.identity, Vector3.one))
            result.Failures.Add("V9 root placement drifted from the shared world frame");
        if (root.childCount != 4) result.Failures.Add("V9 root ownership groups drifted");

        result.RootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        result.MapMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (!Same(result.RootMetrics, Metrics(ExpectedRootRenderers, ExpectedRootVertices, ExpectedRootTriangles, ExpectedRootColliders)))
            result.Failures.Add("Unexpected V9 root metrics: " + MetricsToken(result.RootMetrics));
        if (!Same(result.MapMetrics, Metrics(ExpectedMapRenderers, ExpectedMapVertices, ExpectedMapTriangles, ExpectedMapColliders)))
            result.Failures.Add("Unexpected full-map V9 metrics: " + MetricsToken(result.MapMetrics));

        Physics.SyncTransforms();
        ValidateFrozenRoots(map, result);
        ValidateGeneratedVisuals(root, result);
        ValidateStructuralPairs(root, result);
        ValidateSupersededRenderers(map, result);
        ValidateInheritedFloors(map, result);
        ValidateCausewayColliderInventory(map, root, result);
        ValidateAnchors(root, result);
        ValidateGameplayObjects(result);
        ValidateRouteClearance(root, result);
        ValidateForbiddenComponents(root, result);
        return Finish(result, root);
    }

    private static ValidationResult Finish(ValidationResult result, Transform root)
    {
        result.Signature = root == null ? string.Empty : ComputeSignature(root);
        result.Passed = result.Failures.Count == 0;
        return result;
    }

    private static void ValidateFrozenInputs(ValidationResult result)
    {
        ExpectHash(result, "V5 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs", FrozenV5BuilderSha);
        ExpectHash(result, "V5 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV5AcceptanceValidator.cs", FrozenV5ValidatorSha);
        ExpectHash(result, "V6 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualFidelityBuilder.cs", FrozenV6BuilderSha);
        ExpectHash(result, "V6 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV6VisualSliceValidator.cs", FrozenV6ValidatorSha);
        ExpectHash(result, "V7 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingBuilder.cs", FrozenV7BuilderSha);
        ExpectHash(result, "V7 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV7EntryWayfindingValidator.cs", FrozenV7ValidatorSha);
        ExpectHash(result, "V8 pipeline", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleArtPipeline.cs", FrozenV8PipelineSha);
        ExpectHash(result, "V8 builder", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtBuilder.cs", FrozenV8BuilderSha);
        ExpectHash(result, "V8 validator", "Assets/_Project/Scripts/Editor/ChannelPlayKhufuV8TempleProductionArtValidator.cs", FrozenV8ValidatorSha);
        ExpectHash(result, "V8 proof probe", "Assets/_Project/Scripts/Gameplay/KhufuV8TempleProofProbe.cs", FrozenV8ProbeSha);
        ExpectHash(result, "package manifest", "Packages/manifest.json", FrozenManifestSha);
        ExpectHash(result, "package lock", "Packages/packages-lock.json", FrozenLockSha);
        ExpectHash(result, "source FBX", ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath, FrozenSourceSha);
        ExpectHash(result, "source FBX meta", ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath + ".meta", FrozenSourceMetaSha);
    }

    private static void ValidateFrozenRoots(Transform map, ValidationResult result)
    {
        var v6 = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName);
        var v7 = map.Find(ChannelPlayKhufuV7EntryWayfindingBuilder.RootName);
        var v8 = map.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.RootName);
        if (v6 == null || v7 == null || v8 == null)
        {
            result.Failures.Add("Frozen V6/V7/V8 extension root missing");
            return;
        }
        if (!Same(ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v6), Metrics(11, 520, 404, 0)))
            result.Failures.Add("Frozen V6 root metrics drifted");
        if (!Same(ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v7), Metrics(8, 192, 96, 0)))
            result.Failures.Add("Frozen V7 root metrics drifted");
        if (!Same(ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v8), Metrics(10, 33550, 27180, 0)))
            result.Failures.Add("Frozen V8 root metrics drifted");
        if (ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(v6) != FrozenV6RootSignature)
            result.Failures.Add("Frozen V6 root signature drifted");
        if (ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(v7) != FrozenV7RootSignature)
            result.Failures.Add("Frozen V7 root signature drifted");
        if (ComputeV8Signature(v8) != FrozenV8Signature)
            result.Failures.Add("Frozen V8 root signature drifted");
    }

    private static void ValidateGeneratedVisuals(Transform root, ValidationResult result)
    {
        var visuals = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.VisualRootName);
        if (visuals == null)
        {
            result.Failures.Add("V9 visual root missing");
            return;
        }
        if (visuals.GetComponentsInChildren<Collider>(true).Length != 0)
            result.Failures.Add("Decorative or combined visual geometry owns a collider");

        var specs = ChannelPlayKhufuV9CausewayMeshPipeline.BuildSpecs();
        foreach (var bucket in ChannelPlayKhufuV9CausewayMeshPipeline.Buckets)
        {
            var child = visuals.Find("V9_" + bucket);
            var renderer = child == null ? null : child.GetComponent<MeshRenderer>();
            var filter = child == null ? null : child.GetComponent<MeshFilter>();
            var assetPath = MeshAssetPath(bucket);
            var asset = AssetDatabase.LoadAssetAtPath<Mesh>(assetPath);
            if (renderer == null || filter == null || asset == null || filter.sharedMesh != asset)
            {
                result.Failures.Add("Missing or unbound V9 generated mesh: " + bucket);
                continue;
            }
            if (!renderer.enabled) result.Failures.Add("V9 production renderer disabled: " + bucket);
            if (renderer.sharedMaterial == null || renderer.sharedMaterial.name != ExpectedMaterials[bucket])
                result.Failures.Add("Unexpected V9 material: " + bucket);
            if (!TransformMatches(child, Vector3.zero, Quaternion.identity, Vector3.one))
                result.Failures.Add("V9 combined mesh transform drifted: " + bucket);

            var expectedBoxes = specs.Count(item => item.Bucket == bucket);
            if (asset.vertexCount != expectedBoxes * 24 || ChannelPlayKhufuV9CausewayMeshPipeline.TriangleCount(asset) != expectedBoxes * 12)
                result.Failures.Add("V9 generated mesh topology drifted: " + bucket);
            if (string.IsNullOrEmpty(AssetDatabase.AssetPathToGUID(assetPath)))
                result.Failures.Add("V9 generated mesh GUID missing: " + bucket);
        }
        if (visuals.GetComponentsInChildren<Renderer>(true).Length != ExpectedRootRenderers)
            result.Failures.Add("V9 renderer bucket count drifted");
    }

    private static void ValidateStructuralPairs(Transform root, ValidationResult result)
    {
        var pairs = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.PairRootName);
        var proxies = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.CollisionRootName);
        if (pairs == null || proxies == null)
        {
            result.Failures.Add("V9 structural pair ownership roots missing");
            return;
        }

        var specs = ChannelPlayKhufuV9CausewayMeshPipeline.BuildSpecs()
            .Where(item => item.Structural && item.Collider)
            .OrderBy(item => item.Name, StringComparer.Ordinal)
            .ToArray();
        if (specs.Length != ExpectedRootColliders || pairs.childCount != specs.Length || proxies.childCount != specs.Length)
            result.Failures.Add("V9 structural pair count drifted");

        foreach (var spec in specs)
        {
            var marker = pairs.Find("V9_PAIR_" + spec.Name);
            var proxy = proxies.Find("V9_PROXY_" + spec.Name);
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(MeshAssetPath(spec.Bucket));
            if (marker == null || proxy == null)
            {
                result.Failures.Add("Structural pair missing: " + spec.Name);
                continue;
            }
            if (!TransformMatches(marker, spec.Position, spec.Rotation, spec.Scale) ||
                !TransformMatches(proxy, spec.Position, spec.Rotation, spec.Scale))
                result.Failures.Add("Structural pair transform drifted: " + spec.Name);

            var collider = proxy.GetComponent<BoxCollider>();
            if (collider == null || !collider.enabled || collider.isTrigger || collider.center != Vector3.zero || collider.size != Vector3.one)
            {
                result.Failures.Add("Structural pair collider contract drifted: " + spec.Name);
                continue;
            }
            var expectedBounds = BoundsForSpec(spec);
            var markerBounds = BoundsForTransform(marker);
            var delta = Mathf.Max(BoundsDelta(expectedBounds, markerBounds), BoundsDelta(markerBounds, collider.bounds));
            result.MaxPairDelta = Mathf.Max(result.MaxPairDelta, delta);
            if (delta > PairTolerance)
                result.Failures.Add("Structural pair bounds drifted: " + spec.Name + " delta=" + delta.ToString("0.000", CultureInfo.InvariantCulture));
            if (!MeshContainsSpec(mesh, spec))
                result.Failures.Add("Structural visual is missing from combined mesh: " + spec.Name);
        }
    }

    private static void ValidateSupersededRenderers(Transform map, ValidationResult result)
    {
        var superseded = ChannelPlayKhufuV9CausewayFidelityBuilder.CollectSupersededRenderers(map);
        if (superseded.Count != ChannelPlayKhufuV9CausewayFidelityBuilder.ExpectedSupersededRenderers)
            result.Failures.Add("Superseded renderer whitelist count drifted");
        foreach (var renderer in superseded)
        {
            if (renderer.enabled) result.Failures.Add("Superseded graybox renderer enabled: " + renderer.name);
        }

        var v5Hub = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_District_Pyramid_Temple_Hub");
        var v6Hub = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName + "/V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
        if (v5Hub == null || v6Hub == null || v5Hub.GetComponentsInChildren<Renderer>(true).Any(item => item.enabled) ||
            v6Hub.GetComponentsInChildren<Renderer>(true).Any(item => item.enabled))
            result.Failures.Add("Frozen V8 temple supersession state drifted");
    }

    private static void ValidateInheritedFloors(Transform map, ValidationResult result)
    {
        var floors = ChannelPlayKhufuV9CausewayFidelityBuilder.CollectInheritedFloorColliders(map);
        if (floors.Count != ChannelPlayKhufuV9CausewayFidelityBuilder.ExpectedInheritedFloorColliders)
        {
            result.Failures.Add("Inherited forward floor collider count drifted");
            return;
        }
        var specs = ChannelPlayKhufuV9CausewayMeshPipeline.BuildSpecs();
        var expected = new Dictionary<string, ChannelPlayKhufuV9CausewayMeshPipeline.BoxSpec>(StringComparer.Ordinal)
        {
            { "V5_Route_Segment_00_Floor", specs.Single(item => item.Name == "Valley_To_Causeway_Floor") },
            { "V5_Route_Segment_01_Floor", specs.Single(item => item.Name == "Causeway_To_Hub_Floor") }
        };
        foreach (var floor in floors)
        {
            if (!floor.enabled || floor.isTrigger) result.Failures.Add("Inherited floor collider disabled or trigger: " + floor.name);
            if (floor.center != Vector3.zero || floor.size != Vector3.one)
                result.Failures.Add("Inherited floor collider center/size drifted: " + floor.name);
            var spec = expected[floor.name];
            var positionDelta = Vector3.Distance(floor.transform.position, spec.Position);
            var scaleDelta = MaxComponentDelta(floor.transform.lossyScale, spec.Scale);
            var angleDelta = Quaternion.Angle(floor.transform.rotation, spec.Rotation);
            result.MaxFloorPositionDelta = Mathf.Max(result.MaxFloorPositionDelta, positionDelta);
            result.MaxFloorScaleDelta = Mathf.Max(result.MaxFloorScaleDelta, scaleDelta);
            result.MaxFloorAngleDelta = Mathf.Max(result.MaxFloorAngleDelta, angleDelta);
            if (positionDelta > PairTolerance || scaleDelta > PairTolerance || angleDelta > 0.01f)
                result.Failures.Add("Inherited floor transform drifted: " + floor.name +
                                    " position=" + positionDelta.ToString("0.000", CultureInfo.InvariantCulture) +
                                    " scale=" + scaleDelta.ToString("0.000", CultureInfo.InvariantCulture) +
                                    " angle=" + angleDelta.ToString("0.000", CultureInfo.InvariantCulture));
            var delta = BoundsDelta(BoundsForSpec(spec), floor.bounds);
            result.MaxFloorDelta = Mathf.Max(result.MaxFloorDelta, delta);
            if (delta > PairTolerance)
                result.Failures.Add("Inherited floor visual/collider bounds drifted: " + floor.name + " delta=" + delta.ToString("0.000", CultureInfo.InvariantCulture));
        }
    }

    private static void ValidateCausewayColliderInventory(Transform map, Transform root, ValidationResult result)
    {
        var renderers = root.GetComponentsInChildren<Renderer>(true)
            .Where(item => item.enabled && item.gameObject.activeInHierarchy)
            .ToArray();
        if (renderers.Length == 0)
        {
            result.Failures.Add("V9 causeway collider envelope has no renderers");
            return;
        }

        var envelope = renderers[0].bounds;
        foreach (var renderer in renderers.Skip(1)) envelope.Encapsulate(renderer.bounds);
        result.CausewayEnvelope = envelope;

        var proxies = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.CollisionRootName);
        var v9Colliders = proxies == null
            ? Array.Empty<Collider>()
            : proxies.GetComponentsInChildren<Collider>(true);
        var inheritedFloors = ChannelPlayKhufuV9CausewayFidelityBuilder.CollectInheritedFloorColliders(map)
            .Cast<Collider>()
            .ToArray();
        var allowed = new HashSet<Collider>(v9Colliders.Concat(inheritedFloors));
        var intersecting = map.GetComponentsInChildren<Collider>(true)
            .Where(item => item.enabled && item.gameObject.activeInHierarchy && !item.isTrigger && item.bounds.Intersects(envelope))
            .OrderBy(item => item.name, StringComparer.Ordinal)
            .ToArray();

        result.CausewayEnabledSolidColliders = intersecting.Length;
        result.CausewayV9Colliders = intersecting.Count(v9Colliders.Contains);
        result.CausewayInheritedFloorColliders = intersecting.Count(inheritedFloors.Contains);
        var visibleExtras = intersecting
            .Where(item => !allowed.Contains(item) && HasEnabledRenderer(item.transform))
            .ToArray();
        var orphaned = intersecting
            .Where(item => !allowed.Contains(item) && !HasEnabledRenderer(item.transform))
            .ToArray();
        result.CausewayVisibleMatchedColliders = visibleExtras.Length;
        result.CausewayOrphanedColliders = orphaned.Length;
        foreach (var collider in orphaned)
            result.Failures.Add("Enabled solid collider has no visible geometry in V9 causeway envelope: " + collider.name);

        foreach (var renderer in ChannelPlayKhufuV9CausewayFidelityBuilder.CollectSupersededRenderers(map))
        foreach (var collider in renderer.GetComponents<Collider>())
        {
            if (!allowed.Contains(collider) && collider.enabled && !collider.isTrigger && collider.bounds.Intersects(envelope))
                result.Failures.Add("Superseded renderer retains enabled solid collider in V9 causeway envelope: " + renderer.name);
        }
        if (result.CausewayV9Colliders != ExpectedRootColliders ||
            result.CausewayInheritedFloorColliders != ChannelPlayKhufuV9CausewayFidelityBuilder.ExpectedInheritedFloorColliders ||
            result.CausewayOrphanedColliders != 0)
            result.Failures.Add("V9 causeway collider inventory drifted: total=" + intersecting.Length +
                                " v9=" + result.CausewayV9Colliders +
                                " inherited=" + result.CausewayInheritedFloorColliders +
                                " visible-extra=" + result.CausewayVisibleMatchedColliders +
                                " orphaned=" + result.CausewayOrphanedColliders);
    }

    private static bool HasEnabledRenderer(Transform colliderTransform)
    {
        return colliderTransform.GetComponentsInChildren<Renderer>(true)
            .Any(item => item.enabled && item.gameObject.activeInHierarchy);
    }

    private static void ValidateAnchors(Transform root, ValidationResult result)
    {
        var metadata = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.MetadataRootName);
        if (metadata == null)
        {
            result.Failures.Add("V9 metadata root missing");
            return;
        }
        ValidateAnchor(metadata, "V9_Anchor_Valley_Gate", ChannelPlayKhufuV9CausewayMeshPipeline.ValleyPoint, result);
        ValidateAnchor(metadata, "V9_Anchor_Covered_Causeway", ChannelPlayKhufuV9CausewayMeshPipeline.CausewayPoint, result);
        ValidateAnchor(metadata, "V9_Anchor_V8_Temple_Hub", ChannelPlayKhufuV9CausewayMeshPipeline.HubPoint, result);
        if (metadata.Find("V9_META_GAME_ART_INTERPRETATION_NOT_RECONSTRUCTION") == null)
            result.Failures.Add("V9 historical-boundary metadata missing");
    }

    private static void ValidateAnchor(Transform parent, string name, Vector3 expected, ValidationResult result)
    {
        var anchor = parent.Find(name);
        if (anchor == null || Vector3.Distance(anchor.position, expected) > 0.001f)
            result.Failures.Add("V9 route anchor drifted: " + name);
    }

    private static void ValidateGameplayObjects(ValidationResult result)
    {
        foreach (var name in new[] { "Runtime_Mission_Terminal", "Runtime_Shop_Terminal", "Runtime_Final_Exit_Door", "Gameplay_PlayerSpawn_ValleyGate" })
        {
            if (GameObject.Find(name) == null) result.Failures.Add("Frozen gameplay binding object missing: " + name);
        }
    }

    private static void ValidateRouteClearance(Transform root, ValidationResult result)
    {
        var proxies = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.CollisionRootName);
        if (proxies == null) return;
        var colliders = proxies.GetComponentsInChildren<BoxCollider>(true);
        result.ClearanceSamples = 0;
        ValidateRouteSegmentClearance(ChannelPlayKhufuV9CausewayMeshPipeline.ValleyPoint,
            ChannelPlayKhufuV9CausewayMeshPipeline.CausewayPoint, colliders, result);
        ValidateRouteSegmentClearance(ChannelPlayKhufuV9CausewayMeshPipeline.CausewayPoint,
            ChannelPlayKhufuV9CausewayMeshPipeline.HubPoint, colliders, result);
    }

    private static void ValidateRouteSegmentClearance(Vector3 start, Vector3 end, IEnumerable<BoxCollider> colliders, ValidationResult result)
    {
        var steps = Mathf.CeilToInt(Vector3.Distance(start, end));
        for (var index = 0; index <= steps; index++)
        {
            var point = Vector3.Lerp(start, end, index / (float)steps);
            var corridor = new Bounds(point + Vector3.up * 1.1f, new Vector3(0.4f, 2.2f, 1.8f));
            result.ClearanceSamples++;
            foreach (var collider in colliders)
            {
                if (collider.bounds.Intersects(corridor))
                    result.Failures.Add("V9 structural collider intrudes into 1.8m x 2.2m route clearance: " + collider.name);
            }
        }
    }

    private static void ValidateForbiddenComponents(Transform root, ValidationResult result)
    {
        if (root.GetComponentsInChildren<MeshCollider>(true).Length != 0) result.Failures.Add("V9 root contains MeshCollider");
        if (root.GetComponentsInChildren<Light>(true).Length != 0) result.Failures.Add("V9 root contains Light");
        if (root.GetComponentsInChildren<Camera>(true).Length != 0) result.Failures.Add("V9 root contains Camera");
        if (root.GetComponentsInChildren<Rigidbody>(true).Length != 0) result.Failures.Add("V9 root contains Rigidbody");
        var proxies = root.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.CollisionRootName);
        foreach (var collider in root.GetComponentsInChildren<Collider>(true))
        {
            if (proxies == null || !collider.transform.IsChildOf(proxies))
                result.Failures.Add("V9 collider exists outside collision ownership root: " + collider.name);
        }
    }

    private static bool MeshContainsSpec(Mesh mesh, ChannelPlayKhufuV9CausewayMeshPipeline.BoxSpec spec)
    {
        if (mesh == null) return false;
        var vertices = mesh.vertices;
        foreach (var corner in SpecCorners(spec))
        {
            if (!vertices.Any(vertex => Vector3.SqrMagnitude(vertex - corner) <= 0.000001f)) return false;
        }
        return true;
    }

    private static IEnumerable<Vector3> SpecCorners(ChannelPlayKhufuV9CausewayMeshPipeline.BoxSpec spec)
    {
        var half = spec.Scale * 0.5f;
        var matrix = Matrix4x4.TRS(spec.Position, spec.Rotation, Vector3.one);
        for (var x = -1; x <= 1; x += 2)
        for (var y = -1; y <= 1; y += 2)
        for (var z = -1; z <= 1; z += 2)
            yield return matrix.MultiplyPoint3x4(Vector3.Scale(half, new Vector3(x, y, z)));
    }

    private static Bounds BoundsForSpec(ChannelPlayKhufuV9CausewayMeshPipeline.BoxSpec spec)
    {
        return BoundsFromPoints(SpecCorners(spec));
    }

    private static Bounds BoundsForTransform(Transform target)
    {
        var half = Vector3.one * 0.5f;
        var points = new List<Vector3>();
        for (var x = -1; x <= 1; x += 2)
        for (var y = -1; y <= 1; y += 2)
        for (var z = -1; z <= 1; z += 2)
            points.Add(target.TransformPoint(Vector3.Scale(half, new Vector3(x, y, z))));
        return BoundsFromPoints(points);
    }

    private static Bounds BoundsFromPoints(IEnumerable<Vector3> source)
    {
        var points = source.ToArray();
        var bounds = new Bounds(points[0], Vector3.zero);
        foreach (var point in points.Skip(1)) bounds.Encapsulate(point);
        return bounds;
    }

    private static float BoundsDelta(Bounds left, Bounds right)
    {
        var center = Abs(left.center - right.center);
        var size = Abs(left.size - right.size);
        return Mathf.Max(center.x, center.y, center.z, size.x, size.y, size.z);
    }

    private static float MaxComponentDelta(Vector3 left, Vector3 right)
    {
        var delta = left - right;
        return Mathf.Max(Mathf.Abs(delta.x), Mathf.Abs(delta.y), Mathf.Abs(delta.z));
    }

    private static Vector3 Abs(Vector3 value)
    {
        return new Vector3(Mathf.Abs(value.x), Mathf.Abs(value.y), Mathf.Abs(value.z));
    }

    private static bool TransformMatches(Transform target, Vector3 position, Quaternion rotation, Vector3 scale)
    {
        return target != null && Vector3.Distance(target.position, position) <= 0.001f &&
               Quaternion.Angle(target.rotation, rotation) <= 0.01f && Vector3.Distance(target.lossyScale, scale) <= 0.001f;
    }

    private static Transform FindRoot()
    {
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        var root = map == null ? null : map.transform.Find(ChannelPlayKhufuV9CausewayFidelityBuilder.RootName);
        if (root == null) throw new InvalidOperationException("V9 root is missing.");
        return root;
    }

    private static string ComputeSignature(Transform root)
    {
        var text = new StringBuilder(ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(root));
        foreach (var item in GeneratedAssetBindings()) text.AppendLine(item);
        return Sha256Text(text.ToString());
    }

    private static string ComputeV8Signature(Transform root)
    {
        var text = new StringBuilder(ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(root));
        var paths = ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedDonorBuckets()
            .Concat(new[] { "Square_Red_Granite_Pillars" })
            .Select(ChannelPlayKhufuV8TempleProductionArtBuilder.MeshAssetPath)
            .OrderBy(item => item, StringComparer.Ordinal);
        foreach (var path in paths) text.AppendLine(path + "=" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path));
        return Sha256Text(text.ToString());
    }

    private static List<string> GeneratedAssetBindings()
    {
        return ChannelPlayKhufuV9CausewayMeshPipeline.Buckets
            .Select(MeshAssetPath)
            .OrderBy(item => item, StringComparer.Ordinal)
            .Select(path => path + "|guid=" + AssetDatabase.AssetPathToGUID(path) + "|sha256=" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path))
            .ToList();
    }

    private static string MeshAssetPath(string bucket)
    {
        return ChannelPlayKhufuV9CausewayMeshPipeline.GeneratedRoot + "/KhufuV9_" + bucket + ".asset";
    }

    private static void ExpectHash(ValidationResult result, string label, string path, string expected)
    {
        var actual = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
        if (actual != expected) result.Failures.Add("Frozen " + label + " hash drifted");
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(RunPath("validation.md")) ?? ".");
        var text = new StringBuilder("# Khufu V9 Causeway Fidelity Validation\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Root metrics: `" + MetricsToken(result.RootMetrics) + "`");
        text.AppendLine("- Full-map metrics: `" + MetricsToken(result.MapMetrics) + "`");
        text.AppendLine("- Structural pairs: `" + ExpectedRootColliders + "`");
        text.AppendLine("- Maximum structural pair bounds delta: `" + result.MaxPairDelta.ToString("0.000", CultureInfo.InvariantCulture) + " m`");
        text.AppendLine("- Maximum inherited floor bounds delta: `" + result.MaxFloorDelta.ToString("0.000", CultureInfo.InvariantCulture) + " m`");
        text.AppendLine("- Maximum inherited floor position / scale / angle delta: `" +
                        result.MaxFloorPositionDelta.ToString("0.000", CultureInfo.InvariantCulture) + " m / " +
                        result.MaxFloorScaleDelta.ToString("0.000", CultureInfo.InvariantCulture) + " / " +
                        result.MaxFloorAngleDelta.ToString("0.000", CultureInfo.InvariantCulture) + " deg`");
        text.AppendLine("- Causeway envelope center / size: `" + VectorToken(result.CausewayEnvelope.center) + " / " + VectorToken(result.CausewayEnvelope.size) + "`");
        text.AppendLine("- Enabled solid colliders in causeway envelope: `" + result.CausewayEnabledSolidColliders + "` (`" +
                        result.CausewayV9Colliders + " V9 + " + result.CausewayInheritedFloorColliders + " inherited floors + " +
                        result.CausewayVisibleMatchedColliders + " visible extras; " + result.CausewayOrphanedColliders + " orphaned`)");
        text.AppendLine("- Route clearance samples: `" + result.ClearanceSamples + "` at `1.8m x 2.2m`");
        text.AppendLine("- Signature: `" + result.Signature + "`");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("V9_STATIC_VALIDATION: " + (result.Passed ? "passed" : "failed"));
        File.WriteAllText(RunPath("validation.md"), text.ToString());
    }

    private static void WriteMutation(string filename, string mutation, IEnumerable<string> failures, bool rejected, string token)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(RunPath(filename)) ?? ".");
        var text = new StringBuilder("# Khufu V9 Mutation Gate\n\n");
        text.AppendLine("- Verdict: **" + (rejected ? "passed" : "failed") + "**");
        text.AppendLine("- Mutation: `" + mutation + "`");
        foreach (var failure in failures) text.AppendLine("- Observed failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine(token + ": " + (rejected ? "passed" : "failed"));
        File.WriteAllText(RunPath(filename), text.ToString());
    }

    private static string RunPath(string filename)
    {
        return ChannelPlayKhufuV9CausewayFidelityBuilder.RunRoot + "/" + filename;
    }

    private static ChannelPlayKhufuV6VisualFidelityBuilder.Metrics Metrics(int renderers, int vertices, int triangles, int colliders)
    {
        return new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics
        {
            Renderers = renderers,
            Vertices = vertices,
            Triangles = triangles,
            Colliders = colliders
        };
    }

    private static bool Same(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics left, ChannelPlayKhufuV6VisualFidelityBuilder.Metrics right)
    {
        return left.Renderers == right.Renderers && left.Vertices == right.Vertices &&
               left.Triangles == right.Triangles && left.Colliders == right.Colliders;
    }

    private static string MetricsToken(ChannelPlayKhufuV6VisualFidelityBuilder.Metrics metrics)
    {
        return "renderers=" + metrics.Renderers + "_vertices=" + metrics.Vertices +
               "_triangles=" + metrics.Triangles + "_colliders=" + metrics.Colliders;
    }

    private static string VectorToken(Vector3 value)
    {
        return value.x.ToString("0.000", CultureInfo.InvariantCulture) + "," +
               value.y.ToString("0.000", CultureInfo.InvariantCulture) + "," +
               value.z.ToString("0.000", CultureInfo.InvariantCulture);
    }

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create())
            return string.Concat(sha.ComputeHash(Encoding.UTF8.GetBytes(value)).Select(item => item.ToString("x2")));
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public string Signature = string.Empty;
        public float MaxPairDelta;
        public float MaxFloorDelta;
        public float MaxFloorPositionDelta;
        public float MaxFloorScaleDelta;
        public float MaxFloorAngleDelta;
        public int ClearanceSamples;
        public int CausewayEnabledSolidColliders;
        public int CausewayV9Colliders;
        public int CausewayInheritedFloorColliders;
        public int CausewayVisibleMatchedColliders;
        public int CausewayOrphanedColliders;
        public Bounds CausewayEnvelope;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics RootMetrics = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics MapMetrics = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public readonly List<string> Failures = new List<string>();
    }
}

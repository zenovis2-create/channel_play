using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ChannelPlayKhufuV8TempleProductionArtValidator
{
    private const string FrozenV5BuilderSha = "0a9f7a1f071db40fbab05e955e41acfbfa98c6b22aa7ee9d059f454392184faf";
    private const string FrozenV5ValidatorSha = "405573071d52ef12fa816cf230e51bab11e2f2cda2f7dfe7e708a7b99fbc5ebd";
    private const string FrozenV6BuilderSha = "ffa6fa51a20074760181db6c87319f2aad5afca443e37f80da657b17759c75f2";
    private const string FrozenV6ValidatorSha = "6ab23d70ce11c8c8e69352937150599352a821db55426e150935e0fec2a3cf1c";
    private const string FrozenV7BuilderSha = "3d7cd2f0542d2b3755ce449433b2c00e5a2261bcbe2df050401a0b8af77429f6";
    private const string FrozenV7ValidatorSha = "746130bbd87310bcad04be5914d5622cbed7a8cf3c84d29d95fb0002bf802a08";
    private const string FrozenManifestSha = "7cd02eaeb95d283e74c459ebc0babca4a936f92158f337b155ec1e5da0eacb38";
    private const string FrozenLockSha = "d9553a688d4afe8a5c95a0aba04b755647b72d90f5956a19b2fae160d2b7ec8e";
    private const string FrozenSourceSha = "234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d";
    private const string FrozenSourceMetaSha = "6457410564068ea13f962237a9178321e5e608f4f5a482f68eeea4b064e2d094";
    private const string FrozenV6RootSignature = "b41580ea2636838635ac54cacf2f20f34224b39bb32a506d223bbcfc2476d530";
    private const string FrozenV7RootSignature = "9730013ededc08da590b99de5d2bd1ae91c485b25d67e6c591117d4431c2d321";

    private const int ExpectedRootVertices = 33550;
    private const int ExpectedRootTriangles = 27180;
    private const int ExpectedMapRenderers = 813;
    private const int ExpectedMapVertices = 57518;
    private const int ExpectedMapTriangles = 43784;
    private const int ExpectedMapColliders = 441;

    [MenuItem("Channel Play/Khufu V8/Run All Static Gates")]
    public static void RunAllStaticGates()
    {
        ChannelPlayCameraCutawayValidator.ValidateCameraCutaway();
        ValidateMenu();
        ValidateIdempotence();
        ValidatePlacementMutation();
        ValidateGrayboxMutation();
        ValidatePillarIntrusionMutation();
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_STATIC_GATES result=passed");
    }

    [MenuItem("Channel Play/Khufu V8/Validate Temple Production Art")]
    public static void ValidateMenu()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath);
        var result = ValidateScene();
        WriteValidation(result);
        if (!result.Passed) throw new InvalidOperationException("Khufu V8 validation failed: " + string.Join("; ", result.Failures));
        Debug.Log("CHANNEL_PLAY_KHUFU_V8_VALIDATE result=passed signature=" + result.Signature);
    }

    [MenuItem("Channel Play/Khufu V8/Validate Rebuild Idempotence")]
    public static void ValidateIdempotence()
    {
        Directory.CreateDirectory(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot);
        ChannelPlayKhufuV8TempleProductionArtBuilder.Rebuild();
        var first = ValidateScene();
        var firstAssets = GeneratedAssetHashes();
        ChannelPlayKhufuV8TempleProductionArtBuilder.Rebuild();
        var second = ValidateScene();
        var secondAssets = GeneratedAssetHashes();
        var passed = first.Passed && second.Passed && first.Signature == second.Signature &&
                     Same(first.RootMetrics, second.RootMetrics) && firstAssets.SequenceEqual(secondAssets);
        var text = new StringBuilder("# Khufu V8 Rebuild Idempotence\n\n");
        text.AppendLine("- Verdict: **" + (passed ? "passed" : "failed") + "**");
        text.AppendLine("- First signature: `" + first.Signature + "`");
        text.AppendLine("- Second signature: `" + second.Signature + "`");
        text.AppendLine("- First metrics: `" + MetricsToken(first.RootMetrics) + "`");
        text.AppendLine("- Second metrics: `" + MetricsToken(second.RootMetrics) + "`");
        text.AppendLine("- Stable generated assets: `" + firstAssets.Count + "`");
        text.AppendLine();
        text.AppendLine("V8_IDEMPOTENCE: " + (passed ? "passed" : "failed"));
        File.WriteAllText(Path.Combine(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot, "idempotence.md"), text.ToString());
        if (!passed) throw new InvalidOperationException("Khufu V8 idempotence failed.");
    }

    [MenuItem("Channel Play/Khufu V8/Validate Placement Mutation")]
    public static void ValidatePlacementMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath);
        var root = FindRoot();
        var original = root.position;
        root.position += Vector3.forward * 5f;
        var mutated = ValidateScene(false);
        root.position = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("placement", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("placement-mutation.md", "V8 root +5m world Z", mutated.Failures, rejected, "V8_PLACEMENT_MUTATION");
        if (!rejected) throw new InvalidOperationException("V8 placement mutation was not rejected.");
    }

    [MenuItem("Channel Play/Khufu V8/Validate Graybox Mutation")]
    public static void ValidateGrayboxMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath);
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName).transform;
        var v5Hub = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_District_Pyramid_Temple_Hub");
        var target = v5Hub.GetComponentsInChildren<Renderer>(true).OrderBy(item => HierarchyPath(v5Hub, item.transform), StringComparer.Ordinal).First();
        var original = target.enabled;
        target.enabled = true;
        var mutated = ValidateScene(false);
        target.enabled = original;
        var rejected = !mutated.Passed && mutated.Failures.Any(item => item.IndexOf("graybox", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("graybox-mutation.md", "Re-enable " + target.name, mutated.Failures, rejected, "V8_GRAYBOX_MUTATION");
        if (!rejected) throw new InvalidOperationException("V8 graybox mutation was not rejected.");
    }

    [MenuItem("Channel Play/Khufu V8/Validate Pillar Intrusion Mutation")]
    public static void ValidatePillarIntrusionMutation()
    {
        EditorSceneManager.OpenScene(ChannelPlayKhufuV8TempleProductionArtBuilder.ScenePath);
        var failures = ValidateRouteClearance(new Vector3(0f, 0f, 2f));
        var rejected = failures.Any(item => item.IndexOf("authored pillar", StringComparison.OrdinalIgnoreCase) >= 0);
        WriteMutation("pillar-intrusion-mutation.md", "Add authored pillar at local (0,0,2)", failures, rejected, "V8_PILLAR_INTRUSION_MUTATION");
        if (!rejected) throw new InvalidOperationException("V8 authored-pillar intrusion mutation was not rejected.");
    }

    private static ValidationResult ValidateScene(bool validateSelector = true)
    {
        var result = new ValidationResult();
        ValidateFrozenInputs(result);
        var mapObject = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        if (mapObject == null)
        {
            result.Failures.Add("Shared map root missing");
            return result;
        }

        var map = mapObject.transform;
        var roots = map.Cast<Transform>().Where(item => item.name == ChannelPlayKhufuV8TempleProductionArtBuilder.RootName).ToArray();
        if (roots.Length != 1)
        {
            result.Failures.Add("Expected exactly one V8 root, found " + roots.Length);
            return result;
        }

        var root = roots[0];
        if (Vector3.Distance(root.position, ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedPosition) > 0.001f ||
            Quaternion.Angle(root.rotation, ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedRotation) > 0.01f ||
            Vector3.Distance(root.localScale, Vector3.one) > 0.001f)
            result.Failures.Add("V8 placement does not match the frozen art frame");

        result.RootMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(root);
        result.MapMetrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(map);
        if (!Same(result.RootMetrics, Metrics(10, ExpectedRootVertices, ExpectedRootTriangles, 0)))
            result.Failures.Add("Unexpected V8 root metrics: " + MetricsToken(result.RootMetrics));
        if (!Same(result.MapMetrics, Metrics(ExpectedMapRenderers, ExpectedMapVertices, ExpectedMapTriangles, ExpectedMapColliders)))
            result.Failures.Add("Unexpected full-map V8 metrics: " + MetricsToken(result.MapMetrics));
        if (root.GetComponentsInChildren<Light>(true).Length != 0 || root.GetComponentsInChildren<Camera>(true).Length != 0)
            result.Failures.Add("V8 root contains imported light or camera components");

        ValidateRenderersAndMaterials(root, result);
        ValidateFrozenExtensionRoots(map, result);
        ValidateGrayboxState(map, result);
        ValidateAnchors(root, result);
        ValidateGameplayObjects(result);
        result.Failures.AddRange(ValidateRouteClearance(null));
        if (validateSelector) ValidateSelectorAndGeneratedAssets(result);
        result.Signature = ComputeSignature(root);
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
        ExpectHash(result, "package manifest", "Packages/manifest.json", FrozenManifestSha);
        ExpectHash(result, "package lock", "Packages/packages-lock.json", FrozenLockSha);
        ExpectHash(result, "source FBX", ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath, FrozenSourceSha);
        ExpectHash(result, "source FBX meta", ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath + ".meta", FrozenSourceMetaSha);
    }

    private static void ValidateRenderersAndMaterials(Transform root, ValidationResult result)
    {
        var expected = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            { "V8_Donor_Basalt_Court", "V6_Basalt_Court" },
            { "V8_Donor_Core_Limestone", "V6_Core_Limestone" },
            { "V8_Donor_Door_Shadow", "Temple_Door_Shadow" },
            { "V8_Donor_Paint_Blue", "Temple_Faded_Blue_Paint" },
            { "V8_Donor_Paint_Red", "Temple_Faded_Red_Paint" },
            { "V8_Donor_Paint_Teal", "Temple_Faded_Teal_Paint" },
            { "V8_Donor_Relief_Gold", "Temple_Faded_Gold_Relief" },
            { "V8_Donor_Tura_Limestone", "V6_Tura_Casing" },
            { "V8_Donor_Tura_Processional_Aisle", "V6_Tura_Casing" },
            { "V8_Authored_Square_Red_Granite_Pillars", "V6_Red_Granite" }
        };
        var renderers = root.GetComponentsInChildren<Renderer>(true);
        if (renderers.Length != expected.Count) result.Failures.Add("V8 renderer count does not match bucket contract");
        foreach (var pair in expected)
        {
            var child = root.Find(pair.Key);
            var renderer = child == null ? null : child.GetComponent<Renderer>();
            var filter = child == null ? null : child.GetComponent<MeshFilter>();
            if (renderer == null || filter == null || filter.sharedMesh == null)
            {
                result.Failures.Add("Missing V8 renderer/mesh: " + pair.Key);
                continue;
            }
            if (!renderer.enabled) result.Failures.Add("V8 production renderer disabled: " + pair.Key);
            if (renderer.sharedMaterial == null || renderer.sharedMaterial.name != pair.Value)
                result.Failures.Add("Unexpected material on " + pair.Key);
        }
    }

    private static void ValidateFrozenExtensionRoots(Transform map, ValidationResult result)
    {
        var v6 = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName);
        var v7 = map.Find(ChannelPlayKhufuV7EntryWayfindingBuilder.RootName);
        if (v6 == null || v7 == null)
        {
            result.Failures.Add("Frozen V6/V7 extension root missing");
            return;
        }
        var v6Metrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v6);
        var v7Metrics = ChannelPlayKhufuV6VisualFidelityBuilder.CollectMetrics(v7);
        if (!Same(v6Metrics, Metrics(11, 520, 404, 0))) result.Failures.Add("Frozen V6 root metrics drifted");
        if (!Same(v7Metrics, Metrics(8, 192, 96, 0))) result.Failures.Add("Frozen V7 root metrics drifted");
        if (ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(v6) != FrozenV6RootSignature)
            result.Failures.Add("Frozen V6 root signature drifted");
        if (ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(v7) != FrozenV7RootSignature)
            result.Failures.Add("Frozen V7 root signature drifted");
    }

    private static void ValidateGrayboxState(Transform map, ValidationResult result)
    {
        var v5Hub = map.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName + "/V5_District_Pyramid_Temple_Hub");
        var v6Hub = map.Find(ChannelPlayKhufuV6VisualFidelityBuilder.RootName + "/V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
        if (v5Hub == null || v6Hub == null)
        {
            result.Failures.Add("Superseded graybox roots missing");
            return;
        }
        var v5 = v5Hub.GetComponentsInChildren<Renderer>(true);
        var v6 = v6Hub.GetComponentsInChildren<Renderer>(true);
        if (v5.Length != ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedV5HubRenderers ||
            v6.Length != ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedV6HubRenderers)
            result.Failures.Add("Graybox renderer whitelist count drifted");
        if (v5.Concat(v6).Any(item => item.enabled)) result.Failures.Add("Superseded graybox renderer remains enabled");
    }

    private static void ValidateAnchors(Transform root, ValidationResult result)
    {
        var threshold = root.Find("V8_Anchor_Causeway_Threshold");
        var court = root.Find("V8_Anchor_Open_Court");
        var exit = root.Find("V8_Anchor_Pyramid_Side_Exit");
        if (threshold == null || court == null || exit == null)
        {
            result.Failures.Add("V8 route anchors missing");
            return;
        }
        if (!(threshold.position.x > court.position.x && court.position.x > exit.position.x) ||
            Mathf.Abs(threshold.position.z) > 0.01f || Mathf.Abs(court.position.z) > 0.01f || Mathf.Abs(exit.position.z) > 0.01f)
            result.Failures.Add("V8 route anchor ordering or causeway-axis placement is invalid");
    }

    private static void ValidateGameplayObjects(ValidationResult result)
    {
        var names = new[]
        {
            "Runtime_Mission_Terminal",
            "Runtime_Shop_Terminal",
            "Runtime_Final_Exit_Door",
            "Gameplay_PlayerSpawn_ValleyGate"
        };
        foreach (var name in names)
        {
            if (GameObject.Find(name) == null) result.Failures.Add("V5 gameplay binding object missing: " + name);
        }
    }

    private static void ValidateSelectorAndGeneratedAssets(ValidationResult result)
    {
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath);
        var instance = model == null ? null : PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (instance == null)
        {
            result.Failures.Add("V8 source could not be instantiated for selector validation");
            return;
        }
        try
        {
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;
            var buckets = ChannelPlayKhufuV8TempleArtPipeline.CollectBucketInputs(instance);
            var selected = buckets.SelectMany(item => item.Items).Select(item => item.Path).Distinct().Count();
            if (selected != ChannelPlayKhufuV8TempleArtPipeline.ExpectedSelectedRenderers)
                result.Failures.Add("Selector renderer count drifted: " + selected);
            if (buckets.Count != ChannelPlayKhufuV8TempleArtPipeline.ExpectedBucketCount)
                result.Failures.Add("Selector bucket count drifted: " + buckets.Count);
            long vertices = 0;
            long triangles = 0;
            foreach (var bucket in buckets)
            {
                var combined = ChannelPlayKhufuV8TempleArtPipeline.CombineBucket(bucket);
                vertices += combined.vertexCount;
                triangles += TriangleCount(combined);
                var generated = AssetDatabase.LoadAssetAtPath<Mesh>(ChannelPlayKhufuV8TempleProductionArtBuilder.MeshAssetPath(bucket.Name));
                if (generated == null || generated.vertexCount != combined.vertexCount || TriangleCount(generated) != TriangleCount(combined))
                    result.Failures.Add("Generated donor mesh drifted: " + bucket.Name);
                UnityEngine.Object.DestroyImmediate(combined);
            }
            if (vertices != ChannelPlayKhufuV8TempleArtPipeline.ExpectedCombinedVertices ||
                triangles != ChannelPlayKhufuV8TempleArtPipeline.ExpectedCombinedTriangles)
                result.Failures.Add("Selector combined metrics drifted");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static List<string> ValidateRouteClearance(Vector3? extraPillarLocalPosition)
    {
        var failures = new List<string>();
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(ChannelPlayKhufuV8TempleArtPipeline.SourceAssetPath);
        var instance = model == null ? null : PrefabUtility.InstantiatePrefab(model) as GameObject;
        if (instance == null)
        {
            failures.Add("Source instance missing for route-clearance validation");
            return failures;
        }
        try
        {
            instance.transform.SetPositionAndRotation(ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedPosition,
                ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedRotation);
            instance.transform.localScale = Vector3.one;
            foreach (var renderer in instance.GetComponentsInChildren<Renderer>(true)
                         .Where(item => item.enabled && item.gameObject.activeInHierarchy &&
                                        ChannelPlayKhufuV8TempleArtPipeline.IsSelectedRendererName(item.name)))
            {
                if (IsAllowedRouteSurface(renderer.name)) continue;
                if (IntersectsRouteCorridor(renderer.bounds))
                    failures.Add("Selected donor intrudes into route corridor: " + renderer.name);
            }

            for (var index = 0; index < ChannelPlayKhufuV8TempleProductionArtBuilder.AuthoredPillarCount; index++)
            {
                var bounds = PillarWorldBounds(ChannelPlayKhufuV8TempleProductionArtBuilder.PillarLocalPosition(index));
                if (IntersectsRouteCorridor(bounds)) failures.Add("Authored pillar intrudes into route corridor: " + index);
            }
            if (extraPillarLocalPosition.HasValue && IntersectsRouteCorridor(PillarWorldBounds(extraPillarLocalPosition.Value)))
                failures.Add("Authored pillar mutation intrudes into route corridor");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
        return failures;
    }

    private static bool IsAllowedRouteSurface(string name)
    {
        return name.IndexOf("Floor", StringComparison.Ordinal) >= 0 ||
               name.IndexOf("Aisle", StringComparison.Ordinal) >= 0 ||
               name.IndexOf("Seam", StringComparison.Ordinal) >= 0;
    }

    private static bool IntersectsRouteCorridor(Bounds bounds)
    {
        for (var x = 48f; x <= 78f; x += 0.5f)
        {
            var floorY = x <= 62f ? 1.15f : Mathf.Lerp(1.15f, 3.15f, (x - 62f) / 43f);
            var corridor = new Bounds(new Vector3(x, floorY + 1.1f, 0f), new Vector3(0.5f, 2.2f, 1.8f));
            if (bounds.Intersects(corridor)) return true;
        }
        return false;
    }

    private static Bounds PillarWorldBounds(Vector3 localBase)
    {
        var local = new Bounds(localBase + new Vector3(0f, 2.34f, 0f), new Vector3(1.5f, 4.68f, 1.5f));
        var matrix = Matrix4x4.TRS(ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedPosition,
            ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedRotation, Vector3.one);
        var corners = new List<Vector3>();
        for (var x = -1; x <= 1; x += 2)
        for (var y = -1; y <= 1; y += 2)
        for (var z = -1; z <= 1; z += 2)
            corners.Add(matrix.MultiplyPoint3x4(local.center + Vector3.Scale(local.extents, new Vector3(x, y, z))));
        var result = new Bounds(corners[0], Vector3.zero);
        foreach (var corner in corners.Skip(1)) result.Encapsulate(corner);
        return result;
    }

    private static void WriteValidation(ValidationResult result)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V8 Temple Production Art Validation\n\n");
        text.AppendLine("- Verdict: **" + (result.Passed ? "passed" : "failed") + "**");
        text.AppendLine("- Root metrics: `" + MetricsToken(result.RootMetrics) + "`");
        text.AppendLine("- Full-map metrics: `" + MetricsToken(result.MapMetrics) + "`");
        text.AppendLine("- Signature: `" + result.Signature + "`");
        foreach (var failure in result.Failures) text.AppendLine("- Failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine("V8_STATIC_VALIDATION: " + (result.Passed ? "passed" : "failed"));
        File.WriteAllText(Path.Combine(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot, "validation.md"), text.ToString());
    }

    private static void WriteMutation(string filename, string mutation, IEnumerable<string> failures, bool rejected, string token)
    {
        Directory.CreateDirectory(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot);
        var text = new StringBuilder("# Khufu V8 Mutation Gate\n\n");
        text.AppendLine("- Verdict: **" + (rejected ? "passed" : "failed") + "**");
        text.AppendLine("- Mutation: `" + mutation + "`");
        foreach (var failure in failures) text.AppendLine("- Observed failure: `" + failure + "`");
        text.AppendLine();
        text.AppendLine(token + ": " + (rejected ? "passed" : "failed"));
        File.WriteAllText(Path.Combine(ChannelPlayKhufuV8TempleProductionArtBuilder.RunRoot, filename), text.ToString());
    }

    private static Transform FindRoot()
    {
        var map = GameObject.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.MapRootName);
        var root = map == null ? null : map.transform.Find(ChannelPlayKhufuV8TempleProductionArtBuilder.RootName);
        if (root == null) throw new InvalidOperationException("V8 root is missing.");
        return root;
    }

    private static string ComputeSignature(Transform root)
    {
        var text = new StringBuilder(ChannelPlayKhufuV6VisualFidelityBuilder.ComputeVisualSignature(root));
        foreach (var item in GeneratedAssetHashes()) text.AppendLine(item);
        return Sha256Text(text.ToString());
    }

    private static List<string> GeneratedAssetHashes()
    {
        var paths = ChannelPlayKhufuV8TempleProductionArtBuilder.ExpectedDonorBuckets()
            .Concat(new[] { "Square_Red_Granite_Pillars" })
            .Select(ChannelPlayKhufuV8TempleProductionArtBuilder.MeshAssetPath)
            .OrderBy(item => item, StringComparer.Ordinal);
        return paths.Select(path => path + "=" + ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path)).ToList();
    }

    private static void ExpectHash(ValidationResult result, string label, string path, string expected)
    {
        var actual = ChannelPlayKhufuV6VisualFidelityBuilder.Sha256File(path);
        if (actual != expected) result.Failures.Add("Frozen " + label + " hash drifted");
    }

    private static int TriangleCount(Mesh mesh)
    {
        if (mesh == null) return 0;
        var total = 0;
        for (var index = 0; index < mesh.subMeshCount; index++) total += (int)mesh.GetIndexCount(index) / 3;
        return total;
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

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create())
        {
            return string.Concat(sha.ComputeHash(Encoding.UTF8.GetBytes(value)).Select(item => item.ToString("x2")));
        }
    }

    private static string HierarchyPath(Transform root, Transform node)
    {
        var names = new Stack<string>();
        var cursor = node;
        while (cursor != null && cursor != root)
        {
            names.Push(cursor.name);
            cursor = cursor.parent;
        }
        return string.Join("/", names);
    }

    private sealed class ValidationResult
    {
        public bool Passed;
        public string Signature = string.Empty;
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics RootMetrics = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public ChannelPlayKhufuV6VisualFidelityBuilder.Metrics MapMetrics = new ChannelPlayKhufuV6VisualFidelityBuilder.Metrics();
        public readonly List<string> Failures = new List<string>();
    }
}

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
using UnityEngine.Rendering;

public static class ChannelPlayKhufuV6VisualFidelityBuilder
{
    public const string RootName = "Runtime_Khufu_V6_Visual_Fidelity_Slice";
    public const string MapRootName = "TraitorEscape_Runtime_Map";
    public const string MaterialRoot = "Assets/_Project/Materials/KhufuV6";
    public const string TextureRoot = "Assets/_Project/Art/Generated/KhufuV6VisualSlice/Textures";
    public const string RunRoot = "runs/khufu-v6-visual-slice";
    public const string V5BuilderPath = "Assets/_Project/Scripts/Editor/ChannelPlayKhufuMegaLabyrinthV5Builder.cs";
    public const int TextureSize = 512;
    public const int MaximumAddedRenderers = 12;
    public const int MaximumAddedVertices = 800;
    public const int MaximumAddedTriangles = 600;
    public const int MaximumMaterialCount = 8;

    public static readonly string[] SurfaceNames =
    {
        "TuraCasing",
        "CoreLimestone",
        "Basalt",
        "RedGranite",
    };

    public static readonly string[] MaterialNames =
    {
        "V6_Tura_Casing",
        "V6_Core_Limestone",
        "V6_Interior_Limestone",
        "V6_Basalt_Court",
        "V6_Red_Granite",
        "V6_Causeway_Limestone",
        "V6_Scan_Inlay",
    };

    private static readonly SurfaceSpec[] Surfaces =
    {
        new SurfaceSpec("TuraCasing", new Color(0.58f, 0.54f, 0.45f), new Color(0.20f, 0.18f, 0.15f), 112, 56, 3, 101, 0.025f, 6.5f),
        new SurfaceSpec("CoreLimestone", new Color(0.45f, 0.35f, 0.24f), new Color(0.16f, 0.12f, 0.085f), 96, 52, 4, 211, 0.05f, 7.5f),
        new SurfaceSpec("Basalt", new Color(0.095f, 0.105f, 0.11f), new Color(0.025f, 0.03f, 0.035f), 72, 72, 3, 307, 0.025f, 6.0f),
        new SurfaceSpec("RedGranite", new Color(0.29f, 0.12f, 0.085f), new Color(0.11f, 0.045f, 0.035f), 256, 128, 1, 401, 0.18f, 3.5f),
    };

    private static readonly MaterialSpec[] Materials =
    {
        new MaterialSpec("V6_Tura_Casing", "TuraCasing", new Vector2(4f, 4f), 0.03f, 0.18f),
        new MaterialSpec("V6_Core_Limestone", "CoreLimestone", new Vector2(6f, 6f), 0.02f, 0.12f),
        new MaterialSpec("V6_Interior_Limestone", "CoreLimestone", new Vector2(4f, 4f), 0.02f, 0.17f),
        new MaterialSpec("V6_Basalt_Court", "Basalt", new Vector2(8f, 8f), 0.03f, 0.30f),
        new MaterialSpec("V6_Red_Granite", "RedGranite", new Vector2(1.5f, 1.5f), 0.04f, 0.32f),
        new MaterialSpec("V6_Causeway_Limestone", "CoreLimestone", new Vector2(5f, 4f), 0.02f, 0.15f),
        new MaterialSpec("V6_Scan_Inlay", "Basalt", new Vector2(5f, 5f), 0.02f, 0.28f, new Color(0.12f, 0.55f, 0.57f)),
    };

    [MenuItem("Channel Play/Khufu V6/Rebuild Visual Fidelity Slice")]
    public static void Rebuild()
    {
        ChannelPlayKhufuMegaLabyrinthV5Builder.Rebuild();
        var scene = EditorSceneManager.GetActiveScene();
        var mapRootObject = GameObject.Find(MapRootName);
        if (mapRootObject == null) throw new InvalidOperationException("Shared map root is missing after V5 rebuild.");

        var mapRoot = mapRootObject.transform;
        var oldRoot = mapRoot.Find(RootName);
        if (oldRoot != null) UnityEngine.Object.DestroyImmediate(oldRoot.gameObject);

        var v4 = mapRoot.Find(ChannelPlayPyramidReferenceMatchedV4Builder.RootName);
        var v5 = mapRoot.Find(ChannelPlayKhufuMegaLabyrinthV5Builder.RootName);
        if (v4 == null || v5 == null) throw new InvalidOperationException("V4/V5 roots are required before V6 dressing.");

        var baseline = CollectMetrics(mapRoot);
        var v5BuilderSha = Sha256File(V5BuilderPath);
        var v5TopologySha = ComputeTopologySignature(v5);

        CreateTextureAssets();
        CreateMaterials();

        var root = Child(mapRoot, RootName);
        Marker(root, "V6_META_V5_BUILDER_SHA256_" + v5BuilderSha);
        Marker(root, "V6_META_V5_TOPOLOGY_SHA256_" + v5TopologySha);
        Marker(root, "V6_META_BASELINE_COLLIDERS_" + baseline.Colliders);
        Marker(root, "V6_META_BASELINE_RENDERERS_" + baseline.Renderers);
        Marker(root, "V6_META_BASELINE_VERTICES_" + baseline.Vertices);
        Marker(root, "V6_META_BASELINE_TRIANGLES_" + baseline.Triangles);
        Marker(root, "V6_META_SCOPE_FICTIONALIZED_PRODUCTION_READABILITY");
        Marker(root, "V6_META_TARGET_TEMPLE_HUB_DENSE_CORE");

        var assignments = ApplyMaterialPass(v4, v5);
        Marker(root, "V6_META_MATERIAL_ASSIGNMENTS_" + assignments);
        BuildTempleHubColonnade(root);
        TuneExistingLights(v5);

        var added = CollectMetrics(root);
        if (added.Renderers > MaximumAddedRenderers || added.Vertices > MaximumAddedVertices || added.Triangles > MaximumAddedTriangles)
        {
            throw new InvalidOperationException(
                "V6 dressing exceeds its static budget: renderers=" + added.Renderers +
                " vertices=" + added.Vertices + " triangles=" + added.Triangles);
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log(
            "CHANNEL_PLAY_KHUFU_V6_BUILD result=built assignments=" + assignments +
            " renderers=" + added.Renderers + " vertices=" + added.Vertices + " triangles=" + added.Triangles);
    }

    [MenuItem("Channel Play/Khufu V6/Rebuild Validate Render")]
    public static void RebuildValidateRender()
    {
        Rebuild();
        ChannelPlayKhufuMegaLabyrinthV5Builder.Validate();
        ChannelPlayKhufuV6VisualSliceValidator.ValidateMenu();
        ChannelPlayKhufuV6VisualSliceScreenshotExporter.ExportScreenshots();
    }

    public static string AlbedoPath(string surfaceName)
    {
        return TextureRoot + "/V6_" + surfaceName + "_Albedo.png";
    }

    public static string NormalPath(string surfaceName)
    {
        return TextureRoot + "/V6_" + surfaceName + "_Normal.png";
    }

    public static string MaterialPath(string materialName)
    {
        return MaterialRoot + "/" + materialName + ".mat";
    }

    public static Material LoadMaterial(string materialName)
    {
        return AssetDatabase.LoadAssetAtPath<Material>(MaterialPath(materialName));
    }

    public static Metrics CollectMetrics(Transform root)
    {
        var metrics = new Metrics();
        if (root == null) return metrics;

        metrics.Renderers = root.GetComponentsInChildren<Renderer>(true).Length;
        metrics.Colliders = root.GetComponentsInChildren<Collider>(true).Length;
        foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
        {
            var mesh = filter.sharedMesh;
            if (mesh == null) continue;
            metrics.Vertices += mesh.vertexCount;
            for (var subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
                metrics.Triangles += (int)mesh.GetIndexCount(subMesh) / 3;
        }
        return metrics;
    }

    public static string ComputeTopologySignature(Transform root)
    {
        if (root == null) return string.Empty;
        var builder = new StringBuilder();
        var transforms = root.GetComponentsInChildren<Transform>(true)
            .OrderBy(item => HierarchyPath(item, root), StringComparer.Ordinal)
            .ToArray();
        foreach (var item in transforms)
        {
            builder.Append(HierarchyPath(item, root)).Append('|');
            AppendVector(builder, item.localPosition);
            AppendQuaternion(builder, item.localRotation);
            AppendVector(builder, item.localScale);
            var filter = item.GetComponent<MeshFilter>();
            if (filter != null && filter.sharedMesh != null)
                builder.Append("mesh=").Append(filter.sharedMesh.name).Append(':').Append(filter.sharedMesh.vertexCount).Append('|');
            var collider = item.GetComponent<Collider>();
            if (collider != null)
                builder.Append("collider=").Append(collider.GetType().Name).Append(':').Append(collider.enabled).Append(':').Append(collider.isTrigger).Append('|');
            builder.AppendLine();
        }
        return Sha256Text(builder.ToString());
    }

    public static string ComputeVisualSignature(Transform root)
    {
        if (root == null) return string.Empty;
        var builder = new StringBuilder(ComputeTopologySignature(root));
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true)
                     .OrderBy(item => HierarchyPath(item.transform, root), StringComparer.Ordinal))
        {
            builder.Append(HierarchyPath(renderer.transform, root)).Append('=');
            foreach (var material in renderer.sharedMaterials)
                builder.Append(material == null ? "null" : material.name).Append(',');
            builder.AppendLine();
        }
        foreach (var surface in SurfaceNames)
        {
            builder.Append(surface).Append(':').Append(Sha256File(AlbedoPath(surface))).Append(':')
                .Append(Sha256File(NormalPath(surface))).AppendLine();
        }
        return Sha256Text(builder.ToString());
    }

    public static string Sha256File(string path)
    {
        if (!File.Exists(path)) return string.Empty;
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return ToHex(sha.ComputeHash(stream));
    }

    private static void CreateTextureAssets()
    {
        Directory.CreateDirectory(TextureRoot);
        foreach (var surface in Surfaces)
        {
            float[] heights;
            var albedoBytes = BuildAlbedo(surface, out heights);
            var normalBytes = BuildNormal(surface, heights);
            ImportTexture(AlbedoPath(surface.Name), albedoBytes, false);
            ImportTexture(NormalPath(surface.Name), normalBytes, true);
        }
    }

    private static byte[] BuildAlbedo(SurfaceSpec spec, out float[] heights)
    {
        var texture = new Texture2D(TextureSize, TextureSize, TextureFormat.RGBA32, false, false);
        var pixels = new Color32[TextureSize * TextureSize];
        heights = new float[pixels.Length];
        for (var y = 0; y < TextureSize; y++)
        {
            var row = y / spec.BlockHeight;
            var offset = row % 2 == 0 ? 0 : spec.BlockWidth / 2;
            for (var x = 0; x < TextureSize; x++)
            {
                var shiftedX = PositiveMod(x + offset, spec.BlockWidth);
                var localY = PositiveMod(y, spec.BlockHeight);
                var grout = shiftedX < spec.Grout || shiftedX >= spec.BlockWidth - spec.Grout ||
                            localY < spec.Grout || localY >= spec.BlockHeight - spec.Grout;
                var blockX = (x + offset) / spec.BlockWidth;
                var blockNoise = Noise(blockX, row, spec.Seed);
                var fineNoise = Noise(x, y, spec.Seed + 97);
                var weather = Mathf.Sin((x + spec.Seed) * 0.031f) * Mathf.Sin((y - spec.Seed) * 0.019f) * 0.035f;
                var speckleNoise = Noise(x * 3, y * 5, spec.Seed + 503);
                var baseColor = grout ? spec.GroutColor : spec.BaseColor;
                var brightness = grout
                    ? 0.82f + fineNoise * 0.12f
                    : 0.88f + blockNoise * 0.18f + (fineNoise - 0.5f) * 0.08f + weather;
                if (!grout && speckleNoise > 1f - spec.Speckle)
                    brightness *= speckleNoise > 1f - spec.Speckle * 0.35f ? 1.18f : 0.78f;

                var color = new Color(
                    Mathf.Clamp01(baseColor.r * brightness),
                    Mathf.Clamp01(baseColor.g * brightness),
                    Mathf.Clamp01(baseColor.b * brightness),
                    1f);
                var index = y * TextureSize + x;
                pixels[index] = color;
                var edgeDistance = Mathf.Min(
                    Mathf.Min(shiftedX, spec.BlockWidth - 1 - shiftedX),
                    Mathf.Min(localY, spec.BlockHeight - 1 - localY));
                var edgeWear = Mathf.Clamp01(edgeDistance / Mathf.Max(1f, spec.Grout * 2f));
                heights[index] = grout ? 0.16f + fineNoise * 0.03f : 0.62f + edgeWear * 0.18f + (fineNoise - 0.5f) * 0.06f;
            }
        }
        texture.SetPixels32(pixels);
        texture.Apply(false, false);
        var bytes = texture.EncodeToPNG();
        UnityEngine.Object.DestroyImmediate(texture);
        return bytes;
    }

    private static byte[] BuildNormal(SurfaceSpec spec, float[] heights)
    {
        var texture = new Texture2D(TextureSize, TextureSize, TextureFormat.RGBA32, false, true);
        var pixels = new Color32[TextureSize * TextureSize];
        for (var y = 0; y < TextureSize; y++)
        {
            for (var x = 0; x < TextureSize; x++)
            {
                var left = heights[y * TextureSize + PositiveMod(x - 1, TextureSize)];
                var right = heights[y * TextureSize + PositiveMod(x + 1, TextureSize)];
                var down = heights[PositiveMod(y - 1, TextureSize) * TextureSize + x];
                var up = heights[PositiveMod(y + 1, TextureSize) * TextureSize + x];
                var normal = new Vector3((left - right) * spec.NormalStrength, (down - up) * spec.NormalStrength, 1f).normalized;
                pixels[y * TextureSize + x] = new Color(
                    normal.x * 0.5f + 0.5f,
                    normal.y * 0.5f + 0.5f,
                    normal.z * 0.5f + 0.5f,
                    1f);
            }
        }
        texture.SetPixels32(pixels);
        texture.Apply(false, false);
        var bytes = texture.EncodeToPNG();
        UnityEngine.Object.DestroyImmediate(texture);
        return bytes;
    }

    private static void ImportTexture(string path, byte[] bytes, bool normalMap)
    {
        if (!File.Exists(path) || !File.ReadAllBytes(path).SequenceEqual(bytes)) File.WriteAllBytes(path, bytes);
        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null) throw new InvalidOperationException("Texture importer missing: " + path);
        importer.textureType = normalMap ? TextureImporterType.NormalMap : TextureImporterType.Default;
        importer.sRGBTexture = !normalMap;
        importer.alphaSource = TextureImporterAlphaSource.None;
        importer.mipmapEnabled = true;
        importer.wrapMode = TextureWrapMode.Repeat;
        importer.filterMode = FilterMode.Trilinear;
        importer.anisoLevel = 4;
        importer.maxTextureSize = TextureSize;
        importer.textureCompression = TextureImporterCompression.CompressedHQ;
        importer.SaveAndReimport();
    }

    private static void CreateMaterials()
    {
        Directory.CreateDirectory(MaterialRoot);
        var shader = Shader.Find("Standard");
        if (shader == null) throw new InvalidOperationException("Built-in Standard shader is unavailable.");
        foreach (var spec in Materials)
        {
            var path = MaterialPath(spec.Name);
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, path);
            }
            else
            {
                material.shader = shader;
            }

            var albedo = AssetDatabase.LoadAssetAtPath<Texture2D>(AlbedoPath(spec.SurfaceName));
            var normal = AssetDatabase.LoadAssetAtPath<Texture2D>(NormalPath(spec.SurfaceName));
            if (albedo == null || normal == null) throw new InvalidOperationException("V6 texture pair missing for " + spec.SurfaceName);

            material.name = spec.Name;
            material.color = spec.Tint;
            material.SetTexture("_MainTex", albedo);
            material.SetTextureScale("_MainTex", spec.Tiling);
            material.SetTexture("_BumpMap", normal);
            material.SetTextureScale("_BumpMap", spec.Tiling);
            material.SetFloat("_BumpScale", 0.72f);
            material.SetFloat("_Metallic", spec.Metallic);
            material.SetFloat("_Glossiness", spec.Smoothness);
            material.EnableKeyword("_NORMALMAP");
            material.enableInstancing = true;
            material.doubleSidedGI = false;
            EditorUtility.SetDirty(material);
        }
        AssetDatabase.SaveAssets();
    }

    private static int ApplyMaterialPass(Transform v4, Transform v5)
    {
        var tura = LoadMaterial("V6_Tura_Casing");
        var core = LoadMaterial("V6_Core_Limestone");
        var interior = LoadMaterial("V6_Interior_Limestone");
        var basalt = LoadMaterial("V6_Basalt_Court");
        var granite = LoadMaterial("V6_Red_Granite");
        var causeway = LoadMaterial("V6_Causeway_Limestone");
        var scanInlay = LoadMaterial("V6_Scan_Inlay");
        var assignments = 0;

        foreach (var renderer in v4.GetComponentsInChildren<Renderer>(true))
        {
            var sourceName = renderer.sharedMaterial == null ? string.Empty : renderer.sharedMaterial.name;
            Material target = null;
            if (sourceName == "PyramidV4_Tura_Casing" || sourceName == "PyramidV4_Casing_Trim") target = tura;
            else if (sourceName == "PyramidV4_Core_Limestone") target = core;
            else if (sourceName == "PyramidV4_Interior_Limestone" || sourceName == "PyramidV3_Passage_Floor") target = interior;
            else if (sourceName == "PyramidV3_Red_Granite") target = granite;
            if (target == null) continue;
            renderer.sharedMaterial = target;
            assignments++;
        }

        assignments += AssignDistrict(v5, "Pyramid_Temple_Hub", basalt, granite, granite);
        assignments += AssignDistrict(v5, "Authentic_Interior_Spine", interior, core, core);
        assignments += AssignDistrict(v5, "Covered_Causeway", causeway, causeway, causeway);
        assignments += AssignDistrict(v5, "Valley_Gate", causeway, granite, granite);
        var hubObservation = v5.Find("V5_District_Pyramid_Temple_Hub/V5_Observation_Only_Pyramid_Temple_Hub");
        var hubObservationRenderer = hubObservation == null ? null : hubObservation.GetComponent<Renderer>();
        if (hubObservationRenderer != null)
        {
            hubObservationRenderer.sharedMaterial = scanInlay;
            assignments++;
        }
        return assignments;
    }

    private static int AssignDistrict(Transform v5, string districtName, Material floor, Material pylon, Material lintel)
    {
        var district = v5.Find("V5_District_" + districtName);
        if (district == null) throw new InvalidOperationException("V6 target district missing: " + districtName);
        var assignments = 0;
        foreach (var renderer in district.GetComponentsInChildren<Renderer>(true))
        {
            Material target = null;
            if (renderer.name.EndsWith("_Floor", StringComparison.Ordinal)) target = floor;
            else if (renderer.name.IndexOf("_Pylon_", StringComparison.Ordinal) >= 0) target = pylon;
            else if (renderer.name.EndsWith("_Lintel", StringComparison.Ordinal)) target = lintel;
            if (target == null) continue;
            renderer.sharedMaterial = target;
            assignments++;
        }
        return assignments;
    }

    private static void BuildTempleHubColonnade(Transform root)
    {
        var colonnade = Child(root, "V6_Temple_Hub_Red_Granite_Colonnade_Fictionalized");
        var granite = LoadMaterial("V6_Red_Granite");
        var tura = LoadMaterial("V6_Tura_Casing");
        var positions = new[]
        {
            new Vector3(57f, 0f, -4.3f),
            new Vector3(57f, 0f, 4.3f),
            new Vector3(67f, 0f, -4.3f),
            new Vector3(67f, 0f, 4.3f),
        };
        for (var i = 0; i < positions.Length; i++)
        {
            var position = positions[i];
            DecorativePrimitive(PrimitiveType.Cylinder, "V6_Red_Granite_Column_" + i, colonnade, position + Vector3.up * 3.62f, new Vector3(0.66f, 2.18f, 0.66f), granite);
            if (position.z < 0f)
            {
                DecorativePrimitive(PrimitiveType.Cube, "V6_Column_Base_" + i, colonnade, position + Vector3.up * 1.22f, new Vector3(1.65f, 0.42f, 1.65f), tura);
                DecorativePrimitive(PrimitiveType.Cube, "V6_Column_Capital_" + i, colonnade, position + Vector3.up * 5.98f, new Vector3(1.9f, 0.46f, 1.9f), tura);
            }
        }
        DecorativePrimitive(PrimitiveType.Cube, "V6_Colonnade_Lintel_Front", colonnade, new Vector3(62f, 6.25f, -4.3f), new Vector3(12f, 0.58f, 1.55f), tura);
        DecorativePrimitive(PrimitiveType.Cube, "V6_Colonnade_Lintel_Rear", colonnade, new Vector3(62f, 6.25f, 4.3f), new Vector3(12f, 0.58f, 1.55f), tura);
        DecorativePrimitive(PrimitiveType.Cube, "V6_Offering_Altar_Fictionalized", colonnade, new Vector3(62f, 1.55f, 0f), new Vector3(3.4f, 1.1f, 2.2f), granite);
    }

    private static void TuneExistingLights(Transform v5)
    {
        var key = v5.Find("V5_Key_Light");
        var keyLight = key == null ? null : key.GetComponent<Light>();
        if (keyLight != null)
        {
            keyLight.intensity = 0.34f;
            keyLight.color = new Color(1f, 0.80f, 0.62f);
            keyLight.shadows = LightShadows.None;
        }
        foreach (var light in v5.GetComponentsInChildren<Light>(true))
        {
            if (light == keyLight) continue;
            light.intensity = Mathf.Min(light.intensity, 1.35f);
            light.shadows = LightShadows.None;
        }
    }

    private static GameObject DecorativePrimitive(PrimitiveType type, string name, Transform parent, Vector3 position, Vector3 scale, Material material)
    {
        var go = GameObject.CreatePrimitive(type);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.position = position;
        go.transform.localScale = scale;
        var collider = go.GetComponent<Collider>();
        if (collider != null) UnityEngine.Object.DestroyImmediate(collider);
        var renderer = go.GetComponent<Renderer>();
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        return go;
    }

    private static Transform Child(Transform parent, string name)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        return go.transform;
    }

    private static void Marker(Transform parent, string name)
    {
        Child(parent, name);
    }

    private static string HierarchyPath(Transform item, Transform root)
    {
        var names = new List<string>();
        var cursor = item;
        while (cursor != null)
        {
            names.Add(cursor.name);
            if (cursor == root) break;
            cursor = cursor.parent;
        }
        names.Reverse();
        return string.Join("/", names);
    }

    private static void AppendVector(StringBuilder builder, Vector3 value)
    {
        builder.Append(value.x.ToString("R", CultureInfo.InvariantCulture)).Append(',')
            .Append(value.y.ToString("R", CultureInfo.InvariantCulture)).Append(',')
            .Append(value.z.ToString("R", CultureInfo.InvariantCulture)).Append('|');
    }

    private static void AppendQuaternion(StringBuilder builder, Quaternion value)
    {
        builder.Append(value.x.ToString("R", CultureInfo.InvariantCulture)).Append(',')
            .Append(value.y.ToString("R", CultureInfo.InvariantCulture)).Append(',')
            .Append(value.z.ToString("R", CultureInfo.InvariantCulture)).Append(',')
            .Append(value.w.ToString("R", CultureInfo.InvariantCulture)).Append('|');
    }

    private static int PositiveMod(int value, int divisor)
    {
        var result = value % divisor;
        return result < 0 ? result + divisor : result;
    }

    private static float Noise(int x, int y, int seed)
    {
        unchecked
        {
            var value = (uint)(x * 374761393 + y * 668265263 + seed * 69069);
            value = (value ^ (value >> 13)) * 1274126177u;
            value ^= value >> 16;
            return (value & 0x00ffffffu) / 16777215f;
        }
    }

    private static string Sha256Text(string value)
    {
        using (var sha = SHA256.Create()) return ToHex(sha.ComputeHash(Encoding.UTF8.GetBytes(value)));
    }

    private static string ToHex(byte[] bytes)
    {
        var builder = new StringBuilder(bytes.Length * 2);
        foreach (var value in bytes) builder.Append(value.ToString("x2"));
        return builder.ToString();
    }

    public struct Metrics
    {
        public int Renderers;
        public int Vertices;
        public int Triangles;
        public int Colliders;
    }

    private sealed class SurfaceSpec
    {
        public readonly string Name;
        public readonly Color BaseColor;
        public readonly Color GroutColor;
        public readonly int BlockWidth;
        public readonly int BlockHeight;
        public readonly int Grout;
        public readonly int Seed;
        public readonly float Speckle;
        public readonly float NormalStrength;

        public SurfaceSpec(string name, Color baseColor, Color groutColor, int blockWidth, int blockHeight, int grout, int seed, float speckle, float normalStrength)
        {
            Name = name;
            BaseColor = baseColor;
            GroutColor = groutColor;
            BlockWidth = blockWidth;
            BlockHeight = blockHeight;
            Grout = grout;
            Seed = seed;
            Speckle = speckle;
            NormalStrength = normalStrength;
        }
    }

    private sealed class MaterialSpec
    {
        public readonly string Name;
        public readonly string SurfaceName;
        public readonly Vector2 Tiling;
        public readonly float Metallic;
        public readonly float Smoothness;
        public readonly Color Tint;

        public MaterialSpec(string name, string surfaceName, Vector2 tiling, float metallic, float smoothness)
            : this(name, surfaceName, tiling, metallic, smoothness, Color.white)
        {
        }

        public MaterialSpec(string name, string surfaceName, Vector2 tiling, float metallic, float smoothness, Color tint)
        {
            Name = name;
            SurfaceName = surfaceName;
            Tiling = tiling;
            Metallic = metallic;
            Smoothness = smoothness;
            Tint = tint;
        }
    }
}

using System.Collections.Generic;
using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

namespace ChannelPlay.Gameplay
{
    internal static class ChannelPlayAssetRuntime
    {
        public const string PointGainEvent = "point_gain";
        public const string InteractEvent = "object_interact";
        public const string WarningEvent = "danger_warning";
        public const string EliminatedEvent = "contestant_eliminated";
        public const string RoundStartEvent = "round_start";
        public const string RoundEndEvent = "round_end";

        private const string MapPath = "Assets/_Project/Art/Maps/SchoolStage/CP_Map_SchoolStage_Blockout.fbx";
        private const string PropsPath = "Assets/_Project/Art/Props/CP_Props_Interaction.fbx";
        private const string PlayerPath = "Assets/_Project/Art/Characters/Player/CP_Char_PlayerProxy.fbx";
        private const string ContestantPath = "Assets/_Project/Art/Characters/Contestant/CP_Char_ContestantProxy.fbx";
        private const string OperatorPath = "Assets/_Project/Art/Characters/Operator/CP_Char_OperatorProxy.fbx";

        private static readonly Dictionary<string, string> AudioPaths = new Dictionary<string, string>
        {
            { PointGainEvent, "Assets/_Project/Audio/MVP/CP_SFX_PointGain.wav" },
            { InteractEvent, "Assets/_Project/Audio/MVP/CP_SFX_Interact.wav" },
            { WarningEvent, "Assets/_Project/Audio/MVP/CP_SFX_Warning.wav" },
            { EliminatedEvent, "Assets/_Project/Audio/MVP/CP_SFX_Eliminated.wav" },
            { RoundStartEvent, "Assets/_Project/Audio/MVP/CP_Stinger_RoundStart.wav" },
            { RoundEndEvent, "Assets/_Project/Audio/MVP/CP_Stinger_RoundEnd.wav" },
        };

        public static bool InstantiateMapVisuals(Transform parent)
        {
            var created = false;
            created |= InstantiateAsset(parent, MapPath, "Asset_Map_SchoolStage", Vector3.zero, Quaternion.identity, Vector3.one) != null;
            created |= InstantiateAsset(parent, PropsPath, "Asset_Props_Interaction", Vector3.zero, Quaternion.identity, Vector3.one) != null;
            created |= InstantiateAsset(parent, OperatorPath, "Asset_Operator", new Vector3(0f, 0f, 0f), Quaternion.identity, Vector3.one) != null;
            return created;
        }

        public static void HideGeometryProxyRenderers(Transform root)
        {
            var prefixes = new[]
            {
                "Runtime_Floor",
                "Runtime_Back_Wall",
                "Runtime_Front_Wall",
                "Runtime_Left_Wall",
                "Runtime_Right_Wall",
                "Runtime_Center_Table",
                "Runtime_Cover_",
                "Runtime_Blue_Spawn",
                "Runtime_Red_Spawn",
            };

            for (var index = 0; index < root.childCount; index++)
            {
                var child = root.GetChild(index);
                foreach (var prefix in prefixes)
                {
                    if (!child.name.StartsWith(prefix, System.StringComparison.Ordinal))
                    {
                        continue;
                    }

                    var renderer = child.GetComponent<Renderer>();
                    if (renderer != null)
                    {
                        renderer.enabled = false;
                    }
                }
            }
        }

        public static void AttachPlayerVisual(Transform host, Material fallbackMaterial)
        {
            AttachCharacterVisual(host, PlayerPath, "Asset_Player_Visual", fallbackMaterial, new Vector3(1f, 1f, 1f));
        }

        public static void AttachContestantVisual(Transform host, Material fallbackMaterial)
        {
            AttachCharacterVisual(host, ContestantPath, "Asset_Contestant_Visual", fallbackMaterial, new Vector3(1f, 1f, 1f));
        }

        public static AudioSource EnsureAudioSource(GameObject host)
        {
            var source = host.GetComponent<AudioSource>();
            if (source == null)
            {
                source = host.AddComponent<AudioSource>();
            }

            source.playOnAwake = false;
            source.spatialBlend = 0f;
            source.volume = 0.75f;
            return source;
        }

        public static void PlaySfx(AudioSource source, string eventName)
        {
            if (source == null || !AudioPaths.TryGetValue(eventName, out var path))
            {
                return;
            }

            var clip = LoadAsset<AudioClip>(path);
            if (clip != null)
            {
                source.PlayOneShot(clip);
            }
        }

        private static void AttachCharacterVisual(Transform host, string assetPath, string childName, Material fallbackMaterial, Vector3 localScale)
        {
            if (host.Find(childName) != null)
            {
                return;
            }

            var directRenderer = host.GetComponent<Renderer>();
            if (directRenderer != null)
            {
                directRenderer.enabled = false;
            }

            var visual = InstantiateAsset(host, assetPath, childName, Vector3.zero, Quaternion.identity, localScale);
            if (visual == null)
            {
                if (directRenderer != null)
                {
                    directRenderer.enabled = true;
                    directRenderer.sharedMaterial = fallbackMaterial;
                }

                return;
            }

            DisableChildColliders(visual);
            ApplyFallbackMaterialIfNeeded(visual, fallbackMaterial);
            EnsureAnimator(visual);
        }

        private static GameObject InstantiateAsset(Transform parent, string assetPath, string name, Vector3 localPosition, Quaternion localRotation, Vector3 localScale)
        {
            if (parent.Find(name) != null)
            {
                return parent.Find(name).gameObject;
            }

            var prefab = LoadAsset<GameObject>(assetPath);
            if (prefab == null)
            {
                return null;
            }

            var instance = UnityEngine.Object.Instantiate(prefab, parent);
            instance.name = name;
            instance.transform.localPosition = localPosition;
            instance.transform.localRotation = localRotation;
            instance.transform.localScale = localScale;
            return instance;
        }

        private static void DisableChildColliders(GameObject root)
        {
            foreach (var collider in root.GetComponentsInChildren<Collider>())
            {
                collider.enabled = false;
            }
        }

        private static void ApplyFallbackMaterialIfNeeded(GameObject root, Material material)
        {
            if (material == null)
            {
                return;
            }

            foreach (var renderer in root.GetComponentsInChildren<Renderer>())
            {
                if (renderer.sharedMaterial == null)
                {
                    renderer.sharedMaterial = material;
                }
            }
        }

        private static void EnsureAnimator(GameObject root)
        {
            if (root.GetComponentInChildren<Animator>() == null)
            {
                root.AddComponent<Animator>();
            }
        }

        private static T LoadAsset<T>(string path) where T : UnityEngine.Object
        {
#if UNITY_EDITOR
            return AssetDatabase.LoadAssetAtPath<T>(path);
#else
            return null;
#endif
        }
    }
}

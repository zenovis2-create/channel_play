using System;
using ChannelPlay.Player;
using UnityEditor;
using UnityEngine;

public static class ChannelPlayCameraCutawayValidator
{
    [MenuItem("Channel Play/Validate Camera Cutaway")]
    public static void ValidateCameraCutaway()
    {
        var root = new GameObject("CP_Camera_Cutaway_Test_Root");
        var cameraObject = new GameObject("CP_Camera_Cutaway_Test_Camera");
        try
        {
            var target = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            target.name = "CP_Camera_Cutaway_Test_Target";
            target.transform.SetParent(root.transform);
            target.transform.position = new Vector3(0f, 1.2f, 0f);

            var wall = Occluder(root.transform, "Interior_Hypostyle_Ceiling_Beam_Test", new Vector3(0f, 4f, -2.5f), new Vector3(4.5f, 1.6f, 0.5f));
            var rearPylon = Occluder(root.transform, "V5_Valley_Gate_Pylon_-1", new Vector3(0f, 3f, -7f), new Vector3(5f, 6f, 2f));
            var frontPylon = Occluder(root.transform, "V5_Valley_Gate_Pylon_1", new Vector3(0f, 5.2f, -4.5f), new Vector3(4.5f, 1.6f, 0.5f));
            var unrelatedPylon = Occluder(root.transform, "V5_Covered_Causeway_Pylon_1", new Vector3(0f, 4.6f, -3.5f), new Vector3(4.5f, 1.6f, 0.5f));
            var wallRenderer = wall.GetComponent<Renderer>();
            var rearRenderer = rearPylon.GetComponent<Renderer>();
            var frontRenderer = frontPylon.GetComponent<Renderer>();
            var unrelatedRenderer = unrelatedPylon.GetComponent<Renderer>();

            var camera = cameraObject.AddComponent<Camera>();
            camera.transform.position = new Vector3(0f, 7.3f, -8f);
            camera.transform.LookAt(target.transform.position + Vector3.up * 1.35f);

            var cutaway = cameraObject.AddComponent<ChannelCameraOccluderCutaway>();
            cutaway.Configure(target.transform, root.transform);
            var hiddenCount = cutaway.ForceRefresh();

            foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
            {
                var bounds = renderer.bounds;
                Debug.Log(
                    "CHANNEL_PLAY_CAMERA_CUTAWAY_DIAGNOSTIC name=\"" + renderer.name + "\"" +
                    " active=" + renderer.gameObject.activeInHierarchy + " enabled=" + renderer.enabled +
                    " bounds_center=" + bounds.center.ToString("F3") + " bounds_size=" + bounds.size.ToString("F3") +
                    " force_off=" + renderer.forceRenderingOff + " state=\"" + cutaway.DiagnosticCandidateState(renderer) + "\"");
            }
            Debug.Log("CHANNEL_PLAY_CAMERA_CUTAWAY_DIAGNOSTIC ray_origin=" + camera.transform.position.ToString("F3") +
                " target=" + (target.transform.position + Vector3.up * 1.35f).ToString("F3") +
                " hidden=" + hiddenCount + " valley=" + cutaway.DiagnosticActiveValleyGatePylonCount +
                " visible=" + cutaway.DiagnosticVisibleOccluderCount());

            if (hiddenCount != 3 || wallRenderer == null || rearRenderer == null || frontRenderer == null || unrelatedRenderer == null ||
                !wallRenderer.forceRenderingOff || rearRenderer.enabled || frontRenderer.enabled ||
                !unrelatedRenderer.enabled || unrelatedRenderer.forceRenderingOff ||
                cutaway.DiagnosticActiveValleyGatePylonCount != 2 || cutaway.DiagnosticVisibleOccluderCount() != 0)
            {
                throw new InvalidOperationException("Camera cutaway did not apply the exact Valley Gate pylon scope.");
            }

            wall.transform.position = new Vector3(8f, 1.35f, 0f);
            rearPylon.transform.position = new Vector3(8f, 1.35f, 0f);
            frontPylon.transform.position = new Vector3(8f, 1.35f, 0f);
            var restoredCount = cutaway.ForceRefresh();
            if (restoredCount != 0 || wallRenderer.forceRenderingOff || !rearRenderer.enabled || rearRenderer.forceRenderingOff ||
                !frontRenderer.enabled || frontRenderer.forceRenderingOff || !unrelatedRenderer.enabled || unrelatedRenderer.forceRenderingOff)
            {
                throw new InvalidOperationException("Camera cutaway did not restore the renderer after obstruction moved away.");
            }

            Debug.Log($"CHANNEL_PLAY_CAMERA_CUTAWAY result=passed hidden={hiddenCount} valley_pylons=2 unrelated_pylons=0 restored={restoredCount}");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(cameraObject);
            UnityEngine.Object.DestroyImmediate(root);
        }
    }

    private static GameObject Occluder(Transform parent, string name, Vector3 position, Vector3 scale)
    {
        var result = GameObject.CreatePrimitive(PrimitiveType.Cube);
        result.name = name;
        result.transform.SetParent(parent);
        result.transform.position = position;
        result.transform.localScale = scale;
        return result;
    }
}

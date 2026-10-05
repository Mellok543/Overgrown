using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

// Wires the shears animator into the open scene and play-tests it:
//  edit mode : FP_Shears.controller -> arms Animator, PlayerItemInventory.armsAnimator / gardenShearsObject
//  play mode : GiveGardenShears(), capture idle, PlayGardenShearsCut() (the game's own trigger path),
//              capture the fully closed frame, capture after the return, log blade angle / hand distance per frame.
// Output: Logs/FP_Shears_PlayTest.txt + Logs/FP_Shears_*.png. Runs when Logs/FP_Shears_PlayTest.request exists,
// or via Tools/Overgrown/Play-Test Shears Animations.
[InitializeOnLoad]
public static class ShearsPlayModeTest
{
    private const string RequestPath = "Logs/FP_Shears_PlayTest.request";
    private const string ReportPath = "Logs/FP_Shears_PlayTest.txt";
    private const string ControllerPath = "Assets/Art/Models/Player/Animations/FP_Shears.controller";
    private const string StageKey = "ShearsPlayTest.Stage";
    private const string LogKey = "ShearsPlayTest.Log";

    private static double startTime;
    private static double cutTime = -1;
    private static bool givenShears, idleShot, closedShot, afterShot;
    private static float minAngle = 999f, maxAngle = -1f, minHands = 999f, maxHands = -1f;
    private static readonly StringBuilder frameLog = new StringBuilder();

    private static double nextPoll;

    static ShearsPlayModeTest()
    {
        EditorApplication.playModeStateChanged += OnPlayModeChanged;
        EditorApplication.update += PollRequest;            // the request file may appear after this assembly loaded
    }

    private static void PollRequest()
    {
        if (EditorApplication.timeSinceStartup < nextPoll)
            return;
        nextPoll = EditorApplication.timeSinceStartup + 1.0;
        if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
            return;
        if (File.Exists(RequestPath) && SessionState.GetInt(StageKey, 0) == 0)
            Begin();
    }

    [MenuItem("Tools/Overgrown/Play-Test Shears Animations")]
    public static void Begin()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            return;
        if (File.Exists(RequestPath))
            File.Delete(RequestPath);

        ShearsAnimationSetup.Run();
        var log = new StringBuilder();
        log.AppendLine("FP_Shears play-mode test  " + System.DateTime.Now);

        Animator arms = FindArmsAnimator();
        var controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(ControllerPath);
        if (arms == null || controller == null)
        {
            File.WriteAllText(ReportPath, log + $"FAILED: arms animator {(arms == null ? "not found" : "ok")}, controller {(controller == null ? "missing" : "ok")}");
            return;
        }
        log.AppendLine($"Arms animator: {Path(arms.transform)}  previous controller: {(arms.runtimeAnimatorController != null ? arms.runtimeAnimatorController.name : "NONE")}");
        Undo.RecordObject(arms, "Assign FP_Shears controller");
        arms.runtimeAnimatorController = controller;
        arms.applyRootMotion = false;
        arms.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        EditorUtility.SetDirty(arms);

        Transform shearsMesh = arms.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(r => r.name == "Garden_Shears_FP")?.transform;
        var inventory = Object.FindObjectsByType<PlayerItemInventory>(FindObjectsInactive.Include).FirstOrDefault();
        if (inventory != null)
        {
            var so = new SerializedObject(inventory);
            so.FindProperty("armsAnimator").objectReferenceValue = arms;
            if (shearsMesh != null)
                so.FindProperty("gardenShearsObject").objectReferenceValue = shearsMesh.gameObject;
            so.FindProperty("shearsCutTrigger").stringValue = "Cut";
            so.ApplyModifiedProperties();
            log.AppendLine($"PlayerItemInventory: armsAnimator + gardenShearsObject ({(shearsMesh != null ? shearsMesh.name : "MISSING")}) assigned, trigger 'Cut'");
        }
        else
        {
            log.AppendLine("PlayerItemInventory not found in the open scene");
        }
        EditorSceneManager.MarkSceneDirty(arms.gameObject.scene);

        SessionState.SetString(LogKey, log.ToString());
        SessionState.SetInt(StageKey, 1);
        EditorApplication.EnterPlaymode();
    }

    private static void OnPlayModeChanged(PlayModeStateChange change)
    {
        if (change == PlayModeStateChange.EnteredPlayMode && SessionState.GetInt(StageKey, 0) == 1)
        {
            SessionState.SetInt(StageKey, 2);
            startTime = EditorApplication.timeSinceStartup;
            cutTime = -1;
            givenShears = idleShot = closedShot = afterShot = false;
            frameLog.Clear();
            EditorApplication.update += Tick;
        }
        else if (change == PlayModeStateChange.EnteredEditMode && SessionState.GetInt(StageKey, 0) == 3)
        {
            SessionState.SetInt(StageKey, 0);
        }
    }

    private static void Tick()
    {
        if (!EditorApplication.isPlaying)
        {
            EditorApplication.update -= Tick;
            return;
        }

        double t = EditorApplication.timeSinceStartup - startTime;
        Animator arms = FindArmsAnimator();
        var inventory = Object.FindAnyObjectByType<PlayerItemInventory>();
        Camera cam = arms != null ? arms.GetComponentInParent<Camera>() : Camera.main;
        if (arms == null || inventory == null || cam == null)
        {
            Finish($"FAILED in play mode: arms={arms != null} inventory={inventory != null} camera={cam != null}");
            return;
        }

        Transform shA = FindBone(arms.transform, "Shears_A"), shB = FindBone(arms.transform, "Shears_B");
        Transform handR = FindBone(arms.transform, "Hand_R"), handL = FindBone(arms.transform, "Hand_L");
        float angle = Vector3.Angle(shA.forward, shB.forward);
        float hands = Vector3.Distance(handR.position, handL.position) * 100f;
        AnimatorStateInfo st = arms.GetCurrentAnimatorStateInfo(0);
        string state = st.IsName("ShearsCut") ? "ShearsCut" : st.IsName("ShearsIdle") ? "ShearsIdle" : "other";

        if (!givenShears && t > 1.0)
        {
            inventory.GiveGardenShears();
            givenShears = true;
        }
        if (givenShears && !idleShot && t > 2.0)
        {
            Capture(cam, "Logs/FP_Shears_PlayMode_Idle.png");
            frameLog.AppendLine($"IDLE   state={state} t={st.normalizedTime:F2} blade opening={angle:F1} deg  hands apart={hands:F1} cm  shears visible={IsShearsVisible(arms)}");
            idleShot = true;
            bool fired = inventory.PlayGardenShearsCut();          // the game's own call: ResetTrigger + SetTrigger("Cut")
            cutTime = EditorApplication.timeSinceStartup;
            frameLog.AppendLine($"PlayGardenShearsCut() returned {fired}");
            return;
        }
        if (cutTime > 0)
        {
            double dt = EditorApplication.timeSinceStartup - cutTime;
            if (dt < 0.9)
            {
                frameLog.AppendLine($"  +{dt:F3}s state={state} norm={st.normalizedTime:F2} blade={angle:F1} deg hands={hands:F1} cm");
                minAngle = Mathf.Min(minAngle, angle); maxAngle = Mathf.Max(maxAngle, angle);
                minHands = Mathf.Min(minHands, hands); maxHands = Mathf.Max(maxHands, hands);
            }
            if (!closedShot && state == "ShearsCut" && st.normalizedTime >= 0.46f)
            {
                Capture(cam, "Logs/FP_Shears_PlayMode_Closed.png");
                frameLog.AppendLine($"CLOSED shot at norm={st.normalizedTime:F2} blade={angle:F1} deg hands={hands:F1} cm");
                closedShot = true;
            }
            if (!afterShot && dt > 1.0)
            {
                Capture(cam, "Logs/FP_Shears_PlayMode_After.png");
                frameLog.AppendLine($"AFTER  state={state} blade={angle:F1} deg hands={hands:F1} cm");
                afterShot = true;
                Finish($"blade opening range during cut: {minAngle:F1} .. {maxAngle:F1} deg (travel {maxAngle - minAngle:F1} deg)\n" +
                       $"hand distance range during cut: {minHands:F1} .. {maxHands:F1} cm\n" +
                       $"closed frame captured: {closedShot}");
            }
        }
        if (t > 12)
            Finish("TIMEOUT");
    }

    private static void Finish(string summary)
    {
        EditorApplication.update -= Tick;
        File.WriteAllText(ReportPath, SessionState.GetString(LogKey, "") + frameLog + summary + "\n");
        SessionState.SetInt(StageKey, 3);
        EditorApplication.ExitPlaymode();
    }

    private static bool IsShearsVisible(Animator arms)
    {
        var r = arms.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(x => x.name == "Garden_Shears_FP");
        return r != null && r.gameObject.activeInHierarchy && r.enabled;
    }

    private static Animator FindArmsAnimator()
    {
        return Object.FindObjectsByType<Animator>(FindObjectsInactive.Include)
            .FirstOrDefault(a => FindBone(a.transform, "Shears_A") != null);
    }

    private static Transform FindBone(Transform root, string name)
    {
        return root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name && t.GetComponent<Renderer>() == null);
    }

    private static string Path(Transform t)
    {
        var parts = new List<string>();
        for (; t != null; t = t.parent)
            parts.Insert(0, t.name);
        return string.Join("/", parts);
    }

    private static void Capture(Camera cam, string path)
    {
        var rt = RenderTexture.GetTemporary(1280, 720, 24, RenderTextureFormat.ARGB32);
        var request = new RenderPipeline.StandardRequest();
        if (RenderPipeline.SupportsRenderRequest(cam, request))
        {
            request.destination = rt;
            RenderPipeline.SubmitRenderRequest(cam, request);
        }
        else
        {
            RenderTexture prev = cam.targetTexture;
            cam.targetTexture = rt;
            cam.Render();
            cam.targetTexture = prev;
        }
        RenderTexture active = RenderTexture.active;
        RenderTexture.active = rt;
        var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0);
        tex.Apply();
        RenderTexture.active = active;
        RenderTexture.ReleaseTemporary(rt);
        File.WriteAllBytes(path, tex.EncodeToPNG());
        Object.DestroyImmediate(tex);
    }
}

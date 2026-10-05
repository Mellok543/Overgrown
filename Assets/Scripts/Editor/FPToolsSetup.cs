using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

// Sickle / trimmer / mower first-person setup + play-mode verification.
//  Edit mode : import settings (via ShearsAnimationSetup), FP_Sickle / FP_Trimmer / FP_Mower controllers,
//              tool objects parented to the arm sockets (Tool_Sickle / Tool_Trimmer / Tool_Mower),
//              ToolInventory first-person fields, FPToolGroundFollow on the arms.
//  Play mode : selects every tool through ToolInventory, captures Idle + Work from the game camera at FOV 77,
//              logs animator states, socket attachment and ground clearance -> Logs/FP_Tools_PlayTest.txt.
// Runs when Logs/FP_Tools_PlayTest.request exists, or via Tools/Overgrown/Setup + Play-Test FP Tools.
[InitializeOnLoad]
public static class FPToolsSetup
{
    private const string Dir = "Assets/Art/Models/Player/Animations/";
    private const string RequestPath = "Logs/FP_Tools_PlayTest.request";
    private const string ReportPath = "Logs/FP_Tools_PlayTest.txt";
    private const string StageKey = "FPToolsTest.Stage";
    private const string LogKey = "FPToolsTest.Log";

    private static double nextPoll, startTime, swingTime = -1;
    private static int step;
    private static bool swingShot;
    private static float savedFov;
    private static readonly StringBuilder log = new StringBuilder();

    static FPToolsSetup()
    {
        EditorApplication.playModeStateChanged += OnPlayModeChanged;
        EditorApplication.update += PollRequest;
    }

    private static void PollRequest()
    {
        if (EditorApplication.timeSinceStartup < nextPoll)
            return;
        nextPoll = EditorApplication.timeSinceStartup + 1.0;
        if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
            return;
        if (File.Exists(RequestPath) && SessionState.GetInt(StageKey, 0) == 0)
            SetupAndPlay();
    }

    [MenuItem("Tools/Overgrown/Setup + Play-Test FP Tools")]
    public static void SetupAndPlay()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            return;
        if (File.Exists(RequestPath))
            File.Delete(RequestPath);

        var sb = new StringBuilder();
        sb.AppendLine("FP tools setup + play test  " + System.DateTime.Now);
        ShearsAnimationSetup.Run();                       // mask (now incl. Tool_ sockets), importers for all clip files

        var sickle = BuildController("FP_Sickle", "SickleIdle", "FP_Sickle_Idle", "SickleSwing", "FP_Sickle_Swing", "Swing", AnimatorControllerParameterType.Trigger, sb);
        var trimmer = BuildController("FP_Trimmer", "TrimmerIdle", "FP_Trimmer_Idle", "TrimmerWork", "FP_Trimmer_Work", "Working", AnimatorControllerParameterType.Bool, sb);
        var mower = BuildController("FP_Mower", "MowerIdle", "FP_Mower_Idle", "MowerPush", "FP_Mower_Push", "Moving", AnimatorControllerParameterType.Bool, sb);
        if (sickle == null || trimmer == null || mower == null)
        {
            File.WriteAllText(ReportPath, sb + "FAILED: controller(s) not built");
            return;
        }

        if (!WireScene(sickle, trimmer, mower, sb))
        {
            File.WriteAllText(ReportPath, sb.ToString());
            return;
        }

        SessionState.SetString(LogKey, sb.ToString());
        SessionState.SetInt(StageKey, 1);
        EditorApplication.EnterPlaymode();
    }

    // ------------------------------------------------------------------ controllers
    private static AnimatorController BuildController(string name, string idleState, string idleClipName,
        string workState, string workClipName, string param, AnimatorControllerParameterType type, StringBuilder sb)
    {
        AnimationClip idle = ShearsAnimationSetup.LoadClip(Dir + idleClipName + ".fbx");
        AnimationClip work = ShearsAnimationSetup.LoadClip(Dir + workClipName + ".fbx");
        if (idle == null || work == null)
        {
            sb.AppendLine($"{name}: clips missing ({idleClipName}={idle != null}, {workClipName}={work != null})");
            return null;
        }

        string path = Dir + name + ".controller";
        AnimatorController c = AssetDatabase.LoadAssetAtPath<AnimatorController>(path) ?? AnimatorController.CreateAnimatorControllerAtPath(path);
        foreach (AnimatorControllerParameter p in c.parameters)
            c.RemoveParameter(p);
        c.AddParameter(param, type);
        AnimatorStateMachine sm = c.layers[0].stateMachine;
        foreach (ChildAnimatorState st in sm.states)
            sm.RemoveState(st.state);

        AnimatorState a = sm.AddState(idleState, new Vector3(260, 80, 0));
        a.motion = idle;
        AnimatorState b = sm.AddState(workState, new Vector3(260, 200, 0));
        b.motion = work;
        sm.defaultState = a;

        AnimatorStateTransition ab = a.AddTransition(b);
        ab.hasExitTime = false;
        ab.hasFixedDuration = true;
        AnimatorStateTransition ba = b.AddTransition(a);
        ba.hasFixedDuration = true;
        if (type == AnimatorControllerParameterType.Trigger)
        {
            ab.AddCondition(AnimatorConditionMode.If, 0f, param);
            ab.duration = 0f;                      // the swing starts on the idle pose
            ba.hasExitTime = true;
            ba.exitTime = 0.92f;
            ba.duration = 0.03f;
        }
        else
        {
            ab.AddCondition(AnimatorConditionMode.If, 0f, param);
            ab.duration = 0.12f;
            ba.AddCondition(AnimatorConditionMode.IfNot, 0f, param);
            ba.hasExitTime = false;
            ba.duration = 0.15f;
        }
        EditorUtility.SetDirty(c);
        AssetDatabase.SaveAssets();
        AnimationClipSettings ws = AnimationUtility.GetAnimationClipSettings(work);
        AnimationClipSettings ids = AnimationUtility.GetAnimationClipSettings(idle);
        sb.AppendLine($"{name}.controller: {idleState} ({idle.length:F2}s loop={ids.loopTime}) <-> {workState} ({work.length:F2}s loop={ws.loopTime}), {type} {param}");
        return c;
    }

    // ------------------------------------------------------------------ scene wiring
    private static bool WireScene(RuntimeAnimatorController sickleC, RuntimeAnimatorController trimmerC, RuntimeAnimatorController mowerC, StringBuilder sb)
    {
        Animator arms = FindArms();
        var inv = Object.FindObjectsByType<ToolInventory>(FindObjectsInactive.Include).FirstOrDefault();
        if (arms == null || inv == null)
        {
            sb.AppendLine($"FAILED: arms animator {(arms != null)}, ToolInventory {(inv != null)}");
            return false;
        }

        var so = new SerializedObject(inv);
        var objects = new[] { ("sickleObject", "Tool_Sickle"), ("trimmerObject", "Tool_Trimmer"), ("mowerObject", "Tool_Mower") };
        foreach (var (field, socketName) in objects)
        {
            var go = so.FindProperty(field).objectReferenceValue as GameObject;
            Transform socket = FindNode(arms.transform, socketName);
            if (go == null || socket == null)
            {
                sb.AppendLine($"FAILED: {field}={(go != null)} socket {socketName}={(socket != null)}");
                return false;
            }
            Vector3 oldScale = go.transform.localScale;
            if (go.transform.parent != socket)
                Undo.SetTransformParent(go.transform, socket, "Parent tool to FP socket");
            Undo.RecordObject(go.transform, "Reset tool transform");
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = Vector3.one;
            sb.AppendLine($"{go.name} -> {Path(socket)} (local 0 / identity / scale 1; previous scale {oldScale})");
        }

        FPToolGroundFollow follow = arms.GetComponent<FPToolGroundFollow>() ?? Undo.AddComponent<FPToolGroundFollow>(arms.gameObject);
        var trimmerGo = so.FindProperty("trimmerObject").objectReferenceValue as GameObject;
        var mowerGo = so.FindProperty("mowerObject").objectReferenceValue as GameObject;
        Transform tgp = FindNode(trimmerGo.transform, "TrimmerGroundPoint");
        Transform mgp = FindNode(mowerGo.transform, "MowerGroundPoint");

        so.FindProperty("armsAnimator").objectReferenceValue = arms;
        so.FindProperty("sickleArmsController").objectReferenceValue = sickleC;
        so.FindProperty("trimmerArmsController").objectReferenceValue = trimmerC;
        so.FindProperty("mowerArmsController").objectReferenceValue = mowerC;
        so.FindProperty("groundFollow").objectReferenceValue = follow;
        so.FindProperty("trimmerGroundPoint").objectReferenceValue = tgp;
        so.FindProperty("mowerGroundPoint").objectReferenceValue = mgp;
        so.ApplyModifiedProperties();
        EditorSceneManager.MarkSceneDirty(arms.gameObject.scene);
        sb.AppendLine($"ToolInventory wired: armsAnimator, 3 controllers, FPToolGroundFollow, TrimmerGroundPoint={(tgp != null)}, MowerGroundPoint={(mgp != null)}");
        return tgp != null && mgp != null;
    }

    // ------------------------------------------------------------------ play-mode test
    private static void OnPlayModeChanged(PlayModeStateChange change)
    {
        if (change == PlayModeStateChange.EnteredPlayMode && SessionState.GetInt(StageKey, 0) == 1)
        {
            SessionState.SetInt(StageKey, 2);
            startTime = EditorApplication.timeSinceStartup;
            step = 0;
            swingTime = -1;
            swingShot = false;
            log.Clear();
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
        var inv = Object.FindAnyObjectByType<ToolInventory>();
        Animator arms = FindArms();
        Camera cam = arms != null ? arms.GetComponentInParent<Camera>() : null;
        if (inv == null || arms == null || cam == null)
        {
            Finish("FAILED in play mode: inventory/arms/camera missing");
            return;
        }

        if (step == 0 && t > 1.0)
        {
            var look = Object.FindAnyObjectByType<PlayerLook>();
            if (look != null)
                look.enabled = false;                      // the test drives the camera pitch itself
            savedFov = cam.fieldOfView;
            cam.fieldOfView = 77f;
            inv.UnlockTool(ToolInventory.ToolType.Sickle);
            inv.UnlockTool(ToolInventory.ToolType.Trimmer);
            inv.UnlockTool(ToolInventory.ToolType.Mower);
            Pitch(cam, 0f);
            inv.SelectSickle();
            Report("select sickle", arms, inv);
            step = 1;
        }
        else if (step == 1 && t > 1.8)
        {
            Shot(cam, "Sickle_Idle", arms, inv);
            var swing = inv.GetComponentsInChildren<SickleSwing>(true).FirstOrDefault() ?? Object.FindAnyObjectByType<SickleSwing>();
            bool started = swing != null && swing.TrySwing();
            log.AppendLine($"  SickleSwing.TrySwing() -> {started}");
            swingTime = EditorApplication.timeSinceStartup;
            step = 2;
        }
        else if (step == 2)
        {
            AnimatorStateInfo st = arms.GetCurrentAnimatorStateInfo(0);
            if (!swingShot && st.IsName("SickleSwing") && st.normalizedTime >= 0.5f)
            {
                Shot(cam, "Sickle_Swing", arms, inv);
                swingShot = true;
            }
            if (EditorApplication.timeSinceStartup - swingTime > 0.8)
            {
                Report("after swing", arms, inv);
                if (!swingShot)
                    log.AppendLine("  WARNING: swing state not reached");
                inv.SelectTrimmer();
                Report("select trimmer", arms, inv);
                step = 3;
            }
        }
        else if (step == 3 && t > 3.6)
        {
            Shot(cam, "Trimmer_Idle", arms, inv);
            SetForce<TrimmerController>("ForceWorkingVisual", true);
            step = 4;
        }
        else if (step == 4 && t > 4.4)
        {
            Shot(cam, "Trimmer_Work", arms, inv);
            Ground(inv, "TrimmerGroundPoint", arms, "trimmer, pitch 0");
            Pitch(cam, 40f);
            step = 5;
        }
        else if (step == 5 && t > 5.0)
        {
            Shot(cam, "Trimmer_Work_LookDown40", arms, inv);
            Ground(inv, "TrimmerGroundPoint", arms, "trimmer, looking down 40");
            SetForce<TrimmerController>("ForceWorkingVisual", false);
            Pitch(cam, 40f);
            inv.SelectMower();
            Report("select mower", arms, inv);
            step = 6;
        }
        else if (step == 6 && t > 5.8)
        {
            Shot(cam, "Mower_Idle_LookDown40", arms, inv);
            Ground(inv, "MowerGroundPoint", arms, "mower idle, looking down 40");
            SetForce<MowerController>("ForceMovingVisual", true);
            step = 7;
        }
        else if (step == 7 && t > 6.6)
        {
            Shot(cam, "Mower_Push_LookDown40", arms, inv);
            Ground(inv, "MowerGroundPoint", arms, "mower push, looking down 40");
            Pitch(cam, 0f);
            step = 8;
        }
        else if (step == 8 && t > 7.1)
        {
            Shot(cam, "Mower_Push_LookAhead", arms, inv);
            Ground(inv, "MowerGroundPoint", arms, "mower push, looking ahead");
            Pitch(cam, 70f);
            step = 9;
        }
        else if (step == 9 && t > 7.6)
        {
            Ground(inv, "MowerGroundPoint", arms, "mower push, looking down 70");
            SetForce<MowerController>("ForceMovingVisual", false);
            inv.SelectHands();
            Report("select hands (slot 1)", arms, inv);
            inv.SelectSickle();
            Report("select sickle again (no leftover pose expected)", arms, inv);
            Pitch(cam, 0f);
            cam.fieldOfView = savedFov;
            Finish("done");
        }
        if (t > 20)
            Finish("TIMEOUT");
    }

    private static void Report(string label, Animator arms, ToolInventory inv)
    {
        AnimatorStateInfo st = arms.GetCurrentAnimatorStateInfo(0);
        string state = arms.runtimeAnimatorController == null ? "-" :
            new[] { "SickleIdle", "SickleSwing", "TrimmerIdle", "TrimmerWork", "MowerIdle", "MowerPush", "ShearsIdle", "ShearsCut" }
                .FirstOrDefault(n => st.IsName(n)) ?? "?";
        var follow = arms.GetComponent<FPToolGroundFollow>();
        log.AppendLine($"[{label}] tool={inv.CurrentTool} controller={(arms.runtimeAnimatorController != null ? arms.runtimeAnimatorController.name : "none")} " +
                       $"state={state} t={st.normalizedTime:F2} groundFollow={(follow != null ? follow.CurrentMode.ToString() : "none")}");
    }

    private static void Shot(Camera cam, string name, Animator arms, ToolInventory inv)
    {
        Report(name, arms, inv);
        Capture(cam, $"Logs/FP_Tools_{name}.png");
    }

    private static void Ground(ToolInventory inv, string pointName, Animator arms, string label)
    {
        Transform p = FindNode(arms.transform, pointName);
        var follow = arms.GetComponent<FPToolGroundFollow>();
        if (p == null)
        {
            log.AppendLine($"  ground ({label}): {pointName} not found under the arms");
            return;
        }
        int mask = ~((1 << 2) | (1 << 3));
        if (Physics.Raycast(p.position + Vector3.up * 1.0f, Vector3.down, out RaycastHit hit, 4f, mask, QueryTriggerInteraction.Ignore))
            log.AppendLine($"  ground ({label}): {pointName} is {(p.position.y - hit.point.y) * 100f:F1} cm above '{hit.collider.name}', lift={(follow != null ? follow.CurrentLift * 100f : 0f):F1} cm");
        else
            log.AppendLine($"  ground ({label}): no ground hit below {pointName}");
    }

    private static void SetForce<T>(string property, bool value) where T : Component
    {
        foreach (T c in Object.FindObjectsByType<T>(FindObjectsInactive.Include))
        {
            PropertyInfo pi = typeof(T).GetProperty(property);
            pi?.SetValue(c, value);
        }
    }

    private static void Pitch(Camera cam, float degreesDown)
    {
        cam.transform.localRotation = Quaternion.Euler(degreesDown, 0f, 0f);
    }

    private static void Finish(string summary)
    {
        EditorApplication.update -= Tick;
        var look = Object.FindAnyObjectByType<PlayerLook>(FindObjectsInactive.Include);
        if (look != null)
            look.enabled = true;
        File.WriteAllText(ReportPath, SessionState.GetString(LogKey, "") + log + summary + "\n");
        SessionState.SetInt(StageKey, 3);
        EditorApplication.ExitPlaymode();
    }

    // ------------------------------------------------------------------ helpers
    private static Animator FindArms()
    {
        return Object.FindObjectsByType<Animator>(FindObjectsInactive.Include)
            .FirstOrDefault(a => FindNode(a.transform, "Tool_Mower") != null);
    }

    private static Transform FindNode(Transform root, string name)
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

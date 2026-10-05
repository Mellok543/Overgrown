using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

// Sets up the two-handed garden shears first-person clips (FP_Shears_Idle / FP_Shears_Cut):
// import settings (Generic, avatar copied from Player_Arms_FP, no root motion, loop flags, bones-only mask),
// the FP_Shears animator controller, and writes a validation report to Logs/FP_Shears_SetupReport.txt.
// Runs once automatically after the FBX files change; re-run via Tools/Overgrown/Setup Shears Animations.
public static class ShearsAnimationSetup
{
    private const string ArmsPath = "Assets/Art/Models/Player/Player_Arms_FP.fbx";
    private const string IdlePath = "Assets/Art/Models/Player/Animations/FP_Shears_Idle.fbx";
    private const string CutPath = "Assets/Art/Models/Player/Animations/FP_Shears_Cut.fbx";
    private const string MaskPath = "Assets/Art/Models/Player/Animations/FP_BonesOnly.mask";
    private const string ControllerPath = "Assets/Art/Models/Player/Animations/FP_Shears.controller";
    private const string ReportPath = "Logs/FP_Shears_SetupReport.txt";

    private static readonly string[] LoopingClips =
        { "FP_Idle", "FP_SickleHold", "FP_TrimmerHold", "FP_MowerHold", "FP_Shears_Idle" };

    [InitializeOnLoadMethod]
    private static void AutoRun()
    {
        if (!File.Exists(IdlePath) || !File.Exists(CutPath) || !File.Exists(ArmsPath))
            return;

        System.DateTime newest = new[] { IdlePath, CutPath, ArmsPath }.Max(File.GetLastWriteTimeUtc);
        if (File.Exists(ReportPath) && File.GetLastWriteTimeUtc(ReportPath) > newest)
            return;

        EditorApplication.delayCall += () =>
        {
            if (!EditorApplication.isPlayingOrWillChangePlaymode)
                Run();
        };
    }

    [MenuItem("Tools/Overgrown/Setup Shears Animations")]
    public static void Run()
    {
        var report = new StringBuilder();
        report.AppendLine("FP_Shears setup report  " + System.DateTime.Now);

        AssetDatabase.ImportAsset(ArmsPath, ImportAssetOptions.ForceUpdate);
        GameObject armsModel = AssetDatabase.LoadAssetAtPath<GameObject>(ArmsPath);
        if (armsModel == null)
        {
            Fail(report, "Player_Arms_FP.fbx could not be loaded");
            return;
        }

        AvatarMask mask = BuildBonesOnlyMask(armsModel, report);

        // arms model: clean clip names, loops, mask (the armature root carries constant curves in every take)
        ConfigureImporter(ArmsPath, mask, null, report);
        Avatar armsAvatar = AssetDatabase.LoadAllAssetsAtPath(ArmsPath).OfType<Avatar>().FirstOrDefault();
        report.AppendLine($"Arms avatar: {(armsAvatar != null ? armsAvatar.name : "MISSING")}  valid={armsAvatar != null && armsAvatar.isValid}  human={armsAvatar != null && armsAvatar.isHuman}");

        ConfigureImporter(IdlePath, mask, armsAvatar, report);
        ConfigureImporter(CutPath, mask, armsAvatar, report);

        AnimationClip idle = LoadClip(IdlePath);
        AnimationClip cut = LoadClip(CutPath);
        if (idle == null || cut == null)
        {
            Fail(report, "clips not found after import");
            return;
        }

        BuildController(idle, cut, report);

        report.AppendLine();
        Validate(armsModel, idle, true, report);
        Validate(armsModel, cut, false, report);
        SampleCheck(armsModel, idle, cut, report);

        Directory.CreateDirectory(Path.GetDirectoryName(ReportPath));
        File.WriteAllText(ReportPath, report.ToString());
        AssetDatabase.SaveAssets();
        Debug.Log("[ShearsAnimationSetup] done, report: " + Path.GetFullPath(ReportPath) + "\n" + report);
    }

    private static AvatarMask BuildBonesOnlyMask(GameObject armsModel, StringBuilder report)
    {
        AvatarMask mask = AssetDatabase.LoadAssetAtPath<AvatarMask>(MaskPath);
        if (mask == null)
        {
            mask = new AvatarMask();
            AssetDatabase.CreateAsset(mask, MaskPath);
        }

        mask.transformCount = 0;
        mask.AddTransformPath(armsModel.transform, true);

        int active = 0;
        for (int i = 0; i < mask.transformCount; i++)
        {
            string path = mask.GetTransformPath(i);
            // only the FP_Root bone hierarchy is animated; the model root and the mesh nodes are not
            bool on = path.Contains("FP_Root");
            mask.SetTransformActive(i, on);
            if (on) active++;
        }
        EditorUtility.SetDirty(mask);
        report.AppendLine($"Mask FP_BonesOnly: {active} of {mask.transformCount} transforms active (root + meshes excluded)");
        return mask;
    }

    private static void ConfigureImporter(string path, AvatarMask mask, Avatar sourceAvatar, StringBuilder report)
    {
        var importer = (ModelImporter)AssetImporter.GetAtPath(path);
        importer.importAnimation = true;
        importer.animationType = ModelImporterAnimationType.Generic;
        importer.motionNodeName = "";                       // no root motion node
        if (sourceAvatar == null)
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;   // the arms model owns the Generic avatar
        else
        {
            importer.avatarSetup = ModelImporterAvatarSetup.CopyFromOther;
            importer.sourceAvatar = sourceAvatar;
            importer.materialImportMode = ModelImporterMaterialImportMode.None;   // animation-only files
        }

        var clips = new List<ModelImporterClipAnimation>();
        foreach (ModelImporterClipAnimation clip in importer.defaultClipAnimations)
        {
            string name = clip.takeName.Contains("|") ? clip.takeName.Substring(clip.takeName.LastIndexOf('|') + 1) : clip.takeName;
            clip.name = name;
            clip.loopTime = LoopingClips.Contains(name);
            clip.loopPose = false;
            clip.maskType = ClipAnimationMaskType.CopyFromOther;
            clip.maskSource = mask;
            clips.Add(clip);
        }
        importer.clipAnimations = clips.ToArray();
        importer.SaveAndReimport();
        report.AppendLine($"{Path.GetFileName(path)}: Generic, clips = {string.Join(", ", clips.Select(c => c.name + (c.loopTime ? " (loop)" : "")))}");
    }

    private static AnimationClip LoadClip(string path)
    {
        return AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>()
            .FirstOrDefault(c => !c.name.StartsWith("__preview__"));
    }

    private static void BuildController(AnimationClip idle, AnimationClip cut, StringBuilder report)
    {
        // rebuilt in place (never deleted) so Animator references in scenes stay valid
        AnimatorController controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath)
                                        ?? AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
        foreach (AnimatorControllerParameter p in controller.parameters)
            controller.RemoveParameter(p);
        controller.AddParameter("Cut", AnimatorControllerParameterType.Trigger);
        AnimatorStateMachine sm = controller.layers[0].stateMachine;
        foreach (ChildAnimatorState st in sm.states)
            sm.RemoveState(st.state);

        AnimatorState idleState = sm.AddState("ShearsIdle", new Vector3(260, 80, 0));
        idleState.motion = idle;
        AnimatorState cutState = sm.AddState("ShearsCut", new Vector3(260, 200, 0));
        cutState.motion = cut;
        sm.defaultState = idleState;

        AnimatorStateTransition toCut = idleState.AddTransition(cutState);
        toCut.AddCondition(AnimatorConditionMode.If, 0f, "Cut");
        toCut.hasExitTime = false;
        toCut.hasFixedDuration = true;
        toCut.duration = 0f;                                 // FP_Shears_Cut starts on the idle pose

        AnimatorStateTransition toIdle = cutState.AddTransition(idleState);
        toIdle.hasExitTime = true;
        toIdle.exitTime = 0.95f;
        toIdle.hasFixedDuration = true;
        toIdle.duration = 0.025f;                            // the last 5% of the cut is already the idle pose

        EditorUtility.SetDirty(controller);
        report.AppendLine($"Controller {ControllerPath}: ShearsIdle (default) -[Cut]-> ShearsCut -[exit 0.95, 0.025 s]-> ShearsIdle");
    }

    private static void Validate(GameObject armsModel, AnimationClip clip, bool shouldLoop, StringBuilder report)
    {
        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(clip);
        EditorCurveBinding[] bindings = AnimationUtility.GetCurveBindings(clip);
        var paths = new HashSet<string>(bindings.Select(b => b.path));
        int missing = paths.Count(p => p.Length > 0 && armsModel.transform.Find(p) == null);
        bool rootCurves = paths.Any(p => !p.Contains("FP_Root"));      // model root / armature node / meshes

        report.AppendLine($"[{clip.name}] length={clip.length:F3}s frames={Mathf.RoundToInt(clip.length * clip.frameRate) + 1} fps={clip.frameRate} " +
                          $"loopTime={settings.loopTime} (expected {shouldLoop}) human={clip.humanMotion} legacy={clip.legacy}");
        report.AppendLine($"    animated transforms={paths.Count} curves={bindings.Length} unbound paths={missing} non-bone curves={rootCurves} " +
                          $"hasRootCurves={clip.hasRootCurves} hasMotionCurves={clip.hasMotionCurves}");
        report.AppendLine($"    shears bones animated: {paths.Any(p => p.EndsWith("Shears_A"))}/{paths.Any(p => p.EndsWith("Shears_B"))}");
        bool ok = settings.loopTime == shouldLoop && missing == 0 && !rootCurves && !clip.humanMotion;
        report.AppendLine("    => " + (ok ? "OK" : "PROBLEM"));
    }

    private static void SampleCheck(GameObject armsModel, AnimationClip idle, AnimationClip cut, StringBuilder report)
    {
        GameObject go = Object.Instantiate(armsModel);
        go.hideFlags = HideFlags.HideAndDontSave;
        try
        {
            Transform handR = Find(go.transform, "Hand_R", true);
            Transform handL = Find(go.transform, "Hand_L", true);
            Transform shA = Find(go.transform, "Shears_A", true);
            Transform shB = Find(go.transform, "Shears_B", true);
            Transform shRoot = Find(go.transform, "Shears_Root", true);
            report.AppendLine();
            report.AppendLine($"Sample check (Unity space, relative to Player_Arms_FP root); shears renderer present: {go.GetComponentsInChildren<SkinnedMeshRenderer>(true).Any(r => r.name == "Garden_Shears_FP")}");
            if (handR == null || handL == null || shA == null || shB == null || shRoot == null)
            {
                report.AppendLine("    bones missing: Hand_R/Hand_L/Shears_A/Shears_B/Shears_Root");
                return;
            }

            // hand -> its handle half must stay rigid: the hand's position expressed in the half's local space
            // should not drift during the cut (that is what "no slipping" means numerically)
            Vector3? refA = null, refB = null;
            float driftA = 0f, driftB = 0f;
            foreach (float t in new[] { 0f, 0.1f, 0.2f, 0.25f, 0.3f, 0.35f, 0.4f, 0.5f })
            {
                cut.SampleAnimation(go, Mathf.Min(t, cut.length));
                Vector3 la = shA.InverseTransformPoint(handR.position);
                Vector3 lb = shB.InverseTransformPoint(handL.position);
                refA ??= la; refB ??= lb;
                driftA = Mathf.Max(driftA, Vector3.Distance(la, refA.Value));
                driftB = Mathf.Max(driftB, Vector3.Distance(lb, refB.Value));
                float hands = Vector3.Distance(handR.position, handL.position);
                float open = Vector3.Angle(shA.forward, shB.forward);
                report.AppendLine($"    cut t={t:F2}s  hands apart={hands * 100f:F1} cm  blade opening={open:F1} deg  root pos={go.transform.position}");
            }
            report.AppendLine($"    max hand drift relative to its handle: right {driftA * 1000f:F1} mm, left {driftB * 1000f:F1} mm");

            idle.SampleAnimation(go, 0f);
            Vector3 i0 = handR.position;
            cut.SampleAnimation(go, 0f);
            Vector3 c0 = handR.position;
            cut.SampleAnimation(go, cut.length);
            Vector3 c1 = handR.position;
            report.AppendLine($"    idle(0) vs cut(start) {Vector3.Distance(i0, c0) * 1000f:F2} mm, idle(0) vs cut(end) {Vector3.Distance(i0, c1) * 1000f:F2} mm (seamless if ~0)");
        }
        finally
        {
            Object.DestroyImmediate(go);
        }
    }

    private static Transform Find(Transform root, string name, bool bonesOnly)
    {
        foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
        {
            if (t.name != name)
                continue;
            if (bonesOnly && t.GetComponent<Renderer>() != null)
                continue;                                    // mesh "Hand_R" vs bone "Hand_R"
            return t;
        }
        return null;
    }

    private static void Fail(StringBuilder report, string msg)
    {
        report.AppendLine("FAILED: " + msg);
        Directory.CreateDirectory(Path.GetDirectoryName(ReportPath));
        File.WriteAllText(ReportPath, report.ToString());
        Debug.LogError("[ShearsAnimationSetup] " + msg);
    }
}

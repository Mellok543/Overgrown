using System.Collections.Generic;
using UnityEngine;

public class TrimmerController : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private GrassInventory inventory;
    [SerializeField] private Transform trimmerHead;

    [Header("Cutting")]
    [SerializeField] private LayerMask grassLayer;
    [SerializeField] private float cutDistance = 2.2f;
    [SerializeField] private float cutRadius = 1.15f;
    [SerializeField] private float cutsPerSecond = 5f;
    [SerializeField] private int bundlesPerTick = 2;

    [Header("Tool Identity")]
    [Tooltip("Trimmer stays precise: smaller working circle than the old prototype.")]
    [SerializeField, Range(0.4f, 1f)] private float effectiveRadiusMultiplier = 0.7f;
    [Tooltip("Maximum separate grass clumps cut by one trimmer tick.")]
    [SerializeField, Range(1, 4)] private int maxClumpsPerTick = 1;

    [Header("Visual")]
    [SerializeField] private float headSpinSpeed = 1200f;
    [Tooltip("Arms Animator (FP_Trimmer.controller); found from the trimmer head if left empty.")]
    [SerializeField] private Animator armsAnimator;
    [SerializeField] private string workingParameter = "Working";

    /// <summary>Plays the work animation + head spin without the mouse button (tests / scripted use). Does not cut.</summary>
    public bool ForceWorkingVisual { get; set; }

    private float nextCutTime;

    public float CutRadius => cutRadius;
    public float CutsPerSecond => cutsPerSecond;
    public int BundlesPerTick => bundlesPerTick;

    private void Awake()
    {
        if (playerCamera == null)
        {
            playerCamera = GetComponentInParent<Camera>();
        }

        if (playerCamera == null)
        {
            playerCamera = Camera.main;
        }

        if (inventory == null)
        {
            inventory = FindFirstObjectByType<GrassInventory>();
        }

        if (armsAnimator == null && trimmerHead != null)
        {
            armsAnimator = trimmerHead.GetComponentInParent<Animator>();
        }
    }

    private void OnDisable()
    {
        SetWorkingVisual(false);
    }

    private void SetWorkingVisual(bool working)
    {
        if (armsAnimator == null || armsAnimator.runtimeAnimatorController == null)
            return;

        foreach (AnimatorControllerParameter p in armsAnimator.parameters)
        {
            if (p.name == workingParameter && p.type == AnimatorControllerParameterType.Bool)
            {
                armsAnimator.SetBool(workingParameter, working);
                return;
            }
        }
    }

    private void Update()
    {
        SetWorkingVisual(Input.GetMouseButton(0) || ForceWorkingVisual);

        if (ForceWorkingVisual && trimmerHead != null && !Input.GetMouseButton(0))
        {
            trimmerHead.Rotate(Vector3.up, headSpinSpeed * Time.deltaTime, Space.Self);
        }

        if (!Input.GetMouseButton(0))
            return;

        if (inventory == null || inventory.IsFull)
            return;

        if (trimmerHead != null)
        {
            trimmerHead.Rotate(
                Vector3.up,
                headSpinSpeed * Time.deltaTime,
                Space.Self
            );
        }

        if (Time.time < nextCutTime)
            return;

        nextCutTime = Time.time + 1f / Mathf.Max(0.1f, cutsPerSecond);
        CutGrass();
    }

    private void CutGrass()
    {
        if (playerCamera == null || inventory == null)
            return;

        Vector3 cutPosition =
            playerCamera.transform.position +
            playerCamera.transform.forward * cutDistance;

        float effectiveRadius = cutRadius * effectiveRadiusMultiplier;

        Collider[] hits = Physics.OverlapSphere(
            cutPosition,
            effectiveRadius,
            grassLayer,
            QueryTriggerInteraction.Collide
        );

        List<GrassCuttable> grassObjects = new List<GrassCuttable>();
        HashSet<GrassCuttable> unique = new HashSet<GrassCuttable>();

        foreach (Collider hit in hits)
        {
            GrassCuttable grass = hit.GetComponentInParent<GrassCuttable>();

            if (grass == null || grass.IsCut || unique.Contains(grass))
                continue;

            unique.Add(grass);
            grassObjects.Add(grass);
        }

        grassObjects.Sort((a, b) =>
        {
            float distanceA = (a.transform.position - cutPosition).sqrMagnitude;
            float distanceB = (b.transform.position - cutPosition).sqrMagnitude;
            return distanceA.CompareTo(distanceB);
        });

        int freeSpace = inventory.Capacity - inventory.Bundles;
        int maxCollect = Mathf.Min(
            Mathf.Min(bundlesPerTick, maxClumpsPerTick),
            freeSpace
        );
        int collected = 0;

        foreach (GrassCuttable grass in grassObjects)
        {
            if (collected >= maxCollect)
                break;

            if (inventory.TryAddBundles(1) == 0)
                break;

            if (grass.Cut())
            {
                collected++;
            }
            else
            {
                inventory.RemoveBundles(1);
            }
        }
    }
}

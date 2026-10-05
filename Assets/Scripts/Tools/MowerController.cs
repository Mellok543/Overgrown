using System.Collections.Generic;
using UnityEngine;

public class MowerController : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private GrassInventory inventory;

    [Header("Visual")]
    [SerializeField] private Transform wheelFL;
    [SerializeField] private Transform wheelFR;
    [SerializeField] private Transform wheelBL;
    [SerializeField] private Transform wheelBR;
    [SerializeField] private float wheelSpinSpeed = 720f;

    [Header("Cutting")]
    [SerializeField] private LayerMask grassLayer;
    [SerializeField] private float cutDistance = 2.0f;
    [SerializeField] private float cutWidth = 1.6f;
    [SerializeField] private float cutDepth = 1.0f;
    [SerializeField] private float cutsPerSecond = 6f;
    [SerializeField] private int bundlesPerTick = 4;

    [Header("Control")]
    [SerializeField] private bool requireForwardMovement = true;
    [SerializeField] private KeyCode useKey = KeyCode.Mouse0;

    [Header("First Person Animation")]
    [Tooltip("Arms Animator (FP_Mower.controller); found from a wheel if left empty.")]
    [SerializeField] private Animator armsAnimator;
    [SerializeField] private string movingParameter = "Moving";

    /// <summary>Plays the push animation + wheel spin without input (tests / scripted use). Does not cut.</summary>
    public bool ForceMovingVisual { get; set; }

    private float nextCutTime;

    public float CutWidth => cutWidth;
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

        if (armsAnimator == null && wheelFL != null)
        {
            armsAnimator = wheelFL.GetComponentInParent<Animator>();
        }
    }

    private void OnDisable()
    {
        SetMovingVisual(false);
    }

    private void SetMovingVisual(bool moving)
    {
        if (armsAnimator == null || armsAnimator.runtimeAnimatorController == null)
            return;

        foreach (AnimatorControllerParameter p in armsAnimator.parameters)
        {
            if (p.name == movingParameter && p.type == AnimatorControllerParameterType.Bool)
            {
                armsAnimator.SetBool(movingParameter, moving);
                return;
            }
        }
    }

    private void Update()
    {
        bool pushing = Input.GetKey(useKey) && (!requireForwardMovement || Input.GetAxisRaw("Vertical") > 0.1f);
        SetMovingVisual(pushing || ForceMovingVisual);

        if (ForceMovingVisual && !pushing)
        {
            SpinWheels();
        }

        bool isUsing = Input.GetKey(useKey);

        if (!isUsing)
            return;

        if (requireForwardMovement)
        {
            float vertical = Input.GetAxisRaw("Vertical");

            if (vertical <= 0.1f)
                return;
        }

        if (inventory == null || inventory.IsFull)
            return;

        SpinWheels();

        if (Time.time < nextCutTime)
            return;

        nextCutTime = Time.time + 1f / Mathf.Max(0.1f, cutsPerSecond);
        CutGrassStrip();
    }

    private void SpinWheels()
    {
        RotateWheel(wheelFL);
        RotateWheel(wheelFR);
        RotateWheel(wheelBL);
        RotateWheel(wheelBR);
    }

    private void RotateWheel(Transform wheel)
    {
        if (wheel == null)
            return;

        wheel.Rotate(Vector3.right, wheelSpinSpeed * Time.deltaTime, Space.Self);
    }

    private void CutGrassStrip()
    {
        if (playerCamera == null || inventory == null)
            return;

        Vector3 center =
            playerCamera.transform.position +
            playerCamera.transform.forward * cutDistance;

        Quaternion orientation = Quaternion.LookRotation(
            playerCamera.transform.forward,
            Vector3.up
        );

        Vector3 halfExtents = new Vector3(
            cutWidth * 0.5f,
            0.75f,
            cutDepth * 0.5f
        );

        Collider[] hits = Physics.OverlapBox(
            center,
            halfExtents,
            orientation,
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
            float distanceA = (a.transform.position - center).sqrMagnitude;
            float distanceB = (b.transform.position - center).sqrMagnitude;
            return distanceA.CompareTo(distanceB);
        });

        int freeSpace = inventory.Capacity - inventory.Bundles;
        int maxCollect = Mathf.Min(bundlesPerTick, freeSpace);
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

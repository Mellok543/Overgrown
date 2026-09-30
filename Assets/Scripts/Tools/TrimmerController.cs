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

    [Header("Visual")]
    [SerializeField] private float headSpinSpeed = 1200f;

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
    }

    private void Update()
    {
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

        Collider[] hits = Physics.OverlapSphere(
            cutPosition,
            cutRadius,
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

using System.Collections.Generic;
using UnityEngine;

public class GrassCutter : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private GrassInventory inventory;

    [Header("Cutting")]
    [SerializeField] private float cutDistance = 2f;
    [SerializeField] private float cutRadius = 0.8f;
    [SerializeField] private int bundlesPerSwing = 3;
    [SerializeField] private LayerMask grassLayer;

    public float CutDistance => cutDistance;
    public float CutRadius => cutRadius;
    public int BundlesPerSwing => bundlesPerSwing;

    private void Awake()
    {
        if (playerCamera == null)
        {
            playerCamera = GetComponentInChildren<Camera>();
        }

        if (inventory == null)
        {
            inventory = GetComponent<GrassInventory>();
        }
    }

    public int CutGrass()
    {
        if (playerCamera == null || inventory == null || inventory.IsFull)
            return 0;

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

        int collected = 0;
        int freeSpace = inventory.Capacity - inventory.Bundles;
        int maxCollect = Mathf.Min(bundlesPerSwing, freeSpace);

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

        return collected;
    }

    public void AddCutRadius(float amount)
    {
        cutRadius = Mathf.Max(0.1f, cutRadius + amount);
    }

    public void AddCutDistance(float amount)
    {
        cutDistance = Mathf.Max(0.1f, cutDistance + amount);
    }

    public void AddBundlesPerSwing(int amount)
    {
        bundlesPerSwing = Mathf.Max(1, bundlesPerSwing + amount);
    }
}

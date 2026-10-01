using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(BoxCollider))]
public class GroundDetailScatter : MonoBehaviour
{
    [Header("Prefabs")]
    [SerializeField] private List<GameObject> detailPrefabs = new();

    [Header("Area")]
    [SerializeField] private int detailCount = 80;
    [SerializeField] private int maxPlacementAttempts = 5000;
    [SerializeField] private BoxCollider areaBounds;

    [Header("Ground")]
    [SerializeField] private LayerMask groundLayer = ~0;
    [SerializeField] private float rayHeight = 10f;
    [SerializeField, Range(0f, 60f)] private float maxGroundSlope = 35f;

    [Header("Avoid Obstacles")]
    [SerializeField] private float obstacleClearance = 0.35f;
    [SerializeField] private bool blockAnyNonGroundCollider = true;
    [SerializeField] private Collider[] exclusionColliders;

    [Header("Scatter Rules")]
    [SerializeField] private float minSpacing = 0.35f;
    [SerializeField] private bool randomYRotation = true;
    [SerializeField] private float randomScaleMin = 0.9f;
    [SerializeField] private float randomScaleMax = 1.15f;

    public List<GameObject> DetailPrefabs => detailPrefabs;
    public int DetailCount => detailCount;
    public int MaxPlacementAttempts => maxPlacementAttempts;
    public BoxCollider AreaBounds => areaBounds;
    public LayerMask GroundLayer => groundLayer;
    public float RayHeight => rayHeight;
    public float MaxGroundSlope => maxGroundSlope;
    public float ObstacleClearance => obstacleClearance;
    public bool BlockAnyNonGroundCollider => blockAnyNonGroundCollider;
    public Collider[] ExclusionColliders => exclusionColliders;
    public float MinSpacing => minSpacing;
    public bool RandomYRotation => randomYRotation;
    public float RandomScaleMin => randomScaleMin;
    public float RandomScaleMax => randomScaleMax;

    private void Reset()
    {
        areaBounds = GetComponent<BoxCollider>();

        if (areaBounds != null)
        {
            areaBounds.isTrigger = true;
            areaBounds.center = Vector3.zero;
            areaBounds.size = new Vector3(20f, 1f, 20f);
        }
    }

    private void Awake()
    {
        if (areaBounds == null)
        {
            areaBounds = GetComponent<BoxCollider>();
        }
    }

    public bool IsInsideExclusionVolume(Vector3 worldPoint)
    {
        if (exclusionColliders == null)
            return false;

        foreach (Collider exclusion in exclusionColliders)
        {
            if (exclusion == null || !exclusion.enabled)
                continue;

            Vector3 closest = exclusion.ClosestPoint(worldPoint);

            if ((closest - worldPoint).sqrMagnitude <= 0.0001f)
                return true;
        }

        return false;
    }

    private void OnDrawGizmosSelected()
    {
        if (areaBounds == null)
        {
            areaBounds = GetComponent<BoxCollider>();
        }

        if (areaBounds == null)
            return;

        Matrix4x4 oldMatrix = Gizmos.matrix;
        Gizmos.matrix = areaBounds.transform.localToWorldMatrix;

        Gizmos.DrawWireCube(areaBounds.center, areaBounds.size);

        Gizmos.matrix = oldMatrix;
    }
}

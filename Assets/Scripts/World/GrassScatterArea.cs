using UnityEngine;

[RequireComponent(typeof(BoxCollider))]
public class GrassScatterArea : MonoBehaviour
{
    [Header("Prefab")]
    [SerializeField] private GameObject grassPrefab;

    [Header("Area")]
    [SerializeField] private int grassCount = 200;
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

    [Header("Placement")]
    [SerializeField] private float randomScaleMin = 0.85f;
    [SerializeField] private float randomScaleMax = 1.15f;
    [SerializeField] private bool randomYRotation = true;

    public GameObject GrassPrefab => grassPrefab;
    public int GrassCount => grassCount;
    public int MaxPlacementAttempts => maxPlacementAttempts;
    public BoxCollider AreaBounds => areaBounds;
    public LayerMask GroundLayer => groundLayer;
    public float RayHeight => rayHeight;
    public float MaxGroundSlope => maxGroundSlope;
    public float ObstacleClearance => obstacleClearance;
    public bool BlockAnyNonGroundCollider => blockAnyNonGroundCollider;
    public Collider[] ExclusionColliders => exclusionColliders;
    public float RandomScaleMin => randomScaleMin;
    public float RandomScaleMax => randomScaleMax;
    public bool RandomYRotation => randomYRotation;

    private void Reset()
    {
        areaBounds = GetComponent<BoxCollider>();

        if (areaBounds != null)
        {
            areaBounds.isTrigger = true;
            areaBounds.center = Vector3.zero;
            areaBounds.size = new Vector3(10f, 1f, 10f);
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

        Gizmos.DrawWireCube(
            areaBounds.center,
            areaBounds.size
        );

        Gizmos.matrix = oldMatrix;
    }
}

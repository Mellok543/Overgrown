using UnityEngine;

public class GrassScatterArea : MonoBehaviour
{
    [Header("Prefab")]
    [SerializeField] private GameObject grassPrefab;

    [Header("Area")]
    [SerializeField] private Vector2 areaSize = new Vector2(10f, 10f);
    [SerializeField] private int grassCount = 200;
    [SerializeField] private int maxPlacementAttempts = 5000;

    [Header("Ground")]
    [SerializeField] private LayerMask groundLayer = ~0;
    [SerializeField] private float rayHeight = 10f;
    [SerializeField, Range(0f, 60f)] private float maxGroundSlope = 35f;

    [Header("Avoid Obstacles")]
    [SerializeField] private LayerMask obstacleLayer;
    [SerializeField] private float obstacleClearance = 0.35f;
    [SerializeField] private Collider[] exclusionColliders;

    [Header("Placement")]
    [SerializeField] private float randomScaleMin = 0.85f;
    [SerializeField] private float randomScaleMax = 1.15f;
    [SerializeField] private bool randomYRotation = true;

    public GameObject GrassPrefab => grassPrefab;
    public Vector2 AreaSize => areaSize;
    public int GrassCount => grassCount;
    public int MaxPlacementAttempts => maxPlacementAttempts;
    public LayerMask GroundLayer => groundLayer;
    public float RayHeight => rayHeight;
    public float MaxGroundSlope => maxGroundSlope;
    public LayerMask ObstacleLayer => obstacleLayer;
    public float ObstacleClearance => obstacleClearance;
    public Collider[] ExclusionColliders => exclusionColliders;
    public float RandomScaleMin => randomScaleMin;
    public float RandomScaleMax => randomScaleMax;
    public bool RandomYRotation => randomYRotation;

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
        Gizmos.matrix = transform.localToWorldMatrix;
        Gizmos.DrawWireCube(
            Vector3.zero,
            new Vector3(areaSize.x, 0.05f, areaSize.y)
        );
    }
}

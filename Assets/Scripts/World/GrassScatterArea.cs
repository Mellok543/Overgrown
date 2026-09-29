using UnityEngine;

public class GrassScatterArea : MonoBehaviour
{
    [Header("Prefab")]
    [SerializeField] private GameObject grassPrefab;

    [Header("Area")]
    [SerializeField] private Vector2 areaSize = new Vector2(10f, 10f);
    [SerializeField] private int grassCount = 200;

    [Header("Placement")]
    [SerializeField] private LayerMask groundLayer = ~0;
    [SerializeField] private float rayHeight = 10f;
    [SerializeField] private float randomScaleMin = 0.85f;
    [SerializeField] private float randomScaleMax = 1.15f;
    [SerializeField] private bool randomYRotation = true;

    public GameObject GrassPrefab => grassPrefab;
    public Vector2 AreaSize => areaSize;
    public int GrassCount => grassCount;
    public LayerMask GroundLayer => groundLayer;
    public float RayHeight => rayHeight;
    public float RandomScaleMin => randomScaleMin;
    public float RandomScaleMax => randomScaleMax;
    public bool RandomYRotation => randomYRotation;

    private void OnDrawGizmosSelected()
    {
        Gizmos.matrix = transform.localToWorldMatrix;
        Gizmos.DrawWireCube(
            Vector3.zero,
            new Vector3(areaSize.x, 0.05f, areaSize.y)
        );
    }
}

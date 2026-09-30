using UnityEngine;

public class GrassCutter : MonoBehaviour
{
    [SerializeField] private Camera playerCamera;

    [Header("Cutting")]
    [SerializeField] private float cutDistance = 2f;
    [SerializeField] private float cutRadius = 0.8f;
    [SerializeField] private LayerMask grassLayer;

    public float CutDistance => cutDistance;
    public float CutRadius => cutRadius;

    public void CutGrass()
    {
        if (playerCamera == null)
            return;

        Vector3 cutPosition =
            playerCamera.transform.position +
            playerCamera.transform.forward * cutDistance;

        Collider[] grassObjects = Physics.OverlapSphere(
            cutPosition,
            cutRadius,
            grassLayer,
            QueryTriggerInteraction.Collide
        );

        foreach (Collider grassCollider in grassObjects)
        {
            GrassCuttable grass =
                grassCollider.GetComponentInParent<GrassCuttable>();

            if (grass != null)
            {
                grass.Cut();
            }
        }
    }

    public void AddCutRadius(float amount)
    {
        cutRadius = Mathf.Max(0.1f, cutRadius + amount);
    }

    public void AddCutDistance(float amount)
    {
        cutDistance = Mathf.Max(0.1f, cutDistance + amount);
    }
}

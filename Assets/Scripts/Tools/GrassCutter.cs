using UnityEngine;

public class GrassCutter : MonoBehaviour
{
    [SerializeField] private Camera playerCamera;

    [SerializeField] private float cutDistance = 2f;
    [SerializeField] private float cutRadius = 0.8f;

    [SerializeField] private LayerMask grassLayer;

    public void CutGrass()
    {
        Vector3 cutPosition =
            playerCamera.transform.position +
            playerCamera.transform.forward * cutDistance;

        Collider[] grassObjects = Physics.OverlapSphere(
            cutPosition,
            cutRadius,
            grassLayer
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
}
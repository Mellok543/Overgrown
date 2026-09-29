using UnityEngine;

public class GrassCuttable : MonoBehaviour
{
    [SerializeField] private GameObject fullGrass;
    [SerializeField] private GameObject cutGrass;

    private bool isCut;

    public void Cut()
    {
        if (isCut)
            return;

        isCut = true;

        fullGrass.SetActive(false);
        cutGrass.SetActive(true);
    }
}
using UnityEngine;

public class PlayerItemInventory : MonoBehaviour
{
    [Header("Quest Items")]
    [SerializeField] private bool hasGardenShears;

    [Header("First Person")]
    [SerializeField] private GameObject gardenShearsObject;
    [SerializeField] private Animator armsAnimator;
    [SerializeField] private string shearsCutTrigger = "Cut";

    public bool HasGardenShears => hasGardenShears;

    private void Awake()
    {
        if (armsAnimator == null)
        {
            armsAnimator = GetComponentInChildren<Animator>(true);
        }

        RefreshFirstPersonItems();
    }

    public void GiveGardenShears()
    {
        hasGardenShears = true;
        RefreshFirstPersonItems();
    }

    public bool PlayGardenShearsCut()
    {
        if (!hasGardenShears)
            return false;

        ShowGardenShears();

        if (armsAnimator == null)
            return false;

        armsAnimator.ResetTrigger(shearsCutTrigger);
        armsAnimator.SetTrigger(shearsCutTrigger);
        return true;
    }

    public void HideGardenShears()
    {
        if (gardenShearsObject != null)
        {
            gardenShearsObject.SetActive(false);
        }
    }

    public void ShowGardenShears()
    {
        if (gardenShearsObject != null && hasGardenShears)
        {
            gardenShearsObject.SetActive(true);
        }
    }

    private void RefreshFirstPersonItems()
    {
        if (gardenShearsObject != null)
        {
            gardenShearsObject.SetActive(hasGardenShears);
        }
    }
}

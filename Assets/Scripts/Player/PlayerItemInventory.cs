using UnityEngine;

public class PlayerItemInventory : MonoBehaviour
{
    [Header("Quest Items")]
    [SerializeField] private bool hasGardenShears;

    [Header("First Person")]
    [SerializeField] private GameObject gardenShearsObject;

    public bool HasGardenShears => hasGardenShears;

    private void Awake()
    {
        RefreshFirstPersonItems();
    }

    public void GiveGardenShears()
    {
        hasGardenShears = true;
        RefreshFirstPersonItems();
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

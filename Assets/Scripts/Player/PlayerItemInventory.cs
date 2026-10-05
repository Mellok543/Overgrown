using UnityEngine;

public class PlayerItemInventory : MonoBehaviour
{
    [Header("Quest Items")]
    [SerializeField] private bool hasGardenShears;

    [Header("First Person")]
    [SerializeField] private GameObject gardenShearsObject;
    [SerializeField] private Animator armsAnimator;
    [SerializeField] private RuntimeAnimatorController normalArmsController;
    [SerializeField] private RuntimeAnimatorController shearsArmsController;
    [SerializeField] private string shearsCutTrigger = "Cut";

    private bool gardenShearsEquipped;
    private ToolInventory toolInventory;

    public bool HasGardenShears => hasGardenShears;
    public bool IsGardenShearsEquipped => hasGardenShears && gardenShearsEquipped;

    private void Awake()
    {
        toolInventory = GetComponent<ToolInventory>();

        if (armsAnimator == null)
            armsAnimator = GetComponentInChildren<Animator>(true);

        // Claude assigned the shears controller directly to the Animator.
        // Preserve it as the shears-only controller, then return hands to normal.
        if (shearsArmsController == null && armsAnimator != null)
            shearsArmsController = armsAnimator.runtimeAnimatorController;

        gardenShearsEquipped = false;
        RefreshFirstPersonItems();
    }

    public void GiveGardenShears()
    {
        hasGardenShears = true;
        gardenShearsEquipped = false;
        RefreshFirstPersonItems();
    }

    public void SetGardenShearsEquipped(bool equipped)
    {
        gardenShearsEquipped = hasGardenShears && equipped;
        RefreshFirstPersonItems();
    }

    public bool PlayGardenShearsCut()
    {
        if (!IsGardenShearsEquipped)
            return false;

        if (armsAnimator == null)
            return false;

        armsAnimator.ResetTrigger(shearsCutTrigger);
        armsAnimator.SetTrigger(shearsCutTrigger);
        return true;
    }

    public void ConsumeGardenShears()
    {
        hasGardenShears = false;
        gardenShearsEquipped = false;
        RefreshFirstPersonItems();

        if (toolInventory == null)
            toolInventory = GetComponent<ToolInventory>();

        if (toolInventory != null)
            toolInventory.SelectHands();
    }

    private void RefreshFirstPersonItems()
    {
        bool showShears = HasGardenShears && gardenShearsEquipped;

        if (gardenShearsObject != null)
            gardenShearsObject.SetActive(showShears);

        if (armsAnimator != null)
        {
            RuntimeAnimatorController desiredController =
                showShears ? shearsArmsController : normalArmsController;

            if (armsAnimator.runtimeAnimatorController != desiredController)
                armsAnimator.runtimeAnimatorController = desiredController;
        }
    }
}

using System.Collections;
using UnityEngine;

public class PlayerItemInventory : MonoBehaviour
{
    [Header("Quest Items")]
    [SerializeField] private bool hasGardenShears;

    [Header("First Person")]
    [SerializeField] private GameObject gardenShearsObject;
    [SerializeField] private Animator armsAnimator;
    [SerializeField] private RuntimeAnimatorController shearsArmsController;
    [SerializeField] private string shearsIdleState = "ShearsIdle";
    [SerializeField] private string shearsCutTrigger = "Cut";

    [Header("Shears Disappear")]
    [SerializeField] private float disappearDuration = 0.3f;
    [SerializeField] private float disappearDrop = 0.12f;

    private bool gardenShearsEquipped;
    private bool isConsumingShears;
    private ToolInventory toolInventory;

    private Vector3 shearsOriginalScale = Vector3.one;
    private Vector3 shearsOriginalLocalPosition;

    public bool HasGardenShears => hasGardenShears;
    public bool IsGardenShearsEquipped =>
        hasGardenShears && gardenShearsEquipped && !isConsumingShears;

    private void Awake()
    {
        toolInventory = GetComponent<ToolInventory>();

        if (armsAnimator == null)
            armsAnimator = GetComponentInChildren<Animator>(true);

        // Claude already assigned FP_Shears.controller to the arms Animator.
        // Cache it once so slot 5 can restore it later.
        if (shearsArmsController == null && armsAnimator != null)
            shearsArmsController = armsAnimator.runtimeAnimatorController;

        if (gardenShearsObject != null)
        {
            shearsOriginalScale = gardenShearsObject.transform.localScale;
            shearsOriginalLocalPosition = gardenShearsObject.transform.localPosition;
        }

        gardenShearsEquipped = false;
        SetShearsVisible(false);
        ResetArmsToBindPose();
    }

    public void GiveGardenShears()
    {
        hasGardenShears = true;
        gardenShearsEquipped = false;
        isConsumingShears = false;

        ResetShearsTransform();
        SetShearsVisible(false);
    }

    public void SetGardenShearsEquipped(bool equipped)
    {
        if (isConsumingShears)
            return;

        gardenShearsEquipped = hasGardenShears && equipped;

        if (gardenShearsEquipped)
        {
            EquipShearsVisuals();
        }
        else
        {
            UnequipShearsVisuals();
        }
    }

    private void EquipShearsVisuals()
    {
        ResetShearsTransform();
        SetShearsVisible(true);

        if (armsAnimator == null)
            return;

        if (shearsArmsController != null &&
            armsAnimator.runtimeAnimatorController != shearsArmsController)
        {
            armsAnimator.runtimeAnimatorController = shearsArmsController;
        }

        armsAnimator.enabled = true;
        armsAnimator.Rebind();
        armsAnimator.Update(0f);

        if (HasState(armsAnimator, shearsIdleState))
        {
            armsAnimator.Play(shearsIdleState, 0, 0f);
            armsAnimator.Update(0f);
        }
    }

    private void UnequipShearsVisuals()
    {
        SetShearsVisible(false);
        ResetArmsToBindPose();
    }

    public bool PlayGardenShearsCut()
    {
        if (!IsGardenShearsEquipped)
            return false;

        if (armsAnimator == null)
            return false;

        if (shearsArmsController != null &&
            armsAnimator.runtimeAnimatorController != shearsArmsController)
        {
            armsAnimator.runtimeAnimatorController = shearsArmsController;
            armsAnimator.Rebind();
            armsAnimator.Update(0f);
        }

        armsAnimator.ResetTrigger(shearsCutTrigger);
        armsAnimator.SetTrigger(shearsCutTrigger);
        return true;
    }

    public void ConsumeGardenShears()
    {
        if (!hasGardenShears || isConsumingShears)
            return;

        StartCoroutine(ConsumeGardenShearsRoutine());
    }

    private IEnumerator ConsumeGardenShearsRoutine()
    {
        isConsumingShears = true;

        Transform shearsTransform =
            gardenShearsObject != null ? gardenShearsObject.transform : null;

        if (shearsTransform != null && gardenShearsObject.activeSelf)
        {
            Vector3 startScale = shearsTransform.localScale;
            Vector3 startPosition = shearsTransform.localPosition;
            Vector3 endScale = Vector3.zero;
            Vector3 endPosition = startPosition + Vector3.down * disappearDrop;

            float elapsed = 0f;
            float duration = Mathf.Max(0.01f, disappearDuration);

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = Mathf.Clamp01(elapsed / duration);
                float eased = t * t * (3f - 2f * t);

                shearsTransform.localScale =
                    Vector3.Lerp(startScale, endScale, eased);

                shearsTransform.localPosition =
                    Vector3.Lerp(startPosition, endPosition, eased);

                yield return null;
            }
        }

        hasGardenShears = false;
        gardenShearsEquipped = false;
        isConsumingShears = false;

        SetShearsVisible(false);
        ResetShearsTransform();
        ResetArmsToBindPose();

        if (toolInventory == null)
            toolInventory = GetComponent<ToolInventory>();

        if (toolInventory != null)
            toolInventory.SelectHands();
    }

    private void ResetArmsToBindPose()
    {
        if (armsAnimator == null)
            return;

        // No shears controller while another slot is selected.
        // Rebind returns the first-person hands to their normal rig pose.
        if (armsAnimator.runtimeAnimatorController != null)
            armsAnimator.runtimeAnimatorController = null;

        armsAnimator.Rebind();
        armsAnimator.Update(0f);
    }

    private bool HasState(Animator animator, string stateName)
    {
        if (animator == null || string.IsNullOrWhiteSpace(stateName))
            return false;

        int hash = Animator.StringToHash(stateName);
        return animator.HasState(0, hash);
    }

    private void SetShearsVisible(bool visible)
    {
        if (gardenShearsObject != null)
            gardenShearsObject.SetActive(visible);
    }

    private void ResetShearsTransform()
    {
        if (gardenShearsObject == null)
            return;

        gardenShearsObject.transform.localScale = shearsOriginalScale;
        gardenShearsObject.transform.localPosition = shearsOriginalLocalPosition;
    }
}

using System.Collections;
using UnityEngine;

public class GateVines : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private PlayerItemInventory playerItems;
    [SerializeField] private Transform visualRoot;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Cut Timing")]
    [SerializeField] private float cutEffectDelay = 0.25f;

    [Header("Vine Cut Effect")]
    [SerializeField] private float fallDuration = 0.45f;
    [SerializeField] private float fallDistance = 0.45f;
    [SerializeField] private float shrinkTo = 0.15f;
    [SerializeField] private float fallRotation = 18f;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;
    private bool isCleared;
    private bool isCutting;

    private Vector3 visualStartLocalPosition;
    private Vector3 visualStartLocalScale;
    private Quaternion visualStartLocalRotation;

    public bool IsCleared => isCleared;

    private void Awake()
    {
        if (playerCamera == null)
            playerCamera = Camera.main;

        if (playerItems == null)
            playerItems = FindFirstObjectByType<PlayerItemInventory>();

        if (visualRoot == null)
            visualRoot = transform;

        visualStartLocalPosition = visualRoot.localPosition;
        visualStartLocalScale = visualRoot.localScale;
        visualStartLocalRotation = visualRoot.localRotation;
    }

    private void Update()
    {
        if (isCleared || isCutting)
            return;

        isLookedAt = IsPlayerLookingAtVines();

        if (isLookedAt && Input.GetKeyDown(interactKey))
            TryCutVines();
    }

    private bool IsPlayerLookingAtVines()
    {
        if (playerCamera == null)
            return false;

        Ray ray = new Ray(playerCamera.transform.position, playerCamera.transform.forward);

        if (!Physics.Raycast(ray, out RaycastHit hit, interactDistance, ~0, QueryTriggerInteraction.Ignore))
            return false;

        return hit.collider.GetComponentInParent<GateVines>() == this;
    }

    public void TryCutVines()
    {
        if (isCleared || isCutting)
            return;

        if (playerItems == null || !playerItems.HasGardenShears)
            return;

        StartCoroutine(CutVinesRoutine());
    }

    private IEnumerator CutVinesRoutine()
    {
        isCutting = true;
        isLookedAt = false;

        playerItems.PlayGardenShearsCut();

        yield return new WaitForSeconds(cutEffectDelay);

        // Stop the vines from blocking the gate as soon as the blades close.
        foreach (Collider col in GetComponentsInChildren<Collider>(true))
            col.enabled = false;

        yield return AnimateCutVines();

        isCleared = true;

        foreach (Renderer rend in GetComponentsInChildren<Renderer>(true))
            rend.enabled = false;

        isCutting = false;
    }

    private IEnumerator AnimateCutVines()
    {
        if (visualRoot == null || fallDuration <= 0f)
            yield break;

        Vector3 startPosition = visualRoot.localPosition;
        Vector3 startScale = visualRoot.localScale;
        Quaternion startRotation = visualRoot.localRotation;

        Vector3 targetPosition = startPosition + Vector3.down * fallDistance;
        Vector3 targetScale = startScale * Mathf.Clamp(shrinkTo, 0.01f, 1f);
        Quaternion targetRotation =
            startRotation * Quaternion.Euler(fallRotation, 0f, fallRotation * 0.35f);

        float elapsed = 0f;

        while (elapsed < fallDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / fallDuration);

            // Fast initial drop, softer finish.
            float eased = 1f - Mathf.Pow(1f - t, 3f);

            visualRoot.localPosition = Vector3.Lerp(startPosition, targetPosition, eased);
            visualRoot.localScale = Vector3.Lerp(startScale, targetScale, eased);
            visualRoot.localRotation = Quaternion.Slerp(startRotation, targetRotation, eased);

            yield return null;
        }

        visualRoot.localPosition = targetPosition;
        visualRoot.localScale = targetScale;
        visualRoot.localRotation = targetRotation;
    }

    public void ResetVines()
    {
        StopAllCoroutines();

        isLookedAt = false;
        isCleared = false;
        isCutting = false;

        if (visualRoot != null)
        {
            visualRoot.localPosition = visualStartLocalPosition;
            visualRoot.localScale = visualStartLocalScale;
            visualRoot.localRotation = visualStartLocalRotation;
        }

        foreach (Collider col in GetComponentsInChildren<Collider>(true))
            col.enabled = true;

        foreach (Renderer rend in GetComponentsInChildren<Renderer>(true))
            rend.enabled = true;
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt || isCleared || isCutting)
            return;

        string text =
            playerItems != null && playerItems.HasGardenShears
                ? "Нажми " + interactKey + ", чтобы срезать заросли"
                : "Нужен секатор, чтобы срезать заросли";

        GUI.Label(
            new Rect(Screen.width * 0.5f - 210f, Screen.height - 55f, 420f, 30f),
            text
        );
    }
}

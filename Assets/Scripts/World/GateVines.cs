using System.Collections;
using UnityEngine;

public class GateVines : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private PlayerItemInventory playerItems;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Cut Timing")]
    [SerializeField] private float cutEffectDelay = 0.25f;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;
    private bool isCleared;
    private bool isCutting;

    public bool IsCleared => isCleared;

    private void Awake()
    {
        if (playerCamera == null)
            playerCamera = Camera.main;

        if (playerItems == null)
            playerItems = FindFirstObjectByType<PlayerItemInventory>();
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

        isCleared = true;

        foreach (Collider col in GetComponentsInChildren<Collider>(true))
            col.enabled = false;

        foreach (Renderer rend in GetComponentsInChildren<Renderer>(true))
            rend.enabled = false;

        isCutting = false;
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

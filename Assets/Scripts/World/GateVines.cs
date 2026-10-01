using UnityEngine;

public class GateVines : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private PlayerItemInventory playerItems;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;
    private bool isCleared;

    public bool IsCleared => isCleared;

    private void Awake()
    {
        if (playerCamera == null)
        {
            playerCamera = Camera.main;
        }

        if (playerItems == null)
        {
            playerItems = FindFirstObjectByType<PlayerItemInventory>();
        }
    }

    private void Update()
    {
        if (isCleared)
            return;

        isLookedAt = IsPlayerLookingAtVines();

        if (isLookedAt && Input.GetKeyDown(interactKey))
        {
            TryCutVines();
        }
    }

    private bool IsPlayerLookingAtVines()
    {
        if (playerCamera == null)
            return false;

        Ray ray = new Ray(playerCamera.transform.position, playerCamera.transform.forward);

        if (!Physics.Raycast(
                ray,
                out RaycastHit hit,
                interactDistance,
                ~0,
                QueryTriggerInteraction.Ignore))
        {
            return false;
        }

        return hit.collider.GetComponentInParent<GateVines>() == this;
    }

    private void TryCutVines()
    {
        if (playerItems == null || !playerItems.HasGardenShears)
            return;

        isCleared = true;
        isLookedAt = false;

        foreach (Collider collider in GetComponentsInChildren<Collider>(true))
        {
            collider.enabled = false;
        }

        foreach (Renderer renderer in GetComponentsInChildren<Renderer>(true))
        {
            renderer.enabled = false;
        }
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt || isCleared)
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

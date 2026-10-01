using UnityEngine;

public class GardenShearsPickup : MonoBehaviour
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
        isLookedAt = IsPlayerLookingAtPickup();

        if (isLookedAt && Input.GetKeyDown(interactKey))
        {
            PickUp();
        }
    }

    private bool IsPlayerLookingAtPickup()
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

        return hit.collider.GetComponentInParent<GardenShearsPickup>() == this;
    }

    private void PickUp()
    {
        if (playerItems == null)
            return;

        playerItems.GiveGardenShears();
        gameObject.SetActive(false);
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt)
            return;

        GUI.Label(
            new Rect(Screen.width * 0.5f - 170f, Screen.height - 55f, 340f, 30f),
            "Нажми " + interactKey + ", чтобы взять секатор"
        );
    }
}

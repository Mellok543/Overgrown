using UnityEngine;

public class GrassSellPoint : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private EconomyManager economy;
    [SerializeField] private Camera playerCamera;
    [SerializeField] private GrassInventory playerInventory;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode sellKey = KeyCode.E;

    [Header("Selling")]
    [SerializeField] private int pricePerBundle = 2;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;

    private void Awake()
    {
        if (economy == null)
        {
            economy = FindFirstObjectByType<EconomyManager>();
        }

        if (playerInventory == null)
        {
            playerInventory = FindFirstObjectByType<GrassInventory>();
        }

        if (playerCamera == null)
        {
            Camera mainCamera = Camera.main;

            if (mainCamera != null)
            {
                playerCamera = mainCamera;
            }
            else if (playerInventory != null)
            {
                playerCamera = playerInventory.GetComponentInChildren<Camera>();
            }
        }
    }

    private void Update()
    {
        isLookedAt = IsPlayerLookingAtSellPoint();

        if (isLookedAt && Input.GetKeyDown(sellKey))
        {
            SellAll();
        }
    }

    private bool IsPlayerLookingAtSellPoint()
    {
        if (playerCamera == null)
            return false;

        Ray ray = new Ray(
            playerCamera.transform.position,
            playerCamera.transform.forward
        );

        if (!Physics.Raycast(
                ray,
                out RaycastHit hit,
                interactDistance,
                ~0,
                QueryTriggerInteraction.Ignore))
        {
            return false;
        }

        return hit.collider.GetComponentInParent<GrassSellPoint>() == this;
    }

    public void SellAll()
    {
        if (playerInventory == null || economy == null)
            return;

        int bundles = playerInventory.RemoveAllBundles();

        if (bundles <= 0)
            return;

        economy.AddMoney(bundles * pricePerBundle);
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt)
            return;

        string text = playerInventory != null && playerInventory.Bundles > 0
            ? "Нажми " + sellKey + ", чтобы продать " + playerInventory.Bundles +
              " пучков за $" + (playerInventory.Bundles * pricePerBundle)
            : "У тебя нет пучков травы";

        GUI.Label(
            new Rect(Screen.width * 0.5f - 220f, Screen.height - 55f, 440f, 30f),
            text
        );
    }
}

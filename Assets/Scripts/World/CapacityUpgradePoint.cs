using UnityEngine;

public class CapacityUpgradePoint : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private EconomyManager economy;
    [SerializeField] private GrassInventory playerInventory;
    [SerializeField] private Camera playerCamera;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Capacity Levels")]
    [SerializeField] private int[] capacityLevels = { 10, 20, 35, 50 };
    [SerializeField] private int[] prices = { 20, 60, 150, 300 };

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;
    private int nextUpgradeIndex;

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

        RefreshUpgradeIndex();
    }

    private void Update()
    {
        isLookedAt = IsPlayerLookingAtPoint();

        if (isLookedAt && Input.GetKeyDown(interactKey))
        {
            TryBuyUpgrade();
        }
    }

    private bool IsPlayerLookingAtPoint()
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

        return hit.collider.GetComponentInParent<CapacityUpgradePoint>() == this;
    }

    private void RefreshUpgradeIndex()
    {
        nextUpgradeIndex = 0;

        if (playerInventory == null)
            return;

        while (
            nextUpgradeIndex < capacityLevels.Length &&
            capacityLevels[nextUpgradeIndex] <= playerInventory.Capacity
        )
        {
            nextUpgradeIndex++;
        }
    }

    public void TryBuyUpgrade()
    {
        if (playerInventory == null || economy == null)
            return;

        RefreshUpgradeIndex();

        if (nextUpgradeIndex >= capacityLevels.Length)
            return;

        if (nextUpgradeIndex >= prices.Length)
        {
            Debug.LogWarning("CapacityUpgradePoint: not enough prices configured.", this);
            return;
        }

        int targetCapacity = capacityLevels[nextUpgradeIndex];
        int price = prices[nextUpgradeIndex];

        if (!economy.SpendMoney(price))
            return;

        int amountToAdd = targetCapacity - playerInventory.Capacity;

        if (amountToAdd > 0)
        {
            playerInventory.AddCapacity(amountToAdd);
        }

        RefreshUpgradeIndex();
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt || playerInventory == null)
            return;

        RefreshUpgradeIndex();

        string text;

        if (nextUpgradeIndex >= capacityLevels.Length)
        {
            text = "Вместимость улучшена до максимума: " + playerInventory.Capacity;
        }
        else if (nextUpgradeIndex >= prices.Length)
        {
            text = "Ошибка настройки цен улучшений";
        }
        else
        {
            int targetCapacity = capacityLevels[nextUpgradeIndex];
            int price = prices[nextUpgradeIndex];

            text =
                "Нажми " + interactKey +
                ", чтобы увеличить вместимость " +
                playerInventory.Capacity + " -> " + targetCapacity +
                " за $" + price;
        }

        GUI.Label(
            new Rect(Screen.width * 0.5f - 260f, Screen.height - 55f, 520f, 30f),
            text
        );
    }
}

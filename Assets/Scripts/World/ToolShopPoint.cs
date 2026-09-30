using UnityEngine;

public class ToolShopPoint : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private EconomyManager economy;
    [SerializeField] private ToolInventory toolInventory;
    [SerializeField] private Camera playerCamera;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Tool")]
    [SerializeField] private ToolInventory.ToolType toolType = ToolInventory.ToolType.Sickle;
    [SerializeField] private int price = 50;
    [SerializeField] private bool autoEquipAfterBuy = true;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;

    private void Awake()
    {
        if (economy == null)
        {
            economy = FindFirstObjectByType<EconomyManager>();
        }

        if (toolInventory == null)
        {
            toolInventory = FindFirstObjectByType<ToolInventory>();
        }

        if (playerCamera == null)
        {
            Camera mainCamera = Camera.main;

            if (mainCamera != null)
            {
                playerCamera = mainCamera;
            }
            else if (toolInventory != null)
            {
                playerCamera = toolInventory.GetComponentInChildren<Camera>();
            }
        }
    }

    private void Update()
    {
        isLookedAt = IsPlayerLookingAtPoint();

        if (isLookedAt && Input.GetKeyDown(interactKey))
        {
            TryBuyTool();
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

        return hit.collider.GetComponentInParent<ToolShopPoint>() == this;
    }

    public void TryBuyTool()
    {
        if (economy == null || toolInventory == null)
            return;

        if (toolInventory.IsToolUnlocked(toolType))
        {
            if (autoEquipAfterBuy)
            {
                toolInventory.SelectTool(toolType);
            }

            return;
        }

        if (!economy.SpendMoney(price))
            return;

        toolInventory.UnlockTool(toolType);

        if (autoEquipAfterBuy)
        {
            toolInventory.SelectTool(toolType);
        }
    }

    private string GetToolName()
    {
        return toolType switch
        {
            ToolInventory.ToolType.Sickle => "серп",
            ToolInventory.ToolType.Trimmer => "триммер",
            ToolInventory.ToolType.Mower => "газонокосилку",
            _ => "инструмент"
        };
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt || toolInventory == null)
            return;

        string text;

        if (toolInventory.IsToolUnlocked(toolType))
        {
            text = "Нажми " + interactKey + ", чтобы взять " + GetToolName();
        }
        else
        {
            text = "Нажми " + interactKey + ", чтобы купить " + GetToolName() + " за $" + price;
        }

        GUI.Label(
            new Rect(Screen.width * 0.5f - 220f, Screen.height - 55f, 440f, 30f),
            text
        );
    }
}

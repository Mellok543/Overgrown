using UnityEngine;
using UnityEngine.UI;

public class GameHUD : MonoBehaviour
{
    [Header("Sources")]
    [SerializeField] private EconomyManager economy;
    [SerializeField] private GrassInventory grassInventory;
    [SerializeField] private ToolInventory toolInventory;
    [SerializeField] private StartZoneProgress zoneProgress;

    [Header("Main HUD")]
    [SerializeField] private Text moneyText;
    [SerializeField] private Text grassText;
    [SerializeField] private Text toolText;
    [SerializeField] private Text zoneText;
    [SerializeField] private Text objectiveText;
    [SerializeField] private Image grassFill;
    [SerializeField] private Image zoneFill;

    [Header("Tool Belt")]
    [SerializeField] private Image[] toolSlots;
    [SerializeField] private Text[] toolSlotLabels;

    private static readonly Color SlotIdle =
        new Color(0.10f, 0.12f, 0.09f, 0.88f);

    private static readonly Color SlotLocked =
        new Color(0.055f, 0.06f, 0.05f, 0.56f);

    private static readonly Color SlotActive =
        new Color(0.48f, 0.58f, 0.22f, 0.96f);

    private static readonly Color TextNormal =
        new Color(0.92f, 0.90f, 0.80f, 1f);

    private static readonly Color TextLocked =
        new Color(0.38f, 0.40f, 0.34f, 1f);

    private void Awake()
    {
        if (economy == null)
            economy = FindFirstObjectByType<EconomyManager>();

        if (grassInventory == null)
            grassInventory = FindFirstObjectByType<GrassInventory>();

        if (toolInventory == null)
            toolInventory = FindFirstObjectByType<ToolInventory>();

        if (zoneProgress == null)
            zoneProgress = FindFirstObjectByType<StartZoneProgress>();

        RefreshAll();
    }

    private void OnEnable()
    {
        if (economy != null)
            economy.MoneyChanged += HandleMoneyChanged;

        if (grassInventory != null)
            grassInventory.InventoryChanged += HandleInventoryChanged;

        RefreshAll();
    }

    private void OnDisable()
    {
        if (economy != null)
            economy.MoneyChanged -= HandleMoneyChanged;

        if (grassInventory != null)
            grassInventory.InventoryChanged -= HandleInventoryChanged;
    }

    private void Update()
    {
        RefreshTool();
        RefreshZone();
    }

    private void HandleMoneyChanged(int value)
    {
        RefreshMoney();
    }

    private void HandleInventoryChanged(int bundles, int capacity)
    {
        RefreshGrass();
    }

    private void RefreshAll()
    {
        RefreshMoney();
        RefreshGrass();
        RefreshTool();
        RefreshZone();
    }

    private void RefreshMoney()
    {
        if (moneyText != null)
            moneyText.text = economy != null ? "$ " + economy.Money : "$ 0";
    }

    private void RefreshGrass()
    {
        int bundles = grassInventory != null ? grassInventory.Bundles : 0;
        int capacity = grassInventory != null ? grassInventory.Capacity : 1;

        if (grassText != null)
            grassText.text = bundles + " / " + capacity;

        if (grassFill != null)
            grassFill.fillAmount =
                capacity > 0 ? Mathf.Clamp01((float)bundles / capacity) : 0f;
    }

    private void RefreshTool()
    {
        if (toolInventory == null)
            return;

        string value = GetToolName(toolInventory.CurrentTool);

        if (toolText != null)
            toolText.text = value;

        if (toolSlots == null || toolSlotLabels == null)
            return;

        ToolInventory.ToolType[] order =
        {
            ToolInventory.ToolType.Hands,
            ToolInventory.ToolType.Sickle,
            ToolInventory.ToolType.Trimmer,
            ToolInventory.ToolType.Mower,
            ToolInventory.ToolType.GardenShears
        };

        for (int i = 0; i < order.Length; i++)
        {
            if (i >= toolSlots.Length || i >= toolSlotLabels.Length)
                break;

            bool unlocked = toolInventory.IsToolUnlocked(order[i]);
            bool active = toolInventory.CurrentTool == order[i];

            if (toolSlots[i] != null)
                toolSlots[i].color =
                    active ? SlotActive : unlocked ? SlotIdle : SlotLocked;

            if (toolSlotLabels[i] != null)
            {
                toolSlotLabels[i].color = unlocked ? TextNormal : TextLocked;
                toolSlotLabels[i].text =
                    (i + 1) + "\n" + (unlocked ? GetShortToolName(order[i]) : "—");
            }
        }
    }

    private void RefreshZone()
    {
        if (zoneText == null || zoneProgress == null)
            return;

        if (zoneProgress.Completed)
        {
            zoneText.text = "100%";
            if (objectiveText != null)
                objectiveText.text = "ДВОР ОЧИЩЕН";

            if (zoneFill != null)
                zoneFill.fillAmount = 1f;

            return;
        }

        float progress = Mathf.Clamp01(zoneProgress.Progress);

        zoneText.text = Mathf.RoundToInt(progress * 100f) + "%";

        if (objectiveText != null)
            objectiveText.text = "ОЧИСТИТЕ ДВОР";

        if (zoneFill != null)
            zoneFill.fillAmount = progress;
    }

    private static string GetToolName(ToolInventory.ToolType tool)
    {
        return tool switch
        {
            ToolInventory.ToolType.Hands => "РУКИ",
            ToolInventory.ToolType.Sickle => "СЕРП",
            ToolInventory.ToolType.Trimmer => "ТРИММЕР",
            ToolInventory.ToolType.Mower => "ГАЗОНОКОСИЛКА",
            ToolInventory.ToolType.GardenShears => "СЕКАТОР",
            _ => tool.ToString().ToUpperInvariant()
        };
    }

    private static string GetShortToolName(ToolInventory.ToolType tool)
    {
        return tool switch
        {
            ToolInventory.ToolType.Hands => "РУКИ",
            ToolInventory.ToolType.Sickle => "СЕРП",
            ToolInventory.ToolType.Trimmer => "ТРИМ",
            ToolInventory.ToolType.Mower => "КОСИЛ",
            ToolInventory.ToolType.GardenShears => "СЕКАТ",
            _ => "?"
        };
    }
}

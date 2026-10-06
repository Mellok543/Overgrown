using UnityEngine;
using UnityEngine.UI;

public class GameHUD : MonoBehaviour
{
    [Header("Sources")]
    [SerializeField] private EconomyManager economy;
    [SerializeField] private GrassInventory grassInventory;
    [SerializeField] private ToolInventory toolInventory;
    [SerializeField] private StartZoneProgress zoneProgress;

    [Header("HUD")]
    [SerializeField] private Text moneyText;
    [SerializeField] private Text grassText;
    [SerializeField] private Text toolText;
    [SerializeField] private Text zoneText;
    [SerializeField] private Image grassFill;
    [SerializeField] private Image zoneFill;

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
            grassText.text = "Трава  " + bundles + " / " + capacity;

        if (grassFill != null)
            grassFill.fillAmount = capacity > 0 ? Mathf.Clamp01((float)bundles / capacity) : 0f;
    }

    private void RefreshTool()
    {
        if (toolText == null || toolInventory == null)
            return;

        string value = toolInventory.CurrentTool switch
        {
            ToolInventory.ToolType.Hands => "1  Руки",
            ToolInventory.ToolType.Sickle => "2  Серп",
            ToolInventory.ToolType.Trimmer => "3  Триммер",
            ToolInventory.ToolType.Mower => "4  Газонокосилка",
            ToolInventory.ToolType.GardenShears => "5  Секатор",
            _ => toolInventory.CurrentTool.ToString()
        };

        toolText.text = value;
    }

    private void RefreshZone()
    {
        if (zoneText == null || zoneProgress == null)
            return;

        if (zoneProgress.Completed)
        {
            zoneText.text = "Двор очищен";
            if (zoneFill != null)
                zoneFill.fillAmount = 1f;
            return;
        }

        float progress = Mathf.Clamp01(zoneProgress.Progress);

        zoneText.text = "Двор  " + Mathf.RoundToInt(progress * 100f) + "%";

        if (zoneFill != null)
            zoneFill.fillAmount = progress;
    }
}

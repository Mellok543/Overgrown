using UnityEngine;

public class EconomyManager : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private GrassCutter grassCutter;
    [SerializeField] private SickleSwing sickleSwing;

    [Header("Economy")]
    [SerializeField] private int moneyPerGrass = 1;
    [SerializeField] private int startingMoney = 0;

    [Header("Upgrade Prices")]
    [SerializeField] private int radiusUpgradePrice = 25;
    [SerializeField] private int distanceUpgradePrice = 30;
    [SerializeField] private int speedUpgradePrice = 40;

    [Header("Upgrade Values")]
    [SerializeField] private float radiusUpgradeAmount = 0.15f;
    [SerializeField] private float distanceUpgradeAmount = 0.2f;
    [SerializeField] private float cooldownReduction = 0.03f;

    [Header("Prototype UI")]
    [SerializeField] private bool showUI = true;

    private GrassCuttable[] grassObjects;
    private int money;

    public int Money => money;

    private void Awake()
    {
        money = startingMoney;

        if (grassCutter == null)
        {
            grassCutter = FindFirstObjectByType<GrassCutter>();
        }

        if (sickleSwing == null)
        {
            sickleSwing = FindFirstObjectByType<SickleSwing>();
        }
    }

    private void Start()
    {
        SubscribeToGrass();
    }

    private void OnDestroy()
    {
        UnsubscribeFromGrass();
    }

    public void RefreshGrassList()
    {
        UnsubscribeFromGrass();
        SubscribeToGrass();
    }

    private void SubscribeToGrass()
    {
        grassObjects = FindObjectsByType<GrassCuttable>(
            FindObjectsInactive.Include,
            FindObjectsSortMode.None
        );

        foreach (GrassCuttable grass in grassObjects)
        {
            if (grass != null)
            {
                grass.CutStateChanged += HandleGrassStateChanged;
            }
        }
    }

    private void UnsubscribeFromGrass()
    {
        if (grassObjects == null)
            return;

        foreach (GrassCuttable grass in grassObjects)
        {
            if (grass != null)
            {
                grass.CutStateChanged -= HandleGrassStateChanged;
            }
        }
    }

    private void HandleGrassStateChanged(GrassCuttable grass, bool isCut)
    {
        if (isCut)
        {
            AddMoney(moneyPerGrass);
        }
    }

    public void AddMoney(int amount)
    {
        money = Mathf.Max(0, money + amount);
    }

    public bool SpendMoney(int amount)
    {
        if (amount < 0 || money < amount)
            return false;

        money -= amount;
        return true;
    }

    public void BuyRadiusUpgrade()
    {
        if (grassCutter == null || !SpendMoney(radiusUpgradePrice))
            return;

        grassCutter.AddCutRadius(radiusUpgradeAmount);
        radiusUpgradePrice = Mathf.CeilToInt(radiusUpgradePrice * 1.5f);
    }

    public void BuyDistanceUpgrade()
    {
        if (grassCutter == null || !SpendMoney(distanceUpgradePrice))
            return;

        grassCutter.AddCutDistance(distanceUpgradeAmount);
        distanceUpgradePrice = Mathf.CeilToInt(distanceUpgradePrice * 1.5f);
    }

    public void BuySpeedUpgrade()
    {
        if (sickleSwing == null || !SpendMoney(speedUpgradePrice))
            return;

        sickleSwing.ReduceCooldown(cooldownReduction);
        speedUpgradePrice = Mathf.CeilToInt(speedUpgradePrice * 1.5f);
    }

    private void OnGUI()
    {
        if (!showUI)
            return;

        GUILayout.BeginArea(new Rect(20f, 105f, 300f, 210f), GUI.skin.box);

        GUILayout.Label($"Деньги: $${money}");
        GUILayout.Space(5f);
        GUILayout.Label("Улучшения серпа");

        if (grassCutter != null)
        {
            GUILayout.Label($"Радиус среза: {grassCutter.CutRadius:0.00}");
            if (GUILayout.Button($"Увеличить радиус — $${radiusUpgradePrice}"))
            {
                BuyRadiusUpgrade();
            }

            GUILayout.Label($"Дальность: {grassCutter.CutDistance:0.00}");
            if (GUILayout.Button($"Увеличить дальность — $${distanceUpgradePrice}"))
            {
                BuyDistanceUpgrade();
            }
        }

        if (sickleSwing != null)
        {
            GUILayout.Label($"Задержка удара: {sickleSwing.Cooldown:0.00} сек.");
            if (GUILayout.Button($"Ускорить серп — $${speedUpgradePrice}"))
            {
                BuySpeedUpgrade();
            }
        }

        GUILayout.EndArea();
    }
}

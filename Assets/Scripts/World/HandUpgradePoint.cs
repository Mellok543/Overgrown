using UnityEngine;

public class HandUpgradePoint : MonoBehaviour
{
    public enum HandUpgradeType
    {
        BundlesPerCollect,
        CollectSpeed,
        CollectRadius
    }

    [Header("References")]
    [SerializeField] private EconomyManager economy;
    [SerializeField] private HandGrassCollector collector;
    [SerializeField] private Camera playerCamera;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Upgrade")]
    [SerializeField] private HandUpgradeType upgradeType;

    [Header("Bundles Per Collect")]
    [SerializeField] private int[] bundleLevels = { 2, 3, 4, 5 };
    [SerializeField] private int[] bundlePrices = { 25, 70, 160, 320 };

    [Header("Collect Speed")]
    [SerializeField] private float[] speedLevels = { 0.48f, 0.36f, 0.26f, 0.18f };
    [SerializeField] private int[] speedPrices = { 20, 55, 130, 280 };

    [Header("Collect Radius")]
    [SerializeField] private float[] radiusLevels = { 0.65f, 0.9f, 1.2f, 1.6f };
    [SerializeField] private int[] radiusPrices = { 20, 60, 140, 300 };

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool isLookedAt;

    private void Awake()
    {
        if (economy == null)
        {
            economy = FindFirstObjectByType<EconomyManager>();
        }

        if (collector == null)
        {
            collector = FindFirstObjectByType<HandGrassCollector>();
        }

        if (playerCamera == null)
        {
            Camera mainCamera = Camera.main;

            if (mainCamera != null)
            {
                playerCamera = mainCamera;
            }
            else if (collector != null)
            {
                playerCamera = collector.GetComponentInChildren<Camera>();
            }
        }
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

        return hit.collider.GetComponentInParent<HandUpgradePoint>() == this;
    }

    private int GetNextUpgradeIndex()
    {
        if (collector == null)
            return -1;

        switch (upgradeType)
        {
            case HandUpgradeType.BundlesPerCollect:
                for (int i = 0; i < bundleLevels.Length; i++)
                {
                    if (collector.BundlesPerCollect < bundleLevels[i])
                        return i;
                }
                break;

            case HandUpgradeType.CollectSpeed:
                for (int i = 0; i < speedLevels.Length; i++)
                {
                    if (collector.CollectDuration > speedLevels[i] + 0.001f)
                        return i;
                }
                break;

            case HandUpgradeType.CollectRadius:
                for (int i = 0; i < radiusLevels.Length; i++)
                {
                    if (collector.CollectRadius < radiusLevels[i] - 0.001f)
                        return i;
                }
                break;
        }

        return -1;
    }

    private int GetPrice(int index)
    {
        switch (upgradeType)
        {
            case HandUpgradeType.BundlesPerCollect:
                return index >= 0 && index < bundlePrices.Length
                    ? bundlePrices[index]
                    : -1;

            case HandUpgradeType.CollectSpeed:
                return index >= 0 && index < speedPrices.Length
                    ? speedPrices[index]
                    : -1;

            case HandUpgradeType.CollectRadius:
                return index >= 0 && index < radiusPrices.Length
                    ? radiusPrices[index]
                    : -1;
        }

        return -1;
    }

    public void TryBuyUpgrade()
    {
        if (economy == null || collector == null)
            return;

        int index = GetNextUpgradeIndex();

        if (index < 0)
            return;

        int price = GetPrice(index);

        if (price < 0)
        {
            Debug.LogWarning("HandUpgradePoint: missing price for configured upgrade level.", this);
            return;
        }

        if (!economy.SpendMoney(price))
            return;

        ApplyUpgrade(index);
    }

    private void ApplyUpgrade(int index)
    {
        switch (upgradeType)
        {
            case HandUpgradeType.BundlesPerCollect:
                if (index < bundleLevels.Length)
                {
                    collector.SetBundlesPerCollect(bundleLevels[index]);
                }
                break;

            case HandUpgradeType.CollectSpeed:
                if (index < speedLevels.Length)
                {
                    collector.SetCollectDuration(speedLevels[index]);
                }
                break;

            case HandUpgradeType.CollectRadius:
                if (index < radiusLevels.Length)
                {
                    collector.SetCollectRadius(radiusLevels[index]);
                }
                break;
        }
    }

    private string GetUpgradeName()
    {
        switch (upgradeType)
        {
            case HandUpgradeType.BundlesPerCollect:
                return "количество пучков";

            case HandUpgradeType.CollectSpeed:
                return "скорость сбора";

            case HandUpgradeType.CollectRadius:
                return "радиус сбора";
        }

        return "улучшение";
    }

    private string GetCurrentValue()
    {
        if (collector == null)
            return "?";

        switch (upgradeType)
        {
            case HandUpgradeType.BundlesPerCollect:
                return collector.BundlesPerCollect.ToString();

            case HandUpgradeType.CollectSpeed:
                return collector.CollectDuration.ToString("0.00") + " c";

            case HandUpgradeType.CollectRadius:
                return collector.CollectRadius.ToString("0.00") + " м";
        }

        return "?";
    }

    private string GetNextValue(int index)
    {
        switch (upgradeType)
        {
            case HandUpgradeType.BundlesPerCollect:
                return index < bundleLevels.Length
                    ? bundleLevels[index].ToString()
                    : "?";

            case HandUpgradeType.CollectSpeed:
                return index < speedLevels.Length
                    ? speedLevels[index].ToString("0.00") + " c"
                    : "?";

            case HandUpgradeType.CollectRadius:
                return index < radiusLevels.Length
                    ? radiusLevels[index].ToString("0.00") + " м"
                    : "?";
        }

        return "?";
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt || collector == null)
            return;

        int index = GetNextUpgradeIndex();
        string text;

        if (index < 0)
        {
            text = GetUpgradeName() + ": максимальный уровень";
        }
        else
        {
            int price = GetPrice(index);

            text =
                "Нажми " + interactKey +
                ": " + GetUpgradeName() +
                " " + GetCurrentValue() +
                " -> " + GetNextValue(index) +
                " за $" + price;
        }

        GUI.Label(
            new Rect(Screen.width * 0.5f - 270f, Screen.height - 55f, 540f, 30f),
            text
        );
    }
}

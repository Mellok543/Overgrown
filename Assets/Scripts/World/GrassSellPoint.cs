using UnityEngine;

public class GrassSellPoint : MonoBehaviour
{
    [SerializeField] private EconomyManager economy;
    [SerializeField] private int pricePerBundle = 2;
    [SerializeField] private KeyCode sellKey = KeyCode.E;
    [SerializeField] private bool showPrototypeUI = true;

    private GrassInventory nearbyInventory;

    private void Awake()
    {
        if (economy == null)
        {
            economy = FindFirstObjectByType<EconomyManager>();
        }
    }

    private void Update()
    {
        if (nearbyInventory == null)
            return;

        if (Input.GetKeyDown(sellKey))
        {
            SellAll();
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        GrassInventory inventory = other.GetComponentInParent<GrassInventory>();

        if (inventory != null)
        {
            nearbyInventory = inventory;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        GrassInventory inventory = other.GetComponentInParent<GrassInventory>();

        if (inventory != null && inventory == nearbyInventory)
        {
            nearbyInventory = null;
        }
    }

    public void SellAll()
    {
        if (nearbyInventory == null || economy == null)
            return;

        int bundles = nearbyInventory.RemoveAllBundles();

        if (bundles <= 0)
            return;

        economy.AddMoney(bundles * pricePerBundle);
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || nearbyInventory == null)
            return;

        string text = nearbyInventory.Bundles > 0
            ? "Нажми " + sellKey + ", чтобы продать " + nearbyInventory.Bundles +
              " пучков за $" + (nearbyInventory.Bundles * pricePerBundle)
            : "У тебя нет пучков травы";

        GUI.Label(
            new Rect(Screen.width * 0.5f - 220f, Screen.height - 55f, 440f, 30f),
            text
        );
    }
}

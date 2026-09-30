using System;
using UnityEngine;

public class GrassInventory : MonoBehaviour
{
    [SerializeField] private int startingCapacity = 5;
    [SerializeField] private bool showPrototypeUI = true;

    private int bundles;
    private int capacity;

    public int Bundles => bundles;
    public int Capacity => capacity;
    public bool IsFull => bundles >= capacity;

    public event Action<int, int> InventoryChanged;

    private void Awake()
    {
        capacity = Mathf.Max(1, startingCapacity);
        bundles = 0;
    }

    public int TryAddBundles(int amount)
    {
        if (amount <= 0)
            return 0;

        int freeSpace = capacity - bundles;
        int added = Mathf.Clamp(amount, 0, freeSpace);

        if (added <= 0)
            return 0;

        bundles += added;
        InventoryChanged?.Invoke(bundles, capacity);
        return added;
    }

    public int RemoveBundles(int amount)
    {
        if (amount <= 0)
            return 0;

        int removed = Mathf.Min(amount, bundles);
        bundles -= removed;

        if (removed > 0)
        {
            InventoryChanged?.Invoke(bundles, capacity);
        }

        return removed;
    }

    public int RemoveAllBundles()
    {
        return RemoveBundles(bundles);
    }

    public void AddCapacity(int amount)
    {
        if (amount <= 0)
            return;

        capacity += amount;
        InventoryChanged?.Invoke(bundles, capacity);
    }

    private void OnGUI()
    {
        if (!showPrototypeUI)
            return;

        GUI.Label(
            new Rect(20f, 130f, 240f, 25f),
            "Пучки травы: " + bundles + " / " + capacity
        );
    }
}

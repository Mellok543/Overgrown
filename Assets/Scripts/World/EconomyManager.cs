using System;
using UnityEngine;

public class EconomyManager : MonoBehaviour
{
    [SerializeField] private int startingMoney = 0;
    [SerializeField] private bool showPrototypeUI = true;

    private int money;

    public int Money => money;

    public event Action<int> MoneyChanged;

    private void Awake()
    {
        money = Mathf.Max(0, startingMoney);
    }

    public void AddMoney(int amount)
    {
        if (amount <= 0)
            return;

        money += amount;
        MoneyChanged?.Invoke(money);
    }

    public bool SpendMoney(int amount)
    {
        if (amount < 0 || money < amount)
            return false;

        money -= amount;
        MoneyChanged?.Invoke(money);
        return true;
    }

    private void OnGUI()
    {
        if (!showPrototypeUI)
            return;

        GUI.Label(new Rect(20f, 105f, 220f, 25f), "Деньги: $" + money);
    }
}

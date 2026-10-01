using UnityEngine;

public class PlayerItemInventory : MonoBehaviour
{
    [Header("Quest Items")]
    [SerializeField] private bool hasGardenShears;

    public bool HasGardenShears => hasGardenShears;

    public void GiveGardenShears()
    {
        hasGardenShears = true;
    }
}

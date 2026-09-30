using System;
using UnityEngine;

public class GrassCuttable : MonoBehaviour
{
    [Header("Visuals")]
    [SerializeField] private GameObject[] fullGrassVariants;
    [SerializeField] private GameObject cutGrass;
    [SerializeField] private bool chooseRandomVariant = true;

    private bool isCut;
    private int activeVariantIndex;

    public bool IsCut => isCut;

    public event Action<GrassCuttable, bool> CutStateChanged;

    private void Awake()
    {
        SetupVisuals(false);
    }

    private void SetupVisuals(bool notify)
    {
        if (fullGrassVariants == null || fullGrassVariants.Length == 0)
        {
            Debug.LogWarning($"GrassCuttable on {name} has no full grass variants assigned.", this);
            return;
        }

        activeVariantIndex = chooseRandomVariant
            ? UnityEngine.Random.Range(0, fullGrassVariants.Length)
            : 0;

        for (int i = 0; i < fullGrassVariants.Length; i++)
        {
            if (fullGrassVariants[i] != null)
            {
                fullGrassVariants[i].SetActive(i == activeVariantIndex);
            }
        }

        if (cutGrass != null)
        {
            cutGrass.SetActive(false);
        }

        isCut = false;

        if (notify)
        {
            CutStateChanged?.Invoke(this, false);
        }
    }

    public void Cut()
    {
        if (isCut)
            return;

        isCut = true;

        if (fullGrassVariants != null)
        {
            foreach (GameObject variant in fullGrassVariants)
            {
                if (variant != null)
                {
                    variant.SetActive(false);
                }
            }
        }

        if (cutGrass != null)
        {
            cutGrass.SetActive(true);
        }

        CutStateChanged?.Invoke(this, true);
    }

    public void ResetGrass()
    {
        SetupVisuals(true);
    }
}

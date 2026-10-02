using System;
using UnityEngine;

public class GrassCuttable : MonoBehaviour
{
    [Header("Visuals")]
    [SerializeField] private GameObject[] fullGrassVariants;
    [SerializeField] private GameObject cutGrass;
    [SerializeField] private bool chooseRandomVariant = true;

    [Header("Highlight")]
    [SerializeField] private Color highlightColor = new Color(1f, 0.9f, 0.35f, 1f);
    [SerializeField, Range(0f, 3f)] private float highlightIntensity = 1.35f;

    private bool isCut;
    private int activeVariantIndex;
    private bool isHighlighted;

    private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
    private static readonly int LegacyColorId = Shader.PropertyToID("_Color");
    private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");

    private MaterialPropertyBlock propertyBlock;

    public bool IsCut => isCut;

    public event Action<GrassCuttable, bool> CutStateChanged;

    private void Awake()
    {
        SetupVisuals(false);
    }

    private void OnDisable()
    {
        if (isHighlighted)
        {
            SetHighlighted(false);
        }
    }

    private void SetupVisuals(bool notify)
    {
        if (fullGrassVariants == null || fullGrassVariants.Length == 0)
        {
            Debug.LogWarning("GrassCuttable on " + name + " has no full grass variants assigned.", this);
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
        SetHighlighted(false);

        if (notify)
        {
            CutStateChanged?.Invoke(this, false);
        }
    }

    public void SetHighlighted(bool highlighted)
    {
        if (isHighlighted == highlighted)
            return;

        isHighlighted = highlighted;

        GameObject activeVisual = GetActiveVisual();

        if (activeVisual == null)
            return;

        Renderer[] renderers = activeVisual.GetComponentsInChildren<Renderer>(true);

        foreach (Renderer renderer in renderers)
        {
            if (renderer == null)
                continue;

            if (propertyBlock == null)\n            {\n                propertyBlock = new MaterialPropertyBlock();\n            }\n\n            renderer.GetPropertyBlock(propertyBlock);

            if (highlighted)
            {
                Color glow = highlightColor * highlightIntensity;
                propertyBlock.SetColor(BaseColorId, highlightColor);
                propertyBlock.SetColor(LegacyColorId, highlightColor);
                propertyBlock.SetColor(EmissionColorId, glow);
            }
            else
            {
                propertyBlock.Clear();
            }

            renderer.SetPropertyBlock(propertyBlock);
        }
    }

    private GameObject GetActiveVisual()
    {
        if (isCut)
        {
            return cutGrass;
        }

        if (fullGrassVariants == null ||
            activeVariantIndex < 0 ||
            activeVariantIndex >= fullGrassVariants.Length)
        {
            return null;
        }

        return fullGrassVariants[activeVariantIndex];
    }

    public bool Cut()
    {
        if (isCut)
            return false;

        SetHighlighted(false);
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
        return true;
    }

    public void ResetGrass()
    {
        SetupVisuals(true);
    }
}

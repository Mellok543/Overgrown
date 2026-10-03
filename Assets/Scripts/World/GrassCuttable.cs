using System;
using UnityEngine;

public class GrassCuttable : MonoBehaviour
{
    [Header("Visuals")]
    [SerializeField] private GameObject[] fullGrassVariants;
    [SerializeField] private GameObject cutGrass;
    [SerializeField] private bool chooseRandomVariant = true;

    [Header("Highlight")]
    [SerializeField] private bool useScaleHighlight = true;
    [SerializeField, Range(1f, 1.3f)] private float highlightScaleMultiplier = 1.12f;
    [SerializeField, Range(0f, 0.15f)] private float highlightLift = 0.04f;
    [SerializeField] private Color highlightColor = new Color(1f, 0.92f, 0.45f, 1f);
    [SerializeField, Range(0f, 3f)] private float highlightIntensity = 1.25f;

    private bool isCut;
    private int activeVariantIndex;
    private bool isHighlighted;

    private GameObject highlightedVisual;
    private Vector3 originalRootScale;
    private Vector3 originalRootLocalPosition;

    private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
    private static readonly int LegacyColorId = Shader.PropertyToID("_Color");
    private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");

    private MaterialPropertyBlock propertyBlock;

    public bool IsCut => isCut;

    public event Action<GrassCuttable, bool> CutStateChanged;

    private void Awake()
    {
        propertyBlock = new MaterialPropertyBlock();
        originalRootScale = transform.localScale;
        originalRootLocalPosition = transform.localPosition;
        SetupVisuals(false);
    }

    private void OnDisable()
    {
        ClearHighlight();
    }

    private void SetupVisuals(bool notify)
    {
        ClearHighlight();

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

        if (notify)
        {
            CutStateChanged?.Invoke(this, false);
        }
    }

    public void SetHighlighted(bool highlighted)
    {
        if (highlighted)
        {
            ApplyHighlight();
        }
        else
        {
            ClearHighlight();
        }
    }

    private void ApplyHighlight()
    {
        if (isCut || isHighlighted)
            return;

        GameObject activeVisual = GetActiveVisual();

        if (activeVisual == null)
            return;

        isHighlighted = true;
        highlightedVisual = activeVisual;

        if (useScaleHighlight)
        {
            transform.localScale = originalRootScale * highlightScaleMultiplier;
        }

        transform.localPosition =
            originalRootLocalPosition + Vector3.up * highlightLift;

        ApplyMaterialHighlight(activeVisual, true);
    }

    private void ClearHighlight()
    {
        if (useScaleHighlight)
        {
            transform.localScale = originalRootScale;
        }

        transform.localPosition = originalRootLocalPosition;

        if (highlightedVisual != null)
        {
            ApplyMaterialHighlight(highlightedVisual, false);
        }

        highlightedVisual = null;
        isHighlighted = false;
    }

    private void ApplyMaterialHighlight(GameObject visual, bool highlighted)
    {
        if (visual == null)
            return;

        if (propertyBlock == null)
        {
            propertyBlock = new MaterialPropertyBlock();
        }

        Renderer[] renderers = visual.GetComponentsInChildren<Renderer>(true);

        foreach (Renderer renderer in renderers)
        {
            if (renderer == null)
                continue;

            renderer.GetPropertyBlock(propertyBlock);

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

        ClearHighlight();
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

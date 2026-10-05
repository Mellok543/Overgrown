using System;
using System.Collections;
using UnityEngine;

public class GrassCuttable : MonoBehaviour
{
    [Header("Visuals")]
    [SerializeField] private GameObject[] fullGrassVariants;
    [SerializeField] private GameObject cutGrass;
    [SerializeField] private bool chooseRandomVariant = true;

    [Header("Cut Animation")]
    [SerializeField] private float cutDisappearDuration = 0.22f;
    [SerializeField, Range(0.01f, 1f)] private float cutShrinkY = 0.08f;
    [SerializeField, Range(0.2f, 1f)] private float cutShrinkXZ = 0.75f;
    [SerializeField] private float cutDropDistance = 0.12f;
    [SerializeField] private float cutTiltAngle = 10f;

    [Header("Highlight")]
    [SerializeField] private bool useScaleHighlight = true;
    [SerializeField, Range(1f, 1.3f)] private float highlightScaleMultiplier = 1.12f;
    [SerializeField, Range(0f, 0.15f)] private float highlightLift = 0.04f;
    [SerializeField] private Color highlightColor = new Color(1f, 0.92f, 0.45f, 1f);
    [SerializeField, Range(0f, 3f)] private float highlightIntensity = 1.25f;

    private bool isCut;
    private int activeVariantIndex;
    private bool isHighlighted;
    private Coroutine cutAnimation;

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

        if (cutAnimation != null)
        {
            StopCoroutine(cutAnimation);
            cutAnimation = null;
        }

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
            if (fullGrassVariants[i] == null)
                continue;

            RestoreVisualTransform(fullGrassVariants[i]);
            fullGrassVariants[i].SetActive(i == activeVariantIndex);
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
            ApplyHighlight();
        else
            ClearHighlight();
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
            transform.localScale = originalRootScale * highlightScaleMultiplier;

        transform.localPosition =
            originalRootLocalPosition + Vector3.up * highlightLift;

        ApplyMaterialHighlight(activeVisual, true);
    }

    private void ClearHighlight()
    {
        if (useScaleHighlight)
            transform.localScale = originalRootScale;

        transform.localPosition = originalRootLocalPosition;

        if (highlightedVisual != null)
            ApplyMaterialHighlight(highlightedVisual, false);

        highlightedVisual = null;
        isHighlighted = false;
    }

    private void ApplyMaterialHighlight(GameObject visual, bool highlighted)
    {
        if (visual == null)
            return;

        if (propertyBlock == null)
            propertyBlock = new MaterialPropertyBlock();

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
            return cutGrass;

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

        GameObject activeVisual =
            fullGrassVariants != null &&
            activeVariantIndex >= 0 &&
            activeVariantIndex < fullGrassVariants.Length
                ? fullGrassVariants[activeVariantIndex]
                : null;

        ClearHighlight();
        isCut = true;

        CutStateChanged?.Invoke(this, true);

        if (activeVisual != null && activeVisual.activeSelf)
        {
            cutAnimation = StartCoroutine(AnimateCut(activeVisual));
        }
        else
        {
            FinishCutVisuals();
        }

        return true;
    }

    private IEnumerator AnimateCut(GameObject visual)
    {
        Transform t = visual.transform;

        Vector3 startPosition = t.localPosition;
        Vector3 startScale = t.localScale;
        Quaternion startRotation = t.localRotation;

        Vector3 targetPosition = startPosition + Vector3.down * cutDropDistance;
        Vector3 targetScale = new Vector3(
            startScale.x * cutShrinkXZ,
            startScale.y * cutShrinkY,
            startScale.z * cutShrinkXZ
        );
        Quaternion targetRotation =
            startRotation * Quaternion.Euler(cutTiltAngle, 0f, -cutTiltAngle * 0.45f);

        float duration = Mathf.Max(0.01f, cutDisappearDuration);
        float elapsed = 0f;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t01 = Mathf.Clamp01(elapsed / duration);
            float eased = 1f - Mathf.Pow(1f - t01, 3f);

            t.localPosition = Vector3.Lerp(startPosition, targetPosition, eased);
            t.localScale = Vector3.Lerp(startScale, targetScale, eased);
            t.localRotation = Quaternion.Slerp(startRotation, targetRotation, eased);

            yield return null;
        }

        FinishCutVisuals();
        cutAnimation = null;
    }

    private void FinishCutVisuals()
    {
        if (fullGrassVariants != null)
        {
            foreach (GameObject variant in fullGrassVariants)
            {
                if (variant != null)
                    variant.SetActive(false);
            }
        }

        if (cutGrass != null)
            cutGrass.SetActive(true);
    }

    private void RestoreVisualTransform(GameObject visual)
    {
        if (visual == null)
            return;

        // Grass variants are authored around the same prefab origin.
        // Reset only runtime animation changes.
        Transform t = visual.transform;

        if (t.localScale.x <= 0.0001f ||
            t.localScale.y <= 0.0001f ||
            t.localScale.z <= 0.0001f)
        {
            t.localScale = Vector3.one;
        }
    }

    public void ResetGrass()
    {
        SetupVisuals(true);
    }
}

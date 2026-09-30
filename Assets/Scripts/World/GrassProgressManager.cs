using System;
using UnityEngine;

public class GrassProgressManager : MonoBehaviour
{
    [Header("Prototype UI")]
    [SerializeField] private bool showProgressUI = true;
    [SerializeField] private Vector2 uiPosition = new Vector2(20f, 20f);
    [SerializeField] private Vector2 uiSize = new Vector2(260f, 70f);

    private GrassCuttable[] grassObjects;
    private int totalGrass;
    private int cutGrass;

    public int TotalGrass => totalGrass;
    public int CutGrass => cutGrass;
    public float Progress => totalGrass > 0 ? (float)cutGrass / totalGrass : 0f;

    public event Action<int, int, float> ProgressChanged;

    private void Start()
    {
        RefreshGrassList();
    }

    private void OnDestroy()
    {
        UnsubscribeFromGrass();
    }

    public void RefreshGrassList()
    {
        UnsubscribeFromGrass();

        grassObjects = FindObjectsByType<GrassCuttable>(
            FindObjectsInactive.Include,
            FindObjectsSortMode.None
        );

        totalGrass = grassObjects.Length;
        cutGrass = 0;

        foreach (GrassCuttable grass in grassObjects)
        {
            if (grass == null)
                continue;

            grass.CutStateChanged += HandleGrassStateChanged;

            if (grass.IsCut)
            {
                cutGrass++;
            }
        }

        NotifyProgressChanged();
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
        cutGrass += isCut ? 1 : -1;
        cutGrass = Mathf.Clamp(cutGrass, 0, totalGrass);

        NotifyProgressChanged();
    }

    private void NotifyProgressChanged()
    {
        ProgressChanged?.Invoke(cutGrass, totalGrass, Progress);
    }

    private void OnGUI()
    {
        if (!showProgressUI)
            return;

        Rect panelRect = new Rect(
            uiPosition.x,
            uiPosition.y,
            uiSize.x,
            uiSize.y
        );

        GUI.Box(panelRect, string.Empty);

        Rect labelRect = new Rect(
            panelRect.x + 10f,
            panelRect.y + 8f,
            panelRect.width - 20f,
            22f
        );

        GUI.Label(
            labelRect,
            $"Очищено: {cutGrass} / {totalGrass} ({Progress * 100f:0}%)"
        );

        Rect backgroundRect = new Rect(
            panelRect.x + 10f,
            panelRect.y + 38f,
            panelRect.width - 20f,
            18f
        );

        GUI.Box(backgroundRect, string.Empty);

        Rect fillRect = backgroundRect;
        fillRect.width *= Progress;

        GUI.Box(fillRect, string.Empty);
    }
}

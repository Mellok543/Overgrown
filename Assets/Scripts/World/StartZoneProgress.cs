using System;
using UnityEngine;

public class StartZoneProgress : MonoBehaviour
{
    [Header("Zone")]
    [Tooltip("Root object that contains only the grass belonging to the starting yard.")]
    [SerializeField] private Transform grassRoot;

    [Header("Reward")]
    [SerializeField] private GameObject shearsReward;

    [Header("Prototype UI")]
    [SerializeField] private bool showProgressUI = true;

    private GrassCuttable[] grassObjects;
    private int totalGrass;
    private int cutGrass;
    private bool completed;

    public int TotalGrass => totalGrass;
    public int CutGrass => cutGrass;
    public float Progress => totalGrass > 0 ? (float)cutGrass / totalGrass : 0f;
    public bool Completed => completed;

    public event Action ZoneCompleted;

    private void Start()
    {
        if (shearsReward != null)
        {
            shearsReward.SetActive(false);
        }

        RefreshZone();
    }

    private void OnDestroy()
    {
        Unsubscribe();
    }

    public void RefreshZone()
    {
        Unsubscribe();

        Transform root = grassRoot != null ? grassRoot : transform;

        grassObjects = root.GetComponentsInChildren<GrassCuttable>(true);
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

        CheckCompletion();
    }

    private void Unsubscribe()
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

        CheckCompletion();
    }

    private void CheckCompletion()
    {
        if (completed || totalGrass <= 0 || cutGrass < totalGrass)
            return;

        completed = true;

        if (shearsReward != null)
        {
            shearsReward.SetActive(true);
        }

        ZoneCompleted?.Invoke();
    }

    private void OnGUI()
    {
        if (!showProgressUI || completed)
            return;

        GUI.Label(
            new Rect(20f, 235f, 360f, 25f),
            $"Двор: {cutGrass} / {totalGrass} ({Progress * 100f:0}%)"
        );
    }
}

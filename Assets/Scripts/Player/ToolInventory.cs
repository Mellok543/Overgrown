using UnityEngine;

public class ToolInventory : MonoBehaviour
{
    public enum ToolType
    {
        Hands,
        Sickle,
        Trimmer,
        Mower
    }

    [Header("References")]
    [SerializeField] private HandGrassCollector handGrassCollector;

    [Header("Sickle")]
    [SerializeField] private GameObject sickleObject;
    [SerializeField] private SickleSwing sickleSwing;
    [SerializeField] private GrassCutter grassCutter;

    [Header("Trimmer")]
    [SerializeField] private GameObject trimmerObject;
    [SerializeField] private TrimmerController trimmerController;

    [Header("Input")]
    [SerializeField] private KeyCode handsKey = KeyCode.Alpha1;
    [SerializeField] private KeyCode sickleKey = KeyCode.Alpha2;
    [SerializeField] private KeyCode trimmerKey = KeyCode.Alpha3;

    [Header("Start State")]
    [SerializeField] private bool startWithSickle = false;
    [SerializeField] private bool startWithTrimmer = false;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool hasSickle;
    private bool hasTrimmer;
    private ToolType currentTool = ToolType.Hands;

    public ToolType CurrentTool => currentTool;
    public bool HasSickle => hasSickle;
    public bool HasTrimmer => hasTrimmer;

    private void Awake()
    {
        if (handGrassCollector == null)
        {
            handGrassCollector = GetComponent<HandGrassCollector>();
        }

        if (grassCutter == null)
        {
            grassCutter = GetComponent<GrassCutter>();
        }

        if (sickleSwing == null && sickleObject != null)
        {
            sickleSwing = sickleObject.GetComponent<SickleSwing>();
        }

        if (trimmerController == null && trimmerObject != null)
        {
            trimmerController = trimmerObject.GetComponent<TrimmerController>();
        }

        hasSickle = startWithSickle;
        hasTrimmer = startWithTrimmer;

        SelectHands();
    }

    private void Update()
    {
        if (Input.GetKeyDown(handsKey))
        {
            SelectHands();
        }

        if (hasSickle && Input.GetKeyDown(sickleKey))
        {
            SelectSickle();
        }

        if (hasTrimmer && Input.GetKeyDown(trimmerKey))
        {
            SelectTrimmer();
        }
    }

    public bool IsToolUnlocked(ToolType toolType)
    {
        return toolType switch
        {
            ToolType.Hands => true,
            ToolType.Sickle => hasSickle,
            ToolType.Trimmer => hasTrimmer,
            _ => false
        };
    }

    public void UnlockTool(ToolType toolType)
    {
        switch (toolType)
        {
            case ToolType.Sickle:
                hasSickle = true;
                break;

            case ToolType.Trimmer:
                hasTrimmer = true;
                break;
        }
    }

    public void SelectTool(ToolType toolType)
    {
        if (!IsToolUnlocked(toolType))
            return;

        currentTool = toolType;
        RefreshToolState();
    }

    public void SelectHands()
    {
        currentTool = ToolType.Hands;
        RefreshToolState();
    }

    public void SelectSickle()
    {
        if (!hasSickle)
            return;

        currentTool = ToolType.Sickle;
        RefreshToolState();
    }

    public void SelectTrimmer()
    {
        if (!hasTrimmer)
            return;

        currentTool = ToolType.Trimmer;
        RefreshToolState();
    }

    private void RefreshToolState()
    {
        bool handsActive = currentTool == ToolType.Hands;
        bool sickleActive = currentTool == ToolType.Sickle && hasSickle;
        bool trimmerActive = currentTool == ToolType.Trimmer && hasTrimmer;

        if (handGrassCollector != null)
        {
            handGrassCollector.enabled = handsActive;
        }

        if (grassCutter != null)
        {
            grassCutter.enabled = sickleActive;
        }

        if (sickleSwing != null)
        {
            sickleSwing.enabled = sickleActive;
        }

        if (sickleObject != null)
        {
            sickleObject.SetActive(sickleActive);
        }

        if (trimmerController != null)
        {
            trimmerController.enabled = trimmerActive;
        }

        if (trimmerObject != null)
        {
            trimmerObject.SetActive(trimmerActive);
        }
    }

    private void OnGUI()
    {
        if (!showPrototypeUI)
            return;

        string currentToolText = currentTool switch
        {
            ToolType.Hands => "Руки",
            ToolType.Sickle => "Серп",
            ToolType.Trimmer => "Триммер",
            _ => currentTool.ToString()
        };

        GUI.Label(new Rect(20f, 155f, 300f, 25f), "Инструмент: " + currentToolText);
        GUI.Label(new Rect(20f, 180f, 300f, 25f), "1 — Руки");

        int y = 205;

        if (hasSickle)
        {
            GUI.Label(new Rect(20f, y, 300f, 25f), "2 — Серп");
            y += 25;
        }

        if (hasTrimmer)
        {
            GUI.Label(new Rect(20f, y, 300f, 25f), "3 — Триммер");
        }
    }
}

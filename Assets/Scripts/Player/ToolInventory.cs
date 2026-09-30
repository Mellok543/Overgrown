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
    [SerializeField] private GameObject sickleObject;
    [SerializeField] private SickleSwing sickleSwing;
    [SerializeField] private GrassCutter grassCutter;

    [Header("Input")]
    [SerializeField] private KeyCode handsKey = KeyCode.Alpha1;
    [SerializeField] private KeyCode sickleKey = KeyCode.Alpha2;

    [Header("Start State")]
    [SerializeField] private bool startWithSickle = false;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool hasSickle;
    private ToolType currentTool = ToolType.Hands;

    public ToolType CurrentTool => currentTool;
    public bool HasSickle => hasSickle;

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

        hasSickle = startWithSickle;
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
    }

    public bool IsToolUnlocked(ToolType toolType)
    {
        return toolType switch
        {
            ToolType.Hands => true,
            ToolType.Sickle => hasSickle,
            _ => false
        };
    }

    public void UnlockTool(ToolType toolType)
    {
        if (toolType == ToolType.Sickle)
        {
            hasSickle = true;
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

    private void RefreshToolState()
    {
        bool handsActive = currentTool == ToolType.Hands;
        bool sickleActive = currentTool == ToolType.Sickle && hasSickle;

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
    }

    private void OnGUI()
    {
        if (!showPrototypeUI)
            return;

        string currentToolText = currentTool == ToolType.Hands ? "Руки" : "Серп";

        GUI.Label(new Rect(20f, 155f, 300f, 25f), "Инструмент: " + currentToolText);
        GUI.Label(new Rect(20f, 180f, 300f, 25f), "1 — Руки");

        if (hasSickle)
        {
            GUI.Label(new Rect(20f, 205f, 300f, 25f), "2 — Серп");
        }
    }
}

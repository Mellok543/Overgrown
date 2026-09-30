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

    [Header("Mower")]
    [SerializeField] private GameObject mowerObject;
    [SerializeField] private MowerController mowerController;

    [Header("Input")]
    [SerializeField] private KeyCode handsKey = KeyCode.Alpha1;
    [SerializeField] private KeyCode sickleKey = KeyCode.Alpha2;
    [SerializeField] private KeyCode trimmerKey = KeyCode.Alpha3;
    [SerializeField] private KeyCode mowerKey = KeyCode.Alpha4;

    [Header("Start State")]
    [SerializeField] private bool startWithSickle = false;
    [SerializeField] private bool startWithTrimmer = false;
    [SerializeField] private bool startWithMower = false;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private bool hasSickle;
    private bool hasTrimmer;
    private bool hasMower;
    private ToolType currentTool = ToolType.Hands;

    public ToolType CurrentTool => currentTool;
    public bool HasSickle => hasSickle;
    public bool HasTrimmer => hasTrimmer;
    public bool HasMower => hasMower;

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

        if (mowerController == null && mowerObject != null)
        {
            mowerController = mowerObject.GetComponent<MowerController>();
        }

        hasSickle = startWithSickle;
        hasTrimmer = startWithTrimmer;
        hasMower = startWithMower;

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

        if (hasMower && Input.GetKeyDown(mowerKey))
        {
            SelectMower();
        }
    }

    public bool IsToolUnlocked(ToolType toolType)
    {
        return toolType switch
        {
            ToolType.Hands => true,
            ToolType.Sickle => hasSickle,
            ToolType.Trimmer => hasTrimmer,
            ToolType.Mower => hasMower,
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

            case ToolType.Mower:
                hasMower = true;
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

    public void SelectMower()
    {
        if (!hasMower)
            return;

        currentTool = ToolType.Mower;
        RefreshToolState();
    }

    private void RefreshToolState()
    {
        bool handsActive = currentTool == ToolType.Hands;
        bool sickleActive = currentTool == ToolType.Sickle && hasSickle;
        bool trimmerActive = currentTool == ToolType.Trimmer && hasTrimmer;
        bool mowerActive = currentTool == ToolType.Mower && hasMower;

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

        if (mowerController != null)
        {
            mowerController.enabled = mowerActive;
        }

        if (mowerObject != null)
        {
            mowerObject.SetActive(mowerActive);
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
            ToolType.Mower => "Газонокосилка",
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
            y += 25;
        }

        if (hasMower)
        {
            GUI.Label(new Rect(20f, y, 300f, 25f), "4 — Газонокосилка");
        }
    }
}

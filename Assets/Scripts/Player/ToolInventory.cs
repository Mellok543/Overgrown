using UnityEngine;

public class ToolInventory : MonoBehaviour
{
    public enum ToolType
    {
        Hands,
        Sickle,
        Trimmer,
        Mower,
        GardenShears
    }

    [Header("References")]
    [SerializeField] private HandGrassCollector handGrassCollector;
    [SerializeField] private PlayerItemInventory playerItems;

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

    [Header("First Person Animation")]
    [SerializeField] private Animator armsAnimator;
    [SerializeField] private RuntimeAnimatorController sickleArmsController;
    [SerializeField] private RuntimeAnimatorController trimmerArmsController;
    [SerializeField] private RuntimeAnimatorController mowerArmsController;
    [SerializeField] private FPToolGroundFollow groundFollow;
    [SerializeField] private Transform trimmerGroundPoint;
    [SerializeField] private Transform mowerGroundPoint;

    [Header("Input")]
    [SerializeField] private KeyCode handsKey = KeyCode.Alpha1;
    [SerializeField] private KeyCode sickleKey = KeyCode.Alpha2;
    [SerializeField] private KeyCode trimmerKey = KeyCode.Alpha3;
    [SerializeField] private KeyCode mowerKey = KeyCode.Alpha4;
    [SerializeField] private KeyCode gardenShearsKey = KeyCode.Alpha5;

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
            handGrassCollector = GetComponent<HandGrassCollector>();

        if (playerItems == null)
            playerItems = GetComponent<PlayerItemInventory>();

        if (grassCutter == null)
            grassCutter = GetComponent<GrassCutter>();

        if (sickleSwing == null && sickleObject != null)
            sickleSwing = sickleObject.GetComponent<SickleSwing>();

        if (trimmerController == null && trimmerObject != null)
            trimmerController = trimmerObject.GetComponent<TrimmerController>();

        if (mowerController == null && mowerObject != null)
            mowerController = mowerObject.GetComponent<MowerController>();

        hasSickle = startWithSickle;
        hasTrimmer = startWithTrimmer;
        hasMower = startWithMower;

        SelectHands();
    }

    private void Update()
    {
        if (Input.GetKeyDown(handsKey))
            SelectHands();

        if (hasSickle && Input.GetKeyDown(sickleKey))
            SelectSickle();

        if (hasTrimmer && Input.GetKeyDown(trimmerKey))
            SelectTrimmer();

        if (hasMower && Input.GetKeyDown(mowerKey))
            SelectMower();

        if (playerItems != null &&
            playerItems.HasGardenShears &&
            Input.GetKeyDown(gardenShearsKey))
        {
            SelectGardenShears();
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
            ToolType.GardenShears => playerItems != null && playerItems.HasGardenShears,
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

    public void SelectGardenShears()
    {
        if (playerItems == null || !playerItems.HasGardenShears)
            return;

        currentTool = ToolType.GardenShears;
        RefreshToolState();
    }

    private void RefreshToolState()
    {
        bool handsActive = currentTool == ToolType.Hands;
        bool sickleActive = currentTool == ToolType.Sickle && hasSickle;
        bool trimmerActive = currentTool == ToolType.Trimmer && hasTrimmer;
        bool mowerActive = currentTool == ToolType.Mower && hasMower;
        bool shearsActive =
            currentTool == ToolType.GardenShears &&
            playerItems != null &&
            playerItems.HasGardenShears;

        if (handGrassCollector != null)
            handGrassCollector.enabled = handsActive;

        if (grassCutter != null)
            grassCutter.enabled = sickleActive;

        if (sickleSwing != null)
            sickleSwing.enabled = sickleActive;

        if (sickleObject != null)
            sickleObject.SetActive(sickleActive);

        if (trimmerController != null)
            trimmerController.enabled = trimmerActive;

        if (trimmerObject != null)
            trimmerObject.SetActive(trimmerActive);

        if (mowerController != null)
            mowerController.enabled = mowerActive;

        if (mowerObject != null)
            mowerObject.SetActive(mowerActive);

        // shears first: unequipping them resets the arms; the tool controller is applied afterwards
        if (playerItems != null)
            playerItems.SetGardenShearsEquipped(shearsActive);

        ApplyArmsAnimation(sickleActive, trimmerActive, mowerActive);
    }

    private void ApplyArmsAnimation(bool sickleActive, bool trimmerActive, bool mowerActive)
    {
        RuntimeAnimatorController controller =
            sickleActive ? sickleArmsController :
            trimmerActive ? trimmerArmsController :
            mowerActive ? mowerArmsController : null;

        if (armsAnimator != null && controller != null)
        {
            // fresh controller + Rebind: no pose of the previous tool survives, the new Idle applies at once
            armsAnimator.runtimeAnimatorController = controller;
            armsAnimator.enabled = true;
            armsAnimator.Rebind();
            armsAnimator.Update(0f);
        }

        if (groundFollow != null)
        {
            if (mowerActive)
                groundFollow.SetMode(FPToolGroundFollow.Mode.Level, mowerGroundPoint);
            else if (trimmerActive)
                groundFollow.SetMode(FPToolGroundFollow.Mode.Lift, trimmerGroundPoint);
            else
                groundFollow.SetMode(FPToolGroundFollow.Mode.Off, null);
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
            ToolType.GardenShears => "Секатор",
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
            y += 25;
        }

        if (playerItems != null && playerItems.HasGardenShears)
        {
            GUI.Label(new Rect(20f, y, 300f, 25f), "5 — Секатор");
        }
    }
}

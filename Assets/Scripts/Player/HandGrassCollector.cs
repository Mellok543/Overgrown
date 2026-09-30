using UnityEngine;

public class HandGrassCollector : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private GrassInventory inventory;

    [Header("Collection")]
    [SerializeField] private LayerMask grassLayer;
    [SerializeField] private float collectDistance = 2f;
    [SerializeField] private float collectDuration = 0.6f;
    [SerializeField] private KeyCode collectKey = KeyCode.E;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private GrassCuttable currentTarget;
    private float collectProgress;

    private void Awake()
    {
        if (playerCamera == null)
        {
            playerCamera = GetComponentInChildren<Camera>();
        }

        if (inventory == null)
        {
            inventory = GetComponent<GrassInventory>();
        }
    }

    private void Update()
    {
        GrassCuttable target = FindTarget();

        if (target != currentTarget)
        {
            currentTarget = target;
            collectProgress = 0f;
        }

        if (currentTarget == null || currentTarget.IsCut)
        {
            collectProgress = 0f;
            return;
        }

        if (inventory == null || inventory.IsFull)
        {
            collectProgress = 0f;
            return;
        }

        if (Input.GetKey(collectKey))
        {
            collectProgress += Time.deltaTime;

            if (collectProgress >= collectDuration)
            {
                CollectCurrentTarget();
                collectProgress = 0f;
            }
        }
        else
        {
            collectProgress = 0f;
        }
    }

    private GrassCuttable FindTarget()
    {
        if (playerCamera == null)
            return null;

        Ray ray = new Ray(
            playerCamera.transform.position,
            playerCamera.transform.forward
        );

        if (!Physics.Raycast(
                ray,
                out RaycastHit hit,
                collectDistance,
                grassLayer,
                QueryTriggerInteraction.Collide))
        {
            return null;
        }

        GrassCuttable grass = hit.collider.GetComponentInParent<GrassCuttable>();

        if (grass == null || grass.IsCut)
            return null;

        return grass;
    }

    private void CollectCurrentTarget()
    {
        if (currentTarget == null || inventory == null || inventory.IsFull)
            return;

        if (inventory.TryAddBundles(1) == 0)
            return;

        if (!currentTarget.Cut())
        {
            inventory.RemoveBundles(1);
        }
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || currentTarget == null)
            return;

        string text;

        if (inventory == null)
        {
            text = "Нет GrassInventory";
        }
        else if (inventory.IsFull)
        {
            text = "Переноска заполнена — отнеси траву на продажу";
        }
        else if (Input.GetKey(collectKey))
        {
            float percent = collectDuration > 0f
                ? Mathf.Clamp01(collectProgress / collectDuration) * 100f
                : 100f;

            text = "Собираем... " + percent.ToString("0") + "%";
        }
        else
        {
            text = "Удерживай " + collectKey + ", чтобы собрать траву";
        }

        GUI.Label(
            new Rect(Screen.width * 0.5f - 170f, Screen.height - 90f, 340f, 30f),
            text
        );
    }
}

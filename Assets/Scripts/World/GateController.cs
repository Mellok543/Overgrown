using UnityEngine;

public class GateController : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Transform gate;
    [SerializeField] private Camera playerCamera;

    [Header("Interaction")]
    [SerializeField] private float interactDistance = 2.5f;
    [SerializeField] private KeyCode interactKey = KeyCode.E;

    [Header("Gate")]
    [SerializeField] private float openAngle = 90f;
    [SerializeField] private float openSpeed = 180f;

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private Quaternion closedRotation;
    private Quaternion openRotation;
    private bool isOpen;
    private bool isLookedAt;

    private void Awake()
    {
        if (playerCamera == null)
        {
            playerCamera = Camera.main;
        }

        if (gate == null)
        {
            gate = transform;
        }

        closedRotation = gate.localRotation;
        openRotation = closedRotation * Quaternion.Euler(0f, openAngle, 0f);
    }

    private void Update()
    {
        isLookedAt = IsPlayerLookingAtGate();

        if (isLookedAt && Input.GetKeyDown(interactKey))
        {
            isOpen = !isOpen;
        }

        Quaternion targetRotation = isOpen ? openRotation : closedRotation;

        gate.localRotation = Quaternion.RotateTowards(
            gate.localRotation,
            targetRotation,
            openSpeed * Time.deltaTime
        );
    }

    private bool IsPlayerLookingAtGate()
    {
        if (playerCamera == null)
            return false;

        Ray ray = new Ray(
            playerCamera.transform.position,
            playerCamera.transform.forward
        );

        if (!Physics.Raycast(
                ray,
                out RaycastHit hit,
                interactDistance,
                ~0,
                QueryTriggerInteraction.Ignore))
        {
            return false;
        }

        return hit.collider.GetComponentInParent<GateController>() == this;
    }

    private void OnGUI()
    {
        if (!showPrototypeUI || !isLookedAt)
            return;

        string action = isOpen ? "закрыть" : "открыть";

        GUI.Label(
            new Rect(Screen.width * 0.5f - 170f, Screen.height - 55f, 340f, 30f),
            "Нажми " + interactKey + ", чтобы " + action + " калитку"
        );
    }
}

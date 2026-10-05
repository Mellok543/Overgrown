using UnityEngine;

// Visual-only ground handling for the first-person arms (no physics, no gameplay effect).
// Lives on the Player_Arms_FP root (child of the camera) and runs after the Animator (LateUpdate).
//   Off   : arms stay at their authored local pose under the camera (hands, sickle, shears).
//   Lift  : camera-locked viewmodel (trimmer); if the ground point would dip below the ground,
//           the whole viewmodel is lifted so the head never goes through it.
//   Level : the arms ignore camera pitch (yaw only) and the ground point is snapped onto the
//           ground (mower): the deck stays on the surface whatever the vertical look angle.
public class FPToolGroundFollow : MonoBehaviour
{
    public enum Mode
    {
        Off,
        Lift,
        Level
    }

    [SerializeField] private Transform cameraTransform;
    [SerializeField] private LayerMask groundMask = ~((1 << 2) | (1 << 3));   // not Ignore Raycast, not Grass
    [SerializeField] private float probeHeight = 1.0f;
    [SerializeField] private float maxCorrection = 0.6f;
    [SerializeField] private float clearance = 0.02f;
    [SerializeField] private float smoothing = 18f;
    [Tooltip("Arms root relative to the camera (yaw space) while in Level mode.")]
    [SerializeField] private Vector3 levelLocalOffset = new Vector3(0f, 0f, -0.15f);

    private Mode mode = Mode.Off;
    private Transform groundPoint;
    private Vector3 defaultLocalPosition;
    private Quaternion defaultLocalRotation;
    private float currentLift;
    private bool cached;

    public Mode CurrentMode => mode;
    public float CurrentLift => currentLift;

    private void Awake()
    {
        Cache();
    }

    private void Cache()
    {
        if (cached)
            return;

        if (cameraTransform == null)
            cameraTransform = transform.parent;

        defaultLocalPosition = transform.localPosition;
        defaultLocalRotation = transform.localRotation;
        cached = true;
    }

    public void SetMode(Mode newMode, Transform newGroundPoint)
    {
        Cache();
        mode = newGroundPoint != null ? newMode : Mode.Off;
        groundPoint = newGroundPoint;
        currentLift = 0f;

        if (mode == Mode.Off)
        {
            transform.localPosition = defaultLocalPosition;
            transform.localRotation = defaultLocalRotation;
        }
    }

    private void LateUpdate()
    {
        if (mode == Mode.Off || cameraTransform == null)
            return;

        if (mode == Mode.Level)
        {
            Vector3 forward = Vector3.ProjectOnPlane(cameraTransform.forward, Vector3.up);
            if (forward.sqrMagnitude < 1e-6f)
                forward = Vector3.ProjectOnPlane(cameraTransform.up, Vector3.up);

            Quaternion yaw = Quaternion.LookRotation(forward.normalized, Vector3.up);
            transform.SetPositionAndRotation(cameraTransform.position + yaw * levelLocalOffset, yaw);
        }
        else
        {
            transform.localPosition = defaultLocalPosition;
            transform.localRotation = defaultLocalRotation;
        }

        if (groundPoint == null)
            return;

        Vector3 point = groundPoint.position;
        float target = 0f;
        if (Physics.Raycast(point + Vector3.up * probeHeight, Vector3.down, out RaycastHit hit,
                probeHeight + maxCorrection + 2f, groundMask, QueryTriggerInteraction.Ignore))
        {
            float delta = hit.point.y + clearance - point.y;          // > 0: the point is below the ground
            target = mode == Mode.Level
                ? Mathf.Clamp(delta, -maxCorrection, maxCorrection)   // keep the wheels on the surface
                : Mathf.Clamp(delta, 0f, maxCorrection);              // only ever lift the trimmer head
        }

        currentLift = Mathf.Lerp(currentLift, target, 1f - Mathf.Exp(-smoothing * Time.deltaTime));
        transform.position += Vector3.up * currentLift;
    }
}

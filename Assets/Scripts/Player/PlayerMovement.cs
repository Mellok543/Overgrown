using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class PlayerMovement : MonoBehaviour
{
    [Header("Movement")]
    [SerializeField] private float walkSpeed = 5f;
    [SerializeField] private float runSpeed = 8f;
    [SerializeField] private float crouchSpeed = 2.5f;

    [Header("Jump & Gravity")]
    [SerializeField] private float jumpHeight = 1.5f;
    [SerializeField] private float gravity = -20f;

    [Header("Crouch")]
    [SerializeField] private Transform cameraTransform;

    [SerializeField] private float standingHeight = 2f;
    [SerializeField] private float crouchingHeight = 1f;

    [SerializeField] private float standingCameraHeight = 0.7f;
    [SerializeField] private float crouchingCameraHeight = 0.2f;

    [SerializeField] private float crouchTransitionSpeed = 8f;

    [Header("Head Bob")]
    [SerializeField] private bool enableHeadBob = true;

    [SerializeField] private float walkBobSpeed = 10f;
    [SerializeField] private float walkBobAmount = 0.035f;

    [SerializeField] private float runBobSpeed = 14f;
    [SerializeField] private float runBobAmount = 0.06f;

    [SerializeField] private float crouchBobSpeed = 7f;
    [SerializeField] private float crouchBobAmount = 0.02f;

    private CharacterController controller;

    private Vector3 verticalVelocity;
    private Vector3 standingCenter;

    private bool isCrouching;
    private bool isRunning;

    private float currentCameraHeight;
    private float bobTimer;
    private float currentBobOffset;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();

        standingCenter = controller.center;
        currentCameraHeight = standingCameraHeight;

        if (cameraTransform == null)
        {
            Camera childCamera = GetComponentInChildren<Camera>();

            if (childCamera != null)
            {
                cameraTransform = childCamera.transform;
            }
        }
    }

    private void Update()
    {
        HandleCrouch();
        HandleMovement();
        HandleHeadBob();
    }

    private void HandleMovement()
    {
        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");

        Vector3 direction =
            transform.right * horizontal +
            transform.forward * vertical;

        direction = direction.normalized;

        isRunning =
            Input.GetKey(KeyCode.LeftShift) &&
            !isCrouching &&
            direction.sqrMagnitude > 0.01f;

        float currentSpeed = walkSpeed;

        if (isCrouching)
        {
            currentSpeed = crouchSpeed;
        }
        else if (isRunning)
        {
            currentSpeed = runSpeed;
        }

        if (controller.isGrounded && verticalVelocity.y < 0f)
        {
            verticalVelocity.y = -2f;
        }

        if (
            Input.GetKeyDown(KeyCode.Space) &&
            controller.isGrounded &&
            !isCrouching
        )
        {
            verticalVelocity.y =
                Mathf.Sqrt(jumpHeight * -2f * gravity);
        }

        verticalVelocity.y += gravity * Time.deltaTime;

        Vector3 movement =
            direction * currentSpeed +
            verticalVelocity;

        controller.Move(movement * Time.deltaTime);
    }

    private void HandleCrouch()
    {
        isCrouching = Input.GetKey(KeyCode.LeftControl);

        float targetHeight;
        float targetCameraHeight;
        Vector3 targetCenter;

        if (isCrouching)
        {
            targetHeight = crouchingHeight;
            targetCameraHeight = crouchingCameraHeight;

            targetCenter =
                standingCenter +
                Vector3.down *
                ((standingHeight - crouchingHeight) / 2f);
        }
        else
        {
            targetHeight = standingHeight;
            targetCameraHeight = standingCameraHeight;
            targetCenter = standingCenter;
        }

        controller.height = Mathf.Lerp(
            controller.height,
            targetHeight,
            crouchTransitionSpeed * Time.deltaTime
        );

        controller.center = Vector3.Lerp(
            controller.center,
            targetCenter,
            crouchTransitionSpeed * Time.deltaTime
        );

        currentCameraHeight = Mathf.Lerp(
            currentCameraHeight,
            targetCameraHeight,
            crouchTransitionSpeed * Time.deltaTime
        );
    }

    private void HandleHeadBob()
    {
        if (cameraTransform == null)
        {
            return;
        }

        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");

        bool isMoving =
            Mathf.Abs(horizontal) > 0.1f ||
            Mathf.Abs(vertical) > 0.1f;

        float targetBobOffset = 0f;

        if (
            enableHeadBob &&
            isMoving &&
            controller.isGrounded
        )
        {
            float bobSpeed;
            float bobAmount;

            if (isCrouching)
            {
                bobSpeed = crouchBobSpeed;
                bobAmount = crouchBobAmount;
            }
            else if (isRunning)
            {
                bobSpeed = runBobSpeed;
                bobAmount = runBobAmount;
            }
            else
            {
                bobSpeed = walkBobSpeed;
                bobAmount = walkBobAmount;
            }

            bobTimer += Time.deltaTime * bobSpeed;

            targetBobOffset =
                Mathf.Sin(bobTimer) * bobAmount;
        }
        else
        {
            bobTimer = 0f;
        }

        currentBobOffset = Mathf.Lerp(
            currentBobOffset,
            targetBobOffset,
            10f * Time.deltaTime
        );

        Vector3 cameraPosition =
            cameraTransform.localPosition;

        cameraPosition.y =
            currentCameraHeight + currentBobOffset;

        cameraTransform.localPosition =
            cameraPosition;
    }
}
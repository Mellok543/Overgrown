using UnityEngine;

public class PlayerLook : MonoBehaviour
{
    [Header("Mouse Look")]
    [SerializeField] private Transform playerBody;
    [SerializeField] private float sensitivity = 2f;

    [SerializeField] private float minVerticalAngle = -85f;
    [SerializeField] private float maxVerticalAngle = 85f;

    private float verticalRotation;

    private void Start()
    {
        if (playerBody == null)
        {
            playerBody = transform.parent;
        }

        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    private void Update()
    {
        float mouseX =
            Input.GetAxisRaw("Mouse X") * sensitivity;

        float mouseY =
            Input.GetAxisRaw("Mouse Y") * sensitivity;

        verticalRotation -= mouseY;

        verticalRotation = Mathf.Clamp(
            verticalRotation,
            minVerticalAngle,
            maxVerticalAngle
        );

        transform.localRotation =
            Quaternion.Euler(
                verticalRotation,
                0f,
                0f
            );

        if (playerBody != null)
        {
            playerBody.Rotate(
                Vector3.up * mouseX
            );
        }

        if (Input.GetKeyDown(KeyCode.Escape))
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        if (Input.GetMouseButtonDown(0))
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }
    }
}
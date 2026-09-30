using System.Collections;
using UnityEngine;

public class SickleSwing : MonoBehaviour
{
    [Header("Audio")]
    [SerializeField] private AudioSource audioSource;
    [SerializeField] private AudioClip swingSound;
    [SerializeField] private AudioClip cutSound;

    [Header("References")]
    [SerializeField] private GrassCutter grassCutter;

    [Header("Swing Rotation")]
    [SerializeField] private float swingAngle = 70f;

    [Header("Swing Movement")]
    [SerializeField] private float forwardDistance = 0.15f;
    [SerializeField] private float downDistance = 0.05f;

    [Header("Timing")]
    [SerializeField] private float swingDuration = 0.12f;
    [SerializeField] private float returnDuration = 0.18f;
    [SerializeField] private float cooldown = 0.35f;

    private Quaternion startRotation;
    private Vector3 startPosition;

    private bool isSwinging;
    private float nextSwingTime;

    public float Cooldown => cooldown;

    private void Awake()
    {
        startRotation = transform.localRotation;
        startPosition = transform.localPosition;

        if (audioSource == null)
        {
            audioSource = GetComponent<AudioSource>();
        }

        if (grassCutter == null)
        {
            grassCutter = GetComponentInParent<GrassCutter>();
        }
    }

    private void Update()
    {
        if (
            Input.GetMouseButtonDown(0) &&
            !isSwinging &&
            Time.time >= nextSwingTime
        )
        {
            StartCoroutine(Swing());
        }
    }

    public void ReduceCooldown(float amount, float minimumCooldown = 0.12f)
    {
        cooldown = Mathf.Max(minimumCooldown, cooldown - amount);
    }

    private IEnumerator Swing()
    {
        isSwinging = true;

        if (audioSource != null && swingSound != null)
        {
            audioSource.PlayOneShot(swingSound);
        }

        nextSwingTime = Time.time + cooldown;

        Quaternion targetRotation =
            startRotation *
            Quaternion.Euler(0f, swingAngle, 0f);

        Vector3 targetPosition =
            startPosition +
            Vector3.forward * forwardDistance +
            Vector3.down * downDistance;

        float time = 0f;

        while (time < swingDuration)
        {
            time += Time.deltaTime;

            float progress =
                Mathf.Clamp01(time / swingDuration);

            float smoothProgress =
                Mathf.SmoothStep(0f, 1f, progress);

            transform.localRotation =
                Quaternion.Slerp(
                    startRotation,
                    targetRotation,
                    smoothProgress
                );

            transform.localPosition =
                Vector3.Lerp(
                    startPosition,
                    targetPosition,
                    smoothProgress
                );

            yield return null;
        }

        if (grassCutter != null)
        {
            grassCutter.CutGrass();

            if (audioSource != null && cutSound != null)
            {
                audioSource.PlayOneShot(cutSound);
            }
        }

        time = 0f;

        while (time < returnDuration)
        {
            time += Time.deltaTime;

            float progress =
                Mathf.Clamp01(time / returnDuration);

            float smoothProgress =
                Mathf.SmoothStep(0f, 1f, progress);

            transform.localRotation =
                Quaternion.Slerp(
                    targetRotation,
                    startRotation,
                    smoothProgress
                );

            transform.localPosition =
                Vector3.Lerp(
                    targetPosition,
                    startPosition,
                    smoothProgress
                );

            yield return null;
        }

        transform.localRotation = startRotation;
        transform.localPosition = startPosition;

        isSwinging = false;
    }
}

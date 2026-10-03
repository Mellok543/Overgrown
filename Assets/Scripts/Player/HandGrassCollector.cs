using System.Collections.Generic;
using UnityEngine;

public class HandGrassCollector : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private GrassInventory inventory;

    [Header("Hand Animation")]
    [SerializeField] private Transform handTransform;
    [SerializeField] private Vector3 handCollectOffset = new Vector3(0f, -0.12f, 0.18f);
    [SerializeField] private Vector3 handCollectEuler = new Vector3(18f, 0f, -10f);
    [SerializeField] private float handAnimationSpeed = 12f;

    [Header("Collection")]
    [SerializeField] private LayerMask grassLayer;
    [SerializeField] private float interactDistance = 2f;
    [SerializeField] private float collectDuration = 0.6f;
    [SerializeField] private int bundlesPerCollect = 1;
    [SerializeField] private float collectRadius = 0.75f;
    [SerializeField] private KeyCode collectKey = KeyCode.E;

    [Header("Limits")]
    [SerializeField] private float minimumCollectDuration = 0.15f;
    [SerializeField] private int maximumBundlesPerCollect = 5;
    [SerializeField] private float maximumCollectRadius = 3.5f;

    [Header("Crosshair")]
    [SerializeField] private bool showCrosshair = true;
    [SerializeField] private float crosshairSize = 7f;
    [SerializeField] private float crosshairThickness = 2f;
    [SerializeField] private float crosshairGap = 4f;
    [SerializeField] private Color crosshairColor = Color.white;
    [SerializeField] private Color targetCrosshairColor = new Color(1f, 0.9f, 0.25f, 1f);

    [Header("Prototype UI")]
    [SerializeField] private bool showPrototypeUI = true;

    private GrassCuttable currentTarget;
    private Collider currentTargetCollider;
    private float collectProgress;

    private Vector3 handStartLocalPosition;
    private Quaternion handStartLocalRotation;
    private bool handPoseCached;

    public float CollectDuration => collectDuration;
    public int BundlesPerCollect => bundlesPerCollect;
    public float CollectRadius => collectRadius;

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

        CacheHandPose();
    }

    private void OnDisable()
    {
        if (currentTarget != null)
        {
            currentTarget.SetHighlighted(false);
        }

        currentTarget = null;
        currentTargetCollider = null;
        collectProgress = 0f;

        ResetHandImmediate();
    }

    private void Update()
    {
        GrassCuttable target = FindTarget(out Collider targetCollider);

        if (target != currentTarget)
        {
            if (currentTarget != null)
            {
                currentTarget.SetHighlighted(false);
            }

            currentTarget = target;
            currentTargetCollider = targetCollider;
            collectProgress = 0f;

            if (currentTarget != null)
            {
                currentTarget.SetHighlighted(true);
            }
        }
        else if (target != null)
        {
            currentTargetCollider = targetCollider;

            // Re-apply every frame so hover feedback survives visual/material changes.
            currentTarget.SetHighlighted(true);
        }

        bool canCollect =
            currentTarget != null &&
            !currentTarget.IsCut &&
            inventory != null &&
            !inventory.IsFull;

        if (!canCollect)
        {
            collectProgress = 0f;
            AnimateHand(false);
            return;
        }

        bool collecting = Input.GetKey(collectKey);

        if (collecting)
        {
            collectProgress += Time.deltaTime;

            if (collectProgress >= collectDuration)
            {
                CollectGrass();
                collectProgress = 0f;
            }
        }
        else
        {
            collectProgress = 0f;
        }

        AnimateHand(collecting);
    }

    private void CacheHandPose()
    {
        if (handTransform == null)
            return;

        handStartLocalPosition = handTransform.localPosition;
        handStartLocalRotation = handTransform.localRotation;
        handPoseCached = true;
    }

    private void AnimateHand(bool collecting)
    {
        if (handTransform == null)
            return;

        if (!handPoseCached)
        {
            CacheHandPose();
        }

        Vector3 targetPosition = handStartLocalPosition;
        Quaternion targetRotation = handStartLocalRotation;

        if (collecting)
        {
            float duration = Mathf.Max(0.01f, collectDuration);
            float t = Mathf.Clamp01(collectProgress / duration);

            // Reach forward, then pull back slightly near the end.
            float reach = Mathf.Sin(t * Mathf.PI);

            targetPosition =
                handStartLocalPosition +
                handCollectOffset * reach;

            targetRotation =
                handStartLocalRotation *
                Quaternion.Euler(handCollectEuler * reach);
        }

        float lerp = 1f - Mathf.Exp(-handAnimationSpeed * Time.deltaTime);

        handTransform.localPosition = Vector3.Lerp(
            handTransform.localPosition,
            targetPosition,
            lerp
        );

        handTransform.localRotation = Quaternion.Slerp(
            handTransform.localRotation,
            targetRotation,
            lerp
        );
    }

    private void ResetHandImmediate()
    {
        if (handTransform == null || !handPoseCached)
            return;

        handTransform.localPosition = handStartLocalPosition;
        handTransform.localRotation = handStartLocalRotation;
    }

    private GrassCuttable FindTarget(out Collider targetCollider)
    {
        targetCollider = null;

        if (playerCamera == null)
            return null;

        Ray ray = new Ray(
            playerCamera.transform.position,
            playerCamera.transform.forward
        );

        if (!Physics.Raycast(
                ray,
                out RaycastHit hit,
                interactDistance,
                grassLayer,
                QueryTriggerInteraction.Collide))
        {
            return null;
        }

        GrassCuttable grass = hit.collider.GetComponentInParent<GrassCuttable>();

        if (grass == null || grass.IsCut)
            return null;

        targetCollider = hit.collider;
        return grass;
    }

    private void CollectGrass()
    {
        if (currentTarget == null || inventory == null || inventory.IsFull)
            return;

        int freeSpace = inventory.Capacity - inventory.Bundles;
        int wantedCount = Mathf.Min(bundlesPerCollect, freeSpace);

        if (wantedCount <= 0)
            return;

        List<GrassCuttable> targets = FindGrassInRadius(wantedCount);

        foreach (GrassCuttable grass in targets)
        {
            if (inventory.IsFull)
                break;

            if (inventory.TryAddBundles(1) == 0)
                break;

            if (!grass.Cut())
            {
                inventory.RemoveBundles(1);
            }
        }
    }

    private List<GrassCuttable> FindGrassInRadius(int maxCount)
    {
        List<GrassCuttable> result = new List<GrassCuttable>();
        HashSet<GrassCuttable> unique = new HashSet<GrassCuttable>();

        if (currentTarget == null || currentTarget.IsCut)
            return result;

        Vector3 center = currentTargetCollider != null
            ? currentTargetCollider.bounds.center
            : currentTarget.transform.position;

        result.Add(currentTarget);
        unique.Add(currentTarget);

        if (result.Count >= maxCount)
            return result;

        Collider[] hits = Physics.OverlapSphere(
            center,
            collectRadius,
            grassLayer,
            QueryTriggerInteraction.Collide
        );

        List<GrassCuttable> nearby = new List<GrassCuttable>();

        foreach (Collider hit in hits)
        {
            GrassCuttable grass = hit.GetComponentInParent<GrassCuttable>();

            if (grass == null || grass.IsCut || unique.Contains(grass))
                continue;

            unique.Add(grass);
            nearby.Add(grass);
        }

        nearby.Sort((a, b) =>
        {
            float distanceA = (a.transform.position - center).sqrMagnitude;
            float distanceB = (b.transform.position - center).sqrMagnitude;
            return distanceA.CompareTo(distanceB);
        });

        foreach (GrassCuttable grass in nearby)
        {
            result.Add(grass);

            if (result.Count >= maxCount)
                break;
        }

        return result;
    }

    public void SetCollectDuration(float value)
    {
        collectDuration = Mathf.Max(minimumCollectDuration, value);
    }

    public void SetBundlesPerCollect(int value)
    {
        bundlesPerCollect = Mathf.Clamp(value, 1, maximumBundlesPerCollect);
    }

    public void SetCollectRadius(float value)
    {
        collectRadius = Mathf.Clamp(value, 0.1f, maximumCollectRadius);
    }

    private void OnGUI()
    {
        DrawCrosshair();

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
            text =
                "Удерживай " + collectKey +
                " — до " + bundlesPerCollect +
                " пучк., радиус " + collectRadius.ToString("0.00") + " м";
        }

        GUI.Label(
            new Rect(Screen.width * 0.5f - 230f, Screen.height - 90f, 460f, 30f),
            text
        );
    }

    private void DrawCrosshair()
    {
        if (!showCrosshair)
            return;

        Color previousColor = GUI.color;
        GUI.color = currentTarget != null ? targetCrosshairColor : crosshairColor;

        float centerX = Screen.width * 0.5f;
        float centerY = Screen.height * 0.5f;

        Texture2D pixel = Texture2D.whiteTexture;

        GUI.DrawTexture(
            new Rect(
                centerX - crosshairGap - crosshairSize,
                centerY - crosshairThickness * 0.5f,
                crosshairSize,
                crosshairThickness
            ),
            pixel
        );

        GUI.DrawTexture(
            new Rect(
                centerX + crosshairGap,
                centerY - crosshairThickness * 0.5f,
                crosshairSize,
                crosshairThickness
            ),
            pixel
        );

        GUI.DrawTexture(
            new Rect(
                centerX - crosshairThickness * 0.5f,
                centerY - crosshairGap - crosshairSize,
                crosshairThickness,
                crosshairSize
            ),
            pixel
        );

        GUI.DrawTexture(
            new Rect(
                centerX - crosshairThickness * 0.5f,
                centerY + crosshairGap,
                crosshairThickness,
                crosshairSize
            ),
            pixel
        );

        GUI.color = previousColor;
    }
}

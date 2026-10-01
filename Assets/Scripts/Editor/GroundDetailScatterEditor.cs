#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(GroundDetailScatter))]
public class GroundDetailScatterEditor : Editor
{
    private const string GeneratedRootName = "Generated Ground Details";

    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();

        GroundDetailScatter scatter = (GroundDetailScatter)target;

        EditorGUILayout.Space();

        if (GUILayout.Button("Generate Details"))
        {
            GenerateDetails(scatter);
        }

        if (GUILayout.Button("Clear Generated Details"))
        {
            ClearDetails(scatter);
        }
    }

    private static void GenerateDetails(GroundDetailScatter scatter)
    {
        if (scatter.DetailPrefabs == null || scatter.DetailPrefabs.Count == 0)
        {
            Debug.LogWarning("GroundDetailScatter: add at least one detail prefab.", scatter);
            return;
        }

        BoxCollider boundsCollider = scatter.AreaBounds != null
            ? scatter.AreaBounds
            : scatter.GetComponent<BoxCollider>();

        if (boundsCollider == null)
        {
            Debug.LogWarning("GroundDetailScatter: BoxCollider bounds are required.", scatter);
            return;
        }

        boundsCollider.isTrigger = true;

        ClearDetails(scatter);

        GameObject root = new GameObject(GeneratedRootName);
        Undo.RegisterCreatedObjectUndo(root, "Create generated ground details root");
        root.transform.SetParent(scatter.transform);
        root.transform.localPosition = Vector3.zero;
        root.transform.localRotation = Quaternion.identity;
        root.transform.localScale = Vector3.one;

        List<Vector3> placedPoints = new();

        int placed = 0;
        int attempts = 0;
        int maxAttempts = Mathf.Max(scatter.DetailCount, scatter.MaxPlacementAttempts);

        while (placed < scatter.DetailCount && attempts < maxAttempts)
        {
            attempts++;

            Vector3 localPoint = boundsCollider.center + new Vector3(
                Random.Range(-boundsCollider.size.x * 0.5f, boundsCollider.size.x * 0.5f),
                0f,
                Random.Range(-boundsCollider.size.z * 0.5f, boundsCollider.size.z * 0.5f)
            );

            Vector3 worldPoint = boundsCollider.transform.TransformPoint(localPoint);
            Vector3 rayStart = worldPoint + Vector3.up * scatter.RayHeight;

            if (!Physics.Raycast(
                    rayStart,
                    Vector3.down,
                    out RaycastHit hit,
                    scatter.RayHeight * 2f,
                    scatter.GroundLayer,
                    QueryTriggerInteraction.Ignore))
            {
                continue;
            }

            if (Vector3.Angle(hit.normal, Vector3.up) > scatter.MaxGroundSlope)
                continue;

            Vector3 placementPoint = hit.point + hit.normal * 0.01f;

            if (!IsPointInsideBounds(boundsCollider, placementPoint))
                continue;

            if (scatter.IsInsideExclusionVolume(placementPoint))
                continue;

            if (scatter.BlockAnyNonGroundCollider &&
                HasBlockingCollider(scatter, boundsCollider, placementPoint))
            {
                continue;
            }

            if (IsTooCloseToOtherPoints(placedPoints, placementPoint, scatter.MinSpacing))
                continue;

            GameObject prefab = scatter.DetailPrefabs[Random.Range(0, scatter.DetailPrefabs.Count)];

            if (prefab == null)
                continue;

            GameObject instance = PrefabUtility.InstantiatePrefab(prefab) as GameObject;

            if (instance == null)
                continue;

            Undo.RegisterCreatedObjectUndo(instance, "Generate ground detail");
            instance.transform.SetParent(root.transform, true);

            if (scatter.RandomYRotation)
            {
                instance.transform.rotation = Quaternion.Euler(
                    0f,
                    Random.Range(0f, 360f),
                    0f
                );
            }

            float scale = Random.Range(
                scatter.RandomScaleMin,
                scatter.RandomScaleMax
            );

            instance.transform.localScale *= scale;
            instance.transform.position = placementPoint;

            AlignVisualBoundsToGround(instance, placementPoint);

            if (!AreVisualBoundsInsideArea(instance, boundsCollider))
            {
                Undo.DestroyObjectImmediate(instance);
                continue;
            }

            placedPoints.Add(instance.transform.position);
            placed++;
        }

        EditorUtility.SetDirty(scatter);

        if (placed < scatter.DetailCount)
        {
            Debug.LogWarning(
                $"GroundDetailScatter: placed {placed}/{scatter.DetailCount} details after {attempts} attempts.",
                scatter
            );
        }
        else
        {
            Debug.Log(
                $"GroundDetailScatter: placed {placed} details in {attempts} attempts.",
                scatter
            );
        }
    }

    private static bool HasBlockingCollider(
        GroundDetailScatter scatter,
        BoxCollider boundsCollider,
        Vector3 placementPoint)
    {
        float radius = Mathf.Max(0.05f, scatter.ObstacleClearance);
        float halfHeight = Mathf.Max(1f, scatter.RayHeight * 0.5f);

        Collider[] overlaps = Physics.OverlapBox(
            placementPoint + Vector3.up * halfHeight,
            new Vector3(radius, halfHeight, radius),
            Quaternion.identity,
            ~0,
            QueryTriggerInteraction.Ignore
        );

        foreach (Collider collider in overlaps)
        {
            if (collider == null || !collider.enabled)
                continue;

            if (collider == boundsCollider)
                continue;

            if (((1 << collider.gameObject.layer) & scatter.GroundLayer.value) != 0)
                continue;

            if (collider.GetComponentInParent<GrassCuttable>() != null)
                continue;

            return true;
        }

        return false;
    }

    private static bool IsTooCloseToOtherPoints(List<Vector3> points, Vector3 point, float minSpacing)
    {
        float sqr = minSpacing * minSpacing;

        foreach (Vector3 existing in points)
        {
            Vector3 a = new Vector3(existing.x, 0f, existing.z);
            Vector3 b = new Vector3(point.x, 0f, point.z);

            if ((a - b).sqrMagnitude < sqr)
                return true;
        }

        return false;
    }

    private static void AlignVisualBoundsToGround(GameObject instance, Vector3 placementPoint)
    {
        Renderer[] renderers = instance.GetComponentsInChildren<Renderer>(true);

        if (renderers.Length == 0)
            return;

        Bounds bounds = renderers[0].bounds;

        for (int i = 1; i < renderers.Length; i++)
        {
            bounds.Encapsulate(renderers[i].bounds);
        }

        Vector3 offset = new Vector3(
            placementPoint.x - bounds.center.x,
            placementPoint.y - bounds.min.y,
            placementPoint.z - bounds.center.z
        );

        instance.transform.position += offset;
    }

    private static bool AreVisualBoundsInsideArea(GameObject instance, BoxCollider boundsCollider)
    {
        Renderer[] renderers = instance.GetComponentsInChildren<Renderer>(true);

        if (renderers.Length == 0)
            return true;

        Bounds bounds = renderers[0].bounds;

        for (int i = 1; i < renderers.Length; i++)
        {
            bounds.Encapsulate(renderers[i].bounds);
        }

        Vector3[] corners =
        {
            new Vector3(bounds.min.x, bounds.min.y, bounds.min.z),
            new Vector3(bounds.min.x, bounds.min.y, bounds.max.z),
            new Vector3(bounds.max.x, bounds.min.y, bounds.min.z),
            new Vector3(bounds.max.x, bounds.min.y, bounds.max.z)
        };

        foreach (Vector3 corner in corners)
        {
            if (!IsPointInsideBounds(boundsCollider, corner))
                return false;
        }

        return true;
    }

    private static bool IsPointInsideBounds(BoxCollider boundsCollider, Vector3 worldPoint)
    {
        Vector3 local = boundsCollider.transform.InverseTransformPoint(worldPoint) - boundsCollider.center;
        Vector3 half = boundsCollider.size * 0.5f;

        return Mathf.Abs(local.x) <= half.x + 0.001f
            && Mathf.Abs(local.y) <= half.y + 0.5f
            && Mathf.Abs(local.z) <= half.z + 0.001f;
    }

    private static void ClearDetails(GroundDetailScatter scatter)
    {
        Transform existing = scatter.transform.Find(GeneratedRootName);

        if (existing != null)
        {
            Undo.DestroyObjectImmediate(existing.gameObject);
        }
    }
}
#endif

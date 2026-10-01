#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(GrassScatterArea))]
public class GrassScatterAreaEditor : Editor
{
    private const string GeneratedRootName = "Generated Grass";

    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();

        GrassScatterArea area = (GrassScatterArea)target;

        EditorGUILayout.Space();

        if (GUILayout.Button("Generate Grass"))
        {
            GenerateGrass(area);
        }

        if (GUILayout.Button("Clear Generated Grass"))
        {
            ClearGrass(area);
        }
    }

    private static void GenerateGrass(GrassScatterArea area)
    {
        if (area.GrassPrefab == null)
        {
            Debug.LogWarning("GrassScatterArea: assign a Grass Prefab first.", area);
            return;
        }

        BoxCollider boundsCollider = area.AreaBounds != null
            ? area.AreaBounds
            : area.GetComponent<BoxCollider>();

        if (boundsCollider == null)
        {
            Debug.LogWarning("GrassScatterArea: BoxCollider bounds are required.", area);
            return;
        }

        boundsCollider.isTrigger = true;
        ClearGrass(area);

        GameObject root = new GameObject(GeneratedRootName);
        Undo.RegisterCreatedObjectUndo(root, "Create generated grass root");
        root.transform.SetParent(area.transform);
        root.transform.localPosition = Vector3.zero;
        root.transform.localRotation = Quaternion.identity;
        root.transform.localScale = Vector3.one;

        int placed = 0;
        int attempts = 0;
        int maxAttempts = Mathf.Max(area.GrassCount, area.MaxPlacementAttempts);

        while (placed < area.GrassCount && attempts < maxAttempts)
        {
            attempts++;

            Vector3 localPoint = boundsCollider.center + new Vector3(
                Random.Range(-boundsCollider.size.x * 0.5f, boundsCollider.size.x * 0.5f),
                0f,
                Random.Range(-boundsCollider.size.z * 0.5f, boundsCollider.size.z * 0.5f)
            );

            Vector3 worldPoint = boundsCollider.transform.TransformPoint(localPoint);
            Vector3 rayStart = worldPoint + Vector3.up * area.RayHeight;

            if (!Physics.Raycast(
                    rayStart,
                    Vector3.down,
                    out RaycastHit hit,
                    area.RayHeight * 2f,
                    area.GroundLayer,
                    QueryTriggerInteraction.Ignore))
            {
                continue;
            }

            if (Vector3.Angle(hit.normal, Vector3.up) > area.MaxGroundSlope)
                continue;

            Vector3 placementPoint = hit.point + hit.normal * 0.01f;

            if (!IsPointInsideBounds(boundsCollider, placementPoint))
                continue;

            if (area.IsInsideExclusionVolume(placementPoint))
                continue;

            if (area.BlockAnyNonGroundCollider &&
                HasBlockingCollider(area, boundsCollider, placementPoint))
            {
                continue;
            }

            GameObject instance = PrefabUtility.InstantiatePrefab(area.GrassPrefab) as GameObject;

            if (instance == null)
                continue;

            Undo.RegisterCreatedObjectUndo(instance, "Generate grass");
            instance.transform.SetParent(root.transform, true);

            if (area.RandomYRotation)
            {
                instance.transform.rotation = Quaternion.Euler(
                    0f,
                    Random.Range(0f, 360f),
                    0f
                );
            }

            float scale = Random.Range(
                area.RandomScaleMin,
                area.RandomScaleMax
            );

            instance.transform.localScale *= scale;
            instance.transform.position = placementPoint;

            AlignVisualBoundsToPoint(instance, placementPoint);

            if (!AreVisualBoundsInsideArea(instance, boundsCollider))
            {
                Undo.DestroyObjectImmediate(instance);
                continue;
            }

            placed++;
        }

        EditorUtility.SetDirty(area);

        if (placed < area.GrassCount)
        {
            Debug.LogWarning(
                $"GrassScatterArea: placed {placed}/{area.GrassCount} grass objects after {attempts} attempts.",
                area
            );
        }
        else
        {
            Debug.Log(
                $"GrassScatterArea: placed {placed} grass objects in {attempts} attempts.",
                area
            );
        }
    }

    private static bool HasBlockingCollider(
        GrassScatterArea area,
        BoxCollider boundsCollider,
        Vector3 placementPoint)
    {
        float radius = Mathf.Max(0.05f, area.ObstacleClearance);
        float halfHeight = Mathf.Max(1f, area.RayHeight * 0.5f);

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

            if (((1 << collider.gameObject.layer) & area.GroundLayer.value) != 0)
                continue;

            if (collider.GetComponentInParent<GrassCuttable>() != null)
                continue;

            return true;
        }

        return false;
    }

    private static void AlignVisualBoundsToPoint(GameObject instance, Vector3 placementPoint)
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

    private static void ClearGrass(GrassScatterArea area)
    {
        Transform existing = area.transform.Find(GeneratedRootName);

        if (existing != null)
        {
            Undo.DestroyObjectImmediate(existing.gameObject);
        }
    }
}
#endif

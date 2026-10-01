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

            float offsetX = Random.Range(-area.AreaSize.x * 0.5f, area.AreaSize.x * 0.5f);
            float offsetZ = Random.Range(-area.AreaSize.y * 0.5f, area.AreaSize.y * 0.5f);

            Vector3 worldPoint = area.GetWorldPoint(offsetX, offsetZ);
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

            float slope = Vector3.Angle(hit.normal, Vector3.up);

            if (slope > area.MaxGroundSlope)
                continue;

            Vector3 placementPoint = hit.point + hit.normal * 0.01f;

            if (area.IsInsideExclusionVolume(placementPoint))
                continue;

            if (area.ObstacleLayer.value != 0 &&
                Physics.CheckSphere(
                    placementPoint + Vector3.up * 0.15f,
                    Mathf.Max(0.01f, area.ObstacleClearance),
                    area.ObstacleLayer,
                    QueryTriggerInteraction.Ignore))
            {
                continue;
            }

            GameObject instance = PrefabUtility.InstantiatePrefab(area.GrassPrefab) as GameObject;

            if (instance == null)
                continue;

            Undo.RegisterCreatedObjectUndo(instance, "Generate grass");

            instance.transform.SetParent(root.transform, true);
            instance.transform.position = placementPoint;

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
            placed++;
        }

        EditorUtility.SetDirty(area);

        if (placed < area.GrassCount)
        {
            Debug.LogWarning(
                $"GrassScatterArea: placed {placed}/{area.GrassCount} grass objects after {attempts} attempts. " +
                "Increase Max Placement Attempts or reduce obstacle/exclusion coverage.",
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

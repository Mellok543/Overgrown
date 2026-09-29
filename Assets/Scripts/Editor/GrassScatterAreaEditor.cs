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

        for (int i = 0; i < area.GrassCount; i++)
        {
            Vector3 localOffset = new Vector3(
                Random.Range(-area.AreaSize.x * 0.5f, area.AreaSize.x * 0.5f),
                0f,
                Random.Range(-area.AreaSize.y * 0.5f, area.AreaSize.y * 0.5f)
            );

            Vector3 worldPoint = area.transform.TransformPoint(localOffset);
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

            GameObject instance = PrefabUtility.InstantiatePrefab(area.GrassPrefab) as GameObject;

            if (instance == null)
                continue;

            Undo.RegisterCreatedObjectUndo(instance, "Generate grass");
            instance.transform.SetParent(root.transform);
            instance.transform.position = hit.point;

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
        Debug.Log($"GrassScatterArea: placed {placed} grass objects.", area);
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

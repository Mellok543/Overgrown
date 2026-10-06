using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class GameHUDSetup
{
    [MenuItem("Tools/Overgrown/Setup Game HUD")]
    public static void Setup()
    {
        GameObject old = GameObject.Find("GameHUD");
        if (old != null)
            Object.DestroyImmediate(old);

        Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        GameObject root = new GameObject("GameHUD");
        Canvas canvas = root.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;

        CanvasScaler scaler = root.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);
        scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
        scaler.matchWidthOrHeight = 0.5f;

        root.AddComponent<GraphicRaycaster>();
        GameHUD hud = root.AddComponent<GameHUD>();

        Color panel = new Color(0.055f, 0.065f, 0.05f, 0.82f);
        Color panelSoft = new Color(0.055f, 0.065f, 0.05f, 0.68f);
        Color text = new Color(0.96f, 0.94f, 0.84f, 1f);
        Color muted = new Color(0.73f, 0.76f, 0.64f, 1f);
        Color accent = new Color(0.66f, 0.76f, 0.34f, 1f);
        Color track = new Color(0.18f, 0.20f, 0.15f, 0.92f);

        // ---------- top left: money + carried grass ----------
        GameObject statusCard = CreatePanel(
            root.transform, "Status",
            new Vector2(28f, -28f), new Vector2(300f, 112f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f),
            panel
        );

        Text moneyText = CreateText(
            statusCard.transform, "Money", "$ 0",
            font, 28, text, TextAnchor.MiddleLeft
        );
        SetAnchoredRect(moneyText.rectTransform,
            new Vector2(18f, -12f), new Vector2(264f, 34f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f));

        Text grassText = CreateText(
            statusCard.transform, "Grass", "Трава  0 / 5",
            font, 21, muted, TextAnchor.MiddleLeft
        );
        SetAnchoredRect(grassText.rectTransform,
            new Vector2(18f, -52f), new Vector2(264f, 26f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f));

        Image grassTrack = CreateImage(statusCard.transform, "GrassTrack", track);
        SetAnchoredRect(grassTrack.rectTransform,
            new Vector2(18f, 14f), new Vector2(264f, 8f),
            new Vector2(0f, 0f), new Vector2(0f, 0f), new Vector2(0f, 0f));

        Image grassFill = CreateImage(grassTrack.transform, "Fill", accent);
        grassFill.type = Image.Type.Filled;
        grassFill.fillMethod = Image.FillMethod.Horizontal;
        grassFill.fillOrigin = 0;
        grassFill.fillAmount = 0f;
        SetStretch(grassFill.rectTransform);

        // ---------- top center: zone progress ----------
        GameObject zoneCard = CreatePanel(
            root.transform, "ZoneProgress",
            new Vector2(0f, -28f), new Vector2(340f, 62f),
            new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f),
            panelSoft
        );

        Text zoneText = CreateText(
            zoneCard.transform, "Label", "Двор  0%",
            font, 22, text, TextAnchor.MiddleCenter
        );
        SetAnchoredRect(zoneText.rectTransform,
            new Vector2(0f, -7f), new Vector2(310f, 34f),
            new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f));

        Image zoneTrack = CreateImage(zoneCard.transform, "Track", track);
        SetAnchoredRect(zoneTrack.rectTransform,
            new Vector2(0f, 10f), new Vector2(310f, 7f),
            new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f));

        Image zoneFill = CreateImage(zoneTrack.transform, "Fill", accent);
        zoneFill.type = Image.Type.Filled;
        zoneFill.fillMethod = Image.FillMethod.Horizontal;
        zoneFill.fillOrigin = 0;
        zoneFill.fillAmount = 0f;
        SetStretch(zoneFill.rectTransform);

        // ---------- bottom center: selected tool ----------
        GameObject toolCard = CreatePanel(
            root.transform, "CurrentTool",
            new Vector2(0f, 26f), new Vector2(300f, 52f),
            new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f),
            panelSoft
        );

        Text toolText = CreateText(
            toolCard.transform, "Label", "1  Руки",
            font, 22, text, TextAnchor.MiddleCenter
        );
        SetStretch(toolText.rectTransform);
        toolText.rectTransform.offsetMin = new Vector2(12f, 4f);
        toolText.rectTransform.offsetMax = new Vector2(-12f, -4f);

        CreateCrosshair(root.transform, new Color(1f, 1f, 1f, 0.9f));

        SerializedObject so = new SerializedObject(hud);
        so.FindProperty("moneyText").objectReferenceValue = moneyText;
        so.FindProperty("grassText").objectReferenceValue = grassText;
        so.FindProperty("toolText").objectReferenceValue = toolText;
        so.FindProperty("zoneText").objectReferenceValue = zoneText;
        so.FindProperty("grassFill").objectReferenceValue = grassFill;
        so.FindProperty("zoneFill").objectReferenceValue = zoneFill;
        so.ApplyModifiedPropertiesWithoutUndo();

        DisablePrototypeUI<EconomyManager>("showPrototypeUI");
        DisablePrototypeUI<GrassInventory>("showPrototypeUI");
        DisablePrototypeUI<ToolInventory>("showPrototypeUI");
        DisablePrototypeUI<StartZoneProgress>("showProgressUI");
        DisablePrototypeUI<GrassProgressManager>("showProgressUI");
        DisablePrototypeUI<HandGrassCollector>("showPrototypeUI");
        DisablePrototypeUI<HandGrassCollector>("showCrosshair");

        EditorSceneManager.MarkSceneDirty(
            UnityEngine.SceneManagement.SceneManager.GetActiveScene()
        );

        Selection.activeGameObject = root;
        Debug.Log("[GameHUDSetup] Clean HUD created. Save the scene (Ctrl+S).");
    }

    private static GameObject CreatePanel(
        Transform parent,
        string name,
        Vector2 anchoredPosition,
        Vector2 size,
        Vector2 anchorMin,
        Vector2 anchorMax,
        Vector2 pivot,
        Color color)
    {
        GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
        go.transform.SetParent(parent, false);

        RectTransform rt = go.GetComponent<RectTransform>();
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.pivot = pivot;
        rt.sizeDelta = size;
        rt.anchoredPosition = anchoredPosition;

        Image image = go.GetComponent<Image>();
        image.color = color;
        image.raycastTarget = false;

        return go;
    }

    private static Text CreateText(
        Transform parent,
        string name,
        string value,
        Font font,
        int fontSize,
        Color color,
        TextAnchor alignment)
    {
        GameObject go = new GameObject(name, typeof(RectTransform), typeof(Text));
        go.transform.SetParent(parent, false);

        Text label = go.GetComponent<Text>();
        label.font = font;
        label.fontSize = fontSize;
        label.color = color;
        label.alignment = alignment;
        label.text = value;
        label.raycastTarget = false;
        label.horizontalOverflow = HorizontalWrapMode.Overflow;
        label.verticalOverflow = VerticalWrapMode.Overflow;

        return label;
    }

    private static Image CreateImage(Transform parent, string name, Color color)
    {
        GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
        go.transform.SetParent(parent, false);

        Image image = go.GetComponent<Image>();
        image.color = color;
        image.raycastTarget = false;

        return image;
    }

    private static void CreateCrosshair(Transform parent, Color color)
    {
        GameObject crosshair = new GameObject("Crosshair", typeof(RectTransform));
        crosshair.transform.SetParent(parent, false);

        RectTransform root = crosshair.GetComponent<RectTransform>();
        root.anchorMin = new Vector2(0.5f, 0.5f);
        root.anchorMax = new Vector2(0.5f, 0.5f);
        root.pivot = new Vector2(0.5f, 0.5f);
        root.sizeDelta = new Vector2(24f, 24f);
        root.anchoredPosition = Vector2.zero;

        float length = 6f;
        float gap = 4f;
        float thickness = 2f;

        CrosshairLine(crosshair.transform, "Left",
            new Vector2(-(gap + length * 0.5f), 0f),
            new Vector2(length, thickness), color);

        CrosshairLine(crosshair.transform, "Right",
            new Vector2(gap + length * 0.5f, 0f),
            new Vector2(length, thickness), color);

        CrosshairLine(crosshair.transform, "Top",
            new Vector2(0f, gap + length * 0.5f),
            new Vector2(thickness, length), color);

        CrosshairLine(crosshair.transform, "Bottom",
            new Vector2(0f, -(gap + length * 0.5f)),
            new Vector2(thickness, length), color);
    }

    private static void CrosshairLine(
        Transform parent,
        string name,
        Vector2 position,
        Vector2 size,
        Color color)
    {
        Image image = CreateImage(parent, name, color);
        RectTransform rt = image.rectTransform;

        rt.anchorMin = new Vector2(0.5f, 0.5f);
        rt.anchorMax = new Vector2(0.5f, 0.5f);
        rt.pivot = new Vector2(0.5f, 0.5f);
        rt.anchoredPosition = position;
        rt.sizeDelta = size;
    }

    private static void SetAnchoredRect(
        RectTransform rt,
        Vector2 anchoredPosition,
        Vector2 size,
        Vector2 anchorMin,
        Vector2 anchorMax,
        Vector2 pivot)
    {
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.pivot = pivot;
        rt.anchoredPosition = anchoredPosition;
        rt.sizeDelta = size;
    }

    private static void SetStretch(RectTransform rt)
    {
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
    }

    private static void DisablePrototypeUI<T>(string propertyName) where T : Component
    {
        T[] objects = Object.FindObjectsByType<T>(
            FindObjectsInactive.Include,
            FindObjectsSortMode.None
        );

        foreach (T item in objects)
        {
            SerializedObject so = new SerializedObject(item);
            SerializedProperty p = so.FindProperty(propertyName);

            if (p != null && p.propertyType == SerializedPropertyType.Boolean)
            {
                p.boolValue = false;
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(item);
            }
        }
    }
}

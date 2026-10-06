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

        Color panel = new Color(0.075f, 0.09f, 0.07f, 0.78f);
        Color panelSoft = new Color(0.10f, 0.12f, 0.09f, 0.72f);
        Color text = new Color(0.94f, 0.92f, 0.82f, 1f);
        Color accent = new Color(0.63f, 0.72f, 0.34f, 1f);
        Color track = new Color(0.18f, 0.20f, 0.15f, 0.9f);

        Text moneyText = CreateCard(root.transform, "Money", "$ 0",
            new Vector2(24f, -24f), new Vector2(190f, 62f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), font, 30, panel, text,
            TextAnchor.MiddleLeft);

        GameObject zoneCard = CreatePanel(root.transform, "ZoneProgress",
            new Vector2(0f, -24f), new Vector2(340f, 76f),
            new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), panel);

        Text zoneText = CreateText(zoneCard.transform, "Label", "Двор  0%", font, 24, text,
            TextAnchor.MiddleCenter);
        SetRect(zoneText.rectTransform, new Vector2(14f, -8f), new Vector2(-14f, -39f),
            Vector2.zero, Vector2.one);

        Image zoneTrack = CreateImage(zoneCard.transform, "Track", track);
        RectTransform zt = zoneTrack.rectTransform;
        zt.anchorMin = new Vector2(0f, 0f);
        zt.anchorMax = new Vector2(1f, 0f);
        zt.pivot = new Vector2(0.5f, 0f);
        zt.offsetMin = new Vector2(14f, 12f);
        zt.offsetMax = new Vector2(-14f, 22f);

        Image zoneFill = CreateImage(zoneTrack.transform, "Fill", accent);
        zoneFill.type = Image.Type.Filled;
        zoneFill.fillMethod = Image.FillMethod.Horizontal;
        zoneFill.fillOrigin = 0;
        zoneFill.fillAmount = 0f;
        SetStretch(zoneFill.rectTransform);

        GameObject grassCard = CreatePanel(root.transform, "GrassInventory",
            new Vector2(24f, 24f), new Vector2(300f, 86f),
            new Vector2(0f, 0f), new Vector2(0f, 0f), panel);

        Text grassText = CreateText(grassCard.transform, "Label", "Трава  0 / 5", font, 25, text,
            TextAnchor.MiddleLeft);
        SetRect(grassText.rectTransform, new Vector2(18f, -8f), new Vector2(-18f, -43f),
            Vector2.zero, Vector2.one);

        Image grassTrack = CreateImage(grassCard.transform, "Track", track);
        RectTransform gt = grassTrack.rectTransform;
        gt.anchorMin = new Vector2(0f, 0f);
        gt.anchorMax = new Vector2(1f, 0f);
        gt.pivot = new Vector2(0.5f, 0f);
        gt.offsetMin = new Vector2(18f, 15f);
        gt.offsetMax = new Vector2(-18f, 27f);

        Image grassFill = CreateImage(grassTrack.transform, "Fill", accent);
        grassFill.type = Image.Type.Filled;
        grassFill.fillMethod = Image.FillMethod.Horizontal;
        grassFill.fillOrigin = 0;
        grassFill.fillAmount = 0f;
        SetStretch(grassFill.rectTransform);

        Text toolText = CreateCard(root.transform, "CurrentTool", "1  Руки",
            new Vector2(-24f, 24f), new Vector2(330f, 64f),
            new Vector2(1f, 0f), new Vector2(1f, 0f), font, 26, panelSoft, text,
            TextAnchor.MiddleCenter);

        CreateCrosshair(root.transform, text);

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
        DisablePrototypeUI<HandGrassCollector>("showPrototypeUI");
        DisablePrototypeUI<HandGrassCollector>("showCrosshair");

        EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        Selection.activeGameObject = root;

        Debug.Log("[GameHUDSetup] HUD created. Save the scene (Ctrl+S).");
    }

    private static Text CreateCard(Transform parent, string name, string value,
        Vector2 anchoredPosition, Vector2 size,
        Vector2 anchorMin, Vector2 anchorMax,
        Font font, int fontSize, Color background, Color foreground,
        TextAnchor alignment)
    {
        GameObject card = CreatePanel(parent, name, anchoredPosition, size, anchorMin, anchorMax, background);
        Text label = CreateText(card.transform, "Label", value, font, fontSize, foreground, alignment);
        RectTransform rt = label.rectTransform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = new Vector2(18f, 4f);
        rt.offsetMax = new Vector2(-18f, -4f);
        return label;
    }

    private static GameObject CreatePanel(Transform parent, string name,
        Vector2 anchoredPosition, Vector2 size,
        Vector2 anchorMin, Vector2 anchorMax, Color color)
    {
        GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
        go.transform.SetParent(parent, false);

        RectTransform rt = go.GetComponent<RectTransform>();
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.pivot = anchorMin;
        rt.sizeDelta = size;
        rt.anchoredPosition = anchoredPosition;

        go.GetComponent<Image>().color = color;
        return go;
    }

    private static Text CreateText(Transform parent, string name, string value, Font font,
        int fontSize, Color color, TextAnchor alignment)
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
        GameObject root = new GameObject("Crosshair", typeof(RectTransform));
        root.transform.SetParent(parent, false);

        RectTransform rr = root.GetComponent<RectTransform>();
        rr.anchorMin = new Vector2(0.5f, 0.5f);
        rr.anchorMax = new Vector2(0.5f, 0.5f);
        rr.pivot = new Vector2(0.5f, 0.5f);
        rr.sizeDelta = new Vector2(28f, 28f);
        rr.anchoredPosition = Vector2.zero;

        float length = 7f;
        float gap = 4f;
        float thickness = 2f;

        CreateCrosshairLine(root.transform, "Left", new Vector2(-(gap + length * 0.5f), 0f), new Vector2(length, thickness), color);
        CreateCrosshairLine(root.transform, "Right", new Vector2(gap + length * 0.5f, 0f), new Vector2(length, thickness), color);
        CreateCrosshairLine(root.transform, "Top", new Vector2(0f, gap + length * 0.5f), new Vector2(thickness, length), color);
        CreateCrosshairLine(root.transform, "Bottom", new Vector2(0f, -(gap + length * 0.5f)), new Vector2(thickness, length), color);
    }

    private static void CreateCrosshairLine(Transform parent, string name, Vector2 pos, Vector2 size, Color color)
    {
        Image image = CreateImage(parent, name, color);
        RectTransform rt = image.rectTransform;
        rt.anchorMin = new Vector2(0.5f, 0.5f);
        rt.anchorMax = new Vector2(0.5f, 0.5f);
        rt.pivot = new Vector2(0.5f, 0.5f);
        rt.anchoredPosition = pos;
        rt.sizeDelta = size;
    }

    private static void SetRect(RectTransform rt, Vector2 minOffset, Vector2 maxOffset, Vector2 minAnchor, Vector2 maxAnchor)
    {
        rt.anchorMin = minAnchor;
        rt.anchorMax = maxAnchor;
        rt.offsetMin = minOffset;
        rt.offsetMax = maxOffset;
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
        T[] objects = Object.FindObjectsByType<T>(FindObjectsInactive.Include, FindObjectsSortMode.None);

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

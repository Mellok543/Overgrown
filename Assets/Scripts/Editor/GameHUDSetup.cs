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

        Color panel = new Color(0.045f, 0.055f, 0.04f, 0.90f);
        Color panelSoft = new Color(0.055f, 0.065f, 0.05f, 0.82f);
        Color panelLight = new Color(0.10f, 0.12f, 0.09f, 0.90f);
        Color text = new Color(0.95f, 0.93f, 0.83f, 1f);
        Color muted = new Color(0.66f, 0.69f, 0.58f, 1f);
        Color accent = new Color(0.62f, 0.74f, 0.30f, 1f);
        Color track = new Color(0.14f, 0.16f, 0.12f, 1f);

        // -------- Status card --------
        GameObject status = CreatePanel(
            root.transform, "Status",
            new Vector2(30f, -30f), new Vector2(330f, 126f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f),
            panel
        );
        AddShadow(status, new Color(0f, 0f, 0f, 0.32f), new Vector2(4f, -4f));

        Image statusAccent = CreateImage(status.transform, "Accent", accent);
        SetAnchoredRect(statusAccent.rectTransform,
            new Vector2(0f, 0f), new Vector2(6f, 126f),
            new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(0f, 0.5f));

        Text moneyCaption = CreateText(status.transform, "MoneyCaption", "ДЕНЬГИ",
            font, 14, muted, TextAnchor.UpperLeft);
        SetAnchoredRect(moneyCaption.rectTransform,
            new Vector2(22f, -16f), new Vector2(120f, 22f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f));

        Text moneyText = CreateText(status.transform, "Money", "$ 0",
            font, 30, text, TextAnchor.UpperLeft);
        SetAnchoredRect(moneyText.rectTransform,
            new Vector2(22f, -38f), new Vector2(180f, 36f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f));

        Text grassCaption = CreateText(status.transform, "GrassCaption", "СОБРАНО ТРАВЫ",
            font, 14, muted, TextAnchor.UpperRight);
        SetAnchoredRect(grassCaption.rectTransform,
            new Vector2(-20f, -16f), new Vector2(145f, 22f),
            new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(1f, 1f));

        Text grassText = CreateText(status.transform, "Grass", "0 / 5",
            font, 26, text, TextAnchor.UpperRight);
        SetAnchoredRect(grassText.rectTransform,
            new Vector2(-20f, -40f), new Vector2(145f, 32f),
            new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(1f, 1f));

        Image grassTrack = CreateImage(status.transform, "GrassTrack", track);
        SetAnchoredRect(grassTrack.rectTransform,
            new Vector2(22f, 16f), new Vector2(286f, 9f),
            new Vector2(0f, 0f), new Vector2(0f, 0f), new Vector2(0f, 0f));

        Image grassFill = CreateImage(grassTrack.transform, "Fill", accent);
        grassFill.type = Image.Type.Filled;
        grassFill.fillMethod = Image.FillMethod.Horizontal;
        grassFill.fillOrigin = 0;
        grassFill.fillAmount = 0f;
        SetStretch(grassFill.rectTransform);

        // -------- Objective card --------
        GameObject objective = CreatePanel(
            root.transform, "Objective",
            new Vector2(0f, -30f), new Vector2(430f, 92f),
            new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f),
            panelSoft
        );
        AddShadow(objective, new Color(0f, 0f, 0f, 0.26f), new Vector2(3f, -3f));

        Text objectiveText = CreateText(objective.transform, "ObjectiveText", "ОЧИСТИТЕ ДВОР",
            font, 18, muted, TextAnchor.MiddleLeft);
        SetAnchoredRect(objectiveText.rectTransform,
            new Vector2(20f, -10f), new Vector2(260f, 28f),
            new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f));

        Text zoneText = CreateText(objective.transform, "Percent", "0%",
            font, 27, text, TextAnchor.MiddleRight);
        SetAnchoredRect(zoneText.rectTransform,
            new Vector2(-18f, -8f), new Vector2(90f, 32f),
            new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(1f, 1f));

        Image zoneTrack = CreateImage(objective.transform, "Track", track);
        SetAnchoredRect(zoneTrack.rectTransform,
            new Vector2(20f, 16f), new Vector2(392f, 10f),
            new Vector2(0f, 0f), new Vector2(0f, 0f), new Vector2(0f, 0f));

        Image zoneFill = CreateImage(zoneTrack.transform, "Fill", accent);
        zoneFill.type = Image.Type.Filled;
        zoneFill.fillMethod = Image.FillMethod.Horizontal;
        zoneFill.fillOrigin = 0;
        zoneFill.fillAmount = 0f;
        SetStretch(zoneFill.rectTransform);

        // -------- Tool belt --------
        GameObject belt = CreatePanel(
            root.transform, "ToolBelt",
            new Vector2(0f, 28f), new Vector2(560f, 112f),
            new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f),
            new Color(panel.r, panel.g, panel.b, 0.72f)
        );
        AddShadow(belt, new Color(0f, 0f, 0f, 0.25f), new Vector2(3f, -3f));

        Text toolText = CreateText(belt.transform, "CurrentTool", "РУКИ",
            font, 16, muted, TextAnchor.MiddleCenter);
        SetAnchoredRect(toolText.rectTransform,
            new Vector2(0f, -10f), new Vector2(520f, 24f),
            new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f));

        Image[] slots = new Image[5];
        Text[] slotLabels = new Text[5];

        float startX = -208f;
        for (int i = 0; i < 5; i++)
        {
            GameObject slot = CreatePanel(
                belt.transform, "Slot_" + (i + 1),
                new Vector2(startX + i * 104f, 14f), new Vector2(88f, 64f),
                new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f),
                panelLight
            );

            slots[i] = slot.GetComponent<Image>();

            Outline outline = slot.AddComponent<Outline>();
            outline.effectColor = new Color(accent.r, accent.g, accent.b, 0.28f);
            outline.effectDistance = new Vector2(1f, -1f);

            Text label = CreateText(slot.transform, "Label",
                (i + 1) + "\n—",
                font, 15, text, TextAnchor.MiddleCenter);
            SetStretch(label.rectTransform);
            slotLabels[i] = label;
        }

        CreateCrosshair(root.transform, new Color(1f, 1f, 1f, 0.92f));

        SerializedObject so = new SerializedObject(hud);
        so.FindProperty("moneyText").objectReferenceValue = moneyText;
        so.FindProperty("grassText").objectReferenceValue = grassText;
        so.FindProperty("toolText").objectReferenceValue = toolText;
        so.FindProperty("zoneText").objectReferenceValue = zoneText;
        so.FindProperty("objectiveText").objectReferenceValue = objectiveText;
        so.FindProperty("grassFill").objectReferenceValue = grassFill;
        so.FindProperty("zoneFill").objectReferenceValue = zoneFill;

        SerializedProperty slotProp = so.FindProperty("toolSlots");
        slotProp.arraySize = slots.Length;

        SerializedProperty labelProp = so.FindProperty("toolSlotLabels");
        labelProp.arraySize = slotLabels.Length;

        for (int i = 0; i < slots.Length; i++)
        {
            slotProp.GetArrayElementAtIndex(i).objectReferenceValue = slots[i];
            labelProp.GetArrayElementAtIndex(i).objectReferenceValue = slotLabels[i];
        }

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
        Debug.Log("[GameHUDSetup] Styled HUD created. Save the scene (Ctrl+S).");
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

    private static void AddShadow(GameObject target, Color color, Vector2 distance)
    {
        Shadow shadow = target.AddComponent<Shadow>();
        shadow.effectColor = color;
        shadow.effectDistance = distance;
        shadow.useGraphicAlpha = true;
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
        root.sizeDelta = new Vector2(22f, 22f);
        root.anchoredPosition = Vector2.zero;

        float length = 5f;
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

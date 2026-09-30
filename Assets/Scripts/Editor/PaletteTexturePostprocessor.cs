using UnityEditor;
using UnityEngine;

// Flat-colour palette atlases for the low-poly props (SellPoint, CapacityUpgrade, ...):
// UVs point at the centre of solid colour cells, so they need point filtering and no compression/mips
// or neighbouring cells bleed into each other.
public class PaletteTexturePostprocessor : AssetPostprocessor
{
    private void OnPreprocessTexture()
    {
        // Grass_Atlas is a smooth gradient and wants regular filtering + mips
        if (!assetPath.StartsWith("Assets/Art/Models/") || assetPath.StartsWith("Assets/Art/Models/Grass/"))
            return;

        string fileName = System.IO.Path.GetFileNameWithoutExtension(assetPath);
        if (!fileName.EndsWith("_Atlas") && !fileName.EndsWith("_Palette"))
            return;

        TextureImporter importer = (TextureImporter)assetImporter;
        importer.filterMode = FilterMode.Point;
        importer.mipmapEnabled = false;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.wrapMode = TextureWrapMode.Clamp;
    }
}

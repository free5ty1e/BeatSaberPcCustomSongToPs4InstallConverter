# Manual Unity Workflow - Step by Step Guide

## Problem
Beat Saber PS4 uses Unity 2022.3.33f1 with **LZ4HAM compression** for AssetBundles. This is a Unity-specific compression format that cannot be decompressed with standard tools.

## Solution Overview
You need to use **Unity 2022.3 LTS** itself to:
1. Extract and analyze existing Beat Saber AssetBundles
2. Create new custom level AssetBundles
3. Build a test PKG with custom songs

---

## Step 1: Install Unity 2022.3 LTS

### Download Unity Hub
1. Go to https://unity.com/download
2. Download and install Unity Hub

### Install Unity 2022.3 LTS
1. Open Unity Hub
2. Go to **Installs** → **Add** → **Specific Unity Version**
3. Search for: `2022.3.33f1` (or closest 2022.3 LTS)
4. If not available, use `2022.3.30f1` or newer 2022.3 version
5. Add these modules:
   - **Linux Build Support** (for AssetBundle building)
   - **WebGL Build Support** (not needed but ok)
6. Click **Install**

---

## Step 2: Get UABEA (AssetBundle Tool)

UABEA is a tool for viewing and editing Unity AssetBundles.

1. Download from: https://github.com/nesrak1/UABEA
2. Download the latest release from the Releases page
3. Extract to: `C:\Tools\UABEA\`
4. Run `UABEA.exe`

**Note:** UABEA requires .NET 6.0 or newer. Download from https://dotnet.microsoft.com/download/dotnet/6.0

---

## Step 3: Analyze Beat Saber Levels with UABEA

### Open the Level File
1. Run UABEA.exe
2. Click **File** → **Open** (or press Ctrl+O)
3. Navigate to the beatmap level file:
   ```
   CUSA12878-patch\Media\StreamingAssets\BeatmapLevelsData\beatsaber
   ```
4. Click **Open**

### Understanding the Interface

**Left Panel (Asset Tree):** Shows all assets inside the bundle:
- Textures (cover images)
- AudioClips (music files)
- MonoBehaviours (game logic)
- GameObjects
- Other assets

**Right Panel (Details):**
- Shows selected asset info
- Preview for images/audio
- Export options at the bottom

### What to Look For

1. **Click on each asset** in the left tree and note:
   - Type (Texture2D, AudioClip, MonoBehaviour, etc.)
   - Size
   - Preview (for images/audio)

2. **Look for these key assets:**
   - `AudioClip` - The song audio
   - `Texture2D` - Cover art
   - `MonoBehaviour` or `BeatmapLevelData` - Level metadata

3. **Expand the tree** by clicking the arrows to see all contained assets

---

## Step 4: Create Unity Project for Level Building

### Create New Project
1. Unity Hub → **Projects** → **New Project**
2. Template: **3D (Built-in Render Pipeline)**
3. Name: `BeatSaberCustomLevels`
4. Location: `C:\BeatSaberModding\UnityProjects\`
5. Click **Create Project**

### Import Beat Saber SDK (Optional but Recommended)
1. Download Beat Saber IPA (BSIPA) from: https://github.com/nike4613/BeatSaber-IPA-Reloaded/releases
2. This contains reference assemblies for Beat Saber's classes
3. Or use the extracted DLLs from `globalgamemanagers.assets`

### Create Level Template Scene
1. Create a new scene: `Assets\Scenes\CustomLevelTemplate.unity`
2. Add a simple 3D plane as a placeholder
3. We'll use this as a base for building custom levels

---

## Step 5: Create Custom Level Script

### Create Level Data Script
Create file: `Assets\Scripts\CustomBeatmapLevel.cs`

```csharp
using UnityEngine;

[System.Serializable]
public class DifficultyBeatmap
{
    public string beatmapFilename;
    public string difficulty;
    public string difficultyRank;
    public float noteJumpMovementSpeed;
    public float noteJumpStartBeatTime;
    public ColorScheme colorScheme;
    public EnvironmentColourScheme environmentColourScheme;
}

[System.Serializable]
public class ColorScheme
{
    public Color colorA;
    public Color colorB;
}

[System.Serializable]
public class EnvironmentColourScheme
{
    public Color environmentColor0;
    public Color environmentColor1;
}

[System.Serializable]
public class CustomBeatmapLevel : MonoBehaviour
{
    public string levelId;
    public string levelName;
    public string songName;
    public string songAuthorName;
    public string levelAuthorName;
    public float beatsPerMinute;
    public float songTimeOffset;
    public float shuffle;
    public float shufflePeriod;
    public float previewDuration;
    public float coverImageImage;
    
    public DifficultyBeatmap[] difficultyBeatmaps;
    
    // Audio will be loaded from AssetBundle
    public AudioClip songAudio;
    public Sprite coverImage;
}
```

---

## Step 6: Build Custom AssetBundle

### Create AssetBundle Build Script
Create file: `Assets\Editor\BuildCustomLevels.cs`

```csharp
using UnityEngine;
using UnityEditor;
using System.IO;

public class BuildCustomLevels
{
    [MenuItem("BeatSaber/Build Custom Levels")]
    public static void BuildAssetBundles()
    {
        string outputPath = "C:/BeatSaberModding/Output";
        
        if (!Directory.Exists(outputPath))
            Directory.CreateDirectory(outputPath);
        
        // Build AssetBundle for current platform
        BuildPipeline.BuildAssetBundles(
            outputPath,
            BuildAssetBundleOptions.UncompressedAssetBundle,
            BuildTarget.PS4
        );
        
        Debug.Log("AssetBundles built to: " + outputPath);
    }
    
    [MenuItem("BeatSaber/Build AssetBundle (Single File)")]
    public static void BuildSingleAssetBundle()
    {
        string outputPath = "C:/BeatSaberModding/Output/CustomLevels";
        
        if (!Directory.Exists(outputPath))
            Directory.CreateDirectory(outputPath);
        
        // Select the level prefab in the scene
        Object[] selected = Selection.objects;
        
        BuildPipeline.BuildAssetBundles(
            outputPath,
            BuildAssetBundleOptions.UncompressedAssetBundle | BuildAssetBundleOptions.ForceDisableCompression,
            BuildTarget.PS4
        );
        
        Debug.Log("Built: " + outputPath);
    }
}
```

### Create Level Prefab
1. Create a GameObject with your CustomBeatmapLevel script
2. Fill in the level metadata
3. Assign audio and cover image
4. Drag into Assets folder to create Prefab
5. Select the prefab
6. In Inspector, mark for AssetBundle: `Assets → Mark as AssetBundle`
7. Name the bundle: `customlevel_mysong`

### Build
1. Unity menu: **BeatSaber** → **Build Custom Levels**
2. Check `C:\BeatSaberModding\Output\` for the built bundle

---

## Step 7: Verify AssetBundle Format

### Check with UABEA
1. Open UABEA
2. Open the built AssetBundle
3. Verify it contains:
   - Your level data
   - Correct structure matching Beat Saber's format

### Check Compression
The built bundle should use **LZ4** compression (Beat Saber's format).

If UABEA shows "LZ4" or no compression, you're good.

---

## Step 8: Test with Plugin (Future)

Once we have:
1. Function addresses from eboot.bin (requires PS4 debugging)
2. Working plugin build

You'll place custom AssetBundles in:
```
/data/GoldHEN/BeatSaberDX/songs/mysong
```

The plugin will intercept `AssetBundle.LoadFromFile` and redirect to custom levels.

---

## Next Steps After This Workflow

1. **Analyze extracted levels** → Document the exact format
2. **Create Python parser** → Once format is known, automate extraction
3. **Build level converter** → Convert BS+ format to Beat Saber PS4 format
4. **Create plugin** → Hook AssetBundle.LoadFromFile
5. **Build test PKG** → Package everything together

---

## Tools Summary

| Tool | Purpose | Download |
|------|---------|----------|
| Unity Hub | Install Unity 2022.3 LTS | unity.com/download |
| Unity 2022.3 LTS | Create/modify AssetBundles | Via Unity Hub |
| UABEA | View/edit AssetBundles | github.com/DragonBals/UABEA |
| .NET 6.0 | Required for UABEA | dotnet.microsoft.com |

---

## Step 4: What to Document

**Take screenshots of each major asset type:**

1. **AudioClip** (if present):
   - Note the format (WAV, OGG, etc.)
   - Sample rate, channels

2. **Texture2D** (cover art):
   - Dimensions
   - Format

3. **Any MonoBehaviour/BeatmapLevelData**:
   - Field names
   - Data types
   - Example values

**Report back with:**
1. Screenshot of the full asset tree
2. Details of each major asset type
3. What fields are visible in any level data objects

---

## Questions to Answer After Step 3

When you analyze the levels with UABEA, please report:

1. What asset types are in the file? (AudioClip, Texture2D, MonoBehaviour?)
2. Are there any "BeatmapLevelData" or similar level data objects?
3. What fields are visible in level data? (song name, BPM, etc.)
4. Is there embedded audio or just a reference?
5. Any other interesting structures?

This information will let us create the custom song pipeline.

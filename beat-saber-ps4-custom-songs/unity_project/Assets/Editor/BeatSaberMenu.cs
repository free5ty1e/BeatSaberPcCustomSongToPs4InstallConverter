using UnityEngine;
using UnityEditor;
using System.IO;

namespace BeatSaber.Editor
{
    /// <summary>
    /// Unity Editor menu items for Beat Saber level creation and building
    /// </summary>
    public static class BeatSaberMenu
    {
        private const string MENU_PATH = "BeatSaber/";
        private const string OUTPUT_PATH = "../../output/CustomLevels";

        /// <summary>
        /// Creates a new custom Beat Saber level GameObject in the current scene
        /// </summary>
        [MenuItem(MENU_PATH + "Create Custom Level")]
        public static void CreateCustomLevel()
        {
            // Create a new GameObject
            GameObject levelObject = new GameObject("CustomBeatmapLevel");

            // Add the CustomBeatmapLevel component
            var level = levelObject.AddComponent<BeatSaber.CustomBeatmapLevel>();

            // Set default level ID based on time
            level.levelID = "custom_level_" + System.DateTime.Now.ToString("yyyyMMdd_HHmmss");

            // Select the new object
            Selection.activeGameObject = levelObject;

            // Focus on the Inspector
            EditorApplication.ExecuteMenuItem("Window/General/Inspector");

            Debug.Log($"Created new custom level: {levelObject.name}");
            Debug.Log("Configure the level in the Inspector, then use BeatSaber → Build for PS4");
        }

        /// <summary>
        /// Creates a custom level from a selected AudioClip
        /// </summary>
        [MenuItem(MENU_PATH + "Create Level from Audio Clip")]
        public static void CreateLevelFromAudio()
        {
            // Check if AudioClip is selected
            if (Selection.activeObject is AudioClip audioClip)
            {
                GameObject levelObject = new GameObject(Path.GetFileNameWithoutExtension(audioClip.name));
                var level = levelObject.AddComponent<BeatSaber.CustomBeatmapLevel>();

                level.levelID = audioClip.name.ToLower().Replace(" ", "_");
                level.songName = audioClip.name;
                level.audioClip = audioClip;

                Selection.activeGameObject = levelObject;

                Debug.Log($"Created level from: {audioClip.name}");
            }
            else
            {
                Debug.LogWarning("Please select an AudioClip in the Project window first.");
                EditorUtility.DisplayDialog(
                    "No AudioClip Selected",
                    "Please select an AudioClip asset in the Project window, then try again.",
                    "OK"
                );
            }
        }

        /// <summary>
        /// Builds all custom levels marked as AssetBundles
        /// </summary>
        [MenuItem(MENU_PATH + "Build for PS4")]
        public static void BuildForPS4()
        {
            // Ensure output directory exists
            string outputDir = Path.Combine(Application.dataPath, "..", OUTPUT_PATH);
            outputDir = Path.GetFullPath(outputDir);

            if (!Directory.Exists(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }

            // Build AssetBundles for PS4
            BuildPipeline.BuildAssetBundles(
                outputDir,
                BuildAssetBundleOptions.UncompressedAssetBundle,
                BuildTarget.PS4
            );

            // Create metadata file
            CreateMetadataFile(outputDir);

            Debug.Log($"Build complete! AssetBundles saved to: {outputDir}");
            EditorUtility.RevealInFinder(outputDir);
        }

        /// <summary>
        /// Builds a single level to AssetBundle
        /// </summary>
        [MenuItem(MENU_PATH + "Build Selected Level")]
        public static void BuildSelectedLevel()
        {
            if (Selection.activeGameObject == null)
            {
                Debug.LogError("Please select a GameObject with CustomBeatmapLevel component.");
                return;
            }

            var level = Selection.activeGameObject.GetComponent<BeatSaber.CustomBeatmapLevel>();
            if (level == null)
            {
                Debug.LogError("Selected object does not have CustomBeatmapLevel component.");
                return;
            }

            if (!level.IsValid())
            {
                Debug.LogError("Level configuration is invalid. Please fix errors first.");
                return;
            }

            // Create temporary prefab
            string prefabPath = $"Assets/Prefabs/{level.levelID}.prefab";
            string prefabDir = Path.GetDirectoryName(prefabPath);

            if (!Directory.Exists(prefabDir))
            {
                Directory.CreateDirectory(prefabDir);
            }

            // Create prefab
            GameObject prefab = PrefabUtility.SaveAsPrefabAsset(
                Selection.activeGameObject,
                prefabPath
            );

            if (prefab == null)
            {
                Debug.LogError("Failed to create prefab.");
                return;
            }

            // Mark as AssetBundle
            AssetImporter.GetAtPath(prefabPath).assetBundleName = $"customlevel_{level.levelID}";

            // Build
            string outputDir = Path.Combine(Application.dataPath, "..", OUTPUT_PATH);
            outputDir = Path.GetFullPath(outputDir);

            if (!Directory.Exists(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }

            BuildPipeline.BuildAssetBundles(
                outputDir,
                BuildAssetBundleOptions.UncompressedAssetBundle,
                BuildTarget.PS4
            );

            Debug.Log($"Built level: {level.levelID}");
            Debug.Log($"Output: {outputDir}");

            // Clean up prefab
            AssetDatabase.DeleteAsset(prefabPath);
        }

        /// <summary>
        /// Opens the output folder in the file explorer
        /// </summary>
        [MenuItem(MENU_PATH + "Open Output Folder")]
        public static void OpenOutputFolder()
        {
            string outputDir = Path.Combine(Application.dataPath, "..", OUTPUT_PATH);
            outputDir = Path.GetFullPath(outputDir);

            if (Directory.Exists(outputDir))
            {
                EditorUtility.RevealInFinder(outputDir);
            }
            else
            {
                Debug.LogWarning($"Output folder does not exist: {outputDir}");
            }
        }

        /// <summary>
        /// Creates a metadata JSON file with build information
        /// </summary>
        private static void CreateMetadataFile(string outputDir)
        {
            var metadata = new
            {
                buildDate = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                unityVersion = Application.unityVersion,
                targetPlatform = "PS4",
                outputPath = outputDir
            };

            string json = JsonUtility.ToJson(metadata, true);
            string metadataPath = Path.Combine(outputDir, "build_metadata.json");
            File.WriteAllText(metadataPath, json);
        }

        /// <summary>
        /// Validates all levels in the scene
        /// </summary>
        [MenuItem(MENU_PATH + "Validate All Levels")]
        public static void ValidateAllLevels()
        {
            var levels = Object.FindObjectsOfType<BeatSaber.CustomBeatmapLevel>();

            if (levels.Length == 0)
            {
                Debug.Log("No custom levels found in scene.");
                return;
            }

            int valid = 0;
            int invalid = 0;

            foreach (var level in levels)
            {
                if (level.IsValid())
                {
                    Debug.Log($"✓ {level.levelID}: Valid");
                    valid++;
                }
                else
                {
                    Debug.LogError($"✗ {level.levelID}: Invalid");
                    invalid++;
                }
            }

            Debug.Log($"Validation complete: {valid} valid, {invalid} invalid");
        }
    }
}
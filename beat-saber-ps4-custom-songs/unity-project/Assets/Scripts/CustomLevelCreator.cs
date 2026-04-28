using UnityEngine;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;

namespace BeatSaberCustomSongs
{
    /// <summary>
    /// Beat Saber Level Data - matches the PC format
    /// </summary>
    [System.Serializable]
    public class BeatSaberLevelData
    {
        public string songName;
        public string songSubName;
        public string songAuthorName;
        public string levelAuthorName;
        public float beatsPerMinute;
        public float previewStartTime;
        public float previewDuration;
        public float songTimeOffset;
        public float shuffle;
        public float shufflePeriod;
        public string environmentName;
        public string allDirectionsEnvironmentName;
        public bool oneSaber;
        public List<DifficultyLevel> difficultyLevels;

        public static BeatSaberLevelData FromJson(string json)
        {
            return JsonUtility.FromJson<BeatSaberLevelData>(json);
        }
    }

    [System.Serializable]
    public class DifficultyLevel
    {
        public string difficulty;
        public int difficultyRank;
        public float njs;
        public float offset;
        public string jsonPath;
        public string beatmapCharName;
    }

    /// <summary>
    /// Beatmap note data - matches PC format
    /// </summary>
    [System.Serializable]
    public class BeatmapNote
    {
        public float time;
        public int lineIndex;
        public int lineLayer;
        public int noteType;
        public int cutDirection;

        public BeatmapNote(float t, int line, int layer, int type, int dir)
        {
            time = t;
            lineIndex = line;
            lineLayer = layer;
            noteType = type;
            cutDirection = dir;
        }
    }

    [System.Serializable]
    public class BeatmapBomb
    {
        public float time;
        public int lineIndex;
        public int lineLayer;
    }

    [System.Serializable]
    public class BeatmapObstacle
    {
        public float time;
        public float duration;
        public int lineIndex;
        public int lineLayer;
        public int type;
        public int width;
        public int height;
    }

    [System.Serializable]
    public class BeatmapEvent
    {
        public float time;
        public int type;
        public int value;
    }

    [System.Serializable]
    public class BeatmapData
    {
        public float time;
        public float bpm;
        public float rotation;
        public float translation;
        public List<BeatmapNote> colorNotes;
        public List<BeatmapBomb> bombs;
        public List<BeatmapObstacle> obstacles;
        public List<BeatmapEvent> events;

        public static BeatmapData FromJson(string json)
        {
            return JsonUtility.FromJson<BeatmapData>(json);
        }
    }

    /// <summary>
    /// Custom level creator for Beat Saber PS4
    /// </summary>
    public class CustomLevelCreator : MonoBehaviour
    {
        [Header("Song Info")]
        public TextAsset infoDat;

        [Header("Beatmap Files")]
        public TextAsset easyBeatmap;
        public TextAsset normalBeatmap;
        public TextAsset hardBeatmap;
        public TextAsset expertBeatmap;
        public TextAsset expertPlusBeatmap;

        [Header("Audio")]
        public AudioClip songAudio;

        [Header("Cover")]
        public Sprite coverImage;

        private BeatSaberLevelData levelData;
        private Dictionary<string, BeatmapData> beatmaps;

        void Start()
        {
            if (infoDat != null)
            {
                LoadSongInfo();
            }
        }

        public void LoadSongInfo()
        {
            string json = infoDat.text;
            levelData = BeatSaberLevelData.FromJson(json);
            beatmaps = new Dictionary<string, BeatmapData>();

            // Load all difficulties
            foreach (var diff in levelData.difficultyLevels)
            {
                TextAsset beatmapFile = GetBeatmapFile(diff.difficulty);
                if (beatmapFile != null)
                {
                    BeatmapData data = BeatmapData.FromJson(beatmapFile.text);
                    beatmaps[diff.difficulty] = data;
                }
            }

            Debug.Log($"Loaded song: {levelData.songName} with {beatmaps.Count} difficulties");
        }

        TextAsset GetBeatmapFile(string difficulty)
        {
            switch (difficulty.ToLower())
            {
                case "easy": return easyBeatmap;
                case "normal": return normalBeatmap;
                case "hard": return hardBeatmap;
                case "expert": return expertBeatmap;
                case "expertplus": return expertPlusBeatmap;
                default: return null;
            }
        }

        /// <summary>
        /// Create an asset bundle from this level
        /// </summary>
        public void CreateAssetBundle(string outputPath)
        {
            #if UNITY_EDITOR
            // Create the level prefab
            GameObject levelObj = new GameObject(levelData.songName);

            // Add components
            CustomLevel level = levelObj.AddComponent<CustomLevel>();
            level.songName = levelData.songName;
            level.songSubName = levelData.songSubName;
            level.songAuthorName = levelData.songAuthorName;
            level.levelAuthorName = levelData.levelAuthorName;
            level.beatsPerMinute = levelData.beatsPerMinute;
            level.audioClip = songAudio;
            level.coverImage = coverImage;
            level.beatmaps = beatmaps;

            // Save prefab
            string prefabPath = "Assets/Prefabs/" + levelData.songName + ".prefab";
            UnityEditor.PrefabUtility.SaveAsPrefabAsset(levelObj, prefabPath);

            // Create asset bundle
            string[] scenes = new string[] { prefabPath };
            UnityEditor.BuildPipeline.BuildAssetBundles(outputPath, scenes,
                UnityEditor.BuildAssetBundleOptions.None, UnityEditor.BuildTarget.PS4);

            Debug.Log($"Asset bundle created at: {outputPath}");
            #endif
        }
    }

    /// <summary>
    /// Individual custom level component
    /// </summary>
    public class CustomLevel : MonoBehaviour
    {
        public string songName;
        public string songSubName;
        public string songAuthorName;
        public string levelAuthorName;
        public float beatsPerMinute;
        public AudioClip audioClip;
        public Sprite coverImage;
        public Dictionary<string, BeatmapData> beatmaps;
    }
}
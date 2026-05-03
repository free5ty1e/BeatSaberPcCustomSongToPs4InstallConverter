using UnityEngine;
using System;

namespace BeatSaber
{
    /// <summary>
    /// Custom Beat Saber Level Component
    /// Attach to a GameObject to create a custom level
    /// </summary>
    [Serializable]
    public class DifficultyBeatmap
    {
        [Tooltip("Difficulty name: Easy, Normal, Hard, Expert, ExpertPlus")]
        public string difficulty = "Normal";

        [Tooltip("Difficulty rank (1-9): Easy=1, Normal=3, Hard=5, Expert=7, ExpertPlus=9")]
        public int difficultyRank = 3;

        [Tooltip("Note Jump Movement Speed")]
        public float noteJumpMovementSpeed = 10f;

        [Tooltip("Note Jump Start Beat Time")]
        public float noteJumpStartBeatTime = 0f;

        [Tooltip("Beatmap filename")]
        public string beatmapFilename = "Normal.dat";

        [Tooltip("Note color A")]
        public Color noteColorA = new Color(1f, 0f, 0.5f, 1f);

        [Tooltip("Note color B")]
        public Color noteColorB = new Color(0f, 1f, 0.5f, 1f);
    }

    /// <summary>
    /// Main component for creating custom Beat Saber levels
    /// </summary>
    public class CustomBeatmapLevel : MonoBehaviour
    {
        [Header("Level Information")]
        [Tooltip("Unique level identifier")]
        public string levelID = "custom_song";

        [Header("Song Metadata")]
        [Tooltip("Song display name")]
        public string songName = "My Custom Song";

        [Tooltip("Song sub-name (optional)")]
        public string songSubName = "";

        [Tooltip("Song artist name")]
        public string artistName = "Unknown Artist";

        [Tooltip("Level mapper/author name")]
        public string levelAuthorName = "CustomMapper";

        [Header("Audio")]
        [Tooltip("The audio clip for this level")]
        public AudioClip audioClip;

        [Header("Timing")]
        [Tooltip("Beats per minute")]
        public float beatsPerMinute = 120f;

        [Tooltip("Audio time offset in seconds")]
        public float songTimeOffset = 0f;

        [Tooltip("Shuffle amount (0 = none)")]
        public float shuffle = 0f;

        [Tooltip("Shuffle period")]
        public float shufflePeriod = 0.5f;

        [Header("Preview")]
        [Tooltip("Preview duration in seconds")]
        public float previewDuration = 30f;

        [Header("Environment")]
        [Tooltip("Environment name")]
        public string environmentName = "DefaultEnvironment";

        [Tooltip("All directions environment name")]
        public string allDirectionsEnvironmentName = "GlassDesert";

        [Header("Difficulties")]
        [Tooltip("Available difficulty levels")]
        public DifficultyBeatmap[] difficultyBeatmaps = new DifficultyBeatmap[]
        {
            new DifficultyBeatmap { difficulty = "Easy", difficultyRank = 1, noteJumpMovementSpeed = 10 },
            new DifficultyBeatmap { difficulty = "Normal", difficultyRank = 3, noteJumpMovementSpeed = 12 },
            new DifficultyBeatmap { difficulty = "Hard", difficultyRank = 5, noteJumpMovementSpeed = 14 },
            new DifficultyBeatmap { difficulty = "Expert", difficultyRank = 7, noteJumpMovementSpeed = 16 },
            new DifficultyBeatmap { difficulty = "ExpertPlus", difficultyRank = 9, noteJumpMovementSpeed = 18 }
        };

        /// <summary>
        /// Validates the level configuration
        /// </summary>
        public bool IsValid()
        {
            if (string.IsNullOrEmpty(levelID))
            {
                Debug.LogError("Level ID is required!");
                return false;
            }

            if (audioClip == null)
            {
                Debug.LogError("Audio clip is required!");
                return false;
            }

            if (beatsPerMinute <= 0)
            {
                Debug.LogError("BPM must be greater than 0!");
                return false;
            }

            return true;
        }

        /// <summary>
        /// Gets the duration of the audio clip
        /// </summary>
        public float GetDuration()
        {
            return audioClip != null ? audioClip.length : 0f;
        }

        /// <summary>
        /// Gets the approximate song duration in beats
        /// </summary>
        public float GetDurationInBeats()
        {
            return GetDuration() * beatsPerMinute / 60f;
        }

        private void OnValidate()
        {
            // Ensure level ID is valid filename
            levelID = levelID.Replace(" ", "_").Replace("/", "_").Replace("\\", "_");

            // Clamp BPM
            beatsPerMinute = Mathf.Max(1f, beatsPerMinute);

            // Ensure at least one difficulty
            if (difficultyBeatmaps == null || difficultyBeatmaps.Length == 0)
            {
                difficultyBeatmaps = new DifficultyBeatmap[]
                {
                    new DifficultyBeatmap { difficulty = "Easy", difficultyRank = 1 }
                };
            }
        }
    }
}
using UnityEngine;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace BeatSaberCustomSongs
{
    /// <summary>
    /// Converts BeatSaver PC beatmaps to PS4 format
    /// Outputs both beatmap .dat files and creates asset bundles
    /// </summary>
    public class BeatmapConverter : MonoBehaviour
    {
        [Header("Input (PC Format)")]
        public string inputSongPath;

        [Header("Output (PS4 Format)")]
        public string outputSongPath;
        public string assetBundlePath;

        /// <summary>
        /// PC BeatSaver info.dat structure
        /// </summary>
        [System.Serializable]
        public class PCInfoDat
        {
            public string _songName;
            public string _songSubName;
            public string _songAuthorName;
            public string _levelAuthorName;
            public float _beatsPerMinute = 120f;
            public float _previewStartTime;
            public float _previewDuration;
            public float _songTimeOffset;
            public float _shuffle;
            public float _shufflePeriod;
            public string _environmentName;
            public string _oneSaber;
            public List<PCDifficultyBeatmapSet> _difficultyBeatmapSets;
            public List<PCDifficultyBeatmap> _difficultyBeatmaps;
        }

        [System.Serializable]
        public class PCDifficultyBeatmapSet
        {
            public string _beatmapCharacteristicName;
            public List<PCDifficultyBeatmap> _difficultyBeatmaps;
        }

        [System.Serializable]
        public class PCDifficultyBeatmap
        {
            public string _beatmapFilename;
            public float _noteJumpMovementSpeed;
            public float _noteJumpStartBeatOffset;
            public int _difficulty;
            public string _difficultyRank;
            public string _difficultyLabel;
        }

        /// <summary>
        /// PC beatmap JSON structure
        /// </summary>
        [System.Serializable]
        public class PCBeatmapJson
        {
            public float _time;
            public float _BPM;
            public float _rotation;
            public float _translation;
            public List<PCNote> _notes;
            public List<PCBomb> _bombs;
            public List<PCObstacle> _obstacles;
            public List<PCEvent> _events;
        }

        [System.Serializable]
        public class PCNote
        {
            public float _time;
            public int _lineIndex;
            public int _lineLayer;
            public int _noteType;
            public int _cutDirection;
        }

        [System.Serializable]
        public class PCBomb
        {
            public float _time;
            public int _lineIndex;
            public int _lineLayer;
        }

        [System.Serializable]
        public class PCObstacle
        {
            public float _time;
            public float _duration;
            public int _lineIndex;
            public int _lineLayer;
            public int _type;
            public int _width;
            public int _height;
        }

        [System.Serializable]
        public class PCEvent
        {
            public float _time;
            public int _type;
            public int _value;
        }

        /// <summary>
        /// Main conversion function
        /// </summary>
        public bool ConvertSong()
        {
            if (string.IsNullOrEmpty(inputSongPath) || !Directory.Exists(inputSongPath))
            {
                Debug.LogError($"Input path not found: {inputSongPath}");
                return false;
            }

            // Find info.dat
            string infoPath = FindFile(inputSongPath, new[] { "info.dat", "info.json" });
            if (infoPath == null)
            {
                Debug.LogError("No info.dat found");
                return false;
            }

            // Parse info
            string infoJson = File.ReadAllText(infoPath);
            var info = JsonUtility.FromJson<PCInfoDat>(infoJson);

            Debug.Log($"Converting: {info._songName} by {info._songAuthorName}");
            Debug.Log($"BPM: {info._beatsPerMinute}");

            // Create output directory
            if (!string.IsNullOrEmpty(outputSongPath))
            {
                Directory.CreateDirectory(outputSongPath);
            }

            // Convert each difficulty
            int convertedCount = 0;

            // Process from difficultyBeatmapSets (new format)
            if (info._difficultyBeatmapSets != null)
            {
                foreach (var set in info._difficultyBeatmapSets)
                {
                    if (set._difficultyBeatmaps == null) continue;

                    foreach (var diff in set._difficultyBeatmaps)
                    {
                        if (ConvertDifficulty(inputSongPath, diff, info))
                            convertedCount++;
                    }
                }
            }

            // Process from difficultyBeatmaps (old format)
            if (info._difficultyBeatmaps != null)
            {
                foreach (var diff in info._difficultyBeatmaps)
                {
                    if (ConvertDifficulty(inputSongPath, diff, info))
                        convertedCount++;
                }
            }

            Debug.Log($"Converted {convertedCount} difficulties");
            return convertedCount > 0;
        }

        bool ConvertDifficulty(string songPath, PCDifficultyBeatmap diff, PCInfoDat info)
        {
            string beatmapPath = Path.Combine(songPath, diff._beatmapFilename);
            if (!File.Exists(beatmapPath))
            {
                Debug.LogWarning($"Beatmap not found: {beatmapPath}");
                return false;
            }

            // Read PC format
            string beatmapJson = File.ReadAllText(beatmapPath);
            var pcBeatmap = JsonUtility.FromJson<PCBeatmapJson>(beatmapJson);

            if (pcBeatmap == null)
            {
                Debug.LogWarning($"Failed to parse: {beatmapPath}");
                return false;
            }

            // Create PS4 format (custom binary format)
            string outputName = Path.GetFileNameWithoutExtension(diff._beatmapFilename) + ".dat";
            string outputPath = Path.Combine(outputSongPath, outputName);

            WritePS4DatFile(outputPath, pcBeatmap, info);
            Debug.Log($"  -> {outputName}: {pcBeatmap._notes?.Count ?? 0} notes");

            return true;
        }

        /// <summary>
        /// Write PS4 beatmap .dat file
        /// Format: Binary with header + note/bomb/obstacle/event data
        /// </summary>
        void WritePS4DatFile(string path, PCBeatmapJson pcBeatmap, PCInfoDat info)
        {
            using (var ms = new MemoryStream())
            using (var writer = new BinaryWriter(ms))
            {
                // Header
                writer.Write(System.Text.Encoding.ASCII.GetBytes("BSGD")); // Magic: Beat Saber Game Data
                writer.Write((byte)1); // Version
                writer.Write((byte)0); // Reserved

                // Song info
                WriteString(writer, info._songName ?? "");
                WriteString(writer, info._songSubName ?? "");
                WriteString(writer, info._songAuthorName ?? "");
                WriteString(writer, info._levelAuthorName ?? "");
                writer.Write(info._beatsPerMinute);
                writer.Write(info._previewStartTime);
                writer.Write(info._previewDuration);
                writer.Write(info._songTimeOffset);
                writer.Write(info._shuffle);
                writer.Write(info._shufflePeriod);
                WriteString(writer, info._environmentName ?? "DefaultEnvironment");

                // Beatmap data
                int noteCount = pcBeatmap._notes?.Count ?? 0;
                int bombCount = pcBeatmap._bombs?.Count ?? 0;
                int obstacleCount = pcBeatmap._obstacles?.Count ?? 0;
                int eventCount = pcBeatmap._events?.Count ?? 0;

                writer.Write(noteCount);
                writer.Write(bombCount);
                writer.Write(obstacleCount);
                writer.Write(eventCount);

                // Notes
                if (pcBeatmap._notes != null)
                {
                    foreach (var note in pcBeatmap._notes)
                    {
                        writer.Write(note._time);
                        writer.Write((byte)note._lineIndex);
                        writer.Write((byte)note._lineLayer);
                        writer.Write((byte)note._noteType);
                        writer.Write((byte)note._cutDirection);
                    }
                }

                // Bombs
                if (pcBeatmap._bombs != null)
                {
                    foreach (var bomb in pcBeatmap._bombs)
                    {
                        writer.Write(bomb._time);
                        writer.Write((byte)bomb._lineIndex);
                        writer.Write((byte)bomb._lineLayer);
                    }
                }

                // Obstacles
                if (pcBeatmap._obstacles != null)
                {
                    foreach (var obs in pcBeatmap._obstacles)
                    {
                        writer.Write(obs._time);
                        writer.Write(obs._duration);
                        writer.Write((byte)obs._lineIndex);
                        writer.Write((byte)obs._lineLayer);
                        writer.Write((byte)obs._type);
                        writer.Write((byte)obs._width);
                        writer.Write((byte)obs._height);
                    }
                }

                // Events
                if (pcBeatmap._events != null)
                {
                    foreach (var evt in pcBeatmap._events)
                    {
                        writer.Write(evt._time);
                        writer.Write((ushort)evt._type);
                        writer.Write((ushort)evt._value);
                    }
                }

                // Write to file
                File.WriteAllBytes(path, ms.ToArray());
            }
        }

        void WriteString(BinaryWriter writer, string s)
        {
            byte[] bytes = System.Text.Encoding.UTF8.GetBytes(s ?? "");
            writer.Write((ushort)bytes.Length);
            if (bytes.Length > 0)
                writer.Write(bytes);
        }

        string FindFile(string dir, string[] names)
        {
            foreach (var name in names)
            {
                string path = Path.Combine(dir, name);
                if (File.Exists(path))
                    return path;
            }
            return null;
        }
    }
}
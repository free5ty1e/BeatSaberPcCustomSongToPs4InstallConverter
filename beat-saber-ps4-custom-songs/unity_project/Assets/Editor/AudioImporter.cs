using UnityEngine;
using UnityEditor;
using System.IO;

namespace BeatSaber.Editor
{
    /// <summary>
    /// Helper for importing audio files as OGG Vorbis
    /// </summary>
    public static class AudioImporter
    {
        private const string MENU_PATH = "BeatSaber/";

        /// <summary>
        /// Imports all audio files in the Audio folder with correct settings
        /// </summary>
        [MenuItem(MENU_PATH + "Import Audio Files")]
        public static void ImportAudioFiles()
        {
            string audioPath = Path.Combine(Application.dataPath, "Audio");

            if (!Directory.Exists(audioPath))
            {
                Directory.CreateDirectory(audioPath);
                Debug.Log("Created Audio folder. Place your OGG files there and try again.");
                return;
            }

            string[] audioFiles = Directory.GetFiles(audioPath, "*.*");
            int imported = 0;

            foreach (string file in audioFiles)
            {
                string extension = Path.GetExtension(file).ToLower();
                if (extension == ".ogg" || extension == ".wav" || extension == ".mp3")
                {
                    ImportAudioFile(file);
                    imported++;
                }
            }

            Debug.Log($"Imported {imported} audio files.");
            AssetDatabase.Refresh();
        }

        /// <summary>
        /// Imports a single audio file with Beat Saber compatible settings
        /// </summary>
        public static void ImportAudioFile(string filePath)
        {
            AudioImporterPostProcess.isImporting = true;

            AssetDatabase.ImportAsset(
                Path.Combine("Assets", "Audio", Path.GetFileName(filePath)),
                ImportAssetOptions.ImportRecursive
            );

            AudioImporterPostProcess.isImporting = false;
        }
    }

    /// <summary>
    /// Post-processor for imported audio files
    /// </summary>
    public class AudioImporterPostProcess : AssetPostprocessor
    {
        public static bool isImporting = false;

        void OnPreprocessAudio()
        {
            if (!isImporting) return;

            AudioImporterSettings();
        }

        /// <summary>
        /// Configure audio import settings for Beat Saber
        /// </summary>
        public void AudioImporterSettings()
        {
            AudioImporter importer = assetImporter as AudioImporter;

            if (importer == null) return;

            // Create serializeable settings
            var settings = new SerializedObject(importer);

            // Get the audio settings
            AudioImporterSampleSettings sampleSettings = importer.defaultSampleSettings;

            // Set for PS4 (Audio3D = false, ForceToMono = false for stereo)
            sampleSettings.loadType = AudioClipLoadType.CompressedInMemory;
            sampleSettings.compressionBitrate = 128000; // 128 kbps
            sampleSettings.sampleRateSetting = AudioSampleRateSetting.Override;
            sampleSettings.sampleRateOverride = 44100;

            importer.defaultSampleSettings = sampleSettings;

            // Set to Vorbis compression
            SerializedProperty format = settings.FindProperty("m_CompressionFormat");
            if (format != null)
            {
                // OGG Vorbis format for PS4
                format.intValue = 1; // Vorbis
            }

            settings.ApplyModifiedProperties();

            Debug.Log($"Configured audio: {assetPath}");
        }
    }
}
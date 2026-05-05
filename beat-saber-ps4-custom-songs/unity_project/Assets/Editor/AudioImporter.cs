using UnityEngine;
using UnityEditor;
using System.IO;

namespace BeatSaber.Editor
{
    /// <summary>
    /// Helper for importing audio files with correct settings for Beat Saber
    /// </summary>
    public static class AudioImporterHelper
    {
        private const string MENU_PATH = "BeatSaber/";

        /// <summary>
        /// Imports all audio files in the Audio folder
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
                    ImportAudioFile(Path.Combine("Assets", "Audio", Path.GetFileName(file)));
                    imported++;
                }
            }

            Debug.Log($"Imported {imported} audio files. Reimport to apply settings.");
            AssetDatabase.Refresh();
        }

        /// <summary>
        /// Imports a single audio file
        /// </summary>
        public static void ImportAudioFile(string assetPath)
        {
            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ImportRecursive);
        }

        /// <summary>
        /// Opens the audio folder in file explorer
        /// </summary>
        [MenuItem(MENU_PATH + "Open Audio Folder")]
        public static void OpenAudioFolder()
        {
            string audioPath = Path.Combine(Application.dataPath, "Audio");
            audioPath = Path.GetFullPath(audioPath);

            if (Directory.Exists(audioPath))
            {
                EditorUtility.RevealInFinder(audioPath);
            }
            else
            {
                Debug.LogWarning($"Audio folder does not exist: {audioPath}");
            }
        }
    }
}
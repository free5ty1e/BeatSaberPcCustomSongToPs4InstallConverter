using UnityEngine;

namespace BeatSaber
{
    /// <summary>
    /// Simple test script to verify audio playback
    /// Attach to a GameObject with CustomBeatmapLevel and AudioSource
    /// </summary>
    [RequireComponent(typeof(AudioSource))]
    public class TestAudioPlayback : MonoBehaviour
    {
        public CustomBeatmapLevel level;
        private AudioSource audioSource;

        void Start()
        {
            audioSource = GetComponent<AudioSource>();

            if (level != null && level.audioClip != null)
            {
                audioSource.clip = level.audioClip;
                audioSource.Play();

                Debug.Log($"Playing: {level.songName} by {level.artistName}");
                Debug.Log($"Duration: {level.GetDuration():F2} seconds");
                Debug.Log($"BPM: {level.beatsPerMinute}");
            }
        }

        void OnGUI()
        {
            if (audioSource != null && audioSource.clip != null)
            {
                GUILayout.BeginArea(new Rect(10, 10, 400, 200));
                GUILayout.Label($"Now Playing: {level.songName}");
                GUILayout.Label($"Artist: {level.artistName}");
                GUILayout.Label($"Time: {audioSource.time:F2}s / {audioSource.clip.length:F2}s");
                GUILayout.Label($"BPM: {level.beatsPerMinute}");

                if (GUILayout.Button(audioSource.isPlaying ? "Pause" : "Play"))
                {
                    if (audioSource.isPlaying)
                        audioSource.Pause();
                    else
                        audioSource.Play();
                }
                GUILayout.EndArea();
            }
        }
    }
}
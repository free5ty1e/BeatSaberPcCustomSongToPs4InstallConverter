#!/bin/bash
set -e
# Build and deploy Billie Eilish (10 songs) + Lizzo (9 songs) replacements
# Uses the new --download-beat-saver-song feature? No, these songs are already in songs_repo.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE="$SCRIPT_DIR/tools/full_custom_song_pipeline.py"
REPO="/workspace/beat-saber-ps4-custom-songs/songs_repo"
OUTPUT="$SCRIPT_DIR/custom_songs"
mkdir -p "$OUTPUT"

# Billie Eilish replacements
echo "========================================="
echo "BILLIE EILISH REPLACEMENTS (10 songs)"
echo "========================================="
python3 "$PIPELINE" \
  --song-dir "$REPO/0901401f822780455b3b5c9bc19e0e4fb5db052d" \
  --target Oxytocin --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/1817d1ec44a290e011da0c3ffdb4edb1dc17e6cd" \
  --target AllTheGoodGirlsGoToHell --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/25b991cb87f42fedcb2399467b074edf6b9e679e" \
  --target YouShouldSeeMeInACrown --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/1a057b9429d30189aabe4fe0267822ad0ca7b5ae" \
  --target Bellyache --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/49f84e9bfea5347c7c0aca9da186bd44b04f4001" \
  --target BuryAFriend --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/2862f1a372a3823b2dcf194806aa0e8564bbbc98" \
  --target IDidntChangeMyNumber --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/70b3c82ce7536982ae9dd21f52e489d7c28ebbe2" \
  --target HappierThanEver --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/fcbff07e31726bae1fdae413de16aae1be68d537" \
  --target BadGuy --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/81970cd2d5d3b2dff908e6569648a9a51e494e65" \
  --target NDA --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/559113d5c4247438c6ecad852c61d03d79396af1" \
  --target ThereforeIAm --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

# Lizzo replacements
echo "========================================="
echo "LIZZO REPLACEMENTS (9 songs)"
echo "========================================="
python3 "$PIPELINE" \
  --song-dir "$REPO/0298808e5c8824f4a15bc9583a38bac2579740b3" \
  --target 2BeLoved --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/4b980371b6005cc176aed1b402bd104af56c31a3" \
  --target AboutDamnTime --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/4cb323a4340177d7b7ca74f67f6b920ed320ee5e" \
  --target CuzILoveYou --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/52a40af5926b64e029c8f0bac119535b4bc647b7" \
  --target EverybodysGay --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/368cf6a8e58b7823fd612a52d6de024287ad3e11" \
  --target GoodAsHell --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/9a022b3e3a48955691792d40e8fcd53678d2b51a" \
  --target Juice --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/71eff19ed6d32fd0a446e1a32303c77aa7f646f2" \
  --target Tempo --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/65e482f3a7dd9da533c8bb1702f725e98f7636ef" \
  --target TruthHurts --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

python3 "$PIPELINE" \
  --song-dir "$REPO/6b253cbb5a2a81c2575e0778614bf009d7954834" \
  --target Worship --pcm16 --no-pad --convert-to-v3 --deploy --generate-config --deploy-config

echo ""
echo "========================================="
echo "✅ ALL 19 SONGS BUILT AND DEPLOYED!"
echo "   Restart Beat Saber on PS4 to test"
echo "========================================="

FOLDER="$1"
NAME="$2"
ffmpeg -framerate 60 -pattern_type glob -i "$FOLDER/*.png" -c:v prores -pix_fmt yuv420p "/Volumes/OPTIPHONIC/CLIPS/TF24/PRORES/$NAME"
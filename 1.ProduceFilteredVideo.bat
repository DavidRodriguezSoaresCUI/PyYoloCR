vspipe -y YoloAIO.vpy - | ffmpeg -i - -c:v mpeg4 -qscale:v 3 -y Filtered_video.mp4
echo Done ! Check there was no error.
pause
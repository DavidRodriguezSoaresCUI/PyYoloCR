#!/bin/bash

# First, check if youtube-dl, vspipe and ffmpeg are installed
if ! command -v youtube-dl &> /dev/null
then
    echo "youtube-dl could not be found ! Please install it and retry."
    exit
fi
if ! command -v vspipe &> /dev/null
then
    echo "vspipe could not be found ! Please install it and retry."
    exit
fi
if ! command -v ffmpeg &> /dev/null
then
    echo "ffmpeg could not be found ! Please install it and retry."
    exit
fi
echo "youtube-dl, vspipe and ffmpeg found !"
echo " "

# Downloading test videos
if ! [[ -e 1.mp4 ]]; then
    
    echo "Downloading test videos .."
    youtube-dl --quiet --output 1.mp4 https://vimeo.com/192424808
    if ! [[ -e 1.mp4 ]]; then
        echo "Failed to download video 1."
        exit
    fi
    echo "Downloading test videos OK !";
else
    echo "Test videos already there !"
fi
echo " "

# Downloading SubXtract and YoloCR
if ! [[ -e pyyolocr && -e yolocr ]]; then
    echo "Downloading SubXtract and YoloCR .."
    git clone -q https://gitlab.com/DRSCUI/pyyolocr.git 2> /dev/null
    git clone -q https://bitbucket.org/YuriZero/yolocr.git 2> /dev/null
    echo "Downloading SubXtract and YoloCR OK";
else
    echo "SubXtract and YoloCR already there !"
fi
echo " "

if ! [[ -e eng.traineddata ]]; then
    echo "Downloading Tesseract eng.traineddata .."
    curl https://raw.githubusercontent.com/tesseract-ocr/tessdata/master/eng.traineddata  > ./eng.traineddata
    if ! [[ -e eng.traineddata ]]; then
        echo "Failed to download eng.traineddata ."
        exit
    fi
    echo "Downloading Tesseract eng.traineddata OK"
fi
# Putting language data in dedicated directories
if ! [[ -e yolocr/tessdata/eng.traineddata ]]; then
    mkdir yolocr/tessdata &> /dev/null
    cp eng.traineddata yolocr/tessdata/eng.traineddata
fi
if ! [[ -e pyyolocr/tessdata/eng.traineddata ]]; then
    mkdir pyyolocr/tessdata &> /dev/null
    cp eng.traineddata pyyolocr/tessdata/eng.traineddata
fi
echo " "  

# Producing filtered videos vrom VPY scripts
if ! [[ -e yolocr/Filtered_video.mp4 ]]; then
    echo "Producing video for YoloCR .."
    vspipe -y YoloCR.vpy - | ffmpeg -i - -c:v mpeg4 -qscale:v 3 -y yolocr/Filtered_video.mp4 &> /dev/null
    echo "Producing video for YoloCR OK"
    mv SceneChanges.log yolocr/SceneChanges.log
fi
if ! [[ -e pyyolocr/Filtered_video.mp4 ]]; then
    echo "Producing video for SubXtract .."
    vspipe -y YoloAIO.vpy - | ffmpeg -i - -c:v mpeg4 -qscale:v 3 -y pyyolocr/Filtered_video.mp4 &> /dev/null
    echo "Producing video for SubXtract OK"
    mv stat_nonblackframes.log pyyolocr/stat_nonblackframes.log
    mv stat_scenechanges.log pyyolocr/stat_scenechanges.log
fi

function separator {
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
}


cd yolocr
separator
echo "Running YoloCR .."
separator
time ./YoloCR.sh Filtered_video.mp4 eng
separator
echo "Running YoloCR OK"
separator
cd ..
mv yolocr/Filtered_video.srt 1.yolocr.srt


cd pyyolocr
separator
echo "Running SubXtract .."
separator
time python3 ./YoloCRMod.py --engine legacy -l eng --overwrite
separator
echo "Running SubXtract OK"
separator
cd ..
mv pyyolocr/output.legacy.eng.srt 1.subxtract.srt



echo "End of program"
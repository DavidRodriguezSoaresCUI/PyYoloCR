# [PyYoloCR](https://gitlab.com/DRSCUI/pyyolocr)

## About PyYoloCR
This is a Bash $\to$ Python 3.6+ re-implementation of the original [YoloCR](https://bitbucket.org/YuriZero/yolocr/src) by bitbucket user YuriZero (specifically at commit [7dd128c](https://bitbucket.org/YuriZero/yolocr/commits/7dd128c61a75578380572d5def65b804814e82e9))

### Why go through the trouble of re-implementing working software ?
I needed an easy, low effort and automated way to extract hardcoded subtitles (subtitles in the video stream, not in a dedicated subtitle stream). There are multiple open-source projects that share the same user need and I tried some with little success, so I chose __YoloCR__ as a base and modded it.

### Key improvements
 * __OCR performance__ : The original implementation made compromises to lower _time complexity_ (focus on speed) that could cripple _accuracy_, rendering its ouput useless or requiring a lot of manual cleanup. __PyYoloCR__ sacrifices _speed_ for better _accuracy_.
 * __Maintainability__ : While the original `bash` code is functional and compact, it's arguably harder to maintain than a program written in a high-level language

## Requirements

* [FFmpeg](https://ffmpeg.org/) : should be callable from the command line
* Vapoursynth R36+
	* plugins for Vapoursynth: 
		* [FFMS2](https://github.com/FFMS/ffms2)
		* [HAvsFunc](http://forum.doom9.org/showthread.php?t=166582), requires [mvsfunc](http://forum.doom9.org/showthread.php?t=172564) and [adjust](https://github.com/dubhater/vapoursynth-adjust)
		* [fmtconv](http://forum.doom9.org/showthread.php?t=166504)
		* *optional*: [edi_rpow2](http://forum.doom9.org/showthread.php?t=172652), requires [znedi3](https://github.com/sekrit-twc/znedi3)
		* *very optional*: [Waifu2x-w2xc](http://forum.doom9.org/showthread.php?t=172390)
	* note:
		* Vapoursynth plugins (.so on Unix, .dll on Windows) should be placed inside one of theses directories: http://www.vapoursynth.com/doc/autoloading.html
		* Vapoursynth scripts (.py) should be placed inside the "site-packages" directory of your Python3 installation.
* [Vapoursynth Editor](https://bitbucket.org/mystery_keeper/vapoursynth-editor)
* OCR tool : for now only [Tesseract](https://github.com/tesseract-ocr/tesseract) is supported. Windows users can find binaries [here](https://github.com/UB-Mannheim/tesseract/wiki).

### Unix/Linux Requirements

__Note__ : For Ubuntu 20.04, all the requirements can be installed with the YoloBuntuInstallation script : `sh YoloBuntuInstallation.sh`

* Tesseract-OCR (version 4 recommended)
	* and install the data corresponding to the languages you want to OCR
	* Imagemagick is required if you use LSTM engine
* sxiv (Simple X Image Viewer) (GUI mode only)
* xdotool (Linux only, GUI mode only)

> *Note*: most of these package, with the exception of all the plugins for vapoursynth, are available as official package for your distro.

> For Ubuntu, *vapoursynth*, *vapoursynth-editor* and  *vapoursynth-extra-plugins* (to install all the mandatory plugins above) are available through this ppa: [`ppa:djcj/vapoursynth`](https://launchpad.net/~djcj/+archive/ubuntu/vapoursynth)

### Windows Requirements
 * FFmpeg : Download "ffmpeg-git-full.7z" from [this page](https://www.gyan.dev/ffmpeg/builds/) and follow [this tutorial](https://www.thewindowsclub.com/how-to-install-ffmpeg-on-windows-10) for installation instructions.
 
 * Vapoursynth : Follow [these instructions](http://www.vapoursynth.com/doc/installation.html), which includes installing a recent version of `Python`.
	* When installing `Python`, make sure to check the `Install for all users` and `Add to PATH` boxes, and restart your computer for changes to take effect.

 * Vapoursynth Editor : You can find the latest portable binaries from [its official download page](https://bitbucket.org/mystery_keeper/vapoursynth-editor/downloads/). No install needed, just decompress it !

 * Tesseract : You can find installers [here](https://github.com/UB-Mannheim/tesseract/wiki).

## How to use?

### Help for determining the parameters for the `YoloCR.vpy` file

#### Determine the Resize parameters.

Resize is very helpful to locate the subtitles.

1. open `YoloResize.vpy` in Vapoursynth Editor.
2. Change this value:
	* `FichierSource` is the path of the video to OCR.
	* `DimensionCropbox` allows you to limit the OCR zone.
	* `HauteurCropBox` allows you to define the height of the Cropbox's bottom border.

> Note that theses two parameters have to be adjusted before upscale.

You can then change `Supersampling` parameter to -1 and verify that your subtitles aren't eated by the white borderline by using **F5**.

#### Determine the threshold of the subtitles

It's to improve the OCR-process and the subtitles detection.

1. Open `YoloSeuil.vpy` in Vapoursynth editor.
2. Report `FichierSource`, `DimensionCropBox` and `HauteurCropBox` you have defined in the `Resize` file.
3. Choose the fitting ModeS. 'L' if you want to define a white or black threshold, succesively 'R', 'G' and 'B' otherwise.
4. Adjust the Threshold with the help of the "Color Panel" found in the **F5** window.

You must to do this two times if you are using ModeS=L:

* in the first case, the Inline threshold will be the minimum.
* in the second case, the Outline threshold will be the maximum.

You can then change `Seuil` paremeter to the values previously found.

* in the first case, the subtitles must remain completely visible. The highest the value, the better.
* in the second case, the Outline must remain completely black. The lowest the value, the better.

### Filter the video

1. Edit the first lines in `YoloCR.vpy` thanks to the two previos steps (and the previous file `YoloSeuil.vpy`).
	* SeuilI = the inline threshold value (decrease it if it improves the clarity of the letters)
	* SeuilO = the outline threshold value (increase it if some letters got erased)
 
2. Then filter it: `vspipe -y YoloCR.vpy - | ffmpeg -i - -c:v mpeg4 -qscale:v 3 -y nameOftheVideoOutput.mp4`

> Be careful: your must use a different name for your `FichierSource` in the previous files and `nameOftheVideoOutput.mp4` for the output of the ffmpeg command.

You now have an OCR-isable video and scenechange informations.

### OCR the video

Then you can OCR the video: `./YoloCR.sh nameOftheVideoOutput.mp4`

> The `nameOftheVideoOutput.mp4` must be the same than the output of the ffmpeg command.

> You can use `YoloTime.sh` instead of `YoloCR.sh` if you only want the Timing of the subtitles.

**Now it's Checking time :D**

## Serial use of YoloCR

1. Make sure that sxiv isn't installed.
2. Make sure that YoloCR directory includes the video files you want to OCR and only theses.
3. Comment the first line of YoloCR.vpy. ("FichierSource" becomes "#FichierSource".)
4. Move to the YoloCR directory and use this bash command:
	* `for file in *.mp4; do filef="${file%.*}_filtered.mp4"; vspipe -y --arg FichierSource="$file" YoloCR.vpy - | ffmpeg -i - -c:v mpeg4 -qscale:v 3 -y "$filef"; ./YoloCR.sh "$filef"; done`

> "*.mp4" means that all files having the mp4 extension will be processed. Read about bash regex if you want more flexibility.

## Known bugs

* Tesseract's LSTM engine produce a lower quality OCR (such as a worse italics detection).
	* Use Legacy engine [traineddata](https://github.com/tesseract-ocr/tessdata) instead.
	* You can put these files inside YoloCR's tessdata directory.
* Cygwin (Windows), when you run YoloCR.sh for the first time.
	* Signal SIGCHLD received, but no signal handler set.
	* YoloCR will run without errors the next times.
* Babun (Windows), you will have errors when trying to run YoloCR.sh.
	* Use Cygwin instead.

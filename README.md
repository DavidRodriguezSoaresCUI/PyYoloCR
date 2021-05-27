# [PyYoloCR](https://gitlab.com/DRSCUI/pyyolocr)

## About PyYoloCR
This is a Bash -> Python 3.6+ re-implementation of the [original YoloCR](https://bitbucket.org/YuriZero/yolocr/src) by bitbucket user `YuriZero` (specifically at commit [7dd128c](https://bitbucket.org/YuriZero/yolocr/commits/7dd128c61a75578380572d5def65b804814e82e9))

### Why go through the trouble of re-implementing working software ?
I needed an easy, low effort and automated way to extract hardcoded subtitles (subtitles in the video stream, not in a dedicated subtitle stream). There are multiple open-source projects that share the same user need and I tried some with little success, so I chose __YoloCR__ as a base and modded it.

### Key improvements
 * __OCR performance__ : The original implementation made compromises to lower _time complexity_ (focus on speed) that could cripple _accuracy_, rendering its ouput useless or requiring a lot of manual cleanup. __PyYoloCR__ sacrifices _speed_ for better _accuracy_.
 * __Maintainability__ : While the original `bash` code is functional and compact, it's arguably harder to maintain than a program written in a high-level language
 * __Cross-compatibility__ : Not relying on `Bash` and other linux-y dependences means it can be ported more easily. Specifically I focused on making it `Windows`-friendly.

# Requirements

* [FFmpeg](https://ffmpeg.org/) : should be callable from the command line
* Vapoursynth R36+
	* plugins for Vapoursynth: 
		* [FFMS2](https://github.com/FFMS/ffms2)
		* [HAvsFunc](http://forum.doom9.org/showthread.php?t=166582), requires [mvsfunc](http://forum.doom9.org/showthread.php?t=172564) and [adjust](https://github.com/dubhater/vapoursynth-adjust)
		* [fmtconv](http://forum.doom9.org/showthread.php?t=166504)
		* *optional*: [edi_rpow2](http://forum.doom9.org/showthread.php?t=172652), requires [znedi3](https://github.com/sekrit-twc/znedi3)
		* *very optional*: [Waifu2x-w2xc](http://forum.doom9.org/showthread.php?t=172390)
	* _Note for manual installs_: `Vapoursynth` plugins (.so on Unix, .dll on Windows) should be placed inside one of theses directories: http://www.vapoursynth.com/doc/autoloading.html and `Vapoursynth` python scripts (.py) should be placed inside the "site-packages" directory of your Python3 installation.
* [Vapoursynth Editor](https://bitbucket.org/mystery_keeper/vapoursynth-editor)
* OCR tool : for now only [Tesseract](https://github.com/tesseract-ocr/tesseract) is supported.

## Unix/Linux Requirements / Install

__Note__ : For Ubuntu 20.04, all the requirements can be installed with the YoloBuntuInstallation script : `sh YoloBuntuInstallation.sh`

* Tesseract-OCR (version 4 recommended)
	* and install the data corresponding to the languages you want to OCR
	* Imagemagick is required if you use LSTM engine
* sxiv (Simple X Image Viewer) (GUI mode only)
* xdotool (Linux only, GUI mode only)

> *Note*: most of these package, with the exception of all the plugins for vapoursynth, are available as official package for your distro.

> For Ubuntu, *vapoursynth*, *vapoursynth-editor* and  *vapoursynth-extra-plugins* (to install all the mandatory plugins above) are available through this ppa: [`ppa:djcj/vapoursynth`](https://launchpad.net/~djcj/+archive/ubuntu/vapoursynth)

## Windows Requirements / Install
It is recommended to install the following dependencies in the given order.

 * FFmpeg : Download "ffmpeg-git-full.7z" from [this page](https://www.gyan.dev/ffmpeg/builds/) and follow [this tutorial](https://www.thewindowsclub.com/how-to-install-ffmpeg-on-windows-10) for installation instructions.
	* Successful installation can be verified by opening a terminal, typing `ffmpeg` and confirming ffmpeg ouputs text. 
 
 * Vapoursynth : Follow [these instructions](http://www.vapoursynth.com/doc/installation.html), which includes installing a recent version of `Python` beforehand. Do not choose the portable version.
	* It is recommended to install it for all users. To be able to do that, when installing `Python`, make sure to choose `Customize installation`, then check the `Install for all users` and `Add to PATH`/`Add Python to environment variables` boxes. Otherwise `VapourSynth` will not be able to be installed for all users since it depends on `Python`.
	* A `Microsoft Defender SmartScreen` message box may appear when trying to launch the VapourSynth installer. Ignore this by clicking on `Complementary information`, then `Execute anyway`.

 * Vapoursynth Editor : You can find the latest portable binaries from [its official download page](https://bitbucket.org/mystery_keeper/vapoursynth-editor/downloads/). No install needed, just decompress it !
	* For ease of use, it is recommended to make a desktop shortcut by right-clicking on `vsedit.exe` and selecting `send to -> Desktop (add shortcut)`.

 * Tesseract : You can find installers [here](https://github.com/UB-Mannheim/tesseract/wiki).
	* Support for OCR languages can be added at installation or later (see section `Adding OCR language support`)

	* You need to add `C:\Program Files\Tesseract-OCR` to your system PATH environment variable in order to call `Tesseract` from the command line.

__Note__ : There is a helper script (`0.WinAutoInstall.bat`) that automates the installation of required `VapourSynth` filters/plugins and `Python` libraries. It must be launched with admin privileges __AFTER ALL__ previous dependencies are properly installed or it may fail.
> __Warning__ : You need to have associated `.py` files with `Python` on your machine before running this script or it will fail installing plugins ! Simply right-click a file ending in `.py` -> Properties -> Open with -> Python (check "always use" checkbox if present)

# How to use?

## Basics
1. Preprocessing : Adjust parameters in `YoloAIO.vpy`, so the output is optimal for OCR.
	* Next step needs variable `Step` to be set to 3.
2. Generate filtered video with `1.ProduceFilteredVideo` script.
3. Use `2.LaunchYoloCRMod` script to extract frames, OCR them and generate a subtitle file.

## Help for determining the parameters for the `YoloAIO.vpy` file
0. Open `YoloAIO.vpy` in Vapoursynth Editor and set value `VideoSrc` to the path of the video file from which you want to extract subtitles.
1. 'Resize' step : Set `Step` to 1 and adjust these values:
	* `DimensionCropbox` determines the width/height of the bounding box.
	* `HauteurCropBox` determines the vertical position of the bounding box.
	* In this step, you are to choose values such that any subtitles are within the bounding box.
2. 'Threshold' step : Set `Step` to 2 and adjust these values:
	* Choose the fitting `ModeS` : 'L' if you want to define a white or black threshold, succesively 'R', 'G' and 'B' otherwise.
	* `SeuilI` : the inline threshold value (decrease it if it improves the clarity of the letters)
	* `SeuilO` : the outline threshold value (increase it if some letters got erased)
	* Note : `SeuilO` < `SeuilI`
	* Adjust the Threshold with the help of the "Color Panel" found in the **F5** window.
3. 'OCR' step : Set `Step` to 3 and verify that previously set values capture all the subtitles and minimize artifacts
	* Typically you will play with `SeuilO` and `SeuilI` to maximise subtitle clarity and minimize artifacts.

# Known bugs
Please tell me if you find one !

* [_Written by `YuriZero` for the original YoloCR, in my testing I sometimes found the LSTM engine to be superior in accuracy_] Tesseract's LSTM engine produce a lower quality OCR (such as a worse italics detection).
	* Use Legacy engine [traineddata](https://github.com/tesseract-ocr/tessdata) instead.
	* You can put these files inside YoloCR's `./tessdata` directory.

# Possible improvements
I don't really take feature requests, so you may need to do it yourself. These are just a few feature ideas for forks.

 * Add support for [ABBYY FineReader](https://pdf.abbyy.com) as alternative OCR engine, because apparently it's a popular (Windows-specific) and viable alternative to `Tesseract`.
 * Add _italics_ detection : originally in YoloCR and scrapped in PyYoloCR.

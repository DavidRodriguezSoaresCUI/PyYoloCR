# [SubXtract](https://gitlab.com/DRSCUI/pyyolocr)

## About SubXtract
This software aims at offering a __simple__, __easy__ and mostly __automated__ way of __extracting hardcoded subtitles__ (burned into the video stream) from a video.

This is not only a Bash -> Python 3.6+ re-implementation of the [original YoloCR](https://bitbucket.org/YuriZero/yolocr/src) by bitbucket user `YuriZero` (specifically at commit [7dd128c](https://bitbucket.org/YuriZero/yolocr/commits/7dd128c61a75578380572d5def65b804814e82e9)), but also a major overhaul of most of the code.


### Why go through the trouble of re-implementing/modding working software ?
I needed an easy, low effort and automated way to extract hardcoded subtitles (subtitles in the video stream, not in a dedicated subtitle stream). There are multiple open-source projects that share the same user need and I tried some with little success, so I chose __YoloCR__ as a base and modded it.

### Key improvements
 * __OCR performance__ : The original implementation made compromises to lower _time complexity_ (focus on speed) that could cripple _accuracy_, rendering its ouput useless or requiring a lot of manual cleanup. __PyYoloCR__ sacrifices _speed_ for better _accuracy_.
 * __Usability__ : Requires less manual input in the pre-processing and post-processing steps, and in the terminal. Also on `Windows`, doesn't requires `cygwin`-related stuff.
 * __Maintainability__ : While the original `bash` code is functional and compact, it's arguably harder to maintain than a program written in a high-level language
 * __Cross-compatibility__ : Not relying on `Bash` and other linux-y dependencies means it can be ported more easily. Specifically I focused on making it `Windows`-friendly.

# Requirements
Look below for OS-specific installation instructions.

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

For Ubuntu 20.04, all the requirements (and more because I'm lazy and didn't remove deprecated stuff from the script) can be installed with the `YoloBuntuInstallation.sh` script.

Notes:
* Tesseract-OCR (version 4 recommended)
	* and install the data corresponding to the languages you want to OCR
	* Imagemagick is required if you use LSTM engine

> *Note*: most of these package, with the exception of all the plugins for vapoursynth, are available as official package for your distro.

> For Ubuntu, *vapoursynth*, *vapoursynth-editor* and  *vapoursynth-extra-plugins* (to install all the mandatory plugins above) are available through this ppa: [`ppa:djcj/vapoursynth`](https://launchpad.net/~djcj/+archive/ubuntu/vapoursynth)

## Windows Requirements / Install
It is recommended to install the following dependencies in the given order.

[Here is a repository with all binaries/installers for 64-bit Windows in case you can't find something elsewhere.](https://gitlab.com/DRSCUI/pyyolocr-extra/-/tree/main/PyYoloCR_Win64_dependencies)

 * FFmpeg : Download "ffmpeg-git-full.7z" from [this page](https://www.gyan.dev/ffmpeg/builds/) and follow [this tutorial](https://www.thewindowsclub.com/how-to-install-ffmpeg-on-windows-10) for installation instructions.
	* Successful installation can be verified by opening a terminal, typing `ffmpeg` and confirming ffmpeg ouputs text. 
 
 * Vapoursynth : Follow [these instructions](http://www.vapoursynth.com/doc/installation.html), which includes installing a recent version of `Python` beforehand. Do not choose the portable version.
	* It is recommended to install it for all users. To be able to do that, when installing `Python`, make sure to choose `Customize installation`, then check the `Install for all users` and `Add to PATH`/`Add Python to environment variables` boxes. Otherwise `VapourSynth` will not be able to be installed for all users since it depends on `Python`.
	![Image](https://gitlab.com/DRSCUI/pyyolocr-extra/-/raw/main/img/PyInstall.png)
	* A `Microsoft Defender SmartScreen` message box may appear when trying to launch the VapourSynth installer. Ignore this by clicking on `Complementary information`, then `Execute anyway`.

 * Vapoursynth Editor : You can find the latest portable binaries from [its official download page](https://bitbucket.org/mystery_keeper/vapoursynth-editor/downloads/). No install needed, just decompress it !
	* For ease of use, it is recommended to make a desktop shortcut by right-clicking on `vsedit.exe` and selecting `send to -> Desktop (add shortcut)`.

 * Tesseract : You can find installers [here](https://github.com/UB-Mannheim/tesseract/wiki).
	* Support for OCR languages can be added at installation or later (see section `Adding OCR language support`)

	* You need to add `C:\Program Files\Tesseract-OCR` to your system PATH environment variable in order to call `Tesseract` from the command line.

__Note__ : There is a helper script (`0.WinAutoInstall.bat`) that automates the installation of required `VapourSynth` filters/plugins and `Python` libraries. It must be launched with admin privileges and __AFTER ALL__ previous dependencies are properly installed or it may fail.
> __Warning__ : You need to have associated `.py` files with `Python` on your machine before running this script or it will fail installing plugins ! Simply right-click a file ending in `.py` -> Properties -> Open with -> Python (check "always use" checkbox if present)

Your PATH should look something like that : ![Image](https://gitlab.com/DRSCUI/pyyolocr-extra/-/raw/main/img/PATH%20example.png)

# How to use

## Basics
1. Preprocessing : Adjust parameters in `YoloAIO.vpy`, so the output is optimal for OCR.
	* Next step needs variable `Step` to be set to 3.
2. Generate filtered video with `1.ProduceFilteredVideo` script.
3. Use `2.LaunchYoloCRMod` script to extract frames, OCR them and generate a `srt` subtitle file.
4. Post-processing : Use your favourite tool to _manually correct errors_ with the output subtitle file (recommended: [Aegisub](https://github.com/Aegisub/Aegisub)) : 
	* Spelling errors, malformed words, erroneous punctuation, etc
	* Remove additional "phantom" symbols (a result of OCR'ing video artifacts)
	* De-duplicate : some lines may be duplicated with slight variations. Simply join them and correct the text.
	* Re-time : Some lines may not begin/end at the right timestamp. Lines with unusually high CPS (character per second) should be considered suspicious.

## Determining the parameters for the `YoloAIO.vpy` file
You can find descriptions and advice on each parameter in `YoloAIO.vpy`, but here are the basics :

0. Open `YoloAIO.vpy` in Vapoursynth Editor and set value `VideoSrc` to the path of the video file from which you want to extract subtitles.
1. 'Resize' step : Set `Step` to 1 and adjust these values:
	* `CropBoxDimension` determines the width/height of the bounding box. Make sure it's big enough.
	* `CropBoxElevation` determines the vertical position of the bounding box.
	* In this step, you are to choose values such that any subtitles are within the bounding box.
2. 'Threshold' step : Set `Step` to 2 and adjust these values:
	* Choose the fitting `ModeS` : 'L' if you want to define a white or black threshold, succesively 'R', 'G' and 'B' otherwise.
	* `SeuilI` : the inline threshold value (decrease it if it improves the clarity of the letters)
	* `SeuilO` : the outline threshold value (increase it if some letters got erased)
	* Note : `SeuilO` < `SeuilI`
	* Adjust the Threshold with the help of the "Color Panel" found in the **F5** window.
3. 'OCR' step : Set `Step` to 3 and verify that previously set values capture all the subtitles and minimize artifacts
	* Typically you will play with `SeuilO` and `SeuilI` to maximise subtitle clarity and minimize artifacts.

For more help, check these resources (may not apply directly) : [original YoloCR's README](https://bitbucket.org/YuriZero/yolocr/src/master/), [Subbing tutorial by __subarashii-no-fansub__](https://subarashii-no-fansub.github.io/Subbing-Tutorial/OCR-Hardsub-Videos/)

## Tesseract: Adding new languages / languages that work with legacy engine
The idea is to download a language file from the [Tesseract-OCR/tessdata](https://github.com/tesseract-ocr/tessdata) repository and put it into the local `tessdata` folder. Choose the method you prefer:
* On Windows, simply use the `0.TesseractDownloadLanguage.bat` script : you type the language code (eg: 'eng' for english) and it downloads it for you.
* On Linux, type the following command from the `PyYoloCR` folder : `wget https://github.com/tesseract-ocr/tessdata/blob/master/<lang-code>.traineddata?raw=true -O tessdata/<lang-code>.traineddata` (replace `<lang-code>` by the actual language code).
* Manually as described above.


## YoloCRMod.py usage
Not used in normal usage, prefer the `2.LaunchYoloCRMod` script for your system. Optional arguments take precedent over interactively asking the user to make choices when necessary. They were mainly added for tests.
```
YoloCRMod.py [-h] [--engine {legacy,LSTM,legacy+LSTM}] [-l lang] [--overwrite]

optional arguments:
  -h, --help            show this help message and exit
  --engine {legacy,LSTM,legacy+LSTM}
                        Select Tesseract engine.
  -l lang               Select Tesseract language.
  --overwrite           Overwrite extracted frames.
```

# Known bugs
Please tell me if you find more !

* [_Written by `YuriZero` for the original `YoloCR`, in my testing I sometimes found the LSTM engine to be superior in accuracy_] Tesseract's LSTM engine produce a lower quality OCR (such as a worse italics detection).
	* Use Legacy engine [traineddata](https://github.com/tesseract-ocr/tessdata) instead.
	* You can put these files inside YoloCR's `./tessdata` directory.

* Windows : The `*.bat` scripts can fail when `*.py` files are not assigned to a `Python` interpreter (which is weird since it's called explicitely). 
	* See __Warning__ in the `Windows Requirements / Install` section or apply the same solution as the problem below.

* Windows : The `*.bat` scripts can fail when the default `Python` interpreter is not the same as the one used by `VapourSynth`. 
	* To remedy that, create a file named `Python.txt` and write in it the path of the correct interpreter (eg: `C:\Program Files\Python39\python.exe`).

* Windows : For some reason `vsrepo` may encounter issues and make `VapourSynth plugin` installation impossible through the provided `0.WinAutoInstall.bat` script. In that case the following workaround may work :
	1. [Download the compiled plugins from PyYoloCR-extra](https://gitlab.com/DRSCUI/pyyolocr-extra/-/tree/main/PyYoloCR_Win64_dependencies) and unzip it.
	2. Copy the content of `python_site-packages` the `Python` interpreter `VapourSynth` uses `site-packages` folder (eg: `C:\Program Files\Python39\Lib\site-packages`) 
	3. Copy the content of `VapourSynth_plugins` the `plugins` folder of `VapourSynth` (eg: `C:\Program Files\VapourSynth\plugins`)
		* You may need to restart your computer.
	4. Check if `VapourSynth Editor` can preview `YoloAIO.vpy` without error now.

* `VapourSynth: Failed to initialize VapourSynth environment` : see [VapourSynth's documentation](http://www.vapoursynth.com/doc/installation.html)

* `VapourSynth Editor` can crash on `Step 1` in `YoloAIO.vpy`. Please use the workaround provided there.


# General remarks
* __Tesseract-OCR engines accuracy__ : For general, clear text, both engines perform admirably well. The `legacy` engine can have more difficulties on punctuation, mostly corrected by automatic post-processing. On difficult conditions (text with artifacts due to non-text background leaking into pre-processed frames) `LSTM` engine tends to fail hard, outputing unusable text, where `legacy` usually at least finds some characters.

* __Storage__ : You need space to store the pre-processed video and the frames that will be extracted. This may require a few gigabytes.

* __Performance__ : The longest steps are, in descending order : OCR, extracting frames with FFmpeg, encoding pre-processed video. For reference, on a modern 8 core machine you should experience the following speeds, respectively : 0.5-2x, 1-3x, 10-20x

* __Naming__ : The original name of this project was __PyYoloCR__, but I found it verbose and not very "user-facingly descriptive" so it was changed to __SubXtract__, keeping the original name as _codename_.

## Compatibility
SubXtract was successfully tested on the following system configurations : `Ubuntu 20.04.2 LTS` (64bit), `Windows 20H2` and `21H1` (64-bit).

Theoretically, SubXtract _should_ work on any system that complies with requirements, but keep in mind the following : Other OSs, and architectures that are not x86-64, are UNTESTED and may exhibit issues or not work at all, and will not be developped for by me.


# Possible improvements
I don't really take feature requests, so you may need to do it yourself. These are just a few feature ideas for forks.

 * Add support for [ABBYY FineReader](https://pdf.abbyy.com) as alternative OCR engine, because apparently it's a popular (Windows-specific?) and viable alternative to `Tesseract`.
 * Add _italics_ detection : originally in `YoloCR` and scrapped in `PyYoloCR`.
 * Make the code less ugly / bad : I'm an amateur, so it's to be expected.
 * Augment subtitle post-processing filtering.


# Test suite
__Only available for bash environments (bash on Linux, WSL on windows)__

You can find a test suite in folder `tests`. Simply run `perf_test.sh` and it should be able to download a test video, extract subtitles using both `the original YoloCR` and `SubXtract`, making it easy to compare speed and OCR accuracy.

Findings (as of 02.06.2021) :
 * `SubXtract` is about 10-20 times slower than `YoloCR`
 * Both programs have very similar OCR accuracy and subtitle syncing quality. Note: this is a best-case scenario for `YoloCR`, as subtitles don't hava a fading effect applied to them.

Note : This test is only focused on demonstrating the similarities and difference in accuracy of the SRT output.

TODO : Test OCR accuracy in challenging scenarios (subtitles moving, fading, high noise, etc).

## Manual experiment
The goal of this informal experiment was to quantify the time save from using `SubXtract` instead of `YoloCR`: a reduction in manual work, mainly in the post-processing step.

I used a 16 minute clip of animation that had interesting properties : Subtitle font resembles Arial Black size 42 with a dithered outline, slightly transparent and with fade-in/out (~0.6s) effects applied.

The filtered videos contained a lot of artifacts resulting from the permissible `SeuilO/SeuilI` values necessary to catch every character. 
 
The particular nature of these subtitles was deemed appropriate to show the performance of both programs in challenging situations.


|   | SubXtract | YoloCR |
| --- | --- | --- |
| Video Pre-processing | 67s | 67s |
| Frame extraction + OCR script | 3m11s | 6s |
| Post : Removing bad lines, deduplicating | 2m20s | 2m10 |
| Post : Spelling correction (OCR mistakes only) | 1m50 | 5m30 |
| Post : Synchronization (re-timing) | ~5m | >23m |
| __"manual" sub-total__ | __~11m__ | __>32m__ |
| __TOTAL__ | __~14m__ | __>32m__ |

__Results__ : The overall reduction in manual workload is well worth the extra time the computer has to work on extracting and OCR more frames, and it was possible to mostly batch the re-timing process to cover the few frames of fade-in/out with `SubXtract`, while the same step was mostly line-by-line manual work with `YoloCR`-generated subtitles.

Note : I did not record the time to fill the VPY scripts (I took the values from `YoloAIO.vpy` and put them in `YoloCR.vpy`), but it is evident `YoloCR.vpy` version is easier to work with and slightly faster.

Note : Due to the copyrighted nature of the source material, I will not make any resource public. If you wish to replicate this test, you may have to burn subtitles onto a video


# Notice and Licensing
The software contained in this repository is the property of `David Rodriguez` ("me","I" in this file), except portions of code in file `YoloAIO.vpy` that are the property of bitbucket user `YuriZero`.

This software is provided as-is, without any warranties of any kind. Use it at your own risk. You can find the full license in the `LICENSE` file included in this repository.

To avoid fragmentation, please only fork this project if you intend to significantly improve it in some way, and in that case prefer issuing a pull request instead if possible.


# Afterword
I would like to thank the following people :
 * `YuriZero`, the original creator of `YoloCR`, for the extensive ground work on which this project is based on. This project would not exist without them.
 * All the people that worked on `Tesseract-OCR`, `pytesseract`, `VapourSynth`, used `VapourSynth plugins`, `VapourSynth Editor` and `FFmpeg`. The world is a better place thanks to these precious tools.
 * The beautiful people at `StackOverflow` and similar forums, that provide treasures of information to anyone.

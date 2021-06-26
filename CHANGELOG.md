# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.1] - 2021-06-26

### Modified

- `YoloAIO.vpy` : Rework of step 1 for readability and bugfix (see below); Thinner white padding for text box; Added coordinates to simplify maintaining code that crops stuff. Default 'step' is now 1 (duh).

- `YoloAIO.py` : Added to double quote normalization.

### Bugfix

- `YoloAIO.vpy` : In step 1, text box had incorrect vertical position. Also, solved some "Error: __ must be MOD2" issues and an AssertionError in step 3 when looking for 1 Color only.

- `YoloAIO.py` : Reworked CLI UI to behave more intuitively.

## [1.1.0] - 2021-06-07

### Added

- `YoloAIO.py` : contains functions/classes used by `YoloAIO.vpy`

- `0.TesseractDownloadLanguage.bat` : Added pause for the user to check if language file was successfully downloaded

### Modified

- `YoloAIO.vpy` : Major rework of most of the code to accomodate for streamlined per-color text extraction

## [1.0.0] - 2021-06-02

__INITIAL RELEASE__

### Added

- Current file `Changelog.md`
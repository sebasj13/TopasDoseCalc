# <p align="center">TopasDoseCalc</p>

![TopasDoseCalc Logo](/topasdosecalc/icon.png?raw=true)

## <p align="center">A GUI to merge and scale split-up TOPAS simulations to absolute doses and calculate DVHs</p>

This GUI allows the merging of multiple TOPAS DICOM simulations. This can be useful when a patient plan has been split up into individual simulations of the control points. The merged simulation can then be scaled using a reference calibration simulation and data from the RTPLAN. Finally, DVHs can be automatically created when supplying a RTSTRUCT file.

## Installation

Install using pip:

```console
$ pip install topasdosecalc  
```
     
Then, start the GUI by running:
     
```console
$ python -m topasdosecalc
```

Or, if your Python is added to $PATH, simply run:

```console
$ topasdosecalc
```

## Screenshots

![Screenshot 2022-05-31 163018](https://user-images.githubusercontent.com/87897942/171198692-1b9d553a-b9eb-43d6-aa59-17173d948cb6.png)

## Dependencies

Built using the beautiful [Azure-ttk theme](https://github.com/rdbende/Azure-ttk-theme) by [@rdbende](https://github.com/rdbende). Requires python3, numpy, matplotlib, pydicom and dicompyler-core.

## Contact me!

Thank you for using TopasDoseCalc! Please let me know about any issues you encounter, or suggestions/wishes you might have! 

# <p align="center">TopasDoseCalc</p>

<p align="center"><img src=https://user-images.githubusercontent.com/87897942/173801225-fd4c4500-cf75-4f9d-93be-72b7d67144c7.png width=100 height=100></p>

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

## Manual



## Screenshots

<p align="center"><img src=https://user-images.githubusercontent.com/87897942/171198692-1b9d553a-b9eb-43d6-aa59-17173d948cb6.png></p>

## Dependencies

Built using the beautiful [Azure-ttk theme](https://github.com/rdbende/Azure-ttk-theme) by [@rdbende](https://github.com/rdbende). Requires python3, numpy, matplotlib, pydicom and dicompyler-core.

## Contact me!

Thank you for using TopasDoseCalc! Please let me know about any issues you encounter, or suggestions/wishes you might have! 

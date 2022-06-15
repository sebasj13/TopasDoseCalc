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

To use TopasDoseCalc, you need to supply at least five things:

1. A directory containing your TOPAS DICOM simulation results, named after the control point (order is relevant!)
2. A TOPAS dose profile reference simulation. The mean of the values close to the center axis is used as the scale
3. A directory containing at least the relevant RTPLAN file. For DVH calculation, a RTDOSE and RTSTRUCT file is required
4. The histories used for the simulation of each control point (individual, not total) 
5. A new series description for the merged DICOM.

If you supplied a RTDOSE and RTSTRUCT file you can select the structures for which to calculate a DVH. THis is good as an initial validation of the simulation results.

<b>Note:</b>
The program assumes 1 MU to be equivalent to 1cGy. If this doesn't apply to your case, scale the histories per simulation by the relevant amount.

## Screenshots

<p align="center"><img src=https://user-images.githubusercontent.com/87897942/171198692-1b9d553a-b9eb-43d6-aa59-17173d948cb6.png></p>

## Dependencies

Built using the beautiful [Azure-ttk theme](https://github.com/rdbende/Azure-ttk-theme) by [@rdbende](https://github.com/rdbende). Requires python3, numpy, matplotlib, pydicom and dicompyler-core.

## Contact me!

Thank you for using TopasDoseCalc! Please let me know about any issues you encounter, or suggestions/wishes you might have! 

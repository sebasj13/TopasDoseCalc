import os
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as fd
from tkinter import simpledialog as sd

import numpy as np
import topas2numpy
from dicompylercore import dicomparser
from natsort import natsorted, ns
from PIL import Image, ImageTk
from pydicom import dcmread

from .structure_selector import StructureSelector


class Configurator(tk.Frame):
    def __init__(self, parenttk, parent):

        tk.Frame.__init__(self, parenttk)
        self.parent = parent
        self.parenttk = parenttk

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)

        self.configure(
            highlightbackground="black", highlightthickness=2, highlightcolor="black"
        )

        buttonImage = Image.open(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "src",
                    "folder.ico",
                )
            )
        )
        self.foldertext = tk.Canvas(self, width=200, height=20)
        self.foldertext.create_text(
            100, 10, anchor=tk.CENTER, text="1. Select TOPAS simulation directory"
        )
        self.foldertext.grid(column=0, row=0)  # , rowspan=2)
        self.buttonPhoto = ImageTk.PhotoImage(buttonImage)
        self.dcmfolderbutton = ttk.Button(
            self,
            text="TOPAS simulation results",
            image=self.buttonPhoto,
            compound=tk.TOP,
            command=lambda: threading.Thread(target=self.pick_sim_folder).start(),
        )
        self.dcmfolderbutton.grid(column=0, row=1, rowspan=4)

        self.reftext = tk.Canvas(self, width=200, height=20)
        self.reftext.create_text(
            100, 10, anchor=tk.CENTER, text="2. Select TOPAS reference simulation"
        )
        self.reftext.grid(column=1, row=0)  # , rowspan=2)
        topasImage = Image.open(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "src",
                    "topas.ico",
                )
            )
        )
        self.topasPhoto = ImageTk.PhotoImage(topasImage)
        self.refbutton = ttk.Button(
            self,
            text="TOPAS reference simulation",
            image=self.topasPhoto,
            compound=tk.TOP,
            command=lambda: threading.Thread(target=self.pick_ref_simulation).start(),
        )
        self.refbutton.grid(column=1, row=1, rowspan=4)

        self.refdcmtext = tk.Canvas(self, width=250, height=20)
        self.refdcmtext.create_text(
            125, 10, anchor=tk.CENTER, text="3. Select RTPLAN, RTDOSE, and RTSTRUCT"
        )
        self.refdcmtext.grid(column=2, row=0)  # , rowspa)
        dcmImage = Image.open(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "src",
                    "dcm.ico",
                )
            )
        )
        self.dcmPhoto = ImageTk.PhotoImage(dcmImage)
        self.refbutton = ttk.Button(
            self,
            text="RTPLAN, RTDOSE, RTSTRUCT",
            image=self.dcmPhoto,
            compound=tk.TOP,
            command=lambda: threading.Thread(target=self.pick_ref_dicom_folder).start(),
        )
        self.refbutton.grid(column=2, row=1, rowspan=4)

        self.simhistories = tk.Label(self, text="4. Histories per simulation:")
        self.simhistoriesentry = tk.Entry(self, width=30)

        self.simhistories.grid(column=3, row=0)
        self.simhistoriesentry.grid(column=3, row=1, padx=(0, 5))

        self.seriesdescription = tk.Label(self, text="5. New DICOM series description:")
        self.seriesdescriptionentry = tk.Entry(self, width=30)

        self.seriesdescription.grid(column=3, row=2)
        self.seriesdescriptionentry.grid(column=3, row=3, padx=(0, 5))
        self.parenttk.bind("<Return>", self.pick_simulated_histories)

        self.dvh = tk.BooleanVar()
        self.dvh.set(False)
        self.dvhselect = ttk.Checkbutton(
            self, text="Calculate DVHs ?", command=self.show_buttons, variable=self.dvh
        )
        self.dvhselect.grid(column=3, row=4)

    def show_buttons(self):
        try:
            if self.dvh.get() == True:

                self.parent.frame2 = StructureSelector(self.parenttk, self.parent)
                self.parent.frame2.create_buttons()
                self.parent.frame2.show_buttons()
                self.parent.frame2.grid(
                    row=1, column=1, padx=(0, 5), pady=(5, 0), sticky=tk.NW
                )

            else:
                self.parent.frame2.grid_forget()
                self.parent.frame2 = None
        except AttributeError:
            self.parent.output.add_text(
                "(ERROR) No or invalid DICOM directory selected!"
            )
            self.dvh.set(False)

    def pick_sim_folder(self):
        self.folder_selected = fd.askdirectory()
        if self.folder_selected != "":
            self.parent.output.add_text(
                f"Selected simulation directory: {self.folder_selected}"
            )
            self.parent.output.add_text(
                f"Searching for TOPAS RTDOSE simulation results..."
            )
            self.simulations = []

            self.parent.run.grid_forget()
            self.parent.pb.grid(row=2, column=0, padx=(5, 5), pady=(5, 5))

            self.parent.log.grid(row=2, column=1, padx=(5, 5), pady=(5, 5))

            for r, d, f in os.walk(self.folder_selected):
                for file in f:
                    if file.endswith("dcm"):
                        # with dcmread(os.path.join(r, file)) as dcmfile:
                        dcmfile = dicomparser.DicomParser(os.path.join(r, file))
                        if dcmfile.ds.Modality == "RTDOSE":
                            self.simulations += [os.path.join(r, file)]

                            self.parenttk.update_idletasks()
                            self.parent.pb["value"] += 100 / len(next(os.walk(r))[2])

            self.parent.log.grid_forget()
            self.parent.log.configure(text="Merging simulations ...")
            self.parent.pb.grid_forget()
            self.parent.pb.config(mode="determinate")
            self.parent.run.grid(
                row=2, column=0, columnspan=2, padx=(5, 5), pady=(5, 5), sticky=tk.NSEW
            )
            self.parent.pb["value"] = 0

            self.parent.output.add_text(f"Found {len(self.simulations)} RTDOSE files!")
            self.simulations = natsorted(self.simulations, alg=ns.IC)
        else:
            self.parent.output.add_text("Simulation folder selection cancelled!")

    def pick_ref_simulation(self):
        self.reference_simulation = fd.askopenfilename(
            filetypes=[("TOPAS simulation outputs", "*.csv; *.bin")]
        )
        if self.reference_simulation != "":
            self.parent.output.add_text(
                f"Selected reference simulation: {self.reference_simulation}"
            )
            try:
                self.data = topas2numpy.BinnedResult(self.reference_simulation)
            except Exception:
                self.parent.output.add_text(f"Unsupported reference simulation type!")
                self.reference_simulation = ""
                return
            bins = [dim.n_bins for dim in self.data.dimensions]
            if bins.count(1) != 2:
                self.parent.output.add_text(f"Unsupported reference simulation type!")
                self.reference_simulation = ""
                return

            axdict = {0: "X", 1: "Y", 2: "Z"}
            databin_index = bins.index(max(bins))
            self.direction = axdict[databin_index]
            self.axis = np.array(self.data.dimensions[databin_index].get_bin_centers())
            unit = self.data.dimensions[databin_index].unit
            self.axis = [self.convert_SI(x, unit) for x in self.axis]
            if "Mean" in self.data.statistics:
                scored_quantity = "Mean"
            if "Sum" in self.data.statistics:
                scored_quantity = "Sum"
            self.dose = self.data.data[scored_quantity]
            self.dose = np.flip(self.dose.flatten())
            try:
                self.std_dev = np.flip(self.data.data["Standard_Deviation"].flatten())
                self.histories = int(
                    self.data.data["Histories_with_Scorer_Active"].flatten()[0]
                )
                if scored_quantity == "Sum":
                    self.std_dev = self.std_dev * np.sqrt(self.histories)
                else:
                    self.std_dev = self.std_dev / np.sqrt(self.histories)
            except KeyError as e:
                if e.args[0] == "Histories_with_Scorer_Active":
                    self.histories = sd.askinteger(
                        title="  ", prompt="Histories used for reference simulation:"
                    )
                    self.std_dev = self.data.data["Standard_Deviation"].flatten()
                    if scored_quantity == "Sum":
                        self.std_dev = self.std_dev * np.sqrt(self.histories)
                    else:
                        self.std_dev = self.std_dev / np.sqrt(self.histories)
                else:
                    self.std_dev = np.array([])

            self.parent.output.add_text(
                f"Reference simulation in {self.direction}-direction with binning {tuple(bins)}"
            )
            self.parent.output.add_text(
                f"Reference simulation used {self.histories} total histories"
            )
            self.avg_dose = np.mean(
                self.dose[len(self.dose) // 2 - 3 : len(self.dose) // 2 + 3]
            )
            self.parent.output.add_text(f"Setting reference dose to {self.avg_dose} Gy")

        else:
            self.parent.output.add_text("Reference simulation selection cancelled!")

    def pick_ref_dicom_folder(self):
        self.dcm_folder_selected = fd.askdirectory()
        if self.dcm_folder_selected != "":
            self.parent.output.add_text(
                f"Selected reference DICOM directory: {self.dcm_folder_selected}"
            )
            CTs = 0
            for r, d, f in os.walk(self.dcm_folder_selected):
                for file in f:
                    if ".dcm" in file:
                        with dcmread(os.path.join(r, file)) as dcmfile:
                            if dcmfile.Modality == "CT":
                                CTs += 1
                            elif dcmfile.Modality == "RTDOSE":
                                self.refdose = os.path.join(r, file)
                                self.parent.output.add_text(
                                    f"Selected reference RTDOSE file: {file}"
                                )
                            elif dcmfile.Modality == "RTSTRUCT":
                                self.rtstruct = os.path.join(r, file)
                                self.parent.output.add_text(
                                    f"Selected reference RTSTRUCT file: {file}"
                                )
                            elif dcmfile.Modality == "RTPLAN":
                                self.rtplan = os.path.join(r, file)
                                self.fractions = 0
                                for frac in dcmfile.FractionGroupSequence:
                                    self.fractions += int(frac.NumberOfFractionsPlanned)
                                self.total_mu = []
                                for mu in dcmfile.FractionGroupSequence:
                                    for beam in mu.ReferencedBeamSequence:
                                        self.total_mu += [float(beam.BeamMeterset)]
                                self.mus = []
                                for j in range(len(dcmfile.BeamSequence)):
                                    temp = []
                                    for i in range(
                                        len(
                                            dcmfile.BeamSequence[j].ControlPointSequence
                                        )
                                    ):
                                        temp += [
                                            float(
                                                dcmfile.BeamSequence[j]
                                                .ControlPointSequence[i]
                                                .CumulativeMetersetWeight
                                            )
                                            * self.total_mu[j]
                                        ]
                                    temp = np.diff(temp).tolist()
                                    temp.append(0)
                                    self.mus += temp
                                self.total_mu = sum(self.total_mu)
                                for index, value in enumerate(self.mus):
                                    if value < 0:
                                        self.mus[index] = 0

                                self.parent.output.add_text(
                                    f"Selected reference RTPLAN file: {file}"
                                )
                                self.parent.output.add_text(
                                    f"Number of planned fractions: {self.fractions}"
                                )
                                self.parent.output.add_text(
                                    f"Total MUs/fraction: {self.total_mu:5.1f}"
                                )

        else:
            self.parent.output.add_text("Reference DICOM folder selection cancelled!")

    def pick_simulated_histories(self, event=None):
        if event.widget.winfo_name() != "!entry2":

            self.simulated_histories = self.simhistoriesentry.get()
            try:
                self.simulated_histories = int(self.simulated_histories)
                self.parent.output.add_text(
                    f"Set simulated histories to: {self.simulated_histories}"
                )
            except Exception:
                self.parent.output.add_text("Invalid simulated histories entry!")
        else:
            self.newseriesdescription = self.seriesdescriptionentry.get()
            if self.newseriesdescription == "":
                self.parent.output.add_text("Invalid series description!")
            else:
                self.parent.output.add_text(
                    f"Set output series description to {self.newseriesdescription}"
                )

    def convert_SI(self, val, unit_in):
        SI = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0}
        return val * SI[unit_in] / SI["mm"]


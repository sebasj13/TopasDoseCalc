import os
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk

import dicompylercore.dvhcalc as dv
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from pydicom import dcmread


class StructureSelector(tk.Frame):
    def __init__(self, parenttk, parent):

        tk.Frame.__init__(self, parenttk)
        self.parenttk = parenttk
        self.parent = parent

        self.configure(
            highlightbackground="black", highlightthickness=2, highlightcolor="black"
        )

    def create_buttons(self):

        self.structures = []
        with dcmread(self.parent.frame.rtstruct) as dcmfile:
            for i in range(len(dcmfile.StructureSetROISequence)):
                self.structures += [
                    (
                        dcmfile.StructureSetROISequence[i].ROINumber,
                        dcmfile.StructureSetROISequence[i].ROIName,
                    )
                ]
        self.structures.sort(key=lambda y: y[0])

        self.variables = [tk.BooleanVar() for i in range(len(self.structures))]
        [variable.set(False) for variable in self.variables]
        self.buttons = [
            ttk.Checkbutton(
                self, variable=self.variables[i], text=f"{self.structures[i][1]}"
            )
            for i in range(len(self.structures))
        ]

    def show_buttons(self):

        try:

            if self.parent.frame.dvh.get() == True:

                [
                    button.grid(sticky="W", padx=(2, 2), pady=(1, 1))
                    for button in self.buttons
                ]
            else:
                [button.grid_forget() for button in self.buttons]

        except AttributeError:

            self.parent.output.add_text(
                "(ERROR) No or invalid RTSTRUCT file in reference DICOM folder!"
            )
            self.parent.frame.dvh.set(False)

    def calculate_dvhs(self):
        def calculate_TOPAS_DVHs():
            dvh = []

            while True:
                if os.path.exists(
                    f"C://Users//sebas//Desktop//TESTS//{self.parent.frame.newseriesdescription}.dcm"
                ):
                    for i in range(len(self.structures)):
                        if self.variables[i].get() == True:
                            dvh += [
                                dv.get_dvh(
                                    self.parent.frame.rtstruct,
                                    f"C://Users//sebas//Desktop//TESTS//{self.parent.frame.newseriesdescription}.dcm",
                                    # "C://Users//sebas//Documents//GitHub//dicom2topas//dicom2topas//Plans//16_22_Patientin_Kopf//RD1.2.752.243.1.1.20220112085113628.6500.76031.dcm",
                                    self.structures[i][0],
                                )
                            ]
                if len(dvh) == len([x for x in self.variables if x.get() == True]):
                    break
            self.topas_dvh = dvh

        def calculate_Reference_DVHs():
            dvh = []

            for i in range(len(self.structures)):
                if self.variables[i].get() == True:
                    dvh += [
                        dv.get_dvh(
                            self.parent.frame.rtstruct,
                            f"{self.parent.frame.refdose}",
                            self.structures[i][0],
                        )
                    ]
            self.ref_dvh = dvh

        self.parent.log.configure(text="Creating DVHs ...")
        threading.Thread(calculate_TOPAS_DVHs()).start()
        threading.Thread(calculate_Reference_DVHs()).start()

        while True:
            try:
                if self.ref_dvh:
                    pass
                if self.topas_dvh:
                    pass

                for i in range(len(self.ref_dvh)):
                    plt.plot(
                        self.topas_dvh[i].bincenters,
                        self.topas_dvh[i].relative_volume.counts,
                        label=self.topas_dvh[i].name + " - TOPAS",
                    )
                    self.parent.pb["value"] += 50 / len(self.ref_dvh)
                    time.sleep(0.5)

                    plt.plot(
                        self.ref_dvh[i].bincenters,
                        self.ref_dvh[i].relative_volume.counts,
                        label=self.ref_dvh[i].name + " - Ref",
                    )

                    self.parent.pb["value"] += 50 / len(self.ref_dvh)
                    time.sleep(0.5)
                break

            except NameError:
                pass

        plt.xlabel("Dose [%s]" % self.ref_dvh[0].dose_units)
        plt.ylabel("Volume [%s]" % self.ref_dvh[0].relative_volume.volume_units)
        plt.legend(loc="best")
        plt.savefig("C://Users//sebas//Desktop//plot.png", dpi=600)

        self.parent.pb.grid_forget()
        self.parent.log.grid_forget()
        self.parent.log.configure(text="Merging Sims ...")
        self.parent.pb["value"] = 0
        self.parent.run.grid(row=2, column=1, columnspan=2, padx=(5, 5), pady=(5, 5))
        return


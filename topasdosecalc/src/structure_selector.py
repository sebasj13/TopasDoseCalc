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
        self.canvas = tk.Canvas(self, width=196, height=388)
        self.canvas.configure(highlightthickness=0)
        self.canvas.pack(side=tk.LEFT)
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.frame = tk.Frame(self.canvas)
        self.frame.configure(highlightthickness=0)
        self.canvas.create_window(
            (4, 4), window=self.frame, anchor="nw", tags="self.frame"
        )
        self.frame.bind("<Configure>", self.onFrameConfigure)
        self.scrollbar.configure(command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.bind("<Enter>", self._bound_to_mousewheel)
        self.bind("<Leave>", self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def onFrameConfigure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

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
                self.frame, variable=self.variables[i], text=f"{self.structures[i][1]}"
            )
            for i in range(len(self.structures))
        ]

    def show_buttons(self):

        try:
            if self.parent.frame.dvh.get() == True:

                [
                    button.pack(anchor=tk.W, padx=(2, 2), pady=(2, 2))
                    for button in self.buttons
                ]
            else:
                [button.pack_forget() for button in self.buttons]

        except AttributeError:
            self.parent.output.add_text(
                "(ERROR) No or invalid RTSTRUCT file in reference DICOM folder!"
            )
            self.parent.frame.dvh.set(False)

    def calculate_dvhs(self):
        def calculate_TOPAS_DVHs():
            dvh = []
            filename = self.parent.frame.newseriesdescription + ".dcm"
            filename = os.path.join(self.parent.frame.folder_selected, filename)

            while True:
                if os.path.exists(filename):
                    for i in range(len(self.structures)):
                        if self.variables[i].get() == True:
                            self.parent.output.add_text(
                                f"Calculating TOPAS DVH for structure {self.structures[i][1]} ..."
                            )
                            dvh += [
                                dv.get_dvh(
                                    self.parent.frame.rtstruct,
                                    filename,
                                    self.structures[i][0],
                                )
                            ]
                            self.parent.pb["value"] += 50 / len(
                                [
                                    variable
                                    for variable in self.variables
                                    if variable.get() == True
                                ]
                            )

                if len(dvh) == len([x for x in self.variables if x.get() == True]):
                    break
            self.topas_dvh = dvh

        def calculate_Reference_DVHs():
            dvh = []

            for i in range(len(self.structures)):
                if self.variables[i].get() == True:
                    self.parent.output.add_text(
                        f"Calculating Reference DVH for structure {self.structures[i][1]} ..."
                    )
                    dvh += [
                        dv.get_dvh(
                            self.parent.frame.rtstruct,
                            f"{self.parent.frame.refdose}",
                            self.structures[i][0],
                        )
                    ]
                    self.parent.pb["value"] += 50 / len(
                        [
                            variable
                            for variable in self.variables
                            if variable.get() == True
                        ]
                    )
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

                    plt.plot(
                        self.ref_dvh[i].bincenters,
                        self.ref_dvh[i].relative_volume.counts,
                        label=self.ref_dvh[i].name + " - Ref",
                    )

                break

            except Exception:
                pass

        plt.xlabel("Dose [%s]" % self.ref_dvh[0].dose_units)
        plt.ylabel("Volume [%s]" % self.ref_dvh[0].relative_volume.volume_units)
        # plt.xlim(
        #    left=0,
        #    right=max(
        #        [max(self.ref_dvh[i].bincenters) for i in range(len(self.ref_dvh))]
        #    )
        #    * 1.5,
        # )
        plt.legend(loc="best")
        self.parent.output.add_text(
            f"Saving DVH.png to {self.parent.frame.folder_selected}"
        )
        plt.savefig(
            os.path.join((self.parent.frame.folder_selected), "DVH.png"), dpi=600
        )

        self.parent.pb.grid_forget()
        self.parent.log.grid_forget()
        self.parent.log.configure(text="Merging simulations ...")
        self.parent.pb["value"] = 0
        self.parent.run.grid(
            row=2, column=0, columnspan=2, padx=(5, 5), pady=(5, 5), sticky=tk.NSEW
        )
        self.parent.output.add_text(f"(SUCCESS) Completed!")
        return


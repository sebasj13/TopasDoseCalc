import os
import threading
import tkinter as tk
import customtkinter as ctk

import dicompylercore.dvhcalc as dv
import matplotlib as mpl

#mpl.use("Agg")
import matplotlib.pyplot as plt
from pydicom import dcmread


class StructureSelector(ctk.CTkScrollableFrame):
    def __init__(self, parent):

        super().__init__(parent, orientation = "vertical")
        self.parent = parent


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
        with dcmread(self.parent.master.rtstruct) as dcmfile:
            self.rtstruct = dcmfile
            for i in range(len(dcmfile.StructureSetROISequence)):

                self.structures += [
                    (
                        dcmfile.StructureSetROISequence[i].ROINumber,
                        dcmfile.StructureSetROISequence[i].ROIName,
                        "#"+"".join([format(c,'02x') for c in [dcmfile.ROIContourSequence[j].ROIDisplayColor for j in range(len(dcmfile.ROIContourSequence)) if dcmfile.ROIContourSequence[j].ReferencedROINumber == dcmfile.StructureSetROISequence[i].ROINumber][0]]),
                    )
                ]
        self.structures.sort(key=lambda y: y[0])
        self.variables = [ctk.BooleanVar() for i in range(len(self.structures))]
        [variable.set(False) for variable in self.variables]
        self.buttons = [
            ctk.CTkCheckBox(
                self, variable=self.variables[i], text=f"{self.structures[i][1]}"
            )
            for i in range(len(self.structures))
        ]

    def show_buttons(self):

        try:
            if self.parent.master.dvh.get() == True:

                [
                    button.pack(anchor=tk.W, padx=(2, 2), pady=(2, 2))
                    for button in self.buttons
                ]
            else:
                [button.pack_forget() for button in self.buttons]

        except AttributeError:
            self.parent.master.log(
                "(ERROR) No or invalid RTSTRUCT file in reference DICOM folder!"
            )

    def calculate_dvhs(self):
        def calculate_TOPAS_DVHs():
            dvh = []
            filename = os.path.join(self.parent.master.folder.get(), f'{self.parent.master.descriptionentry.get().strip()}.dcm')

            while True:
                if os.path.exists(filename):
                    k=1
                    for i in range(len(self.structures)):
                        if self.variables[i].get() == True:
                            self.parent.master.log(
                                f"Calculating TOPAS DVH for structure {self.structures[i][1]} ..."
                            )
                            self.parent.master.parent.pbvar.set((k)/len(
                                [
                                    variable
                                    for variable in self.variables
                                    if variable.get() == True
                                ]
                            ))
                            dvh += [
                                dv.get_dvh(
                                    self.rtstruct,
                                    filename,
                                    self.structures[i][0],
                                    limit=int(self.parent.master.fractions*self.parent.master.dose*110),
                                )
                            ]
                            k+=1

                if len(dvh) == len([x for x in self.variables if x.get() == True]):
                    break
            self.parent.master.parent.pbvar.set(0)
            self.topas_dvh = dvh

        def calculate_Reference_DVHs():
            dvh = []
            k = 1
            for i in range(len(self.structures)):
                if self.variables[i].get() == True:
                    self.parent.master.log(
                        f"Calculating Reference DVH for structure {self.structures[i][1]} ..."
                    )
                    self.parent.master.parent.pbvar.set((k)/len(
                        [
                            variable
                            for variable in self.variables
                            if variable.get() == True
                        ]
                    ))
                    k+=1
                    dvh += [
                        dv.get_dvh(
                            self.rtstruct,
                            f"{self.parent.master.rtdose}",
                            self.structures[i][0],
                            limit=int(self.parent.master.fractions*self.parent.master.dose*110),
                        )
                    ]

            self.parent.master.parent.pbvar.set(0)
            self.ref_dvh = dvh

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
                        color=self.structures[[self.structures[j][1] for j in range(len(self.structures))].index(self.topas_dvh[i].name)][2],
                        linestyle="--",
                        linewidth=0.5,
                    )

                    plt.plot(
                        self.ref_dvh[i].bincenters,
                        self.ref_dvh[i].relative_volume.counts,
                        label=self.ref_dvh[i].name + " - Ref",
                        color=self.structures[[self.structures[j][1] for j in range(len(self.structures))].index(self.ref_dvh[i].name)][2],
                        linewidth=0.5,
                    )

                break

            except Exception as e:
                print(e)
        if len(self.ref_dvh) != 0:
            plt.xlabel("Dosis [%s]" % self.ref_dvh[0].dose_units)
            plt.ylabel("Volumen [%s]" % self.ref_dvh[0].relative_volume.volume_units)
            plt.xlim(
                left=0,
                right=self.parent.master.fractions*self.parent.master.dose*1.1)
            self.parent.master.log(
                f"Saving DVH.png to {self.parent.master.folder.get()}"
            )
            plt.grid()
            plt.gcf().legend(bbox_to_anchor=(0.5,-0.05), loc="upper center", ncols=5, fancybox=True, shadow=True, prop={'size': 8})
            plt.gcf().tight_layout()
            plt.savefig(
                os.path.join((self.parent.master.folder.get()), "DVH.png"), dpi=600, bbox_inches='tight'
            )


            self.parent.master.parent.pbvar.set(0)
            self.parent.master.log(f"Completed DVH calculation")
        return


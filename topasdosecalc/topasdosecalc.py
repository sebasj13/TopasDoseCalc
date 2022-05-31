#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 28 10:54:31 2022

@author: Sebastian Schäfer
@institution: Martin-Luther-Universität Halle-Wittenberg
@email: sebastian.schaefer@student.uni-halle.de
"""

import os
import threading
import tkinter as tk
import tkinter.ttk as ttk

from .src.config import Configurator
from .src.merge_doses import merge_doses
from .src.output import Output
from .src.structure_selector import StructureSelector


class TopasDoseCalc:
    def __init__(self):

        self.root = tk.Tk()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = 812
        height = 550
        self.root.minsize(width, height)

        x = screen_width // 2 - width // 2
        y = screen_height // 2 - height // 2
        self.root.geometry(f"{width}x{height}+{x-25}+{y}")
        self.root.state("normal")
        self.root.resizable(False, False)
        self.root.title("TopasDoseCalc")
        self.root.tk.call(
            "wm",
            "iconphoto",
            self.root._w,
            tk.PhotoImage(
                file=os.path.realpath(
                    os.path.join(
                        os.path.dirname(os.path.realpath(__file__)), "src", "icon.png",
                    )
                )
            ),
        ),

        ttk.Style(self.root)
        self.root.tk.call(
            "source",
            str(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                    "topasdosecalc",
                    "src",
                    "Azure-ttk-theme",
                    "azure.tcl",
                )
            ),
        )
        self.frame = Configurator(self.root, self)
        self.frame.grid(row=0, column=0, columnspan=5, padx=(5, 5), pady=(5, 0))
        self.root.columnconfigure(4, weight=10)
        self.frame2 = StructureSelector(self.root, self)
        self.frame2.grid(row=1, column=4, padx=(5, 5), pady=(5, 5))
        self.output = Output(self.root)
        self.output.add_text("Initialized")
        self.output.grid(row=1, column=0, columnspan=4, padx=(5, 5), pady=(5, 5))
        self.pb = ttk.Progressbar(
            self.root, orient=tk.HORIZONTAL, length=400, mode="determinate"
        )
        self.log = tk.Label(self.root, text="Loading DICOMs ...")
        self.run = ttk.Button(
            self.root,
            text="RUN!",
            command=lambda: threading.Thread(
                target=merge_doses(
                    self.root,
                    self.frame,
                    self.pb,
                    self.run,
                    self.output,
                    self.frame2,
                    self.log,
                )
            ).start(),
        )
        self.run.grid(row=2, column=1, columnspan=2, padx=(5, 5), pady=(5, 5))

    def mainloop(self):
        self.root.mainloop()


def topasdosecalc():
    TDC = TopasDoseCalc()
    TDC.mainloop()


if __name__ == "__main__":
    topasdosecalc()

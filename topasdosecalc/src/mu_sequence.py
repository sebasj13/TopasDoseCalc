import customtkinter as ctk
from tkinter.ttk import Separator

class MU_Sequence(ctk.CTkScrollableFrame):
    
    def __init__(self, parent, sequence):
    
        self.parent = parent
        super().__init__(self.parent, height=100, orientation="horizontal")
        self.beams = len(sequence)
        self.mus = sequence
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, weight=1)
        self.rowconfigure(6, weight=1)
        self.columnconfigure(1, weight=1)
        Separator(self, orient="horizontal").grid(row=0, column=1, columnspan=2, sticky="ew")
        ctk.CTkLabel(self, text="Control Point:", font=("Bahnschrift", 12), anchor="w").grid(row=1, column=1, sticky="nsew", padx=5)
        ctk.CTkLabel(self, text="MUs:", font=("Bahnschrift", 12), anchor="w").grid(row=3, column=1, sticky="nsew", padx=5)
        Separator(self, orient="vertical").grid(row=0, column= 0, rowspan=4, sticky="ns")
        Separator(self, orient="vertical").grid(row=0, column= 2, rowspan=4, sticky="ns")
        Separator(self, orient="horizontal").grid(row=2, column=1, columnspan=2, sticky="ew")
        Separator(self, orient="horizontal").grid(row=4, column=1, columnspan=2, sticky="ew")
        for i,mu in enumerate(self.mus):
            self.columnconfigure(i+2, weight=1)
            Separator(self, orient="horizontal").grid(row=0, column=i*2+3, columnspan=2, sticky="ew")
            ctk.CTkLabel(self, text=f"{i}", font=("Bahnschrift", 12), anchor="center").grid(row=1, column=i*2+3, sticky="ns", padx=5)
            ctk.CTkLabel(self, text=f"{round(mu,3)} MU", font=("Bahnschrift", 12)).grid(row=3, column=i*2+3, sticky="nsew", padx=5)
            Separator(self, orient="vertical").grid(row=0, column=i*2+4, rowspan=4, sticky="ns")
            Separator(self, orient="horizontal").grid(row=2, column=i*2+3, columnspan=2, sticky="ew")
            Separator(self, orient="horizontal").grid(row=4, column=i*2+3, columnspan=2, sticky="ew")
        ctk.CTkLabel(self, text=f"Number of Beams: {self.beams}", font=("Bahnschrift", 12), anchor="w").grid(row=5, column=1, sticky="nsew", padx=5)
        ctk.CTkLabel(self, text=f"Total: {round(sum(list(self.mus)),3)} MUs", font=("Bahnschrift", 12), anchor="w").grid(row=6, column=1, sticky="nsew", padx=5)
        
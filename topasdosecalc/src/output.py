import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from tkinter import font


class Output(ctk.CTkFrame):
    def __init__(self, parent):

        ctk.CTkFrame.__init__(self, parent)
        self.parent = parent

        #self.configure(
        #    highlightbackground="black", highlightthickness=2, highlightcolor="black",
        #)

        self.scrollbar = ctk.CTkScrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.textbox = tk.Text(self, width=74, wrap=tk.WORD)
        self.textbox.pack(side=tk.TOP, fill="both", expand=True)
        self.textbox.config(yscrollcommand=self.scrollbar.set)
        self.textbox.configure(state="disabled")
        self.scrollbar.configure(command=self.textbox.yview)

        text_font = font.nametofont(self.textbox.cget("font"))
        bullet_width = text_font.measure("%H:%M:%S - ")
        em = text_font.measure("m")
        self.textbox.tag_configure("bulleted", lmargin1=em, lmargin2=em + bullet_width)

    def add_text(self, text=None):

        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        self.textbox.configure(state="normal")
        self.textbox.insert(tk.END, f"{current_time} - {text}\n", "bulleted")
        self.textbox.configure(state="disabled")
        self.textbox.see("end")


import customtkinter as ctk
import os
import sys
from datetime import datetime

from .src.options import Options

class topasdosecalc(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.appname = "TopasDoseCalc"
        self.version = "2.0.0"
        self.author = "Sebastian Schäfer"
        self.title(f"{self.appname} - v.{self.version}")
        
        self.minsize(width=960, height=500)
        self.geometry("960x500")
        self.resizable(False, False)
        self.iconpath = self.resource_path(os.path.join("src", "images", "icon.ico"))
        self.iconbitmap(self.iconpath)
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, minsize=480)
        self.columnconfigure(1, minsize=480)
        self.rowconfigure(1, minsize=12)
        
        self.options = Options(self)
        self.options.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.logger = ctk.CTkTextbox(self, activate_scrollbars=True, state="disabled", border_color="black", border_width=1, font=("Bahnschrift",14), fg_color="#2B2B2B")
        self.init_logger()
        self.logger.grid(row=0, column=1, sticky="nsew", padx=2)
        self.pbvar=ctk.DoubleVar(value=0)
        self.pb = ctk.CTkProgressBar(self, progress_color="green", corner_radius=0, variable = self.pbvar)
        self.pb.grid(row=1, columnspan=2, column=0, sticky="nsew", pady=(2,0))

        self.mainloop()
            
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, "topasdosecalc", relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
    
    def init_logger(self):
        self.log(f"{self.appname} v.{self.version} - by {self.author}", logtime = False)
        self.log("_______________________________________________\n", logtime = False)
        self.log("Initialized")
    
    def log(self, message, logtime=True):
        self.logger.configure(state="normal")
        time = ""
        if logtime:
            time = datetime.now().strftime("%H:%M:%S") + " | "
        self.logger.insert("end", f"{time}{message}\n")
        self.logger.configure(state="disabled")
        self.logger.see("end")                       
        
if __name__ == "__main__":
    topasdosecalc()

import os
import numpy as np
from PIL import Image
import customtkinter as ctk
from pydicom import dcmread
from threading import Thread
from .mu_sequence import MU_Sequence
from .structure_selector import StructureSelector
from tkinter.filedialog import askdirectory, askopenfilename
from natsort import natsorted

class Options(ctk.CTkTabview):
    def __init__(self, parent):
        self.parent = parent
        self.log = self.parent.log
        self.resource_path = self.parent.resource_path
        self.sequence = []
        self.fractions = 1
        super().__init__(parent, border_color="black", border_width=1)
        
        self.add("General")
        self.add("RTPLAN")
        self.add("DVH")
        
        self.init_tab1()
        self.init_tab2()
        self.init_tab3()
        self.check_buttons()
         
    def init_tab1(self):
        ### TAB 1 ###
        self.tab("General").grid_propagate(False)
        self.tab("General").columnconfigure(0, minsize=30)
        self.tab("General").columnconfigure(1, weight=1)
        self.tab("General").columnconfigure(2, weight=1)
        self.tab("General").columnconfigure(3, weight=1)
        
        self.folderlabel = ctk.CTkLabel(self.tab("General"), text="1. Select the directory containing the DICOM dose files", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.folderimage = ctk.CTkImage(dark_image=Image.open(self.resource_path(os.path.join("src","images","folder.png"))), size=(32,32))
        self.foldercheckbox = ctk.CTkCheckBox(self.tab("General"), state="disabled", text="", width=30)
        self.subdircheckbox = ctk.CTkCheckBox(self.tab("General"), text="Include subdirectories", width=20)
        self.folder = ctk.StringVar()
        self.select_folder_button = ctk.CTkButton(self.tab("General"), text="Select Folder", image=self.folderimage, compound="left", command=self.select_folder)
        
        self.historieslabel = ctk.CTkLabel(self.tab("General"), text="2. Input the histories used for the simulations", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.histories = ctk.StringVar()
        self.historycheckbox = ctk.CTkCheckBox(self.tab("General"), state="disabled", text="", width=30)
        self.histories_entry = ctk.CTkEntry(self.tab("General"), width=140, textvariable=self.histories)
        self.histories_entry.bind("<Return>", lambda event: self.entry_callback(event, self.histories_entry, self.historycheckbox, "simulation histories"))
        
        self.mus_label = ctk.CTkLabel(self.tab("General"), text="3. Input the monitor units of the simulated sequence", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.mus = ctk.StringVar()
        self.mus_checkbox = ctk.CTkCheckBox(self.tab("General"), state="disabled", text="", width=30, command = self.toggle_mus)
        self.mus_entry = ctk.CTkEntry(self.tab("General"), width=140, textvariable=self.mus)
        self.mus_entry.bind("<Return>", lambda event: self.entry_callback(event, self.mus_entry, self.mus_checkbox, "simulation monitor units"))
        
        self.reference_label = ctk.CTkLabel(self.tab("General"), text="4. Specify the reference simulation and scale factors", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.reference_mus = ctk.StringVar(value="100")
        self.reference_histories = ctk.StringVar(value="500000000")
        self.reference_scale = ctk.StringVar(value="973375")
        self.reference_checkbox = ctk.CTkCheckBox(self.tab("General"), state="disabled", text="", width=30)

        self.reference_mus_label = ctk.CTkLabel(self.tab("General"), text="Reference Monitor Units", font=("Bahnschrift",12), fg_color="#2B2B2B", anchor="center")
        self.reference_mus_entry = ctk.CTkEntry(self.tab("General"), width=120, textvariable=self.reference_mus)
        self.reference_mus_entry.bind("<Return>", lambda event: self.entry_callback_2(event, self.reference_mus_entry, "reference monitor units"))
        self.reference_histories_label = ctk.CTkLabel(self.tab("General"), text="Reference Histories", font=("Bahnschrift",12), fg_color="#2B2B2B", anchor="center")
        self.reference_histories_entry = ctk.CTkEntry(self.tab("General"), width=120, textvariable=self.reference_histories)
        self.reference_histories_entry.bind("<Return>", lambda event: self.entry_callback_2(event, self.reference_histories_entry, "reference histories"))
        self.reference_scale_label = ctk.CTkLabel(self.tab("General"), text="Reference Scale Factor", font=("Bahnschrift",12), fg_color="#2B2B2B", anchor="center")
        self.reference_scale_entry = ctk.CTkEntry(self.tab("General"), width=120, textvariable=self.reference_scale)
        self.reference_scale_entry.bind("<Return>", lambda event: self.entry_callback_2(event, self.reference_scale_entry, "reference scale factor"))
        
        self.descriptionlabel = ctk.CTkLabel(self.tab("General"), text="5. Enter a new series description", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.descriptioncheckbox = ctk.CTkCheckBox(self.tab("General"), state="disabled", text="", width=30)
        self.descriptionentry = ctk.CTkEntry(self.tab("General"), width=200)
        self.descriptionentry.bind("<Return>", lambda event: self.descriptioncheckbox.select())
        
        self.merge_button = ctk.CTkButton(self.tab("General"), text="Merge Dose Files", command=lambda: Thread(target=self.merge_dose_files).start(), state="disabled")
        
        self.folderlabel.grid(row=0, column=1, columnspan=3, sticky="nsew", padx=5, pady=1)
        self.foldercheckbox.grid(row=0, column=0, sticky="w", padx=10, pady=1)
        self.select_folder_button.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=1)
        self.subdircheckbox.grid(row=2, column=1, columnspan=3,sticky="w", padx=5, pady=(5,1))
        
        self.historieslabel.grid(row=3, column=1, columnspan=3, sticky="nsew", padx=5, pady=1)
        self.historycheckbox.grid(row=3, column=0, sticky="w", padx=10, pady=1)
        self.histories_entry.grid(row=4, column=1, columnspan=3, sticky="w", padx=5, pady=1)
        
        self.mus_label.grid(row=5, column=1, columnspan=3, sticky="nsew", padx=5, pady=1)
        self.mus_checkbox.grid(row=5, column=0, sticky="w", padx=10, pady=1)
        self.mus_entry.grid(row=6, column=1, columnspan=3, sticky="w", padx=5, pady=(5,10))
        
        self.reference_label.grid(row=7, column=1, columnspan=3, sticky="nsew", padx=5, pady=1)
        self.reference_checkbox.grid(row=7, column=0, sticky="nsew", padx=10, pady=1)
        self.reference_mus_label.grid(row=8, column=1, sticky="nsew", padx=5, pady=1)
        self.reference_histories_label.grid(row=8, column=2, sticky="nsew", padx=5, pady=1)
        self.reference_scale_label.grid(row=8, column=3, sticky="nsew", padx=5, pady=1)
        self.reference_mus_entry.grid(row=9, column=1, sticky="ns", padx=5, pady=1)
        self.reference_histories_entry.grid(row=9, column=2, sticky="ns", padx=5, pady=1)
        self.reference_scale_entry.grid(row=9, column=3, sticky="ns", padx=5, pady=1)
        
        self.descriptioncheckbox.grid(row=10, column=0, sticky="w", padx=10, pady=1)
        self.descriptionlabel.grid(row=10, column=1, columnspan=3, sticky="nsew", padx=5, pady=1)
        self.descriptionentry.grid(row=11, column=1, columnspan=3, sticky="w", padx=5, pady=(1,20))
        
        self.merge_button.grid(row=12, column=0, columnspan=4, sticky="ns", padx=5, pady=1)
        
    def check_buttons(self):
        if  (self.foldercheckbox._check_state == True and\
            self.historycheckbox._check_state == True and\
            self.reference_checkbox._check_state == True and\
            self.descriptioncheckbox._check_state == True) and \
            (self.mus_checkbox._check_state == True or \
            (self.rtplan_checkbox._check_state == True and len(self.sequence.flatten()) > 0)):
            if self.merge_button.cget("state") == "disabled":
                self.log("All options selected. Ready to merge dose files.")
                self.merge_button.configure(state="normal") 
        else:
            self.merge_button.configure(state="disabled")
            
        self.after(500, self.check_buttons)
        
    def select_folder(self):
        self.folder.set(askdirectory())
        if os.path.isdir(self.folder.get()):
            self.log(f"Selected Folder: {self.folder.get()}")
            self.foldercheckbox.configure(state="normal")
            self.foldercheckbox.select()
            self.foldercheckbox.configure(state="disabled")
        else:
            self.log("No valid folder selected")
            
    def entry_callback(self, event, entry, checkbox, text):
        try:
            float(entry.get())
            self.log(f"Set {text} to: {entry.get()}")
            checkbox.configure(state="normal")
            checkbox.toggle()
            checkbox.configure(state="disabled")
        except ValueError:
            self.log(f"Invalid input for {text}")
            checkbox.configure(state="normal")
            checkbox.deselect()
            checkbox.configure(state="disabled")
            
    def entry_callback_2(self, event, entry, text):
        try:
            float(entry.get())
            self.log(f"Set {text} to: {entry.get()}")
            self.reference_checkbox.configure(state="normal")
            self.reference_checkbox.select()
            self.reference_checkbox.configure(state="disabled")
        except ValueError:
            self.log(f"Invalid input for {text}")
            self.reference_checkbox.configure(state="normal")
            self.reference_checkbox.deselect()
            self.reference_checkbox.configure(state="disabled")
            
        try:
            float(self.reference_mus_entry.get())
            float(self.reference_histories_entry.get())
            float(self.reference_scale_entry.get())    
            
            self.reference_checkbox.configure(state="normal")
            self.reference_checkbox.select()
            self.reference_checkbox.configure(state="disabled")
        except Exception:
            self.reference_checkbox.configure(state="normal")
            self.reference_checkbox.deselect()
            self.reference_checkbox.configure(state="disabled")
            
    def merge_dose_files(self):
        files = []
        iso_files = []
        if self.subdircheckbox._check_state == True:
            for root, dirs, files in os.walk(self.folder.get()):
                for file in files:
                    if file.endswith(".dcm"):
                        files.append(os.path.join(root, file))
                    elif file.endswith(".csv"):
                        iso_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(self.folder.get()):
                if file.endswith(".dcm"):
                    files.append(os.path.join(self.folder.get(), file))  
                elif file.endswith(".csv"):
                    iso_files.append(os.path.join(root, file))
                    
        if len(files) == 0:
            self.log("No dose files found in selected folder")
            return
        else:
            self.log(f"Found {len(files)} dose files in selected folder")
            
            if self.mergeiso.get() == True:
                self.log(f"Found {len(iso_files)} isocenter files in selected folder")
            
            if self.mus_checkbox._check_state == False:
                if len(files) != len(self.sequence.flatten()):
                    self.log("Number of dose files does not match number of control points. Trying to merge individual fields...")
                    
                    try:
                        sort_string = "Field_"
                        fields = len(self.sequence)
                        fields_to_merge = [[] for i in range(fields)]
                        for file in files:
                            for i in range(fields):
                                if sort_string + str(i) in file:
                                    fields_to_merge[i].append(file) 
                    except Exception as e:
                        print(e)
                        return
                    
                    ####MERGE FIELDS; UPDATE FILES LIST AND CONTINUE####
        
        self.log("Merging dose files...")
        flag = 0
        
        for i,file in enumerate(natsorted(files)):
            
            ds = dcmread(file)
            self.parent.pbvar.set((i+1)/len(files))
            if flag == 0:
                data = ds.pixel_array * ds.DoseGridScaling
                data *= float(self.reference_scale_entry.get()) * (float(self.reference_histories_entry.get()) / float(self.histories_entry.get()))
                if self.mus_checkbox._check_state == False:
                    data *= (float(self.sequence.flatten()[i]) / float(self.reference_mus_entry.get()))
                flag = 1
            else:
                newdata = ds.pixel_array * ds.DoseGridScaling
                newdata *= float(self.reference_scale_entry.get()) * (float(self.reference_histories_entry.get()) / float(self.histories_entry.get()))
                if self.mus_checkbox._check_state == False:

                    newdata *= (float(self.sequence.flatten()[i]) / float(self.reference_mus_entry.get()))

                data = np.add(data, newdata)
        data *= self.fractions
        with dcmread(file) as ds:
            if self.mus_checkbox._check_state == True:
                data *= (float(self.mus_entry.get()) / float(self.reference_mus_entry.get()))
            ds.PatientName = "TOPASMC"
            ds.DoseGridScaling = np.max(data) / (2 ** int(ds.HighBit))
            data = (data / ds.DoseGridScaling).astype(np.uint32)
            ds.PixelData = data.tobytes()
            ds.SeriesDescription = self.descriptionentry.get()
            ds.save_as(os.path.join(self.folder.get(), f"{self.descriptionentry.get().strip()}.dcm"))
            self.log(f"Saved merged dose file to {os.path.join(self.folder.get(), f'{self.descriptionentry.get().strip()}.dcm')}")
        self.parent.pbvar.set(0)
        
        if self.mergeiso.get() == True and len(iso_files) == len(self.sequence.flatten()):
            self.log("Merging isocenter data...")
            data = []
            for i,file in enumerate(natsorted(iso_files)):
                self.parent.pbvar.set((i+1)/len(iso_files))
                scale =  float(self.reference_scale_entry.get()) * (float(self.reference_histories_entry.get()) / float(self.histories_entry.get())) * float(self.sequence.flatten()[i]) / float(self.reference_mus_entry.get())
                data += [self.read_iso_csv(file, scale)]
            self.parent.pbvar.set(0)
            dose = []
            std_dev = []
            n_hist = []
            count_in_bin = []
            max_dose = []
            for i in range(len(data[0])):
                self.parent.pbvar.set((i+1)/len(data[0]))
                dose += np.array([ sum([data[j][i][0] for j in range(len(data))])  ]).reshape(-1,1)
                std_dev += np.array([ np.sqrt(sum([data[j][i][1]**2 for j in range(len(data))])) ]).reshape(-1,1)
                n_hist += np.array([ sum([data[j][i][2] for j in range(len(data))])  ]).reshape(-1,1)
                count_in_bin +=  np.array([sum([data[j][i][3] for j in range(len(data))])  ]).reshape(-1,1)
                max_dose += np.array([ max([data[j][i][0] for j in range(len(data))])  ]).reshape(-1,1)
            data  = np.array([dose,std_dev,n_hist,count_in_bin, max_dose])     
            with open(os.path.join(self.folder.get(), f"{self.descriptionentry.get().strip()}_iso.csv"), "w") as file:
                np.savetxt(file, data, delimiter=",", header="Sum, Standard_Deviation, Histories_with_Scorer_Active, Count_in_Bin, Max", comments="") 
            self.log(f"Saved merged isocenter file to {os.path.join(self.folder.get(), f'{self.descriptionentry.get().strip()}_iso.csv')}")
            self.parent.pbvar.set(0)
            
        if self.dvh.get():
            self.structures.calculate_dvhs()
        
        self.log("Merging complete. Done!")
        
    def read_iso_csv(self, f, scale):
        
        with open(f, "r") as file:
            lines = file.readlines()[9:]
            
        data = []
        for line in lines:
            l = line.split(",")
            data += [float(l[3])*scale, float(l[4])*scale, int(l[5]), int(l[6]), float(l[7])*scale]
        return np.array(data).reshape(-1, 5)  
    
    def add_iso_data(self, data, data2):
        for i in range(len(data)):
            data[i][0] += data2[i][0]
            data[i][1] = np.sqrt( data[i][1]**2 + data2[i][1]*+2)
            data[i][2] += data2[i][2]
            data[i][3] += data2[i][3]
            data[i][4] = max([data[i][4], data2[i][4]])
        return data
          
        
    def init_tab2(self):
        ### TAB 2 ###
        self.tab("RTPLAN").grid_propagate(False)
        self.tab("RTPLAN").columnconfigure(0, minsize=30)
        self.tab("RTPLAN").columnconfigure(1, weight=1)
        self.tab("RTPLAN").columnconfigure(2, weight=1)
        self.tab("RTPLAN").columnconfigure(3, weight=1)
        
        self.rtplanlabel = ctk.CTkLabel(self.tab("RTPLAN"), text="Load MU sequence from RTPLAN", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.rtplanlabel.grid(row=0, column=1, columnspan=4, sticky="nsew", padx=5, pady=(20,1))
        self.rtplan_checkbox = ctk.CTkCheckBox(self.tab("RTPLAN"), text="", width=30, command=self.reveal_button)
        self.rtplan_checkbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=(20,1))
        self.dicomimage = ctk.CTkImage(dark_image=Image.open(self.resource_path(os.path.join("src","images","dcm.ico"))), size=(40,24))
        self.rtplan_button = ctk.CTkButton(self.tab("RTPLAN"), image=self.dicomimage, compound="left", text="Load RTPLAN", width=30, command=self.load_mu_sequence)
        
        self.mergeisolabel = ctk.CTkLabel(self.tab("RTPLAN"), text="Merge Isocenter data", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.mergeiso = ctk.BooleanVar(self, value=False)
        self.mergeisocheckbox = ctk.CTkCheckBox(self.tab("RTPLAN"), text="", width=30, variable = self.mergeiso)
        self.mergeisolabel.grid(row=3, column=1, columnspan=4, sticky="nsew", padx=5, pady=(20,1))
        self.mergeisocheckbox.grid(row=3, column=0, sticky="nsew", padx=5, pady=(20,1))
        
    def reveal_button(self):
        if self.rtplan_checkbox._check_state == True:
            self.rtplan_button.grid(row=1, column=1, sticky="nsw", padx=5, pady=(20,1))
            self.mus_checkbox.deselect()
            try: self.scrollframe.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=(20,1))
            except Exception: pass
        else:
            self.rtplan_button.grid_forget()
            try: self.scrollframe.grid_forget()
            except Exception: pass
        
    def toggle_mus(self):
        if self.mus_checkbox._check_state == True:
            self.rtplan_checkbox.deselect()
        
    def load_mu_sequence(self):
        
        path = askopenfilename(filetypes=[("RTPLAN", "*.dcm")])
        if path != "":
            self.log(f"Loading MU sequence from {path}")
            sequence = []
            ds = dcmread(path)
            for i in range(len(ds.BeamSequence)):
                temp = [0]
                if len(ds.BeamSequence[i].ControlPointSequence) == 2:
                    mus = ds.FractionGroupSequence[0].ReferencedBeamSequence[i].BeamMeterset
                    temp.append(ds.BeamSequence[i].ControlPointSequence[1].CumulativeMetersetWeight * mus)
                else:
                    for j in range(len(ds.BeamSequence[i].ControlPointSequence)):
                        mus = ds.FractionGroupSequence[0].ReferencedBeamSequence[i].BeamMeterset
                        temp.append(ds.BeamSequence[i].ControlPointSequence[j].CumulativeMetersetWeight * mus)
                sequence.append(np.diff(temp))
            sequence = np.array(sequence)
            self.fractions = ds.FractionGroupSequence[0].NumberOfFractionsPlanned
            self.sequence = sequence
            self.log(f"Number of fractions: {self.fractions}")
            self.log(f"Number of beams: {len(sequence)}")
            self.log(f"Number of control points: {len(sequence.flatten())}")
            self.log(f"Total MU: {round(np.sum(sequence.flatten()),3)}")
            self.scrollframe = MU_Sequence(self.tab("RTPLAN"), sequence)
            self.scrollframe.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=(20,1))
                                             
        else:
            self.log("No RTPLAN selected")
            
    def init_tab3(self):
        ### TAB 3 ###
        self.tab("DVH").grid_propagate(False)
        self.tab("DVH").columnconfigure(0, minsize=30)
        self.tab("DVH").columnconfigure(1, weight=1)
        self.tab("DVH").columnconfigure(2, weight=1)
        self.rtdose = ""
        
        self.dvhlabel = ctk.CTkLabel(self.tab("DVH"), text="Calculate DVH", font=("Bahnschrift",14), fg_color="#2B2B2B", anchor="w")
        self.dvhlabel.grid(row=0, column=1, columnspan=4, sticky="nsew", padx=5, pady=(20,1))
        self.dvh = ctk.BooleanVar(self, value=False)
        self.dvh_checkbox = ctk.CTkCheckBox(self.tab("DVH"), text="", width=30, command=self.reveal_button2, variable = self.dvh)
        self.dvh_checkbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=(20,1))
        self.structures = StructureSelector(self.tab("DVH"))
        self.rtstruct_button = ctk.CTkButton(self.tab("DVH"), image=self.dicomimage, compound="left", text="Load RTSTRUCT", width=30, command=self.load_structures)
        self.rtdosebutton = ctk.CTkButton(self.tab("DVH"), image=self.dicomimage, compound="left", text="Load RTDOSE", width=30, command=self.load_dose)

    def reveal_button2(self):
        if self.dvh_checkbox.get() == True:
            self.rtstruct_button.grid(row=1, column=1, sticky="nsw", padx=5, pady=(20,1))
            self.rtdosebutton.grid(row=1, column=2, sticky="nsw", padx=5, pady=(20,1))
        else:
            self.rtstruct_button.grid_forget()
            self.rtdosebutton.grid_forget()
            try: self.structures.grid_forget()
            except Exception: pass
        
    def load_structures(self):
        self.rtstruct = askopenfilename(filetypes=[("RTSTRUCT", "*.dcm")])
        try: self.structures.grid(row=2, column=1, columnspan=3, sticky="nsew", padx=5, pady=(20,1))
        except Exception: pass
        if self.rtstruct != "":
            self.log(f"Loading structures from {self.rtstruct}")
            self.structures.create_buttons()
            self.structures.show_buttons()
    
    def load_dose(self):
        self.rtdose = askopenfilename(filetypes=[("RTSTRUCT", "*.dcm")])
        if self.rtdose != "":
            self.log(f"Loading reference dose from {self.rtstruct}")
        
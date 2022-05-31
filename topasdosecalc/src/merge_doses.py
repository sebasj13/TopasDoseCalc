import threading
from datetime import datetime

import numpy as np
from pydicom import dcmread, uid


def merge_doses(root, frame, progressbar, button, output, frame2, log):

    output.add_text("Begun job...")

    try:

        initial_file = dcmread(frame.simulations[0])

        try:
            initial_file.SeriesDescription = frame.newseriesdescription
        except Exception:
            try:
                initial_file.SeriesDescription = frame.seriesdescriptionentry.get()
                frame.newseriesdescription = initial_file.SeriesDescription
                if frame.newseriesdescription == "":
                    raise Exception
                output.add_text(
                    f"Set output series description to {frame.newseriesdescription}"
                )
            except Exception:
                output.add_text("Invalid series description!")
                return

        array = initial_file.pixel_array * initial_file.DoseGridScaling * frame.mus[0]

        hist_cal = frame.histories
        try:
            hist_sum = frame.simulated_histories
        except Exception:
            try:
                hist_sum = int(frame.simhistoriesentry.get())
                frame.simulated_histories = hist_sum
                output.add_text(f"Set simulated histories to: {hist_sum}")
            except Exception:
                output.add_text("Invalid simulated histories entry!")
                return

        dose_cal = frame.avg_dose
        fx = frame.fractions

        button.grid_forget()
        progressbar.grid(row=2, column=0, columnspan=4, padx=(5, 5), pady=(5, 5))
        log.grid(row=2, column=4, padx=(5, 5), pady=(5, 5))

        progressbar["value"] += 100 / len(frame.simulations)

        threading.Thread(target=lambda: frame2.calculate_dvhs()).start()

        def run_merge(frame, array):
            for i in range(1, len(frame.simulations)):

                with dcmread(frame.simulations[i]) as dicom:
                    scale = (
                        dicom.DoseGridScaling
                        * 1
                        / dose_cal
                        * frame.mus[i]
                        / 100
                        * hist_cal
                        / hist_sum
                        * fx
                    )
                    array += dicom.pixel_array * scale

                progressbar["value"] += 100 / len(frame.simulations)
                root.update_idletasks()

        threading.Thread(target=run_merge(frame, array)).start()
        root.update()

        initial_file.BitsAllocated = 32
        initial_file.BitsStored = 32
        initial_file.HighBit = 31

        initial_file.DoseGridScaling = np.max(array) / (2 ** int(initial_file.HighBit))

        pixel_array_summed = (array / initial_file.DoseGridScaling).astype(np.uint32)

        initial_file.PixelData = pixel_array_summed.tobytes()
        initial_file.SeriesDescription = frame.newseriesdescription

        dt = datetime.now()
        initial_file.InstanceCreationDate = dt.strftime("%Y%m%d")
        initial_file.ContentDate = dt.strftime("%Y%m%d")
        timeStr = dt.strftime("%H%M%S.%f")  # long format with micro seconds
        initial_file.InstanceCreationTime = timeStr
        initial_file.ContentTime = timeStr
        initial_file.SOPInstanceUID = uid.generate_uid(
            prefix=".".join(initial_file.SOPInstanceUID.split(".")[:-1]) + "."
        )
        initial_file.DoseUnits = "Gy"
        initial_file.DoseType = "PHYSICAL"
        initial_file.DoseSummationType = "PLAN"

        initial_file.save_as(
            f"C://Users//sebas//Desktop//TESTS//{frame.newseriesdescription}.dcm"
        )

        progressbar["value"] = 0

        output.add_text("(SUCCESS) All simulations succesfully scaled and merged!")

    except Exception as e:
        print(e)
        if e.__str__() == "'Configurator' object has no attribute 'simulations'":
            output.add_text("(ERROR) No or invalid simulation directory selected!")

        if e.__str__() == "'Configurator' object has no attribute 'mus'":
            output.add_text("(ERROR) No or invalid DICOM directory selected!")

        if e.__str__() == "'Configurator' object has no attribute 'histories'":
            output.add_text("(ERROR) No or invalid reference simulation file selected!")
        return

    return


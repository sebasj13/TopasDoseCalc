import numpy as np
import cv2
import matplotlib.pyplot as plt
from dcmMLC import DICOMMLC
from tkinter.filedialog import askopenfilename

plan = askopenfilename(title="Select a DICOM RT Plan")

def plan_weight(plan):
    MLC = DICOMMLC(plan)
    MLC.setPixelSpacing(2.5)
    MLC.setDimensions(int(1200*2.5/4),int(1200*2.5/4))

    def draw(beam, control_point, rotate=False, draw_edges=False):

        """Draw the MLC for a given beam and control point.
        
        Args:
            beam (int): Beam number.
            control_point (int): Control point number.
            rotate (bool, optional): Rotate the MLC. Defaults to False.
            draw_edges (bool, optional): Draw the edges of the MLC. Defaults to True.
        """                
        image = np.zeros(MLC._dimensions, np.uint8)

        center = int((image.shape[0])/2)
        mlc_positions = MLC.getBeamMLCSequence()[beam].getMLCLeafSequence()
        
        for i in range(len(mlc_positions[control_point]["LeafBank1"]["Leaf Bank 1 [mm]"])):

            leaf1 = mlc_positions[control_point]["LeafBank1"]["Leaf Bank 1 [mm]"][i]
            leaf2 = mlc_positions[control_point]["LeafBank2"]["Leaf Bank 2 [mm]"][i] 
            pointA = (center + int((leaf1*MLC.getPixelSpacing())), center + int((MLC.getLeafPositionBoundaries()["Offset [mm]"][i]*MLC.getPixelSpacing())))
            pointD = (center + int((leaf2*MLC.getPixelSpacing())), center + int((MLC.getLeafPositionBoundaries()["Offset [mm]"][i+1]*MLC.getPixelSpacing())))
            cv2.rectangle(image, pointA, pointD, (255,255,255), -1)
            
            if i == len(mlc_positions[control_point]["LeafBank1"]["Leaf Bank 1 [mm]"])-1:
                jaw1 = center + int(mlc_positions[control_point]["Jaw1"]["Jaw 1 [mm]"][0]*MLC.getPixelSpacing())
                jaw2 = center + int((mlc_positions[control_point]["Jaw2"]["Jaw 2 [mm]"][0]*MLC.getPixelSpacing()))
                jaw1PointA = (0, 0)
                jaw1PointD = (749,jaw1)
                jaw2PointA = (0,jaw2)
                jaw2PointD = (749,749)
                cv2.rectangle(image, jaw1PointA, jaw1PointD, (0,0,0), -1)
                cv2.rectangle(image, jaw2PointA, jaw2PointD, (0,0,0), -1)
            
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)        
        image = np.flip(image, axis=0)
        image =  np.array(image, dtype=np.uint8)
        return image

    MLC.DrawMLCAperture = draw
            
    def isocenter_average(img):
        y,x = img.shape
        startx = x//2-(3//2)
        starty = y//2-(3//2)    
        return np.average(img[starty:starty+3,startx:startx+3])

    sequence = []
    ds = MLC.ds
    dose = 0
    for i in range(len(ds.BeamSequence)):
        temp = [0]
        if len(ds.BeamSequence[i].ControlPointSequence) == 2:
            mus = ds.FractionGroupSequence[0].ReferencedBeamSequence[i].BeamMeterset
            dose += ds.FractionGroupSequence[0].ReferencedBeamSequence[i].BeamDose
            temp.append(ds.BeamSequence[i].ControlPointSequence[1].CumulativeMetersetWeight * mus)
        else:
            dose += ds.FractionGroupSequence[0].ReferencedBeamSequence[i].BeamDose
            for j in range(len(ds.BeamSequence[i].ControlPointSequence)):
                mus = ds.FractionGroupSequence[0].ReferencedBeamSequence[i].BeamMeterset
                temp.append(ds.BeamSequence[i].ControlPointSequence[j].CumulativeMetersetWeight * mus)
        sequence += np.diff(temp).tolist()
    sequence = np.array(sequence)

    apertures = MLC.DrawEntireMLCSequence()

    mu_fields = [np.multiply(apertures[i],sequence[i]) for i in range(len(apertures))]
    integrated_image = np.sum([mu_fields[i] for i in range(len(mu_fields))], axis=0)/(255*np.sum(sequence))
    print(f"Total MUs: {round(np.sum(sequence),4)} Gy")
    print(f"Total dose: {round(dose,4)} Gy")
    print(f"{(nz:=np.count_nonzero(sequence))} fields contributing MU")
    print(f"Normalized intensity in the isocenter: {(iso:=round(isocenter_average(integrated_image), 4))}")
    print(f"Normalized total intensity: {round(np.average(integrated_image),4)}")
    print(f"Relative isocenter intensity: {(r:=round(isocenter_average(integrated_image)/np.average(integrated_image),4))}")
    print(f"Determined history cost: {round((r/iso)/nz,3)}")
    plt.imshow(integrated_image, cmap="gray")
    plt.show()
    
if __name__ == "__main__":
    plan_weight(plan)


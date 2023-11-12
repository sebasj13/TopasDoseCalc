import cv2
import imutils
import pydicom
import numpy as np
import pandas as pd

from dataclasses import dataclass

@dataclass
class DICOMBeamMLC:
    """Class to represent the MLC Sequence for a beam.
    """

    def __init__(self, control_points:int, collimator_angle:float, mlc_leaf_sequence: dict, gantry_angles:list) -> None:
        """Initialize the DICOMBeamMLC class.

        Args:
            control_points (int): Number of control points.
            collimator_angle (float): Collimator angle.
            mlc_leaf_sequence (dict): MLC leaf sequence.
            gantry_angles (list): Gantry angles.
        """

        self._control_points = control_points
        self._collimator_angle = collimator_angle
        self._mlc_leaf_sequence = mlc_leaf_sequence	
        self._gantry_angles = gantry_angles


    def getNumberOfControlPoints(self) -> int:
        """Get the number of control points.

        Returns:
            int: Number of control points.
        """

        return self._control_points

    def getCollimatorAngle(self) -> float:
        """Get the collimator angle.

        Returns:
            float: Collimator angle.
        """

        return self._collimator_angle

    def getMLCLeafSequence(self) -> dict:
        """Get the MLC leaf sequence.

        Returns:
            dict: MLC leaf sequence.
        """

        return self._mlc_leaf_sequence

    def getGantryAngles(self) -> list:
        """Get the gantry angles.

        Returns:
            list: Gantry angles.
        """

        return self._gantry_angles


class DICOMMLC:
    """Class to represent the MLC Sequence for a DICOM plan. The MLC sequence is
    a list of DICOMBeamMLC objects. The MLC can be drawn and animated. Using edge detection,
    the center of gravity of the MLC openings can be determined.
    """

    def __init__(self, RTPlan) -> None:
        """Initialize the DICOMMLC class.

        Args:
            RTPlan (pathlike or pydicom.FileDataset): DICOM dataset.
        """

        if type(RTPlan) == str:
            self.ds = pydicom.dcmread(RTPlan)
        elif type(RTPlan) == pydicom.FileDataset:
            self.ds = RTPlan
        else:
            raise TypeError("The input must be a path to the DICOM RTPLAN file or the dataset containing the DICOM information.")
        
        if self.ds.Modality != "RTPLAN":
            raise TypeError("The file is not a DICOM RTPLAN file")


        self._number_of_beams = len(self.ds.BeamSequence)

        for i in range(len(self.ds.BeamSequence[0].BeamLimitingDeviceSequence)):
            if self.ds.BeamSequence[0].BeamLimitingDeviceSequence[i].RTBeamLimitingDeviceType in ["MLCX","MLCY"] :
                mlc_index = i
                leaf_pairs = self.ds.BeamSequence[0].BeamLimitingDeviceSequence[i].NumberOfLeafJawPairs
                mlc_offsets = pd.DataFrame({"Offset [mm]":self.ds.BeamSequence[0].BeamLimitingDeviceSequence[i].LeafPositionBoundaries})
                break
            
        self._leaf_pairs = int(leaf_pairs)
        self._leaf_position_boundaries = mlc_offsets
        self._leaf_positions = self._InitializeLeafPositions()
        self._beam_mlc_sequence = self._InitializeBeamMLCSequence()

        self._image_width = 1200
        self._image_height = 1200
        self._dimensions = (self._image_width, self._image_height, 3)
        self._pixel_spacing = 4

    def __str__(self):
        """String representation of the DICOMMLC object.

        Returns:
            str: String representation.
        """

        return


    def _InitializeLeafPositions(self) -> pd.DataFrame:
        """Calculate the leaf centers from the leaf position boundaries.

        Returns:
            pd.DataFrame: Leaf positions.
        """


        leaf_positions = pd.DataFrame({"Position [mm]": [
            np.mean(
                [
                    self.getLeafPositionBoundaries()["Offset [mm]"][i],
                    self.getLeafPositionBoundaries()["Offset [mm]"][i + 1],
                ]
            )
            for i in range(len(self.getLeafPositionBoundaries()["Offset [mm]"]) - 1)
        ]})

        return leaf_positions

    def _InitializeBeamMLCSequence(self) -> list:
        """Initialize the beam MLC sequence.

        Args:

        Returns:
            list: Beam MLC sequence.
        """

        beam_mlc_sequence = {}
        self._control_points = 0

        for i in range(self._number_of_beams):
            mlc_positions = {}
            control_points = len(self.ds.BeamSequence[i].ControlPointSequence)
            self._control_points += control_points
            collimator_angle = float(self.ds.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)
            try:
                gantry_angles = [self.ds.BeamSequence[i].ControlPointSequence[j].GantryAngle for j in range(control_points)]
            except AttributeError:
                gantry_angles = [self.ds.BeamSequence[i].ControlPointSequence[0].GantryAngle for j in range(control_points)]
            for j in range(control_points):
                if self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence[0].RTBeamLimitingDeviceType in ["ASYMX","ASYMY"] :
                    Jaw1 = [self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence[0].LeafJawPositions[0]]
                    Jaw2 = [self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence[0].LeafJawPositions[1]]
                else:
                    Jaw1 = [Jaw1[-1]]
                    Jaw2 = [Jaw2[-1]]
                for mlc_index in range(len(self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence)):
                    if self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence[mlc_index].RTBeamLimitingDeviceType in ["MLCX","MLCY"] :
                        break

                LeafBank1 = []
                LeafBank2 = []
                LeafBank1 += self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence[mlc_index].LeafJawPositions[:self.getLeafPairs()]
                LeafBank2 += self.ds.BeamSequence[i].ControlPointSequence[j].BeamLimitingDevicePositionSequence[mlc_index].LeafJawPositions[self.getLeafPairs():]
                
                mlc_positions[j] = {}
                mlc_positions[j]["LeafBank1"] = pd.DataFrame({"Leaf Bank 1 [mm]":LeafBank1})	
                mlc_positions[j]["LeafBank2"] = pd.DataFrame({"Leaf Bank 2 [mm]":LeafBank2})	
                mlc_positions[j]["Jaw1"] = pd.DataFrame({"Jaw 1 [mm]":Jaw1})
                mlc_positions[j]["Jaw2"] = pd.DataFrame({"Jaw 2 [mm]":Jaw2})

            beam_mlc_sequence[i] = DICOMBeamMLC(control_points, collimator_angle, mlc_positions, gantry_angles)

        return beam_mlc_sequence

    def DrawEntireMLCSequence(self, rotate=False, draw_edges=True):
        """Draw the entire MLC sequence.

        Args:
            rotate (bool, optional): Rotate the MLC. Defaults to False.
            draw_edges (bool, optional): Draw the edges of the MLC. Defaults to True.
        """

        images = []
        for i in range(self.getNumberOfBeams()):
            for j in range(self.getBeamMLCSequence()[i].getNumberOfControlPoints()):
                images.append(self.DrawMLCAperture(i, j, rotate, draw_edges))

        return np.array(images)


    def DrawMLCAperture(self, beam, control_point, rotate=False, draw_edges=True):
        """Draw the MLC for a given beam and control point.
        
        Args:
            beam (int): Beam number.
            control_point (int): Control point number.
            rotate (bool, optional): Rotate the MLC. Defaults to False.
            draw_edges (bool, optional): Draw the edges of the MLC. Defaults to True.
        """                

        image = np.zeros(self._dimensions, np.uint8)

        center = int((image.shape[0])/2)
        collimator_angle = self.getBeamMLCSequence()[beam].getCollimatorAngle()
        mlc_length = 100 * self.getPixelSpacing()
        mlc_positions = self.getBeamMLCSequence()[beam].getMLCLeafSequence()
        
        for i, leaf in enumerate(mlc_positions[control_point]["LeafBank1"]["Leaf Bank 1 [mm]"]):

            pointA = (center + int((leaf*self.getPixelSpacing())), center + int((self.getLeafPositionBoundaries()["Offset [mm]"][i]*self.getPixelSpacing())))
            pointB = (center + int((leaf*self.getPixelSpacing())), center + int((self.getLeafPositionBoundaries()["Offset [mm]"][i+1]*self.getPixelSpacing())))
            pointC = (pointA[0]-mlc_length, pointA[1])
            pointD = (pointB[0]-mlc_length, pointB[1])
            
            cv2.rectangle(image, pointA, pointD, (255,255,255), -1)
            if draw_edges:
                cv2.line(image, pointA, pointB, (0,0,255), 1)
                cv2.line(image, pointA, pointC, (0,0,255), 1)
                cv2.line(image, pointC, pointD, (0,0,255), 1)
                cv2.line(image, pointB, pointD, (0,0,255), 1)
            
        for i, leaf in enumerate(mlc_positions[control_point]["LeafBank2"][" Leaf Bank 2 [mm]"]):

            pointA = (center + int((leaf*self.getPixelSpacing())), center + int((self.getLeafPositionBoundaries()["Offset [mm]"][i]*self.getPixelSpacing())))
            pointB = (center + int((leaf*self.getPixelSpacing())), center + int((self.getLeafPositionBoundaries()["Offset [mm]"][i+1]*self.getPixelSpacing())))
            pointC = (pointA[0]+mlc_length, pointA[1])
            pointD = (pointB[0]+mlc_length, pointB[1])
            
            cv2.rectangle(image, pointA, pointD, (255,255,255), -1)
            if draw_edges:
                cv2.line(image, pointA, pointB, (0,0,255), 1)
                cv2.line(image, pointA, pointC, (0,0,255), 1)
                cv2.line(image, pointC, pointD, (0,0,255), 1)
                cv2.line(image, pointB, pointD, (0,0,255), 1)
            
        image = np.flip(image, axis=0)
        if rotate:
            image = imutils.rotate_bound(image, -collimator_angle) 

        return np.array(image, dtype=np.uint8)
    
    def FindApertureCenters(self, beam:int, control_point:int, lower_area_bound:int, upper_area_bound:int) -> tuple:
        """Find the center of the aperture for a given beam and control point.

        Args:
            beam (int): Beam number.
            control_point (int): Control point number.
            lower_area_bound (int): Lower bound for the area of the aperture.
            upper_area_bound (int): Upper bound for the area of the aperture.

        Returns:
            tuple: Tuple containing the center of the aperture.
        """
        
        image = self.DrawMLCAperture(beam, control_point, rotate=True, draw_edges=False)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        #create a blank copy of the image
        blank = np.zeros(image.shape, dtype=np.uint8)
        stencil  = blank.copy().astype(np.uint8)
        edges = cv2.Canny(image,100,200)

        contours, _ = cv2.findContours(edges, 1, 2)

        centers = []
        for contour in contours:
            stencil  = np.zeros(image.shape, dtype=np.uint8)
            cv2.fillConvexPoly(stencil, contour, 100)
            counts = cv2.countNonZero(stencil)

            if counts <= upper_area_bound and counts >= lower_area_bound:
                moments = cv2.moments(contour)
                try:
                    cX = int(moments["m10"] / moments["m00"])
                    cY = int(moments["m01"] / moments["m00"])
                except ZeroDivisionError:
                    continue
                if centers == []:
                    centers += [(cX, cY)]
                    cv2.circle(stencil, (cX, cY), 5, (0, 0, 255), -1)
                #check the centers list to see if a cenetr point +-2 pixels is already in the list
                if len(centers) > 0:
                    for center in centers:
                        if abs(center[0] - cX) < 2 and abs(center[1] - cY) < 2:
                            break
                    else:
                        centers += [(cX, cY)]
                        cv2.circle(stencil, (cX, cY), 5, (0, 0, 255), -1)
                        continue
                    
        return centers

    def getNumberOfBeams(self) -> int:
        """Get the number of beams.

        Returns:
            int: Number of beams.
        """

        return self._number_of_beams
    
    def getNumberOfControlPoints(self) -> int:
        """Get the number of control points.

        Returns:
            int: Number of control points.
        """

        return self._control_points


    def getLeafPairs(self) -> int:
        """Get the number of leaf pairs.

        Returns:
            int: Number of leaf pairs.
        """

        return self._leaf_pairs

    def getLeafPositionBoundaries(self) -> pd.DataFrame:
        """Get the leaf position boundaries.

        Returns:
            pd.DataFrame: Leaf position boundaries.
        """

        return self._leaf_position_boundaries

    def getLeafPositions(self) -> pd.DataFrame:
        """Get the leaf positions.

        Returns:
            pd.DataFrame: Leaf positions.
        """

        return self._leaf_positions

    def getBeamMLCSequence(self) -> list:
        """Get the beam MLC sequence.

        Returns:
            list: Beam MLC sequence.
        """

        return self._beam_mlc_sequence        

    def setImageWidth(self, width: int) -> None:
        """Set the width of the output array in pixels.

        Args:
            width (int): Width in pixels.
        """
        if width > 0:
            self._image_width = width
            self._dimensions = (self.image_width, self.image_height, 3)    
        else:
            raise ValueError("^Width must be greater than 0")
        
    def getImageWidth(self) -> int:
        """Get the width of the output array in pixels.

        Returns:
            int: Width in pixels.
        """
        return self._image_width	   
        	
    def setImageHeight(self, height: int) -> None:
        """Set the height of the output array in pixels.

        Args:
            height (int): Height in pixels.
        """
        if height > 0:
            self._image_height = height	
            self._dimensions = (self._image_width, self._image_heigh, 3)	
        else:
            raise ValueError("Height must be greater that 0")
        
    def getImageHeight(self) -> int:
        """Get the height of the output array in pixels.

        Returns:
            int: Height in pixels.
        """
        return self._image_height	
    
    def setDimensions(self, width:int, height:int) -> None:
        """Set the dimensions of the output array in pixels.

        Args:
            width (int): Width in pixels.
            height (int): Height in pixels.
        """
        if width >0 and height > 0:
            self._image_width = width	
            self._image_height = height
            self._dimensions = (self._image_width, self._image_height, 3)	
        else:
            raise ValueError("Dimensions must be greater than 0")
        
    def getDimensions(self) -> tuple:
        """Get the dimensions of the output array in pixels.

        Returns:
            tuple: Dimensions in pixels.	
        """
        return (self._dimensions[0], self._dimensions[1])	
    
    def setPixelSpacing(self, x: int) -> None:
        if x > 0:
            self._pixel_spacing = x
        else:
            raise ValueError("Pixel spacing must be greater than 0")
        
    def getPixelSpacing(self) -> int:
        """Set the pixel spacing of the output array in pixels.

        Returns:
            int: Pixel spacing in pixels.		
        """
        return self._pixel_spacing
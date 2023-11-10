from dicompylercore import dicomparser
import collections
from six import iteritems
import numpy as np
import matplotlib
import pymedphys
import time

# Copyright (C) 2015-2018 Simon Biggs
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Compare two dose grids with the gamma index.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional
from warnings import warn

from pymedphys._imports import numpy as np
from pymedphys._imports import scipy
import pymedphys._utilities.createshells

DEFAULT_RAM = int(2**30 * 1.5)  # 1.5 GB


def gamma(
    axes_reference,
    dose_reference,
    axes_evaluation,
    dose_evaluation,
    pbvar,
    dose_percent_threshold,
    distance_mm_threshold,
    lower_percent_dose_cutoff=20,
    interp_fraction=10,
    max_gamma=None,
    local_gamma=False,
    global_normalisation=None,
    skip_once_passed=False,
    random_subset=None,
    ram_available=DEFAULT_RAM,
    quiet=None,
):
    """Compare two dose grids with the gamma index.

    It computes 1, 2, or 3 dimensional gamma with arbitrary gird sizes while
    interpolating on the fly. This function makes use of some of the ideas
    presented within <http://dx.doi.org/10.1118/1.2721657>.

    Parameters
    ----------
    axes_reference : tuple
        The reference coordinates.
    dose_reference : np.array
        The reference dose grid. Each point in the reference grid becomes the
        centre of a Gamma ellipsoid. For each point of the reference, nearby
        evaluation points are searched at increasing distances.
    axes_evaluation : tuple
        The evaluation coordinates.
    dose_evaluation : np.array
        The evaluation dose grid. Evaluation here is defined as the grid which
        is interpolated and searched over at increasing distances away from
        each reference point.
    dose_percent_threshold : float
        The percent dose threshold
    distance_mm_threshold : float
        The gamma distance threshold. Units must
        match of the coordinates given.
    lower_percent_dose_cutoff : float, optional
        The percent lower dose cutoff below which gamma will not be calculated.
        This is only applied to the reference grid.
    interp_fraction : float, optional
        The fraction which gamma distance threshold is divided into for
        interpolation. Defaults to 10 as recommended within
        <http://dx.doi.org/10.1118/1.2721657>. If a 3 mm distance threshold is chosen
        this default value would mean that the evaluation grid is interpolated at
        a step size of 0.3 mm.
    max_gamma : float, optional
        The maximum gamma searched for. This can be used to speed up
        calculation, once a search distance is reached that would give gamma
        values larger than this parameter, the search stops. Defaults to :obj:`np.inf`
    local_gamma
        Designates local gamma should be used instead of global. Defaults to
        False.
    global_normalisation : float, optional
        The dose normalisation value that the percent inputs calculate from.
        Defaults to the maximum value of :obj:`dose_reference`.
    random_subset : int, optional
        Used to only calculate a random subset of the reference grid. The
        number chosen is how many random points to calculate.
    ram_available : int, optional
        The number of bytes of RAM available for use by this function. Defaults
        to 0.8 times your total RAM as determined by psutil.
    quiet : bool, optional
        Deprecated but maintained for now for backwards compatibility.
        `pymedphys.gamma` now utilises the `logging` module. You can set
        your desired verbosity by setting the corresponding logging
        level. Basic information is given for the `info` level.
        Additional information using for benchmarking or troubleshooting
        performance is provided for the `debug` level.

    Returns
    -------
    gamma
        The array of gamma values the same shape as that
        given by the reference coordinates and dose.
    """

    if max_gamma is None:
        max_gamma = np.inf

    options = GammaInternalFixedOptions.from_user_inputs(
        axes_reference,
        dose_reference,
        axes_evaluation,
        dose_evaluation,
        dose_percent_threshold,
        distance_mm_threshold,
        lower_percent_dose_cutoff,
        interp_fraction,
        max_gamma,
        local_gamma,
        global_normalisation,
        skip_once_passed,
        random_subset,
        ram_available,
        quiet,
    )

    if options.local_gamma:
        logging.info("Computing the gamma using local normalisation point")
    else:
        logging.info("Computing the gamma using global normalisation point")

    logging.info("Global normalisation set to %.3f", options.global_normalisation)
    logging.info(
        "Global dose threshold set to %.3f (%.2f%% of normalisation)",
        options.global_dose_threshold,
        options.dose_percent_threshold,
    )

    logging.info("Distance threshold set to %s", options.distance_mm_threshold)
    logging.info(
        "Lower dose cutoff set to %.3f (%.1f%% of normalisation)",
        options.lower_dose_cutoff,
        lower_percent_dose_cutoff,
    )

    current_gamma = gamma_loop(options, pbvar)

    gamma = {}
    for i, dose_threshold in enumerate(options.dose_percent_threshold):
        for j, distance_threshold in enumerate(options.distance_mm_threshold):
            key = (dose_threshold, distance_threshold)

            gamma_temp = current_gamma[:, i, j]
            gamma_temp = np.reshape(gamma_temp, np.shape(dose_reference))
            gamma_temp[np.isinf(gamma_temp)] = np.nan

            with np.errstate(invalid="ignore"):
                gamma_greater_than_ref = gamma_temp > max_gamma
                gamma_temp[gamma_greater_than_ref] = max_gamma

            gamma[key] = gamma_temp

    logging.info("Complete!")

    if len(gamma.keys()) == 1:
        gamma = next(iter(gamma.values()))

    return gamma


def expand_dims_to_1d(array):
    array = np.array(array)
    dims = len(np.shape(array))

    if dims == 0:
        return array[None]

    if dims == 1:
        return array

    raise ValueError("Expected a 0-d or 1-d array")


@dataclass(frozen=True)
class GammaInternalFixedOptions:
    flat_mesh_axes_reference: Any
    flat_dose_reference: Any
    reference_points_to_calc: Any
    dose_percent_threshold: Any
    distance_mm_threshold: Any
    evaluation_interpolation: Callable
    interp_fraction: int
    max_gamma: float
    lower_dose_cutoff: float = 0
    maximum_test_distance: float = -1
    global_normalisation: Optional[float] = None
    local_gamma: bool = False
    skip_once_passed: bool = False
    ram_available: Optional[int] = DEFAULT_RAM
    quiet: Any = None

    def __post_init__(self):
        self.set_defaults()

    def set_defaults(self):
        if self.maximum_test_distance == -1:
            object.__setattr__(self, "maximum_test_distance", np.inf)

        if self.global_normalisation is None:
            object.__setattr__(
                self, "global_normalisation", np.max(self.flat_dose_reference)
            )

    @property
    def global_dose_threshold(self):
        return self.dose_percent_threshold / 100 * self.global_normalisation

    @classmethod
    def from_user_inputs(
        cls,
        axes_reference,
        dose_reference,
        axes_evaluation,
        dose_evaluation,
        dose_percent_threshold,
        distance_mm_threshold,
        lower_percent_dose_cutoff=20,
        interp_fraction=10,
        max_gamma=None,
        local_gamma=False,
        global_normalisation=None,
        skip_once_passed=False,
        random_subset=None,
        ram_available=None,
        quiet=None,
    ):

        if max_gamma is None:
            max_gamma = np.inf


        dose_percent_threshold = expand_dims_to_1d(dose_percent_threshold)
        distance_mm_threshold = expand_dims_to_1d(distance_mm_threshold)

        if global_normalisation is None:
            global_normalisation = np.max(dose_reference)

        lower_dose_cutoff = lower_percent_dose_cutoff / 100 * global_normalisation

        maximum_test_distance = np.max(distance_mm_threshold) * max_gamma

        evaluation_interpolation = scipy.interpolate.RegularGridInterpolator(
            axes_evaluation,
            np.array(dose_evaluation),
            bounds_error=False,
            fill_value=np.inf,
        )

        dose_reference = np.array(dose_reference)
        reference_dose_above_threshold = dose_reference >= lower_dose_cutoff

        mesh_axes_reference = np.meshgrid(*axes_reference, indexing="ij")
        flat_mesh_axes_reference = np.array(
            [np.ravel(item) for item in mesh_axes_reference]
        )

        reference_points_to_calc = reference_dose_above_threshold
        reference_points_to_calc = np.ravel(reference_points_to_calc)

        if random_subset is not None:
            to_calc_index = np.where(reference_points_to_calc)[0]

            np.random.shuffle(to_calc_index)
            random_subset_to_calc = np.full_like(
                reference_points_to_calc, False, dtype=bool
            )
            random_subset_to_calc[  # pylint: disable=unsupported-assignment-operation
                to_calc_index[0:random_subset]
            ] = True

            reference_points_to_calc = random_subset_to_calc

        flat_dose_reference = np.ravel(dose_reference)

        return cls(
            flat_mesh_axes_reference,
            flat_dose_reference,
            reference_points_to_calc,
            dose_percent_threshold,
            distance_mm_threshold,
            evaluation_interpolation,
            interp_fraction,
            max_gamma,
            lower_dose_cutoff,
            maximum_test_distance,
            global_normalisation,
            local_gamma,
            skip_once_passed,
            ram_available,
            quiet,
        )


def gamma_loop(options: GammaInternalFixedOptions, pbvar):

    still_searching_for_gamma = np.full_like(
        options.flat_dose_reference, True, dtype=bool
    )

    current_gamma = np.inf * np.ones(
        (
            len(options.flat_dose_reference),
            len(options.dose_percent_threshold),
            len(options.distance_mm_threshold),
        )
    )

    distance_step_size = np.min(options.distance_mm_threshold) / options.interp_fraction

    to_be_checked = options.reference_points_to_calc & still_searching_for_gamma
    distance = 0.0

    force_search_distances = np.sort(options.distance_mm_threshold)
    while distance <= options.maximum_test_distance:
        pbvar.set(distance/options.maximum_test_distance)
        logging.debug(
            "Current distance: %.2f mm | " "Number of reference points remaining: %i",
            distance,
            np.sum(to_be_checked),
        )

        min_relative_dose_difference = calculate_min_dose_difference(
            options, distance, to_be_checked, distance_step_size
        )

        current_gamma, still_searching_for_gamma_all = multi_thresholds_gamma_calc(
            options,
            current_gamma,
            min_relative_dose_difference,
            distance,
            to_be_checked,
        )

        still_searching_for_gamma = np.any(
            np.any(still_searching_for_gamma_all, axis=-1), axis=-1
        )

        to_be_checked = options.reference_points_to_calc & still_searching_for_gamma

        if np.sum(to_be_checked) == 0:
            break

        relevant_distances = options.distance_mm_threshold[
            np.any(
                np.any(
                    options.reference_points_to_calc[:, None, None]
                    & still_searching_for_gamma_all,
                    axis=0,
                ),
                axis=0,
            )
        ]

        distance_step_size = np.min(relevant_distances) / options.interp_fraction

        distance_step_size = np.max(
            [distance / options.interp_fraction / options.max_gamma, distance_step_size]
        )

        distance += distance_step_size
        if len(force_search_distances) != 0:
            if distance >= force_search_distances[0]:
                distance = force_search_distances[0]
                force_search_distances = np.delete(force_search_distances, 0)
    pbvar.set(0)
    return current_gamma


def multi_thresholds_gamma_calc(
    options: GammaInternalFixedOptions,
    current_gamma,
    min_relative_dose_difference,
    distance,
    to_be_checked,
):

    gamma_at_distance = np.sqrt(
        (
            min_relative_dose_difference[:, None, None]
            / (options.dose_percent_threshold[None, :, None] / 100)
        )
        ** 2
        + (distance / options.distance_mm_threshold[None, None, :]) ** 2
    )

    current_gamma[to_be_checked, :, :] = np.min(
        np.concatenate(
            [
                gamma_at_distance[None, :, :, :],
                current_gamma[None, to_be_checked, :, :],
            ],
            axis=0,
        ),
        axis=0,
    )

    still_searching_for_gamma = current_gamma > (
        distance / options.distance_mm_threshold[None, None, :]
    )

    if options.skip_once_passed:
        still_searching_for_gamma = still_searching_for_gamma & (current_gamma >= 1)

    return current_gamma, still_searching_for_gamma


def calculate_min_dose_difference(options, distance, to_be_checked, distance_step_size):
    """Determine the minimum dose difference.

    Calculated for a given distance from each reference point.
    """

    min_relative_dose_difference = np.nan * np.ones_like(
        options.flat_dose_reference[to_be_checked]
    )

    num_dimensions = np.shape(options.flat_mesh_axes_reference)[0]

    coordinates_at_distance_shell = pymedphys._utilities.createshells.calculate_coordinates_shell(  # pylint: disable = protected-access
        distance, num_dimensions, distance_step_size
    )

    num_points_in_shell = np.shape(coordinates_at_distance_shell)[1]

    estimated_ram_needed = (
        np.uint64(num_points_in_shell)
        * np.uint64(np.count_nonzero(to_be_checked))
        * np.uint64(32)
        * np.uint64(num_dimensions)
        * np.uint64(2)
    )

    num_slices = np.floor(estimated_ram_needed / options.ram_available).astype(int) + 1

    logging.debug(
        "Points tested per reference point: %i | RAM split count: %i",
        num_points_in_shell,
        num_slices,
    )

    all_checks = np.where(np.ravel(to_be_checked))[0]
    index = np.arange(len(all_checks))
    sliced = np.array_split(index, num_slices)

    sorted_sliced = [np.sort(current_slice) for current_slice in sliced]

    for current_slice in sorted_sliced:
        to_be_checked_sliced = np.full_like(to_be_checked, False, dtype=bool)
        to_be_checked_sliced[  # pylint: disable=unsupported-assignment-operation
            all_checks[current_slice]
        ] = True

        assert np.all(to_be_checked[to_be_checked_sliced])

        axes_reference_to_be_checked = options.flat_mesh_axes_reference[
            :, to_be_checked_sliced
        ]

        evaluation_dose = interpolate_evaluation_dose_at_distance(
            options.evaluation_interpolation,
            axes_reference_to_be_checked,
            coordinates_at_distance_shell,
        )

        if options.local_gamma:
            with np.errstate(divide="ignore"):
                relative_dose_difference = (
                    evaluation_dose
                    - options.flat_dose_reference[to_be_checked_sliced][None, :]
                ) / (options.flat_dose_reference[to_be_checked_sliced][None, :])
        else:
            relative_dose_difference = (
                evaluation_dose
                - options.flat_dose_reference[to_be_checked_sliced][None, :]
            ) / options.global_normalisation

        min_relative_dose_difference[current_slice] = np.min(
            np.abs(relative_dose_difference), axis=0
        )

    return min_relative_dose_difference


def interpolate_evaluation_dose_at_distance(
    evaluation_interpolation,
    axes_reference_to_be_checked,
    coordinates_at_distance_shell,
):
    """Determine the evaluation dose for the points a given distance away for
    each reference coordinate.
    """
    all_points = add_shells_to_ref_coords(
        axes_reference_to_be_checked, coordinates_at_distance_shell
    )

    evaluation_dose = evaluation_interpolation(all_points)

    return evaluation_dose


def add_shells_to_ref_coords(
    axes_reference_to_be_checked, coordinates_at_distance_shell
):
    """Add the distance shells to each reference coordinate to make a set of
    points to be tested for this given distance"""

    coordinates_at_distance = []
    for shell_coord, ref_coord in zip(
        coordinates_at_distance_shell, axes_reference_to_be_checked
    ):

        coordinates_at_distance.append(
            np.array(ref_coord[None, :] + shell_coord[:, None])[:, :, None]
        )

    all_points = np.concatenate(coordinates_at_distance, axis=2)

    return all_points


def crop_dose_to_roi(rtdose_file, rtstruct_file, roi_number, pbvar):

    def dosegrid_extents_indices(extents, dd, padding=1):
        """Determine dose grid extents from structure extents as array indices.

        Parameters
        ----------
        extents : list
            Structure extents in patient coordintes: [xmin, ymin, xmax, ymax].
            If an empty list, no structure extents will be used in the calculation.
        dd : dict
            Dose data from dicomparser.GetDoseData.
        padding : int, optional
            Pixel padding around the structure extents.

        Returns
        -------
        list
            Dose grid extents in pixel coordintes as array indices:
            [xmin, ymin, xmax, ymax].
        """
        if not len(extents):
            return [0, 0, dd['lut'][0].shape[0] - 1, dd['lut'][1].shape[0] - 1]
        dgxmin = np.argmin(np.fabs(dd['lut'][0] - extents[0])) - padding
        if dd['lut'][0][dgxmin] > extents[0]:
            dgxmin -= 1
        dgxmax = np.argmin(np.fabs(dd['lut'][0] - extents[2])) + padding
        dgymin = np.argmin(np.fabs(dd['lut'][1] - extents[1])) - padding
        dgymax = np.argmin(np.fabs(dd['lut'][1] - extents[3])) + padding
        dgxmin = 0 if dgxmin < 0 else dgxmin
        dgymin = 0 if dgymin < 0 else dgymin
        if dgxmax == dd['lut'][0].shape[0]:
            dgxmax = dd['lut'][0].shape[0] #- 1
        if dgymax == dd['lut'][1].shape[0]:
            dgymax = dd['lut'][1].shape[0] #- 1
        return [dgxmin, dgymin, dgxmax, dgymax]


    def dosegrid_extents_positions(extents, dd):
        """Determine dose grid extents in patient coordinate indices.

        Parameters
        ----------
        extents : list
            Dose grid extents in pixel coordintes: [xmin, ymin, xmax, ymax].
        dd : dict
            Dose data from dicomparser.GetDoseData.

        Returns
        -------
        list
            Dose grid extents in patient coordintes: [xmin, ymin, xmax, ymax].
        """
        return [
            dd['lut'][0][extents[0]], dd['lut'][1][extents[1]],
            dd['lut'][0][extents[2]], dd['lut'][1][extents[3]]
        ]

    def get_resampled_lut(index_extents,
                        extents,
                        new_pixel_spacing,
                        min_pixel_spacing):
        """Determine the patient to pixel LUT based on new pixel spacing.

        Parameters
        ----------
        index_extents : list
            Dose grid extents as array indices.
        extents : list
            Dose grid extents in patient coordinates.
        new_pixel_spacing : float
            New pixel spacing in mm
        min_pixel_spacing : float
            Minimum pixel spacing used to determine the new pixel spacing

        Returns
        -------
        tuple
            A tuple of lists (x, y) of patient to pixel coordinate mappings.

        Raises
        ------
        AttributeError
            Raised if the new pixel_spacing is not a factor of the minimum pixel
            spacing.

        Notes
        -----
        The new pixel spacing must be a factor of the original (minimum) pixel
        spacing. For example if the original pixel spacing was ``3`` mm, the new
        pixel spacing should be: ``3 / (2^n)`` mm, where ``n`` is an integer.

        Examples
        --------
        Original pixel spacing: ``3`` mm, new pixel spacing: ``0.375`` mm
        Derived via: ``(3 / 2^16) == 0.375``

        """
        if (min_pixel_spacing % new_pixel_spacing != 0.0):
            raise AttributeError(
                "New pixel spacing must be a factor of %g/(2^n),"
                % min_pixel_spacing +
                " where n is an integer. Value provided was %g."
                % new_pixel_spacing)
        sampling_rate = np.array([
            abs(index_extents[0] - index_extents[2])+1,
            abs(index_extents[1] - index_extents[3])+1
        ])
        xsamples, ysamples = sampling_rate * min_pixel_spacing / new_pixel_spacing
        x = np.linspace(extents[0], extents[2], int(xsamples), dtype=float)
        y = np.linspace(extents[1], extents[3], int(ysamples), dtype=float)
        return x, y

    def interpolate_between_planes(planes, n=2):
        """Interpolate n additional structure planes (segments) in between planes.

        Parameters
        ----------
        planes : dict
            RT Structure plane data from dicomparser.GetStructureCoordinates.
        n : int, optional
            Number of planes to interpolate in between the existing planes.

        Returns
        -------
        dict
            Plane data with additional keys representing interpolated planes.
        """
        keymap = {np.array([k], dtype=np.float32)[0]: k for k in planes.keys()}
        sorted_keys = np.sort(np.array(list(planes.keys()), dtype=np.float32))
        num_new_samples = (len(planes.keys()) * (n + 1)) - n
        newgrid = np.linspace(sorted_keys[0], sorted_keys[-1], num_new_samples)
        new_planes = {}
        # If the plane already exists in the dictionary, use it
        # otherwise use the closest plane
        # TODO: Add actual interpolation of structure data between planes
        for plane in newgrid:
            new_plane = sorted_keys[np.argmin(np.fabs(sorted_keys - plane))]
            new_planes[plane] = planes[keymap[new_plane]]
        return new_planes

    def get_contour_mask(dd, dosegridpoints, contour):
        """Get the mask for the contour with respect to the dose plane."""
        doselut = dd['lut']

        c = matplotlib.path.Path(list(contour))

        # def inpolygon(polygon, xp, yp):
        #     return np.array(
        #         [Point(x, y).intersects(polygon) for x, y in zip(xp, yp)],
        #         dtype=np.bool)

        # p = Polygon(contour)
        # x, y = np.meshgrid(np.array(dd['lut'][0]), np.array(dd['lut'][1]))
        # mask = inpolygon(p, x.ravel(), y.ravel())
        # return mask.reshape((len(doselut[1]), len(doselut[0])))

        grid = c.contains_points(dosegridpoints)
        grid = grid.reshape((len(doselut[1]), len(doselut[0])))
        return grid 

    interpolation_resolution = 2.5
    interpolation_segments_between_planes = 1
    rtss = dicomparser.DicomParser(rtstruct_file)
    rtdose = dicomparser.DicomParser(rtdose_file)
    structures = rtss.GetStructures()
    roi = roi_number
    s = structures[roi]
    s['planes'] = rtss.GetStructureCoordinates(roi)
    s['thickness'] =  rtss.CalculatePlaneThickness(s['planes'])
    planes = collections.OrderedDict(sorted(iteritems(s['planes'])))

    if ((len(planes)) and ("PixelData" in rtdose.ds)):

        dd = rtdose.GetDoseData()
        id = rtdose.GetImageData()
        
        
        if interpolation_resolution:
            extents = []
            dgindexextents = dosegrid_extents_indices(extents, dd)
            dgextents = dosegrid_extents_positions(dgindexextents, dd)
            dd['lut'] = get_resampled_lut(
                dgindexextents,
                dgextents,
                new_pixel_spacing=interpolation_resolution,
                min_pixel_spacing=id['pixelspacing'][0])
            dd['rows'] = dd['lut'][1].shape[0]
            dd['columns'] = dd['lut'][0].shape[0]
            
        x, y = np.meshgrid(np.array(dd['lut'][0]), np.array(dd['lut'][1]))
        x, y = x.flatten(), y.flatten()
        dosegridpoints = np.vstack((x, y)).T

    planes = interpolate_between_planes(
                planes, interpolation_segments_between_planes)
            # Thickness derived from total number of segments relative to original
    s['thickness'] = s['thickness'] / (interpolation_segments_between_planes + 1)

    map = []   
    l = 0
    for z, plane in iteritems(planes):
        pbvar.set(l/len(planes))
        contours = [[x[0:2] for x in c['data']] for c in plane]
        grid = np.zeros((dd['rows'], dd['columns']), dtype=np.uint8)
        for i, contour in enumerate(contours):
            m = get_contour_mask(dd, dosegridpoints, contour)
            grid = np.logical_xor(m.astype(np.uint8), grid).astype(bool)
        map += [[float(z),np.invert(grid)]]
        l += 1
    sorted_map = sorted(map, key=lambda x: x[0])
    z = [x[0] for x in sorted_map]

    ax, _ = pymedphys.dicom.zyx_and_dose_from_dataset(rtdose.ds)
    dose_grid_scaling = rtdose.ds.DoseGridScaling

    cropped_dose = []
    for i in ax[0]:
        if i not in z:
            cropped_dose += [np.zeros((dd['rows'], dd['columns']))]
        else:
            cropped_dose += [np.ma.masked_array(rtdose.GetDoseGrid(i), mask=sorted_map[z.index(i)][1]).filled(0) * dose_grid_scaling]

    return ax, cropped_dose
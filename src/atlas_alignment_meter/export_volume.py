import json
import nrrd
import numpy as np


def createVolumeMetricsPerRegion(
    metrics_per_region,
    reference_volume_data,
    reference_volume_meta,
    output_filepath,
    metric_name="mean",
):
    """
    Use precomputed metrics to export a NRRD file (volume) with a ratio-per-regions approach.

      Parameters:
        metrics_per_region (dict): the "perRegion" property of the precomputed metrics
        reference_volume_data (np.ndarray): Numpy array of the original parcellation volume (used from creating an empty clone of the same size)
        reference_volume_meta (dict): Metadata capturing the origin parcellation NRRD header. Used to conserve spatial transform
        output_filepath (string): filepath where to save the metrics volume
        metric_name (string): name of the metric to export in the volume. Can be "mean", "std" or "median" (default: "mean")
    """
    metric_volume = np.zeros_like(reference_volume_data, dtype=np.float32)

    for region_id in metrics_per_region:
        metric_volume[reference_volume_data == int(region_id)] = float(
            metrics_per_region[region_id][metric_name]
        )

    nrrd.write(output_filepath, metric_volume, reference_volume_meta)


def createVolumeMetricsPerSlice(
    metrics_per_slice,
    reference_volume_data,
    reference_volume_meta,
    output_filepath,
    per_slice_axis=0,
    metric_name="mean",
):
    """
    Use precomputed metrics to export a NRRD file (volume) with a ratio-per-slice approach.

      Parameters:
        metrics_per_slice (dict): the "perSlice" property of the precomputed metrics
        reference_volume_data (np.ndarray): Numpy array of the original parcellation volume (used from creating an empty clone of the same size)
        reference_volume_meta (dict): Metadata capturing the origin parcellation NRRD header. Used to conserve spatial transform
        output_filepath (string): filepath where to save the metrics volume
        metric_name (string): name of the metric to export in the volume. Can be "mean", "std" or "median", "min" and "max" (default: "mean")
    """

    metric_volume = np.zeros_like(reference_volume_data, dtype=np.float32)

    for slice_index in range(0, len(metrics_per_slice[metric_name])):
        metric_value = float(metrics_per_slice[metric_name][slice_index] or 0)

        # would have liked to user .take instead but dont want to do a deepcopy, to slicing "dynamically" here
        slice_ref = None
        slice_out = None

        if per_slice_axis == 0:
            slice_ref = reference_volume_data[slice_index, :, :]
            slice_out = metric_volume[slice_index, :, :]
        elif per_slice_axis == 1:
            slice_ref = reference_volume_data[:, slice_index, :]
            slice_out = metric_volume[:, slice_index, :]
        elif per_slice_axis == 2:
            slice_ref = reference_volume_data[:, :, slice_index]
            slice_out = metric_volume[:, :, slice_index]

        if slice_ref is None:
            raise Exception("The parameter per_slice_axis must be 0, 1 or 2")

        slice_out[slice_ref != 0] = metric_value

    nrrd.write(output_filepath, metric_volume, reference_volume_meta)

import json
import nrrd
import numpy as np

def createVolumeMetricsPerRegion(metrics_per_region, reference_volume_data, reference_volume_meta, output_filepath, metric_name = "mean"):
  metric_volume = np.zeros_like(reference_volume_data, dtype=np.float32)

  count = 0
  for region_id in metrics_per_region:
    print(region_id)
    metric_volume[reference_volume_data == int(region_id)] = float(metrics_per_region[region_id][metric_name])

  nrrd.write(output_filepath, metric_volume, reference_volume_meta)


def createVolumeMetricsPerSlice(metrics_per_slice, reference_volume_data, reference_volume_meta, output_filepath, per_slice_axis = 0, metric_name = "mean"):
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



# metadata_filepath = "test_data/annotation_25_ccfv2.json"
# metadata = json.loads(open(metadata_filepath, "r").read())
# volume_data, volume_header = nrrd.read("test_data/annotation_25_ccfv2.nrrd")

# createVolumeMetricsPerRegion(metrics_per_region = metadata["perRegion"], reference_volume_data = volume_data, reference_volume_meta = volume_header, output_filepath = "test_data/mean_region_25_ccfv2.nrrd", metric_name = "mean")

# createVolumeMetricsPerSlice(metadata["perSlice"], volume_data, volume_header, "test_data/median_slice_25_ccfv2_bis.nrrd", metric_name = "median")
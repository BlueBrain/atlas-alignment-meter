from jaggy_meter import core
from jaggy_meter import export_volume
import nrrd
import os

def test_exporter():
  # load your volume and all:
  volume_data, volume_header = nrrd.read("./test_data/annotation_25_ccfv3.nrrd")
  number_of_slice = volume_data.shape[0]

  # a subset of regions located in the cortical plate
  regions = [68, 656, 320, 1030, 670, 113, 943, 962, 667]
  metrics = core.compute(volume_data, regions = regions)

  region_volume_filepath = "/tmp/region_volume.nrrd"
  slice_volume_filepath = "/tmp/slice_volume.nrrd"

  # Those files may exist from a previous run
  try:
    os.remove(region_volume_filepath)
    os.remove(slice_volume_filepath)
  except Exception as e:
    pass

  # Exporting validation volume with score per region...
  export_volume.createVolumeMetricsPerRegion(metrics_per_region = metrics["perRegion"], reference_volume_data = volume_data, reference_volume_meta = volume_header, output_filepath = region_volume_filepath, metric_name = "mean")

  # Exporting validation volume with score per slice...
  export_volume.createVolumeMetricsPerSlice(metrics_per_slice = metrics["perSlice"], reference_volume_data = volume_data, reference_volume_meta = volume_header, output_filepath = slice_volume_filepath, metric_name = "mean")

  # test that the files were created
  assert os.path.exists(region_volume_filepath)
  assert os.path.exists(slice_volume_filepath)

  # check that they are valid nrrd files
  valid_region_file = False
  try:
    data_region, header_region = nrrd.read(region_volume_filepath)
    valid_region_file = True
  except:
    pass

  assert valid_region_file

  valid_slice_file = False
  try:
    data_slice, header_slice = nrrd.read(slice_volume_filepath)
    valid_slice_file = True
  except:
    pass

  assert valid_slice_file

# to reun the test manually
if __name__ == "__main__":
  test_exporter()
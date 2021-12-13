from atlas_alignment_meter import core
from atlas_alignment_meter import __version__
import nrrd
import numpy as np

def test_report_integrity_largest_regions():
  
  assert len(__version__)

  # load your volume and all:
  volume_data, volume_header = nrrd.read("./test_data/annotation_25_ccfv3.nrrd")
  number_of_slice = volume_data.shape[0]


  nb_to_keep = 10
  regions_ids, regions_counts = np.unique(volume_data, return_counts=True)
  r = dict(zip(regions_counts.tolist(), regions_ids.tolist() ))
  precomputed_all_region_ids = regions_ids
  
  regions = []
  for nb_voxels in sorted(r, reverse = True):
      region_id = r[nb_voxels]

      # the no_data case
      if region_id == 0:
          continue

      regions.append(region_id)
      if len(regions) == nb_to_keep:
          break

  # a subset of regions located in the cortical plate
  metrics = core.compute(volume_data, regions = regions, precomputed_all_region_ids = precomputed_all_region_ids)

  # The report must contain those three categories
  assert "perRegion" in metrics
  assert "perSlice" in metrics
  assert "global" in metrics

  # Check that the metrics report includes all the regions listed above
  for region in regions:
    # region must be in the "perRegion" section of the report
    assert region in metrics["perRegion"]

    # Presence of sub props
    assert "mean" in metrics["perRegion"][region]
    assert "std" in metrics["perRegion"][region]
    assert "median" in metrics["perRegion"][region]

    # Checking value integrity
    assert metrics["perRegion"][region]["mean"] >= 0 and metrics["perRegion"][region]["mean"] <= 1
    assert metrics["perRegion"][region]["std"] >= 0 and metrics["perRegion"][region]["std"] <= 1
    assert metrics["perRegion"][region]["median"] >= 0 and metrics["perRegion"][region]["median"] <= 1

  # Check that the "perRegion" section does not contain more than the regions listed above
  assert len(metrics["perRegion"]) == len(regions)

  # Check that the "perSlice" contain as many elements as slices in the volume
  assert "mean" in metrics["perSlice"]
  assert "std" in metrics["perSlice"]
  assert "median" in metrics["perSlice"]
  assert "min" in metrics["perSlice"]
  assert "max" in metrics["perSlice"]
  
  # In each case, the first, last and before last must have null/None values
  assert metrics["perSlice"]["mean"][0] == None
  assert metrics["perSlice"]["mean"][-1] == None
  assert metrics["perSlice"]["mean"][-2] == None
  assert metrics["perSlice"]["std"][0] == None
  assert metrics["perSlice"]["std"][-1] == None
  assert metrics["perSlice"]["std"][-2] == None
  assert metrics["perSlice"]["median"][0] == None
  assert metrics["perSlice"]["median"][-1] == None
  assert metrics["perSlice"]["median"][-2] == None
  assert metrics["perSlice"]["min"][0] == None
  assert metrics["perSlice"]["min"][-1] == None
  assert metrics["perSlice"]["min"][-2] == None
  assert metrics["perSlice"]["max"][0] == None
  assert metrics["perSlice"]["max"][-1] == None
  assert metrics["perSlice"]["max"][-2] == None

  # For all the other slices, values can be None (no target region) or in [0, 1]
  for i in range(1, number_of_slice - 2):
    assert  metrics["perSlice"]["mean"][i] is None or (metrics["perSlice"]["mean"][i] >= 0 and  metrics["perSlice"]["mean"][i] <= 1)
    assert  metrics["perSlice"]["std"][i] is None or (metrics["perSlice"]["std"][i] >= 0 and  metrics["perSlice"]["std"][i] <= 1)
    assert  metrics["perSlice"]["median"][i] is None or (metrics["perSlice"]["median"][i] >= 0 and  metrics["perSlice"]["median"][i] <= 1)
    assert  metrics["perSlice"]["min"][i] is None or (metrics["perSlice"]["min"][i] >= 0 and  metrics["perSlice"]["min"][i] <= 1)
    assert  metrics["perSlice"]["max"][i] is None or (metrics["perSlice"]["max"][i] >= 0 and  metrics["perSlice"]["max"][i] <= 1)

  # Checking presence of whole-volume metrics
  assert "global" in metrics
  assert "min" in metrics["global"]
  assert "max" in metrics["global"]
  assert "median" in metrics["global"]
  assert "mean" in metrics["global"]
  assert "max" in metrics["global"]
  assert "std" in metrics["global"]

  # checking values are in [0, 1]
  assert metrics["global"]["min"] == None or (metrics["global"]["min"] >= 0 and metrics["global"]["min"] <= 1)
  assert metrics["global"]["max"] == None or (metrics["global"]["max"] >= 0 and metrics["global"]["max"] <= 1)
  assert metrics["global"]["median"] == None or (metrics["global"]["median"] >= 0 and metrics["global"]["median"] <= 1)
  assert metrics["global"]["mean"] == None or (metrics["global"]["mean"] >= 0 and metrics["global"]["mean"] <= 1)
  assert metrics["global"]["std"] == None or (metrics["global"]["std"] >= 0 and metrics["global"]["std"] <= 1)


# to reun the test manually
if __name__ == "__main__":
  test_report_integrity_largest_regions()
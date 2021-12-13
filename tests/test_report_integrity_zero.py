from atlas_alignment_meter import core
from atlas_alignment_meter import __version__
import nrrd

def test_report_integrity_zero():
  
  assert len(__version__)

  # load your volume and all:
  volume_data, volume_header = nrrd.read("./test_data/annotation_25_ccfv3.nrrd")

  # a subset of regions located in the cortical plate
  regions = [0]
  metrics = core.compute(volume_data, regions = regions)
  assert metrics == None


# to reun the test manually
if __name__ == "__main__":
  test_report_integrity_zero()
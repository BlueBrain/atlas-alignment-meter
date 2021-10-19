import argparse
import sys
from jaggy_meter import __version__
import nrrd
import json
from jaggy_meter import core


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version="jaggy-meter {ver}".format(ver=__version__),
    )

    parser.add_argument(
        "--input-parcellation-volume",
        "-i",
        dest="parcellation_volume",
        required=True,
        metavar="<FILE PATH>",
        help="The NRRD parcellation volume file (input)")

    parser.add_argument(
        "--output-report",
        "-o",
        dest="out_report",
        required=True,
        metavar="<FILE PATH>",
        help="Path to the JSON report file (output)")

    return parser.parse_args(args)

def main():
  args = parse_args(sys.argv[1:])
  volume_file_path = args.parcellation_volume
  report_filepath = args.out_report
  volume_data, volume_header = nrrd.read(volume_file_path)
  
  metrics = core.compute2(volume_data)
  # metrics = core.compute(volume_data)

  metrics_file = open(report_filepath, 'w')
  metrics_file.write(json.dumps(metrics, ensure_ascii = False, indent = 2))
  metrics_file.close()
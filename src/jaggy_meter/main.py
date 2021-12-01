import argparse
import sys
from jaggy_meter import __version__
import nrrd
import json
from jaggy_meter import core
from jaggy_meter import export_volume
import numpy as np
import os


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

    parser.add_argument(
        "--output-per-region-volume",
        "-vr",
        dest="out_region_volume",
        required=False,
        default=None,
        metavar="<FILE PATH>",
        help="Path to the NRRD file that contains the ratios per region (output)")


    parser.add_argument(
        "--output-per-slice-volume",
        "-vs",
        dest="out_slice_volume",
        required=False,
        default=None,
        metavar="<FILE PATH>",
        help="Path to the NRRD file that contains the ratios per slice (output)")

    parser.add_argument(
        "--volume-metric",
        "-vm",
        dest="out_metric",
        required=False,
        default="MEDIAN",
        choices=["MEAN", "MEDIAN", "STD", "MIN", "MAX"],
        help="Metric to export in the volume. Only works with --output-per-region-volume and --output-per-slice-volume (default: MEDIAN)")

    parser.add_argument(
        "--regions",
        "-r",
        dest="regions",
        default=None,
        required=False,
        help="ids of regions to measure on, coma-separated with no whitespace (ex. -r 1,2,3,4 ). The values '-r LARGEST,N' or '-r SMALLEST,N' can also be used (with 'N' being an integer)")

    parser.add_argument(
      "--threads",
      "-t",
      required=False,
      dest="threads",
      default='AUTO',
      help="Number of threads to run on. Number or 'AUTO' (default: AUTO)"
    )

    return parser.parse_args(args)

def main():
    args = parse_args(sys.argv[1:])
    volume_file_path = args.parcellation_volume
    report_filepath = args.out_report
    volume_data, volume_header = nrrd.read(volume_file_path)


    regions = None
    precomputed_all_region_ids = None


    if args.regions:
        if args.regions.upper().strip().startswith("LARGEST"):
            nb_to_keep = int(args.regions.split(",")[-1])
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

        elif args.regions.upper().strip().startswith("SMALLEST"):
            nb_to_keep = int(args.regions.split(",")[-1])
            regions_ids, regions_counts = np.unique(volume_data, return_counts=True)
            r = dict(zip(regions_counts.tolist(), regions_ids.tolist() ))
            precomputed_all_region_ids = regions_ids
            
            regions = []
            for nb_voxels in sorted(r):
                region_id = r[nb_voxels]

                # the no_data case
                if region_id == 0:
                    continue

                regions.append(region_id)
                if len(regions) == nb_to_keep:
                    break
        else:
            regions = list( map(lambda id: int(id), args.regions.split(",")  ) )
        


    

    nb_thread = os.cpu_count() - 1
    if args.threads.strip().upper() != 'AUTO':
        try:
            nb_thread = int(args.threads)
        except:
            pass
    
    metrics = core.compute(volume_data, regions = regions, precomputed_all_region_ids = precomputed_all_region_ids, nb_thread = nb_thread)

    metrics_file = open(report_filepath, 'w')
    metrics_file.write(json.dumps(metrics, ensure_ascii = False, indent = 2))
    metrics_file.close()

    #Are there any volume to export?
    if args.out_region_volume:
        print("Exporting validation volume with score per region...")
        export_volume.createVolumeMetricsPerRegion(metrics_per_region = metrics["perRegion"], reference_volume_data = volume_data, reference_volume_meta = volume_header, output_filepath = args.out_region_volume, metric_name = args.out_metric.lower())

    if args.out_slice_volume:
        print("Exporting validation volume with score per slice...")
        export_volume.createVolumeMetricsPerSlice(metrics_per_slice = metrics["perSlice"], reference_volume_data = volume_data, reference_volume_meta = volume_header, output_filepath = args.out_slice_volume, metric_name = args.out_metric.lower())
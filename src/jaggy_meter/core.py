import numpy as np
from numpy.core.numeric import NaN, zeros_like
import nrrd
import json




def compute(volume, coronal_axis_index = 0, short_report = True):
    print('computing...')
    regions_ids = np.unique(volume)
    shape = volume.shape

    # key: region id, value: list of diff_ratio (one per slice)
    report = {
        "perRegion": {},
        "perSlice": {},
    }

    # For each region is, we create a volumetric mask
    for id in regions_ids:
        # we don't process the no_data part
        if id == 0:
            continue

        report[int(id)] = []

        # creating the volumetric mask for this region
        region_mask = np.zeros_like(volume)
        region_mask[volume == id] = 1
        nb_slices = shape[coronal_axis_index]

        # nrrd.write('mask2011_1.nrrd', region_mask)

        report["perRegion"][id] = {
            "diffRatios": [],
            "mean": None,
            "std": None,
            "median": None,
        }

        # for each slice
        for slice_index in range(0, nb_slices - 1):
            current_slice = region_mask[slice_index, :, :]
            next_slice = region_mask[slice_index + 1, :, :]

            # The algorithm consists in checking
            current_non_zero = np.count_nonzero(current_slice)
            next_non_zero = np.count_nonzero(next_slice)

            # no_data on both slice, meaning the current roi is not present here.
            # If only one or the other is no_data, this means it's the begining of a region
            # which we don't want to count or consider jaggy
            if current_non_zero == 0 or next_non_zero == 0:
                continue

            

            # getting the voxel that changes from the current slice to the next
            diff_slice = np.abs(current_slice - next_slice)
            diff_non_zero = np.count_nonzero(diff_slice)

            # print(f"[region: {id} –– slice: {slice_index}] current_non_zero: {current_non_zero}  ––  next_non_zero: {next_non_zero}  ––  diff_non_zero: {diff_non_zero}")
            # continue

            diff_ratio = float(diff_non_zero / (current_non_zero + next_non_zero))

            if slice_index not in report["perSlice"]:
                report["perSlice"][int(slice_index)] = {
                    "diffRatios": [],
                    "mean": None,
                    "std": None,
                    "median": None,
                }

            report["perSlice"][slice_index]["diffRatios"].append(diff_ratio)
            report["perRegion"][id]["diffRatios"].append(diff_ratio)
        
        # computing some metrics on a per region basis
        report["perRegion"][id]["mean"] = np.mean(report["perRegion"][id]["diffRatios"])
        report["perRegion"][id]["median"] = np.median(report["perRegion"][id]["diffRatios"])
        report["perRegion"][id]["std"] = np.std(report["perRegion"][id]["diffRatios"])

        if short_report:
            del report["perRegion"][id]["diffRatios"]

    # computing some metrics on a per slice basis
    for slice_index in report["perSlice"]:
        report["perSlice"][slice_index]["mean"] = np.mean(report["perSlice"][slice_index]["diffRatios"])
        report["perSlice"][slice_index]["median"] = np.median(report["perSlice"][slice_index]["diffRatios"])
        report["perSlice"][slice_index]["std"] = np.std(report["perSlice"][slice_index]["diffRatios"])

        if short_report:
            del report["perRegion"][slice_index]["diffRatios"]
    return report





def compute2(volume, coronal_axis_index = 0, short_report = True):
    print('computing...')
    regions_ids = np.unique(volume)
    shape = volume.shape
    nb_slices = shape[coronal_axis_index]
    nb_regions = len(regions_ids)

    # key: region id, value: list of diff_ratio (one per slice)
    report = {
        "perRegion": {},
        "perSlice": {},
        "global": {},
    }



    # compute the axis tuple that is being used for a per-slice operation
    # such as in the use of np.count_nonzero
    per_slice_axis = {0, 1, 2}
    per_slice_axis.remove(coronal_axis_index)
    per_slice_axis = tuple(per_slice_axis)

    # each element is related to specific brain region.
    # each element is an array with as many element as slices in the volume
    list_of_ratios_per_region = []

    ratios_per_region_per_slice = np.zeros(nb_slices * nb_regions)

    counter = 0
    # For each region is, we create a volumetric mask
    for id in regions_ids:
        # we don't process the no_data part
        if id == 0:
            continue

        print("region id: ", id , f" ({counter + 1}/{nb_regions})")

        # creating the volumetric mask for this region
        region_mask = np.zeros_like(volume)
        region_mask[volume == id] = 1

        # nrrd.write('region_mask.nrrd', region_mask)

        # creating a rolled mask so that each slice in the rolled_region_mask is the same
        # the slice i+1 in the region_mask
        rolled_region_mask = np.roll(region_mask, -1, axis = coronal_axis_index)
        # nrrd.write('rolled_region_mask.nrrd', rolled_region_mask)

        # by substracting region_mask from rolled_region_mask and get the absolute val
        # of the difference, we obtain a mask of where there are differences
        diff_volume = np.abs(rolled_region_mask - region_mask)

        # compute the per slice number of diff
        diff_per_slice_non_zero = np.count_nonzero(diff_volume, axis = per_slice_axis)

        region_mask_per_slice_non_zero = np.count_nonzero(region_mask, axis = per_slice_axis) 
        rolled_region_mask_per_slice_non_zero = np.count_nonzero(rolled_region_mask, axis = per_slice_axis)

        sum_non_zero = (region_mask_per_slice_non_zero + rolled_region_mask_per_slice_non_zero)

        diff_ratios_per_slice = np.divide(diff_per_slice_non_zero, sum_non_zero, out=np.zeros_like(diff_per_slice_non_zero, dtype=float), where=sum_non_zero!=0)
        
        # we want to remove the ratios that are 1 because it means it's the begining or the end of a region,
        # hence not a transition from one true slice of a region to another.
        diff_ratios_per_slice[diff_ratios_per_slice == 1] = 0

        # Same logic for the first and last slices
        diff_ratios_per_slice[0] = 0
        diff_ratios_per_slice[-1] = 0

        non_zero_only = diff_ratios_per_slice[diff_ratios_per_slice > 0]

        list_of_ratios_per_region.append(diff_ratios_per_slice)

        # np.insert(ratios_per_region_per_slice, counter * nb_slices, diff_ratios_per_slice)

        # print(non_zero_only)

        # f = open("diff_ratios_per_slice.json", "w")
        # f.write(json.dumps(diff_ratios_per_slice.tolist(), ensure_ascii = False, indent = 2))
        # f.close()

        # f = open("diff_per_slice_non_zero.json", "w")
        # f.write(json.dumps(diff_per_slice_non_zero.tolist(), ensure_ascii = False, indent = 2))
        # f.close()

        # f = open("region_mask_per_slice_non_zero.json", "w")
        # f.write(json.dumps(region_mask_per_slice_non_zero.tolist(), ensure_ascii = False, indent = 2))
        # f.close()

        # f = open("rolled_region_mask_per_slice_non_zero.json", "w")
        # f.write(json.dumps(rolled_region_mask_per_slice_non_zero.tolist(), ensure_ascii = False, indent = 2))
        # f.close()

        # nrrd.write('diff_volume.nrrd', diff_volume)

        report["perRegion"][int(id)] = {
            # "diffRatios": diff_ratios_per_slice.tolist(),
            "mean": float(np.mean(non_zero_only)),
            "std": float(np.std(non_zero_only)),
            "median": float(np.median(non_zero_only)),
        }

        # f = open("report.json", "w")
        # f.write(json.dumps(report["perRegion"][id], ensure_ascii = False, indent = 2))
        # f.close()
        # return None

        counter += 1

    # list_of_ratios_per_region
    ratios_per_region_per_slice = np.concatenate(list_of_ratios_per_region)
    ratios_per_region_per_slice.shape = (nb_slices, int(ratios_per_region_per_slice.shape[0] / nb_slices))
    # print(ratios_per_region_per_slice.shape)

    report["perSlice"]["mean"] = np.mean(ratios_per_region_per_slice, axis=1).tolist()
    report["perSlice"]["median"] = np.median(ratios_per_region_per_slice, axis=1).tolist()
    report["perSlice"]["std"] = np.std(ratios_per_region_per_slice, axis=1).tolist()
    report["perSlice"]["max"] = np.max(ratios_per_region_per_slice, axis=1).tolist()
    report["perSlice"]["min"] = np.min(ratios_per_region_per_slice, axis=1).tolist()

    report["global"]["mean"] = float(np.mean(ratios_per_region_per_slice))
    report["global"]["median"] = float(np.median(ratios_per_region_per_slice))
    report["global"]["std"] = float(np.std(ratios_per_region_per_slice))
    report["global"]["min"] = float(np.min(ratios_per_region_per_slice))
    report["global"]["max"] = float(np.max(ratios_per_region_per_slice))

    return report
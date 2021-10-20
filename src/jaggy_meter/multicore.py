import numpy as np
import threading
import os


def threadedProcess(volume, id, list_of_ratios_per_region, report, coronal_axis_index, per_slice_axis):
    # we don't process the no_data part
    if id == 0:
        return

    # print("region id: ", id , f" ({counter + 1}/{nb_regions})")
    print("region id: ", id)

    # creating the volumetric mask for this region
    region_mask = np.zeros_like(volume)
    region_mask[volume == id] = 1

    # nrrd.write(f'region_mask_{id}.nrrd', region_mask)

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

    report["perRegion"][int(id)] = {
        # "diffRatios": diff_ratios_per_slice.tolist(),
        "mean": float(np.mean(non_zero_only)),
        "std": float(np.std(non_zero_only)),
        "median": float(np.median(non_zero_only)),
    }




def compute(volume, coronal_axis_index = 0, regions = None, precomputed_all_region_ids = None, nb_thread = os.cpu_count() - 1):
    print(f"computing on {nb_thread} threads...")
    shape = volume.shape
    nb_slices = shape[coronal_axis_index]

    if precomputed_all_region_ids is not None:
        all_region_ids = precomputed_all_region_ids
    else:
        all_region_ids = np.unique(volume)
      
    if regions:
        regions_ids = [ e for e in regions if e in all_region_ids ]

        if len(regions) != len(regions_ids):
          print("Among the provided regions, only the folowwing are present in the volume: ", regions_ids)

    else:
        regions_ids = all_region_ids.tolist()

    nb_regions = len(regions_ids)

    if nb_regions == 0:
      raise Exception("None of the provided regions are in the volume.")


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

    thread_list = []

    # def run_next_thread():
    #     if len(thread_list) == 0:
    #         return

    #     thread = thread_list.pop()
    #     thread.start()
    #     thread.join()

    # counter = 0
    # For each region is, we create a volumetric mask
    for id in regions_ids:
        thread = threading.Thread(target=threadedProcess, args=(volume, id, list_of_ratios_per_region, report, coronal_axis_index, per_slice_axis),)
        thread_list.append(thread)
        # thread.start()

    # for thread in thread_list:
    #     thread.join()

    def run_some_thread():
        if len(thread_list) == 0:
            return

        sub_list = []
        for j in range(0, nb_thread):
            try:
                t = thread_list.pop()
                sub_list.append(t)
                t.start()
            except:
                pass

        for t in sub_list:
            t.join()
        
        run_some_thread()

    run_some_thread()
        
        



    # list_of_ratios_per_region
    ratios_per_region_per_slice = np.concatenate(list_of_ratios_per_region)
    # np.savetxt("ratios_per_region_per_slice_BEFORE_RESHAPE.csv", ratios_per_region_per_slice)
    ratios_per_region_per_slice.shape = (int(ratios_per_region_per_slice.shape[0] / nb_slices), nb_slices)
    ratios_per_region_per_slice = ratios_per_region_per_slice.T
    print(ratios_per_region_per_slice.shape)

    # for debugging purpose, we may not run the thing on all the regions, hence we need to know
    # on how many region the thing was ran
    actual_nb_regions = ratios_per_region_per_slice.shape[1]
    
    per_slice = np.split(ratios_per_region_per_slice, ratios_per_region_per_slice.shape[0], axis=0)

    report["perSlice"]["mean"] = []
    report["perSlice"]["median"] = []
    report["perSlice"]["std"] = []
    report["perSlice"]["min"] = []
    report["perSlice"]["max"] = []

    # for the per-slice approach, we need to filter out all the zeros because we want to consider
    # only the jaggies of where the regions are and keeping the zeros (aka. where each region is not)
    # is lowering down very much the average, which create an important bias into detecting the jaggies
    for slice_data in per_slice:
      slice_data_sub = slice_data[0].copy()
      non_zero_only = slice_data_sub[slice_data_sub > 0]

      if len(non_zero_only) == 0:
        report["perSlice"]["mean"].append( None )
        report["perSlice"]["median"].append( None )
        report["perSlice"]["std"].append( None )
        report["perSlice"]["min"].append( None )
        report["perSlice"]["max"].append( None )
      else:
        report["perSlice"]["mean"].append( float(np.mean(non_zero_only)) )
        report["perSlice"]["median"].append( float(np.median(non_zero_only)) )
        report["perSlice"]["std"].append( float(np.std(non_zero_only)) )
        report["perSlice"]["min"].append( float(np.min(non_zero_only)) )
        report["perSlice"]["max"].append( float(np.max(non_zero_only)) )

    # for the global approach, no need to 
    flat = ratios_per_region_per_slice.ravel()
    flat_non_zero = flat[flat > 0]
    report["global"]["mean"] = float(np.mean(flat_non_zero))
    report["global"]["median"] = float(np.median(flat_non_zero))
    report["global"]["std"] = float(np.std(flat_non_zero))
    report["global"]["min"] = float(np.min(flat_non_zero))
    report["global"]["max"] = float(np.max(flat_non_zero))

    return report
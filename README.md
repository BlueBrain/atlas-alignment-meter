Pythonic tool (CLI and library) to measure the slice-to-slice jaggyness of a volumetric dataset (NRRD file only).

# Usage
install the last version:
```
pip install git+https://bbpgitlab.epfl.ch/dke/users/jonathanlurie/jaggy-meter.git
```

Will probably move to `https://bbpgitlab.epfl.ch/dke/apps/jaggy-meter.git` when no longer *beta*.

## As a CLI:
```
jaggy-meter -i test_data/annotation_25_ccfv3.nrrd -o test_data/annotation_25_ccfv3.json
```
With `-i` for **input volume**, `-o` for **output json report**.  

To run it only on a selected subset or region IDs, use `-r` or `--regions` and a comma separated list (with no whitespace between them)
```
jaggy-meter -i test_data/annotation_25_ccfv3.nrrd -o test_data/annotation_25_ccfv3.json -r 12,23,34,45
```

To run it on the *N* (ex. 10) largest regions of the volume:
```
jaggy-meter -i test_data/annotation_25_ccfv3.nrrd -o test_data/annotation_25_ccfv3.json -r LARGEST,10
```

To run it on the *N* (ex. 10) smallest regions of the volume:
```
jaggy-meter -i test_data/annotation_25_ccfv3.nrrd -o test_data/annotation_25_ccfv3.json -r SMALLEST,10
```
Note that the `-t` options followed by a number runs the CLI on the given number of threads. If not provided or providing `-t AUTO`, then the CLI run on *(max_number_of_thread - 1)* to not bloat the machine. Keep in mind that running a process on more threads than physically available will perform poorly.

More info with `jaggy-meter --help`.

## As a Python library
To import *jaggy-meter* into another codebase, we need to import its core:

```python
from jaggy_meter import core
import nrrd

# load your volume and all:
volume_data, volume_header = nrrd.read("some_path/to_volume.nrrd")

metrics = core.compute(volume_data)
```

and with some more options:
```python
metrics = compute(
    volume_data, 
    coronal_axis_index = 0, # for future non-along-faster-axis improvement
    regions = [1, 2, 3, 4], 
    precomputed_all_region_ids = None, # mainly intended to be used from CLI not not recompute it, don't pay attention to it 
    nb_thread = 3
  )
```

# What's a jagged volume
Some imagery capture methods rely on slicing a brain mechanically , capturing a picture of each individual slice and later reconstruct the volume from slices digitally stuck together in the correct order. One drawback of this method is the slight displacement of each slice to the next, resulting in volume being imperfectly aligned along the axis orthogonal to the slicing plane.

Here is an illustration of a smooth (not jagged) volume:

AIBS CCFv3 axial             |  AIBS CCFv3 sagittal
:-------------------------:|:-------------------------:
![Smooth AIBS CCF v3 axial plane](images/aibs_ccfv3_axial.png)  |  ![Smooth AIBS CCF v3 sagittal plane](images/aibs_ccfv3_sagittal.png)


As a comparison, here is a jagged volume:

AIBS CCFv2 axial             |  AIBS CCFv2 sagittal
:-------------------------:|:-------------------------:
![Jaggy AIBS CCF v2 axial plane](images/aibs_ccfv2_axial.png)  |  ![Jaggy AIBS CCF v2 sagittal plane](images/aibs_ccfv2_sagittal.png)

# Why measuring the jaggyness?
Providing such metric is important mostly to evaluate the quality of the volume alignment, from `1` (very jagged volume, basically white noise) to `0` (no jaggies at all, basically a unified blob of a single value).  

At Blue Brain, we also have some procedures to obtain a smooth volume from a jaggy one, with the purpose of placing cells or building circuit. Hence, it is key to provide a metric to evaluate the efficiency of the re-alignment process and eventually improve it.

# Method
## General
*In the following, we will assume as a generality that the coronal plane is always the capture plane, and that the purpose is to measure the jaggyness along the anterior-posterior axis.*  

For a given region of interest (ROI) that we convert into a binary mask, we measure its distribution on each slice compared to the next. To achieve that, we use the following method:

<p style="text-align: center;">
<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="19.57ex" height="9.352ex" style="vertical-align: -1.671ex;" viewBox="0 -1293.7 4213 2013.3" role="img" focusable="false" xmlns="http://www.w3.org/2000/svg"><defs><path stroke-width="1" id="E2-MJMAIN-7C" d="M139 -249H137Q125 -249 119 -235V251L120 737Q130 750 139 750Q152 750 159 735V-235Q151 -249 141 -249H139Z"></path><path stroke-width="1" id="E2-MJMATHI-4E" d="M234 637Q231 637 226 637Q201 637 196 638T191 649Q191 676 202 682Q204 683 299 683Q376 683 387 683T401 677Q612 181 616 168L670 381Q723 592 723 606Q723 633 659 637Q635 637 635 648Q635 650 637 660Q641 676 643 679T653 683Q656 683 684 682T767 680Q817 680 843 681T873 682Q888 682 888 672Q888 650 880 642Q878 637 858 637Q787 633 769 597L620 7Q618 0 599 0Q585 0 582 2Q579 5 453 305L326 604L261 344Q196 88 196 79Q201 46 268 46H278Q284 41 284 38T282 19Q278 6 272 0H259Q228 2 151 2Q123 2 100 2T63 2T46 1Q31 1 31 10Q31 14 34 26T39 40Q41 46 62 46Q130 49 150 85Q154 91 221 362L289 634Q287 635 234 637Z"></path><path stroke-width="1" id="E2-MJMATHI-69" d="M184 600Q184 624 203 642T247 661Q265 661 277 649T290 619Q290 596 270 577T226 557Q211 557 198 567T184 600ZM21 287Q21 295 30 318T54 369T98 420T158 442Q197 442 223 419T250 357Q250 340 236 301T196 196T154 83Q149 61 149 51Q149 26 166 26Q175 26 185 29T208 43T235 78T260 137Q263 149 265 151T282 153Q302 153 302 143Q302 135 293 112T268 61T223 11T161 -11Q129 -11 102 10T74 74Q74 91 79 106T122 220Q160 321 166 341T173 380Q173 404 156 404H154Q124 404 99 371T61 287Q60 286 59 284T58 281T56 279T53 278T49 278T41 278H27Q21 284 21 287Z"></path><path stroke-width="1" id="E2-MJMAIN-2212" d="M84 237T84 250T98 270H679Q694 262 694 250T679 230H98Q84 237 84 250Z"></path><path stroke-width="1" id="E2-MJMAIN-2B" d="M56 237T56 250T70 270H369V420L370 570Q380 583 389 583Q402 583 409 568V270H707Q722 262 722 250T707 230H409V-68Q401 -82 391 -82H389H387Q375 -82 369 -68V230H70Q56 237 56 250Z"></path><path stroke-width="1" id="E2-MJMAIN-31" d="M213 578L200 573Q186 568 160 563T102 556H83V602H102Q149 604 189 617T245 641T273 663Q275 666 285 666Q294 666 302 660V361L303 61Q310 54 315 52T339 48T401 46H427V0H416Q395 3 257 3Q121 3 100 0H88V46H114Q136 46 152 46T177 47T193 50T201 52T207 57T213 61V578Z"></path></defs><g stroke="currentColor" fill="currentColor" stroke-width="0" transform="matrix(1 0 0 -1 0 0)"><g transform="translate(120,0)"><rect stroke="none" width="3973" height="60" x="0" y="220"></rect><g transform="translate(60,631)"><use transform="scale(0.707)" xlink:href="#E2-MJMAIN-7C"></use><g transform="translate(446,0)"><use transform="scale(0.707)" xlink:href="#E2-MJMATHI-4E" x="0" y="0"></use><use transform="scale(0.574)" xlink:href="#E2-MJMATHI-69" x="989" y="-238"></use></g><use transform="scale(0.707)" xlink:href="#E2-MJMAIN-2212" x="1816" y="0"></use><g transform="translate(1834,0)"><use transform="scale(0.707)" xlink:href="#E2-MJMATHI-4E" x="0" y="0"></use><g transform="translate(568,-140)"><use transform="scale(0.574)" xlink:href="#E2-MJMATHI-69" x="0" y="0"></use><use transform="scale(0.574)" xlink:href="#E2-MJMAIN-2B" x="345" y="0"></use><use transform="scale(0.574)" xlink:href="#E2-MJMAIN-31" x="1124" y="0"></use></g></g><use transform="scale(0.707)" xlink:href="#E2-MJMAIN-7C" x="5170" y="-1"></use></g><g transform="translate(381,-429)"><use transform="scale(0.707)" xlink:href="#E2-MJMATHI-4E" x="0" y="0"></use><use transform="scale(0.574)" xlink:href="#E2-MJMATHI-69" x="989" y="-238"></use><use transform="scale(0.707)" xlink:href="#E2-MJMAIN-2B" x="1183" y="0"></use><g transform="translate(1637,0)"><use transform="scale(0.707)" xlink:href="#E2-MJMATHI-4E" x="0" y="0"></use><g transform="translate(568,-140)"><use transform="scale(0.574)" xlink:href="#E2-MJMATHI-69" x="0" y="0"></use><use transform="scale(0.574)" xlink:href="#E2-MJMAIN-2B" x="345" y="0"></use><use transform="scale(0.574)" xlink:href="#E2-MJMAIN-31" x="1124" y="0"></use></g></g></g></g></g></svg>
</p>

In plain English, this could be summarised as follow:  
> "What is the ratio of ROI voxels that are diffent from one slice to the next over the total count of ROI voxels in these two slices?"

With:
- *N*: the count of voxels belonging to the ROI 
- *i*: the coronal slice index

The pros of this methods are:
- relatively basic and cost efficient
- the result is bounded in the interval *[0, 1]*
- no division by zero possible (since only computed on ROI)

The cons of this method (and how they are worked around) are:
- The slice just before the begining of a region or the slice just after the end will have `0` voxel of this ROI, hence the ratio is always going to be `1.0`. Furthermore, a ratio of `1.0` can happen only in this particular case. Since we do not want to measure where a ROI is starting or ending but only want to measure the jaggyness happening within a ROI, we can just safely remove all the `1.0` from our set of measures. The reason for removing those values is that a ratio of `1.0` would add a bias to the final measures, making a ROI looking more jagged than it actually is.
- The method is based on a difference from a slice to the next, as a result, it will not be possible to compute this value for the very last slice fo the volume. The solution is to simply not compute the ratio on the last slice and making it *nullish*.

**Note 1:** the *no data* part around the brain is *NOT* considered as a ROI and its score is not computed.  

**Note 2:** The final score, from a pair of slices or averaged on a whole volume, will not tell whether or not a volume has an acceptable jaggyness, as this entirely depends on the conducted experiment and the eye of the scientist. To compensate for this lack of objectivity, the best course of action is to run this method on a reference volume, either an unacceptably jagged one or a very smooth one (or both). This will minimize the interval of confidence and help bearing a judgement on a candidate volume. 

## Part 1: The per-region metrics
It may happen that an annotation volume is aligned with an algorithm that takes into consideration mostly its external envelope and does not process the alignement on internal structure. As a result, the whole brain mask would be fairly smooth but the internal parts would still be very much jagged.  

The proposed method adopts a per-parcellation tactic, creating a ROI (binary mask) for all the unique regions present in an annotation volume. Then, for each ROI mask, a slice-to-slice approach is ran.  
For each ROI are provided the `mean`, `std` and `median` of the difference ratio.

## Part 2: The per-slice metrics
When the computation of **part 1** is done on all available (or desired) regions, a per-slice aggregation of ratios is done to provide metrics such as `mean`, `std`, `median`, `min` and `max` of difference ratio on each slice.  
**Important notice:** some slices may not be populated by any ROI, or be populated by less ROI than other slices. In order to avoid a *no data bias* that would artificially lower the score (and make slices less jagged than they actually are), the per-slice approach is only taking into account the ROIs that are actually present on this particular slice index, discarding the `null` of the other ROIs that not present. (in other word, the absents are not part of the computed statistics).

## Part 3: The global metrics
Comparably to the the *per-slice* approach, the metrics related to the global score (`mean`, `std`, `median`, `min` and `max`) are computed after discarding all the *no data* of outside the brain and the *no data* around each ROI.  
As a general comment, the global metrics are best suited for a not-too-in-depth sneek peak into the jaggyness metrics.

# Output
A Pyton dictionnary is outputed and can be saved as JSON. Samples of these JSON files can be found in the folder `test_data/*.json`, where they are related to the volumes of the same name `*.nrrd`.

Here are some interesting global values from AIBS CCF v2 (jagged):
```json
{
  "mean": 0.24857328984712668,
  "median": 0.19326241134751773,
  "std": 0.18146920902864508,
  "min": 0.0037735849056603774,
  "max": 0.9971671388101983
}
```

From AIBS CCF v3 (smooth):
```json
{
  "mean": 0.13067491908784817,
  "median": 0.0743801652892562,
  "std": 0.15140213631276536,
  "min": 0.0009910802775024777,
  "max": 0.9948453608247423
}
```

From the ML aligned candidate (rather smooth outer hull but quite jagged internals):
```json
{
  "mean": 0.28250164209832207,
  "median": 0.2171945701357466,
  "std": 0.200293614299299,
  "min": 0.011627906976744186,
  "max": 0.9988348383338188
}
```

While the `min` and `max` metrics are difficult to make sense of (or maybe even irrelevant), the `median` shows that CCF v3 is `2.6x` less jagged than CCF v2 (and almost `2x` according to the `mean`).  
Following this logic, we can say that the ML-aligned candidate is even jaggier than the original CCF v2, which is the opposite its original intention.


# Current limitations
## File format
Only NRRD files are compatible for the moment. Though if other formats are necessary (ex. NIfTI) we could add those in the future.

## Type of dataset
As of now, this tool only works for annotation volumes encoding parcellations. This would not work on a NISSL/Golgi stained dataset.

## File encoding and orientation
As of now, the comparison from one slice to the next only applies for slices being orthogonal to the fastest varying axis.  
For example, following the [NRRD format spec](http://teem.sourceforge.net/nrrd/format.html#sizes), the NRRD header entry `sizes: 528 320 456` implies that:
- the fastest varying axis has a size of 528 elements (voxels)
- the intermediate axis has a size of 320 elements
- the slowest varying axis has a size of 456 elements

Then, looking at datasets such as AIBS Mouse CCF v3 volume in 25um (no rotation), we know that those axis, in respective order, corresponds to:
- the anterior (0) to posterior (527) X axis
- the superior (0) to inferior (319) Y axis
- the left (0) to right (455) Z axis

As a result, the image plane orthogonal to the X axis is represented by 2D images that are on Y-by-Z, where lay the coronal slices. If in the future there is a need for the reference slice orientation to be different than along the fastest varying axis, then an update will be done to this module.  

(For example, the rat atlas volume has its coronal slices on the X-by-Z place and its aterior-to-posterior axis on Y)
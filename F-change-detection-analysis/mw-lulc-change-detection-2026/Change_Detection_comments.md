# LULC Change Detection

This notebook is used to analyse Land Use and Land Cover (LULC) changes between 2024 and 2025. The workflow focuses on extracting a selected LULC class, comparing the two years, identifying areas of gain and loss, and calculating the area of change.

## Import Libraries

The required Python libraries are imported for raster data processing, numerical calculations, visualisation, and geospatial analysis.

## Input and Output Data

The input datasets represent the LULC data for 2024 and 2025. Output filenames are also defined so that the processed raster layers can be saved for further analysis.

## Target LULC Class

A target LULC class is selected for the analysis. In this workflow, **Class 2** is used as the target class.

> **Review comment:** The target class should be clearly explained so that the user knows what type of land cover Class 2 represents.

## Loading the LULC Data

The LULC raster datasets for 2024 and 2025 are loaded and their dimensions are checked. This helps ensure that the datasets can be compared.

> **Review comment:** It would be useful to also check that both datasets have the same CRS, resolution, extent, and spatial alignment.

## Visualising the LULC Data

The 2024 and 2025 LULC datasets are displayed side by side. This provides a visual comparison of the land-cover distribution between the two years.

> **Positive comment:** The side-by-side visualisation makes it easier to identify possible changes between the two datasets.

> **Improvement:** A consistent colour scheme and legend would make the LULC classes easier to interpret.

## Extracting the Target Class

The selected target class is extracted from both LULC datasets. Pixels belonging to Class 2 are assigned a value of **1**, while all other classes are assigned a value of **0**.

This creates binary raster layers that can be used for change detection.

## Exporting the Extracted Layers

The extracted 2024 and 2025 binary layers are saved as GeoTIFF files. These outputs can be used for further analysis in GIS software such as ArcGIS Pro or QGIS.

> **Positive comment:** Exporting the processed layers makes the workflow useful beyond the Jupyter Notebook.

## Visualising the Extracted Class

The extracted target class is displayed for both years to compare its spatial distribution.

> **Improvement:** Adding clear titles, legends, coordinates, and other map elements would improve the presentation of the results.

## LULC Change Detection

Change detection is performed by subtracting the 2024 binary layer from the 2025 binary layer.

The resulting values represent:

* **-1 = Loss**
* **0 = No Change**
* **1 = Gain**

This allows areas of gain and loss to be identified spatially.

## Visualising the Change

The difference raster is displayed to show the spatial distribution of LULC change between 2024 and 2025.

> **Positive comment:** The difference method provides a simple and clear way to identify areas of gain and loss.

> **Improvement:** Using different colours for gain, loss, and no change would make the results easier to interpret.

## Exporting the Change Detection Result

The change detection raster is exported as a GeoTIFF file. This allows the results to be opened and analysed in GIS software.

## Area Calculation

The area of the selected LULC class and the detected changes is calculated using the raster pixel size.

The results are converted into:

* Square metres
* Hectares
* Square kilometres
* Acres

> **Review comment:** The 2024 and 2025 area results should be checked because the output currently shows **0.00**, while gain and loss values are being calculated. The variable names used in the area calculation should be checked for consistency.

## Results and Interpretation

The final results provide an estimate of the amount of LULC area that has been gained or lost between 2024 and 2025.

The spatial results can also be used to identify where the changes occurred within the study area.

## Overall Review

### Positive Review

The notebook follows a clear and logical workflow from data preparation to change detection and area calculation. The use of binary extraction and raster differencing provides a simple approach for identifying LULC changes.

### Areas for Improvement

The notebook could be improved by:

* Providing more explanation of the LULC classes.
* Checking CRS, resolution, extent, and spatial alignment.
* Improving map legends and visualisation.
* Using consistent variable names.
* Checking the area calculation results.
* Validating the change detection results against reference or ground-truth data.
* Adding more interpretation of the final results.

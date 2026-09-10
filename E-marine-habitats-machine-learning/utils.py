
from odc.stac import load  # Correct source for `load`
import xarray as xr
from xarray import DataArray, Dataset
import numpy as np
from odc.algo import mask_cleanup
from skimage.feature import graycomatrix, graycoprops
from skimage import data
from skimage.util import view_as_windows
from shapely import box
from datetime import datetime
from shapely.geometry import Polygon
from pyproj import CRS 
import folium
import geopandas as gpd
import pandas as pd
import rasterio as rio
import rioxarray
from ipyleaflet import basemaps
from numpy.lib.stride_tricks import sliding_window_view
import pystac_client
import planetary_computer
from odc.stac import load
from pystac.client import Client
from skimage.feature import graycomatrix, graycoprops

def load_data(items, bands, bbox):
    """
    Load data into a dataset with specified measurements and configurations.

    Parameters:
    - items: List of STAC items to load.
    - bbox: Bounding box for the region of interest.

    Returns:
    - data: The loaded dataset.
    """
    data = load(
        items,
        bands=[
            "nir",
            "red",
            "blue",
            "green",
            "emad",
            "smad",
            "bcmad",
            # "count",
            "green",
            "nir08",
            "nir09",
            "swir16",
            "swir22",
            "coastal",
            "rededge1",
            "rededge2",
            "rededge3",
        ],
        bbox=bbox,
        chunks={"x": 2048, "y": 2048},
        groupby="solar_day",
    )
    return data

from odc.geo import GeoBox
from odc.stac import load
from pystac_client import Client

catalog = "https://earth-search.aws.element84.com/v1/"
client = Client.open(catalog)

def load_s1_dem(collection, year, bbox): 
    
    items = client.search(
        collections=[collection],
        bbox=bbox,
        datetime=year,
    ).item_collection()

    chunks = dict(x=2048, y=2048)
    geom = GeoBox.from_bbox(bbox, crs="EPSG:4326", resolution=0.0001)

    
    if collection == "sentinel-1-grd":
        measurements = ["vh", "vv"]
        groupby = "solar_day"
    elif collection == "cop-dem-glo-30":
        measurements = None
        groupby = None
        chunks = None
    else:
        measurements = None
        groupby = None

    # Load data
    data = load(
        items,
        chunks=chunks,
        like=geom,
        groupby=groupby,
        measurements=measurements,
    )
    
    data = data.rename({"latitude": "y", "longitude": "x"})

    return data



def calculate_band_indices(data):
    """
    Calculate various band indices and add them to the dataset.

    Parameters:
    data (xarray.Dataset): The input dataset containing the necessary spectral bands.

    Returns:
    xarray.Dataset: The dataset with added band indices.
    """
# --- DEFINITION: Coefficients from your Table's WETNESS row (Nedkov 2017) --- https://www.researchgate.net/profile/R-Nedkov-2/publication/329184434_ORTHOGONAL_TRANSFORMATION_OF_SEGMENTED_IMAGES_FROM_THE_SATELLITE_SENTINEL-2/links/5bfbd74592851ced67d82a2a/ORTHOGONAL-TRANSFORMATION-OF-SEGMENTED-IMAGES-FROM-THE-SATELLITE-SENTINEL-2.pdf
    C_B1 = 0.0649    # Coastal Aerosol
    C_B2 = 0.1363    # Blue
    C_B3 = 0.2802    # Green
    C_B4 = 0.3072    # Red
    C_B5 = 0.5288    # RedEdge 1
    C_B6 = 0.1379    # RedEdge 2
    C_B7 = -0.0001   # RedEdge 3
    C_B8 = -0.0807   # NIR (Wide)
    C_B9 = -0.0302   # Water Vapour
    C_B10 = 0.0003   # SWIR - Cirrus
    C_B11 = -0.4064  # SWIR1 (your 'swir16')
    C_B12 = -0.5602  # SWIR2 (your 'swir22')
    C_B8A = -0.1389  # NIR (Narrow)
    
    data["mndwi"] = (data["green"] - data["swir16"]) / (data["green"] + data["swir16"])
    data["ndti"] = (data["red"] - data["green"]) / (data["red"] + data["green"])
    data["cai"] = (data["coastal"] - data["blue"]) / (data["coastal"] + data["blue"])
    data["ndvi"] = (data["nir"] - data["red"]) / (data["nir"] + data["red"])
    data["evi"] = (2.5 * data["nir"] - data["red"]) / (data["nir"] + (6 * data["red"]) - (7.5 * data["blue"]) + 1)
    data["savi"] = (data["nir"] - data["red"]) / (data["nir"] + data["red"])
    data["ndwi"] = (data["green"] - data["nir"]) / (data["green"] + data["nir"])
    data["b_g"] = data["blue"] / data["green"]
    data["b_r"] = data["blue"] / data["red"]
    data["swir22_swir16"] = data["swir22"] / data["swir16"]
    data["mci"] = data["nir"] / data["rededge1"]
    data["ndci"] = (data["rededge1"] - data["red"]) / (data["rededge1"] + data["red"])
    data["nbi"] = (data["swir16"] - data["nir"]) / (data["swir16"] + data["nir"])
    data["ndmi"] = (data["nir"] - data["swir16"]) / (data["nir"] + data["swir16"])
    data["bsi"] = ((data["swir22"] + data["red"]) - (data["nir"] + data["blue"])) / ((data["swir22"] + data["red"]) + (data["nir"] + data["blue"]))
    data["awei"] = (data["blue"] + (2.5 * data["green"]) - (1.5 * (data["nir"] + data["swir16"]) - (0.25 * data["swir22"])))
    data["tc_wetness"] = ((C_B1 * data["coastal"]) + (C_B2 * data["blue"]) + (C_B3 * data["green"]) + (C_B4 * data["red"]) + (C_B5 * data["rededge1"]) + (C_B6 * data["rededge2"]) + (C_B7 * data["rededge3"]) + (C_B8 * data["nir"]) + (C_B11 * data["swir16"]) + (C_B12 * data["swir22"]) + (C_B8A * data["nir08"]))
    
    return data


def scale(data):
    """
    Scale the input data by applying a factor and clipping the values.

    Parameters:
    data (xr.Dataset): The input dataset containing the bands to be scaled.

    Returns:
    xr.Dataset: The scaled dataset with values clipped between 0 and 1.
    """
    scaled = (data * 0.0001).clip(0, 1)
    return scaled


def apply_mask(
    ds: Dataset,
    mask: DataArray,
    ds_to_mask: Dataset | None = None,
    return_mask: bool = False,
) -> Dataset:
    """Applies a mask to a dataset"""
    to_mask = ds if ds_to_mask is None else ds_to_mask
    masked = to_mask.where(mask)

    if return_mask:
        return masked, mask
    else:
        return masked

def mask_water(
    ds: Dataset, ds_to_mask: Dataset | None = None, return_mask: bool = False
) -> Dataset:
    """Masks out land pixels based on the NDWI and MNDWI indices.

    Args:
        ds (Dataset): Dataset to mask
        ds_to_mask (Dataset | None, optional): Dataset to mask. Defaults to None.
        return_mask (bool, optional): If True, returns the mask as well. Defaults to False.

    Returns:
        Dataset: Masked dataset
    """
    water = (ds.mndwi).squeeze() < 0
    mask = mask_cleanup(water, [["dilation", 5], ["erosion", 6]])

    return apply_mask(ds, mask, ds_to_mask, return_mask)
    

def mask_urban(
    ds: Dataset, ds_to_mask: Dataset | None = None, return_mask: bool = False
) -> Dataset:
    """
    Identifies urban pixels that also have water-like index values 
    (though this is generally an unusual definition for a base urban mask).
    """
    # This ensures (NBI > 0) is calculated, (MNDWI < 0.08) is calculated,
    # and THEN the resulting boolean arrays are combined with '&'.
    urban = ((ds.nbi).squeeze() > 0.5) & ((ds.mndwi).squeeze() < 0.08)
    
    mask = mask_cleanup(urban, [["dilation", 5], ["erosion", 5]])

    return apply_mask(ds, mask, ds_to_mask, return_mask)

def all_masks(
    ds: Dataset,
    return_mask: bool = False,
) -> Dataset:
    """
    Creates a final mask that is inclusive of water (MNDWI) 
    and exclusive of urban areas (NBI).
    """
    # 1. Get the cleaned water mask (True = Water)
    _, water_mask = mask_water(ds, return_mask = True)
    
    # 2. Get the cleaned urban mask (True = Urban)
    _, urban_mask = mask_urban(ds, return_mask = True)
    
    # 3. Combine the masks: Water AND (NOT Urban)
    # The bitwise NOT operator (~) inverts the urban mask (Urban becomes False),
    # and the bitwise AND operator (&) selects only the pixels that are TRUE 
    # in the water mask AND TRUE in the inverted urban mask (i.e., not urban).
    mask = water_mask & ~urban_mask
    
    return apply_mask(ds, mask, None, return_mask)

# def all_masks(
#     ds: Dataset,
#     return_mask: bool = False,
# ) -> Dataset:
#     _, water_mask = mask_water(ds, return_mask = True)
#     _, urban_mask = mask_urban(ds, return_mask = True)
    
#     # 🌟 This is the correct logic: Water AND (NOT Urban)
#     mask = water_mask & ~urban_mask
    
#     return apply_mask(ds, mask, None, return_mask)
    

def do_prediction(ds, model, output_name: str | None = None):
    """Predicts the model on the dataset and adds the prediction as a new variable.

    Args:
        ds (Dataset): Dataset to predict on
        model (RegressorMixin): Model to predict with
        output_name (str | None): Name of the output variable. Defaults to None.

    Returns:
        Dataset: Dataset with the prediction as a new variable
    """
    mask = ds.red.isnull()  # Probably should check more bands

    # Convert to a stacked array of observations
    stacked_arrays = ds.to_array().stack(dims=["y", "x"])

    # Replace any infinities with NaN
    stacked_arrays = stacked_arrays.where(stacked_arrays != float("inf"))
    stacked_arrays = stacked_arrays.where(stacked_arrays != float("-inf"))

    # Replace any NaN values with 0
    # TODO: Make sure that each column is labelled with the correct band name
    stacked_arrays = stacked_arrays.squeeze().fillna(0).transpose()

    # Predict the classes
    predicted = model.predict(stacked_arrays)

    # Reshape back to the original 2D array
    array = predicted.reshape(ds.y.size, ds.x.size)

    # Convert to an xarray again, because it's easier to work with
    predicted_da = xr.DataArray(array, coords={"y": ds.y, "x": ds.x}, dims=["y", "x"])

    # Mask the prediction with the original mask
    # predicted_da = predicted_da.where(~mask).compute()

    # If we have a name, return dataset, else the dataarray
    if output_name is None:
        return predicted_da
    else:
        return predicted_da.to_dataset(name=output_name)

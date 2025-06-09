dri-owrd-et
=========================

# [Oregon Statewide ET Project](https://www.dri.edu/project/owrd-et/)

![Workflow Diagram](Oregon_Statewide_ET_data_processing_pipeline_clipped.jpeg "Field- and HUC-level Data Processing Workflow")

Google Earth Engine (GEE) Python API tools for downloading/exporting OpenET and gridMET timeseries for field boundaries as part
of the OWRD Statewide ET Project. Additional post-processing steps are provided to prepare field- and HUC-level summary tables/shapefiles
containing all timeseries variables and the final geopackages with all layers. GEE export scripts are provided in the 
"ee_zonal_stats.ipynb" Jupyter Notebook and the post-processing scripts are provided in the "post-processing.ipynb" Jupyter Notebook.

## Requirements
1. Python 3.11
2. earthengine-api
3. jupyterlab
4. pandas
5. numpy
6. geopandas
7. gdal

--------

### Python

The ee_zonal_stats and post_processing Python jupyter notebooks have been developed primarily for Python 3.11+.

### Earth Engine
To run the ee_zonal_stats notebook you must have an Earth Engine account.  If you do not have an account, please go to the Earth Engine [signup page](https://signup.earthengine.google.com)

#### Conda

The easiest way of managing Python and all of the necessary external modules is to use conda environments and the conda package manager.  

##### Miniconda / Anaconda

The easiest way of obtaining conda is to install [Python 3.13 Miniconda](https://www.anaconda.com/download/) at the very bottom of the website, which is a minimal version of the full [Anaconda Distribution](https://www.anaconda.com/distribution/) that includes only conda and its dependencies. 

After installing Miniconda or if you already have Python installed, it is important to double check that you are calling the expected version of Python. This is especially important if you have two or more version of Python installed (e.g. Anaconda and ArcGIS).  To check the default Python location on your computer, type the appropriate commands in a command prompt or terminal:
+ Windows: "where python"
+ Linux/Mac: "which python"


##### Updating Conda

If you previously installed conda/Miniconda/Anaconda and haven't updated in awhile, it would be good to update to the latest version: 
```
> conda update -n base -c conda conda
```

#### Creating the Environment

A Conda environment is a separate instance of Python (stored in a sub-directory in the Python "envs" folder) that has a specific set of python modules and packages installed.  The environment can also be an entirely different version of Python (i.e. the environment could be Python 2.7 even though you have Python 3.11 Miniconda). It can be helpful to build a separate conda environment for each project to ensure that updating a python module for one project doesn't break anything else.

After installing conda, the "py311" environment can be built directly from the provided [environment.yml](environment.yml) file using the following command:
```
conda env create -f environment.yml
```

##### Activating the Environment

After building the "py311" conda environment, it must be activated in order to use this version of Python and modules/packages.  The following command will need to be run everytime you open a new command prompt or terminal.
```
> conda activate py311
```

After activating, the environment name should show up before the path in the command prompt or terminal:
```
(py311) C:\
```

##### Installing/Updating Python Modules

All of the modules needed for these scripts were installed when the environment was built above, but additional modules can be installed (and/or updated) using the "conda" CLI.  For example to install the pandas module, enter the following in a command prompt or terminal window:
```
conda install pandas
```

To update the pandas module to the latest version, enter the following in a command prompt or terminal window:
```
conda update pandas
```

The external modules can also be updated all together with the following command:
```
> conda update configparser gdal numpy pandas
```

###### Earth Engine API

After installing the Python Earth Engine API module, you will need to authorize access to Earth Engine by running the following command in the command prompt or terminal.
```
> earthengine authenticate
```

"To use Earth Engine, you need access either via a Google Cloud project that's registered to use Earth Engine or via an individually signed-up account."
[Register](https://code.earthengine.google.com/register) and
[Guide](https://developers.google.com/earth-engine/guides/access)<br>
> NOTE: All Earth Engine users will now need to use a Google Cloud project (which is also registered for designated uses, such as academic, gov., commercial, etc.) to access Earth Engine.

To test if the authentication was successful, you can run the following command which will build a simple Earth Engine object and test check it can be retrieved.
```
> python -c "import ee; ee.Initialize(project='your_gcloud_project_id'); print(ee.Number(1).getInfo())"
```

###### GDAL

After installing GDAL, you may need to manually set the GDAL_DATA user environmental variable.

####### Windows

You can check the current value of the variable at the command prompt:
```
echo %GDAL_DATA%
```

If GDAL_DATA is set, this will return a folder path (something similar to C:\Miniconda3\envs\ee-tools\Library\share\gdal)

If GDAL_DATA is not set, it can be set from the command prompt (note, your path may vary):
```
> setx GDAL_DATA "C:\Miniconda3\envs\ee-tools\Library\share\gdal"
```

The GDAL_DATA environment variable can also be set through the Windows Control Panel (System -> Advanced system settings -> Environment Variables).

####### Linux / Mac

You can check the current value of the variable at the terminal:

```
echo $GDAL_DATA
```

If GDAL_DATA is set, this will return a folder path (something similar to /Users/<USER>/miniconda3/envs/py311/share/gdal)

If GDAL_DATA is not set, it can be set from the terminal or added to your .bashrc (note, your path may vary):

```
export GDAL_DATA=/Users/<USER>/miniconda3/envs/py311/share/gdal
```

###### Jupyter Notebooks

While the py311 is activated in command prompt/terminal, open the jupyter notebooks in a browser

```
> jupyter lab
```

Once the jupyter lab dashboard opens in a browser, use the File Browser on the left hand side to locate the "ee_zonal_stats.ipynb" and "post_processing.ipynb"
notebooks within the "notebooks" subfolder of this github repository. From there, you will be able to follow along the guides within each notebook.

--------

## Field- and HUC-level geodatabase and geopackage development workflow (jupyter notebooks - python)
1. Google Earth Engine (GEE) zonal stats export scripts - ee_zonal_stats.ipynb
2. Python post-processing scripts, Field- and HUC-level geodatabase and geopackage preparation scripts - post_processing.ipynb


1. GEE zonal stats export workflow overview:
   
### Export irrigation/water use field-level summaries and small pond evaporation HUC-level summaries to Google Cloud Storage or Google Drive (recommended)<br>
> Field-level exports are year-specific (shifted water-year months, Nov-Oct) and export separately as composite dataframes (similar to an ArcGIS attribute table for a shapefile)<br>
> Field-level irrigation/water use summaries: monthly (e.g, ETa, ETo, EToF), annual (e.g., irrigation status), and static (e.g., HUC attributes) summaries for ~250,000 features<br>
> HUC-level small pond evaporation summaries: monthly and monthly climatology (ETo and Evaporation) summaries for HUC8 and HUC12 features


2. Post-processing workflow overview:

### **Post-Processing Workflow**
1. Concatenate individual static & annual irrigation/water use summaries (creates one table per year)
2. Join ET Demands data to field summaries
3. Gap-fill EToF using linear interpolation (1 mo) or climatologies (2+ mo)
   * **NOTE**: This step requires all individual annual tables within the respective gap-filling window to be processed in the previous step (i.e., ET Demands join)
   * Start/End year options for each gap-filling window:
    > 1985-1991<br>
    > 1992-1997<br>
    > 1998-2003<br>
    > 2004-2009<br>
    > 2010-2015<br>
    > 2016-2022
4. Soil moisture carry forward and applied water calculations
   * Final field-level stats tables/CSVs will be produced during this step
5. HUC8/HUC12 aggregations of irrigation/water use summaries
6. HUC-level irrigation/water use shapefile preparation
7. Field-level geopackage preparation
8. HUC-level geopackage preparation
    * includes irrigation/water use and small pond evaporation summaries
<br>


--------







# **Environment Setup**

## Requirements
1. Python 3.11
2. earthengine-api
3. jupyterlab
4. pandas
5. polars
6. refet
7. xarray
8. netcdf4
9. joblib
10. tqdm
11. numpy
12. geopandas
13. gdal

--------

### Python

The pre_processing, ee_zonal_stats, and post_processing Python jupyter notebooks have been developed primarily for Python 3.11+.

### Earth Engine
To run the pre_processing and ee_zonal_stats notebooks you must have an Earth Engine account.  If you do not have an account, please go to the Earth Engine [signup page](https://signup.earthengine.google.com)

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
conda update -n base -c conda conda
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
conda activate py311
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
conda update configparser gdal numpy pandas
```

###### Earth Engine API

After installing the Python Earth Engine API module, you will need to authorize access to Earth Engine by running the following command in the command prompt or terminal.
```
earthengine authenticate
```

"To use Earth Engine, you need access either via a Google Cloud project that's registered to use Earth Engine or via an individually signed-up account."
[Register](https://code.earthengine.google.com/register) and
[Guide](https://developers.google.com/earth-engine/guides/access)<br>
> NOTE: All Earth Engine users will now need to use a Google Cloud project (which is also registered for designated uses, such as academic, gov., commercial, etc.) to access Earth Engine.

To test if the authentication was successful, you can run the following command which will build a simple Earth Engine object and test check it can be retrieved.
```
python -c "import ee; ee.Initialize(project='your_gcloud_project_id'); print(ee.Number(1).getInfo())"
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
setx GDAL_DATA "C:\Miniconda3\envs\ee-tools\Library\share\gdal"
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

###### Jupyter Notebooks and Jupyter Lab

The environment file installs a python package called "jupyterlab" as opposed to "notebook". It is recommended to use Jupyter Lab instead of the classic Jupyter Notebook package. The advantages of using Jupyter Lab over the classic Jupyter Notebook is that with Lab you can have multiple kernels running at the same time, which allows you to manage/run/edit/visualize all of your notebooks in one location/dashboard. While the py311 environment is activated in a command prompt/terminal, open jupyter lab in a browser using the following command.

```
jupyter lab
```

Once the jupyter lab dashboard opens in a browser, use the File Browser on the left hand side to locate the "ee_zonal_stats.ipynb" and "post_processing.ipynb"
notebooks within the "notebooks" subfolder of this github repository. From there, you will be able to follow along the guides within each notebook.

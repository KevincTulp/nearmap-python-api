
# Installing Nearmap-Python-API on Windows Operating Systems

****

<h2>Installing Nearmap-Python-API</h2>

1.) Ensure you have ***ONE*** of the following Python Package Managers Installed:
- Conda (Data Science Toolkit): https://www.anaconda.com/products/individual
- Miniconda (Minimal Installer for Conda): https://docs.conda.io/en/latest/miniconda.html
- MiniForge3: https://github.com/conda-forge/miniforge#miniforge3
- MambaForge: https://github.com/conda-forge/miniforge#mambaforge

2.) Open the Conda Command Prompt. More info: https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html#starting-conda 
    
- **Note: Unlike Linux & macOS, Windows Conda should not be called from the default windows command prompt**

3.) Download or GIT the nearmap-python-api from github

**For Nearmap-Py3-Standard Library Installer:**

- 4.) Map to the install directory: ```cd nearmap-python-api/install" directory```

- 5.) Run: ```make env```

- 6.) Activate the conda environment ```conda activate nearmap-py3```

**For Nearmap-Py3-Advanced Library Installer:**

- 4.) Map to the install directory: ```cd nearmap-python-api/install/advanced_analytics ```

- 5.) Run: ```make env```

- 6.) Activate the conda environment ```conda activate nearmap-py3-advanced```

This will deploy a new conda environment from scripts at the root + install directory of the project with all necessary analytics package dependencies.

<h2>Removing/Updating (Nearmap) or (Nearmap + Virtual Environment + Dependencies)</h2>

1.) Pull the latest Nearmap-Python-API from GitHub

2.) Depending on the installed library map to the appropriate installation directory
  - For Nearmap-Py3 Standard Library: ```cd nearmap-python-api/install``` 
  - For Nearmap-Py3-Advanced Library: ```cd nearmap-python-api/install/advanced_analytics```

- <B>If only updating or removing Nearmap:</B>
  - 3.) Run: ```make pip_remove```
  - Stop at this point if you are only removing Nearmap
  - 4.) Run: ```make pip_install```
  - This will update only the nearmap library on your Virtual Environment
- <B>If updating or removing Nearmap + Virtual Environment + Dependencies:</B>
  - 3.) Run: ```make env_remove```
  - Stop at this point if you are only removing Nearmap & Virtual Environment + Dependencies
  - 4.) Run: ```make env```
  - 5.) Activate the conda environment conda: ```activate nearmap-py3-advanced```
  - This will deploy a new conda environment from scripts at the root + install directory of the project with all necessary analytics package dependencies.


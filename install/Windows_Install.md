
# Installing Nearmap-Python-API on Windows Operating Systems

****

1.) Ensure you have Conda or Miniconda installed from https://www.anaconda.com/

2.) Open the Conda Command Prompt. More info: https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html#starting-conda 
    
- **Note: Unlike Linux & macOS, Windows Conda should not be called from the default windows command prompt**


**For Nearmap-Py3-Standard Library Installer:**

- 3.) Map to the install directory: ```cd``` "nearmap-python-api/install" directory

- 4.) Run: ```make env```

- 5.) Activate the conda environment ```conda activate nearmap-py3```

**For Nearmap-Pyt-Advanced Library Installer:**

- 3.) Map to the install directory: ```cd``` "nearmap-python-api/install/advanced_analytics"

- 4.) Run: ```make env```

- 5.) Activate the conda environment ```conda activate nearmap-py3-advanced```


This will deploy a new conda environment from scripts at the root + install directory of the project with all necessary analytics package dependencies.
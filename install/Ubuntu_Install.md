
# Installing Nearmap-Python-API on Ubuntu Operating Systems including ARM64 (Raspberry PI 4, NVIDIA Jetson Nano...)

** The process supports all versions of Ubuntu supported by MiniForge**
****

<h2>Installing Nearmap-Python-API</h2>

<i>As the Nearmap-Python-API is currently in BETA it is installed in Development Mode. We will be releasing 
"Conda-Forge" and "PIP Install" deployments in the future. The following installation methodology ensures 
compatibility across operating systems and cpu architectures.</i>

** [If You Prefer... Click here for Video Walkthroughs (No Audio)](https://miro.com/app/board/uXjVOQB1X4I=/?invite_link_id=455996902306) **

1.) Update Ubuntu
- ```sudo apt update && sudo apt upgrade```

2.) Install Conda -or- MiniConda/MambaForge... **Install ONLY one or the other!**:
- MiniConda/Mamba Forge:
  - Install MiniForge Conda or MambaForge: https://github.com/conda-forge/miniforge see process below...
    - For MambaForge (Mamba):
      - ```wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh && bash Mambaforge-$(uname)-$(uname -m).sh```
      - ```export PATH=~/Mambaforge/bin:$PATH```
    - For MiniForge3 (Conda):
      - ```wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh && bash Miniforge-$(uname)-$(uname -m).sh```
      - ```export PATH=~/Miniforge3/bin:$PATH```
      - - ```source mambaforge/bin/activate```
- Conda:
  - Conda [Installation Instructions](https://docs.anaconda.com/anaconda/install/linux/)

3.) Install Git:
- ```sudo apt-get install git```

4.) Install Make
- ```sudo apt install make```

4.) Download Nearmap-Python-API from GitHub and install environment using Conda:

- ```cd Documents```
<br></br>
- For Nearmap-Py3-Standard + Nearmap API for Python: (Supported on Arm64 Devices)
  - ```git clone https://github.com/nearmap/nearmap-python-api```
  - ```cd nearmap-python-api/install && make env```


- For Nearmap-Py3-Advanced-Analytics Dependencies + Nearmap API for Python: (Not Supported on ARM64 Devices)
  - ```git clone https://github.com/nearmap/nearmap-python-api```
  - ```cd nearmap-python-api/install/advanced_analytics && make env```

5.) Confirm Installation and Activate Environment:
- To Confirm installation:
  - ```conda list nearmap```
- To Activate the Environment:
  - ```conda activate nearmap-py3``` or ```conda activate nearmap-py3-advanced``` depending on the environment you installed.

<h2>Removing/Updating (Nearmap) or (Nearmap + Virtual Environment + Dependencies)</h2>

1.) If Updating, Delete the existing Nearmap-Python-API directory: ```cd Documents && sudo rm -r nearmap-python-api``` Skip this step if Removing

2.) If Updating, Download Nearmap-Python-API from GitHub: ```git clone https://github.com/nearmap/nearmap-python-api``` Skip this step if Removing

3.) Depending on the installed library map to the appropriate installation directory

- For Nearmap-Py3 Standard Library: ```cd nearmap-python-api/install```
- For Nearmap-Py3-Advanced Library:```cd nearmap-python-api/install/advanced_analytics```


- <B>If only updating Nearmap:</B>
    - 4.) Run: ```make pip_update```
    - This will update only the nearmap library on your Virtual Environment


- <b>If only removing Nearmap:</b>
  - 4.) Run: ```make pip_remove```
  - This will only remove the nearmap library on your Virtual Environment


- <B>If removing Nearmap + Virtual Environment + Dependencies:</B>
    - 4.) Deactivate the 'nearmap-py3' or 'nearmap-py3-advanced' environment by running: ```conda deactivate```
    - 5.) Run: ```make env_remove```
    - This removes the entire Virtual Environment


- <B>If Updating Nearmap + Virtual Environment + Dependencies:</B>
  - 4.) Deactivate the 'nearmap-py3' or 'nearmap-py3-advanced' environment by running: ```conda deactivate```
  - 5.) Run: ```make env_update```
  - 6.) To Confirm installation Run: ```conda list nearmap```
  - 7.) Top Activate the Environment: ```conda activate nearmap-py3``` or ```conda activate nearmap-py3-advanced``` depending on the environment you installed.
  - This will update the virtual environment with all necessary dependencies and Nearmap API


# Installing Nearmap-Python-API on Ubuntu Operating Systems including ARM64 (Raspberry PI 4, NVIDIA Jetson Nano...)

** The process supports all versions of Ubuntu supported by MiniForge**
****

1.) Update Ubuntu
- ```sudo apt update && sudo apt upgrade```

2.) Install Conda of MiniConda/MambaForge... **Install ONLY one or the other!**:
- MiniConda/Mamba Forge:
  - Install MiniForge Conda or MambaForge: https://github.com/conda-forge/miniforge see process below...
    - For MambaForge:
      - ```wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh && bash Mambaforge-$(uname)-$(uname -m).sh```
      - ```export PATH=~/Mambaforge/bin:$PATH```
    - For MiniForge3 (Conda):
      - ```wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh && bash Miniforge-$(uname)-$(uname -m).sh```
      - ```export PATH=~/Miniforge3/bin:$PATH```
- Conda:
  - Conda [Installation Instructions](https://docs.anaconda.com/anaconda/install/linux/)

3.) Install Git:
- ```sudo apt-get install git```

4.) Download Nearmap-Python-API from GitHub and install environment using Conda:


- ```cd Documents && mkdir nearmap && cd nearmap```


- For Nearmap-Py3-Standard: (Supported on Arm64 Devices)
  - ```git clone https://github.com/nearmap/nearmap-python-api```
  - ```cd nearmap-python-api/install && conda env create -f environment.yml```


- For Nearmap-Py3-Advanced-Analytics Dependencies: (Not Supported on ARM64 Devices)
  - ```git clone https://github.com/nearmap/nearmap-python-api```
  - ```cd nearmap-python-api/install/advanced_analytics && conda env create -f environment.yml```

5.) Install Nearmap API for Python **(currently limited to development mode but works... just don't remove the nearmap-python-api folder)**
- Change Directory to the "nearmap-python-api" root directory
  - If you just installed "Nearmap-Py3-Standard":
    - ```cd ..```
  - If you just installed "Nearmap-Py3-Advanced":
    - ```cd ../..```
- Install the Nearmap API for Python in Development Mode using Pip
  - ```python -m pip install -e .```
- To Confirm installation:
  - ```conda list nearmap```


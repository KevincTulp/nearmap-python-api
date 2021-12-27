
# Installing Nearmap-Python-API on Ubuntu Operating Systems including ARM64 (Raspberry PI 4, NVIDIA Jetson Nano...)

** The process supports all versions of Ubuntu supported by MiniForge**
****

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

5.) Confirm Installation:
- To Confirm installation:
  - ```conda list nearmap```


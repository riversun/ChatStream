## Design: Building the ChatStream Library Development Environment

## Build Conda virtual environment

```
conda update -n base -c defaults conda --yes
conda create --yes -n env-chatstream
conda activate env-chatstream
conda install python=3.10.10 --yes
```

## Install required packages

```
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
pip install accelerate transformers
pip install fastapi
pip install fastsession
pip install tokflow
pip install "uvicorn[standard]" gunicorn
pip install loadtime
```

## Remove Conda virtual environment

```
conda deactivate
conda remove -n env-chatstream --all --yes
```

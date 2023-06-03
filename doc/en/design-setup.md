# 設計編： ChatStream ライブラリ 開発環境の構築

## Conda 仮想環境の構築

```
conda update -n base -c defaults conda --yes
conda create --yes -n env-chatstream
conda activate env-chatstream
conda install python=3.10.10 --yes
```

## 必要パッケージのインストール

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

## Conda 仮想環境の削除

```
conda deactivate
conda remove -n env-chatstream --all --yes
```

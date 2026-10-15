# === MNIST Lab (PyTorch) with ipywidgets ===
FROM python:3.11-slim

# System deps for matplotlib/Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install CPU-only PyTorch + deps + JupyterLab + ipywidgets + pandas
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        torch torchvision && \
    pip install --no-cache-dir jupyterlab matplotlib ipywidgets ipycanvas pandas gensim scikit-learn seaborn

# Pre-download the word2vec model
RUN python -c "import gensim.downloader as api; api.load('glove-wiki-gigaword-100')"

EXPOSE 8888

# No auth token for classroom simplicity; change if needed
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--NotebookApp.token=", "--NotebookApp.password="]

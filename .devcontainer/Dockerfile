FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm
LABEL maintainer="Elkia-core"
LABEL description="Entorno científico avanzado para el tablero multiagente Disboard-NGNL (Tet / Stephanie Dola HITL)"

# Dependencias del sistema: LaTeX completo, LibreOffice, utilidades PDF y herramientas base
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    texlive-fonts-extra \
    latexmk \
    libreoffice-writer \
    libreoffice-calc \
    poppler-utils \
    pandoc \
    git \
    curl \
    build-essential \
    locales \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:UTF-8
ENV LC_ALL=en_US.UTF-8

WORKDIR /workspaces/Disboard-NGNL
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

CMD ["bash"]

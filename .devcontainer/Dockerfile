# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# ---------------------------------------------------------------------------
# Metadatos
# ---------------------------------------------------------------------------
LABEL maintainer="Elkia-core"
LABEL description="Entorno científico para Disboard-NGNL (Tet / Stephanie Dola HITL). Shiro opera con el proveedor que Suniaster asigne."
LABEL org.opencontainers.image.title="disboard-ngnl-devcontainer"
LABEL org.opencontainers.image.source="https://github.com/<tu-usuario>/Disboard-NGNL"
LABEL org.opencontainers.image.licenses="MIT"

# ---------------------------------------------------------------------------
# Variables de entorno base
# ---------------------------------------------------------------------------
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/vscode/.local/bin:${PATH}"

# ---------------------------------------------------------------------------
# Dependencias del sistema
# ---------------------------------------------------------------------------
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    # --- LaTeX ---
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-science \
    texlive-bibtex-extra \
    texlive-lang-spanish \
    biber \
    latexmk \
    # --- LibreOffice ---
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-java-common \
    # --- PDF ---
    poppler-utils \
    qpdf \
    ghostscript \
   # --- Chromium para smoke tests de Playwright ---
   libatk1.0-0 \
   libatk-bridge2.0-0 \
   libatspi2.0-0 \
   libnss3 \
   libx11-xcb1 \
   libxcomposite1 \
   libxdamage1 \
   libxfixes3 \
   libxrandr2 \
   libgbm1 \
   libxkbcommon0 \
   libxshmfence1 \
   libgtk-3-0 \
    # --- Documentos y utilidades ---
    pandoc \
    git \
    curl \
    wget \
    gnupg \
    ca-certificates \
    build-essential \
    locales \
    tzdata \
    sudo \
    # --- PostgreSQL client (inspección del checkpointer) ---
    postgresql-client \
    # --- SQLite (checkpointer en modo memory/SQLite) ---
    sqlite3 \
    # --- STT/TTS local ---
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    espeak-ng \
    libespeak1 \
 && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
 && sed -i -e 's/# es_MX.UTF-8 UTF-8/es_MX.UTF-8 UTF-8/' /etc/locale.gen \
 && dpkg-reconfigure --frontend=noninteractive locales \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Cloudflared (opcional; el usuario lo invoca con `make tunnel`)
# ---------------------------------------------------------------------------
RUN curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb \
 && dpkg -i /tmp/cloudflared.deb \
 && rm -f /tmp/cloudflared.deb

# ---------------------------------------------------------------------------
# Directorio de trabajo
# ---------------------------------------------------------------------------
WORKDIR /workspaces/Disboard-NGNL

# ---------------------------------------------------------------------------
# Dependencias Python
# ---------------------------------------------------------------------------
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then touch requirements.txt; fi \
 && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Antigravity CLI (agy) — herramienta OPCIONAL para Shiro.
# ---------------------------------------------------------------------------
RUN curl -fsSL https://antigravity.google/cli/install.sh | bash \
 && echo 'export PATH="$HOME/.local/bin:$PATH"' >> /etc/bash.bashrc

# ---------------------------------------------------------------------------
# Usuario no root
# ---------------------------------------------------------------------------
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
      groupadd --gid ${USER_GID} ${USERNAME} \
      && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} \
      && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/${USERNAME}; \
    fi \
 && chown -R ${USERNAME}:${USERNAME} /workspaces/Disboard-NGNL

USER ${USERNAME}

# ---------------------------------------------------------------------------
# Healthcheck: solo lo obligatorio para el entorno.
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
  CMD python --version \
   && latexmk --version >/dev/null \
   && libreoffice --version >/dev/null \
   || exit 1

CMD ["bash"]

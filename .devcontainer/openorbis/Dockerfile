FROM --platform=linux/amd64 ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# ── System packages (Mirrored from main Dockerfile) ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    jq \
    python3 \
    python3-pip \
    unzip \
    wget \
    sudo \
    cifs-utils \
    git \
    zsh \
    p7zip-full \
    less \
    lftp \
    libgl1 \
    libglu1-mesa \
    libx11-6 \
    libfontconfig1 \
    libfreetype6 \
    xvfb \
    alsa-utils \
    libpulse0 \
    build-essential \
    cmake \
    libmbedtls-dev \
    uthash-dev \
    bsdmainutils \
    smbclient \
    libicu-dev \
    icu-devtools \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js 22 (Mirrored from main Dockerfile) ──────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Prettier ────────────────────────────────────────────────────────────────────
RUN npm install -g prettier

# ── OpenCode CLI (Mirrored from main Dockerfile) ────────────────────────────────
RUN curl -fsSL -o /tmp/opencode.tar.gz https://github.com/anomalyco/opencode/releases/download/v1.15.0/opencode-linux-x64.tar.gz \
    && tar -xzf /tmp/opencode.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/opencode \
    && rm /tmp/opencode.tar.gz

# ── OpenOrbis SDK Environment Setup ──────────────────────────────────────────────
# We create the directory where the SDK should be placed.
# The user will mount or copy the SDK files into this directory.
RUN mkdir -p /opt/openorbis
ENV ORBIS_SDK_PATH=/opt/openorbis

# ── Python packages (Mirrored from main Dockerfile) ──────────────────────────────
RUN pip3 install --break-system-packages beautifulsoup4==4.14.3 lxml==6.1.0 requests==2.32.3 pycryptodome==3.23.0

# ── Non-root user (vscode convention) ──────────────────────────────────────────
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN if getent passwd $USER_UID > /dev/null; then \
    userdel -r ubuntu || true; \
    fi \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
RUN usermod -s /usr/bin/zsh $USERNAME \
    && sudo -u $USERNAME sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

USER $USERNAME
WORKDIR /workspace

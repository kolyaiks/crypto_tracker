FROM accetto/ubuntu-vnc-xfce-g3:24.04
LABEL authors="kolyaiks"

# running as root to do apt-get update
USER root

# installing python and libs
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    libgl1 libglib2.0-0 \
    libxcb1 libx11-xcb1 \
    libxrender1 libxi6 \
    libxkbcommon0 libxkbcommon-x11-0 \
    libdbus-1-3 libfontconfig1 libfreetype6  \
    libsm6 libice6 \
    libxcb-cursor0 libegl1 \
    python3 \
    python3-pip \
    python3-pyqt6 \
    python3-pandas \
    python3-requests

# application files
WORKDIR /app
COPY crypto_tracker.py config.ini portfolio.csv /app/

# exposing port 5901 for VNC viewer and 6901 for access via noVNC using web browser
EXPOSE 5901
EXPOSE 6901

# auto-start
CMD ["python3", "/app/crypto_tracker.py"]


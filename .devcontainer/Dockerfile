# ROS Version
FROM osrf/ros:humble-desktop-full

ENV DEBIAN_FRONTEND=noninteractive

# General Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nano \
    wget \
    sudo \
    iproute2 \
    htop \
    iputils-ping \
    net-tools \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# Clearpath Packages
RUN apt-get update && apt-get install -y \
    ros-humble-clearpath-simulator \
    ros-humble-clearpath-nav2-demos \
    && rm -rf /var/lib/apt/lists/*

# Realsense Camera
RUN mkdir -p /etc/apt/keyrings \
    && curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc | gpg --dearmor | tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null \
    && echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/librealsense.list \
    && apt-get update

RUN apt-get install -y \
    librealsense2-utils \
    ros-humble-realsense2-camera \
    ros-humble-realsense2-description \
    && rm -rf /var/lib/apt/lists/*

# Python Libraries
# COPY .devcontainer/requirements.txt /tmp/requirements.txt
# RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
#     && rm /tmp/requirements.txt
RUN pip3 install --no-cache-dir opencv-python ultralytics deepface \
    && pip3 freeze > /requirements.txt

# Non-root user 
ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user group and add bash as default shell
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
USER user

# ROS environment setup
RUN echo "source /opt/ros/humble/setup.bash" >> /home/${USERNAME}/.bashrc
# Build workspace 
RUN echo 'if [ -f /workspaces/ros_ws/install/setup.bash ]; then source /workspaces/ros_ws/install/setup.bash; fi' >> /home/${USERNAME}/.bashrc

# NVIDIA Optimus
RUN echo 'export __NV_PRIME_RENDER_OFFLOAD=1' >> /home/${USERNAME}/.bashrc
RUN echo 'export __GLX_VENDOR_LIBRARY_NAME=nvidia' >> /home/${USERNAME}/.bashrc
RUN echo 'export NVIDIA_DRIVER_CAPABILITIES=all' >> /home/${USERNAME}/.bashrc

WORKDIR /workspaces/ros_ws
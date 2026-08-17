#!/bin/bash
set -e

# Add the host's DRM device groups to the user.
# The GIDs come from the actual /dev/dri devices on the host.

add_device_group() {
    local gid="$1"

    # Ignore invalid/missing GIDs
    if [[ -z "$gid" || "$gid" == "0" ]]; then
        return
    fi

    # If a group with this GID already exists, use it.
    local existing_group
    existing_group=$(getent group "$gid" | cut -d: -f1 || true)

    if [[ -z "$existing_group" ]]; then
        existing_group="host_dri_${gid}"
        groupadd --gid "$gid" "$existing_group" 2>/dev/null || true
    fi

    usermod -aG "$existing_group" user 2>/dev/null || true
}

if [[ -d /dev/dri ]]; then
    if [[ -e /dev/dri/card0 ]]; then
        CARD_GID=$(stat -c '%g' /dev/dri/card0)
        add_device_group "$CARD_GID"
    fi

    if [[ -e /dev/dri/renderD128 ]]; then
        RENDER_GID=$(stat -c '%g' /dev/dri/renderD128)
        add_device_group "$RENDER_GID"
    fi
fi

# Make sure ROS environment is initialized.
source /opt/ros/humble/setup.bash

# Continue with the command supplied by Docker/devcontainer.
exec "$@"
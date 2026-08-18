# Accessing Topics Offboard

## Ethernet Setup (Laptop)
1. On your laptop, **Settings > Network > Wired**.
2. Click the plus (**+**) icon at the top to create a new profile.
3. Go to the **IPv4** tab and select **Manual**.
4. Fill in the fields as shown below:

| Setting | Value |
| :--- | :--- |
| **Address** | `192.168.131.101` |
| **Netmask** | `255.255.255.0` |
5. Click **Add** and choose that profile

### Connecting to the Jackal
- Turn the Jackal on
- Connect an ethernet cable from the Jackal to your laptop
  - Ensure the profile is chosen in your wired settings
- Open a terminal on your laptop and verify the connection:
```bash
ping 192.168.131.1
```
- If successful, SSH into the Jackal:
```bash
ssh administrator@192.168.131.1
```

## Ethernet Connection
Inside the **devcontainer**, open a new terminal and source the ethernet script when using a direct wired connection. 

```bash
cd /workspaces/ros_ws/scripts
source ros_ethernet.env
```
## Wi-Fi Setup (Onboard Jackal)
will update is emtpy for now


## Wireless Connection
When using Wi-Fi or wireless AP, you must use the robot environment script and provide the robot's IP address as an argument.
```bash
ping <robot_IP>
source ros_robot.env <robot_IP>
```

If unsure what the robot's IP address is, **SSH into the Jackal**:
```base
ip addr show
```
and look at the IP address shown under wlp2s0. The robot's IP address in the Robohub is : **129.97.71.36**

## Access Point Setup (Onboard Jackal)

will update
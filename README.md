# Offboard Laptop Repository (Jackal-Person-Nav)

This repository contains the docker container, scripts, and project source files to run a full person nav demo.

## Repository Structure
These are the important directories that need to be accessed in this repository.
```text
Jackal-Person-Nav/
├── clearpath/
│   └── robot.yaml          # Main config for the robot (sensor bringup)
├── scripts/
│   └── sourcing scripts    # Networking scripts to access topics offboard
└── src/
    └── project/
        ├── vision_server
        ├── orchestrator
        ├── distance_server
        └── map_annotator
```

## Building the Workspace
1. Pull the repository onto your laptop.
```text
git pull https://github.com/nahl-f/Jackal-Person-Nav
```
2. Open the folder in VS Code using `code .`
3. Using the **Dev Containers** extension, click **Reopen in Container** and wait for it to build.

## Documentation Directory
Refer to the separate documentation pages below for detailed instructions.
* [Accessing Topics](docs/ACCESSING_TOPICS.md)
* [Simulation Documentation](docs/SIMULATION.md)
* [Project Documentation](docs/PROJECT_DOCUMENTATION.md)
* [Debugging](docs/DEBUGGING.md)
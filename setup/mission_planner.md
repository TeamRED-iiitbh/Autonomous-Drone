# Mission Planner Installation on Ubuntu 20.04 using Mono

## Installation Steps

### 1. Add the Mono Repository:

```bash
sudo apt install ca-certificates gnupg
sudo gpg --homedir /tmp --no-default-keyring --keyring /usr/share/keyrings/mono-official-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
echo "deb [signed-by=/usr/share/keyrings/mono-official-archive-keyring.gpg] https://download.mono-project.com/repo/ubuntu stable-focal main" | sudo tee /etc/apt/sources.list.d/mono-official-stable.list
sudo apt update
```

### 2. Install Mono:

```bash
sudo apt install mono-devel  # For development purposes
# OR
sudo apt install mono-complete # For full Mono environment
```

### 3. Download Mission Planner:

- Download the latest zip file from: [https://firmware.ardupilot.org/Tools/MissionPlanner/MissionPlanner-latest.zip](https://firmware.ardupilot.org/Tools/MissionPlanner/MissionPlanner-latest.zip)

### 4. Extract and Run:

```bash
unzip MissionPlanner-latest.zip
cd MissionPlanner
mono MissionPlanner.exe
```

### Troubleshooting

- **Architecture Errors:** If you encounter errors related to "i386" architecture, run the following commands:
  ```bash
  dpkg --print-foreign-architectures
  sudo dpkg --remove-architecture i386
  ```

# Installing QGroundControl (QGC) on Ubuntu

## Choose Your QGC Version:
- **Stable Build:** For tested reliability, [https://docs.qgroundcontrol.com/master/en/getting_started/download_and_install.html](https://docs.qgroundcontrol.com/master/en/getting_started/download_and_install.html)
- **Daily Build:** For the latest features (potentially less stable), [https://docs.qgroundcontrol.com/master/en/releases/daily_builds.html](https://docs.qgroundcontrol.com/master/en/releases/daily_builds.html)

## Installation Steps:

### 1. Update User Permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   sudo apt-get remove modemmanager -y
   ```

### 2. Install Dependencies:
   ```bash
   sudo apt install gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl libqt5gui5 libfuse2 -y
   ```

### 3. Logout and Login:
   * This ensures the permission changes take effect.

### 4. Download and Run QGroundControl AppImage:
   * Download the appropriate AppImage (stable or daily) from the links above.
   * Make it executable:  
     ```bash
     chmod +x ./QGroundControl.AppImage
     ```
   * Run QGroundControl: 
      ```bash
      ./QGroundControl.AppImage
      # Or, double-click the AppImage file
      ``` 
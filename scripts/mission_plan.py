import pandas as pd
import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from mavsdk.geofence import Point, Polygon, GeofenceResult
import math

EARTH_RADIUS = 6371000  # Earth's radius in meters


# Function to convert latitude and longitude to Cartesian coordinates
async def lat_lon_to_cartesian(latitude, longitude):
    """
    Convert latitude and longitude coordinates to Cartesian coordinates (2D).
    """
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longitude)
    x = EARTH_RADIUS * math.cos(lat_rad) * math.cos(lon_rad)
    y = EARTH_RADIUS * math.cos(lat_rad) * math.sin(lon_rad)
    return x, y



# Function to convert Cartesian coordinates to latitude and longitude
async def cartesian_to_lat_lon(x, y):
    """
    Convert Cartesian coordinates (2D) to latitude and longitude coordinates.
    """
    lon = math.degrees(math.atan2(y, x))
    lat = math.degrees(math.asin(y / EARTH_RADIUS))
    return lat, lon



# Function to calculate geofence boundary
async def geofence_boundary(df):
    """
    Calculate the geofence boundary based on the provided GPS coordinates.
    """
    latitude = df['lat'].tolist()  # Convert Pandas Series to list
    longitude = df['lon'].tolist()  # Convert Pandas Series to list
    cartesian_coordinates = [await lat_lon_to_cartesian(lat, lon) for lat, lon in zip(latitude, longitude)]

    # Separate the x and y coordinates
    x_coordinates, y_coordinates = zip(*cartesian_coordinates)

    # Calculate mean values
    x_mean = sum(x_coordinates) / len(x_coordinates)
    y_mean = sum(y_coordinates) / len(y_coordinates)

    # Initialize variables to store the last highest x and y values
    last_highest_distance = 0

    # Calculate the maximum distance from the mean
    for x, y in cartesian_coordinates:
        distance = ((x - x_mean) ** 2 + (y - y_mean) ** 2) ** 0.5
        if distance > last_highest_distance:
            last_highest_distance = distance

    # Calculate the radius for the geofence
    radius = 1.2 * last_highest_distance

    return x_mean, y_mean, radius



# Function to monitor battery percentage
async def battery_percent(drone):
    """
    Monitor battery percentage.
    """
    async for battery in drone.telemetry.battery():
        initial_battery_percentage = battery.remaining_percent
        print(f"Initial battery percentage: {initial_battery_percentage}")
        break




# Function to prepare mission items
async def prepare_mission_items(df):
    """
    Prepare mission items from the provided DataFrame.
    """
    latitude = df['lat']
    longitude = df['lon']
    mission_items = []
    for lat, lon in zip(latitude, longitude):
        mission_items.append(MissionItem(lat, lon, 25, 10, True, float('nan'), float('nan'),
                                         MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'),
                                         float('nan'), float('nan')))
    return mission_items




# Function to upload mission
async def mission_upload(drone, mission_way_points):
    """
    Upload the mission to the drone.
    """
    mission_plan = MissionPlan(mission_way_points)
    await drone.mission.set_return_to_launch_after_mission(True)
    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break



# Function Staring Mission
async def drone_mission(drone):
    """
    Start the drone mission.
    """
    try:
        print("-- Arming")
        await drone.action.arm()
    except Exception as e:
        print(f"Error arming the drone: {e}")
        return  # Exit the function if arming fails

    print("-- Starting mission")
    await drone.mission.start_mission()




# Function to monitor and print mission progress
async def print_mission_progress(drone):
    """
    Monitor and print mission progress.
    """
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: {mission_progress.current}/{mission_progress.total}")




# Function to observe if the drone is in the air and return after landing
async def observe_is_in_air(drone, running_tasks):
    """
    Monitor if the drone is in the air and return after landing.
    """
    was_in_air = False
    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air
        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()
            return




# Function to continuously monitor the drone's position and return home if it moves outside the geofence
async def monitor_drone_position(drone, geofence_center, geofence_radius):
    """
    Continuously monitor the drone's position and return home if it moves outside the geofence.
    """
    while True:
        async for gps_info in drone.telemetry.position():
            current_position = Point(gps_info.latitude_deg, gps_info.longitude_deg)

            # Calculate the distance from the center of the geofence
            distance_to_center = math.sqrt((current_position.latitude_deg - geofence_center[0]) ** 2 + (
                    current_position.longitude_deg - geofence_center[1]) ** 2)

            # Check if the drone is outside the geofence
            if distance_to_center > geofence_radius:
                print("Drone is outside the geofence. Returning home...")
                await drone.action.return_to_launch()
                return  # Exit the function after returning home

            # Sleep for a short interval before checking again
            await asyncio.sleep(1)




# Function to create a circular geofence polygon
async def create_circle_geofence(df, home_lat, home_lon):
    x_center, y_center, radius = await geofence_boundary(df)
    num_vertices = 12  # Adjust the number of vertices for better accuracy
    vertices = []
    for i in range(num_vertices):
        angle = 2 * math.pi * i / num_vertices
        x = x_center + radius * math.cos(angle)
        y = y_center + radius * math.sin(angle)
        x_lat, y_long = await cartesian_to_lat_lon(x, y)
        vertices.append(Point(x_lat, y_long))

    # Add home position to the vertices
    vertices.append(Point(home_lat, home_lon))

    geofence_polygon = Polygon(vertices, Polygon.FenceType.INCLUSION)

    
    return geofence_polygon




# Main function to run the program
async def run():
    drone = System()
    try:
        await drone.connect(system_address="udp://:14540")
        print("Waiting for drone to connect...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                print(f"-- Connected to drone!")
                break

        df = pd.read_csv(r"/home/raj/DRONE/MAVSDK-Python/examples/My_program/geocodes.csv")

        # Fetch the current location coordinates of the drone
        async for telemetry in drone.telemetry.position():
            home_lat = telemetry.latitude_deg
            home_lon = telemetry.longitude_deg
            break

        # Create circular geofence object with home position
        geofence_polygon_points = await create_circle_geofence(df, home_lat, home_lon)
        
        # Upload the geofence to your vehicle
        print("Uploading geofence...")
        await drone.geofence.upload_geofence([geofence_polygon_points])
        print("Geofence uploaded successfully")

        # Prepare mission items
        mission_way_points = await prepare_mission_items(df)
        print("Mission way points updated")

        # Upload mission
        await mission_upload(drone, mission_way_points)
        print("Mission Uploaded")

        # Start mission
        await drone_mission(drone)

        # Print battery percentage
        await battery_percent(drone)

        # Start observing mission progress
        print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))
        running_tasks = [print_mission_progress_task]
        termination_task = asyncio.ensure_future(observe_is_in_air(drone, running_tasks))

        # Wait for the mission to complete
        await termination_task


    except Exception as e:
        print(f"An error occurred: {e}")




# Run the asyncio loop
if __name__ == "__main__":
    asyncio.run(run())
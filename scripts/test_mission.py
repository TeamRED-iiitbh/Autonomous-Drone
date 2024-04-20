import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from mavsdk.geofence import Point, Polygon


async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    # Fetch the home location coordinates, in order to set a boundary around
    # the home location.
    print("Fetching home location coordinates...")
    async for terrain_info in drone.telemetry.home():
        latitude = terrain_info.latitude_deg
        longitude = terrain_info.longitude_deg
        break

    await asyncio.sleep(1)

    # Define your geofence boundary
    p1 = Point(latitude - 0.0001, longitude - 0.0001)
    p2 = Point(latitude + 0.0001, longitude - 0.0001)
    p3 = Point(latitude + 0.0001, longitude + 0.0001)
    p4 = Point(latitude - 0.0001, longitude + 0.0001)
    
    arr = [p1,p2, p3, p4]

    # Create a polygon object using your points
    polygon = Polygon(arr, Polygon.FenceType.INCLUSION)

    # Upload the geofence to your vehicle
    print("Uploading geofence...")
    await drone.geofence.upload_geofence([polygon])
    print("Geofence uploaded!")

    print_mission_progress_task = asyncio.ensure_future(
        print_mission_progress(drone))

    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(
        observe_is_in_air(drone, running_tasks))

    # Define mission items
    mission_items = []
    # Add mission items inside geofence
    mission_items.append(MissionItem(latitude + 0.00005, longitude, 25, 10, True, float('nan'), float('nan'), MissionItem.CameraAction.NONE, 0, 0, 5, 0, 0))
    mission_items.append(MissionItem(latitude, longitude + 0.00005, 25, 10, True, float('nan'), float('nan'), MissionItem.CameraAction.NONE, 0, 0, 5, 0, 0))
    mission_items.append(MissionItem(latitude - 0.00005, longitude, 25, 10, True, float('nan'), float('nan'), MissionItem.CameraAction.NONE, 0, 0, 5, 0, 0))
    mission_items.append(MissionItem(latitude, longitude - 0.00005, 25, 10, True, float('nan'), float('nan'), MissionItem.CameraAction.NONE, 0, 0, 5, 0, 0))
    # Add mission item inside geofence
    mission_items.append(MissionItem(latitude + 0.000002, longitude, 25, 10, True, float('nan'), float('nan'), MissionItem.CameraAction.NONE, 0, 0, 5, 0, 0))

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(True)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    try:
        print("-- Arming")
        await drone.action.arm()
    except Exception as e:
        print(f"Error arming the drone: {e}")
        return

    try:
        print("-- Starting mission")
        await drone.mission.start_mission()
    except Exception as e:
        print(f"Error starting the mission: {e}")  # Print the specific error message
        return

    await termination_task


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")


async def observe_is_in_air(drone, running_tasks):
    """ Monitors whether the drone is flying or not and
    returns after landing """

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


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())

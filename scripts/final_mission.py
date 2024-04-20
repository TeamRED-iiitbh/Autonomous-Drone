import asyncio
from mavsdk import System
from mavsdk.offboard import (Attitude, OffboardError)
from mavsdk.mission import (MissionItem, MissionPlan)

async def battery_percent(drone):
    # Get battery information
    async for battery in drone.telemetry.battery():
        initial_battery_percentage = battery.remaining_percent
        print(f"Initial battery percentage: {initial_battery_percentage}")
        break



async def prepare_mission_items(mission_points):
    mission_items = []
    async for i, j in mission_points:
        mission_items.append(MissionItem(i, j, 25, 10, True, float('nan'), float('nan'), MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'), float('nan'), float('nan')))
    return mission_items



async def mission_upload(drone, mission_way_points):
    mission_plan = MissionPlan(await mission_way_points)
    await drone.mission.set_return_to_launch_after_mission(True)
    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break


async def drone_mission(drone):
    print("-- Arming")
    await drone.action.arm()
    print("-- Starting mission")
    await drone.mission.start_mission()


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: {mission_progress.current}/{mission_progress.total}")


async def observe_is_in_air(drone, running_tasks):
    """ Monitors whether the drone is flying or not and returns after landing """
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
        

async def run():
    # Connect to the drone
    drone = System()
    await drone.connect(system_address="udp://:14540")

    # waiting for confirmation
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    # Print battery percentage
    await battery_percent(drone)

    # Define mission points here 
    mission_points = []

    # Prepare mission items
    mission_way_points = prepare_mission_items(mission_points)

    # Upload mission
    await mission_upload(drone, mission_way_points)

    # Start mission
    await drone_mission(drone)

    # Start observing mission progress
    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))
    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(observe_is_in_air(drone, running_tasks))

    # Wait for the mission to complete
    await termination_task

if __name__ == "__main__":
    # Run the asyncio event loop
    asyncio.run(run())

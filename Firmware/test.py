import dronekit_sitl
from dronekit import connect, VehicleMode
from time import sleep

# Setup SITL
sitl = dronekit_sitl.start_default()
connection_string = sitl.connection_string()

print("******************************INITIALIZING******************************")

# Connect to SITL(virtual drone)
print("Connecting to drone on: {}" .format(connection_string))
vehicle = connect(connection_string, wait_ready = True)

def arm_n_takeoff(altitude):
    while not vehicle.is_armable:
        print("Drone is not armable...")
        sleep(1)
    print("\nDrone is now armable!")

    vehicle.mode = VehicleMode("GUIDED")

    while not vehicle.mode.name == 'GUIDED':
        print("Changing mode to GUIDED...")
        sleep(1)
    print("\nIn GUIDED mode!")

    vehicle.armed = True
    while vehicle.armed != True:
        print("Drone is arming...")
        sleep(1)
    print("\nDrone is armed!")

    # Takeoff!
    vehicle.simple_takeoff(altitude)
    print("Taking off.")

    # Wait until 95% of altitude is reached
    while vehicle.location.global_relative_frame.alt < (altitude * .95):
        print("Height: {}m" .format(vehicle.location.global_relative_frame.alt))
        sleep(1)
    print("\nReached target height!")




arm_n_takeoff(20)


# Land drone
vehicle.mode = "LAND"
while not vehicle.mode.name == "LAND":
    print("Changing to LAND mode...")
    sleep(1)
'''
while vehicle.location.global_relative_frame > 1:
    print("Landing - {}m" .format(vehicle.location.global_relative_frame.alt))
    sleep(1)
'''
print("\nDrone landing!")

vehicle.close()
sitl.stop()
print("******************************END******************************")
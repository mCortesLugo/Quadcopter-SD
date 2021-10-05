import argparse
from dronekit import connect, VehicleMode
from time import sleep


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


# Adds -c possitional argument. This lets the user pass the connection string for the connect() function.
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--connect", help = "Enter drone connection string. If connecting through TCP type tcp:STRING_HERE; No need in UDP")
args = parser.parse_args()

# If no drone connection string is passed SITL will run by default.
if args.connect == None:
    # Setup SITL
    import dronekit_sitl
    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()
else:
    connection_string = args.connect

print("******************************INITIALIZING******************************")

# Connect to drone.
print("Connecting to drone on: {}" .format(connection_string))
vehicle = connect(connection_string, wait_ready = True)

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

# If sitl not used then no need to stop sitl
if args.connect == None:
    print("I'M HERE!!!\n")
    sitl.stop()
print("******************************END******************************")
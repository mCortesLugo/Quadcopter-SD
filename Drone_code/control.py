import argparse
from time import sleep
from dronekit import connect, VehicleMode, LocationGlobalRelative

submitConnect = True
submitCoordinates = True
Retreat = False
emergencyLand = False
stopDrone = True
personFound = False
altitude = 10
coordinates = [(-35.3628497594051, 149.16418930153807), \
                (-35.36235104205013, 149.16466137033032), \
                (-35.36348846309731, 149.16625996692213)]

# ---------------------Functions-----------------------------------------
def arm_n_takeoff(altitude):
    
    # Wait for drone to be armable
    while not vehicle.is_armable:
        print("Drone is not armable...")
        sleep(1)  
    print("\nDrone is now armable!")

    # Drone must be set to GUIDED mode for cmds to work.
    vehicle.mode = VehicleMode("GUIDED")

    # Wait for the mode to change to GUIDED
    while not vehicle.mode.name == 'GUIDED':
        print("Changing mode to GUIDED...")
        sleep(1)
    print("\nIn GUIDED mode!")

    # Arm drone and wait for it to occur.
    vehicle.armed = True
    while vehicle.armed != True:
        print("Arming drone...")
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

# This function will land the vehicle at launch location or current location.
# This will be called when script is done; retreat is pressed in UI; or
# the emergency land button is pressed.
# If the emergencyLand = 0 then and RTL cmd is executed; else a land is.
def land():
    global vehicle, args, emergencyLand

    if not emergencyLand:
        # Return to Launch
        print("Returning to launch.")
        vehicle.mode = VehicleMode("RTL")
    else:
        # Land drone
        vehicle.mode = "LAND"
        while not vehicle.mode.name == "LAND":
            print("Changing to LAND mode...")
            sleep(1)
        print("Drone Switched to LAND mode!")
        print("Landing.")

    print("Close vehicle object.")
    vehicle.close()

    # If sitl used close it
    if args.connect is None:
        global sitl
        print("Ending SITL simulator.")
        sitl.stop()

    # End program execution.
    exit()

# Drone loiters when loiter button pressed. When toggled again
# drone will continue mission.
def loiter():
    global stopDrone

    # Change to Loiter mode.
    vehicle.mode = VehicleMode("LOITER")   
    while not vehicle.mode.name == "LOITER":
        print("Changing to LOITER mode...")
        sleep(1)
    print("Drone in LOITER mode.")  

    # Wait for user to exit loiter mode
    while stopDrone:
        sleep(1)
        print("Loitering. toggle loiter button to continue mission")
        sleep(10)
        stopDrone = False
    print("Continueing mission.")
    
    # Drone must be set to GUIDED mode for cmds to work.
    vehicle.mode = VehicleMode("GUIDED")

    # Wait for the mode to change to GUIDED
    while not vehicle.mode.name == 'GUIDED':
        print("Changing mode to GUIDED...")
        sleep(1)
    print("\nIn GUIDED mode!")
    
    return

def search(coordinates):
    arm_n_takeoff(altitude)

    # Execute every move to cmd until no more coordinates.
    for x in coordinates:
        destination = LocationGlobalRelative(x[0], x[1], altitude)

        # Tells drone to move to location
        vehicle.simple_goto(destination)

        sleep(15)   # temporary until I find how to measure distance to target.

        '''while NotReached or Retreat or emergencyLand or stopDrone:
                NOP'''
        # If user presses Retreat button exit and RTL
        if Retreat:
            print("RETREAAAAT!")
            land()

        # If user presses emergency land button, drone lands.
        # Vehicle object closed and script exits.
        if emergencyLand:
            print("EMERGENCY LAND!")
            land()

        # If StopDrone button is pressed drone will loiter until
        # commanded to continue.    
        if stopDrone:
            print("Mission Paused.")
            loiter()

# -----------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--connect", help = "Enter drone connection string. If connecting through TCP type tcp:STRING_HERE; No need in UDP")
args = parser.parse_args()

# If no connection string passed, then start sitl.
if args.connect == None:
    import dronekit_sitl
    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()
else:
    connection_string = args.connect

print("******************************INITIALIZING******************************")


# Wait for user to select drone in user interface.
while(not submitConnect):
    print("Waiting for drone connection...")
    sleep(1)

print("Connecting to drone on: {}" .format(connection_string))
vehicle = connect(connection_string, wait_ready = True)

# Wait for user to enter 4 corner coordinates in user interface
while(not submitCoordinates):
    print("Waiting for user to enter coordinates...")
    sleep(1)

# This function takes in the list of coordinates(tuple) and searches the
# specified area for the rescue target
search(coordinates)

land()

import math
import argparse
from time import sleep
from dronekit import connect, VehicleMode, LocationGlobalRelative

# This flag is set when searching for multiple targets.
multi_rescue = 0

# Telemetry variables used in UI
batteryPercent = 0.0
voltage = 0.0
current = 0.0
position = tuple()
height = 0.0
velocity = 0.0
gps = None

# These flag variables are for testing the code without Lisa's part.
# The coordinates are an example. The CV found list will hold the locations
# of the people found.
submitConnect = True
submitCoordinates = True
Retreat = False
emergencyLand = False
stopDrone = False
personFound = False
personLocation = []
numOfRescued = 0
#altitude = 10

# Used for testing the script w/o search_algorithm(). Do not use if search_algorithm() in use.
coordinates = [(-35.36386175056098, 149.1647898908397), \
                (-35.36203233417043, 149.16445339580716), \
                (-35.361818899557925, 149.16618073697418), \
                    (-35.36366051678722, 149.16665183001973)]

# Test input for search_algorith(). Not a perfect rectangle
testCoordinates =  [(-35.36165545753266, 149.1603591066628),    \
                    (-35.36148046674933, 149.1650368792219),    \
                    (-35.36391280463349, 149.16083117545315),   \
                    (-35.364227778280814, 149.16424294534718)]

# Test input is rectangle
test3 = [(-35.3638805824148, 149.16447914421548), \
                (-35.363915579561386, 149.16236556358444), \
                (-35.36174572778457, 149.16224754639185), \
                    (-35.36171072969738, 149.1643503981872)]

# Test input is half of football field (150' x 160')
test4_ft_ball_field = [(-35.36231539725387, 149.16226176440182), \
                        (-35.36275491977364, 149.1622723321772), \
                            (-35.362758366999635, 149.1617650789596), \
                                (-35.36231712087627, 149.16174605696395)]

test_ft_ball_field_cw = [(-35.362758366999635, 149.1617650789596), (-35.36231712087627, 149.16174605696395), (-35.36231539725387, 149.16226176440182), (-35.36275491977364, 149.1622723321772) ]
 
# Aproximately 50ft x 50ft. Test.
Softball_stadium = [(28.604180078091538, -81.18900877052748), (28.604332475810885, -81.18901279496075), (28.604326611803952, -81.1888585731679), (28.604178558964428, -81.18885112989852)]


# ---------------------Functions-----------------------------------------
def arm_n_takeoff(altitude):
    # Used to detect if drone stuck trying to reach set height.
    count = 1

    # Wait for drone to be armable
    while not vehicle.is_armable:
        print("Drone is not armable...")
        telemetry()
        sleep(1)  
    print("\nDrone is now armable!")

    # Update telemetry.
    telemetry()

    # Drone must be set to GUIDED mode for cmds to work.
    vehicle.mode = VehicleMode("GUIDED")

    # Wait for the mode to change to GUIDED
    while not vehicle.mode.name == 'GUIDED':
        print("Changing mode to GUIDED...")
        vehicle.mode = VehicleMode("GUIDED")    # Issue cmd again in case of instruction interruption.
        telemetry()
        sleep(1)
    print("In GUIDED mode!\n")

    # Update telemetry.
    telemetry()

    # Arm drone and wait for it to occur.
    vehicle.armed = True
    while vehicle.armed != True:
        print("Arming drone...")
        telemetry()
        sleep(1)
    print("Drone armed!")

    # Update telemetry.
    telemetry()

    # Takeoff!
    vehicle.simple_takeoff(altitude)
    print("Taking off.\n")

    # Wait until 95% of altitude is reached
    while vehicle.location.global_relative_frame.alt < (altitude * .95):
        print("Height: {}m" .format(vehicle.location.global_relative_frame.alt))

        # If vehicle stuck trying to reach set height then resent takeoff cmd.
        if count == 7:
            print("Resending takeoff cmd.")
            vehicle.simple_takeoff(altitude)
            count = 1

        telemetry()
        count += 1
        sleep(1)
    print("Reached target height!")

    return


#equation of the line between 2 gps coordinates
def search_algorithm(coordinates, altitude):

    # initialize coords lilst
    coords = [0, 0, 0, 0]

    # coordinates are in (lat,long); coords is a list of the corners of a perfect rectangle that contains the user-inputted search area

    coords[0] = (min(coordinates[0][0], coordinates[3][0]), min(coordinates[0][1], coordinates[1][1]))
    coords[1] = (max(coordinates[1][0], coordinates[2][0]), min(coordinates[0][1], coordinates[1][1]))
    coords[2] = (max(coordinates[1][0], coordinates[2][0]), max(coordinates[2][1], coordinates[3][1]))
    coords[3] = (min(coordinates[0][0], coordinates[3][0]), max(coordinates[2][1], coordinates[3][1]))


    longitudes = [coords[0][1], coords[1][1]]
    latitudes = [coords[0][0], coords[1][0]]

    # interval for search passes: .00006 degrees (approximately 2m)

    i = 1

    while (longitudes[i] < coords[3][1]):
        i += 1
        if i%2 == 0:
            latitudes.append(latitudes[i-1])
            longitudes.append(longitudes[i-1] + .00006)
        else:
            latitudes.append(latitudes[i-3])
            longitudes.append(longitudes[i-3] + .00006)
        

    # write calculated latitudes/longitudes to list of tuples

    waypoints = []
    for i in range(0, len(longitudes)):
        waypoints.append((latitudes[i], longitudes[i]))

    return waypoints

'''
coordinates = [(-35.36165545753266, 149.1603591066628), (-35.36148046674933, 149.1650368792219), (-35.36391280463349, 149.16083117545315), (-35.364227778280814, 149.16424294534718)]
waypoints = search_algorithm(coordinates, 10)
for i in range(0, 5):
    print(waypoints[i])
'''

# This function will land the vehicle at launch location or current location.
# This will be called when script is done; retreat is pressed in UI; or
# the emergency land button is pressed.
# If the emergencyLand = 0 then and RTL cmd is executed; else a land is.
def land():
    
    global vehicle, args, emergencyLand, numOfRescued

    # Update telemetry.
    telemetry()

    if not emergencyLand:
        # Return to Launch
        print("\nReturning to launch.\n")
        vehicle.mode = VehicleMode("RTL")
        while not vehicle.mode.name == "RTL":
            print("Changing to RTL mode...")
            vehicle.mode = VehicleMode("RTL")
            sleep(1)
        print("\nDrone Switched to RTL mode!")

    else:
        # Land drone
        vehicle.mode = "LAND"
        print(vehicle.mode.name)
        while not vehicle.mode.name == "LAND":
            print("Changing to LAND mode...")
            vehicle.mode = "LAND"
            sleep(1)
        print("\nDrone Switched to LAND mode!")
        print("Landing...")

    print("Closing vehicle object.")
    vehicle.close()

    # If sitl used close it
    if args.connect is None:
        global sitl
        print("Ending SITL simulator.")
        sitl.stop()
    
    # Print mission report if rescueing multiple targets.
    if multi_rescue:
        i = 0
        print("\n_______MISSION REPORT:______________________________")
        print("Number of rescued: {}" .format(numOfRescued))
        for location in personLocation:
            print("Person {} at: {}" .format(i, location))
            i += 1
        print("_______END OF MISSION______________________________\n")

    # End program execution.
    exit()


# Drone loiters when loiter button pressed. When toggled again
# drone will continue mission.
def loiter():
    
    global stopDrone

    # Update telemetry.
    telemetry()

    # Change to Loiter mode.
    vehicle.mode = VehicleMode("LOITER")   
    while not vehicle.mode.name == "LOITER":
        print("Changing to LOITER mode...")
        sleep(1)
    print("\nDrone in LOITER mode.")  

    # Update telemetry.
    telemetry()

    # Wait for user to exit loiter mode
    while stopDrone:
        sleep(1)
        print("Loitering. Toggle loiter button to continue mission")
        sleep(3)
        #stopDrone = False
    print("\nContinuing mission.\n")
    
    # Update telemetry.
    telemetry()

    # Drone must be set to GUIDED mode for cmds to work.
    vehicle.mode = VehicleMode("GUIDED")

    # Wait for the mode to change to GUIDED
    while not vehicle.mode.name == 'GUIDED':
        print("Changing mode to GUIDED...")
        sleep(1)
    print("\nIn GUIDED mode!")

    # Udpate telemetry.
    telemetry()
    
    return


# Returns the ground distance in metres between two LocationGlobal objects.
# This method is an approximation, and will not be accurate over large distances and close to the 
# earth's poles. It comes from the ArduPilot test code: 
# https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
def get_distance_meters(aLocation1, aLocation2):

    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5


# This function will iterate through the list of tuples... [(lat, lon), ...]
# It will cmd the drone to move to the location while checking if the user
# has pressed the retreat, emergency land, or stop drone buttons.
# If the CV algorithm finds a person then the drone will print & store its location.
# If battery 20% or less, RTL.
def search(coordinates):

    global batteryPercent, personFound, personLocation, numOfRescued, emergencyLand, velocity,\
            testCoordinates, stopDrone, Retreat
    
    altitude = 3.05   # 3.05ft == 10ft
    
    # Get mission coordinates.
    print("BEFORE - coordinates: {}" .format(coordinates))
    coordinates = search_algorithm(coordinates, altitude)
    print("AFTER - coordinates: {}" .format(coordinates))
    
    arm_n_takeoff(altitude)

    vehicle.airspeed = 20           # Set drone speed in m/s. 6m/s = 13.4mph
    index = 1                       # Used for printing current waypoint #.

    # Execute until no more coordinates. This loop controls what the drone does if special case arises.
    for wp in coordinates:

        # Create LocationGlobalRelative variable of current waypoint to then pass to simple_goto()
        destination = LocationGlobalRelative(wp[0], wp[1], altitude)

        # Get distance between current location and destination. Used to detect arrival to waypoint.
        distance = get_distance_meters(vehicle.location.global_relative_frame, destination)

        # These 2 variables are used for comparison to detect if drone is stuck at waypoint.
        init_distance = distance
        count = 1
        
        # Update telemtry
        telemetry()

        print("\nHeading to waypoint {}: {}\n" .format(index, wp))

        # Tells drone to move to destination.
        vehicle.simple_goto(destination)

        # Keep moving to destination as long as battery ok and no UI interaction occurs.
        while distance >= 1.5 and not Retreat and not emergencyLand and not stopDrone and batteryPercent > 20:

            # Detects if drone gets stuck while heading to waypoint by monitoring change in distance. If 10 iterations have passed
            # and the current distance is 95% or greater of the initial distance; then drone is stuck.
            # simple_goto cmd might have gotten lost.
            if count == 15 and distance/init_distance >= .95:
                print("Getting un-stuck.") 
                vehicle.simple_goto(destination)    # Resend goto cmd to finish heading to wp.
                count = 1                           # Reset count variable to detect if stuck again.

            # If drone randomly changes to RTL go back to GUIDED.
            if vehicle.mode.name == 'RTL':
                vehicle.mode = VehicleMode("GUIDED")
                while not vehicle.mode.name == "GUIDED":
                    print("FIXING RANDOM RTL...")
                print("FIXED: IN GUIDED AGAIN...")
                vehicle.simple_goto(destination)

            if personFound:
                if multi_rescue:    # If rescueing multiple do not RTL at first target find.
                    # Store person location
                    personLocation.append( (vehicle.location.global_frame.lat, vehicle.location.global_frame.lon) )
                
                    print("\nFOUND PERSON AT: ({0:.4f}, {1:.4f})" .format(personLocation[-1][-2], \
                                                                        personLocation[-1][-1])) # Last appended lat & lon
                    # Lower flag to not trigger again, count person, and sleep for 2 seconds to avoid detecting same person.
                    personFound = False
                    numOfRescued += 1
                    sleep(2)
                else:   # Finds 1 target and RTL.
                    print("\nFOUND PERSON AT: ({0:.4f}, {1:.4f})" .format(vehicle.location.global_frame.lat, \
                                                                        vehicle.location.global_frame.lon)) # Last appended lat & lon
                    print("Mission Complete!")
                    land()


            print("Remaining distance: {0:.2f}m | Speed: {1:.2f}mph" .format(distance, velocity))
            telemetry()
            distance = get_distance_meters(vehicle.location.global_frame, destination)

            # Increment count. At count = 10 the code will detect if the distance has changed or not.
            count += 1
            # Used to slow down the amount output printed.
            sleep(.5)

            #vehicle.simple_goto(destination)

            '''NOTE: NOT WORKING - Uncomment next two lines to test Retreat.'''
            #sleep(4)
            #stopDrone = True
            '''Uncomment next two lines to test Retreat.'''
            #sleep(4)
            #Retreat = True
            '''Uncomment next two lines to test emergencyLand.'''
            #sleep(4)
            #emergencyLand = True
            '''Uncomment next two lines to test finding people.'''
            #if index == 4:
                #sleep(3)
                #personFound = True

        # If user presses Retreat button exit and RTL
        if Retreat:
            print("\n-------------------------------------"
            "\nRETREAAAAT!"
            "\n-------------------------------------")
            land()

        # If user presses emergency land button, drone lands.
        # Vehicle object closed and script exits.
        if emergencyLand:
            print("\n-------------------------------------"
            "\nEMERGENCY LAND!"
            "\n-------------------------------------")
            land()
        
        # If battery low, RTL.
        if batteryPercent <= 20:
            print("\n-------------------------------------"
            "\nBATTERY LOW! END OF MISSION."
            "\n-------------------------------------")
            #emergencyLand = True
            land()
            

        # If StopDrone button is pressed drone will loiter until
        # commanded to continue.
        if stopDrone:
            print("\n-------------------------------------"
            "\nMISSION PAUSED."
            "\n-------------------------------------\n")
            #temp = LocationGlobalRelative(position[0], position[1], altitude)
            #vehicle.simple_goto(temp)
            #sleep(20)
            loiter()
            print("Continuing to wp {}:" .format(index))
            stopDrone = False
        index += 1


# This function updates the telemetry data and prints it on the terminal.
def telemetry():
    # These variables are declared at the top of the script. Will be used for
    # the user interface to output telemetry.
    global batteryPercent, voltage, current, position, height, velocity, gps
    
    voltage =           vehicle.battery.voltage
    current =           vehicle.battery.current
    batteryPercent =    vehicle.battery.level
    gps =               vehicle.gps_0
    position =          (vehicle.location.global_frame.lat, vehicle.location.global_frame.lon)
    height =            vehicle.location.global_relative_frame.alt
    velocity =          vehicle.airspeed / 0.44704
    
    '''
    print("\n*************************************")
    print("{}" .format(vehicle.battery))
    print("{}" .format(gps))
    print("Drone position: {}" .format(position))
    print("Drone altitude: {}m" .format(height))
    print("Speed: {}mph" .format(velocity))
    print("*************************************\n")
    '''

# -----------------------------------------------------------------------

# Add -c positional argument to specify connection string as cmd ln arg.
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

print("\nConnecting to drone on: {}\n" .format(connection_string))
vehicle = connect(connection_string, wait_ready = True, timeout = 90)

# Update telemetry
telemetry()

# Wait for user to enter 4 corner coordinates in user interface
while(not submitCoordinates):
    print("Waiting for user to enter coordinates...")
    sleep(1)
print("Coordinates received!")

if batteryPercent <= 10:
    print("Battery low...ending mission")
    vehicle.close()
    exit()

# Update telemetry
telemetry()

# This function takes in the list of coordinates(tuple) and searches the
# specified area for the rescue target
search(test_ft_ball_field_cw)

# Mission ends.
land()

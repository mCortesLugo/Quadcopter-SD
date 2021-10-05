# How to use Start MavProxy:

#### Start dronekit-sitl in terminal:
    
    dronekit-sitl copter
 
#### Open another terminal and type:
    
    mavproxy.py --master=tcp:127.0.0.1:5760 --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551

This command will start MavProxy and connect to the virtual drone at TCP port 5760. It also opens two UDP connections, for telemetry, on ports 14550 & 14551. You can connect Mission Planner to either 14550 or 14551; this applies to the drone script.

The IP address 127.0.0.1 is a loopback address. It is used as a synonym for your device's IP address.

*NOTE: WSL can have a different IP address from your Windows PC. To see your ip adresses in the Cmd Promt type:*
    
    ipconfig

#### Now open Mission Planner and in the upper right corner select UDP -> CONNECT -> 14550 -> OK. Mission Planer should start connecting to the drone.

![MissionPlannerConnect](https://user-images.githubusercontent.com/84548486/133851695-4c95387a-1c41-4080-917d-68197a7d32b0.png)



#### Then run your drone script and pass the positional argument _--connect_ with the connection string. For instance:

    python3 my_script.py --connect 127.0.0.1:14551
    

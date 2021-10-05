# Software Installation Guide:
Getting the environment to work has been troublesome you might encounter issues installing Dronekit, SITL, and MavProxy. Specifically, when installing MavProxy there were some problems. 

You will also encounter CRITICAL messages when running a Dronekit script. You can ignore them - the script will run fine.

This issue can be "fixed" by downgrading Dronekit to version 2.9.1 but then you will have dependency issues and will not be able to install Mavproxy. The problem is that dronekit 2.9.1 uses pymavlink 2.0.6; but mavlink needs pymavlink to be a higher version.



## Install Windows Subsystem for Linux 1(WSL1): Ubuntu 20.04 LTS

Go to Microsoft Store and download Ubuntu 20.04 LTS

After installing Ubuntu check what version of WSL you are using by opening the Cmd Prompt and typing:
   
    wsl -l -v


If you have version 1 as shown below you are set:

![WSL_Version](https://user-images.githubusercontent.com/84548486/133831631-995eea57-c9d2-4947-b176-b254c2bdc0d0.png)


### If you have WSL2 it is recommended to use WSL1 since it can access Windows COM ports(used for connecting to our drone with the RF dongle).



## Install Dronekit & Dronekit SITL

	sudo pip3 install dronekit
	sudo pip3 install dronekit-sitl

Check that your pymavlink version is 2.4.8
	
	pip3 list | grep pymavlink
	
--OR--
	
	pip3 list

If pymavlink is not version 2.4.8:

	sudo pip3 uninstall pymavlink

	sudo pip3 install pymavlink==2.4.8

## Install Mavproxy
	sudo apt-get install python3-dev python3-opencv python3-wxgtk4.0 python3-pip python3-matplotlib python3-lxml python3-pygame
	
	pip3 install PyYAML mavproxy --user

	echo "export PATH=$PATH:$HOME/.local/bin" >> ~/.bashrc


## Install Mission Planner(for viewing drone on a map):

	https://firmware.ardupilot.org/Tools/MissionPlanner/MissionPlanner-latest.msi

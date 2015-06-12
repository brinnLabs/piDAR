# piDAR
Making the Raspberry Pi into a customizable Digital Audio Repeater

For pinouts goto http://pi.gadgetoid.com/pinout though I included pictures for reference too

Note that everything is handled by the settings which the program looks for in the boot directory. You should expand the boot partition to as big as you need it to be. This can be done using tools like the MiniTool Partition Wizard http://www.partitionwizard.com/free-partition-manager.html

This is done to make changing audio files as painless as possible

This script uses pygame for streaming audio and according to their documentation only handles ogg, wav, and has some mp3 functionality

Currently it supports only 1 stream, in the future multiple simultaneous streams will also be an option but I had problems trying to buffer that many songs and streaming 1 at a time was much more manageable.

## Installation

to get this to run at boot create a folder named audio on the boot partition and put piDAR.py and settings.xml in the boot folder. Then edit rc.local which is found in /etc/ by doing

    sudo nano /etc/rc.local
	
and then replace the IP dummy script with

    sudo python /boot/audio/piDAR.py

Make sure to edit the settings file to the layout you would like
   
   
## To Do:
+ add easy install script
+ multiple streams
+ settings GUI
+ more customizable output control

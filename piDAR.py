#==============================================================================
#
#				piDAR the cheap and simple audio repeater
#					Written by Dom Amato 4/28/2015
#
#==============================================================================

#==============================================================================
# import all our modules

import pygame.mixer
from time import sleep
import RPi.GPIO as GPIO
from sys import exit
import numpy as np
import xml.etree.ElementTree as ET
import time
from threading import Timer
import os

#==============================================================================
# our board numbering, we should use BCM to preserve things across hardware
GPIO.setmode(GPIO.BCM)

#==============================================================================
# heres all the XML settings lets break them out into parts
print "Parsing XML"
tree = ET.parse('/boot/Audio/settings.xml')
root = tree.getroot()
mixer = root.find('mixer')
setup = root.find('setup_IO_pins')
input = setup.find('input')
output = setup.find('output')
audio = root.find('Audio')
control = root.find('Control')


#==============================================================================
# all our dictionaries and lists
input_pins = [] #we dont have to search these so lists are good
output_pins = []

#these need to be searchable so we make them dictionaries 
audio_songs = {}
#trickier since we need to know when the song is done playing
audio_playlist = {}
playlist_playing = 0
playlist_pos = 0
playlist_num = 0

controls = {}

#==============================================================================
# take the settings and make it usable 
print "Parsing Input Pins"
for pins in input.findall('pin'):
	#this is ugly but it gives us a list of tuples of the pin and its state
	input_pins.append((int(pins.text), pins.attrib.values()[0]))
	print "\t{}, {}".format(int(pins.text), pins.attrib.values()[0])

print "Parsing Output Pins"	
for pins in output.findall('pin'):
	#this is ugly but it gives us a list of tuples of the pin and its state
	output_pins.append((int(pins.text), pins.attrib.values()[0]))
	print "\t{}, {}".format(int(pins.text), pins.attrib.values()[0])

#is the audio interruptible   
audio_interruptible = audio.attrib.values()[0].upper() == 'TRUE'

print "Parsing Songs"
for songs in audio.findall('song'):
	#trigger pin and the song associated with
	audio_songs[int(songs.attrib.values()[0])] = songs.text
	print "\t{}, trigger {}".format(songs.text, songs.attrib.values()[0])

print "Parsing Playlist"
for songs in audio.findall('playlist'):
	#trigger pin and the songs associated with it
	#the data type is a dictionary that holds an array of song names
	playlist = []
	for songNames in songs.findall('name'):
		playlist.append(songNames.text)
		print "\t{}, trigger {}".format(songNames.text, songs.attrib.values()[0])
	audio_playlist[int(songs.attrib.values()[0])] = playlist

print "Parsing Output Pin Control"	
for outputs in control.findall('Output'):
	#a dictionary that holds a tuple/pair 
	controls[int(outputs.attrib.values()[0])] = (int(outputs.find('pin').text),(int(outputs.find('duration').text) if int(outputs.find('duration').text) > 0 else 0))
	print "\tOutput {}, duration {}, trigger {}".format(int(outputs.find('pin').text), (int(outputs.find('duration').text) if int(outputs.find('duration').text) > 0 else 0), int(outputs.attrib.values()[0]))

#==============================================================================
# setup the mixer
# set sample rate to highest sample rate
# set bit depth to audio bit depth
# channels are probably stereo 
# the buffer size, 1024 should be large enough
print "Setting up mixer"

frequency = int(mixer.find('frequency').text)
bit_depth = int(mixer.find('bit_depth').text) * (-1 if mixer.find('signed').text.upper() == 'TRUE' else 1)
channels = int(mixer.find('channels').text)
buffer = int(mixer.find('buffer').text)

pygame.mixer.init(frequency, bit_depth, channels, buffer)

#=============================================================================   
# we need to handle the threaded callbacks here   

def input_callback(channel):
	global playlist_playing
	global playlist_pos
	global playlist_num
	print "{}, {}".format("Pin triggered", channel)
	#check if we can start a new audio stream
	if(audio_interruptible or not pygame.mixer.music.get_busy()):
		#are we looking at an audio pin
		if(channel in audio_songs):
			print "starting audio playback"
			playlist_playing = 0
			#load audio and play it
			pygame.mixer.music.load(audio_songs[channel])
			pygame.mixer.music.play()
			if(channel in controls):
				#get the current state of the pin and invert it
				state = GPIO.input(controls[channel][0])
				GPIO.output(controls[channel][0], not(state))
				if(controls[channel][1] > 0):
					#check if the pin isn't a toggle
					Timer(controls[channel][1]/1000.0, reset_pin, [controls[channel][0], state]).start()
		#is it a playlist pin
		if(channel in audio_playlist):
			print "starting playlist playback"
			playlist_pos = 0
			playlist_playing = 1
			playlist_num = channel
			#load audio and play it
			pygame.mixer.music.load(audio_playlist[channel][0])
			pygame.mixer.music.play()
			if(channel in controls):
				#get the current state of the pin and invert it
				state = GPIO.input(controls[channel][0])
				GPIO.output(controls[channel][0], not(state))
				if(controls[channel][1] > 0):
					#check if the pin isn't a toggle
					Timer(controls[channel][1]/1000.0, reset_pin, [controls[channel][0], state]).start()
	#check if its just an output pin
	elif(channel in controls):
		#get the current state of the pin and invert it
		state = GPIO.input(controls[channel][0])
		GPIO.output(controls[channel][0], not(state))
		if(controls[channel][1] > 0):
			#check if the pin isn't a toggle
			Timer(controls[channel][1]/1000.0, reset_pin, [controls[channel][0], state]).start()
			
def reset_pin(channel, state):
	GPIO.output(channel, state)

#==============================================================================
#setup pins here
print "Setting up input pins"
for pins in input_pins:
   if (pins[1].upper() == 'PULLUP'):
		GPIO.setup(pins[0], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(pins[0], GPIO.FALLING, callback=input_callback, bouncetime=200) 
		
   else: #we just assume if not declared its a pull down pin 
		GPIO.setup(pins[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.add_event_detect(pins[0], GPIO.RISING, callback=input_callback, bouncetime=200) 

print "Setting up output pins"
for pins in output_pins:
	if (pins[1].upper() == 'HIGH'):
		GPIO.setup(pins[0], GPIO.OUT, initial=GPIO.HIGH)
	else:
		GPIO.setup(pins[0], GPIO.OUT, initial=GPIO.LOW)
   
			
#==============================================================================
#our infinite loop to run everything
print "Starting infinite loop"
#we have to change the working directory or 
#it defaults to wherever called the script
os.chdir("/boot/audio")
print "{}: {}".format("Current Directory", os.getcwd())

while True:
	try:   
		#button presses are threaded so not handled in main loop
		#we have to handle playlist switching here
		if(playlist_playing and not(pygame.mixer.music.get_busy())):
			print "Reached end of song, switching tracks"
			#music is done playing move to the next song if it exists
			if(playlist_pos+1 < len(audio_playlist[playlist_num])):
				playlist_pos+=1
				pygame.mixer.music.load(audio_playlist[playlist_num][playlist_pos])
				pygame.mixer.music.play()
			else:
				print "Reached end of playlist"
				playlist_playing = 0
		sleep(.01)
	except KeyboardInterrupt:
		GPIO.cleanup()
		exit()
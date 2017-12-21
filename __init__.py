# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

# Mycroft libraries
from os.path import dirname
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

# clarifai libraries
from clarifai import rest
from clarifai.rest import ClarifaiApp 
from clarifai.rest import Image as ClImage

#required libraries
import os
import time
import json
import picamera

from time import strftime, gmtime

import re		# regular expression library
import requests		# http library, no known relation to re :)
# NLP/NLG related libraries
from random import *
from pattern.en import parse, Sentence, article

__author__ = 'GregV', '@lachendeKatze'

LOGGER = getLogger(__name__)

class ClothesAssistSkill(MycroftSkill):
    def __init__(self):
        super(ClothesAssistSkill, self).__init__(name="ClothesAssistSkill")

    def initialize(self):
	self.load_data_files(dirname(__file__))
	self.clarifai_app = ClarifaiApp(api_key=self.settings["api_key"])
	self.imgFileName = ""
	LOGGER.info("api_key:" + self.settings["api_key"])	
	self.register_intent_file('clothes.sanity.intent',self.handle_clothes_sanity)
	self.register_intent_file('clothes.assist.intent', self.handle_clothes_assist)

    def handle_clothes_sanity(self,message):

	self.speak("sanity check")	
	fileNumber = message.data.get('type')
	LOGGER.info("*** File Number ***: " + fileNumber)
	self.speak("file " + fileNumber)
	if fileNumber is not None:
		self.imgFileName = "sanity" + fileNumber + ".jpg"
        	self.dataFileName = self.settings["img_location"] + "sanity_" + fileNumber	
		color_results, pattern_results = self.color_and_pattern_results()
        	clothing_description = self.clothesDescription(color_results, pattern_results)
		dataFile = open(self.dataFileName, 'w')
        	dataFile.write( self.imgFileName + "|" + clothing_description + "\n")
        	dataFile.close()
        	# debug, shows text on led matrix       
        	self.enclosure.deactivate_mouth_events()
        	for each_word in clothing_description.split():
                	self.enclosure.mouth_text(each_word)
                	time.sleep(1)
        	self.enclosure.activate_mouth_events()
		self.speak(clothing_description)

	else:
		self.speak("please try again")

    def handle_clothes_assist(self,message):
	
	# vocal indicator that we are in the skill
	self.speak("clothing assist")

	# turn the light on
	r = requests.get('http://' + self.settings["ip"] + '/relay?id=1')

	timeStamp = strftime("%H_%M_%S",gmtime())
	self.imgFileName = "clothesTest" + timeStamp + ".jpg"
	self.dataFileName = self.settings["img_location"] + "clothesTest" + timeStamp

	self.take_picture()

	color_results, pattern_results = self.color_and_pattern_results()	
	clothing_description = self.clothesDescription(color_results, pattern_results)

	
	dataFile = open(self.dataFileName, 'w')
	dataFile.write( self.imgFileName + "|" + clothing_description + "\n")
	dataFile.close()
	
	# turn the light off
	r = requests.get('http://' + self.settings["ip"] + '/relay?id=0')	

	# debug, shows text on led matrix	
	self.enclosure.deactivate_mouth_events()
	for each_word in clothing_description.split():
        	self.enclosure.mouth_text(each_word)
		time.sleep(1)
	self.enclosure.activate_mouth_events()	

	self.speak(clothing_description)

    def take_picture(self):

	self.enclosure.deactivate_mouth_events()
	self.enclosure.mouth_text('Hello!')	
        with picamera.PiCamera() as camera:
		try:
			# camera.resolution = (1280,720)
			# camera.iso = 400
			# camera.awb_mode='off'
			# camera.exposure_mode='night'
		
			# camera.zoom = (0.50,0.50,0.50,0.50)
			# camera.start_preview()
			os.system('fswebcam -r 1280x720 --jpeg 95 --no-banner ' + self.settings["img_location"] + self.imgFileName ) 
			#  /home/mycroft/to_transmit/%H%M%S.jpg')
			time.sleep(3)
			# camera.capture(self.settings["img_location"] + self.imgFileName)
			LOGGER.info('picture taken')
		finally:
			self.enclosure.activate_mouth_events()
			self.enclosure.reset()
			# camera.close()

    def color_and_pattern_results(self):

	color_model = self.clarifai_app.models.get("color")
	pattern_model = self.clarifai_app.models.get("Textures & Patterns")

        try:
	        LOGGER.info('/*/********/----/***********/---/**********/*/')
		LOGGER.info('img location: ' + self.settings["img_location"]) 

		color_resp = color_model.predict_by_filename(self.settings["img_location"]+self.imgFileName)
                pattern_resp = pattern_model.predict_by_filename(self.settings["img_location"]+self.imgFileName)
		
		j_dump_color = json.dumps(color_resp['outputs'][0],separators=(',',':'),indent=3)
		j_load_color = json.loads(j_dump_color)
		

		
		color_index = 0
		color_results = []

		for each in j_load_color['data']['colors']:
			
			colorName = each['w3c']['name']
			colorValue = each['value'] 
			LOGGER.info('*** Color *** : ' + colorName + " | " + str(colorValue)) 		
		        color_results.append(colorName)
		
		j_dump_pattern = json.dumps(pattern_resp['outputs'][0],separators=(',',':'),indent=3)
                j_load_pattern = json.loads(j_dump_pattern)

                pattern_index = 0
		pattern_results = []
		

                for each in j_load_pattern['data']['concepts']:
                        
			patternName = each['name']
			patternValue = each['value']
			LOGGER.info('*** Pattern *** : ' + patternName + " | " + str(patternValue))
			pattern_results.append(patternName)	
			#pattern_results.append(j_load_pattern['data']['concepts'][pattern_index]['name'])
			# pattern_results = pattern_results + j_load_pattern['data']['concepts'][pattern_index]['name'] + " "
                        
			
		return color_results, pattern_results
	except:
		return ['0'],['0']

    def colorsDebug(self, loadColor):
	
	colorTag = ""
	colorRes = []
	color_index = 0
	for each in loadColor['data']['colors']:
                     	
			colorTag = loadColor['data']['colors'][color_index]['w3c']['name']
			colorTag += " | "
			colorTag += loadColor['data']['colors'][color_index]['value']     
			colorRes.append(colorTag)
                        color_index = color_index + 1

	dFile = open('/home/mycroft/colorList', 'w')
	for eachColorTag in colorRes:

        	dFile.write(eachColorTag)
        
	dFile.close()


    def clothesDescription(self, color_results, pattern_results):
    	
	pattern_string = ""
	description_string = "this is "	
	
	# handle colors first
	# the result from clarifai can have at least three words describing a color
        # each word is capitalized; here we separate the individual words so that
        # mycroft can pronounce them; the first color returned is the predominant
        # color, so let's keep all the terms used in the first color.
        
	if len(color_results) == 1:
		
		description_string += self.colorParser(color_results[0],1) 

	elif len(color_results) == 2:

		description_string += self.colorParser(color_results[0],1) + "and " + self.colorParser(color_results[1],2)

	elif len(color_results) >= 3:

		description_string += self.colorParser(color_results[0],1) + self.colorParser(color_results[1],2) + " and " + self.colorParser(color_results[2],3)  

	else: 

		return "we should try again"

	if len(pattern_results) == 0: return "we should try again" 

	else: 

		description_string += " with a " + pattern_results[0] + " pattern"

	return description_string
 
    def colorParser(self, colorString, colorNumber):

	colorTerms = re.findall('[A-Z][a-z]*',colorString)
	colorString = ""
	if colorNumber == 1:
		
		for eachWord in colorTerms:
			colorString += eachWord + " "
	
		return colorString
	else:
		return colorTerms[-1]
		
    # def clothesDescription2(self, color_results, pattern_results):

		

	
    def stop(self):
        pass


def create_skill():
    return ClothesAssistSkill()

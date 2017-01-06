#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
#
#	This file is part of LibreShot Video Editor (http://launchpad.net/libreshot/).
#
#	LibreShot Video Editor is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	LibreShot Video Editor is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with LibreShot Video Editor.  If not, see <http://www.gnu.org/licenses/>.

import os, locale, uuid
import xml.dom.minidom as xml


########################################################################
class effect:
	"""This class represents a media clip on the timeline."""

	#----------------------------------------------------------------------
	def __init__(self, service, paramaters=[]):
		"""Constructor"""
		
		# init variables for clip object
		self.service = service					# the name of the mlt service (i.e. frei0r.water, chroma, sox, etc...)
		self.paramaters = paramaters			# example:  "key" : "123123123",   "variance" : "0.15" (dictionary of settings)
		self.audio_effect = ""
		self.unique_id = str(uuid.uuid1())
		
		if "sox" in service:
			self.audio_effect = service[4:]

	def update_parameter(self, name, value):
		# find the correct parameter
		for param in self.paramaters:
			# check if this param is the correct one
			if name in param.keys():
				# Update the value
				param[name] = value
				return
			
		# parameter not found, so add it
		self.paramaters.append({name:value})
		
		
	def remove_parameter(self, name):
		# find the correct parameter
		for param in self.paramaters:
			# check if this param is the correct one
			if name in param.keys():
				# Update the value
				param.pop(name)
				return


	def isnumeric(self, value):
		return str(value).replace(".", "").replace("-", "").replace(",", "").isdigit()


	def GenerateXML(self, dom, parent_node, in_frame=0.0, out_frame=0.0, track=1):
		print "GenerateXML for an Effect"
		
		service = self.service
		audio_effect = ""
		
		if "sox" in service:
			audio_effect = service[4:]
			service = "sox"
		
		# create effect node
		filter_root = dom.createElement("filter")
		filter_root.setAttribute("mlt_service", service)
		filter_root.setAttribute("in", str(int(round(in_frame))))
		filter_root.setAttribute("out", str(int(round(out_frame))))
		filter_root.setAttribute("track", str(track))
		
		if not audio_effect:
			# VIDEO EFFECT
			# loop through each parameter of this effect, and add a node to the effect XML
			for item in self.paramaters:
				# get key and value
				k = item.items()[0][0]
				v = item.items()[0][1]
				
				# format value for locale (if it's a number)
				if self.isnumeric(v):
					v = locale.str(float(v))					
				
				# add property node
				property_node = dom.createElement("property")
				property_node.setAttribute("name", k)
				# add value
				text = dom.createTextNode(v)
				property_node.appendChild(text)
				# append to the filter node
				filter_root.appendChild(property_node)
		else:
			# AUDIO EFFECT
				# add property node
				property_node = dom.createElement("property")
				property_node.setAttribute("name", "effect1")
				
				# concat all sox params into a single string
				sox_value = ""
				for item in self.paramaters:
					# get key and value
					k = item.items()[0][0]
					v = item.items()[0][1]
					
					# format value for locale (if it's a number)
					if self.isnumeric(v):
						v = locale.str(float(v))	
					
					sox_value = sox_value + " " + v
					
				# add value
				text = dom.createTextNode("%s %s" % (audio_effect, sox_value))
				property_node.appendChild(text)
				# append to the filter node
				filter_root.appendChild(property_node)
		
		# add effect node to parent
		parent_node.appendChild(filter_root)
		
		
	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an LibreShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of old clip classes, to make old project files compatable with
		    newer versions of LibreShot. """
	
		# Check for missing attributes (which means it's an old project format)
		if 'unique_id' not in state:
			state['unique_id'] = str(uuid.uuid1())

		# update the state object with new schema changes
		self.__dict__.update(state)
		
		
		
class effect_metadata:
	""" Class to hold meta data for an effect. """
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self.title = ""
		self.description = ""
		self.icon = ""
		self.category = ""
		self.service = ""
		self.audio_effect = ""
		self.params = []
		
	def get_default_params(self):
		output = []
		
		# loop through params
		for param in self.params:
			# get name and default value
			dict_param = {}
			dict_param[param.name] = param.default
			output.append(dict_param)
			
		# return default params
		return output
		
		
class effect_param_metadata:
	""" Class to hold meta data for an effect. """
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self.title = ""
		self.description = ""
		self.name = ""
		self.type = ""
		self.min = 0.0
		self.max = 0.0
		self.step = 0.10
		self.digits = 2
		self.default = 0.0
		self.values = {}


	
def compare_effect(MyEffect1, MyEffect2):
	if MyEffect1.title > MyEffect2.title:
		return 1
	elif MyEffect1.title == MyEffect2.title:
		return 0
	else:
		return -1

	

def get_effects(project=None, directory=None):
	""" Get a list of effect_metatdata objects. """ 
	EFFECTS_DIR = ""
	
	if directory:
		EFFECTS_DIR = directory
	elif project:
		EFFECTS_DIR = project.EFFECTS_DIR
	else:
		EFFECTS_DIR = "/home/jonathan/libreshot/libreshot/effects"
		
	#parse the xml files and get targets that match the project type
	effects = []
	
	for file in os.listdir(EFFECTS_DIR):
		if os.path.isfile(os.path.join(EFFECTS_DIR, file)) and ".xml" in file:
			# load xml effect file
			xmldoc = xml.parse(os.path.join(EFFECTS_DIR, file))
			
			# create effect_metadata class
			effect1 = effect_metadata()
			
			effect1.title = xmldoc.getElementsByTagName("title")[0].childNodes[0].data
			effect1.description = xmldoc.getElementsByTagName("description")[0].childNodes[0].data
			effect1.icon = xmldoc.getElementsByTagName("icon")[0].childNodes[0].data
			effect1.category = xmldoc.getElementsByTagName("category")[0].childNodes[0].data
			effect1.service = xmldoc.getElementsByTagName("service")[0].childNodes[0].data
			
			if "sox" in effect1.service:
				effect1.audio_effect = effect1.service[4:]
				effect1.service = "sox"
			
			params = xmldoc.getElementsByTagName("param")
			for param in params:
				# create effect_param_metadata object
				param1 = effect_param_metadata()
				
				if param.attributes["title"]:
					param1.title = param.attributes["title"].value
				
				if param.attributes["description"]:
					param1.description = param.attributes["description"].value
					
				if param.attributes["name"]:
					param1.name = param.attributes["name"].value
					
				if param.attributes["type"]:
					param1.type = param.attributes["type"].value
					
				if param.getElementsByTagName("min"):
					param1.min = param.getElementsByTagName("min")[0].childNodes[0].data
					
				if param.getElementsByTagName("max"):
					param1.max = param.getElementsByTagName("max")[0].childNodes[0].data
					
				if param.getElementsByTagName("step"):
					param1.step = param.getElementsByTagName("step")[0].childNodes[0].data
					
				if param.getElementsByTagName("digits"):
					param1.digits = param.getElementsByTagName("digits")[0].childNodes[0].data
					
				if param.getElementsByTagName("default"):
					if param.getElementsByTagName("default")[0].childNodes:
						param1.default = param.getElementsByTagName("default")[0].childNodes[0].data
					else:
						param1.default = ""
					
				values = param.getElementsByTagName("value")
				for value in values:
					# create effect_param_metadata object
					name = ""
					num = ""
					
					if value.attributes["name"]:
						name = value.attributes["name"].value
						
					if value.attributes["num"]:
						num = value.attributes["num"].value
						
					# add to parameter
					param1.values[name] = num
					
				# Append param to effect
				effect1.params.append(param1)
					
				
			# add effect to list
			effects.append(effect1)
			
	# get a list of all clips on this track
	effects.sort(compare_effect)

	# return effect list
	return effects



def main():

	# Get list of all effects
	effect1 = get_effects()[0]
	print effect1
	print effect1.get_default_params()
	

if __name__ == "__main__":
	main()
	
	
	
	
	

#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
#
#	This file is part of LibreShot Video Editor (http://launchpad.net/openshot/).
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
#
#
#	   av_formats.py copyright (C) 2010 Andy Finch
#
#	   Can be used to determine which formats/codecs are installed	   

try:
	import mlt
except ImportError:
	print "*** ERROR: MLT Python bindings failed to import ***"

# init the foreign language
from language import Language_Init


class formats:
	
	def __init__(self, melt_command="melt"):
		# init melt command
		self.melt_command = melt_command
		
		# Start the mlt system
		self.repo = mlt.Factory().init()
		
		
	def get_filters(self, format=None):
		""" Get a list of mlt's filters, including frei0r filters """ 
		
		try:
			filters_raw=[]
			
			services = mlt.Repository.filters(self.repo)
			
			for i in range(mlt.Properties.count(services)):
				filters_raw.append(mlt.Properties.get_name(services, i))
				
			# sort list
			filters_raw.sort()
			return filters_raw
		
		except:
			# If the above code fails, use an older technique which uses the 'melt' 
			# command line, and parses the output
			print "Warning: Could not get list of filters using the MLT API.  Falling back to 'melt' executable."
			return self.get_filters_fallback(format)
	
	def get_filters_fallback(self, format=None):
		""" This method is used for backwards compatibility with older versions of MLT.
			Get a list of mlt's filters, including frei0r filters """ 
		
		import subprocess

		# melt -query 
		command = [self.melt_command, "-query", "filters"]
		output = ''
		
		filters_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
									stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))
			
			# wait for process to finish, and then close
			process.stdin.close()
			if process.wait() != 0:
				print "There were some errors calling melt using os.Popen()"
		except:
			return filters_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				filters_raw.append(line.lstrip('  - '))
		
		# sort list
		filters_raw.sort()
		return filters_raw
	
	
	def has_frei0r_installed(self):
		""" Determine if frei0r effects are installed and configured with libmlt. """
		
		for filter in self.get_filters():
			if filter.startswith("frei0r"):
				return True
			
		# no match
		return False
	
		
	def get_vcodecs(self, format=None):
		try:
			vcodecs_raw=[]
			
			# Create the consumer
			c = mlt.Consumer(mlt.Profile(), "avformat")
	
			# Ask for video codecs supports
			c.set('vcodec', 'list')
	
			# Start the consumer to generate the list
			c.start()
	
			# Get the vcodec property
			codecs = mlt.Properties(c.get_data('vcodec'))
			
			# Display the list of codecs
			for i in range(0, codecs.count()):
					vcodecs_raw.append(codecs.get(i))
			
			# sort list
			vcodecs_raw.sort()
			return vcodecs_raw
		
		except:
			# If the above code fails, use an older technique which uses the 'melt' 
			# command line, and parses the output
			print "Warning: Could not get list of video codecs using the MLT API.  Falling back to 'melt' executable."
			return self.get_vcodecs_fallback(format)
	
	def get_vcodecs_fallback(self, format=None):
		""" This method is used for backwards compatibility with older versions of MLT. """
		
		import subprocess
		
		#melt noise -consumer avformat vcodec=list
		command = [self.melt_command, "noise", "-consumer", "avformat", "vcodec=list"]
		output = ''
		
		vcodecs_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
									stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))
			
			# wait for process to finish, and then close
			process.stdin.close()
			if process.wait() != 0:
				print "There were some errors calling melt using os.Popen()"
		except:
			return vcodecs_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				vcodecs_raw.append(line.lstrip('  - '))
		
		# sort list
		vcodecs_raw.sort()
		return vcodecs_raw
	
	
	def get_acodecs(self, format=None):
		try:
			acodecs_raw=[]
			
			# Create the consumer
			c = mlt.Consumer(mlt.Profile(), "avformat")
	
			# Ask for audio codecs supports
			c.set('acodec', 'list')
	
			# Start the consumer to generate the list
			c.start()
	
			# Get the acodec property
			codecs = mlt.Properties(c.get_data('acodec'))
			
			# Display the list of codecs
			for i in range(0, codecs.count()):
					acodecs_raw.append(codecs.get(i))
			
			# sort list
			acodecs_raw.sort()
			return acodecs_raw
		
		except:
			# If the above code fails, use an older technique which uses the 'melt' 
			# command line, and parses the output
			print "Warning: Could not get list of audio codecs using the MLT API.  Falling back to 'melt' executable."
			return self.get_acodecs_fallback(format)
	
	def get_acodecs_fallback(self, format=None):
		""" This method is used for backwards compatibility with older versions of MLT. """

		import subprocess

		#this is the equivalant of running this command in the terminal:
		#melt noise -consumer avformat acodec=list
		command = [self.melt_command, "noise", "-consumer", "avformat", "acodec=list"]
		output = ''
		
		acodecs_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))
			
			# wait for process to finish, and then close
			process.stdin.close()
			if process.wait() != 0:
				print "There were some errors calling melt using os.Popen()"
		except:
			return acodecs_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				acodecs_raw.append(line.lstrip('  - '))
		
		# sort list
		acodecs_raw.sort()
		return acodecs_raw
	
	
	
	def get_formats(self, format=None):
		try:
			formats_raw=[]
			
			# Create the consumer
			c = mlt.Consumer(mlt.Profile(), "avformat")
	
			# Ask for video codecs supports
			c.set('f', 'list')
	
			# Start the consumer to generate the list
			c.start()
	
			# Get the vcodec property
			codecs = mlt.Properties(c.get_data('f'))
			
			# Display the list of codecs
			for i in range(0, codecs.count()):
					formats_raw.append(codecs.get(i))
			
			# sort list
			formats_raw.sort()
			return formats_raw
		
		except:
			# If the above code fails, use an older technique which uses the 'melt' 
			# command line, and parses the output
			print "Warning: Could not get list of formats using the MLT API.  Falling back to 'melt' executable."
			return self.get_formats_fallback(format)

	def get_formats_fallback(self, format=None):
		""" This method is used for backwards compatibility with older versions of MLT. """

		import subprocess

		#this is the equivalant of running this command inthe terminal:
		#melt noise -consumer avformat f=list
		command = [self.melt_command, "noise", "-consumer", "avformat", "f=list"]
		output = ''
		
		formats_raw=[]
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE,
			stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = str(process.stdout.read(20000))
			
			# wait for process to finish, and then close
			process.stdin.close()
			if process.wait() != 0:
				print "There were some errors calling melt using os.Popen()"
		except:
			return formats_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			if " - " in line and "..." not in line and len(line.strip()) > 0:
				formats_raw.append(line.lstrip('  - '))

		# sort list
		formats_raw.sort()
		return formats_raw

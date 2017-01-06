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

import os, uuid, locale 

########################################################################
class keyframe:
	"""This class represents a media clip on the timeline."""

	#----------------------------------------------------------------------
	def __init__(self, frame, height, width, x, y, alpha):
		"""Constructor"""
		
		# init variables for keyframe object
		self.frame = frame
		self.height = height
		self.width = width
		self.x = x
		self.y = y
		self.alpha = alpha
		self.unique_id = str(uuid.uuid1())	
		
	def set_all(self, height, width, x, y, alpha):
		""" Set all properties with 1 method. """
		if height != None:
			self.height = height
		if width != None:	
			self.width = width
		if x != None:
			self.x = x
		if y != None:
			self.y = y
		if alpha != None:
			self.alpha = alpha
		
	def generate_string(self):
		""" Generate the MLT keyframe string for the XML: 0=0%,0%:100%x100%:100; -1=0%,0%:100%x100%:100 """
		
		# generate string
		output = "%d=%s%%,%s%%:%s%%x%s%%:%s; " % (int(round(self.frame)), locale.str(self.x), locale.str(self.y), locale.str(self.width), locale.str(self.height), locale.str(self.alpha * 100.0))
		
		# return string
		return output
	
	def contains_animation(self):
		""" Determine if this keyframe contains an animation (i.e. values that are not zero) """
		
		if self.height != 100.0 or self.width != 100.0 or self.x != 0.0 or self.y != 0.0:
			return True
		else:
			return False
		
		
		
		
		
		
		
		
		
		
		
		

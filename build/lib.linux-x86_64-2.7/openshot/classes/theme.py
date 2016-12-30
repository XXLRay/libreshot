#	OpenShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2010  Jonathan Thomas
#
#	This file is part of OpenShot Video Editor (http://launchpad.net/openshot/).
#
#	OpenShot Video Editor is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	OpenShot Video Editor is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with OpenShot Video Editor.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
from xml.dom import minidom
import messagebox

########################################################################
class theme:
	"""This class simplifies the reading of a theme.xml file. """

	#----------------------------------------------------------------------
	def __init__(self, folder_name, project=None):
		"""Constructor for the theme object """

		# Find the Theme XML file
		self.folder_name = folder_name
		self.project = project
		self.theme_path = os.path.join(self.project.THEMES_DIR, folder_name)
		self.theme_xml_path = os.path.join(self.project.THEMES_DIR, folder_name, "theme.xml")
		
		# dictionary to hold theme settings
		self.settings = {}
		
		try:
			# Load the Theme XML file
			self.xmldoc = minidom.parse(self.theme_xml_path)
			
			# get timeline settings
			self.settings["timeline"] = self.get_timeline_settings()
			
			# get track settings
			self.settings["track"] = self.get_track_settings()
			
			# get clip settings
			self.settings["clip"] = self.get_clip_settings()
			
			# get transitions settings
			self.settings["transition"] = self.get_transition_settings()
			
		except:
			# Show friendly error message
			messagebox.show(_("Error!"), _("Unable to load theme XML file: %s.  OpenShot will use the blue_glass XML theme file instead.") % self.theme_xml_path)
			print "Unable to load theme XML file: %s.  OpenShot will use the blue_glass XML theme file instead." % self.theme_xml_path
			
			# clear any half-filled settings dictionary
			self.settings = {}
		
		
	def get_timeline_settings(self):
		
		output = {}
		output["playhead_text"] = {
			"font" : self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('playhead_text')[0].getElementsByTagName('font')[0].firstChild.toxml(),
			"x" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('playhead_text')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('playhead_text')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}

		output["ruler"] = {
			"height" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('height')[0].firstChild.toxml()),
			"x" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('y')[0].firstChild.toxml()),
			"playhead" : 
				{
					"x" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('playhead')[0].getElementsByTagName('x')[0].firstChild.toxml()),
					"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('playhead')[0].getElementsByTagName('y')[0].firstChild.toxml()),
				},
			
			"playhead_line" : 
				{
					"stroke_color" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('playhead_line')[0].getElementsByTagName('stroke_color')[0].firstChild.toxml(), 16),
					"line_width" : float(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('playhead_line')[0].getElementsByTagName('line_width')[0].firstChild.toxml()),
					"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('playhead_line')[0].getElementsByTagName('y')[0].firstChild.toxml()),
					"length_offset" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('playhead_line')[0].getElementsByTagName('length_offset')[0].firstChild.toxml()),
				},
				
			"time_text" : 
				{
					"font" : self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('time_text')[0].getElementsByTagName('font')[0].firstChild.toxml(),
					"x" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('time_text')[0].getElementsByTagName('x')[0].firstChild.toxml()),
					"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('time_text')[0].getElementsByTagName('y')[0].firstChild.toxml()),
				},
				
			"small_tick" : 
				{
					"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('small_tick')[0].getElementsByTagName('y')[0].firstChild.toxml()),
					"h" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('small_tick')[0].getElementsByTagName('h')[0].firstChild.toxml()),
				},
				
			"medium_tick" : 
				{
					"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('medium_tick')[0].getElementsByTagName('y')[0].firstChild.toxml()),
					"h" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('medium_tick')[0].getElementsByTagName('h')[0].firstChild.toxml()),
				},
				
			"large_tick" : 
				{
					"y" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('large_tick')[0].getElementsByTagName('y')[0].firstChild.toxml()),
					"h" : int(self.xmldoc.getElementsByTagName('timeline')[0].getElementsByTagName('ruler')[0].getElementsByTagName('large_tick')[0].getElementsByTagName('h')[0].firstChild.toxml()),
				},
		}
		
		return output
	
	def get_track_settings(self):
		output = {}
		output["padding"] = int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('padding')[0].firstChild.toxml())
		
		output["track_name_text"] = {
			"font" : self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('track_name_text')[0].getElementsByTagName('font')[0].firstChild.toxml(),
			"x" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('track_name_text')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('track_name_text')[0].getElementsByTagName('y')[0].firstChild.toxml()),
			"w" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('track_name_text')[0].getElementsByTagName('w')[0].firstChild.toxml()),
		}
		
		output["visible"] = {
			"x" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('visible')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('visible')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		output["speaker"] = {
			"x" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('speaker')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('track')[0].getElementsByTagName('speaker')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		return output
	
	def get_clip_settings(self):
		output = {}
		output["collapse_pixel_threshold"] = int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('collapse_pixel_threshold')[0].firstChild.toxml())
		
		output["thumbnail"] = {
			"x" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('thumbnail')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('thumbnail')[0].getElementsByTagName('y')[0].firstChild.toxml()),
			"w" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('thumbnail')[0].getElementsByTagName('w')[0].firstChild.toxml()),
			"h" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('thumbnail')[0].getElementsByTagName('h')[0].firstChild.toxml()),
		}
		
		output["clip_name_text"] = {
			"font" : self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('clip_name_text')[0].getElementsByTagName('font')[0].firstChild.toxml(),
			"font_resize" : self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('clip_name_text')[0].getElementsByTagName('font_resize')[0].firstChild.toxml(),
			"x" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('clip_name_text')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('clip_name_text')[0].getElementsByTagName('y')[0].firstChild.toxml()),
			"collapsed_x" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('clip_name_text')[0].getElementsByTagName('collapsed_x')[0].firstChild.toxml()),
		}
		
		output["rectangle"] = {
			"stroke_color_rgba" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('stroke_color_rgba')[0].firstChild.toxml(), 16),
			"line_width" : float(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('line_width')[0].firstChild.toxml()),
		}
		
		output["visible"] = {
			"x" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('visible')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('visible')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		output["speaker"] = {
			"x" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('speaker')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('speaker')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		output["effect"] = {
			"x" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('effect')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('clip')[0].getElementsByTagName('effect')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		return output
	
	def get_transition_settings(self):
		output = {}
		output["collapse_pixel_threshold_text"] = int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('collapse_pixel_threshold_text')[0].firstChild.toxml())
		output["collapse_pixel_threshold_thumbnail"] = int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('collapse_pixel_threshold_thumbnail')[0].firstChild.toxml())

		output["transition_name_text"] = {
			"font" : self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('transition_name_text')[0].getElementsByTagName('font')[0].firstChild.toxml(),
			"font_resize" : self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('transition_name_text')[0].getElementsByTagName('font_resize')[0].firstChild.toxml(),
			"x" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('transition_name_text')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('transition_name_text')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		output["rectangle"] = {
			"line_width" : float(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('line_width')[0].firstChild.toxml()),
			"stroke_color_rgba" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('stroke_color_rgba')[0].firstChild.toxml(), 16),
			"fill_color_rgba" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('fill_color_rgba')[0].firstChild.toxml(), 16),
			"y" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('y')[0].firstChild.toxml()),
			"h" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('rectangle')[0].getElementsByTagName('h')[0].firstChild.toxml()),
		}
		
		output["thumbnail"] = {
			"x" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('thumbnail')[0].getElementsByTagName('x')[0].firstChild.toxml()),
			"y" : int(self.xmldoc.getElementsByTagName('transition')[0].getElementsByTagName('thumbnail')[0].getElementsByTagName('y')[0].firstChild.toxml()),
		}
		
		return output


#def main():
#	mytheme = theme("blue_glass")
#	print mytheme.settings["transition"]["rectangle"]
#
#if __name__ == "__main__":
#	main()

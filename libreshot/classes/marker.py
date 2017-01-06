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

import gtk, goocanvas


########################################################################
class marker:
	"""This class represents a marker (i.e. a reference point) on the timeline."""

	#----------------------------------------------------------------------
	def __init__(self, marker_name, position, parent):
		"""Constructor"""
		self.name = marker_name
		self.position_on_track = float(position)
		self.parent = parent
		
	#----------------------------------------------------------------------
	def Render(self):
		
		# get the previous track from the parent sequence (if any)
		pixels_per_second = self.parent.get_pixels_per_second()
		y_top = 22
		
		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.project.theme
		canvas_left = self.parent.project.form.TimelineCanvas_Left
		canvas_right = self.parent.project.form.TimelineCanvas_Right
		
		# Add an item to the goocanvas
		root_left = canvas_left.get_root_item ()
		root_right = canvas_right.get_root_item ()
		
		# load marker image
		imgMarker = gtk.image_new_from_file("%s/libreshot/themes/%s/marker.png" % (self.parent.project.form.libreshot_path, theme))
		imgMarker_Width = imgMarker.get_pixbuf().get_width()
		offset = float(imgMarker_Width) / float(2.0)
		
		# determine position
		x = pixels_per_second * self.position_on_track
		
		# Add Left Image to Group
		image1 = goocanvas.Image (parent = root_right,
								  pixbuf = imgMarker.get_pixbuf(),
								  x = x - offset,
								  y = y_top)
		
		# attach button click event to marker image
		image1.connect ("button_press_event", self.on_marker_press)
		
		
	def on_marker_press (self, item, target, event):
		""" This is the click signal for a marker. """

		if event.button == 3:
			# show the marker popup menu
			self.parent.project.form.mnuMarker1.showmnu(event, self)
			
		elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
			# double click event

			# seek to marker
			self.parent.update_video(self.position_on_track)
			
			# raise playhead
			self.parent.raise_play_head()
			
		return True

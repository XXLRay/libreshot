#	OpenShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
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
import gtk, goocanvas
import xml.dom.minidom as xml

from classes import clip, files, marker, timeline, track
# init the foreign language
from language import Language_Init

########################################################################
class sequence:
	"""A sequence contains tracks and clips that make up a scene (aka sequence).  Currently, Openshot
	only contains a single sequence, but soon it will have the ability to create many sequences."""

	#----------------------------------------------------------------------
	def __init__(self, seq_name, project):
		"""Constructor"""

		# Add language support
		translator = Language_Init.Translator(project)
		_ = translator.lang.gettext

		# init variables for sequence
		self.name = seq_name
		self.length = 600.0		   # length in seconds of sequence.  This controls how wide to render the tracks.
		self.project = project	  # reference to current project
		self.scale = 8.0		   # this represents how many seconds per tick mark
		self.tick_pixels = 100	  # number of pixels between each tick mark
		self.play_head_position = 0.0 # position of the play head in seconds

		# init the tracks on the sequence
		self.tracks = []
		self.tracks.append(track.track(_("Track %s") % 2, self))
		self.tracks.append(track.track(_("Track %s") % 1, self))

		# init markers
		self.markers = []

		# reference to play_head goocanvas group
		self.play_head = None
		self.ruler_time = None
		self.play_head_line = None
		self.enable_animated_playhead = True


	def AddMarker(self, marker_name, position_on_track):

		# loop through existing markers (check for duplicates)
		for exiting_marker in self.markers:
			if exiting_marker.position_on_track == position_on_track:
				return

		# Create marker object
		m = marker.marker(marker_name, position_on_track, self)

		# Add to Marker Collection
		self.markers.append(m)

		# re-order marker collection (to keep them in order of their positions)
		self.reorder_markers()

		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Added marker"))

		return m



	def get_marker(self, direction, current_position):


		# check for markers
		if len(self.markers) == 0:
			return None

		if direction == "left":

			# loop through all markers (check for duplicates)
			possible_match = None
			for m in self.markers:

				if m.position_on_track < current_position - 0.20:
					possible_match = m

			# return the match
			return possible_match

		else:
			# right

			# loop through all markers (check for duplicates)
			for m in self.markers:

				if m.position_on_track > current_position + 0.20:
					# return the match
					return m


		# no markers found
		return None



	def AddTrack(self, track_name, position="above", existing_track=None):


		# Add another track
		if existing_track:
			index_existing_track = self.tracks.index(existing_track)
			# insert next to an existing track
			if position == "above":
				self.tracks.insert(index_existing_track, track.track(track_name, self))
			else:
				self.tracks.insert(index_existing_track + 1, track.track(track_name, self))

		else:
			# insert at top of tracks
			self.tracks.insert(0, track.track(track_name, self))

		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Added Track"))


	def rename_track(self, current_track, new_name):
		current_track.name = new_name

		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Renamed track"))


	def get_pixels_per_second(self):
		# calculate the number of pixels per second, based on the scale of the timeline
		return float(self.tick_pixels) / float(self.scale)	   


	def Render(self):

		# Disable window redraws temporarily (prevents flicker)
		self.project.form.MyCanvas_Left.window.freeze_updates()
		self.project.form.TimelineCanvas_Left.window.freeze_updates()
		self.project.form.MyCanvas.window.freeze_updates()
		self.project.form.TimelineCanvas_Right.window.freeze_updates()

		# Clear the canvases
		self.project.form.MyCanvas_Left.set_root_item(goocanvas.Group())
		self.project.form.TimelineCanvas_Left.set_root_item(goocanvas.Group())
		self.project.form.MyCanvas.set_root_item(goocanvas.Group())
		self.project.form.TimelineCanvas_Right.set_root_item(goocanvas.Group())

		# Render Ruler
		self.RenderRuler()

		# Render Markers
		self.RenderMarkers()

		# loop through each track
		for MyTrack in self.tracks:

			# Render track			
			MyTrack.Render()


		# loop through each track
		for MyTrack in self.tracks:

			# loop through each transition, from the bottom up
			for MyTran in MyTrack.transitions:

				# Render track			
				MyTran.Render()

		# Enable window redraws again
		self.project.form.MyCanvas_Left.window.thaw_updates()
		self.project.form.TimelineCanvas_Left.window.thaw_updates()
		self.project.form.MyCanvas.window.thaw_updates()
		self.project.form.TimelineCanvas_Right.window.thaw_updates()

	def GenerateXML(self, dom, xmlParentNode):

		# get frames per second
		fps = self.project.fps()

		multitrack = dom.createElement("multitrack")
		xmlParentNode.appendChild(multitrack)

		# create fake background track (i.e. black background)
		bg_track = track.track("Background Track", self)
		bg_track.parent = self
		bg_end_time = self.Calculate_Length()
		bg_image = files.OpenShotFile(self.project)
		bg_image.name = os.path.join(self.project.IMAGE_DIR, "black.png")
		bg_image.length = bg_end_time
		bg_image.max_frames = round(bg_end_time * fps)

		# set remaining length
		remaining_length = bg_end_time
		position = 0.0
		current_length = 0.0

		# Add the background black clip in sections (5 minute (i.e. 300 seconds) sections)
		while remaining_length > 0.0:
			# calculate length of this section
			if remaining_length > 300.0:
				current_length = 300.0
				remaining_length -= 300.0
			else:
				current_length = remaining_length
				remaining_length = 0.0

			bg_clip = clip.clip("Background Clip", "Gold", position, 0.0, current_length, bg_track, bg_image)
			bg_clip.distort = True
			bg_clip.fill = True
			bg_track.clips.append(bg_clip)

			# calculate position for next section
			position += current_length

		# add XML for background track
		bg_track.GenerateXML(dom, multitrack, fps=fps)

		# loop through each track, from the bottom up
		for MyTrack in reversed(self.tracks):

			# Render track			
			MyTrack.GenerateXML(dom, multitrack, fps=fps)


	def Calculate_Length(self):
		""" Determine the length of this sequence """
		longest_clip = 0.1
		fps = self.project.fps()

		# loop through each track, from the bottom up
		for MyTrack in self.tracks:

			# loop through each clip
			for MyClip in MyTrack.clips:

				# calculate end of clip
				end_of_clip = MyClip.position_on_track + MyClip.length()

				if end_of_clip > longest_clip:
					longest_clip = end_of_clip

		# return longest clip
		return longest_clip + 0.1

	#----------------------------------------------------------------------
	def RenderRuler(self):
		"""This adds a track to the canvas with 3 images: a left, middle, and right"""

		# get the pixels per second from the parent sequence
		pixels_per_second = self.get_pixels_per_second()

		# determine position of playhead
		time = timeline.timeline().get_friendly_time(self.play_head_position * 1000) 

		# Get theme settings
		theme = self.project.theme
		theme_settings = self.project.theme_settings.settings

		# set the top coordinate of this track to the bottom coordinate of the last track
		x = theme_settings["timeline"]["ruler"]["x"]	  
		y_top = theme_settings["timeline"]["ruler"]["y"]

		# determine the height of the timeline
		imgTrack_Track = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Middle.png" % (self.project.form.openshot_path, theme))
		imgTrack_Track_Height = imgTrack_Track.get_pixbuf().get_height()
		timeline_heigth = len(self.tracks) * imgTrack_Track_Height + (len(self.tracks) * theme_settings["track"]["padding"]) + 10

		# get a reference to the 2 main canvas objects & theme
		theme = self.project.theme
		canvas_timeline = self.project.form.MyCanvas
		canvas_timeline_left = self.project.form.MyCanvas_Left
		canvas_left = self.project.form.TimelineCanvas_Left
		canvas_right = self.project.form.TimelineCanvas_Right

		# Add an item to the goocanvas
		root_left = canvas_left.get_root_item ()
		root_right = canvas_right.get_root_item ()

		# Load all 3 images
		imgTrack_Left = gtk.image_new_from_file("%s/openshot/themes/%s/ruler_left.png" % (self.project.form.openshot_path, theme))
		imgTrack_Middle = gtk.image_new_from_file("%s/openshot/themes/%s/ruler_middle.png" % (self.project.form.openshot_path, theme))
		imgTrack_Right = gtk.image_new_from_file("%s/openshot/themes/%s/ruler_right.png" % (self.project.form.openshot_path, theme))	   
		imgTrack_Tick = gtk.image_new_from_file("%s/openshot/themes/%s/ruler_tick.png" % (self.project.form.openshot_path, theme))	   

		# Get Height and Width of Images 
		imgTrack_Left_Height = imgTrack_Left.get_pixbuf().get_height()
		imgTrack_Left_Width = imgTrack_Left.get_pixbuf().get_width()
		imgTrack_Right_Width = imgTrack_Right.get_pixbuf().get_width()		

		# Get Size of Window (to determine how wide the middle image should be streched)
		Size_Of_Middle = int(pixels_per_second * self.length)

		# resize the canvas height and width
		new_size_of_middle = Size_Of_Middle + 200
		
		canvas_timeline.set_bounds (0, 0, new_size_of_middle, timeline_heigth)
		#1.02 is a fudge factor to make up for rounding errors
		#without this, the scrollbar range will be just a little smaller than the
		#size of the canvas_timeline and you wouldn't be able to scroll all the way to the end		
		#I don't know why this changed from 1.4.3 to 1.4.4 - in 1.4.3 I didn't need to do this.
		#My best guess is that the length is calculated differently than in 1.4.3
		self.project.form.hscrollbar2.set_range(0, new_size_of_middle*1.02)
		self.project.form.vscrollbar2.set_range(0, timeline_heigth)
		self.project.form.on_hscrollbar2_value_changed(self.project.form.hscrollbar2)

		# Get the height of the RULER
		ruler_height = theme_settings["timeline"]["ruler"]["height"]
		left_canvas_width = theme_settings["track"]["track_name_text"]["w"]

		# Resize the LEFT RULER
		canvas_timeline_left.set_bounds (0, 0, left_canvas_width, timeline_heigth)
		canvas_left.set_bounds (0, 0, left_canvas_width, ruler_height)
		canvas_left.set_size_request (0, ruler_height)
		self.project.form.timelineWindowLeft.set_size_request (left_canvas_width, ruler_height)
		self.project.form.scrolledwindow_Left.set_size_request (left_canvas_width, 0)

		# Resize the RIGHT RULER
		canvas_right.set_bounds (0, 0, new_size_of_middle + 16, ruler_height)
		canvas_right.set_size_request (0, ruler_height)
		self.project.form.timelinewindowRight.set_size_request (0, ruler_height)

		# Resize RULER Hbox (which holds both the LEFT and RIGHT windows)
		self.project.form.hbox5.set_size_request (0, ruler_height)

		# Resize Middle pixbuf
		middlePixBuf = imgTrack_Middle.get_pixbuf()
		pixbuf_list = self.split_images(middlePixBuf, imgTrack_Left_Height, Size_Of_Middle)

		# Create Group (for the track)
		GroupTrack = goocanvas.Group (parent = root_right)

		# Add Left Image to Group
		image1 = goocanvas.Image (parent = root_left,
				                  pixbuf = imgTrack_Left.get_pixbuf(),
				                  x = x,
				                  y = y_top)

		# Add Middle Image to Group (this can be multiple image tiled together
		pixbuf_x = 0
		for pixbuf in pixbuf_list:
			# get width of this pixbuf
			pixbuf_width = pixbuf.get_width()

			image2 = goocanvas.Image (parent = GroupTrack,
						              pixbuf = pixbuf,
						              x = pixbuf_x,
						              y = y_top)  

			# increment the x
			pixbuf_x = pixbuf_x + pixbuf_width


		# Add Middle Image to Group
		image3 = goocanvas.Image (parent = GroupTrack,
				                  pixbuf = imgTrack_Right.get_pixbuf(),
				                  x = Size_Of_Middle - 1,
				                  y = y_top)

		# Add Playhead position text
		self.ruler_time = goocanvas.Text (parent = root_left,
				                          text = theme_settings["timeline"]["playhead_text"]["font"] % (time[2], time[3], time[4], time[5]),
				                          antialias = True,
				                          use_markup = True,
				                          x = x + theme_settings["timeline"]["playhead_text"]["x"],
				                          y = y_top + theme_settings["timeline"]["playhead_text"]["y"])

		# Resize tick marks for ruler
		tickPixBuf = imgTrack_Tick.get_pixbuf()
		big_tickPixBuf = tickPixBuf.scale_simple(1, theme_settings["timeline"]["ruler"]["large_tick"]["h"], gtk.gdk.INTERP_NEAREST)
		medium_tickPixBuf = tickPixBuf.scale_simple(1, theme_settings["timeline"]["ruler"]["medium_tick"]["h"], gtk.gdk.INTERP_NEAREST)
		small_tickPixBuf = tickPixBuf.scale_simple(1, theme_settings["timeline"]["ruler"]["small_tick"]["h"], gtk.gdk.INTERP_NEAREST)

		# loop through each tick mark
		number_of_ticks = int(self.length / self.scale)
		ruler_pixels = ((float(self.length) / float(self.scale)) * self.tick_pixels)
		
		tick = 0
		end_of_timeline = False

		while end_of_timeline == False:

			# increment tick
			tick = tick + 1

			# get the formatted time code
			milliseconds = (tick * self.scale) * 1000
			time = timeline.timeline().get_friendly_time(milliseconds)

			if (tick * self.tick_pixels + 16) < ruler_pixels:

				# Add Text to the Track
				text1 = goocanvas.Text (parent = GroupTrack,
								        text = theme_settings["timeline"]["ruler"]["time_text"]["font"] % (time[2], time[3], time[4], time[5]),
								        antialias = True,
								        use_markup = True,
								        x = (tick * self.tick_pixels) - theme_settings["timeline"]["ruler"]["time_text"]["x"],
								        y = y_top + theme_settings["timeline"]["ruler"]["time_text"]["y"])				

				# Add BIG TICK Image to Group
				image5 = goocanvas.Image (parent = GroupTrack,
								          pixbuf = big_tickPixBuf,
								          x = (tick * self.tick_pixels),
								          y = y_top + theme_settings["timeline"]["ruler"]["large_tick"]["y"])


			# determine # of minor ticks.  The longer the timeline, the less
			# ticks can be added do to performance reasons.
			number_of_minor_ticks = 6
			if (number_of_ticks * 10) > 1500:
				number_of_minor_ticks = 2

			# Add Minor ticks
			big_tick_x = ((tick - 1) * self.tick_pixels)
			minor_tick_increment = self.tick_pixels / number_of_minor_ticks

			# loop through minor ticks, and add them to the canvas
			for minor_tick in range(1, number_of_minor_ticks):

				# Resize minor tick pixbuf
				tickPixBuf = None
				minor_y_adjustment = theme_settings["timeline"]["ruler"]["small_tick"]["y"]
				if minor_tick == int(number_of_minor_ticks / 2):
					minor_y_adjustment = theme_settings["timeline"]["ruler"]["medium_tick"]["y"]
					tickPixBuf = medium_tickPixBuf
				else:
					tickPixBuf = small_tickPixBuf

				# don't extend past the ruler
				if (big_tick_x + int(minor_tick_increment * minor_tick)) < ruler_pixels:

					# Add minor tick Image to Group
					image5 = goocanvas.Image (parent = GroupTrack,
										      pixbuf = tickPixBuf,
										      x = big_tick_x + int(minor_tick_increment * minor_tick),
										      y = y_top + minor_y_adjustment)
				else:
					end_of_timeline = True
					break

		# Connect signals to ruler to allow drag and drop
		GroupTrack.connect ("button_press_event", self.on_ruler_press)
		GroupTrack.connect ("motion_notify_event", self.on_ruler_motion)
		GroupTrack.connect ("button_release_event", self.on_ruler_release)




	def on_ruler_press(self, item, target, event):

		# enable animated playhead
		self.enable_animated_playhead = True

		if event.button == 1:
			new_x = event.x

			# get the pixels per second from the parent sequence
			pixels_per_second = self.get_pixels_per_second()

			# calculate playhead position
			play_head_position = new_x / pixels_per_second

			if play_head_position < 0:
				play_head_position = 0

			# update video frame
			self.update_video(play_head_position)



	def on_ruler_motion(self, item, target, event):
		#print "on_ruler_motion"

		if (event.state & gtk.gdk.BUTTON1_MASK):
			new_x = event.x

			# disable animated playhead
			self.enable_animated_playhead = False

			# get the pixels per second from the parent sequence
			pixels_per_second = self.get_pixels_per_second()

			# calculate playhead position
			play_head_position = new_x / pixels_per_second

			if play_head_position < 0:
				play_head_position = 0

			# update video frame
			self.update_video(play_head_position)

	def on_ruler_release(self, item, target, event):

		# enable animated playhead
		self.enable_animated_playhead = True

	#----------------------------------------------------------------------
	def RenderMarkers(self):

		# loop through all markers (check for duplicates)
		for m in self.markers:

			# render the marker
			m.Render()



	def reorder_markers(self):
		# get a list of all clips on this track
		self.markers.sort(self.compare_marker)



	def compare_marker(self, marker1, marker2):
		if marker1.position_on_track > marker2.position_on_track:
			return 1
		elif marker1.position_on_track == marker2.position_on_track:
			return 0
		else:
			return -1


	#----------------------------------------------------------------------
	def RenderPlayHead(self):
		"""This adds the playhead to the canvas, and the play head position line"""

		# Get theme settings
		theme_settings = self.project.theme_settings.settings

		# get the pixels per second from the parent sequence
		pixels_per_second = self.get_pixels_per_second()

		# set the top coordinate of this track to the bottom coordinate of the last track
		x = self.play_head_position * pixels_per_second
		x = x + theme_settings["timeline"]["ruler"]["playhead"]["x"]
		y_top = theme_settings["timeline"]["ruler"]["playhead"]["y"]

		# get a reference to the 2 main canvas objects & theme
		theme = self.project.theme
		canvas_right = self.project.form.TimelineCanvas_Right

		# Add an item to the goocanvas
		root_right = canvas_right.get_root_item ()

		# Load all 3 images
		imgTrack_PlayHead = gtk.image_new_from_file("%s/openshot/themes/%s/play_head.png" % (self.project.form.openshot_path, theme))
		imgTrack_Line = gtk.image_new_from_file("%s/openshot/themes/%s/position_line.png" % (self.project.form.openshot_path, theme))
		imgTrack_Ruler = gtk.image_new_from_file("%s/openshot/themes/%s/ruler_right.png" % (self.project.form.openshot_path, theme))
		imgTrack_Track = gtk.image_new_from_file("%s/openshot/themes/%s/Track_Middle.png" % (self.project.form.openshot_path, theme))

		# Get Height and Width of Images 
		imgTrack_PlayHead_Height = imgTrack_PlayHead.get_pixbuf().get_height()
		imgTrack_PlayHead_Width = imgTrack_PlayHead.get_pixbuf().get_width()
		imgTrack_Ruler_Height = imgTrack_Ruler.get_pixbuf().get_height()
		imgTrack_Track_Height = imgTrack_Track.get_pixbuf().get_height()

		# Get Size of Window (to determine how wide the middle image should be streched)
		Size_Of_Line = len(self.tracks) * imgTrack_Track_Height + (len(self.tracks) * theme_settings["track"]["padding"]) + 2

		# Resize Middle pixbuf
		linePixBuf = imgTrack_Line.get_pixbuf()
		linePixBuf = linePixBuf.scale_simple(1, Size_Of_Line, gtk.gdk.INTERP_NEAREST)

		# Create Group (for the track)
		GroupTrack = goocanvas.Group (parent = root_right)
		self.play_head = GroupTrack

		# Create the red line
		lineRect = goocanvas.Rect(parent = GroupTrack,
				                  x = x,
				                  y = y_top + theme_settings["timeline"]["ruler"]["playhead_line"]["y"],
				                  width = 1,
				                  height = Size_Of_Line,
				                  line_width = theme_settings["timeline"]["ruler"]["playhead_line"]["line_width"],
				                  stroke_color_rgba = theme_settings["timeline"]["ruler"]["playhead_line"]["stroke_color"]
				                  )

		# Create Group (for the extended play line)
		track_canvas_right = self.project.form.MyCanvas
		track_root_right = track_canvas_right.get_root_item ()
		GroupTrack2 = goocanvas.Group (parent = track_root_right)
		self.play_head_line = GroupTrack2

		# Create the red line
		lineRect = goocanvas.Rect(parent = GroupTrack2,
				                  x = x,
				                  y = 0,
				                  width = 1,
				                  height = Size_Of_Line + theme_settings["timeline"]["ruler"]["playhead_line"]["length_offset"],
				                  line_width = theme_settings["timeline"]["ruler"]["playhead_line"]["line_width"],
				                  stroke_color_rgba = theme_settings["timeline"]["ruler"]["playhead_line"]["stroke_color"]
				                  )

		# Add Play Head Image to Group
		image1 = goocanvas.Image (parent = GroupTrack,
				                  pixbuf = imgTrack_PlayHead.get_pixbuf(),
				                  x = x + (imgTrack_PlayHead_Width / 2) * -1,
				                  y = imgTrack_Ruler_Height - imgTrack_PlayHead_Height + y_top - 2)

		GroupTrack3 = goocanvas.Group (parent = track_root_right)
		
		# Connect signals to play head to allow drag and drop
		GroupTrack.connect ("motion_notify_event", self.on_motion_notify_x)
		GroupTrack.connect ("button_press_event", self.on_button_press_x)
		GroupTrack.connect ("button_release_event", self.on_button_release_x)



	def on_motion_notify_x (self, item, target, event):
		"""this method allows the clip to be dragged and dropped on a track"""

		if (event.state & gtk.gdk.BUTTON1_MASK):
			new_x = event.x
			new_y = event.y

			# disable animated playhead
			self.enable_animated_playhead = False

			# get the pixels per second from the parent sequence
			pixels_per_second = self.get_pixels_per_second()

			# get width of playhead
			playhead_width = item.get_bounds().x2 - item.get_bounds().x1
			min_x = (playhead_width / 2) * -1

			# don't allow the clip to slide past the beginning of the canvas
			total_x_diff = new_x - self.drag_x 
			total_y_diff = event.y - self.drag_y
			if (item.get_bounds().x1 + total_x_diff < min_x):
				total_x_diff = min_x - item.get_bounds().x1

			# move clip				
			item.translate (total_x_diff, 0)
			self.play_head_line.translate(total_x_diff, 0)

			# update playhead position
			play_head_position = (item.get_bounds().x1 + (playhead_width / 2)) / pixels_per_second

			# update video frame
			self.update_video(play_head_position)

		return True


	def update_video(self, play_head_position):

		# return to "preview" mode (if in override mode)
		if self.project.form.MyVideo.mode == "override":
			self.project.set_project_modified(is_modified=True, refresh_xml=True)

		# Refresh the MLT XML file
		self.project.RefreshXML()

		# determine new frame number
		frame = self.project.fps() * play_head_position

		# seek to the new frame
		self.project.form.MyVideo.seek(int(frame))


	def move_play_head (self, new_time):
		"""this method allows the play head to be moved to a specific spot on the timeline.  It accepts
		a parameter for the # of seconds to move the playhead to."""

		# move play_head to the top layer
		if self.play_head and new_time != self.play_head_position:

			# keep track of the current play-head position
			self.play_head_position = float(new_time)

			self.play_head.raise_(None)
			self.play_head_line.raise_(None)

			# get the pixels per second from the parent sequence
			pixels_per_second = self.get_pixels_per_second()

			# get width of playhead
			playhead_width = self.play_head.get_bounds().x2 - self.play_head.get_bounds().x1
			min_x = (playhead_width / 2) * -1

			# don't allow the clip to slide past the beginning of the canvas
			total_x_diff = (new_time * pixels_per_second) - (self.play_head.get_bounds().x2 + min_x)

			# animate clip (if needed)
			if self.enable_animated_playhead == True:
				self.play_head.animate(total_x_diff, 0, 1.0, 0.0, False, 100, 4, goocanvas.ANIMATE_FREEZE)
				self.play_head_line.animate(total_x_diff, 0, 1.0, 0.0, False, 100, 4, goocanvas.ANIMATE_FREEZE)

			# move clip
			self.play_head.translate (total_x_diff, 0)
			self.play_head_line.translate (total_x_diff, 0)

			# Get theme settings
			theme_settings = self.project.theme_settings.settings

			# print time of playhead
			milliseconds = ((self.play_head.get_bounds().x1 + (playhead_width / 2)) / pixels_per_second) * 1000
			time = timeline.timeline().get_friendly_time(milliseconds)
			frame = round((time[5] / 1000.0) * self.project.fps())
			self.ruler_time.set_property("text", theme_settings["timeline"]["playhead_text"]["font"] % (time[2], time[3], time[4], frame))


	def on_button_press_x (self, item, target, event):
		""" This method initializes some variables needed for dragging and dropping a clip """

		# enable animated playhead
		self.enable_animated_playhead = True

		# raise the group up to the top level
		item.raise_(None)

		if event.button == 1:

			# set the x and y where the cursor started dragging from
			self.drag_x = event.x
			self.drag_y = event.y

			# change the cursor for the drag n drop operation
			fleur = gtk.gdk.Cursor (gtk.gdk.FLEUR)
			canvas = item.get_canvas ()
			canvas.pointer_grab (item,
						         gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK,
						         fleur,
						         event.time)

			# pause the video
			self.project.form.MyVideo.pause()

		elif event.button == 3:
			# show right click menu
			self.project.form.mnuPlayheadSubMenu1.showmnu(event, self, item)

		return True


	def on_button_release_x (self, item, target, event):

		""" This method drops a clip, and snaps the clip to the nearest valid track """
		# get reference to the canvas, and stop dragging the item
		canvas = item.get_canvas ()
		canvas.pointer_ungrab (item, event.time)

		# enable animated playhead
		self.enable_animated_playhead = True


	def split_images(self, pixbuf, height, max_length):
		""" Because it's not possible to resize an image to an infinate size, we sometimes
		need to split an image into many smaller pieces.  This function takes an image, and
		returns a list of pixbufs to equal the max_length"""

		# how big of chunks do we use (pixels)
		chunk_size = 1000
		image_list = []

		# get a reference to the 2 main canvas objects & theme
		remaining_pixels = max_length

		while remaining_pixels:
			# declare new image
			new_pixbuf = None

			if chunk_size < remaining_pixels:
				# resize the pixbuf
				new_pixbuf = pixbuf.scale_simple(chunk_size, height, gtk.gdk.INTERP_NEAREST)

				# subtract the pixels
				remaining_pixels = remaining_pixels - chunk_size

			else:
				# resize the pixbuf
				new_pixbuf = pixbuf.scale_simple(remaining_pixels, height, gtk.gdk.INTERP_NEAREST)

				# subtract the pixels
				remaining_pixels = 0

			# add image to list
			image_list.append(new_pixbuf)

		# return list of pixbufs
		return image_list


	def resize_image_list(self, image_list, height, new_length):
		""" Because it's not possible to resize an image to an infinate size, we sometimes
		need to split an image into many smaller pieces.  This function takes an image, and
		returns a list of pixbufs to equal the max_length"""

		# create new list
		new_image_list = []

		# get a reference to the 2 main canvas objects & theme
		remaining_pixels = new_length


		# loop through existing pixbufs
		for current_pixbuf in image_list:

			# get width of pixbuf
			pixbuf_width = current_pixbuf.get_width()

			if remaining_pixels == 0:
				pass

			# Is Last Image?
			elif pixbuf_width >= remaining_pixels:

				# resize the pixbuf
				new_pixbuf = current_pixbuf.scale_simple(remaining_pixels, height, gtk.gdk.INTERP_NEAREST)
				new_image_list.append(new_pixbuf)
				remaining_pixels = 0

			else:
				# not the last image
				# subtract the pixels
				new_image_list.append(current_pixbuf)
				remaining_pixels = remaining_pixels - pixbuf_width


		# check for additional pixbufs needed?
		if remaining_pixels > 0:
			# resize the pixbuf
			new_pixbuf = image_list[0].scale_simple(remaining_pixels, height, gtk.gdk.INTERP_NEAREST)

			# add to image list
			new_image_list.append(new_pixbuf)


		# return list of pixbufs
		return new_image_list



	def raise_transitions(self):
		"""this method loops though the children objects of this group looking 
		for the item with a specfic id."""

		# Get root group of the canvas
		canvas_right = self.project.form.MyCanvas
		root_right = canvas_right.get_root_item ()	

		# Build list of canvas IDs
		IDs = {}
		for index in range(0, root_right.get_n_children()):
			child = root_right.get_child(index)
			child_id = child.get_data ("id")

			# add to list
			IDs[str(child_id)] = child


		# loop through each transtion
		for track in self.tracks:
			for trans in track.transitions:

				# see if there is a matching transition
				if trans.unique_id in IDs:
					# raise match to the top layer
					canvas_item = IDs[trans.unique_id]
					canvas_item.raise_(None)

	def raise_play_head(self):
		""" Raise the play-head to the top """
		self.play_head.raise_(None)
		self.play_head_line.raise_(None)

	def get_valid_track(self, x1, y1):
		""" A clip must be dropped on a track.  This method returns the track 
		object that is under the clip's current position """

		# loop through each track
		for track in self.tracks:
			# get the top y and bottom y of each track
			y_top = track.y_top
			y_bottom = track.y_bottom

			# get the middle of the clip
			half_height_of_clip = 0
			middle_position = half_height_of_clip + y1

			# determine if middle of clip is contained inside this track
			if middle_position > y_top and middle_position < y_bottom:
				return track

		# return false if no valid track found
		return None

	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an OpenShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of old clip classes, to make old project files compatable with
		    newer versions of OpenShot. """

		# Check for missing DEBUG attribute (which means it's an old project format)
		if 'enable_animated_playhead' not in state:
			state['enable_animated_playhead'] = False

		# update the state object with new schema changes
		self.__dict__.update(state)


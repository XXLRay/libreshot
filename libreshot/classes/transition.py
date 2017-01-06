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

import os, uuid, locale
import gtk, goocanvas
import time

########################################################################
class transition:
	"""This class represents a media clip on the timeline."""

	#----------------------------------------------------------------------
	def __init__(self, name, position_on_track, length, resource, parent, type="transition", mask_value=50.0):
		"""Constructor"""

		# init variables for clip object
		self.name = name
		self.position_on_track = float(position_on_track)  # the time in seconds where the transition starts on the timeline
		self.length = float(length)		# the length in seconds of this transition
		self.resource = resource		# Any grey-scale image, or leave empty for a dissolve
		self.softness = 0.3				# 0.0 = no softness. 1.0 = too soft.	
		self.reverse = False
		self.unique_id = str(uuid.uuid1())
		self.parent = parent			# the sequence

		# mask settings
		self.type = type				# transition or mask
		self.mask_value = mask_value	# 0.0 to 1.0
		
		# init vars for drag n drop
		self.drag_x = 0.0
		self.drag_y = 0.0

	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an LibreShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of old classes, to make old project files compatable with
		    newer versions of LibreShot. """

		# Check for missing DEBUG attribute (which means it's an old project format)
		if 'drag_x' not in state:
			state['drag_x'] = 0.0
		if 'drag_y' not in state:
			state['drag_y'] = 0.0
			
		# update the state object with new schema changes
		self.__dict__.update(state)
		

	def Render(self, exiting_item=None, x_offset = 0):

		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.parent.project.theme

		# Get theme settings
		theme_settings = self.parent.parent.project.theme_settings.settings

		# init vars
		pixels_per_second = self.parent.parent.get_pixels_per_second()
		x = float(self.position_on_track * pixels_per_second) + x_offset
		width = self.length * pixels_per_second
		height = theme_settings["transition"]["rectangle"]["h"]

		if self.parent:
			# get bottom y of track
			y = self.parent.y_bottom - theme_settings["transition"]["rectangle"]["y"]
		else:
			y = theme_settings["transition"]["rectangle"]["y"]

		# Get root group of the canvas
		canvas_right = self.parent.parent.project.form.MyCanvas
		root_right = canvas_right.get_root_item ()		

		if exiting_item == None:
			# Create the Group (for the clip)
			GroupTransition = goocanvas.Group (parent = root_right)

			# set the unique ID of the group
			GroupTransition.set_data ("id", self.unique_id)

			# Add a translucent blue rectangle
			rec2 = goocanvas.Rect (parent = GroupTransition,
						           x = x,
						           y = y,
						           width = width,
						           height = height,
						           line_width = theme_settings["transition"]["rectangle"]["line_width"],
						           stroke_color_rgba = theme_settings["transition"]["rectangle"]["stroke_color_rgba"],
						           fill_color_rgba = theme_settings["transition"]["rectangle"]["fill_color_rgba"])
			rec2.set_data ("id", "tran_rectangle")

			# add text to the transition
			text1 = goocanvas.Text (parent = GroupTransition,
						            text = theme_settings["transition"]["transition_name_text"]["font"] % self.name,
						            antialias = False,
						            x = x + theme_settings["transition"]["transition_name_text"]["x"],
						            y = y + theme_settings["transition"]["transition_name_text"]["y"],
						            use_markup = True,
						            width = width - 8,
						            ellipsize = 3)
			text1.set_data ("id", "tran_text")

			# hide text (if transition is too small)
			if width <= theme_settings["transition"]["collapse_pixel_threshold_text"]:
				text1.set_properties(visibility = 1)
			else:
				text1.set_properties(visibility = 2)


			# load clip images
			if self.type == "transition":
				# TRANSITIONS
				if self.reverse:
					# DOWN
					imgTrans = gtk.image_new_from_file("%s/libreshot/themes/%s/transition_down.png" % (self.parent.parent.project.form.libreshot_path, theme))
				else:
					# UP
					imgTrans = gtk.image_new_from_file("%s/libreshot/themes/%s/transition_up.png" % (self.parent.parent.project.form.libreshot_path, theme))
			elif self.type == "mask":
				# MASK
				imgTrans = gtk.image_new_from_file("%s/libreshot/themes/%s/transition_mask.png" % (self.parent.parent.project.form.libreshot_path, theme))				

			# create canvas image object
			canvasImageTrans = goocanvas.Image (parent = GroupTransition,
						                        pixbuf = imgTrans.get_pixbuf(),
						                        x = x + theme_settings["transition"]["thumbnail"]["x"],
						                        y = y + theme_settings["transition"]["thumbnail"]["y"])
			canvasImageTrans.lower(text1)
			canvasImageTrans.set_data ("id", "trans_direction")

			# hide up/down image (if transition is too small)
			if width <= theme_settings["transition"]["collapse_pixel_threshold_thumbnail"]:
				canvasImageTrans.set_properties(visibility = 1)
			else:
				canvasImageTrans.set_properties(visibility = 2)


			# connect drag n drop events to the new cavnas group
			GroupTransition.connect ("motion_notify_event", self.on_motion_notify_x)
			GroupTransition.connect ("button_press_event", self.on_button_press_x)
			GroupTransition.connect ("button_release_event", self.on_button_release_x)

		else:
			# get existing item
			GroupTransition = exiting_item

			# get existing object
			rec2 = self.get_canvas_child(GroupTransition, "tran_rectangle")
			text1 = self.get_canvas_child(GroupTransition, "tran_text")
			canvasImageTrans = self.get_canvas_child(GroupTransition, "trans_direction")

			# resize transition
			rec2.set_properties(x = x)
			text1.set_properties(x = x + theme_settings["transition"]["transition_name_text"]["x"])
			canvasImageTrans.set_properties(x = x + theme_settings["transition"]["thumbnail"]["x"])
			rec2.set_properties(width = width)
			text1.set_properties(width = width - theme_settings["transition"]["transition_name_text"]["x"])

			# hide text (if transition is too small)
			if width <= theme_settings["transition"]["collapse_pixel_threshold_text"]:
				text1.set_properties(visibility = 1)
			else:
				text1.set_properties(visibility = 2)

			# hide up/down image (if transition is too small)
			if width <= theme_settings["transition"]["collapse_pixel_threshold_thumbnail"]:
				canvasImageTrans.set_properties(visibility = 1)
			else:
				canvasImageTrans.set_properties(visibility = 2)

		# return the gooCanvas transition object
		return GroupTransition


	def change_direction_image(self, GroupTransition):

		# don't change direction of a mask
		if self.type != "transition":
			return

		# get a reference to the 2 main canvas objects & theme
		theme = self.parent.parent.project.theme

		# get the direction image
		canvasImageTrans = self.get_canvas_child(GroupTransition, "trans_direction")

		if self.reverse:
			# DOWN
			imgTrans = gtk.image_new_from_file("%s/libreshot/themes/%s/transition_down.png" % (self.parent.parent.project.form.libreshot_path, theme))
			canvasImageTrans.set_properties(pixbuf = imgTrans.get_pixbuf())
		else:
			# UP
			imgTrans = gtk.image_new_from_file("%s/libreshot/themes/%s/transition_up.png" % (self.parent.parent.project.form.libreshot_path, theme))
			canvasImageTrans.set_properties(pixbuf = imgTrans.get_pixbuf())


	def get_canvas_child(self, group, requested_child_id):
		"""this method loops though the children objects of this group looking 
		for the item with a specfic id."""

		for index in range(0, group.get_n_children()):
			child = group.get_child(index)
			child_id = child.get_data ("id")

			if child_id == requested_child_id:
				return child

		return None


	def on_button_press_x (self, item, target, event):
		""" This method initializes some variables needed for dragging and dropping a clip """
		# raise the group up to the top level
		item.raise_(None)

		# set the x and y where the cursor started dragging from
		self.drag_x = event.x
		self.drag_y = event.y

		# only respond to the first mouse button
		if event.button == 1:


			# determine what cursor mode is enable (arrow, razor, snap, etc...)
			(isArrow, isRazor, isSnap, isResize) = self.parent.parent.project.form.get_toolbar_options()

			# ARROW MODE
			if isArrow:
				
				if self.parent.parent.project.form._SHIFT:
					# remove transition from goocanvas
					parent = item.get_parent()
					child_num = parent.find_child (item)
					parent.remove_child (child_num)

					# remove transition from parent track
					self.parent.transitions.remove(self)

					# mark project as modified
					self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed transition"))

				else:

					# change the cursor for the drag n drop operation
					fleur = gtk.gdk.Cursor (gtk.gdk.FLEUR)
					canvas = item.get_canvas ()
					canvas.pointer_grab (item, gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK, fleur, event.time)

			# RESIZE MODE
			elif isResize:

				# remember the original length and position before resizing starts
				self.original_length = self.length
				self.original_start_pos = self.position_on_track

			# SNAP MODE
			elif isSnap:
				pass

		elif event.button == 3:

			# show the track popup menu
			self.parent.parent.project.form.mnuTransition1.showmnu(event, self, item)


		return True


	def on_motion_notify_x (self, item, target, event):
		"""this method allows the clip to be dragged and dropped on a track"""	  

		# Get theme settings
		theme_settings = self.parent.parent.project.theme_settings.settings

		# get the new x,y coordinates from the mouse
		new_x = event.x
		new_y = event.y	

		# get the pixels per second from the parent sequence
		pixels_per_second = self.parent.parent.get_pixels_per_second()

		# determine end pixel of sequence
		end_of_timeline = self.parent.parent.length * pixels_per_second

		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.parent.parent.project.form.get_toolbar_options()

		# ARROW MODE
		if isArrow:

			# Move the clip based on the x, y of the mouse
			if (event.state & gtk.gdk.BUTTON1_MASK):

				# don't allow the clip to slide past the beginning of the canvas
				total_x_diff = new_x - self.drag_x 
				total_y_diff = event.y - self.drag_y
				if (item.get_bounds().x1 + total_x_diff < 0):
					total_x_diff = 0 - item.get_bounds().x1
				elif (item.get_bounds().x2 + total_x_diff > end_of_timeline):
					total_x_diff = end_of_timeline - item.get_bounds().x2

				# get the track under this transition (the top track)
				drop_track = self.get_valid_drop(item.get_bounds().x1, item.get_bounds().y1)

				# mark project as modified
				self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)
				

				# Determine CTRL snapping amount (if CTRL key is pressed)
				if not self.parent.parent.project.form._CTRL:
					# move transition
					item.translate (total_x_diff, total_y_diff)
					
				else:
					# CTRL is pressed
					# move transition vertically
					item.translate (0, total_y_diff)


		# RESIZE MODE
		if isResize:

			# update cursor
			self.parent.parent.project.form.current_cursor[1] = int(event.x_root)
			self.parent.parent.project.form.current_cursor[2] = int(event.y_root)
			self.parent.parent.project.form.current_cursor[3] = "clip"

			if (event.state & gtk.gdk.BUTTON1_MASK):

				# get the direction from the cursor object
				direction = self.parent.parent.project.form.current_cursor[0]

				# update transition length text
				text1 = self.get_canvas_child(item, "tran_text")
				text1.set_properties(text = theme_settings["transition"]["transition_name_text"]["font_resize"].replace("|", "\n") % (self.name, locale.format("%.1f", self.length, grouping=False)))


			else:
				# only calculate LEFT or RIGHT when the mouse is not clicked.  Once the user starts resizing
				# a clip, we want to just use the direction in the cursor object.  In other words, we can't allow
				# the direction to change while we are resizing.
				# determine if user is resizing the LEFT or RIGHT side of the clip
				length = float(self.length)

				left_of_clip = self.position_on_track * pixels_per_second
				center_of_clip = left_of_clip + ((length / 2.0) * pixels_per_second)
				right_of_clip = left_of_clip + (length * pixels_per_second)

				direction = "left"
				if event.x_root < center_of_clip:
					direction = "left"
				else:
					direction = "right"

				# if right, update the cursor the "right grab" icon
				if direction == "right":
					# update cursor variable
					if self.parent.parent.project.form.current_cursor[0] != "right":

						# change cursor to "right bar"
						self.parent.parent.project.form.current_cursor[0] = "right"
						self.parent.parent.project.form.MyCanvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)) 

				# if left, update the cursor the "left grab" icon
				if direction == "left":
					# update cursor variable
					if self.parent.parent.project.form.current_cursor[0] != "left":

						# change cursor to "left bar"
						self.parent.parent.project.form.current_cursor[0] = "left" 
						self.parent.parent.project.form.MyCanvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE))


			# Move the clip based on the x, y of the mouse (if the mouse button is pressed)
			if (event.state & gtk.gdk.BUTTON1_MASK):

				# Get side of clip that is being re-sized
				side = self.parent.parent.project.form.current_cursor[0]  # left or right

				# Get the x and y difference
				original_end_pos = (self.original_start_pos * pixels_per_second) + (self.original_length * pixels_per_second)
				x_offset = event.x - event.x_root

				if side == "left":
					# calculate new start position and length
					new_position = float(event.x_root) / float(pixels_per_second)
					new_length = float(original_end_pos - event.x_root) / pixels_per_second
					#new_start_time = self.end_time - new_length

					# update the properties of this clip
					if new_position >= 0 and new_length >= 0:

						# mark project as modified
						self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)

						self.position_on_track = new_position
						self.length = new_length
						#self.start_time = new_start_time

						# adjust x for windows
						if os.name == 'nt':
							x_offset = x_offset - 2

						# re-render this clip to the canvas (passing the canvas group to the RenderClip method)
						self.Render(item, x_offset)

				else:
					# RIGHT side
					# calculate the new clip length
					new_length = (event.x_root - (self.position_on_track * pixels_per_second)) / pixels_per_second
					self.length = new_length

					# update the properties of this clip
					if new_length > 0:

						# mark project as modified
						self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True)

						# re-render this clip to the canvas (passing the canvas group to the RenderClip method)
						self.Render(item, x_offset)

		return True


	def drop_canvas_item(self, item):
		""" Drop the canvas item, and snap and resize it if 'snapping' enabled. """

		# Get theme settings
		theme_settings = self.parent.parent.project.theme_settings.settings

		# raise the play head to the top
		self.parent.parent.play_head.raise_(None)
		self.parent.parent.play_head_line.raise_(None)

		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.parent.parent.project.form.get_toolbar_options()

		if isRazor:
			return None

		if isArrow:
			# get new parent track
			drop_track = self.get_valid_drop(item.get_bounds().x1, item.get_bounds().y1)
			bottom_y = 0
			new_length = 0

			if drop_track == None:
				# keep old parent, if no track found
				drop_track = self.parent

			# get bottom y of track
			bottom_y = drop_track.y_bottom - 20

			# get the pixels per second from the parent sequence
			pixels_per_second = self.parent.parent.get_pixels_per_second()

			# determine the direction of the drag
			if isSnap:
				distance_from_clip = self.get_snap_difference(self, item)
			else:
				distance_from_clip = 0.0

			# update the position 
			new_position_on_track = float(item.get_bounds().x1 + distance_from_clip) / pixels_per_second

			# update the parent (the primary track)
			self.update_parent(drop_track)
			drop_track.reorder_transitions()

			if isSnap:
				# update direction of transition (only in snap mode)
				direction = self.get_direction(self, item)
				if direction == "down":
					self.reverse = True
				else:
					self.reverse = False

				# refresh image
				self.change_direction_image(item)

				# Change length of transition (if snap is enabled)
				track_index = self.parent.parent.tracks.index(self.parent)
				bottom_track = None
				if (track_index + 1) <= (len(self.parent.parent.tracks) - 1):
					bottom_track = self.parent.parent.tracks[track_index + 1]
				
				# get distance from nearby clips (to the Right)
				edges = []
				edge_of_clip = self.get_edge_of_clip(new_position_on_track, "right", self.parent, 10.0)
				if edge_of_clip:
					edges.append(edge_of_clip)
				if bottom_track:
					edge_of_clip = self.get_edge_of_clip(new_position_on_track, "right", bottom_track, 10.0)
					if edge_of_clip:
						edges.append(edge_of_clip)

				# Change length
				if edges:
					if sorted(edges)[0] > new_position_on_track:
						new_length = sorted(edges)[0] - new_position_on_track
	
						if distance_from_clip and self.length != new_length:
							# re-render transition (at correct width)
							self.length = new_length

			# Set the new position
			self.position_on_track = new_position_on_track

			# remove old canvas item
			parent = item.get_parent()
			child_num = parent.find_child (item)
			parent.remove_child (child_num)

			# create new transition canvas item (possibly a bigger size)
			item = self.Render(None, 0)

		# Hide the length label (so it doesn't clutter the timeline)
		text1 = self.get_canvas_child(item, "tran_text")
		text1.set_properties(text = theme_settings["transition"]["transition_name_text"]["font"] % self.name)

		# reset the cursor
		self.parent.parent.project.form.MyCanvas.window.set_cursor(None)

		# check if clip has been really moved or not
		if self.drag_x == item.get_bounds().x1 and self.drag_y == item.get_bounds().y1 and not isResize:
			type_of_event = None
		elif isResize:
			type_of_event = _("Resized transition")
		else:
			type_of_event = _("Moved transition")

		# mark project as modified
		self.parent.parent.project.set_project_modified(is_modified=True, refresh_xml=True, type = type_of_event )


	def on_button_release_x (self, item, target, event):
		""" This method drops a clip, and snaps the clip to the nearest valid track """

		# get reference to the canvas, and stop dragging the item
		canvas = item.get_canvas()
		canvas.pointer_ungrab (item, event.time)

		return self.drop_canvas_item(item)

	def get_valid_drop(self, x1, y1):
		""" A clip must be dropped on a track.  This method returns the track 
		object that is under the clip's current position """

		# loop through each track
		track_counter = 0

		for track in self.parent.parent.tracks:
			# get the top y and bottom y of each track
			y_top = track.y_top
			y_bottom = track.y_bottom

			# increment track counter
			track_counter = track_counter + 1

			# determine if middle of clip is contained inside this track
			if y1 > y_top and y1 < y_bottom and track_counter != len(self.parent.parent.tracks):
				return track

		# return false if no valid track found
		return None


	def update_parent(self, parent_track):
		""" This method updates the x and y settings of the clip in the object model """

		# remove clip from current parent track (if new parent is different)
		if (parent_track != self.parent):
			# remove clip				
			self.parent.transitions.remove(self)

			# add to new parent track
			parent_track.transitions.append(self)
			self.parent = parent_track


	def get_snap_difference(self, clip_object, canvas_item):
		"""Determine the number of pixels to shift this clip to snap to it's 
		closest neighbor clip (if any)"""

		# get the pixels per second from the parent sequence
		pixels_per_second = clip_object.parent.parent.get_pixels_per_second()
		old_x = clip_object.position_on_track * pixels_per_second  # get the old x coordinate of the clip (used to determine direction)

		# get the index of this transition (from the parent collection)
		clip_index = clip_object.parent.transitions.index(clip_object)
		clip_length = clip_object.length * pixels_per_second
		track_index = self.parent.parent.tracks.index(self.parent)
		bottom_track = None
		if (track_index + 1) <= (len(self.parent.parent.tracks) - 1):
			bottom_track = self.parent.parent.tracks[track_index + 1]
		closest_clip = None
		distance_from_clip = 0.0
		distance_from_left_clip = 0.0
		distance_from_playhead = 0.0

		# determine the direction of the drag
		direction = "left"

		# Look on TOP TRACK
		# get distance from nearby clips (to the LEFT)
		nearby_clip_left = self.get_edge_of_clip(canvas_item.get_bounds().x1 / pixels_per_second, "left", self.parent) * pixels_per_second
		distance_from_left_clip = nearby_clip_left - canvas_item.get_bounds().x1

		# check bottom track (if any)
		BOTTOM_distance_from_left_clip = 0.0
		if bottom_track:
			# BOTTOM TRACK
			# get distance from nearby clips (to the LEFT)
			BOTTOM_nearby_clip_left = self.get_edge_of_clip(canvas_item.get_bounds().x1 / pixels_per_second, "left", bottom_track) * pixels_per_second
			BOTTOM_distance_from_left_clip = BOTTOM_nearby_clip_left - canvas_item.get_bounds().x1

		# distance from the play-head
		playhead_time = clip_object.parent.parent.play_head_position
		playhead_pixels = playhead_time * pixels_per_second
		distance_from_playhead = playhead_pixels - canvas_item.get_bounds().x1

		# limit the left /right snapping to 10 pixels
		if distance_from_left_clip > 10 or distance_from_left_clip < -10:
			distance_from_left_clip = 0.0
		if BOTTOM_distance_from_left_clip > 10 or BOTTOM_distance_from_left_clip < -10:
			BOTTOM_distance_from_left_clip = 0.0
		if distance_from_playhead > 10 or distance_from_playhead < -10:
			distance_from_playhead = 0.0

		# determine which direction and what clip to snap to (based on the direction the clip is moving)
		if direction == "left" and distance_from_left_clip != 0:
			distance_from_clip = distance_from_left_clip
			
		if direction == "left" and BOTTOM_distance_from_left_clip != 0:
			distance_from_clip = BOTTOM_distance_from_left_clip
		elif distance_from_left_clip != 0:
			distance_from_clip = distance_from_left_clip
		elif BOTTOM_distance_from_left_clip != 0:
			distance_from_clip = BOTTOM_distance_from_left_clip
		elif distance_from_playhead != 0:
			distance_from_clip = distance_from_playhead

		# return the # of pixesl to snap the clip
		return distance_from_clip


	def get_edge_of_clip(self, current_position, direction, track, threashold=1.0): 
		""" Get the position of the closest edge of a track """

		if direction == "left":
			# loop through clips on track
			edge = 0.0
			for clip in track.clips:
				# get right edge of clip
				next_edge = float(clip.position_on_track)

				# if clip within 1 second distance
				if abs(current_position - next_edge) <= threashold:
					edge = next_edge
					break

			# return right edge
			return edge

		if direction == "right":
			# loop through clips on track
			edge = 0.0
			for clip in track.clips:
				# get right edge of clip
				next_edge = float(clip.position_on_track) + float(clip.length())

				# if clip within 1 second distance 
				if next_edge > current_position and abs(current_position - next_edge) <= threashold:
					edge = next_edge
					break

			# return right edge
			return edge

		# always return something
		return 0.0


	def get_direction(self, clip_object, canvas_item):
		""" Guess the direction of the transition based on the position
		of the surrounding clips. """

		# get the pixels per second from the parent sequence
		pixels_per_second = clip_object.parent.parent.get_pixels_per_second()

		# get the index of this transition (from the parent collection)
		track_index = self.parent.parent.tracks.index(self.parent)
		bottom_track = None
		if (track_index + 1) <= (len(self.parent.parent.tracks) - 1):
			bottom_track = self.parent.parent.tracks[track_index + 1]

		transition_start = self.position_on_track
		transition_end = self.position_on_track + self.length

		# loop through clips on the TOP track
		TOP_left_position = 0.0
		TOP_found = False
		for clip in self.parent.clips:
			# get right edge of clip
			clip_start = float(clip.position_on_track)
			clip_end = float(clip.position_on_track + clip.length())

			# does clip overlap transition
			if (clip_end >= transition_start and clip_end <= transition_end) or (clip_start >= transition_start and clip_start <= transition_end) or (clip_start >= transition_start and clip_end <= transition_end) or (clip_start <= transition_start and clip_end >= transition_end):
				TOP_found = True
				TOP_left_position = clip_start
				break

		# loop through clips on the BOTTOM track
		BOTTOM_left_position = 0.0
		BOTTOM_found = False
		if bottom_track:
			for clip in bottom_track.clips:
				# get right edge of clip
				clip_start = float(clip.position_on_track)
				clip_end = float(clip.position_on_track + clip.length())
	
				# does clip overlap transition
				if (clip_end >= transition_start and clip_end <= transition_end) or (clip_start >= transition_start and clip_start <= transition_end) or (clip_start >= transition_start and clip_end <= transition_end) or (clip_start <= transition_start and clip_end >= transition_end):
					BOTTOM_found = True
					BOTTOM_left_position = clip_start
					break

		if TOP_found == True and BOTTOM_found == True:
			if TOP_left_position <= BOTTOM_left_position:
				return "down"
			else:
				return "up"
		else:
			return None

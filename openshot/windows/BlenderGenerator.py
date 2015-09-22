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

import os, time, uuid, shutil
import gobject, threading, subprocess, re
import gtk
import math
import subprocess
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import preferences, TreeBlender
from classes import project, messagebox, files

# init the foreign language
from language import Language_Init


class frm3dGenerator(SimpleGtkBuilderApp):

	def __init__(self, path="BlenderGenerator.ui", root="frm3dGenerator", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		
		self._ = _
		self.form = form
		self.project = project
		self.unique_folder_name = str(uuid.uuid1())
		self.output_dir = os.path.join(self.project.USER_DIR, "blender")
		self.selected_template = ""
		self.is_rendering = False
		self.my_blender = None
		
		# init blender tree
		self.OSTreeBlender = TreeBlender.OpenShotTree(self.treeTemplates, self.project)
		self.form.OSTreeBlender = self.OSTreeBlender
			
		# show all controls
		self.frm3dGenerator.show_all()
		
		# clear all editing controls
		self.clear_effect_controls()
		
		# clear any temp folders that are older than todays date
		self.clear_temp_files()
		
		# set black background
		self.imgPreviewEventBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		
		# Init dictionary which holds the values to the template parameters
		self.params = {}
		
		# Disable the Render button by default
		self.btnRender.set_sensitive(False)
		self.sliderPreview.set_sensitive(False)
		self.btnRefresh.set_sensitive(False)
		
		# Get a list of all TTF files (i.e. font files) on the users (as fast as possible)
		# computer, so that we can pass these into Blender to set the font.
		self.available_fonts = self.get_font_files()
		
		
	def get_font_files(self):
		""" Get a list of font files on the computer as FAST as possible. """

		# fc-list : file family style
		command = ["fc-list", ":", "file", "family", "style"]
		regexp = re.compile("([^:]*): ?([^:,]*)(,[^:]*)?(:style=([^,]*)(,.*)?)?")

		ttf_raw={}
		
		try:
			process = subprocess.Popen(args=command,stdout=subprocess.PIPE)
			output = str(process.stdout.read())
			
			# wait for process to finish, and then close
			if process.wait() != 0:
				print "There were some errors calling 'fc-list' using subprocess.Popen()"
		except:
			return ttf_raw
			
		output_lines=output.split('\n')
		
		for line in output_lines:
			try:
				filename, family, style = regexp.match(line).group(1, 2, 5)
				
				# get friendly font name
				friendly_name = "%s %s" % (family, style) if style else family
				
				# add font to dictionary
				ttf_raw[friendly_name] = filename
				
			except:
				pass
		
		# sort list
		return ttf_raw


	def on_btnRefresh_clicked(self, widget, *args):
		print "on_btnRefresh_clicked"
		
		# get the frame number
		frame_number = int(self.sliderPreview.get_value())
		
		# Render only the selected frame
		self.Render(frame=frame_number)
		self.sliderPreview.set_value(frame_number)
		
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		
		# close window
		self.request_window_close()
		
	def on_btnRender_clicked(self, widget, *args):
		print "on_btnRender_clicked"
		
		# Disable the Render button, until this Render is finished
		self.btnRender.set_sensitive(False)
		self.sliderPreview.set_sensitive(False)
		self.btnRefresh.set_sensitive(False)
		self.treeTemplates.set_sensitive(False)
		self.is_rendering = True
		
		# Start Render 
		self.Render()
		
		
	def on_sliderPreview_value_changed(self, widget, *args):
		#print "on_sliderPreview_value_changed"
		
		# get the frame number
		frame_number = int(widget.get_value())
		length = int(self.params["end_frame"])
		
		# Get the animation speed (if any)
		if self.params["animation_speed"]:
			# Adjust length (based on animation speed multiplier)
			length *= int(self.params["animation_speed"])

		# Update preview label
		self.lblFrame.set_text("%s/%s" % (frame_number, length))
		
		# Render only the selected frame
		if not self.is_rendering:
			self.Render(frame=frame_number)
		
		
	def on_treeTemplates_button_release_event(self, widget, *args):
		print "on_treeTemplates_button_release_event"
		
		# get correct gettext method
		_ = self._
		
		# get selected effect (if any)
		selected_effect, unique_id = self.get_selected_effect()
		real_effect = self.OSTreeBlender.get_real_effect(service=selected_effect)

		if real_effect:
			
			# get the selected template .blend name
			self.selected_template = real_effect.service
			
			# Clear Effect Edit Controls
			self.clear_effect_controls()
			
			# Assign a new unique id for each template selected
			self.unique_folder_name = str(uuid.uuid1())
			
			# Create a folder (if it does not exist)
			if not os.path.exists(os.path.join(self.output_dir, self.unique_folder_name)):
				os.mkdir(os.path.join(self.output_dir, self.unique_folder_name))
				
			# Enable the Render Button (since an effect is selected)
			self.btnRender.set_sensitive(True)
			self.sliderPreview.set_sensitive(True)
			self.btnRefresh.set_sensitive(True)
			
			# Loop through Params
			param_index = 1
			for param in real_effect.params:
				# is this a hidden param?
				if param.name == "start_frame" or param.name == "end_frame":
					# add value to dictionary
					self.params[param.name] = int(param.default)
					
					# skip to next param without rendering the controls
					continue
				
				# create hbox and label
				hbox = gtk.HBox(False, 0)
				label = gtk.Label("")
				self.sizegroup1.add_widget(label)
				label.set_alignment(0, 0.5)
				hbox.pack_start(label, False, True, 10)
				self.vbox_settings.pack_start(hbox, False, False, 5)
				self.vbox_settings.show_all()
				
				# update label with title
				label.set_text(_(param.title))
				label.set_tooltip_text(_(param.title))

				if param.type == "spinner":
					# add value to dictionary
					self.params[param.name] = float(param.default)
					
					# create spinner
					adj = gtk.Adjustment(float(param.default), float(param.min), float(param.max), 0.01, 0.01, 0.0)
					spinner = gtk.SpinButton(adj, 0.01, 2)
					# connect signal 
					spinner.connect("value-changed", self.effect_spinner_changed, real_effect, param)
					# add to hbox
					hbox.pack_start(spinner, expand=True, fill=True)
					
				elif param.type == "text":
					# add value to dictionary
					self.params[param.name] = param.default
					
					# create spinner
					textbox = gtk.Entry()
					textbox.set_text(param.default)
					# connect signal 
					textbox.connect("changed", self.effect_text_changed, real_effect, param, unique_id)
					# add to hbox
					hbox.pack_start(textbox, expand=True, fill=True)
					
				elif param.type == "multiline":
					# add value to dictionary
					self.params[param.name] = param.default
					
					# create new scrolled window
					scrolled_win = gtk.ScrolledWindow()
					scrolled_win.set_shadow_type("in")
					scrolled_win.set_property("hscrollbar_policy", "automatic")
					scrolled_win.set_property("height-request", 100)
					
					# create buffer
					new_buffer = gtk.TextBuffer()
					new_buffer.set_text(param.default.replace("\\n","\n"))

					# create spinner
					textbox = gtk.TextView()
					textbox.set_buffer(new_buffer)
					#textbox.set_size_request(width=-1, height=75)
					#textbox.set_property("height-request", 100)
					textbox.set_wrap_mode("word")
					
					# connect signal 
					new_buffer.connect("changed", self.effect_multi_text_changed, real_effect, param, unique_id)
					# add to hbox
					scrolled_win.add_with_viewport(textbox)
					hbox.pack_start(scrolled_win, expand=True, fill=True)

				elif param.type == "dropdown":
					# add value to dictionary
					self.params[param.name] = param.default

					# override font dropdown
					if param.name == "fontname":
						param.values = {"Bfont":"Bfont"}
						for k,v in self.available_fonts.items():
							param.values[k] = v
							
					# override files dropdown
					if "project_files" in param.name:
						param.values = {}
						for item in self.project.project_folder.items:
							if isinstance(item, files.OpenShotFile):
								if item.file_type in ("image", "video"):
									(dirName, fileName) = os.path.split(item.name)
									(fileBaseName, fileExtension)=os.path.splitext(fileName)
									
									if fileExtension.lower() not in (".svg"):
										param.values[fileName] = "|".join((item.name, str(item.height), str(item.width), item.file_type, str(item.fps)))

					cboBox = gtk.combo_box_new_text()
					
					# add values
					box_index = 0
					for k,v in sorted(param.values.items()):
						# add dropdown item
						cboBox.append_text(_(k))
						
						# select dropdown (if default)
						if v == param.default:
							cboBox.set_active(box_index)
						box_index = box_index + 1
						
					# connect signal
					cboBox.connect("changed", self.effect_dropdown_changed, real_effect, param)
					# add to hbox
					hbox.pack_start(cboBox, expand=True, fill=True)
					
				elif param.type == "color":
					colorButton = gtk.ColorButton()
					
					# set color
					default_color = gtk.gdk.color_parse(param.default)
					colorButton.set_color(default_color)	
					color = colorButton.get_color()
					
					# adjust gamma values for Blender
					r = math.pow(color.red_float, 2.2)
					g = math.pow(color.green_float, 2.2)
					b = math.pow(color.blue_float, 2.2)
					
					# add value to dictionary
					self.params[param.name] = [r, g, b]

					# connect signal
					colorButton.connect("color-set", self.effect_color_changed, real_effect, param)
					# add to hbox
					hbox.pack_start(colorButton, expand=True, fill=True)
				
				# show all new controls
				hbox.show_all()
				
				# increment param index
				param_index = param_index + 1
				
			# Init preview slider
			self.init_slider_values()
			
	def init_slider_values(self):
		
		# Get current preview slider frame
		preview_frame_number = int(self.sliderPreview.get_value())
		length = int(self.params["end_frame"])
		
		# Get the animation speed (if any)
		if not self.params["animation_speed"]:
			self.params["animation_speed"] = 1
		else:
			# Adjust length (based on animation speed multiplier)
			length *= int(self.params["animation_speed"])

		# Update the preview slider
		preview_adjustment = self.sliderPreview.get_adjustment()
		middle_frame = int(length / 2)
		# Be sure the new 'middle frame' and the current preview frame are not the same
		# This causes the thumbnail to refresh.
		if preview_frame_number == middle_frame:
			middle_frame += 1
		preview_adjustment.set_lower(self.params["start_frame"])
		preview_adjustment.set_upper(length + 10)
		preview_adjustment.set_value(middle_frame)
		self.sliderPreview.set_adjustment(preview_adjustment)
		
		# Update preview label
		self.lblFrame.set_text("%s/%s" % (middle_frame, length))
				
	def effect_dropdown_changed(self, widget, real_effect, param, *args):
		print "effect_dropdown_changed"
		
		# find numeric value of dropdown selection
		dropdown_value = ""
		for k,v in param.values.items():		
			if k == widget.get_active_text():
				dropdown_value = v
				
		# Update the param of the selected effect
		self.params[param.name] = dropdown_value
		
		# Adjust preview slider (if animation speed changes)
		if param.name == "animation_speed":
			self.init_slider_values()
				
	def effect_spinner_changed(self, widget, real_effect, param, *args):
		print "effect_spinner_changed"
		
		# Update the param of the selected effect
		self.params[param.name] = float(widget.get_value())
		
	def effect_text_changed(self, widget, real_effect, param, *args):
		print "effect_text_changed"
		
		# Update the param of the selected effect
		self.params[param.name] = widget.get_text()
		
	def effect_multi_text_changed(self, buffer, real_effect, param, *args):
		print "effect_multi_text_changed"
		
		start, end = buffer.get_bounds()
		updated_text = buffer.get_text(start, end)
		
		# Update the param of the selected effect
		self.params[param.name] = updated_text.replace("\n", "\\n")
		
	def effect_color_changed(self, widget, real_effect, param, *args):
		print "effect_color_changed"
		
		# Get color from color picker
		color = widget.get_color()
		
		# adjust gamma values for Blender
		r = math.pow(color.red_float, 2.2)
		g = math.pow(color.green_float, 2.2)
		b = math.pow(color.blue_float, 2.2)
		
		# add value to dictionary
		self.params[param.name] = [r, g, b]
		
		
	def html_color(self, color):
		'''converts the gtk color into html color code format'''
		return '#%02x%02x%02x' % (color.red/256, color.green/256, color.blue/256)

	def clear_effect_controls(self):
		
		# clear user entered values
		self.params = {}
		
		# Loop through all child hboxes
		for hbox in self.vbox_settings.get_children():
			
			if type(hbox) == gtk.HBox:
				# remove the hbox
				hbox.destroy()
			
		
	def get_selected_effect(self):
		# Get Effect service name
		selection = self.treeTemplates.get_selection()
		rows, selected = selection.get_selected_rows()
		iters = [rows.get_iter(path) for path in selected]
		for iter in iters:
			Name_of_Effect = self.treeTemplates.get_model().get_value(iter, 1)
			Effect_Service = self.treeTemplates.get_model().get_value(iter, 2)
			unique_id = self.treeTemplates.get_model().get_value(iter, 3)
			return Effect_Service, unique_id
		
		# no selected item
		return None, None
	
	
	def get_clip_parameter(self, clip_effect, parameter_name):
		""" Get the actual values that the user has saved for a clip effect paramater """
		for clip_param in clip_effect.paramaters:
			# find the matching param
			if parameter_name in clip_param.keys():
				# update the param
				return clip_param[parameter_name]
			
			
	def get_project_params(self, is_preview=True):
		""" Return a dictionary of project related settings, needed by the Blender python script. """
		project_params = {}
		
		# Append on some project settings
		project_params["fps"] = int(self.project.fps())
		project_params["resolution_x"] = int(self.project.mlt_profile.width())
		project_params["resolution_y"] = int(self.project.mlt_profile.height())
		
		if is_preview:
			project_params["resolution_percentage"] = 50
		else:
			project_params["resolution_percentage"] = 100
		project_params["quality"] = 100
		project_params["file_format"] = "PNG"
		if is_preview:
			# preview mode - use offwhite background (i.e. horizon color)
			project_params["color_mode"] = "RGB"
		else:
			# render mode - transparent background
			project_params["color_mode"] = "RGBA"
		project_params["horizon_color"] = (0.57, 0.57, 0.57)
		project_params["animation"] = True
		project_params["output_path"] = os.path.join(self.output_dir, self.unique_folder_name, self.params["file_name"])

		# return the dictionary
		return project_params
	
	def clear_temp_files(self):
		""" Clear old files that are no longer needed. """
		
		# Loop through all temp folders
		for child_path in os.listdir(self.output_dir):
			# get full child path
			child_path_full = os.path.join(self.output_dir, child_path)
			child_modified_date_in_seconds = os.path.getmtime(child_path_full)
			child_modified_date = time.localtime(child_modified_date_in_seconds)
			todays_date = time.localtime()
			
			# is folder older than today?
			if todays_date.tm_mon != child_modified_date.tm_mon or todays_date.tm_mday != child_modified_date.tm_mday or todays_date.tm_year != child_modified_date.tm_year:
				# remove this folder and any files in it
				self.project.remove_files(child_path_full)
				os.removedirs(child_path_full)
			
		# create blender folder (if it doesn't exist)
		if os.path.exists(self.output_dir) == False:
			# create new thumbnail folder
			os.mkdir(self.output_dir)
				
				
	def inject_params(self, path, frame=None):
		# determine if this is 'preview' mode?
		is_preview = False
		if frame:
			# if a frame is passed in, we are in preview mode.
			# This is used to turn the background color to off-white... instead of transparent
			is_preview = True
		
		# prepare string to inject
		user_params = "\n#BEGIN INJECTING PARAMS\n"
		for k,v in self.params.items():
			if type(v) == int or type(v) == float or type(v) == list or type(v) == bool:
				user_params += "params['%s'] = %s\n" % (k,v)
			if type(v) == str or type(v) == unicode:
				user_params += "params['%s'] = '%s'\n" % (k, v.replace("'", r"\'"))

		for k,v in self.get_project_params(is_preview).items():
			if type(v) == int or type(v) == float or type(v) == list or type(v) == bool:
				user_params += "params['%s'] = %s\n" % (k,v)
			if type(v) == str or type(v) == unicode:
				user_params += "params['%s'] = '%s'\n" % (k, v.replace("'", r"\'"))
		user_params += "#END INJECTING PARAMS\n"
		
		# Force the Frame to 1 frame (for previewing)
		if frame:
			user_params += "\n\n#ONLY RENDER 1 FRAME FOR PREVIEW\n"
			user_params += "params['%s'] = %s\n" % ("start_frame", frame)
			user_params += "params['%s'] = %s\n" % ("end_frame", frame)
			user_params += "\n\n#END ONLY RENDER 1 FRAME FOR PREVIEW\n"
		
		# Open new temp .py file, and inject the user parameters
		f = open(path, 'r')
		script_body = f.read()
		f.close()
		
		# modify script variable
		script_body = script_body.replace("#INJECT_PARAMS_HERE", user_params)
		
		# Write update script
		f = open(path, 'w')
		f.write(script_body)
		f.close()
		
	def update_progress_bar(self, current_frame, current_part, max_parts):

		# update label and preview slider
		self.sliderPreview.set_value(float(current_frame))
		
		# determine length of image sequence
		length = int(self.params["end_frame"])
		
		# Get the animation speed (if any)
		if self.params["animation_speed"]:
			# Adjust length (based on animation speed multiplier)
			length *= int(self.params["animation_speed"])
		
		# calculate the current percentage, and update the progress bar
		progress = float(float(current_frame) / float(length))
		self.progressRender.set_fraction(progress)
		
		
	def on_imgPreview_size_allocate(self, widget, rectangle, *args):
		#print "on_imgPreview_size_allocate"
		
		# record the size of the gtkImage
		self.image_width = rectangle.width
		self.image_height = rectangle.height
		
	def update_image(self, image_path):
		print "update_image: %s" % image_path

		# get the pixbuf
		pbThumb = gtk.gdk.pixbuf_new_from_file(image_path)
		
		# get size of real image
		real_width = pbThumb.get_width()
		real_height = pbThumb.get_height()
		ratio = float(real_width) / float(real_height)

		# resize thumbnail
		pbThumb = pbThumb.scale_simple(int(self.image_height * ratio), int(self.image_height), gtk.gdk.INTERP_BILINEAR)

		# update image
		self.imgPreview.set_from_pixbuf(pbThumb)
		
		
	def render_finished(self):
		print "render_finished"
				
		# Enable the Render button again
		self.btnRender.set_sensitive(True)
		
		# Add Clip to Project (i.e. as an image sequence)
		self.add_clip()
		
		# close window
		self.request_window_close()
		
	def on_frm3dGenerator_close(self, widget, *args):
		print "on_frm3dGenerator_close"

		# close window
		self.request_window_close()
		
	def on_frm3dGenerator_destroy(self, widget, *args):
		print "on_frm3dGenerator_destroy"
		
		# close window
		self.request_window_close()
		
			
	def request_window_close(self):
		
		# stop thread
		if self.my_blender:
			if self.my_blender.is_running:
				# kill any running blender render thread
				self.my_blender.kill()
			else:
				# thread has already stopped... just close window
				self.close_window()
		else:
			# thread has already stopped... just close window
			self.close_window()
			
	def close_window(self):
			
		# close window
		self.frm3dGenerator.destroy()
		
		
	def error_with_blender(self, version=None, command_output=None):
		""" Show a friendly error message regarding the blender executable or version. """
		_ = self._
		
		version_message = ""
		if version:
			version_message = _("\n\nVersion Detected:\n%s") % version
			
		if command_output:
			version_message = _("\n\nError Output:\n%s") % command_output
		
		# show error message
		blender_version = "2.62"
		messagebox.show(_("Blender Error"), _("Blender, the free open source 3D content creation suite is required for this action (http://www.blender.org).\n\nPlease check the preferences in OpenShot and be sure the Blender executable is correct.  This setting should be the path of the 'blender' executable on your computer.  Also, please be sure that it is pointing to Blender version %s or greater.\n\nBlender Path:\n%s%s") % (blender_version, self.form.settings.general["blender_command"], version_message))

		# Enable the Render button again
		self.btnRender.set_sensitive(True)

	
	def add_clip(self):
		""" Add this image sequence to the current project, and copy the images into the
		current project folder. """
		
		# get reference to translation method
		_ = self._
		
		# Create the target folder (in the project folder)
		target_folder = os.path.join(self.project.folder, self.unique_folder_name)
		if not os.path.exists(target_folder):
			os.mkdir(target_folder)
			
		# Loop through all images, and add to this new folder
		first_image = None
		for child_path in os.listdir(os.path.join(self.output_dir, self.unique_folder_name)):
			# get full child path
			child_source_full = os.path.join(self.output_dir, self.unique_folder_name, child_path)
			child_target_full = os.path.join(target_folder, child_path)
			
			if not first_image and ".png" in child_target_full:
				# remember first image in the sequence
				first_image = child_target_full
			
			# copy image into target folder
			shutil.copy(child_source_full, child_target_full)
			
		# determine length of image sequence
		length = int(self.params["end_frame"])
		
		# Get the animation speed (if any)
		if self.params["animation_speed"]:
			# Adjust length (based on animation speed multiplier)
			length *= int(self.params["animation_speed"])
			
		# add file to current project
		f = self.project.thumbnailer.GetFile(first_image)
		if f:
			self.project.project_folder.items.append(f)
			
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added file"))

		# Update the file properties (since it's added as an image)
		# We need to make it look like a video
		f.label = _("Image Sequence")
		f.fps = self.project.fps()
		f.max_frames = length
		f.ttl = 1.0
		f.length = (float(f.max_frames) / float(f.fps)) - 0.01	# Subtract a 10th of a second, to prevent rounding errors
		f.file_type = "image sequence"
		f.name = os.path.join(target_folder, self.params["file_name"] + r"%04d.png")

		# refresh the main form
		self.form.refresh()
		
				
	def Render(self, frame=None):
		""" Render an images sequence of the current template using Blender 2.62+ and the
		Blender Python API. """
		
		# change cursor to "please wait"
		self.frm3dGenerator.window.set_cursor(gtk.gdk.Cursor(150))

		blend_file_path = os.path.join(self.project.BLENDER_DIR, "blend", self.selected_template)
		source_script = os.path.join(self.project.BLENDER_DIR, "scripts", self.selected_template.replace(".blend", ".py"))
		target_script = os.path.join(self.output_dir, self.unique_folder_name, self.selected_template.replace(".blend", ".py"))

		# Copy the .py script associated with this template to the temp folder.  This will allow
		# OpenShot to inject the user-entered params into the Python script.
		shutil.copy(source_script, target_script)
		
		# Open new temp .py file, and inject the user parameters
		self.inject_params(target_script, frame)
		
		# Create new thread to launch the Blender executable (and read the output)
		self.my_blender = None
		if frame:
			# preview mode 
			self.my_blender = BlenderCommand(self, blend_file_path, target_script, True)
		else:
			# render mode
			self.my_blender = BlenderCommand(self, blend_file_path, target_script, False)
			
		# Start blender thread
		self.my_blender.start()
		
		print "Done with Render() method"
		
		

class BlenderCommand(threading.Thread):
	def __init__(self, frm3dGenerator, blend_file_path, target_script, preview_mode=False):
		# Init regex expression used to determine blender's render progress
		
		# get the blender executable path
		self.blender_exec_path = frm3dGenerator.form.settings.general["blender_command"]
		self.blender_frame_expression = re.compile(r"Fra:([0-9,]*).*Mem:(.*?) .*Part ([0-9,]*)-([0-9,]*)")
		self.blender_saved_expression = re.compile(r"Saved: (.*?) Time: (.*)")
		self.blender_version = re.compile(r"Blender (.*?) ")
		self.blend_file_path = blend_file_path
		self.target_script = target_script
		self.frm3dGenerator = frm3dGenerator
		self.preview_mode = preview_mode
		self.frame_detected = False
		self.version = None
		self.command_output = ""
		self.process = None
		self.is_running = True
		
		# base class constructor
		threading.Thread.__init__(self)
		
	def kill(self):
		""" Kill the running process, if any """
		
		self.is_running = False

		if self.process:
			# kill
			self.process.kill()
		else:
			# close window if thread was killed
			gobject.idle_add(self.frm3dGenerator.close_window)
		

	def run(self):

		try:
			# Shell the blender command to create the image sequence
			command_get_version = [self.blender_exec_path, '-v']
			command_render = [self.blender_exec_path, '-b', self.blend_file_path , '-P', self.target_script]
			self.process = subprocess.Popen(command_get_version, stdout=subprocess.PIPE)
			
			# Check the version of Blender
			self.version = self.blender_version.findall(self.process.stdout.readline())

			if self.version:
				if float(self.version[0]) < 2.62:
					# change cursor to "default" and stop running blender command
					gobject.idle_add(self.frm3dGenerator.frm3dGenerator.window.set_cursor, None)
					self.is_running = False
					
					# Wrong version of Blender.  Must be 2.62+:
					gobject.idle_add(self.frm3dGenerator.error_with_blender, float(self.version[0]))
					return
			
			# debug info
			print "Blender command: %s %s '%s' %s '%s'" % (command_render[0], command_render[1], command_render[2], command_render[3], command_render[4])
			
			# Run real command to render Blender project
			self.process = subprocess.Popen(command_render, stdout=subprocess.PIPE)
			
		except:
			# Error running command.  Most likely the blender executable path in the settings
			# is not correct, or is not the correct version of Blender (i.e. 2.62+)
			
			# change cursor to "default" and stop running blender command
			gobject.idle_add(self.frm3dGenerator.frm3dGenerator.window.set_cursor, None)
			self.is_running = False
			
			gobject.idle_add(self.frm3dGenerator.error_with_blender)
			return

		while self.is_running:

			# Look for progress info in the Blender Output
			line = self.process.stdout.readline()
			self.command_output = self.command_output + line + "\n"	# append all output into a variable
			output_frame = self.blender_frame_expression.findall(line)

			# Does it have a match?
			if output_frame:
				# Yes, we have a match
				self.frame_detected = True
				current_frame = output_frame[0][0]
				memory = output_frame[0][1]
				current_part = output_frame[0][2]
				max_parts = output_frame[0][3]
				
				# Update progress bar
				if not self.preview_mode:
					# only update progress if in 'render' mode
					gobject.idle_add(self.frm3dGenerator.update_progress_bar, current_frame, current_part, max_parts)
				
			# Look for progress info in the Blender Output
			output_saved = self.blender_saved_expression.findall(line)

			# Does it have a match?
			if output_saved:
				# Yes, we have a match
				self.frame_detected = True
				image_path = output_saved[0][0]
				time_saved = output_saved[0][1]
				
				# Update preview image
				gobject.idle_add(self.frm3dGenerator.update_image, image_path)
			
			# Are we done? Should we exit the loop?	
			if line == '' and self.process.poll() != None:
				break

				
		# change cursor to "default"
		gobject.idle_add(self.frm3dGenerator.frm3dGenerator.window.set_cursor, None)

		# Check if NO FRAMES are detected
		if not self.frame_detected:
			# Show Error that no frames are detected.  This is likely caused by
			# the wrong command being executed... or an error in Blender.
			print "No frame was found in the output from Blender"
			gobject.idle_add(self.frm3dGenerator.error_with_blender, None, _("No frame was found in the output from Blender"))
		
		# Done with render (i.e. close window)
		elif not self.preview_mode:
			# only close window if in 'render' mode
			gobject.idle_add(self.frm3dGenerator.render_finished)
			
		# Thread finished
		print "Blender render thread finished"
		if self.is_running == False:
			# close window if thread was killed
			gobject.idle_add(self.frm3dGenerator.close_window)
			
		# mark thread as finished
		self.is_running = False

		
			
def main():
	frm_add_files = frm3dGenerator()
	frm_add_files.run()

if __name__ == "__main__":
	main()

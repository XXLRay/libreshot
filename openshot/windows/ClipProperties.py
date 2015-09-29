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


import os,copy,time, gobject
import gtk
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from classes import profiles, project, video
from windows import preferences
import AddEffect, TreeEffects

# init the foreign language
from language import Language_Init

class frmClipProperties(SimpleGtkBuilderApp):

	def __init__(self, path="ClipProperties.ui", root="frmClipProperties", domain="OpenShot", form=None, project=None, current_clip=None, current_clip_item=None, initial_tab=0, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.form = form
		self.project = project
		self.current_clip = current_clip
		self.current_clip_item = current_clip_item
		self.restore_window_size()
		self.frmClipProperties.show_all()

		# Stop the video thread consumer
		self.form.MyVideo.pause()
		self.form.MyVideo.consumer_stop()
		# Force SDL to write on our drawing area
		os.putenv('SDL_WINDOWID', str(self.previewscreen.window.xid))
		gtk.gdk.flush()
		
		# make a copy of the current clip (for preview reasons)
		self.copy_of_clip = copy.copy(self.current_clip)
		self.copy_of_clip.keyframes = copy.deepcopy(self.current_clip.keyframes)
		self.copy_of_clip.effects = copy.deepcopy(self.current_clip.effects)
		self.copy_of_clip.position_on_track = 0

		# add items to direction combo
		options = ["16x", "15x", "14x", "13x", "12x", "11x", "10x", "9x", "8x", "7x", "6x", "5x", "4x", "3x", "2x", _("Normal Speed"), "1/2", "1/3", "1/4", "1/5", "1/6", "1/7", "1/8", "1/9", "1/10", "1/11", "1/12", "1/13", "1/14", "1/15", "1/16" ]
		# loop through export to options
		for option in options:
			# append profile to list
			self.cboSimpleSpeed.append_text(option)
			
		# add items to direction combo
		options = [_("Forward"), _("Reverse")]
		# loop through export to options
		for option in options:
			# append profile to list
			self.cboDirection.append_text(option)
			
		# add items to direction combo
		options = [_("Start of Clip"), _("End of Clip")]
		# loop through export to options
		for option in options:
			# append profile to list
			self.cboKeyFrame.append_text(option)
		
		# get file name
		(dirName, fname) = os.path.split(self.current_clip.file_object.name)
		
		# get a local keyframe collection
		self.keyframes = copy.deepcopy(self.current_clip.keyframes)
		self.current_keyframe = ""
		
		# init the default properties
		self.txtFileName.set_text(fname)
		self.spinbtnStart.set_value(self.current_clip.position_on_track)
		self.txtLength.set_text(_("{0} seconds").format(str(self.current_clip.length())))
		self.txtOut.set_value(round(self.current_clip.end_time, 2))
		self.txtIn.set_value(round(self.current_clip.start_time, 2))
		self.txtAudioFadeInAmount.set_value(round(self.current_clip.audio_fade_in_amount, 2))
		self.txtAudioFadeOutAmount.set_value(round(self.current_clip.audio_fade_out_amount, 2))
		self.txtVideoFadeInAmount.set_value(round(self.current_clip.video_fade_in_amount, 2))
		self.txtVideoFadeOutAmount.set_value(round(self.current_clip.video_fade_out_amount, 2))
		self.txtRotate.set_value(round(self.current_clip.rotation, 2))
		self.sliderVolume.set_value(self.current_clip.volume)
		self.chkFill.set_active(self.current_clip.fill)
		self.chkEffectsApplyAll.set_active(False)
		
		if self.current_clip.distort:
			self.chkMaintainAspect.set_active(False)
		else:
			self.chkMaintainAspect.set_active(True)
			
		self.chkVideoFadeIn.set_active(self.current_clip.video_fade_in)
		self.chkVideoFadeOut.set_active(self.current_clip.video_fade_out)
		self.chkAudioFadeIn.set_active(self.current_clip.audio_fade_in)
		self.chkAudioFadeOut.set_active(self.current_clip.audio_fade_out)
		
		self.spinAdvancedSpeed.set_value(self.current_clip.speed)
		self.set_horizontal_align_dropdown()
		self.set_vertical_align_dropdown()
		self.chkEnableVideo.set_active(self.current_clip.play_video)
		self.chkEnableAudio.set_active(self.current_clip.play_audio)
		self.set_direction_dropdown()
		self.set_keyframe_dropdown()
		self.set_speed_dropdown()
		
		# Hide the speed tab, if this is an image
		if self.current_clip.file_object.file_type == "video":
			# Speed only works for videos.  Image Sequences, audio, and images break with this setting.
			# So, we only show this setting for videos.
			self.vboxSpeed.set_property('visible', True)
		else:
			self.vboxSpeed.set_property('visible', False)
		
		# update effects tree
		self.OSTreeEffects = TreeEffects.OpenShotTree(self.treeEffects, self.project)
		self.update_effects_tree()

		# Refresh XML
		self.RefreshPreview()

		# start and stop the video
		#self.form.MyVideo.play()
		#self.form.MyVideo.pause()
		
		# set the initial tab
		self.notebook1.set_current_page(initial_tab)
		
		# mark project as modified
		# so that the real project is refreshed... even if these
		# preview changes are not accepted
		self.project.set_project_modified(is_modified=True, refresh_xml=True)

		
	def restore_window_size(self):
		#default the form as not maximized
		self.is_maximized = False
		
		#load the window settings
		self.settings = preferences.Settings(self.project)
		self.settings.load_settings_from_xml()
			
		#get the app state settings
		self.width = int(self.settings.app_state["clip_property_window_width"])
		self.height = int(self.settings.app_state["clip_property_window_height"])
		is_max = self.settings.app_state["clip_property_window_maximized"]
		
		#resize window		
		self.frmClipProperties.resize(self.width, self.height)
		
		#maximize window if needed
		if is_max == "True":
			self.frmClipProperties.maximize()
		
		#set pane size from config xml
		self.hpaned1.set_position(int(self.settings.app_state["clip_property_hpane_position"]))
		
	def on_treeEffects_button_release_event(self, widget, *args):
		print "on_treeEffects_button_release_event"
		
		# get correct gettext method
		_ = self._
		
		# get selected effect (if any)
		selected_effect, unique_id = self.get_selected_effect()
		real_effect = self.OSTreeEffects.get_real_effect(service=selected_effect)
		clip_effect = self.get_clip_effect(unique_id)
		
		if real_effect:
			# show the settings panel
			self.vbox_effect_settings.set_property('visible', True)
			
			# Clear Effect Edit Controls
			self.clear_effect_controls()
			
			# Loop through Params
			param_index = 1
			for param in real_effect.params:
				# get hbox
				hbox = self.vbox_effect_settings.get_children()[param_index]
				label = hbox.get_children()[0]
				self.sizegroup1.add_widget(label)
				
				# Get actual value for param
				user_param_value = self.get_clip_parameter(clip_effect, param.name)
				
				# update label with title
				label.set_text(_(param.title))
				label.set_tooltip_text(_(param.title))

				if param.type == "spinner":
					# create spinner
					adj = gtk.Adjustment(float(user_param_value), float(param.min), float(param.max), float(param.step), float(param.step), 0.0)
					spinner = gtk.SpinButton(adj, float(param.step), int(param.digits))
					# connect signal
					spinner.connect("value-changed", self.effect_spinner_changed, real_effect, param, unique_id)
					# add to hbox
					hbox.pack_start(spinner, expand=True, fill=True)
					
				elif param.type == "hscale":
					# create hscale
					adj = gtk.Adjustment(float(user_param_value), float(param.min), float(param.max), float(param.step), float(param.step), 0.0)
					hscale = gtk.HScale(adj)
					hscale.set_digits(int(param.digits))
					# connect signal
					hscale.connect("value-changed", self.effect_hscale_changed, real_effect, param, unique_id)
					# add to hbox
					hbox.pack_start(hscale, expand=True, fill=True)
				
				elif param.type == "dropdown":
					cboBox = gtk.combo_box_new_text()
					
					# add values
					box_index = 0
					for k,v in param.values.items():
						# add dropdown item
						cboBox.append_text(k)
						
						# select dropdown (if default)
						if v == user_param_value:
							cboBox.set_active(box_index)
						box_index = box_index + 1
						
					# connect signal
					cboBox.connect("changed", self.effect_dropdown_changed, real_effect, param, unique_id)
					# add to hbox
					hbox.pack_start(cboBox, expand=True, fill=True)
					
				elif param.type == "color":
					colorButton = gtk.ColorButton()
					# set color
					default_color = gtk.gdk.color_parse(user_param_value)
					colorButton.set_color(default_color)	

					# connect signal
					colorButton.connect("color-set", self.effect_color_changed, real_effect, param, unique_id)
					# add to hbox
					hbox.pack_start(colorButton, expand=True, fill=True)
				
				# show all new controls
				hbox.show_all()
				
				# increment param index
				param_index = param_index + 1
				
	def get_clip_effect(self, unique_id):
		""" find the effect object on the clip... that matches the service string. """
		# Loop through all effects
		for clip_effect in self.copy_of_clip.effects:
			if clip_effect.unique_id == unique_id:
				# Found clip effect... now we need to find the actual param to update
				return clip_effect
			
	def get_clip_parameter(self, clip_effect, parameter_name):
		""" Get the actual values that the user has saved for a clip effect paramater """
		for clip_param in clip_effect.paramaters:
			# find the matching param
			if parameter_name in clip_param.keys():
				# update the param
				return clip_param[parameter_name]
				
				
	def effect_spinner_changed(self, widget, real_effect, param, unique_id, *args):
		print "effect_spinner_changed"
		
		# Update the param of the selected effect
		for clip_effect in self.copy_of_clip.effects:
			if clip_effect.unique_id == unique_id:
				# Found clip effect... now we need to find the actual param to update
				for clip_param in clip_effect.paramaters:
					# find the matching param
					if param.name in clip_param.keys():
						# update the param
						clip_param[param.name] = str(widget.get_value())
						return
					
	def effect_hscale_changed(self, widget, real_effect, param, unique_id, *args):
		print "effect_hscale_changed"
		
		# Update the param of the selected effect
		for clip_effect in self.copy_of_clip.effects:
			if clip_effect.unique_id == unique_id:
				# Found clip effect... now we need to find the actual param to update
				for clip_param in clip_effect.paramaters:
					# find the matching param
					if param.name in clip_param.keys():
						# update the param
						print widget.get_value()
						clip_param[param.name] = str(widget.get_value())
						return
		
	def effect_dropdown_changed(self, widget, real_effect, param, unique_id, *args):
		print "effect_dropdown_changed"
		
		# find numeric value of dropdown selection
		dropdown_value = ""
		for k,v in param.values.items():		
			if k == widget.get_active_text():
				dropdown_value = v
		
		# Update the param of the selected effect
		for clip_effect in self.copy_of_clip.effects:
			if clip_effect.unique_id == unique_id:
				# Found clip effect... now we need to find the actual param to update
				for clip_param in clip_effect.paramaters:
					# find the matching param
					if param.name in clip_param.keys():
						# update the param
						clip_param[param.name] = dropdown_value
						return
		
	def effect_color_changed(self, widget, real_effect, param, unique_id, *args):
		print "effect_color_changed"
		
		# Get color from color picker
		color = widget.get_color()

		# Update the param of the selected effect
		for clip_effect in self.copy_of_clip.effects:
			if clip_effect.unique_id == unique_id:
				# Found clip effect... now we need to find the actual param to update
				for clip_param in clip_effect.paramaters:
					# find the matching param
					if param.name in clip_param.keys():
						# update the param
						clip_param[param.name] = self.html_color(color)
						return
					
	def html_color(self, color):
		'''converts the gtk color into html color code format'''
		return '#%02x%02x%02x' % (color.red/256, color.green/256, color.blue/256)
			
	def clear_effect_controls(self):
		
		# Loop through all child hboxes
		child_index = 0
		for hbox in self.vbox_effect_settings.get_children():
			
			if child_index > 0:
				# get Label
				label = hbox.get_children()[0]
				label.set_text("")
				
				# remove input control (if any)
				if len(hbox.get_children()) > 1:
					# remove the item
					hbox.remove(hbox.get_children()[1])
					
			# increment child index
			child_index = child_index + 1
	
	def update_effects_tree(self):
	
		# get the selection
		selection = self.treeEffects.get_selection()
		(model, paths) = selection.get_selected_rows()
		if len(paths) == 1:
			# save the selected path for later
			path = paths[0]
	
		# Populate effects tree again
		self.OSTreeEffects.populate_tree(self.copy_of_clip.effects)
		
		# hide settings if no effects found
		#if not self.copy_of_clip.effects:
		#	self.vbox_effect_settings.set_property('visible', False)
		#else:
		# select last effect
		if len(paths) == 1:
			# select the path that was selected before the tree was repopulated
			selection = self.treeEffects.get_selection()
			selection.select_path(path)
			
		# call click event for the tree
		self.on_treeEffects_button_release_event(self.treeEffects)
		
		

	def get_selected_effect(self):
		# Get Effect service name
		selection = self.treeEffects.get_selection()
		rows, selected = selection.get_selected_rows()
		iters = [rows.get_iter(path) for path in selected]
		for iter in iters:
			Name_of_Effect = self.treeEffects.get_model().get_value(iter, 1)
			Effect_Service = self.treeEffects.get_model().get_value(iter, 2)
			unique_id = self.treeEffects.get_model().get_value(iter, 3)
			return Effect_Service, unique_id
		
		# no selected item
		return None, None
	
		
	def on_frmClipProperties_window_state_event(self, widget, event, *args):
		# determine if properties window is maximized or not
		
		if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
			if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
				# maximized
				self.is_maximized = True
			else:
				# not maximized
				self.is_maximized = False
				
		# refresh sdl on window resize
		if self.form.MyVideo:
			self.form.MyVideo.refresh_sdl()

		
	def on_frmClipProperties_destroy(self, widget, *args):
		#print "on_frmClipProperties_destroy"
		#get the property window size
		self.settings.app_state["clip_property_window_maximized"] = str(self.is_maximized)
		self.settings.app_state["clip_property_window_width"] = self.width
		self.settings.app_state["clip_property_window_height"] = self.height
		self.settings.app_state["clip_property_hpane_position"] = self.hpaned1.get_position()
		
		#save the settings
		self.settings.save_settings_to_xml()
		
		
	def on_frmClipProperties_close(self, widget, *args):
		print "on_frmClipProperties_close"
		
		# close the window
		self.close_window()
		
		return True
	
	def on_frmClipProperties_configure_event(self, widget, *args):
		print "on_frmClipProperties_configure_event"
		
		#handles the resize event of the window
		#set the new width and height from the window resize
		(self.width, self.height) = self.frmClipProperties.get_size()	

		# refresh sdl on window resize
		if self.form.MyVideo:
			self.form.MyVideo.refresh_sdl()
		
		
	def on_btnAddEffect_clicked(self, widget, *args):
		#print "on_btnAddEffect_clicked"
		
		# show frmExportVideo dialog
		self.frmAddEffect = AddEffect.frmAddEffect(parent=self, form=self.form, project=self.project)
		

	def on_btnRemoveEffect_clicked(self, widget, *args):
		print "on_btnRemoveEffect_clicked"
		
		# Get selected effect
		selected_service, unique_id = self.get_selected_effect()
		if selected_service:
			# Remove effect
			self.copy_of_clip.Remove_Effect(unique_id)
			
			# clear effect controls
			self.clear_effect_controls()
		
			# update effect tree
			self.update_effects_tree()
			
			# hide settings if no effects found
			if not self.copy_of_clip.effects:
				self.vbox_effect_settings.set_property("visible", False)
		
		
	def on_btnEffectUp_clicked(self, widget, *args):
		print "on_btnEffectUp_clicked"
		
		# Get selected effect
		selected_service, unique_id = self.get_selected_effect()
		if selected_service:
			# Move Effect
			self.copy_of_clip.Move_Effect(unique_id, "up")
			
			# Move the selection one step up
			self.move_tree_selection(-1)
			
			# clear effect controls
			self.clear_effect_controls()
			
			# update effect tree
			self.update_effects_tree()

	
	def on_btnEffectDown_clicked(self, widget, *args):
		print "on_btnEffectDown_clicked"
		
		# Get selected effect
		selected_service, unique_id = self.get_selected_effect()
		if selected_service:
			# Move Effect
			self.copy_of_clip.Move_Effect(unique_id, "down")
			
			# Move the selection one step down
			self.move_tree_selection(1)
			
			# clear effect controls
			self.clear_effect_controls()
			
			# update effect tree
			self.update_effects_tree()
			

	def move_tree_selection(self, number_of_rows):
		"""
		moves the selection in the treeview some rows, and stops at the edges
		if the selection gets out of bounds (if sel < 0 or sel > len - 1).
		number_of_rows: The number of rows to move (positive direction down)
		"""
	
		# get the selection
		selection = self.treeEffects.get_selection()
		(model, paths) = selection.get_selected_rows()
		
		# set y to the selected row index
		(y,) = paths[0]
		
		# change the value of y
		y += number_of_rows
		
		# make sure it doesn't get outside bounds
		if y < 0:
			y = 0
		last_effect_index = len(self.copy_of_clip.effects) - 1
		if y > last_effect_index:
			y = last_effect_index
		
		# select the new row index
		selection.select_path((y,))
	

	def on_btnResetVolume_clicked(self, widget, *args):
		print "on_btnResetVolume_clicked"
		
		# reset the speed to 1.0
		self.sliderVolume.set_value(100)		

	def on_txtHeight_value_changed(self, widget, *args):
		print "on_txtHeight_value_changed"
		
		# update property
		self.keyframes[self.current_keyframe].height = self.txtHeight.get_value()
		
	def on_txtWidth_value_changed(self, widget, *args):
		print "on_txtWidth_value_changed"
		
		# update property
		self.keyframes[self.current_keyframe].width = self.txtWidth.get_value()
		
	def on_txtX_value_changed(self, widget, *args):
		print "on_txtX_value_changed"
		
		# update property
		self.keyframes[self.current_keyframe].x = self.txtX.get_value()
		
	def on_txtY_value_changed(self, widget, *args):
		print "on_txtY_value_changed"
		
		# update property
		self.keyframes[self.current_keyframe].y = self.txtY.get_value()
		
	def on_txtAlpha_value_changed(self, widget, *args):
		print "on_txtAlpha_value_changed"
		
		# update property
		self.keyframes[self.current_keyframe].alpha = float(self.scaleAlpha.get_value()) / 100.0
		

	def on_cboKeyFrame_changed(self, widget, *args):
		
		# get correct gettext method
		_ = self._
		
		print "on_cboKeyFrame_changed"
		localcboKeyFrame = self.cboKeyFrame.get_active_text().lower()
		keyframe = None
		
		if localcboKeyFrame == _("Start of Clip").lower():
			# get start keyframe
			self.current_keyframe = "start"
			keyframe = self.keyframes[self.current_keyframe]
		else:
			# get end keyframe
			self.current_keyframe = "end"
			keyframe = self.keyframes[self.current_keyframe]

		# update keyframe widgets
		self.txtHeight.set_value(float(keyframe.height))
		self.txtWidth.set_value(float(keyframe.width))
		self.txtX.set_value(float(keyframe.x))
		self.txtY.set_value(float(keyframe.y))
		self.scaleAlpha.set_value(keyframe.alpha * 100)

		
	def on_cboSimpleSpeed_changed(self, widget, *args):
		
		# get correct gettext method
		_ = self._
		
		print "on_cboSimpleSpeed_changed"	
		localcboSimpleSpeed = self.cboSimpleSpeed.get_active_text().lower().replace("x","")
		
		if localcboSimpleSpeed == _("Normal Speed").lower():
			num = 1.0
			den = 1.0
		else:
			# calculate decimal speed
			arrSpeed = localcboSimpleSpeed.split("/")
			if len(arrSpeed) == 1:
				num = float(arrSpeed[0])
				den = 1.0
			else:
				num = float(arrSpeed[0])
				den = float(arrSpeed[1])
				
		# set the advanced speed textbox
		self.spinAdvancedSpeed.set_value(num / den)
		
	def on_txtIn_value_changed(self, widget, *args):
		# get correct gettext method
		_ = self._
		
		print "on_txtIn_value_changed"
		local_in = float(self.txtIn.get_value())
		local_out = float(self.txtOut.get_value())
		
		# is IN valid?
		if local_in >= local_out:
			local_in = local_out - 0.01
			self.txtIn.set_text(str(local_in))
		
		# update length
		self.txtLength.set_text(_("{0} seconds").format(str(round(local_out - local_in, 2))))
		
	def on_txtOut_value_changed(self, widget, *args):
		# get correct gettext method
		_ = self._
		
		print "on_txtOut_value_changed"
		local_in = float(self.txtIn.get_value())
		local_out = float(self.txtOut.get_value())
		local_max_length = round(self.current_clip.max_length, 2)
		
		# is IN valid?
		if local_out <= local_in:
			local_out = local_in + 0.01
			self.txtOut.set_text(str(local_out))
		
		if local_out > local_max_length:
			local_out = local_max_length
			self.txtOut.set_text(str(local_out))
		
		# update length
		self.txtLength.set_text(_("{0} seconds").format(str(round(local_out - local_in, 2))))

	def set_keyframe_dropdown(self):
		# get the model and iterator of the project type dropdown box
		model = self.cboKeyFrame.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)

			# set the item as active
			self.cboKeyFrame.set_active_iter(iter)
			break

			
			
	def set_speed_dropdown(self):
		
		# get correct gettext method
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboSimpleSpeed.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0).lower().replace("x", "")
			
			if value == _("Normal Speed").lower():
				num = 1.0
				den = 1.0
			else:
				# calculate decimal speed
				arrSpeed = value.split("/")
				if len(arrSpeed) == 1:
					num = float(arrSpeed[0])
					den = 1.0
				else:
					num = float(arrSpeed[0])
					den = float(arrSpeed[1])

				
			# check for the matching project type
			if self.current_clip.speed >= 1.0 and self.current_clip.speed == num:
				
				# set the item as active
				self.cboSimpleSpeed.set_active_iter(iter)
				break
			
			# check for the matching project type
			if self.current_clip.speed < 1.0 and self.current_clip.speed == num / den:
				
				# set the item as active
				self.cboSimpleSpeed.set_active_iter(iter)
				break
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				# collapse simple, expand advanced
				self.expanderSimple.set_expanded(False)
				self.expanderAdvanced.set_expanded(True)
				break
			
				
			
			


	def on_btnResetSpeed_clicked(self, widget, *args):
		print "on_btnResetSpeed_clicked"
		
		# reset the speed to 1.0
		self.sliderSpeed.set_value(1.0)

		
	def set_direction_dropdown(self):
		
		# get correct gettext method
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboDirection.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)

			# check for the matching project type
			if self.current_clip.reversed == True and value.lower() == _("Reverse").lower():			
				
				# set the item as active
				self.cboDirection.set_active_iter(iter)
				
			# check for the matching project type
			if self.current_clip.reversed == False and value.lower() == _("Forward").lower():			
				
				# set the item as active
				self.cboDirection.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
		


	def set_horizontal_align_dropdown(self):
		# get the model and iterator of the project type dropdown box
		model = self.cboHAlign.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)

			# check for the matching project type
			if self.current_clip.halign.lower() == value.lower():			
				
				# set the item as active
				self.cboHAlign.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
	def set_vertical_align_dropdown(self):
		# get the model and iterator of the project type dropdown box
		model = self.cboVAlign.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)

			# check for the matching project type
			if self.current_clip.valign.lower() == value.lower():			
				
				# set the item as active
				self.cboVAlign.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
	def apply_settings(self, clip_object):
		
		# get correct gettext method
		_ = self._
		
		# get the frames per second (from the project)
		fps = self.project.fps()
		
		# Get settings
		localcboEnableVideo = self.chkEnableVideo.get_active()
		localcboEnableAudio = self.chkEnableAudio.get_active()
		localspinbtnStart = self.spinbtnStart.get_value()
		localtxtIn = self.txtIn.get_value()
		localtxtOut = self.txtOut.get_value()
		localtxtLength = float(self.txtLength.get_text().split()[0])
		localcboFill = self.chkFill.get_active()
		localchkMaintainAspect = self.chkMaintainAspect.get_active()
		localcboDirection = self.cboDirection.get_active_text().lower()
		localsliderSpeed = self.spinAdvancedSpeed.get_value()
		localtxtAudioFadeInAmount = self.txtAudioFadeInAmount.get_value()
		localtxtAudioFadeOutAmount = self.txtAudioFadeOutAmount.get_value()
		localtxtVideoFadeInAmount = self.txtVideoFadeInAmount.get_value()
		localtxtVideoFadeOutAmount = self.txtVideoFadeOutAmount.get_value()
		localtxtRotate = self.txtRotate.get_value()
		localsliderVolume = self.sliderVolume.get_value()

		# reset the IN, OUT textboxes to original speed
		original_speed = clip_object.get_speed()
		localtxtIn = localtxtIn * original_speed
		localtxtOut = localtxtOut * original_speed
		localtxtLength = localtxtLength * original_speed

		localtxtHeight = self.txtHeight.get_value()
		localtxtWidth = self.txtWidth.get_value()
		localtxtX = self.txtX.get_value()
		localtxtY = self.txtY.get_value()
		localcboHAlign = self.cboHAlign.get_active_text().lower()
		localcboVAlign = self.cboVAlign.get_active_text().lower()
		localscaleAlpha = self.scaleAlpha.get_value()
		
		# update clip object
		clip_object.position_on_track = localspinbtnStart
		clip_object.play_video = localcboEnableVideo
		clip_object.play_audio = localcboEnableAudio
		clip_object.speed = localsliderSpeed	# set new speed
		clip_object.halign = localcboHAlign
		clip_object.valign = localcboVAlign
		clip_object.audio_fade_in_amount = localtxtAudioFadeInAmount
		clip_object.audio_fade_out_amount = localtxtAudioFadeOutAmount
		clip_object.video_fade_in_amount = localtxtVideoFadeInAmount
		clip_object.video_fade_out_amount = localtxtVideoFadeOutAmount
		clip_object.rotation = localtxtRotate
		clip_object.volume = localsliderVolume
		
		clip_object.video_fade_in = self.chkVideoFadeIn.get_active()
		clip_object.video_fade_out = self.chkVideoFadeOut.get_active()
		clip_object.audio_fade_in = self.chkAudioFadeIn.get_active()
		clip_object.audio_fade_out = self.chkAudioFadeOut.get_active()
		
		clip_object.fill = localcboFill
		if localchkMaintainAspect:
			clip_object.distort = False
		else:
			clip_object.distort = True
		
		# get new speed of clip (and update end_time... and thus length)
		speed_multiplier = clip_object.get_speed()
		original_length = clip_object.length()
		clip_object.max_length = clip_object.file_object.length / speed_multiplier
		clip_object.start_time = localtxtIn / speed_multiplier
		new_end_time = localtxtOut / speed_multiplier
				
		if speed_multiplier < original_speed:
			# clip is longer now (keep the short version)
			clip_object.end_time = clip_object.start_time + original_length
		else:
			# clip is shorter
			clip_object.end_time = new_end_time
		
		# update keyframes
		clip_object.keyframes = self.keyframes
		
		# Update the thumbnail
		clip_object.update_thumbnail()
		
		if localcboDirection.lower() == _("Reverse").lower():
			clip_object.reversed = True
		else:
			clip_object.reversed = False

	def on_btnPlay_clicked(self, widget, *args):
		print "on_btnPlay_clicked"

		# Get the current speed
		current_speed = self.form.MyVideo.get_speed()
		position = self.form.MyVideo.position()
		
		# Refresh Preview XML
		self.RefreshPreview()
		
		# seek back to position
		self.form.MyVideo.seek(position)

		# is video stopped?
		if current_speed == 0:
			# start video
			self.form.MyVideo.play()
		else:
			# stop video
			self.form.MyVideo.pause()
			

		
		
	def on_hpaned1_size_allocate(self, widget, *args):
		#print "on_hpanel1_size_allocate"
		
		if self.form.MyVideo:
			# refresh sdl
			self.form.MyVideo.refresh_sdl()
			

	def on_hsPreviewProgress_button_press_event(self, widget, *args):
		#print "on_hsPreviewProgress_button_press_event"
		
		# get the percentage of the video progress 0 to 100
		video_progress_percent = float(self.hsPreviewProgress.get_value()) / 100.0

		# determine frame number
		new_frame = int(float(self.form.MyVideo.get_length() - 1) * video_progress_percent)

		# Refresh Preview XML
		self.RefreshPreview()

		# jump to this frame
		self.form.MyVideo.seek(new_frame)


	def on_hsPreviewProgress_change_value(self, widget, *args):
		#print "on_hsPreviewProgress_value_changed"

		# get the percentage of the video progress 0 to 100
		video_progress_percent = float(self.hsPreviewProgress.get_value()) / 100.0

		# determine frame number
		new_frame = int(float(self.form.MyVideo.get_length() - 1) * video_progress_percent)

		# jump to this frame
		self.form.MyVideo.seek(new_frame)
		
	def RefreshPreview(self):
		# Apply settings to preview clip object
		self.apply_settings(self.copy_of_clip)

		# Set clip to position 0 seconds
		self.copy_of_clip.position_on_track = 0.0

		# Generate the Preview XML
		self.copy_of_clip.GeneratePreviewXML(os.path.join(self.project.USER_DIR, "preview.mlt"), "clip-properties-preview")

		# Hook up video thread to new alternative progress bar
		#self.form.MyVideo.alternate_progress_bar = self.hsPreviewProgress
		gobject.idle_add(self.form.MyVideo.set_progress_bar, self.hsPreviewProgress)

		# Load XML
		self.form.MyVideo.set_project(self.project, self.form, os.path.join(self.project.USER_DIR, "preview.mlt"), mode="preview")
		self.form.MyVideo.load_xml()


	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		
		# close the window
		self.close_window()


	def on_btnClose_clicked(self, widget, *args):
		print "on_btnClose_clicked"
		
		# only close the window if it finds a current_clip object
		if self.current_clip:
		
			# Apply settings to current clip object
			self.apply_settings(self.current_clip)
			
			# update the effects list
			if not self.chkEffectsApplyAll.get_active():
				# Apply effects to just this clip
				self.current_clip.effects = copy.deepcopy(self.copy_of_clip.effects)
			else:
				# Apply to all clips on this track
				for other_clip in self.current_clip.parent.clips:
					# Apply effects to all clips
					other_clip.effects = copy.deepcopy(self.copy_of_clip.effects)
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type = self._("Modified clip properties"))
			
			# remove from canvas
			parent = self.current_clip_item.get_parent()
			child_num = parent.find_child (self.current_clip_item)
			parent.remove_child (child_num)
			
			# re-render just this clip
			self.current_clip.RenderClip()
			
			# raise all transitions
			self.project.sequences[0].raise_transitions()
			
			# raise the play-head
			self.project.sequences[0].raise_play_head()
			
			# check if the timeline needs to be expanded
			self.form.expand_timeline(self.current_clip)
			
			# clear the clip object
			self.current_clip = None
			
			# close the window
			self.close_window()
			
	def on_chkVideoFadeIn_toggled(self, widget, *args):
		if self.chkVideoFadeIn.get_active():
			self.txtVideoFadeInAmount.set_sensitive(True)
		else:
			self.txtVideoFadeInAmount.set_sensitive(False)
			
		
	def on_chkVideoFadeOut_toggled(self, widget, *args):
		if self.chkVideoFadeOut.get_active():
			self.txtVideoFadeOutAmount.set_sensitive(True)
		else:
			self.txtVideoFadeOutAmount.set_sensitive(False)
			
			
	def on_chkAudioFadeIn_toggled(self, widget, *args):
		if self.chkAudioFadeIn.get_active():
			self.txtAudioFadeInAmount.set_sensitive(True)
		else:
			self.txtAudioFadeInAmount.set_sensitive(False)
			
			
	def on_chkAudioFadeOut_toggled(self, widget, *args):
		if self.chkAudioFadeOut.get_active():
			self.txtAudioFadeOutAmount.set_sensitive(True)
		else:
			self.txtAudioFadeOutAmount.set_sensitive(False)
			
		
	def close_window(self):
		""" Have the video thread close this window, to prevent SDL crashes """
		# Force SDL to write on our drawing area
		os.putenv('SDL_WINDOWID', str(self.form.videoscreen.window.xid))
		gtk.gdk.flush()
		
		# Stop the video thread consumer
		self.form.MyVideo.pause()
		self.form.MyVideo.consumer_stop()
		
		# Un-hook alternative progress bar
		gobject.idle_add(self.form.MyVideo.clear_progress_bar)
		gobject.idle_add(self.form.MyVideo.close_window, self.frmClipProperties)
	
			
def main():
	frmClipProperties = frmClipProperties()
	frmClipProperties.run()

if __name__ == "__main__":
	main()

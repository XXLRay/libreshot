#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2010  Jonathan Thomas
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

import os
import gtk
import random
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import preferences, TreeFiles
from classes import project, messagebox, timeline, files

# init the foreign language
from language import Language_Init


class frmAddToTimeline(SimpleGtkBuilderApp):

	def __init__(self, path="AddToTimeline.ui", root="frmAddToTimeline", domain="LibreShot", form=None, project=None, selected_files=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.form = form
		self.project = project
		self.selected_files = selected_files
		self.transitions = {}
		self.frmAddToTimeline.show_all()
		
		# init the LibreShot files tree
		self.OSTreeFiles = TreeFiles.LibreShotTree(self.treeFiles, self.project)
		self.OSTreeFiles.set_project(self.project)
		self.model = self.treeFiles.get_model()
		
		# init the value of start_time with the play-head position
		self.txtStartTime.set_value(self.project.sequences[0].play_head_position)

		# refresh tree
		self.refresh()

		# Get default length of images
		imported_image_length = float(preferences.Settings.general["imported_image_length"])
		max_transition_length = (imported_image_length / 2.0) - 0.1
		
		# Set the upper limits of the transitions & fade length
		adjustment1 = gtk.Adjustment(value=2.0, lower=0.0, upper=max_transition_length, step_incr=0.5, page_incr=0.5, page_size=0.0)
		self.txtTransitionLength.configure(adjustment1, 0.5, 2)
		
		adjustment2 = gtk.Adjustment(value=2.0, lower=0.0, upper=max_transition_length, step_incr=0.5, page_incr=0.5, page_size=0.0)
		self.txtFadeLength.configure(adjustment2, 0.5, 2)
		
		# init all dropdowns
		self.init_fade()
		self.init_tracks()
		self.init_transitions()
		
		
	def init_transitions(self):

		# get translation object
		_ = self._
		
		# init the transition length
		self.txtTransitionLength.set_value(2.0)
		
		model = self.cboTransition.get_model()
		model.clear()
		
		# Add the first transition
		self.cboTransition.append_text(_("No Transition"))
		self.cboTransition.append_text(_("Random Transition"))
		self.cboTransition.append_text(_("Dissolve"))
		self.transitions[_("Dissolve")] = ""
		
		# get a list of files in the LibreShot /transitions directory
		file_list = os.listdir(os.path.join(self.project.TRANSITIONS_DIR))

		for fname in sorted(file_list):
			
			(dirName, file_name) = os.path.split(fname)
			(fileBaseName, fileExtension)=os.path.splitext(file_name)
			
			if fname == "icons":
				# ignore the 'icons' folder
				continue

			# get name of transition
			trans_name = fileBaseName.replace("_", " ").capitalize()

			# append profile to list
			self.cboTransition.append_text(_(trans_name))
			self.transitions[_(trans_name)] = os.path.join(self.project.TRANSITIONS_DIR, fname)
		
		# set the default value
		self.set_dropdown_values(_("No Transition"), self.cboTransition)
		

	def init_tracks(self):

		# get translation object
		_ = self._

		# validate that 2 tracks are present
		if len(self.project.sequences[0].tracks) == 0:
			# no tracks, so add 2
			self.project.sequences[0].AddTrack(_("New Track 1"))
			self.project.sequences[0].AddTrack(_("New Track 2"))
			self.form.refresh()	# show new tracks
		elif len(self.project.sequences[0].tracks) == 1:
			# only 1 track, so add another
			self.project.sequences[0].AddTrack(_("New Track"))
			self.form.refresh()	# show new tracks
		
		counter = 0
		for dropdown in [self.cboTrackA, self.cboTrackB]:
			model = dropdown.get_model()
			model.clear()
			
			# loop through export to options
			for track in self.project.sequences[0].tracks:
				# append profile to list
				dropdown.append_text(track.name)
			
			# set the default value
			self.set_dropdown_values(self.project.sequences[0].tracks[counter].name, dropdown)
			counter = counter + 1
			
	
	def init_fade(self):
		
		# get translation object
		_ = self._
		
		# init the transition length
		self.txtFadeLength.set_value(2.0)
		
		model = self.cboFade.get_model()
		model.clear()
		
		# loop through export to options
		for option in [_("No Fade"), _("Fade In"), _("Fade Out"), _("Fade In & Out")]:
			# append profile to list
			self.cboFade.append_text(option)
		
		# set the default value
		self.set_dropdown_values(_("No Fade"), self.cboFade)

	
	def init_animation(self):
		
		# get translation object
		_ = self._
		
		model = self.cboAnimation.get_model()
		model.clear()
		
		# loop through export to options
		for option in [_("No Animation"), _("Zoom In (100% to 150%)"), _("Zoom In (50% to 100%)"), _("Zoom Out (100% to 50%)"), _("Zoom Out (150% to 100%)")]:
			# append profile to list
			self.cboAnimation.append_text(option)
		
		# set the default value
		self.set_dropdown_values(_("No Animation"), self.cboAnimation)
	

	def refresh(self):
		# clear the tree
		self.OSTreeFiles.store.clear()
		
		# Init the project files tree (with selected files)
		for item in self.selected_files:
			
			if isinstance(item, files.LibreShotFile):
				#format the file length field
				milliseconds = item.length * 1000
				time = timeline.timeline().get_friendly_time(milliseconds)
				time_str =  "%02d:%02d:%02d" % (time[2], time[3], time[4])
	
				# get the thumbnail (or load default)
				pbThumb = item.get_thumbnail(51, 38)
				
				#find parent (if any)
				match_iter = None

				# get file name
				(dirName, fileName) = os.path.split(item.name)
				
				# Add row to tree
				self.OSTreeFiles.store.append(match_iter, [pbThumb, fileName, time_str, item.label, item.unique_id])
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmAddToTimeline.destroy()
		
	def on_btnMoveUp_clicked(self, widget, *args):
		print "on_btnMoveUp_clicked"
		
		# Get the selection
		selection = self.treeFiles.get_selection()
		rows, selected = selection.get_selected_rows()
		
		# loop through selected files
		iters = [self.model.get_iter(path) for path in selected]
		for iter in iters:
			# get file object
			unique_id = self.model.get_value(iter, 4)
			file_object = self.project.project_folder.FindFileByID(unique_id)

			# move the item down
			old_position = self.selected_files.index(file_object)
			new_position = old_position - 1
			self.selected_files.insert(new_position, self.selected_files.pop(old_position))
			
		# refresh
		self.refresh()
		
	def on_btnMoveDown_clicked(self, widget, *args):
		print "on_btnMoveDown_clicked"
		
		# Get the selection
		selection = self.treeFiles.get_selection()
		rows, selected = selection.get_selected_rows()
		
		# loop through selected files
		iters = [self.model.get_iter(path) for path in selected]
		for iter in reversed(iters):
			# get file object
			unique_id = self.model.get_value(iter, 4)
			file_object = self.project.project_folder.FindFileByID(unique_id)

			# move the item down
			old_position = self.selected_files.index(file_object)
			new_position = old_position + 1
			self.selected_files.insert(new_position, self.selected_files.pop(old_position))
			
		# refresh
		self.refresh()

		
	def on_btnShuffle_clicked(self, widget, *args):
		print "on_btnShuffle_clicked"
		
		# shuffle the file list
		random.shuffle(self.selected_files)
		
		# refresh tree
		self.refresh()
		
	def on_btnRemove_clicked(self, widget, *args):
		print "on_btnRemove_clicked"
		
		# Get the selection
		selection = self.treeFiles.get_selection()
		rows, selected = selection.get_selected_rows()
		
		# loop through selected files
		iters = [self.model.get_iter(path) for path in selected]
		for iter in reversed(iters):
			# get file object
			unique_id = self.model.get_value(iter, 4)
			file_object = self.project.project_folder.FindFileByID(unique_id)
			
			# remove file
			self.selected_files.remove(file_object)
			
		# refresh tree
		self.refresh()
		
		
	def set_dropdown_values(self, value_to_set, combobox):
		
		# get reference to gettext
		_ = self._
		
		model = combobox.get_model()
		iter = model.get_iter_first()
		while iter:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)
			
			# check for the matching value
			if value_to_set == value:			
				
				# set the item as active
				combobox.set_active_iter(iter)
				break
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None and value_to_set not in self.invalid_codecs:
				self.invalid_codecs.append(value_to_set)
				break
		

	def on_btnAdd_clicked(self, widget, *args):
		print "on_btnAdd_clicked"
		
		# get reference to gettext
		_ = self._
		
		# get settings
		new_clip = None
		start_time = self.txtStartTime.get_value()
		trackA_name = self.cboTrackA.get_active_text()
		trackA_object = None
		trackB_name = self.cboTrackB.get_active_text()
		trackB_object = None
		fade_name = self.cboFade.get_active_text()
		fade_length = self.txtFadeLength.get_value()
		transition_name = self.cboTransition.get_active_text()
		transition_file_path = None
		transition_length = self.txtTransitionLength.get_value()
		#animation = self.cboAnimation.get_active_text()
		use_transitions = True
		use_random = False
		
		if transition_name == _("No Transition"):
			# do not use a transition
			use_transitions = False
		elif transition_name == _("Random Transition"):
			# random transitions
			use_random = True
		else:
			# get the file path of the transition
			transition_file_path = self.transitions[transition_name]
			
		# get actual track objects
		for track in self.project.sequences[0].tracks:
			if trackA_name == track.name:
				trackA_object = track
			if trackB_name == track.name:
				trackB_object = track
		
		# Validate the the top track is above the bottom track
		if self.project.sequences[0].tracks.index(trackA_object) >= self.project.sequences[0].tracks.index(trackB_object):
			# Show error message
			messagebox.show(_("Validation Error!"), _("The top track must be higher than the bottom track."))
			return

		# init the start position / time
		position = start_time
		location = "top"
		current_track = trackA_object
		
		# loop through all files (in tree order)
		for file in self.selected_files:
			
			# Get filename
			(dirName, fileName) = os.path.split(file.name)
			
			# Add clips to track 1
			new_clip = current_track.AddClip(fileName, "Gold", position, float(0.0), float(file.length), file)

			# Apply Fade settings
			if fade_name == _("Fade In"):
				new_clip.audio_fade_in = True
				new_clip.video_fade_in = True
				new_clip.audio_fade_in_amount = fade_length
				new_clip.video_fade_in_amount = fade_length
			elif fade_name == _("Fade Out"):
				new_clip.audio_fade_out = True
				new_clip.video_fade_out = True
				new_clip.audio_fade_out_amount = fade_length
				new_clip.video_fade_out_amount = fade_length
			elif fade_name == _("Fade In & Out"):
				new_clip.audio_fade_in = True
				new_clip.video_fade_in = True
				new_clip.audio_fade_out = True
				new_clip.video_fade_out = True
				new_clip.audio_fade_in_amount = fade_length
				new_clip.audio_fade_out_amount = fade_length
				new_clip.video_fade_in_amount = fade_length
				new_clip.video_fade_out_amount = fade_length
			
			# increment position
			if use_transitions:
				# adjust the position based on the transition length
				position = position + new_clip.length() - transition_length
			else:
				position = position + new_clip.length()
				
			# Add transition (if needed)
			if use_transitions:
			
				# if a random transition, choose a random one
				if use_random:
					random_transition = random.choice(self.transitions.items())
					transition_name = random_transition[0]
					transition_file_path = random_transition[1]
				
				# add the transition
				new_trans = trackA_object.AddTransition(transition_name, position, transition_length, transition_file_path)
				if location == "top":
					new_trans.reverse = True
			
			# change tracks (if needed)
			if use_transitions:
				if current_track == trackA_object:
					location = "bottom"
					current_track = trackB_object
				else:
					current_track = trackA_object
					location = "top"

		# Does timeline need to be expanded?
		if new_clip:
			self.form.expand_timeline(new_clip)

		#mark the project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Added files to timeline")
		
		# close this window
		self.frmAddToTimeline.destroy()
		
		# refresh the main form & timeline
		self.form.refresh()
		
			
def main():
	frm_add_files = frmAddToTimeline()
	frm_add_files.run()

if __name__ == "__main__":
	main()

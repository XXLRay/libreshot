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

import cPickle as pickle
import os
import gtk
from classes import messagebox, files

def open_project(project_object, file_path):
   
	# try and open an existing project file
	try:
		# open the serialized file
		myFile = file(file_path, "rb")
		old_form = project_object.form
		old_play_head = project_object.sequences[0].play_head
		old_ruler_time = project_object.sequences[0].ruler_time
		old_thumbnailer = project_object.thumbnailer
		old_play_head_line = project_object.sequences[0].play_head_line
		old_theme = project_object.theme
		project_object.mlt_profile = None

		# update the form reference on the new project file
		project_object = pickle.load(myFile)

		# re-attach some variables (that aren't pickleable)
		project_object.form = old_form
		project_object.sequences[0].play_head = old_play_head
		project_object.sequences[0].ruler_time = old_ruler_time
		project_object.sequences[0].play_head_line = old_play_head_line
		project_object.thumbnailer = old_thumbnailer
		project_object.sequences[0].play_head_position = 0.0
		project_object.theme = old_theme
		
		# update the thumbnailer's project reference
		project_object.thumbnailer.set_project(project_object)
		
		# update project reference to menus
		project_object.form.mnuTrack1.project = project_object
		project_object.form.mnuClip1.project = project_object
		project_object.form.mnuTransition1.project = project_object
		
		# update the project reference on the form variable
		project_object.form.project = project_object

		# update project references in the menus
		project_object.form.mnuTrack1.project = project_object.form.project
		project_object.form.mnuClip1.project = project_object.form.project
		project_object.form.mnuMarker1.project = project_object.form.project
		project_object.form.mnuTransition1.project = project_object.form.project
		project_object.form.mnuFadeSubMenu1.project = project_object.form.project
		project_object.form.mnuAnimateSubMenu1.project = project_object.form.project
		project_object.form.mnuRotateSubMenu1.project = project_object.form.project
		project_object.form.mnuPositionSubMenu1.project = project_object.form.project
		
		
		#check project files still exist in the same location
		missing_files = ""
		items = project_object.project_folder.items
				
		for item in items:
			if isinstance(item, files.OpenShotFile):
				if not os.path.exists(item.name) and "%" not in item.name:
					missing_files += item.name + "\n"
		
		if missing_files:
			messagebox.show("OpenShot", _("The following file(s) no longer exist.") + "\n\n" + missing_files)

		missing_transitions = ""
		
		for sequence in project_object.sequences:
			for track in sequence.tracks:
				for transition in track.transitions:
					if transition.resource == "":
						continue
					if not os.path.exists(transition.resource):
						missing_transitions += transition.resource + "\n"
						transition.resource = "" # default to dissolve
		
		if missing_transitions:
			messagebox.show("OpenShot", _("The following transition(s) no longer exist.") + "\n\n" + missing_transitions)
		
		# Recreate the thumbnail folder if it is missing
		if not os.path.exists(project_object.folder + "/thumbnail"):
			os.makedirs(project_object.folder + "/thumbnail")
		
		# Recreate missing thumbnails for files
		for item in items:
			if isinstance(item, files.OpenShotFile):
				if not os.path.exists(item.thumb_location):
					item.update_thumbnail()
		
		# Recreate missing thumbnails for clips
		for sequence in project_object.sequences:
			for track in sequence.tracks:
				for clip in track.clips:
					# Code to keep pre 1.4.0 .osp files compatible. May be removed later.
					if not hasattr(clip, "thumb_location"):
						clip.thumb_location = ""
				
					if not os.path.exists(clip.thumb_location) and not clip.file_object.file_type == "audio":
						clip.update_thumbnail()
		
		# mark XML as refreshable
		project_object.set_project_modified(is_modified=False, refresh_xml=True)
		
		# refresh xml
		project_object.RefreshXML()
		
		# Set the theme
		project_object.set_theme(project_object.theme)
		
		# clear history (since we are opening a new project)
		project_object.form.history_stack = []
		project_object.form.history_index = -1
		project_object.form.refresh_history()

		# scroll canvases back to 0,0
		project_object.form.vscrollbar2.set_value(0)
		project_object.form.hscrollbar2.set_value(0)
		
		# add project file to recent files
		manager = gtk.recent_manager_get_default()
		manager.add_item('file://' + file_path)

		
	except IOError:
		# Show error message
		messagebox.show(_("Error!"), _("There was an error opening this project file.  Please be sure you are selecting a valid .OSP project file."))
		  
		  
		  
		  

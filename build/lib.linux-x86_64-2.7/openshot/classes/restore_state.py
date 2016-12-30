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
from cStringIO import StringIO as StringIO 
from classes import messagebox, files

def restore_project_state(project_object, state):

	# open the serialized file
	old_form = project_object.form
	old_play_head = project_object.sequences[0].play_head
	old_ruler_time = project_object.sequences[0].ruler_time
	old_thumbnailer = project_object.thumbnailer
	old_play_head_line = project_object.sequences[0].play_head_line
	old_theme = project_object.theme

	# update the form reference on the new project file
	state.seek(0,0)
	project_object = pickle.load(state)

	# re-attach some variables (that aren't pickleable)
	project_object.form = old_form
	project_object.sequences[0].play_head = old_play_head
	project_object.sequences[0].ruler_time = old_ruler_time
	project_object.sequences[0].play_head_line = old_play_head_line
	project_object.thumbnailer = old_thumbnailer
	#project_object.sequences[0].play_head_position = 0.0
	project_object.theme = old_theme
	project_object.mlt_profile = None
	
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
	project_object.form.mnuAnimateSubMenu1.project = project_object.form.project
	project_object.form.mnuPositionSubMenu1.project = project_object.form.project
	
	# mark XML as refreshable
	project_object.set_project_modified(is_modified=True, refresh_xml=True)
	
	#check project files still exist in the same location
	missing_files = ""
	items = project_object.project_folder.items
			
	for item in items:
		if isinstance(item, files.OpenShotFile):
			if not os.path.exists(item.name) and "%" not in item.name:
				missing_files += item.name + "\n"
	
	if missing_files:
		messagebox.show("OpenShot", _("The following file(s) no longer exist." + "\n" + "Please restore them or remove them from your project:" + "\n\n" + missing_files))
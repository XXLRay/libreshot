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

import sys, os
import shutil
import gtk
import cPickle as pickle
from cStringIO import StringIO as StringIO 
from classes import files

def save_state(project_object):
	
		project = project_object
		cstringio_object = StringIO()	

		# clear the following temporary properties which can't be pickeled
		old_form = project_object.form
		old_play_head = project_object.sequences[0].play_head
		old_ruler_time = project_object.sequences[0].ruler_time
		old_play_head_line = project_object.sequences[0].play_head_line
		old_thumbnailer = project_object.thumbnailer
		project_object.mlt_profile = None
		
		project_object.sequences[0].play_head = None
		project_object.sequences[0].ruler_time = None
		project_object.sequences[0].play_head_line = None
		project_object.form = None
		project_object.thumbnailer = None
				
		# serialize the project object
		pickle.dump(project_object, cstringio_object, -1)
		
		# re-attach some variables (that aren't pickleable)
		project_object.form = old_form
		project_object.sequences[0].play_head = old_play_head
		project_object.sequences[0].ruler_time = old_ruler_time
		project_object.sequences[0].play_head_line = old_play_head_line
		project_object.thumbnailer = old_thumbnailer
		
		# update the thumbnailer's project reference
		project_object.thumbnailer.set_project(project_object)
		
		# update project references in the menus
		project_object.form.mnuTrack1.project = project_object
		project_object.form.mnuClip1.project = project_object
		project_object.form.mnuMarker1.project = project_object
		project_object.form.mnuTransition1.project = project_object
		project_object.form.mnuAnimateSubMenu1.project = project_object
		project_object.form.mnuPositionSubMenu1.project = project_object
		
		
		# output the file path
		print "state saved"
		return cstringio_object
		
		
			   

		  
		  

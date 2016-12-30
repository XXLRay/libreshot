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

import os
import gtk
import shutil
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from classes import project, messagebox

# init the foreign language
from language import Language_Init


class frmImportTransitions(SimpleGtkBuilderApp):

	def __init__(self, path="ImportTransitions.ui", root="frmImportTransitions", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.project = project
		self.form = form
		
		filter = gtk.FileFilter()
		filter.set_name("PNG files")
		filter.add_pattern("*.png")
		#filter.add_pattern("*.pgm")
		self.fileTransition.add_filter(filter)
		
		self.transition_file = ""
		self.icon_file = ""
		
		self.frmImportTransitions.show_all()
		
	def on_btnCancel_clicked(self, widget, *args):
		self.frmImportTransitions.destroy()
		
	def on_fileTransition_file_set(self, widget, *args):
		self.transition_file = self.fileTransition.get_filename()
		
		# enable "ok" button
		self.btnOK.set_sensitive(True)
			
		
	def on_fileIcon_file_set(self, widget, *args):
		pass

	def on_btnOK_clicked(self, widget, *args):
		self.import_transition()
			
	def import_transition(self):
		# get translation method
		_ = self._
		
		# Create user directory / transitions folders for the new icon files
		if not os.path.exists(self.project.USER_TRANSITIONS_DIR):
			os.makedirs(self.project.USER_TRANSITIONS_DIR)

		try:
			# init file paths
			(dirName, filename) = os.path.split(self.transition_file)
			(simple_filename, file_extention) = os.path.splitext(filename)
			new_transition_path = os.path.join(self.project.USER_TRANSITIONS_DIR, filename)
	
			# copy transition & icon into .openshot folder
			shutil.copyfile(self.transition_file, new_transition_path)
	
			# Refresh the main screen, to show the new transition
			self.form.on_btnTransFilterAll_toggled(None)
			
			# Switch to transitions tab
			self.form.nbFiles.set_current_page(0) # switch to files
			self.form.nbFiles.set_current_page(1) # and then back to transitions
			
			messagebox.show("Openshot", _("Transition Imported successfully!"))
			self.frmImportTransitions.destroy()
			
		except:
			messagebox.show(_("Error!"), _("There was an error importing the Transition!"))
		
		
def main():
	import_transitions = frmImportTransitions()
	import_transitions.run()

if __name__ == "__main__":
	main()
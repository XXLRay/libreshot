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

import os
import gtk
import time
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import preferences
from classes import project, messagebox

# init the foreign language
from language import Language_Init


class frmAddFiles(SimpleGtkBuilderApp):

	def __init__(self, path="AddFiles.ui", root="frmAddFiles", domain="LibreShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.frmAddFiles.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
		self.frmAddFiles.set_select_multiple(True)
		self.frmAddFiles.set_local_only(False)
		
		self.form = form
		self.project = project
		
		#open the last used folder
		default_folder = preferences.Settings.app_state["import_folder"]
		if default_folder != "None":
			self.frmAddFiles.set_current_folder(preferences.Settings.app_state["import_folder"])
		
		self.frmAddFiles.show_all()


	def on_btnCancel_clicked(self, widget, *args):
		self.frmAddFiles.destroy()
		
	def on_btnAdd_clicked(self, widget, *args):
		files_to_add = self.frmAddFiles.get_filenames()
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		# create a unique session id, to prevent duplicate prompts
		session = str(time.time())
		
		# The total number of ok files selected (not folders)
		total_ok_files = 0
		# The total number of broken files selected (could not be imported)
		total_broken_files = 0
		# The total number of files already imported selected
		total_duplicate_files = 0
		# The total number of folders selected
		total_folders = 0
		
		try:
			for file in files_to_add:
				# add each file
				result = self.project.project_folder.AddFile(file, session=session)
				# parse the results and add to the total
				total_ok_files += result[0]
				total_broken_files += result[1]
				total_duplicate_files += result[2]
				total_folders += result[3]
		
			# The number of total selected files, not including folders
			total_files = total_ok_files + total_broken_files + total_duplicate_files
		
			# print error messages (if needed)
		
			if total_files == 0:
				if total_folders == 1:
					messagebox.show(_("Empty Folder "), _("The selected folder was empty."))
				else:
					messagebox.show(_("Empty Folders"), _("The selected folders were empty."))
			else:
				if total_files == total_broken_files:
					if total_files == 1:
						messagebox.show(_("Unsupported File Type"), _("LibreShot does not support this file type."))
					else:
						messagebox.show(_("Unsupported File Types"), _("LibreShot supports none of the file types of the selected files."))
			
				elif total_files == total_duplicate_files:
					if total_files == 1:
						messagebox.show(_("Already Imported File"), _("The selected file has already been imported to the project."))
					else:
						messagebox.show(_("Already Imported Files"), _("All of the selected files have already been imported to the project."))
			
				elif total_ok_files == 0:
					messagebox.show(_("File Import Error"), _("The selected files either have an unsupported file type or have already been imported to the project."))
					
			# set the project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=False)
			
			# refresh the main form
			self.form.refresh_files()
			
		except:
			messagebox.show(_("Error"), _("There was an error importing the selected file(s)."))

		#set the last used folder
		current_folder = self.frmAddFiles.get_current_folder()
		if current_folder is None:
			current_folder = "None"
		preferences.Settings.app_state["import_folder"] = current_folder
		
		# clear and destroy this dialog
		self.form.import_files_dialog = None	
		self.frmAddFiles.destroy()
		
	def on_frmAddFiles_file_activated(self, widget, *args):
		#call the open project method when a file is double clicked
		self.on_btnAdd_clicked(widget, *args)
		
class frmReplaceFiles(SimpleGtkBuilderApp):

	def __init__(self, path="AddFiles.ui", root="frmAddFiles", domain="LibreShot", form=None, project=None,clip=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.frmAddFiles.set_title("LibreShot")
		self.frmAddFiles.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
		self.frmAddFiles.set_select_multiple(False)
		
		self.form = form
		self.project = project
		self.clip = clip		
		
		self.frmAddFiles.show_all()
		
	def on_btnCancel_clicked(self, widget, *args):
		self.frmAddFiles.destroy()
		
	def on_btnAdd_clicked(self, widget, *args):
		replace_clip_with = self.frmAddFiles.get_filename()
		try:
			#does the new file already exist in the project?
			file_object = self.project.project_folder.FindFile(replace_clip_with)
			if not file_object:
				#add the file to the project
				self.project.project_folder.AddFile(replace_clip_with)
			
			#this method does the actual replacement and modifies the project	
			self.form.replace_clip(self.clip,replace_clip_with)
			
		except:
			messagebox.show(_("Error"), _("There was an error importing the selected file(s)."))

		#set the last used folder
		current_folder = self.frmAddFiles.get_current_folder()
		if current_folder is None:
			current_folder = "None"
		preferences.Settings.app_state["import_folder"] = current_folder
		
			
		self.frmAddFiles.destroy()
		
			
		
	def on_frmAddFiles_file_activated(self, widget, *args):
		#call the open project method when a file is double clicked
		self.on_btnAdd_clicked(widget, *args)
		
	def get_replace_clip_with(self):
		return self.replace_clip_with
		
		
			
def main():
	frm_add_files = frmAddFiles()
	frm_add_files.run()

if __name__ == "__main__":
	main()

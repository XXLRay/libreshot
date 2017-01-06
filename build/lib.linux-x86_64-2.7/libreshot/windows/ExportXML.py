#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
#
#	This file is part of LibreShot Video Editor (http://launchpad.net/openshot/).
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

import os, gtk
import gtk
from classes import messagebox, project
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp

# init the foriegn language
import language.Language_Init as Language_Init


class frmExportXML(SimpleGtkBuilderApp):

	def __init__(self, path="ExportXML.ui", root="frmExportXML", domain="LibreShot", project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		self.project = project
		self.form = self.project.form

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		# set a file type filter (to limit the files to only valid files)
		OSPfilter = gtk.FileFilter()
		OSPfilter.add_pattern("*.mlt")
		OSPfilter.set_name(_("MLT XML (*.mlt)"))
		self.frmExportXML.add_filter(OSPfilter)
		self.frmExportXML.set_current_folder_uri("file://%s" % self.project.DESKTOP)


	def new(self):
		print "A new %s has been created" % self.__class__.__name__

	def on_frmExportXML_response(self, widget, *args):
		#print "on_frmOpenProject_response called with self.%s" % widget.get_name()
		pass

	def on_btnCancel_clicked(self, widget, *args):
		#print "on_btnCancel_clicked called with self.%s" % widget.get_name()
		self.frmExportXML.destroy()


	def on_btnExportXML_clicked(self, widget, *args):
		#print "on_btnExportXML_clicked called with self.%s" % widget.get_name()

		# Get selected file name
		file_to_save = self.frmExportXML.get_filename()	

		try:
			# Call the GenerateXML method on the project
			self.project.GenerateXML(file_to_save)

			# close window
			self.frmExportXML.destroy()

		except:
			# show the error message
			messagebox.show(_("Error!"), _("There was an error saving this project as XML."))


	def on_frmExportXML_file_activated(self, widget, *args):
		#call the ExportXML method when a file is double clicked
		self.on_btnExportXML_clicked(widget, *args)


def main():
	frm_export_xml = frmExportXML()
	frm_export_xml.run()

if __name__ == "__main__":
	main()

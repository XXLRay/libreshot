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
import gtk, pango
from classes import messagebox, project, timeline
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp

# init the foreign language
from language import Language_Init


class frmFileproperties(SimpleGtkBuilderApp):

	def __init__(self, file, path="FileProperties.ui", root="frmFileProperties", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		
		self.form = form
		self.project = project
		self.file = file
		
		#set the thumbnail - use the preview thumbnail
		#for video & image files
		pixbuf = file.get_thumbnail(112, 83)
		self.imgPreview.set_from_pixbuf(pixbuf)
		
		#set the file type	
		self.lblMimeType.set_label(str(file.file_type).title())
		
		#if the file name is too long to fit the space, add ellipses and a tooltip.
		self.lblLocation1.set_text(file.name)
		#self.lblLocation1.set_tooltip_text(file.name)
		#self.lblLocation1.set_ellipsize(pango.ELLIPSIZE_END)
		#format the file length
		milliseconds = file.length * 1000
		time = timeline.timeline().get_friendly_time(milliseconds)
	
		hours = time[2]
		mins = time[3]
		secs = time[4]
		milli = time[5]
		
		time_str =  "%02d:%02d:%02d:%03d" % (hours, mins, secs, milli)
		self.lblLengthValue.set_label(time_str)
		#project label
		self.txtLabel.set_text(file.label)
		
		if file.file_type in ["video", "image", "image sequence"]:
			self.lblSizeValue.set_label(str(file.width) + " x " + str(file.height))
		else:
			self.lblSize.set_sensitive(False)
		
		#show the form
		self.frmFileProperties.show_all()
		
	def on_btnClose_clicked(self, event, *args):
		self.frmFileProperties.destroy()
		
	def on_btnApply_clicked(self, event, *args):
		
		# update path of file
		self.file.name = self.lblLocation1.get_text()
		
		#if self.txtLabel.get_text() == "":
		#	return

		self.project.project_folder.UpdateFileLabel(self.file.unique_id, self.txtLabel.get_text(), 1)
		self.frmFileProperties.destroy()
		
def main():
	frm_file_properties = frmFileproperties()
	frm_file_properties.run()

if __name__ == "__main__":
	main()

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

has_py_notify = False

try:
	import pynotify
	has_py_notify = True
except:
	has_py_notify = False

import os
import gobject
import gtk
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import preferences
from classes import project, messagebox
from uploads.manager import UploadManager

# init the foreign language
from language import Language_Init


class frmUploadVideo(SimpleGtkBuilderApp):

	def __init__(self, path="UploadVideo.ui", root="frmUploadVideo", domain="LibreShot", form=None, project=None, filename=None, service_name=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.form = form
		self.project = project
		self.filename = filename
		self.upload_manager = UploadManager(project, self.form.settings)

		# Init filename (if any passed in)
		if self.filename:
			self.fileFilename.set_filename(self.filename)
		
		# Init upload services dropdown
		upload_model = self.cboUploadService.get_model()
		upload_model.clear()
		
		self.upload_services = self.upload_manager.get_services()
		upload_types = self.upload_services.keys()
		upload_types.sort()
		# loop through export to options
		for option in upload_types:
			# append profile to list
			self.cboUploadService.append_text(option)
			
		# get default upload service
		if service_name:
			# service name passed into form
			default_upload_service = service_name
		else:
			# get default from settings
			default_upload_service = self.form.settings.app_state["upload_service"]

		if default_upload_service in upload_types:
			self.set_dropdown_values(default_upload_service, self.cboUploadService)
		else:
			self.set_dropdown_values(upload_types[0], self.cboUploadService)
		
	def on_cboUploadService_changed(self, widget, *args):
		print "on_cboUploadService_changed"
		
		if self.cboUploadService.get_active_text():
			service_name = str(self.cboUploadService.get_active_text())
			service = self.upload_services[service_name]
			
			# change default upload service
			self.form.settings.app_state["upload_service"] = service_name
			
			# initialize form
			service.initialize(self)
			
			# update logo
			self.imgLogo.set_from_pixbuf(service.get_logo())
			
			# set file
			service.set_file(self.filename)
			
	def on_btnAuthorize_clicked(self, widget, *args):
		print "on_btnAuthorize_clicked"
		
		# get translation object
		_ = self._
		
		if self.cboUploadService.get_active_text():
			service_name = str(self.cboUploadService.get_active_text())
			service = self.upload_services[service_name]

			try:
				# launch verification URL in webbrowser
				import webbrowser
				webbrowser.open(service.get_authorization_url())
			except:
				messagebox.show(_("Error!"), _("Unable to open the verification web page."))
			
	def on_fileFilename_file_set(self, widget, *args):
		print "on_fileFilename_file_set"
		
		if self.cboUploadService.get_active_text():
			service_name = str(self.cboUploadService.get_active_text())
			service = self.upload_services[service_name]
			self.filename = str.strip(self.fileFilename.get_filename())
			
			# set file
			service.set_file(self.filename)
		
	def update_progressbar(self, percent=0.0):
		#print "on_chunk_complete"
		
		# update progress bar
		self.progressUpload.set_fraction(percent)
		
	def on_frmUploadFile_close(self, widget, *args):
		print "on_frmUploadFile_close"
		self.frmUploadVideo.destroy()

	def on_lnkForgot_clicked(self, widget, *args):
		pass
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmUploadVideo.destroy()
		
	def on_btnUpload_clicked(self, widget, *args):
		print "on_btnUpload_clicked"
		_ = self._

		if self.cboUploadService.get_active_text():
			# get upload service
			service_name = str(self.cboUploadService.get_active_text())
			service = self.upload_services[service_name]
			
			if service.validate(self):
				print "form is valid!"
				
				# start upload
				status = service.start_upload(self)

				# did upload succeed?
				if status == True:
					
					# prompt user that export is completed
					if has_py_notify:
						try:
							# Use libnotify to show the message (if possible)
							if pynotify.init("LibreShot Video Editor"):
								n = pynotify.Notification(_("Upload Successful!"), _("Your video has been successfully uploaded!"))
								n.show()
						except:
							# use a GTK messagebox
							messagebox.show(_("Upload Successful!"), _("Your video has been successfully uploaded!"))
					else:
						# use a GTK messagebox
						messagebox.show(_("Upload Successful!"), _("Your video has been successfully uploaded!"))
						
					# close the window
					self.frmUploadVideo.destroy()


	def set_dropdown_values(self, value_to_set, combobox):
		
		# get reference to gettext
		_ = self._
		
		model = combobox.get_model()
		iter = model.get_iter_first()
		while True:
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
			
def main():
	frmUploadVideo = frmUploadVideo()
	frmUploadVideo.run()

if __name__ == "__main__":
	main()

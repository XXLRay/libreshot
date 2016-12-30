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
import re
from classes import messagebox, project
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp

# init the foreign language
from language import Language_Init

class frmImportImageSequence(SimpleGtkBuilderApp):

	def __init__(self, path="ImportImageSeq.ui", root="frmImportImageSequence", domain="OpenShot", form=None, project=None, pattern=None, initial_folder=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.form = form
		self.project = project
		self.frmImportImageSequence.show_all()
		
		# init frames per image
		self.txtFramesPerImage.set_value(1)
		
		if pattern:
			# init the pattern, if passed in
			self.txtFileName.set_text(pattern)
			
		if initial_folder:
			self.folder_location.set_current_folder(initial_folder)
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmImportImageSequence.destroy()
		
	def on_frmImportImageSequence_destroy(self, widget, *args):
		print "on_frmImportImageSequence_destroy"
		
		self.project.form.import_image_seq_dialog = None
		
	def on_btnImport1_clicked(self, widget, *args):
		print "on_btnImport1_clicked"
		
		txtFileName1 = str.strip(self.txtFileName.get_text())
		txtFramesPerImage1 = self.txtFramesPerImage.get_value()
		RepeatNumber = self.txtRepeatSequence.get_value() + 1 # we always need at least 1
		folder_location1 = str.strip(self.folder_location.get_filename())
		
		# regular expression to parse the naming pattern
		# this breaks the pattern up into [before, %, padding character, number of zeros, letter d , extension]
		e = re.compile(r"(.*)(%)(0?)(\d*)(d)(.*)")
		matches = e.findall(txtFileName1)
		
		# get translation object
		_ = self._
		
		# Validate the the form is valid
		if not matches:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid file name.  The file name must have a %d (or %04d) where the number section of the file name is supposed to be.  For example:  MyFile_%d.png."))

		elif int(txtFramesPerImage1) <= 0:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter an integer in the Frames per Image textbox."))

		else:
			# Get the parts of the filename pattern (from the regex)
			filename = matches[0][0]
			if matches[0][2]:
				padding_char = matches[0][2]
			else:
				padding_char = " "
			if matches[0][3]:
				number_of_decimals = int(matches[0][3])
			else:
				number_of_decimals = 1
			extension = matches[0][5]
			
			# is this file a match?
			number_of_matches = 0
			number_of_non_matches = 0
			first_match_path = ""
			
			# loop through a range of files (and be sure at least 2 matches are found)
			for x in range(0, 50000):
				# parse filename
				full_file_name = "%s%s%s" % (filename, str(x).rjust(number_of_decimals, padding_char) , extension)
				
				# check if file exists
				if os.path.exists(os.path.join(folder_location1, full_file_name)):

					# increment counter 
					number_of_matches = number_of_matches + 1
					number_of_non_matches = 0

					# record first match
					if number_of_matches == 1:
						first_match_path = os.path.join(folder_location1, full_file_name)

				elif number_of_matches > 1:

					# non matching file pattern
					number_of_non_matches = number_of_non_matches + 1
					
					if number_of_non_matches >= 100:
						break

			if number_of_matches <= 1:
				# Show error message
				messagebox.show(_("Validation Error!"), _("At least 2 images must match the file name pattern in the selected folder."))
			
			else: 
				
				# create OpenShotFile (and thumbnail) of the first match
				full_file_path = os.path.join(folder_location1, first_match_path)

				# inspect the media file and generate it's thumbnail image (if any)
				f = self.project.thumbnailer.GetFile(full_file_path)
			
				# add projects default folder
				if f:
					self.project.project_folder.items.append(f)
		
				# mark project as modified
				self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added file"))
				
				# Update the file properties (since it's added as an image)
				# We need to make it look like a video
				f.label = _("Image Sequence")
				f.fps = self.project.fps()
				f.max_frames = number_of_matches * RepeatNumber
				f.ttl = int(txtFramesPerImage1)
				f.length = (float(f.max_frames * f.ttl) / float(f.fps))
				f.file_type = "image sequence"
				f.name = os.path.join(folder_location1, txtFileName1)

				# refresh the main form
				self.project.form.refresh()
				self.frmImportImageSequence.destroy()
		
		
			
def main():
	frmImportImageSequence1 = frmImportImageSequence()
	frmImportImageSequence1.run()

if __name__ == "__main__":
	main()

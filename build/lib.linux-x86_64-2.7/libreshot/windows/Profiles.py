#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
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
#
# Profles Manager  Copyright (C) 2009  Andy Finch
#

import os, sys
import gtk
import tarfile
import shutil
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import preferences
from classes import profiles, messagebox


# init the foriegn language
import language.Language_Init as Language_Init

class frmProfilesManager(SimpleGtkBuilderApp):

	def __init__(self, path="profiles.ui", root="frmProfiles", domain="LibreShot", form=None, parent=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.project = project
		self.form = form
		self.parent = parent

		#find path where libreshot is running
		self.path = self.project.BASE_DIR
		
		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProjectType.append_text(p.description())
			
		self.save_prompt = False
		
		self.frmProfiles.show_all()
		
		#set the default profile
		self.set_project_type_dropdown(self.form.settings.general["default_profile"])
		if not self.cmbProjectType.get_active_text():
			self.set_project_type_dropdown("DV/DVD NTSC")
		
	
	def get_profiles_list(self):
		
		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProjectType.append_text(p.description())
		
	def set_project_type_dropdown(self, item):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cmbProjectType.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)
			
			# check for the matching project type
			if item == value:			
				
				# set the item as active
				self.cmbProjectType.set_active_iter(iter)
				self.init_properties(value)
				break
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
				
		
	def on_cmbProjectType_changed(self, widget, *args):
		
		# init the project type properties
		self.init_properties(self.cmbProjectType.get_active_text())
		
		
	def init_properties(self, profile):
		
		# get correct gettext method
		_ = self._
		
		# get the mlt profile
		localType = profile 
		p = profiles.mlt_profiles(self.project).get_profile(localType)

		# populate the labels with values
		self.spnSizeHeight.set_text(str(p.height()))
		self.spnSizeWidth.set_text(str(p.width()))
		self.spnAspect1.set_text(str(p.display_aspect_num()))
		self.spnAspect2.set_text(str(p.display_aspect_den()))
		self.spnFrameRate1.set_text(str(p.frame_rate_num()))
		self.spnFrameRate2.set_text(str(p.frame_rate_den()))
		self.spnPixelRatio1.set_text(str(p.sample_aspect_num()))
		self.spnPixelRatio2.set_text(str(p.sample_aspect_den()))
			
		if p.progressive():
			self.chkProgressive.set_active(True)
		else:
			self.chkProgressive.set_active(False)
			
			
	def on_btnNew_clicked(self, widget, *args):
		#activate the spinbuttons etc.
		self.spnSizeHeight.set_sensitive(True)
		self.spnSizeWidth.set_sensitive(True)
		self.lblSize.set_sensitive(True)
		self.spnAspect1.set_sensitive(True)
		self.spnAspect2.set_sensitive(True)
		self.lblAspect.set_sensitive(True)
		self.spnPixelRatio1.set_sensitive(True)
		self.spnPixelRatio2.set_sensitive(True)
		self.lblPixel.set_sensitive(True)
		self.chkProgressive.set_sensitive(True)
		self.chkDefaultProfile.set_sensitive(True)
		self.txtProfileName.set_sensitive(True)
		self.lblProfile.set_sensitive(True)
		self.spnFrameRate1.set_sensitive(True)
		self.spnFrameRate2.set_sensitive(True)
		self.lblFrame.set_sensitive(True)
		self.btnSave.set_sensitive(True)
		
		#disable the drop down
		self.cmbProjectType.set_sensitive(False)
		
		self.txtProfileName.grab_focus()
		
		self.save_prompt = True
		
		
	def on_btnSave_clicked(self, widget, *args):
		
		file_name = self.txtProfileName.get_text()
		
		#first check if this name already exists in the 'preset' profiles
		#or USER_PROFILES_DIR
		if profiles.mlt_profiles(self.project).profile_exists(file_name):
			messagebox.show("Openshot", _("A profile with this name already exists. Please use another name."))
			return True
		else:
			self.save_profile()
		
		
	def save_profile(self):
		
		#check we have all the data populated
		if self.txtProfileName.get_text() == "":
			messagebox.show("Openshot Error!", _("Please enter a profile name."))
			self.txtProfileName.grab_focus()
			return
			
		if self.spnSizeHeight.get_text() == "0" or self.spnSizeWidth == "0":
			messagebox.show("Openshot Error!", _("Please enter a valid size."))
			return
		
		####create the profile file####
		filename = self.txtProfileName.get_text()
		if self.chkProgressive.get_active():
			progressive = '1'
		else:
			progressive = '0'
		f=open(os.path.join(self.project.USER_PROFILES_DIR, filename),'w')
		f.write("description=" + filename + '\n')
		f.write("frame_rate_num=" + self.spnFrameRate1.get_text() + '\n')
		f.write("frame_rate_den=" + self.spnFrameRate2.get_text() + '\n')
		f.write("width=" + self.spnSizeWidth.get_text() + '\n')
		f.write("height=" + self.spnSizeHeight.get_text() + '\n')
		f.write("progressive=" + progressive + '\n')
		f.write("sample_aspect_num=" + self.spnPixelRatio1.get_text() + '\n')
		f.write("sample_aspect_den=" + self.spnPixelRatio2.get_text() + '\n')
		f.write("display_aspect_num=" + self.spnAspect1.get_text() + '\n')
		f.write("display_aspect_den=" + self.spnAspect2.get_text() + '\n')
		f.close()
		
		# reload parent window's list of profiles
		self.parent.populate_profiles()
		
		#check for default profile
		if self.chkDefaultProfile.get_active():
			# change default profile
			self.parent.set_default_profile(filename)
		else:
			# re-select the default profile
			self.parent.set_default_profile(self.form.settings.general["default_profile"])
		
		#reactivate the drop down
		self.cmbProjectType.set_sensitive(False)
		
		self.btnSave.set_sensitive(False)
		
		#disable the spinbuttons
		self.spnSizeHeight.set_sensitive(False)
		self.spnSizeWidth.set_sensitive(False)
		self.lblSize.set_sensitive(False)
		self.spnAspect1.set_sensitive(False)
		self.spnAspect2.set_sensitive(False)
		self.lblAspect.set_sensitive(False)
		self.spnPixelRatio1.set_sensitive(False)
		self.spnPixelRatio2.set_sensitive(False)
		self.lblPixel.set_sensitive(False)
		self.chkProgressive.set_sensitive(False)
		self.chkDefaultProfile.set_sensitive(False)
		self.txtProfileName.set_sensitive(False)
		self.lblProfile.set_sensitive(False)
		self.spnFrameRate1.set_sensitive(False)
		self.spnFrameRate2.set_sensitive(False)
		self.lblFrame.set_sensitive(False)
		self.btnSave.set_sensitive(False)
		
		#enable the drop down
		self.cmbProjectType.set_sensitive(True)
		
		#add the newly saved profile to the combo
		self.cmbProjectType.append_text(filename)
		self.set_project_type_dropdown(filename)
		
		self.save_prompt = False
		
	def on_btnClose_clicked(self, widget, *args):
		
		if self.save_prompt == True:
			messagebox.show("Openshot", _("Do you want to save this profile?."), gtk.BUTTONS_YES_NO, self.save_profile, self.close_window)
		else:
			self.close_window()
			
	def on_btnDelete_clicked(self, widget, *args):
		
		# get correct gettext method
		_ = self._

		#get the active profile
		model = self.cmbProjectType.get_model()
		iter = self.cmbProjectType.get_active_iter()
		file_name = model.get_value(iter, 0)
		
		messagebox.show("Openshot", _("Are you sure you want to delete the profile %s?" % file_name), gtk.BUTTONS_YES_NO, self.delete_profile)
		
		
			
	def close_window(self):
		
		self.frmProfiles.destroy()
		
	def delete_profile(self):
		
		#get the active profile
		model = self.cmbProjectType.get_model()
		iter = self.cmbProjectType.get_active_iter()
		file_name = model.get_value(iter, 0)

		if os.path.exists(os.path.join(self.project.USER_PROFILES_DIR, file_name)):
			os.remove(os.path.join(self.project.USER_PROFILES_DIR, file_name))
			#clear the combo & repopulate
			model.clear()	
			self.get_profiles_list()
			
			#set the default profile
			self.set_project_type_dropdown(self.form.settings.general["default_profile"])
			if not self.cmbProjectType.get_active_text():
				self.set_project_type_dropdown("DV/DVD NTSC")
				self.parent.set_default_profile("DV/DVD NTSC")

			# reload parent window's list of profiles
			self.parent.populate_profiles()
			
			# re-select the default profile
			self.parent.set_default_profile(self.form.settings.general["default_profile"])
			
		else:
			messagebox.show("Openshot Error!", _("The profile %s cannot be deleted." % file_name))
	
			
	def on_btnImport_clicked(self, widget, *args):
				
		file_open = gtk.FileChooserDialog(title="Select Profile"
					, action=gtk.FILE_CHOOSER_ACTION_OPEN
					, buttons=(gtk.STOCK_CANCEL
								, gtk.RESPONSE_CANCEL
								, gtk.STOCK_OPEN
								, gtk.RESPONSE_OK))
		#add the file filters
		filter = gtk.FileFilter()
		filter.set_name("tar archives")
		filter.add_pattern("*.tar.gz")
		filter.add_pattern("*.tar.bz2")
		file_open.add_filter(filter)
		#add the 'all files' filter"""
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		file_open.add_filter(filter)
		
		if file_open.run() == gtk.RESPONSE_OK:
			file_name = file_open.get_filename()
			
			(dirName, filename) = os.path.split(file_name)
			(fileBaseName, fileExtension)=os.path.splitext(filename)
		
			if ".bz2" in fileExtension or ".gz" in fileExtension:
				#extract the file(s)
				try:
					tar = tarfile.open(file_name)
					tar.extractall(self.project.USER_PROFILES_DIR)
					tar.close()
					messagebox.show("Openshot", _("The profile has been successfully imported."))
				except:
					messagebox.show("Openshot Error!", _("There was an error extracting the file %s" % filename))
					
				
				
			else:
				#regular file - just copy it to the user profiles folder
				# get file name, path, and extention
				
				try:
					shutil.copyfile(file_name, os.path.join(self.project.USER_PROFILES_DIR, fileBaseName))
					messagebox.show("Openshot", _("The profile has been successfully imported."))
				except:
					messagebox.show("Openshot Error!", _("There was an error copying the file %s" % filename))	
					
			#add the new profile to the dropdown
			#clear the combo & repopulate - we can't just add the filename if it was a tar.gz
			model = self.cmbProjectType.get_model()
			model.clear()	
			self.get_profiles_list()
			#set the default profile
			self.set_project_type_dropdown(fileBaseName)
				
		file_open.destroy()
			
			
		
def main():
	frm_profiles = frmProfilesManager()
	frm_profiles.run()

if __name__ == "__main__":
	main()

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
import xml.dom.minidom as xml

from classes import profiles, project, messagebox, tree
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from xdg.IconTheme import *

# init the foriegn language
import language.Language_Init as Language_Init

class PreferencesMgr(SimpleGtkBuilderApp):
	
	
	def __init__(self, path="Preferences.ui", root="frmPreferences", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.project = project
		self.form = form

		if getIconPath("openshot"):
			self.frmPreferences.set_icon_from_file(getIconPath("openshot"))
		
		#populate the profiles dropdown
		self.populate_profiles()

		#populate the themes
		for dir in os.listdir(self.project.THEMES_DIR):
			self.cmbThemes.append_text(dir)
		
		# populate output mode combo
		for output_mode in ["sdl", "sdl_preview"]:
			self.cmbOutputModes.append_text(output_mode)
			
		# populate scrolling options
		for use_stock in [_("Yes"), _("No")]:
			self.cmbSmoothScrolling.append_text(use_stock)
			
		# populate icon size options
		for icon_size in [_("Small"), _("Medium")]:
			self.cmbIconSize.append_text(icon_size)
			
		# disable scrolling options (based on MLT version)
		if self.form.MyVideo:
			if self.form.MyVideo.check_version(0, 6, 0):
				self.cmbSmoothScrolling.set_sensitive(True)
			else:
				self.cmbSmoothScrolling.set_sensitive(False)

		# populate stock icons combo
		for use_stock in [_("Yes"), _("No")]:
			self.cmbUseStockIcons.append_text(use_stock)

			
		#populate the codecs & formats
		self.VCodecList = gtk.ListStore(str)
		self.tvVCodecs.set_model(self.VCodecList)
		tree.treeviewAddGeneralTextColumn(self.tvVCodecs,_('Video Codecs'),0)
		
		self.ACodecList = gtk.ListStore(str)
		self.tvACodecs.set_model(self.ACodecList)
		tree.treeviewAddGeneralTextColumn(self.tvACodecs,_('Audio Codecs'),0)
		
		self.FormatsList = gtk.ListStore(str)
		self.tvFormats.set_model(self.FormatsList)
		tree.treeviewAddGeneralTextColumn(self.tvFormats,_('Formats'),0)	
		self.populate_codecs()
		
			
		#populate form objects
		self.valImageLength.set_value(float(self.form.settings.general["imported_image_length"].replace(",",".")))
		self.valHistoryStackSize.set_value(float(self.form.settings.general["max_history_size"]))
		self.txtMeltCommandName.set_text(self.form.settings.general["melt_command"])
		self.txtBlenderCommand.set_text(self.form.settings.general["blender_command"])
		theme_name = self.form.settings.general["default_theme"]
		self.set_dropdown_values(theme_name, self.cmbThemes)
		self.set_dropdown_values(self.form.settings.general["output_mode"], self.cmbOutputModes)
		
		# Init stock dropdown
		use_stock_icons = self.form.settings.general["use_stock_icons"]
		if use_stock_icons == "Yes":
			self.set_dropdown_values(_("Yes"), self.cmbUseStockIcons)
		else:
			self.set_dropdown_values(_("No"), self.cmbUseStockIcons)
		
		# Init smooth scrolling dropdown
		use_affine = self.form.settings.general["use_affine"]
		if use_affine == "Yes":
			self.set_dropdown_values(_("Yes"), self.cmbSmoothScrolling)
		else:
			self.set_dropdown_values(_("No"), self.cmbSmoothScrolling)
		
		# Init icon size dropdown
		icon_size = self.form.settings.general["icon_size"]
		if icon_size == "small":
			self.set_dropdown_values(_("Small"), self.cmbIconSize)
		else:
			self.set_dropdown_values(_("Medium"), self.cmbIconSize)
		
		#autosave objects
		if self.form.settings.general["autosave_enabled"] == "True":
			self.chkEnableAutosave.set_active(True)
		else:
			self.chkEnableAutosave.set_active(False)
		self.chkEnableAutosave.toggled()
		
		if self.form.settings.general["save_before_playback"] == "True":
			self.chkSaveBeforePlayback.set_active(True)
		else:
			self.chkSaveBeforePlayback.set_active(False)
		self.chkSaveBeforePlayback.toggled()
		
		self.valSaveInterval.set_value(int(self.form.settings.general["save_interval"]))
		
		#show the form
		self.frmPreferences.show_all()
		
	def set_default_profile(self, profile_name):
		# set the selected profile
		self.set_dropdown_values(profile_name, self.cmbProfiles)
		
	def populate_profiles(self):

		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		self.liststore2.clear()
		#self.cmbProfiles.clear()
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProfiles.append_text(str(file_name))
			
		# re-select default profile
		self.set_default_profile(self.form.settings.general["default_profile"])
		if not self.cmbProfiles.get_active_text():
			self.set_default_profile("DV/DVD NTSC")
			
		
	def populate_codecs(self):
		
		#populate the codecs
		
		#video codecs		
		for codec in self.form.vcodecs:
			self.VCodecList.append([codec])
		
		#audio codecs
		for acodec in self.form.acodecs:
			self.ACodecList.append([acodec])
		
		#formats
		for format in self.form.vformats:
			self.FormatsList.append([format])
			
	
	def on_btnReload_clicked(self, widget, *args):
		
		#clear the codecs from the form object
		#and repopulate the listviews
		
		self.VCodecList.clear()
		self.ACodecList.clear()
		self.FormatsList.clear()
		
		self.form.vcodecs[:] = []
		self.form.acodecs[:] = []
		self.form.vformats[:] = []
		
		melt_command = self.form.settings.general["melt_command"]
		self.form.get_avformats(melt_command)

		self.populate_codecs()
		

		
		
	def on_btnClose_clicked(self, widget, *args):
		#write the values from the form to the dictionary objects
		self.form.settings.general["imported_image_length"] = self.valImageLength.get_text().replace(",",".")
		self.form.settings.general["default_theme"] = self.cmbThemes.get_active_text()
		self.form.settings.general["default_profile"] = self.cmbProfiles.get_active_text()
		self.form.settings.general["melt_command"] = self.txtMeltCommandName.get_text()
		self.form.settings.general["blender_command"] = self.txtBlenderCommand.get_text()
		self.form.settings.general["output_mode"] = self.cmbOutputModes.get_active_text()

		# save settings
		self.form.settings.save_settings_to_xml()
		
		# close the window
		self.frmPreferences.destroy()
		
	def on_valImageLength_value_changed(self, widget, *args):
		self.form.settings.general["imported_image_length"] = self.valImageLength.get_text().replace(",",".")
		
	def on_cmbProfiles_changed(self, widget, *args):
		self.form.settings.general["default_profile"] = self.cmbProfiles.get_active_text()
		
	def on_valHistoryStackSize_value_changed(self, widget, *args):
		self.form.settings.general["max_history_size"] = self.valHistoryStackSize.get_value_as_int()
		
	def on_txtMeltCommandName_focus_out_event(self, widget, *args):
		self.form.settings.general["melt_command"] = self.txtMeltCommandName.get_text()
		
	def on_txtBlenderCommand_focus_out_event(self, widget, *args):
		self.form.settings.general["blender_command"] = self.txtBlenderCommand.get_text()
		
	def on_cmbOutputModes_changed(self, widget, *args):
		self.form.settings.general["output_mode"] = self.cmbOutputModes.get_active_text()
		
	def on_cmbUseStockIcons_changed(self, widget, *args):
		
		_ = self._
		use_stock_icons = self.cmbUseStockIcons.get_active_text()
		
		if use_stock_icons == _("Yes"):
			self.form.settings.general["use_stock_icons"] = "Yes"
		else:
			self.form.settings.general["use_stock_icons"] = "No"
			
		# update theme on main form
		self.form.update_icon_theme()
		
	def on_cmbSmoothScrolling_changed(self, widget, *args):
		
		_ = self._
		use_affine = self.cmbSmoothScrolling.get_active_text()
		
		if use_affine == _("Yes"):
			self.form.settings.general["use_affine"] = "Yes"
		else:
			self.form.settings.general["use_affine"] = "No"
			
	def on_cmbIconSize_changed(self, widget, *args):
		
		_ = self._
		icon_size = self.cmbIconSize.get_active_text()
		
		if icon_size == _("Small"):
			self.form.settings.general["icon_size"] = "small"
		else:
			self.form.settings.general["icon_size"] = "medium"
			
		# refresh effects and transitions
		self.form.on_btnTransFilterAll_toggled(widget)
		self.form.on_btnAllEffects_toggled(widget)


	def on_cmbThemes_changed(self, widget, *args):
		
		self.form.settings.general["default_theme"] = self.cmbThemes.get_active_text()
		
		#reload the theme example image
		theme_name = self.cmbThemes.get_active_text()
		
		# update theme on main form
		self.form.project.set_theme(theme_name)
		self.form.update_icon_theme()
		self.form.refresh()


	def on_btnManageProfiles_clicked(self, widget, *args):
		print "on_btnManageProfiles_clicked"
		from windows import Profiles
		Profiles.frmProfilesManager(form=self.form, parent=self, project=self.project)
		
	def on_valSaveInterval_value_changed(self, widget, *args):
		self.form.settings.general["save_interval"] = self.valSaveInterval.get_value_as_int()

		# reload these settings on main form
		self.form.load_autosave_settings()
		
	def on_chkEnableAutosave_toggled(self, widget, *args):
		state = self.chkEnableAutosave.get_active()
		self.form.settings.general["autosave_enabled"] = str(state)
		if state == False:
			self.chkSaveBeforePlayback.set_sensitive(False)
			self.valSaveInterval.set_sensitive(False)
		else:
			self.chkSaveBeforePlayback.set_sensitive(True)
			self.valSaveInterval.set_sensitive(True)
		
		# either start or stop the auto interval thread (depending on the value of the preference)
		self.form.setup_autosave()
		
		# reload these settings on main form
		self.form.load_autosave_settings()
		
	def on_chkSaveBeforePlayback_toggled(self, widget, *args):
		state = self.chkSaveBeforePlayback.get_active()
		self.form.settings.general["save_before_playback"] = str(self.chkSaveBeforePlayback.get_active())
		if state == False:
			self.form.save_before_playback = True
		else:
			self.form.save_before_playback = False
			
		# reload these settings on main form
		self.form.load_autosave_settings()
			
	
	def set_dropdown_values(self, value_to_set, combobox):
		
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
			if iter is None:
				break
			
	
				

class Settings:
	#set some initial values.
	#The first time Openshot is run, the settings file won't exist,
	#so use these default values.
	#When the settings are loaded from the config file, these default
	#values will be overwritten with the file values.
	general = {
		"imported_image_length" : "7",
		"default_theme" : "fresher",
		"default_profile" : "DV/DVD NTSC",
		"project_file_type" : "ascii",
		"max_history_size" : "20",
		"melt_command" : "melt",
		"blender_command" : "blender",
		"output_mode" : "sdl",
		"use_stock_icons" : "Yes",
		"use_affine" : "No",
		"save_interval" : 1,
		"autosave_enabled" : False,
		"save_before_playback" : False,
		"icon_size" : "medium",
		}
	
	app_state = {
		"window_height" : "710",
		"window_width" : "900",
		"window_maximized" : "False",
		"import_folder" : "None",
		"toolbar_visible" : "True",
		"history_visible" : "False",
		"vpane_position" : "370",
		"hpane_position" : "450",
		"clip_property_window_width" : "775",
		"clip_property_window_height" : "345",
		"clip_property_window_maximized" : "False",
		"clip_property_hpane_position" : "260",
		"upload_service" : "YouTube",
		"upload_username" : "",
		"vimeo_token" : "",
		"vimeo_token_secret" : "",
		"vimeo_verifier" : "",
		}
	
	sections = {
		"general" : general,
		"app_state" : app_state
		
		}
	
	def __init__(self, project):
		"""Constructor"""
		
		# Add language support
		translator = Language_Init.Translator(project)
		_ = translator.lang.gettext
		self._ = _
		
		self.project = project
	
	def load_settings_from_xml(self):
		settings_path = os.path.join(self.project.USER_DIR, "config.xml")
		
		#Load the settings from the config file, if it exists
		if os.path.exists(settings_path):
			
			try:
				xmldoc = xml.parse(settings_path)
			except xml.xml.parsers.expat.ExpatError:
				# Invalid or empty config file
				self.save_settings_to_xml()
				return
			#loop through each settings section and load the values
			#into the relevant dictionary
			for section, section_dict in self.sections.iteritems():
				for key, value in section_dict.iteritems():
					try:
						element = xmldoc.getElementsByTagName(key)
						section_dict[key] = element[0].childNodes[0].data
						
						# be sure theme exists
						if key == "default_theme":
							if os.path.exists(os.path.join(self.project.THEMES_DIR, section_dict[key])) == False:
								# DOES NOT EXIST, change to default
								section_dict[key] = "blue_glass"
								
						# be sure profile exists
						if key == "default_profile":
							if profiles.mlt_profiles(self.project).profile_exists(section_dict[key]) == False:
								# DOES NOT EXIST, change to default
								print "Default profile does not exist: %s. Changing default profile to %s." % (section_dict[key], "DV/DVD NTSC")
								section_dict[key] = "DV/DVD NTSC"
						
					except IndexError:
						#the list index will go out of range if there is
						#an extra item in the dictionary which is
						#not in the config file.
						pass
		
		else:
			# no config file found, create one
			self.save_settings_to_xml()
			
	def save_settings_to_xml(self):
		settings_path = os.path.join(self.project.USER_DIR, "config.xml")
		
		#update each xml element with the current dictionary values
		if os.path.exists(settings_path):
			try:
				xmldoc = xml.parse(settings_path)
			except xml.xml.parsers.expat.ExpatError:
				# Invalid or empty config file, create new blank dom
				messagebox.show(_("OpenShot Warning"), _("Invalid or empty preferences file found, loaded default values"))
				xmldoc = xml.Document()
				root_node = xmldoc.createElement("settings")
				xmldoc.appendChild(root_node)
				
				# create a node for each section
				for section, section_dict in self.sections.iteritems():
					section_node = xmldoc.createElement(section)
					root_node.appendChild(section_node)
		else:
			# missing config file, create new blank dom
			xmldoc = xml.Document()
			root_node = xmldoc.createElement("settings")
			xmldoc.appendChild(root_node)
			
			# create a node for each section
			for section, section_dict in self.sections.iteritems():
				section_node = xmldoc.createElement(section)
				root_node.appendChild(section_node)
				
		
		for section, section_dict in self.sections.iteritems():
			for key, value in section_dict.iteritems():
				try:
					element = xmldoc.getElementsByTagName(key)
					if element:
						# does text node exist?
						if not element[0].childNodes:
							txt = xmldoc.createTextNode(str(value))
							element[0].appendChild(txt)
						else:
							# update existing text node
							element[0].childNodes[0].data = str(section_dict[key])
					else:
						#there is no matching element in the xml, 
						#we need to add one
						new_element = xmldoc.createElement(key)
						parent = xmldoc.getElementsByTagName(section)
						parent[0].appendChild(new_element)
						txt = xmldoc.createTextNode(str(value))
						new_element.appendChild(txt)
						
				except IndexError:
					pass
	
		# save settings
		self.write_to_settings_file(xmldoc)
			
			
			
			
					
	def write_to_settings_file(self, xmldoc):
		#write the updated xml document to the config file
		filename = os.path.join(self.project.USER_DIR, "config.xml")
		
		try:
			file = open(filename, "wb") 
			file.write(xmldoc.toxml("UTF-8"))
			#xmldoc.writexml(file, indent='', addindent='    ', newl='', encoding='UTF-8')
			file.close()
		except IOError, inst:
			messagebox.show(_("OpenShot Error"), _("Unexpected Error '%s' while writing to '%s'." % (inst, filename)))
		
		
def main():
	frm_prefs = PreferencesMgr()
	frm_titles.run()

if __name__ == "__main__":
	main()

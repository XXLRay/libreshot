#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas, TJ
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

import os, sys, locale
import gtk, re
import xml.dom.minidom as xml
from classes import profiles, files, thumbnail, open_project, save_project, state_project, restore_state, sequences, video, theme

# init the foreign language
from language import Language_Init

########################################################################
class project():
	"""This is the main project class that contains all
	the details of a project, such as name, folder, timeline
	information, sequences, media files, etc..."""

	#----------------------------------------------------------------------
	def __init__(self, init_threads=True):
		"""Constructor"""
		
		# debug message/function control
		self.DEBUG = True
		
		# define common directories containing resources
		# get the base directory of the libreshot installation for all future relative references
		# Note: don't rely on __file__ to be an absolute path. E.g., in the debugger (pdb) it will be
		# a relative path, so use os.path.abspath()
		self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		self.UI_DIR = os.path.join(self.BASE_DIR, "libreshot", "windows", "ui")
		self.IMAGE_DIR = os.path.join(self.BASE_DIR, "libreshot", "images")
		self.LOCALE_DIR = os.path.join(self.BASE_DIR, "libreshot", "locale")
		self.PROFILES_DIR = os.path.join(self.BASE_DIR, "libreshot", "profiles")
		self.TRANSITIONS_DIR = os.path.join(self.BASE_DIR, "libreshot", "transitions")
		self.BLENDER_DIR = os.path.join(self.BASE_DIR, "libreshot", "blender")
		self.EXPORT_PRESETS_DIR = os.path.join(self.BASE_DIR, "libreshot", "export_presets")
		self.EFFECTS_DIR = os.path.join(self.BASE_DIR, "libreshot", "effects")
		# location for per-session, per-user, files to be written/read to
		self.DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
		self.USER_DIR = os.path.join(os.path.expanduser("~"), ".libreshot")
		self.THEMES_DIR = os.path.join(self.BASE_DIR, "libreshot", "themes")
		self.USER_PROFILES_DIR = os.path.join(self.USER_DIR, "user_profiles")
		self.USER_TRANSITIONS_DIR = os.path.join(self.USER_DIR, "user_transitions")
		

		# only run the following code if we are really using 
		# this project file... 
		if init_threads:

			# Add language support
			translator = Language_Init.Translator(self)
			_ = translator.lang.gettext
			
			# init the variables for the project
			from windows import preferences
			self.name = _("Default Project")
			self.folder = self.USER_DIR
			self.project_type = preferences.Settings.general["default_profile"]
			self.canvas = None
			self.is_modified = False
			self.refresh_xml = True
			self.mlt_profile = None
			
			# set theme
			self.set_theme(preferences.Settings.general["default_theme"])
			
			# reference to the main GTK form
			self.form = None
			
			# init the file / folder list (used to populate the tree)
			self.project_folder = files.LibreShotFolder(self)
	
			# ini the sequences collection
			self.sequences = [sequences.sequence(_("Default Sequence 1"), self)]		
	
			# init the tab collection
			self.tabs = [self.sequences[0]]	  # holds a refernce to the sequences, and the order of the tabs
	
			# clear temp folder
			self.clear_temp_folder()
			
			# create thumbnailer object
			self.thumbnailer = thumbnail.thumbnailer()
			self.thumbnailer.set_project(self)
			self.thumbnailer.start()
			
	def set_theme(self, folder_name):
		""" Set the current theme and theme settings """

		# Set the theme, and load the theme settings
		self.theme = folder_name
		self.theme_settings = theme.theme(folder_name=self.theme, project=self)
		
		# check for empty theme settings (and use blue_glass instead if needed)
		if not self.theme_settings.settings:
			self.theme = "blue_glass"
			self.theme_settings = theme.theme(folder_name=self.theme, project=self)
		
		
	def fps(self):
		# get the profile object
		if self.mlt_profile == None:
			self.mlt_profile = profiles.mlt_profiles(self).get_profile(self.project_type)

		# return the frames per second
		return self.mlt_profile.fps()
	
	

	def clear_temp_folder(self):
		"""This method deletes all files in the /libreshot/temp folder."""
		path = os.path.join(self.USER_DIR)
		
		# get pid from lock file
		pidPath = os.path.join(path, "pid.lock")
		f = open(pidPath, 'r')
		pid=int(f.read().strip())
		f.close()
		
		# list of folders that should not be deleted
		safe_folders = ["blender", "queue", "user_profiles", "user_transitions"]
		
		# loop through all folders in the USER_DIR
		for child_path in os.listdir(path):
			if os.path.isdir(os.path.join(path, child_path)):
				if child_path not in safe_folders:
					# clear all files / folders recursively in the thumbnail folder
					if os.getpid() == pid:

						# only clear this folder for the primary instance of LibreShot
						self.remove_files(os.path.join(path, child_path))
						
						# remove folder
						os.removedirs(os.path.join(path, child_path))
		
		# thumbnail path
		thumbnail_path = os.path.join(path, "thumbnail")
		
		# create thumbnail folder (if it doesn't exist)
		if os.path.exists(thumbnail_path) == False:
			# create new thumbnail folder
			os.mkdir(thumbnail_path)


	def remove_files(self, path):

		# verify this folder exists
		if os.path.exists(path):
			
			# loop through all files in this folder
			for child_path in os.listdir(path):
				# get full child path
				child_path_full = os.path.join(path, child_path)
				
				if os.path.isdir(child_path_full) == True:
					# remove items in this folder
					self.remove_files(child_path_full)
					
					# remove folder
					os.removedirs(child_path_full)
				else:
					# remove file
					os.remove(child_path_full)
			
			
	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an LibreShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of the old project class, to make old project files compatable with
		    newer versions of LibreShot. """
	
		# Check for missing DEBUG attribute (which means it's an old project format)
		#if 'DEBUG' not in state:
		# create empty new project class
		empty_project = project(init_threads=False)
		
		state['DEBUG'] = empty_project.DEBUG
		state['BASE_DIR'] = empty_project.BASE_DIR
		state['UI_DIR'] = empty_project.UI_DIR
		state['IMAGE_DIR'] = empty_project.IMAGE_DIR
		state['LOCALE_DIR'] = empty_project.LOCALE_DIR
		state['PROFILES_DIR'] = empty_project.PROFILES_DIR
		state['TRANSITIONS_DIR'] = empty_project.TRANSITIONS_DIR
		state['BLENDER_DIR'] = empty_project.BLENDER_DIR
		state['EXPORT_PRESETS_DIR'] = empty_project.EXPORT_PRESETS_DIR
		state['EFFECTS_DIR'] = empty_project.EFFECTS_DIR
		state['USER_DIR'] = empty_project.USER_DIR
		state['DESKTOP'] = empty_project.DESKTOP
		state['THEMES_DIR'] = empty_project.THEMES_DIR
		state['USER_PROFILES_DIR'] = empty_project.USER_PROFILES_DIR
		state['USER_TRANSITIONS_DIR'] = empty_project.USER_TRANSITIONS_DIR
		state['refresh_xml'] = True
		state['mlt_profile'] = None

		empty_project = None

		# update the state object with new schema changes
		self.__dict__.update(state)


	#----------------------------------------------------------------------
	def Render(self):
		"""This method recursively renders all the tracks and clips on the timeline"""
		
		# Render the timeline
		self.sequences[0].Render()
		
		# Render Play Head (and position line)
		self.sequences[0].RenderPlayHead()
		
		
	def GenerateXML(self, file_name):
		"""This method creates the MLT XML used by LibreShot"""
		
		# get locale info
		lc, encoding = locale.getdefaultlocale()

		# Create the XML document
		dom = xml.Document()
		dom.encoding = encoding

		# Add the root element
		westley_root = dom.createElement("mlt")
		dom.appendChild(westley_root)
		if self.mlt_profile:
			profile = dom.createElement("profile")
			profile.setAttribute("description", self.mlt_profile.description())
			profile.setAttribute("width", str(self.mlt_profile.width()))
			profile.setAttribute("height", str(self.mlt_profile.height()))
			profile.setAttribute("sample_aspect_num", str(self.mlt_profile.sample_aspect_num()))
			profile.setAttribute("sample_aspect_den", str(self.mlt_profile.sample_aspect_den()))
			profile.setAttribute("display_aspect_num", str(self.mlt_profile.display_aspect_num()))
			profile.setAttribute("display_aspect_den", str(self.mlt_profile.display_aspect_den()))
			profile.setAttribute("progressive", self.mlt_profile.progressive() and "1" or "0")
			profile.setAttribute("frame_rate_num", str(self.mlt_profile.frame_rate_num()))
			profile.setAttribute("frame_rate_den", str(self.mlt_profile.frame_rate_den()))
			westley_root.appendChild(profile)
		tractor1 = dom.createElement("tractor")
		tractor1.setAttribute("id", "tractor0")
		westley_root.appendChild(tractor1)
		
		# Add all the other timeline objects (such as sequences, clips, filters, and transitions)
		self.sequences[0].GenerateXML(dom, tractor1)
		
		# Pretty print using a Regular expression (I am using regex due to a bug in the minidom, with extra 
		# whitespace in it's pretty print method.  This should fix the pretty print's white space issue.)
		pretty_print = re.compile(r'((?<=>)(\n[\t]*)(?=[^<\t]))|((?<=[^>\t])(\n[\t]*)(?=<))')
		pretty_print_output = re.sub(pretty_print, '', dom.toprettyxml())

		# Save the XML dom
		f = open(file_name, "w")
		f.write(pretty_print_output)
		f.close()
		
		# reset project as NOT modified
		self.refresh_xml = False


	#----------------------------------------------------------------------
	def RefreshXML(self):
		""" Generate a new MLT XML file (if needed).  This only creates a
		new XML file if the timeline has changed. """
		
		# has the project timeline been modified (i.e. new clips, re-arranged clips, etc...)
		if self.refresh_xml:
			
			# update cursor to "wait"
			self.form.timelinewindowRight.window.set_cursor(gtk.gdk.Cursor(150))
			self.form.timelinewindowRight.window.set_cursor(gtk.gdk.Cursor(150))
			
			# generate a new MLT XML file
			self.GenerateXML(os.path.join(self.USER_DIR, "sequence.mlt"))

			# ****************************
			# re-load the xml
			if self.form.MyVideo:
				
				# Autosave the project (based on the user's preferences, and if the project needs
				# to be saved.
				if self.form.autosave_enabled and self.form.save_before_playback:
					print "Autosaving... before playback of new XML file."
					self.form.auto_save()
				
				# store current frame position
				prev_position = self.form.MyVideo.position()

				self.form.MyVideo.set_project(self, self.form, os.path.join(self.USER_DIR, "sequence.mlt"), mode="preview")
				self.form.MyVideo.load_xml()

				# restore position
				self.form.MyVideo.seek(prev_position)

			else:
				# create the video thread
				# Force SDL to write on our drawing area
				os.putenv('SDL_WINDOWID', str(self.form.videoscreen.window.xid))
				
				# We need to flush the XLib event loop otherwise we can't
				# access the XWindow which set_mode() requires
				gtk.gdk.flush()

				# play the video in it's own thread
				self.form.MyVideo = video.player(self, self.form, os.path.join(self.USER_DIR, "sequence.mlt"), mode="preview")
				self.form.MyVideo.start()
			# ****************************
			
			# update cursor to normal
			self.form.timelinewindowRight.window.set_cursor(None)
			
		else:
			pass

	
	#----------------------------------------------------------------------
	def Save(self, file_path):
		"""Call the save method of this project, which will 
		persist the project to the file system."""
		
		# get preferences to see whether to save in binary or ascii form
		from windows import preferences
		self.file_type = "ascii"
		
		# call the save method
		save_project.save_project(self, file_path)
		
	#----------------------------------------------------------------------
	def Open(self, file_path):
		"""Call the open method, which will open an existing
		project file from the file system."""
			
		# call the open method
		open_project.open_project(self, file_path)
		self.set_project_modified(is_modified=True, refresh_xml=False, type=_("Opened project"))	

		
	def set_project_modified(self, is_modified=False, refresh_xml=False, type=None):
		"""Set the modified status and accordingly the save button sensitivity"""
		self.is_modified = is_modified
		self.refresh_xml = refresh_xml

		if is_modified == True:
			self.form.tlbSave.set_sensitive(True)

			# Save state for UNDO / REDO
			if type:
				self.form.save_project_state(type)
				
		else:
			self.form.tlbSave.set_sensitive(False)
			
	
	def State(self):
		state = state_project.save_state(self)
		return state
	state = property(State)
	
	
	def restore(self, state):
		
		# Restore State
		restore_state.restore_project_state(self, state)
		
	def translate(self, text):
		""" Translate any string to the current locale. """
		return self.form.translate(text)
				
		

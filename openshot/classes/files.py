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

from classes import messagebox
import os, sys, urllib, uuid, re, glob
import gtk

# init the foreign language
from language import Language_Init

########################################################################
class OpenShotFile:
	"""The generic file object for OpenShot"""

	#----------------------------------------------------------------------
	def __init__(self, project=None):
		self.project = project
		
		"""Constructor"""
		
		# Add language support
		translator = Language_Init.Translator(self.project)
		_ = translator.lang.gettext

		# init the variables for the File Object
		self.name = ""			# short / friendly name of the file
		self.length = 0.0		# length in seconds
		self.videorate = (30,0)	# audio rate or video framerate
		self.file_type = ""		# video, audio, image, image sequence
		self.max_frames = 0.0
		self.fps = 0.0
		self.height = 0
		self.width = 0
		self.label = ""			 # user description of the file
		self.thumb_location = "" # file uri of preview thumbnail
		self.ttl = 1			 # time-to-live - only used for image sequence.  Represents the # of frames per image.
		
		self.unique_id = str(uuid.uuid1())	
		self.parent = None
		self.project = project	  # reference to project
		
		self.video_codec = ""
		self.audio_codec = ""
		self.audio_frequency = ""
		self.audio_channels = ""
		
		
	def get_thumbnail(self, width, height):
		"""Get and resize the pixbuf thumbnail for a file"""	
		
		# get the thumbnail (or load default)
		try:
			if self.thumb_location:
				pbThumb = gtk.gdk.pixbuf_new_from_file(self.thumb_location)
				pbThumb = pbThumb.add_alpha(False, 255, 255, 255)
				
				# Mask the corner of the thumbnail image (for a nice rounding effect)
				corner_mask = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, 'thumbnail_mask.png'))
				corner_mask.composite(pbThumb, 
								0, 
								0, 
								320, 
								240, 
								0, 
								0, 
								1.0, 
								1.0, 
								gtk.gdk.INTERP_NEAREST, 
								255)

				# replace corner with transparency
				pbThumb = pbThumb.add_alpha(True, 255, 0, 202)


			else:
				# Load the No Thumbnail Picture
				if self.file_type == "audio":
					pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "AudioThumbnail.png"))
				else:
					pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "NoThumbnail.png"))
		except:

				# Load the No Thumbnail Picture
				if self.file_type == "audio":
					pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "AudioThumbnail.png"))
				else:
					pbThumb = gtk.gdk.pixbuf_new_from_file(os.path.join(self.project.IMAGE_DIR, "NoThumbnail.png"))

		# resize thumbnail
		return pbThumb.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)	
		
	def update_thumbnail(self):
	
		# Initialize variables
		project = self.project
		thumbnailer = project.thumbnailer
		file_type = self.file_type
		
		# Audio files have a common thumbnail
		if not file_type == "audio":	
		
			# Split the file name
			(dir_name, file_name) = os.path.split(self.name)
			(file_base_name, ext) = os.path.splitext(file_name)
			ext = ext.replace(".", "")
			
			# The shortened path to the thumbnail
			new_name = "thumbnail/" + file_base_name + "_" + ext + "_1.png"
			
			# Create the new thumbnail
			thumbnailer.get_thumb_at_frame(self.name, new_name=new_name, full_size=False)

########################################################################
class OpenShotFolder:
	"""The generic folder object for OpenShot"""

	#----------------------------------------------------------------------
	def __init__(self, project=None):
		"""Constructor"""
		
		# Init the variables for the Folder Object
		self.name = ""		  # short / friendly name of the folder
		self.location = ""	  # file system location
		self.parent = None
		self.project = project
		
		self.label = ""		  # user description of the folder
		self.unique_id = str(uuid.uuid1())

		# init the list of files & folders
		# this list can contain OpenShotFolder or OpenShotFile objects
		# the order of this list determines the order of the tree items
		self.items = []
		
		# this queue holds files that are currently being added. this prevents
		# duplicate files to be added at the same time
		self.queue = []


	#----------------------------------------------------------------------
	def AddFolder(self, folder_name, project=None):
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		"""Add a new folder to the current folder"""
		#does this folder name already exist?
		if self.FindFolder(folder_name):
			messagebox.show(_("OpenShot Error"), _("The folder %s already exists in this project." % folder_name))
			return
		newFolder = OpenShotFolder(project)		
		newFolder.name = folder_name
		
		self.items.append(newFolder)
		
		#set the modified status
		self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added folder"))
		
		self.project.form.refresh_files()
		

	#----------------------------------------------------------------------
	def AddFile(self, file_name, session=None, ignore_image_sequences=False):
		"""Add a new file to the current folder"""
		"""
		Returns a tuple: 
		(The number of files that could be successfully imported (not including folders),
		The number of files that could not be imported (wrong format),
		The number of files already imported to the project,
		The number of folders selected (0 or 1))
		"""
		
		import urllib
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		# clean path to file
		file_name = urllib.unquote(file_name)
		newFile = None
		
		# The number of ok files (not counting folders)
		ok_files = 0
		# The number of files that couldn't be read (wrong format)
		broken_files = 0
		# The number of duplicates in the project
		duplicate_files = 0
		# The number of folders submitted (0 or 1)
		folders = 0
			
		# check if the path is a 'folder' and not a file
		if os.path.isdir(file_name):
			
			folders += 1
			
			# loop through each sub-file (if any)
			for sub_file in os.listdir(file_name):
				sub_file_path = os.path.join(file_name, sub_file)
				
				# only add files
				if os.path.isfile(sub_file_path):
					
					# don't add a file that is already in the project (i.e. dupe check)
					if self.file_exists_in_project(sub_file_path) == False:

						# inspect the media file and generate it's thumbnail image (if any)
						newFile = self.project.thumbnailer.GetFile(sub_file_path)
					
						# add to internal item collection
						if newFile:
							ok_files += 1
							self.items.append(newFile)
						else:
							broken_files += 1
					else:
						duplicate_files += 1

		else:
		
			# don't add a file that is already in this folder (i.e. dupe check)
			if self.file_exists_in_project(file_name):
				duplicate_files += 1
				return (ok_files, broken_files, duplicate_files, folders)
			
			# should we ignore image sequence check?
			if ignore_image_sequences:
				
				# inspect the media file and generate it's thumbnail image (if any)
				newFile = self.project.thumbnailer.GetFile(file_name)
				
				# add to internal item collection
				if newFile:
					ok_files += 1
					self.items.append(newFile)
				else:
					broken_files += 1

			# determine if this is an image sequence
			elif not self.GetImageSequenceDetails(file_name, session):
			
				# inspect the media file and generate it's thumbnail image (if any)
				newFile = self.project.thumbnailer.GetFile(file_name)
			
				# add to internal item collection
				if newFile:
					ok_files += 1
					self.items.append(newFile)
				else:
					broken_files += 1
			else:
				ok_files += 1

		# mark project as modified
		if newFile:
			self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added file"))
		
		return (ok_files, broken_files, duplicate_files, folders)
	
	
	def GetImageSequenceDetails(self, file_path, session=None):
		""" Determine if this image is part of an image sequence, and if so, return
		the regular expression to match this image sequence, else return None. """
		
		# get a reference to the language translate method
		_ = self.project.translate

		# Get just the file name
		(dirName, fileName) = os.path.split(file_path)
		extensions = ["png", "jpg", "jpeg", "gif"]
		match = re.findall(r"(.*[^\d])?(0*)(\d+)\.(%s)" % "|".join(extensions), fileName, re.I)
		
		if not match:
			# File name does not match an image sequence
			return None
		else:
			# Get the parts of image name
			base_name = match[0][0]
			fixlen = match[0][1] > ""
			number = int(match[0][2])
			digits = len(match[0][1] + match[0][2])
			extension = match[0][3]

			full_base_name = os.path.join(dirName, base_name)
			
			# Check for images which the file names have the different length
			fixlen = fixlen or not (glob.glob("%s%s.%s" % (full_base_name, "[0-9]" * (digits + 1), extension))
						or glob.glob("%s%s.%s" % (full_base_name, "[0-9]" * ((digits - 1) if digits > 1 else 3), extension)))
			
			# Check for previous or next image
			for x in range(max(0, number - 100), min(number + 101, 50000)):
				if x != number and os.path.exists("%s%s.%s" % (full_base_name, str(x).rjust(digits, "0") if fixlen else str(x), extension)):
					is_sequence = True
					break
			else:
				is_sequence = False

			parameters = {"file_path":file_path, "folder_path":dirName, "base_name":base_name, "fixlen":fixlen, "digits":digits, "extension":extension}
			
			# if sibling images were found...
			if is_sequence:
				# prevent repeat messageboxes... only prompt user about the first image sequence found in a single drag n drop action
				if session not in self.project.form.file_drop_messages:
				
					# mark this session, so no more dialogs are shown for these drag n drop files
					if session:
						self.project.form.file_drop_messages.append(session)
					
					# prompt user
					messagebox.show("OpenShot", _("Would you like to import %s as an image sequence?") % fileName, gtk.BUTTONS_NONE, self.import_image_sequence, self.dont_import_image_sequence, gtk.MESSAGE_QUESTION, "", gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO, parameters)
					return parameters
				
				return None
			else:
				return None
	
	def import_image_sequence(self, parameters):
		print "import_image_sequence"
		
		from windows import ImportImageSeq
		
		folder_path = parameters["folder_path"]
		file_name = parameters["file_path"]
		base_name = parameters["base_name"]
		fixlen = parameters["fixlen"]
		digits = parameters["digits"]
		extension = parameters["extension"]
		
		if not fixlen:
			zero_pattern = "%d"
		else:
			zero_pattern = "%%0%sd" % digits
		
		# generate the regex pattern for this image sequence
		pattern = "%s%s.%s" % (base_name, zero_pattern, extension)
		
		# show import file dialog
		if not self.project.form.import_image_seq_dialog:
			# only open dialog, if it's not already open
			self.project.form.import_image_seq_dialog = ImportImageSeq.frmImportImageSequence(form=self, project=self.project, pattern=pattern, initial_folder=folder_path)
		else:
			# just add the image the regular way
			self.dont_import_image_sequence(parameters)
	
	def dont_import_image_sequence(self, parameters):
		print "dont_import_image_sequence"
		
		file_name = parameters["file_path"]
		
		# inspect the media file and generate it's thumbnail image (if any)
		newFile = self.project.thumbnailer.GetFile(file_name)
	
		# add to internal item collection
		if newFile:
			self.items.append(newFile)

		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Added file"))
		
		# refresh the window
		self.project.form.refresh_files()
	
	#----------------------------------------------------------------------
	def ConvertFileToImages(self, file_location, start_time=0.00, end_time=None):
		"""Add a new file to the current folder"""
		"""
		file_location: The location of the file to convert.
		start_time: The time to grab the first image.
		end_time: The time to grab the last image. None=last frame
		"""
		
		import urllib
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		# get a reference to the file
		f = self.project.project_folder.FindFile(file_location)

		# clean path to video
		file_location = urllib.unquote(file_location)
		
		# True if only a part of the file should be converted.
		is_part = True
		if start_time == 0.00 and (end_time == None or end_time == f.length):
			is_part = False
		
		# get file name, path, and extension
		(dirName, filename) = os.path.split(file_location)
		(fileBaseName, fileExtension)=os.path.splitext(filename)
		# the folder path if the image sequence is not a part (inside the same folder as the movie file)
		new_folder_path = os.path.join(dirName, fileBaseName)
	

		# check if this file is already in the project
		for item in self.items:
			if not is_part and item.file_type == "image sequence":
				(itemBase, itemExt) = os.path.split(item.name)
				if new_folder_path == itemBase:
					return True
		
		# Create folder(s)
		
		# if file is a video
		if f.file_type == "video":
			
			# create thumbnail folder (if it doesn't exist)
			if os.path.exists(new_folder_path) == False:
				os.mkdir(new_folder_path)
			
			# part of the clip will be converted
			if is_part:
				
				# counter
				x = 1
				
				while(True):
					
					# add "_x" to the name, so the folder has the name "base_x", and the first image will
					# have the name "base_x_1"
					new_file_base_name = fileBaseName + "_" + str(x)
					# create a new folder for this file (inside the previously created folder)
					new_folder_path = os.path.join(dirName, fileBaseName, new_file_base_name)
			
					# create thumbnail folder (if it doesn't exist)
					# FIXME: (TJ) This doesn't use thumbnail_path - should it?
					if os.path.exists(new_folder_path) == False:
						os.mkdir(new_folder_path)
					
					# if the directory is empty
					if not os.listdir(new_folder_path):
						
						# inspect the media file and generate it's thumbnail image (if any)
						newFile = self.project.thumbnailer.GetFile(file_location, False, new_file_base_name, start_time, end_time)
					
						break
					
					x += 1
			# whole clip
			else:
				# get the image sequence
				newFile = self.project.thumbnailer.GetFile(file_location, False)
				
		# update the location
		if newFile:
			
			# add to internal item collection
			self.items.append(newFile)

		return


	def file_exists_in_project(self, file_name):
		""" Check if this file exists in this project """
		
		# check if file exists
		if not os.path.exists(file_name):
			# File does not exist!
			return False
		
		# don't add a file that is already in this folder (i.e. dupe check)
		for item in self.items:
			
			if isinstance(item, OpenShotFile):
				if item.file_type != "image sequence":
					try:
						if os.path.samefile(file_name, item.name):
							return True
					except OSError:
						print "Error checking files on import"
						
		
		# didn't find a match
		return False

	#----------------------------------------------------------------------
	def get_file_path_from_dnd_dropped_uri(self, uri):
		""""""

		path = uri
		#path = urllib.url2pathname(uri) # escape special chars
		path = path.strip('\r\n\x00') # remove \r\n and NULL
		
		if os.name == 'nt':
			path = path.replace("/", "\\")
			path = path.replace("%20", " ")

		# get the path to file
		if path.startswith('file:\\\\\\'): # windows
			path = path[8:] # 8 is len('file:///')
		elif path.startswith('file://'): # nautilus, rox
			path = path[7:] # 7 is len('file://')
		elif path.startswith('file:'): # xffm
			path = path[5:] # 5 is len('file:')
		return path


	def UpdateFileLabel(self, unique_id, value, refresh_tree=0):
		#this will only be called when the treeview mode is selected, not the thumbview 
		for item in self.items:
			if item.unique_id == unique_id:
				item.label = value
				
				# mark project as modified
				self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Updated Label"))
				
		if refresh_tree == 1:
			# Update the main form
			self.project.form.refresh_files()
				
				
	def RemoveFile(self, filename):
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		item = self.FindFile(filename)
		if item:
			
			# find clips that have this file object
			for track in self.project.sequences[0].tracks:
				for clip in reversed(track.clips):
					# does clip match file
					if clip.file_object == item:
						# delete clip and remove thumbnail
						track.clips.remove(clip)
						clip.remove_thumbnail()
			
			# remove from file collection
			self.items.remove(item)
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Removed file"))
			
		else:
			#is this a folder?
			item = self.FindFolder(filename)
			if item:
				# remove from file collection
				self.items.remove(item)
				# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Removed folder"))

  
	#----------------------------------------------------------------------
	def FindFile(self, file_name):
		"""Pass the file system location of the item you 
		are looking for and this function will return the 
		reference to the OpenShot File that matches"""
		
		# loop through all files looking for the matching filename
		for file in self.items:
			if isinstance(file, OpenShotFile):
				name = file.name
				
				# check if file name matches this file
				if file_name == name:
					return file

				# split file name (if it's not found)
				(dirName, fileName) = os.path.split(name)
		
				# check if file name matches the basefile name
				if file_name == fileName:
					return file

		
		# No file found
		return None
	
	
	#----------------------------------------------------------------------
	def FindFileByID(self, unique_id):
		"""Pass the file system location of the item you 
		are looking for and this function will return the 
		reference to the OpenShot File that matches"""
		
		# loop through all files looking for the matching filename
		for file in self.items:
			if isinstance(file, OpenShotFile):

				# check if file name matches this file
				if unique_id == file.unique_id:
					return file

		# No file found
		return None

	
	def FindFolder(self, folder_name):
		"""Returns a reference to the OpenShotFolder
		 that matches the folder_name"""
		for folder in self.items:
			if isinstance(folder, OpenShotFolder):
				name = folder.name
				
				if folder_name == name:
					return folder
	
	def ListFolders(self):
		"""Return a list of any folders in the project"""
		
		folders = []
		for item in self.items:
			if isinstance(item, OpenShotFolder):
				folders.append(item.name)
		return folders
	
	def AddParentToFile(self, file_name, folder_name):
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		file = self.FindFile(file_name)
		if file:
			file.parent = folder_name
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Moved to folder"))
			
	def RemoveParent(self, file_name, folder_name):
		
		# get a reference to the language translate method
		_ = self.project.translate
		
		file = self.FindFile(file_name)
		if file:
			print "REMOVE PARENT"
			file.parent = self.project.project_folder
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=False, type=_("Removed from folder"))
			
	#----------------------------------------------------------------------
	def __setstate__(self, state):
		""" This method is called when an OpenShot project file is un-pickled (i.e. opened).  It can
		    be used to update the structure of old clip classes, to make old project files compatable with
		    newer versions of OpenShot. """
	
		# Check for missing DEBUG attribute (which means it's an old project format)
		if 'label' not in state:
			state['label'] = ""
		if 'unique_id' not in state:
			state['unique_id'] = str(uuid.uuid1())

		# update the state object with new schema changes
		self.__dict__.update(state)
		

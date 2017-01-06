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

import os, threading, time, uuid
from PIL import Image
from classes import files, profiles, messagebox

try:
	import mlt
except ImportError:
	print "*** ERROR: MLT Python bindings failed to import ***"
	

class thumbnailer ( threading.Thread ):
	""" This class is designed to always be running during LibreShot.  It's a seperate thread that 
	is always waiting to inspect video and audio files, generate thumbnails, etc... """

	def set_project(self, project):
		""" Associate the LibreShot project file with this threaded class. """
		self.project = project
		
	def GetFile(self, file_location, only_thumbnail=True, new_file_base_name=None, start_time=0.00, end_time=None):
		""" Use this method to generate an LibreShotFile object based on the URL (or file location)
		of a video or audio file. Each time you call this method, it will lock this thread (and LibreShot's
		main thread) until it has finished. """
		""" 
		file_location: The location of the file on the hard drive, including the name and extension.
		only_thumbnail: True if only a thumbnail should be grabbed from the file, False if image sequence.
		new_file_base_name: The name of the folder and the base for the image sequence name, not including the path.
		start_time: The time to start grabbing frames from the file, in seconds.
		end_time: The time to end grabbing frames from the file, in seconds. None = To the last frame.
		"""

		try:
			
			# determine name and location of thumbnail image
			self.file_name = file_location
			self.thumbnail_path = ""
			self.file_type = "video"
			self.label = ""
			self.unique_id = str(uuid.uuid1())	
			project_path = self.project.folder
			(dirName, fileName) = os.path.split(file_location)
			(fileBaseName, fileExtension) = os.path.splitext(fileName)
			fileExtension = fileExtension.replace(".", "")
			
			
			uniqueFileBaseName = self.unique_id
			actual_thumbnail_path = project_path + "/thumbnail/" + uniqueFileBaseName + "_" + fileExtension + "_1.png"

			if only_thumbnail:
				# just get 1 thumbnail frame
				self.thumbnail_path = project_path + "/thumbnail/" + uniqueFileBaseName + "_" + fileExtension + "_%d.png"
				
				# set the profile
				self.profile = mlt.Profile("quarter_ntsc")

			else:
				if new_file_base_name == None or new_file_base_name == fileBaseName:
					# choose the same folder as the name (without extension) as default
					self.thumbnail_path = os.path.join(dirName, fileBaseName, fileBaseName + "_%d.png")
				else:
					# export a part of the video to a folder under the folder with the same name as the file.
					self.thumbnail_path = os.path.join(dirName, fileBaseName, new_file_base_name, new_file_base_name + "_%d.png")
			
			# re-init the mlt factory
			mlt.Factory.init()
				
			# Create the producer
			self.p = mlt.Producer( self.profile, '%s' % file_location )
			
			# Check if clip is valid (otherwise a seg fault)
			if self.p.is_valid() == False:
				return None
			
			# Check for invalid files - badly generated video files can have
			# a length of 0 or -1, e.g. 
			# https://bugs.launchpad.net/ubuntu/+source/libreshot/+bug/927755, https://bugs.launchpad.net/kazam/+bug/925238
			if self.p.get_length() < 1 or self.p.get_length() == 0x7fffffff:
				return None
			
			# check the 'seekable' property
			# If it is zero, then MLT is likely to have problems with this file.
			if self.p.get("seekable") == '0':
				messagebox.show(_("Warning!"), _("The file %s has properties that may prevent it working properly in LibreShot.\nYou may need to transcode it to another format.") % (self.file_name))
				
			# create the consumer
			self.c = mlt.Consumer(self.profile, "avformat", self.thumbnail_path)

			# set some consumer properties
			self.c.set("real_time", 0)
			self.c.set("vcodec", "png")
			
			# determine length of clip in seconds
			producer_fps = float(self.p.get_fps())
			first_frame = int(round(producer_fps * start_time))
			# Whole clip if end_time = None 
			if end_time == None:
				last_frame = self.p.get_length()
			else:
				last_frame = int(round(producer_fps * end_time))
			max_frames = last_frame - first_frame
		
			# determine dimensions			
			
			height = 0
			width = 0
			if self.p.get("height"):
				height = int(self.p.get("height"))
			if self.p.get("width"):
				width = int(self.p.get("width"))
				
			audio_index = self.p.get_int("audio_index")
			video_index = self.p.get_int("video_index")
			audio_property = "meta.media.%s.codec.long_name" % audio_index
			if self.p.get(audio_property):
				self.audio_codec = self.p.get(audio_property)
			else:
				self.audio_codec = ""
					
			video_property = "meta.media.%s.codec.long_name" % video_index
			if self.p.get(video_property):
				self.video_codec = self.p.get(video_property)
			else:
				self.video_codec = ""
			
			if self.p.get_frame():
				frame = self.p.get_frame()
				self.audio_frequency = frame.get_int("frequency")
				self.audio_channels = frame.get_int("channels")
			
			# determine if this is an image
			is_image = False
			if self.p.get_length() == 15000 and video_index == 0 and audio_index == 0:
				# images always have exactly 15000 frames
				is_image = True
				self.file_type = "image"	

				# set the max length of the image to 300 seconds (i.e. 5 minutes)
				max_frames = producer_fps * 300
				
				# get actual height & width of image (since MLT defaults to 1 x 1)
				width, height = self.get_image_size(file_location)
		
			# determine length
			if only_thumbnail:
				calculate_length = self.p.get_length() / producer_fps
			else:
				calculate_length = max_frames / producer_fps
			if is_image:
				
				# set the length to 300 seconds (i.e. 5 minutes)
				calculate_length = float(300)

				
			# set thumbnail image (if no height & width are detected)
			if (height == False or width == False) and (is_image == False):
				self.thumbnail_path = ""
				self.file_type = "audio"


			# get the 1st frame (if not exporting all frames)
			if only_thumbnail:
				max_frames = float(self.p.get_length()) - 1.0
				self.p = self.p.cut(1, 1)
				# get the frames in an interval
			else:
				self.p = self.p.cut(first_frame, last_frame)
				# mark as image seq
				self.label = "Image Sequence"
				self.file_type = "image sequence"

			# Check if clip is valid (otherwise a seg fault)
			if self.p.is_valid() == False:
				return None

			# connect the producer and consumer
			self.c.connect( self.p )

			# Start the consumer, and lock the thread until it's done (to prevent crazy seg fault errors)
			# Only start if the media item has a thumbnail location (i.e. no audio thumbnails)
			if self.thumbnail_path:
				self.c.run()

	
			# create an libreshot file object
			newFile = files.LibreShotFile(self.project)
			# thumbnails and image sequences are stored at different locations
			if only_thumbnail:
				newFile.name = file_location
			else:
				newFile.name = self.thumbnail_path
			newFile.length = calculate_length
			newFile.thumb_location = actual_thumbnail_path
			newFile.videorate = (self.p.get_fps(), 0)
			newFile.height = height
			newFile.width = width
			newFile.max_frames = max_frames
			newFile.fps = producer_fps
			newFile.file_type = self.file_type
			newFile.label = self.label
			newFile.audio_channels = self.audio_channels
			newFile.audio_codec = self.audio_codec
			newFile.audio_frequency = self.audio_frequency
			newFile.video_codec = self.video_codec

			# return the LibreShotFile object
			return newFile
		
		except Exception:
			print "Failed to import file: %s" % file_location



	def run ( self ):
		""" This is the main method on this thread.  This method should not return anything, or the 
		thread will no longer be active... and thus will no longer be able to inspect media files. """
		
		self.amAlive = True
		self.file_name = ""
		self.c = None
		self.p = None

		# init the factory, and load a small video size / profile
		mlt.Factory().init()
		self.profile = mlt.Profile("quarter_ntsc")

		# this loop will continue as long as LibreShot is running
		while self.amAlive:
			time.sleep( 1 ) 

		# clear all the MLT objects
		self.p = None
		self.c = None
		self.profile = None
		self.f = None
		
	def get_thumb_at_frame(self, filename, frame=1, new_name="", full_size=True):
		""" if new_name = None, it will default to  'name_fileext + "_%d.ext' in the thumbnail folder.
		if full_size is True, a full size frame will be extracted (based on the project profile).
		Else: quarter_ntsc"""
		
		self.file_name = filename
		
		project_path = self.project.folder
		myPath = self.file_name
		(dirName, fileName) = os.path.split(myPath)
		(fileBaseName, fileExtension)=os.path.splitext(fileName)
		fileExtension = fileExtension.replace(".", "")
		
		# Init mlt factory
		mlt.Factory.init()
		
		# set the profile
		if full_size:
			self.profile = profiles.mlt_profiles(self.project).get_profile(self.project.project_type)
		else:
			self.profile = mlt.Profile("quarter_ntsc")
		
		# Create the producer
		self.p = mlt.Producer( self.profile, '%s' % self.file_name )
		
		# Check if clip is valid (otherwise a seg fault)
		if self.p.is_valid() == False:
			return None
		
		
		if new_name == "":
			# just get 1 thumbnail frame
			self.thumbnail_path = project_path + "/thumbnail/" + fileBaseName + "_" + fileExtension + "_%d.png"
		else:
			#for snapshots, use the new file name
			#don't use the thumbnail path for the new file
			self.thumbnail_path = project_path + "/" + new_name
		
		# create the consumer
		self.c = mlt.Consumer(self.profile, "avformat", self.thumbnail_path)
	
		# set some consumer properties
		self.c.set("real_time", 0)
		self.c.set("vcodec", "png")
		
		#get the frame
		self.p = self.p.cut(frame, frame)

		# Check if clip is valid (otherwise a seg fault)
		if self.p.is_valid() == False:
			return None
		
		# connect the producer and consumer
		self.c.connect( self.p )
	
		# Only start if the media item has a thumbnail location (i.e. no audio thumbnails)
		if self.thumbnail_path:
			self.c.run()
			
	def get_image_size(self, filepath):
		""" Get the actual pixel size of an image, if possible """
		
		try:
			# get PIL image object
			image = Image.open(filepath)
			return image.size
			
		except:
			# failed to get size. MLT defaults to a width and height of 1, so 
			# just keep those values
			return (1,1)
			
		
		

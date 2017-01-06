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

import os, sys, locale, time
import threading
import gobject
from classes import profiles
from gtk import STOCK_MEDIA_PAUSE
from gtk import STOCK_MEDIA_PLAY
import gtk

# init the foreign language
from language import Language_Init


try:
	import mlt
except ImportError:
	print "*** ERROR: MLT Python bindings failed to import ***"


class player ( threading.Thread ):
	
	def __init__(self, project, main_form, file_name, mode=None):
		self.project = project
		self.main_form = main_form
		self.file_name = file_name
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		# set the FPS
		self.fps = self.project.fps()
		
		# update mode
		if mode:
			# set the mode
			self.mode = mode

		# call base class
		threading.Thread.__init__(self)


	def set_project(self, project, main_form, file_name, mode=None, render_options = None, override_path = None):
		self.project = project
		self.main_form = main_form
		self.file_name = file_name
		self.render_options = render_options
		
		# set the FPS
		self.fps = self.project.fps()
		
		# update mode
		if mode:
			# set the mode
			self.mode = mode
			
		# override mode
		if override_path:
			self.override_path = override_path
		else:
			self.override_path = None
			
		
	def set_profile(self, profile_name, load_xml = True):

		""" set the MLT profile object... specific in the project properties """
		
		# stop the consumer
		self.consumer_stop()
		
		# set the new profile
		self.profile = profiles.mlt_profiles(self.project).get_profile(profile_name)

		# set the FPS
		self.fps = self.project.fps()

		# create a new consumer
		print "NEW SDL CONSUMER"
		self.new_sdl_consumer()
		
		
		# re-load the mlt objects (i.e. the producer & consumer)
		if load_xml:
			self.load_xml()

		
	def load_xml(self):
		
		# get reference to translate gettext method
		_ = self._

		# re-init the mlt factory
		mlt.Factory.init()

		# Create the consumer
		if self.mode == "render":
			# RENDER MOVIE mode
			
			# stop the consumer
			self.consumer_stop()
	
			# Create the producer
			self.p = mlt.Producer( self.profile, 'xml:%s' % self.file_name)
			if self.p.is_valid() == False:
				print "ERROR WITH %s" % self.file_name
				return

			# get export file path
			folder = self.render_options["folder"]
			file = self.render_options["file"]
			format = self.render_options["f"]
			export_path = "%s.%s" % (os.path.join(folder, file), format)
			
			# create consumer
			self.c = mlt.Consumer( self.profile, "avformat", export_path)
			
			# set some RENDER specific options
			self.c.set("real_time", -1)
			
			# set render options
			if self.render_options["export_to"] == _("Image Sequence"):
				# image seq
				self.c.set("vcodec" , self.render_options["vcodec"])
			else:
				# video & audio
				self.c.set("f" , format)
				self.c.set("vcodec" , self.render_options["vcodec"])
				self.c.set("b" , self.render_options["b"])
				self.c.set("acodec" , self.render_options["acodec"])
				self.c.set("ar" , self.render_options["ar"])
				self.c.set("ac" , self.render_options["ac"])
				self.c.set("ab" , self.render_options["ab"])
			
				if self.render_options["vcodec"] == "libx264":
					self.c.set("minrate", "0")
					self.c.set("b_strategy", "1")
					self.c.set("subcmp", "2")
					self.c.set("cmp", "2")
					self.c.set("coder", "1")
					self.c.set("flags", "+loop")
					self.c.set("flags2", "dct8x8")
					self.c.set("qmax", "51")
					self.c.set("subq", "7")
					self.c.set("qmin", "10")
					self.c.set("qcomp", locale.str(float("0.6")))
					self.c.set("qdiff", "4")
					self.c.set("trellis", "1")
				if format == "dvd":
					# stolen from ffmpeg.c, void opt_target(const char *arg)
					self.c.set("maxrate", "9000000")
					self.c.set("minrate", "0")
					self.c.set("bufsize", "1835008")
					self.c.set("packetsize", "2048")
					self.c.set("muxrate", "10080000")

		else:
			# stop the consumer (if sdl_preview mode and an older version of MLT)
			if self.check_version(0, 6, 0) == False and str(self.main_form.settings.general["output_mode"]) == "sdl_preview":
				# stop the consumer 
				self.consumer_stop()
			
			# Create the producer
			self.p = mlt.Producer( self.profile, 'xml:%s' % self.file_name)
			if self.p.is_valid() == False:
				print "ERROR WITH %s" % self.file_name
				return

			# refresh sdl and pause video
			self.pause()

		# connect the producer and consumer
		self.c.connect( self.p )

		# start consumer
		if self.c.is_stopped:
			self.c.start()


	def run ( self ):
		# FIXME: Is this relevant - doesn't seem to be used in this method?
		self.override_path = None
		self.alternate_progress_bar = None

		# track wheather the thread is playing or not
		self.isPlaying = False 
		
		# track if this thread should die
		self.amAlive = True
		
		# Start the mlt system
		self.f = mlt.Factory().init( )
		
		# set the MLT profile object... specific in the project properties
		self.profile = profiles.mlt_profiles(self.project).get_profile(self.project.project_type)
		
		# Create the producer
		self.p = mlt.Producer( self.profile, 'xml:%s' % self.file_name)

		if self.p.is_valid():
			# set speed to zero (i.e. pause)
			self.pause()
			
			# PREVIEW mode
			self.c = mlt.Consumer( self.profile, str(self.main_form.settings.general["output_mode"]) )
			self.c.set("real_time", 1)
		
			# Connect the producer to the consumer
			self.c.connect( self.p )
			
			# Start the consumer
			self.c.start()
			
			# Get the FPS
			self.fps = self.project.fps()
			
			# init the render percentage
			self.fraction_complete = 0.0		
			
			# Wait until the user stops the consumer
			while self.amAlive:
				
				# get current frame
				current_frame = float(self.p.position())
				total_frames = float(self.p.get_length() - 1)
				decimal_complete = current_frame / total_frames
				percentage_complete = decimal_complete * 100.0

				# only calculate position / percentage when playing
				if self.c.is_stopped() == False:

					# move play head
					new_time = current_frame / float(self.fps)
					
					if self.mode == "render":
						# update Export Dialog Progress Bar
						self.fraction_complete = decimal_complete
						if self.project.form.frmExportVideo:
							gobject.idle_add(self.project.form.frmExportVideo.update_progress, self.fraction_complete)
						
					elif self.mode == "preview":
						
						if self.alternate_progress_bar:
							# update alternateive progress bar (if any) of video
							# this is used by the clip properties window 
							if self.alternate_progress_bar:
								gobject.idle_add(self.alternate_progress_bar.set_value, percentage_complete)
							
						else:
							# update play-head
							if self.project.sequences[0]:
								gobject.idle_add(self.project.sequences[0].move_play_head, new_time)
			
							# update progress bar of video 
							if self.main_form.hsVideoProgress:
								gobject.idle_add(self.main_form.hsVideoProgress.set_value, percentage_complete)
								gobject.idle_add(self.main_form.scroll_to_playhead)
								
							# pause video when 100%
							if percentage_complete == 100:
								self.pause()
						
						
					elif self.mode == "override":
						# update progress bar of video 
						if self.main_form.hsVideoProgress:
							gobject.idle_add(self.main_form.hsVideoProgress.set_value, percentage_complete)

					# wait 1/5 of a second
					time.sleep( 0.1 )
					
				else:
					if self.mode == "render":
						# update Export Dialog Progress Bar
						if self.fraction_complete > 0.0:
							# update progress bar to 100%
							if self.project.form.frmExportVideo:
								gobject.idle_add(self.project.form.frmExportVideo.update_progress, 1.0)
							
							# reset the fraction
							self.fraction_complete = 0.0

					# wait a bit... to cool off the CPU
					time.sleep( 0.1 )



			# clear all the MLT objects
			self.consumer_stop()
			self.p = None
			self.c = None
			self.profile = None
			self.f = None
			
		else:
			# Diagnostics
			print "ERROR WITH %s" % self.file_name

	def set_progress_bar(self, pbar):
		""" Set the progress bar that this thread should update """
		self.alternate_progress_bar = pbar

	def clear_progress_bar(self):
		""" Set the progress bar that this thread should update """
		self.alternate_progress_bar = None
		
	def get_progress_bar(self):
		""" Get the progress bar object """
		return self.alternate_progress_bar
	
	def close_window(self, window):
		""" Let this thread close a window """
		window.destroy()

	def move_play_head(self, new_time):
		# call this thread move the play_head
		gobject.idle_add(self.project.sequences[0].move_play_head, new_time)
		

	def pause(self):
		if self.main_form.settings.general["use_stock_icons"] == "No" or None != self.main_form.tlbPlay.get_icon_widget():
			theme_img = gtk.Image()
			theme_img.set_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "play.png"))
			theme_img.show()
			
			# set new icon image
			self.main_form.tlbPlay.set_icon_widget(theme_img)
			
		else:
			# set stock id
			
			self.main_form.tlbPlay.set_icon_widget(None)
			self.main_form.tlbPlay.set_tooltip_text(self.main_form._('Play'))
			self.main_form.tlbPlay.set_stock_id(STOCK_MEDIA_PLAY)
				
		# pause the video
		self.isPlaying = False
		
		if self.check_version(0, 6, 0):
			# newer pause method, that waits for the pause to happen
			self.p.pause()
		else:
			# older pause method
			self.p.set_speed(0)
		
			
	def play(self):
		if self.main_form.settings.general["use_stock_icons"] == "No" or None != self.main_form.tlbPlay.get_icon_widget():
			theme_img = gtk.Image()
			theme_img.set_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "pause.png"))
			theme_img.show()
			
			# set new icon image
			self.main_form.tlbPlay.set_icon_widget(theme_img)
			
		else:
			# set stock id
			
			self.main_form.tlbPlay.set_icon_widget(None)
			self.main_form.tlbPlay.set_stock_id(STOCK_MEDIA_PAUSE)
			self.main_form.tlbPlay.set_tooltip_text(self.main_form._('Pause'))		
		
		# play the video
		self.isPlaying = True
		self.p.set_speed(1)


	def seek(self, frame_number):

		# pause frame (if the video is playing)
		if self.isPlaying:	
			# pause the producer
			self.pause()
			
		# refresh sdl
		self.refresh_sdl()
			
		# seek to a specific frame 
		self.p.seek(frame_number)
		
		# refresh sdl
		self.refresh_sdl()
		
		
	def consumer_stop(self):
		""" Stop the MLT consumer """
		
		# stop consumer
		self.c.stop()
		
		
	def new_sdl_consumer(self):
		""" Create a new SDL consumer and attach it to the producer """

		# create and set new consumer
		self.c = mlt.Consumer( self.profile, str(self.main_form.settings.general["output_mode"]) )
		self.c.set("real_time", 1)	
		
	def position(self):
		""" Get the MLT position (current frame number) """
		
		# return the current frame
		return self.p.position()
	
	
	def get_speed(self):
		""" Get the MLT speed """
		
		# return the MLT speed
		return self.p.get_speed()
	
	def set_speed(self, new_speed):
		""" Set the MLT speed """
		
		# set the speed of the producer
		self.p.set_speed(new_speed)
		
	
	def get_length(self):
		""" Get the length of the MLT producer """
		
		# return the length of the XML file, in frames
		return self.p.get_length()

		
	def refresh_sdl(self):
		""" Tell MLT to refresh the SDL image. """ 
		
		# update the refresh property on the consumer
		self.c.set("refresh", 1)


	def mlt_version(self):
		""" Get the MLT version (if any).  Version 0.6.0+ has the 
		version methods.  Older versions will fail to find these
		methods, so we need to catch the error here. """

		try:
			major = mlt.mlt_version_get_major()
			minor = mlt.mlt_version_get_minor()
			revision = mlt.mlt_version_get_revision()
			
		except:
			# default version to last version without the version methods (since 
			# there is no way to determine the exact version number)
			major = 0
			minor = 5
			revision = 10
			
		return (major, minor, revision)

	def check_version(self, major, minor, revision):
		""" Check a version against the current version. 
		If it's equal or greater it will return TRUE.  """
	
		# Get current version
		current_major, current_minor, current_revision = self.mlt_version()
		
		# Build strings to compare
		check_version = "%02d%02d%02d" % (major, minor, revision)
		current_version = "%02d%02d%02d" % (current_major, current_minor, current_revision)
		
		if current_version >= check_version:
			return True
		else:
			return False
		
		
		
	

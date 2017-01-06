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

import os, sys, locale, threading

import xml.dom.minidom as xml
from classes import profiles, open_project, video, project
import cPickle as pickle

# init the foreign language
from language import Language_Init
from optparse import OptionParser


class Bot():

	def __init__(self, init_threads=True):

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
		self.EXPORT_PRESETS_DIR = os.path.join(self.BASE_DIR, "libreshot", "export_presets")
		self.EFFECTS_DIR = os.path.join(self.BASE_DIR, "libreshot", "effects")
		# location for per-session, per-user, files to be written/read to
		self.DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
		self.USER_DIR = os.path.join(os.path.expanduser("~"), ".libreshot")
		self.THEMES_DIR = os.path.join(self.BASE_DIR, "libreshot", "themes")

		# only run the following code if we are really using 
		# this project file... 
		if init_threads:

			# Add language support
			translator = Language_Init.Translator(self)
			_ = translator.lang.gettext
			
			# use OptionParser to interpret commandline options
			parser = OptionParser(_("usage: %prog [options] inputfile.osp"))
			parser.add_option("-o",
							"--outputfile",
							dest="FileName",
							default="temp",
							help=_("destination file-name"),
							metavar="FILE")
							
			parser.add_option("-F",
							"--folder",
							dest="ExportFolder",
							default=self.USER_DIR,
							help=_("export folder"),
							metavar="FOLDER")
							
			parser.add_option("-i",
							"--image-sequence",
							action="store_true",
							dest="IsImageSequence",
							default=False,
							help=_("export as image sequence")
							)
							
			parser.add_option("-v",
							"--video",
							action="store_true",
							dest="IsVideo",
							default=False,
							help=_("export as video or audio file"))				

			parser.add_option("-f",
							"--format",
							type="string",
							dest="ImageFormat",
							default="avi",
							help=_("set video codec"))

			parser.add_option("-C",
							"--video-codec",
							type="str",
							dest="VideoCodec",
							default="mpeg4",
							help=_("set video codec"))
							
			parser.add_option("-R",
							"--video-bitrate",
							type="string",
							dest="VideoBitRate",
							default="5 Mb/s",
							help=_("set video bitrate in format 'number kb/s' or 'number Mb/s'"))
							
			parser.add_option("-c",
							"--audio-codec",
							type="string",
							dest="AudioCodec",
							default="libmp3lame",
							help=_("set audio codec"))
							
			parser.add_option("-s",
							"--audio-samplerate",
							type="int",
							dest="SampleRate",
							default=44100,
							help=_("set audio sample rate"))

			parser.add_option(
							"--channels",
							type="int",
							dest="Channels",
							default=2,
							help=_("set number of audio channels"))

			parser.add_option("-r",
							"--audio-bitrate",
							type="string",
							dest="AudioBitRate",
							default="128 kb/s",
							help=_("set video bitrate in format 'number kb/s'"))


			def error(message):
				'''Prints an error message, the help message and quits'''
				global parser
				print _("Error: ") + message
				print
				sys.exit()

			def warn(message):
				'''Print a warning message'''
				print _("Warning: ") + message


			# get optparse arguments and check for sanity
			(options, args) = parser.parse_args()

			if not args:
				parser.print_help()
				error(_('Please specify an input project-file!'))

			if len(args) > 1:
				parser.print_help()
				error(_("Too many arguments!"))

			# this is the file we want to parse
			self.inputscript = args[0]
			
			
			def convert_to_bytes(BitRateString):
				bit_rate_bytes = 0
				# split the string into pieces
				s = BitRateString.lower().split(" ")
				measurement = "kb"
				try:
					# Get Bit Rate
					if len(s) >= 2:
						raw_number = float(s[0])
						raw_measurement = s[1]					
						if "kb" in raw_measurement:
							measurement = "kb"
							#bit_rate_bytes = raw_number * 1024.0
							bit_rate_bytes = raw_number * 1000.0						
						elif "mb" in raw_measurement:
							measurement = "mb"
							#bit_rate_bytes = raw_number * 1024.0 * 1024.0
							bit_rate_bytes = raw_number * 1000.0 * 1000.0
				except:
					pass
				# return the bit rate in bytes
				return str(int(bit_rate_bytes))			
			
			# consider the render options
			self.render_options = {}
			self.render_options["folder"] = options.ExportFolder
			self.render_options["file"] = options.FileName
			
			if options.IsImageSequence:
				self.render_options["vcodec"] = options.ImageFormat
				self.render_options["f"] = options.ImageFormat
				self.render_options["export_to"] = "Image Sequence"
				
			else:
				self.render_options["vcodec"] = options.VideoCodec
				self.render_options["f"] = options.ImageFormat
				self.render_options["export_to"] = ""
				
			self.render_options["b"] = convert_to_bytes(options.VideoBitRate)
			self.render_options["acodec"] = options.AudioCodec
			self.render_options["ar"] = options.SampleRate
			self.render_options["ac"] = options.Channels
			self.render_options["ab"] = convert_to_bytes(options.AudioBitRate)
			
			# Print rendering options to terminal
			print "\n"	
			print _("rendering options:")
			print _("container type:")+" "+str(self.render_options["f"])
			print _("video codec:")+" "+str(self.render_options["vcodec"])
			print _("video bitrate:")+" "+str(self.render_options["b"])+"\n"
			print _("audio codec:")+" "+str(self.render_options["acodec"])
			print _("audio sample rate:")+" "+str(self.render_options["ar"])
			print _("channels:")+" "+str(self.render_options["ac"])
			print _("audio bitrate:")+" "+str(self.render_options["ab"])+"\n"			
			
			# get the complete path to the new file
			self.folder1 = self.render_options["folder"]
			self.file1 = self.render_options["file"]
			self.export_path = "%s.%s" % (os.path.join(self.folder1, self.file1), self.render_options["f"])
			
			self.current_project = project.project()
			
			self.myFile = file(self.inputscript, "rb")
			self.current_project = pickle.load(self.myFile)
			

	def render(self, init_threads=True):
		
		# generates xml file
		self.current_project.GenerateXML(os.path.join(self.USER_DIR, "sequence.mlt"))
		print _("generating XML file for rendering")	
		self.fps = self.current_project.fps()
		#threading.Thread.__init__(self)
		self.profile = profiles.mlt_profiles(self.current_project).get_profile(self.current_project.project_type)
		self.file_name = os.path.join(self.USER_DIR, "sequence.mlt")

		# Import required modules
		import time
		import sys
		import math			
		try:
			import mlt
		except ImportError:
			print "*** ERROR: MLT Python bindings failed to import ***"	
		
		# Progress bar function
		def progress(width, percent):
			marks = math.floor(width * (percent / 100.0))
			spaces = math.floor(width - marks)
			loader = '[' + ('=' * int(marks)) + (' ' * int(spaces)) + ']'
			sys.stdout.write("%s %d%%\r" % (loader, percent))
			#if percent >= 100:
				#sys.stdout.write("\n")
			sys.stdout.flush()

		# Create producer and initialize mlt
		self.f = mlt.Factory().init()
		self.p = mlt.Producer( self.profile, 'xml:%s' % self.file_name)
		if self.p.is_valid() == False:
			print "MLT producer failure"
			sys.exit()
		self.p.set_speed(0)
		out_folder = self.render_options["folder"]
		out_file = self.render_options["file"]
		
		# Set export path
		export_path = "%s.%s" % (os.path.join(out_folder, out_file), self.render_options["f"])

		# RENDER MOVIE
		print _("Starting rendering to ") + str(export_path)
		self.c = mlt.Consumer( self.profile, "avformat", export_path)

		# set some RENDER specific options
		self.c.set("real_time", -1)
			
		# set render options
		self.c.set("f" , self.render_options["f"])
		self.c.set("vcodec" , self.render_options["vcodec"])
		self.c.set("b" , self.render_options["b"])
		self.c.set("acodec" , self.render_options["acodec"])
		self.c.set("ar" , self.render_options["ar"])
		self.c.set("ac" , self.render_options["ac"])
		self.c.set("ab" , self.render_options["ab"])
		
		# sets correct options if rendering to h264
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
			self.c.set("qcomp", "0.6")
			self.c.set("qdiff", "4")
			self.c.set("trellis", "1")		

		# Connect the producer to the consumer
		self.c.connect( self.p )
		self.p.set_speed(1)
		
		# Start the consumer
		self.c.start()
		
		# init the render percentage
		self.fraction_complete = 0.0
		self.render_interrupted = False

		while self.c.is_stopped() == False:
			# update Export Dialog Progress Bar
			self.fraction_complete = (float(self.p.position()) / float(self.p.get_length() - 1))
			progress(50, int(self.fraction_complete*100))
			# wait 1/5 of a second
			try:
				time.sleep( 0.2 )
			except KeyboardInterrupt:
				print "\n"
				print _("program interrupted by user")
				self.render_interrupted = True
				self.c.stop()
		
		if self.render_interrupted == False:
			progress(50, 100)
			print "\n"
			print _("project file correctly rendered")
			
		# clear all the MLT objects
		self.c.stop()
		self.p = None
		self.c = None
		self.profile = None
		self.f = None

		return

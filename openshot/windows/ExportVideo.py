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

has_py_notify = False

try:
	import pynotify
	has_py_notify = True
except:
	has_py_notify = False
		
import os
import gtk
import xml.dom.minidom as xml
import locale

from classes import messagebox, profiles, project, video
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import UploadVideo
from uploads.manager import UploadManager

# init the foreign language
from language import Language_Init


class frmExportVideo(SimpleGtkBuilderApp):

	def __init__(self, path="ExportVideo.ui", root="frmExportVideo", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		# set important vars
		self.form = form
		self.project = project
		self.original_project_type = self.project.project_type		# remember the original project type (i.e. mlt_profile)
		
		# Show all controls on this screen
		self.frmExportVideo.show_all()
		
		# set window as MODAL (so they can't mess up the export)
		self.frmExportVideo.set_modal(True)
		
		self.invalid_codecs = []
		
		# init the project type properties
		self.init_properties(self.cmbProjectType.get_active_text())
		
		# set the export file name
		self.txtFileName.set_text(self.project.name)

		# set the export folder as the project folder (if any)
		if ".openshot" in self.project.folder:
			# This is the openshot default project (set the folder to 'DESKTOP')
			self.fileExportFolder.set_current_folder(self.project.DESKTOP)
		else:
			# Set project folder
			self.fileExportFolder.set_current_folder(self.project.folder)
		
		# init the list of possible project types / profiles
		self.profile_list = profiles.mlt_profiles(self.project).get_profile_list()
		
		# loop through each profile, and add it to the dropdown
		for file_name, p in self.profile_list:
			# append profile to list
			self.cmbProjectType.append_text(p.description())
					
		export_options = [_("Video & Audio"), _("Image Sequence")]
		# loop through export to options
		for option in export_options:
			# append profile to list
			self.cboExportTo.append_text(option)


		export_types_model = self.cboExportType.get_model()
		export_types_model.clear()
		
		export_types = [_("Export to Folder"), _("Upload to Web")]
		# loop through export to options
		for option in export_types:
			# append profile to list
			self.cboExportType.append_text(option)
		self.set_dropdown_values(_("Export to Folder"), self.cboExportType)
		
		
		upload_model = self.cboUploadServices.get_model()
		upload_model.clear()
		
		self.upload_manager = UploadManager(project, self.form.settings)
		self.upload_services = self.upload_manager.get_services()
		upload_types = self.upload_services.keys()
		upload_types.sort()
		# loop through export to options
		for option in upload_types:
			# append profile to list
			self.cboUploadServices.append_text(option)
		self.set_dropdown_values(_("YouTube"), self.cboUploadServices)
		

		#populate the format/codec drop downs 
		#formats
		format_model = self.cboVIdeoFormat.get_model()
		format_model.clear()
		
		for format in self.form.vformats:
			self.cboVIdeoFormat.append_text(format)
			
		#video codecs
		vcodecs_model = self.cboVideoCodec.get_model()
		vcodecs_model.clear()
		
		for vcodec in self.form.vcodecs:
			self.cboVideoCodec.append_text(vcodec)
			
		#audio codecs
		acodecs_model = self.cboAudioCodec.get_model()
		acodecs_model.clear()
		
		# Add 'none' audio codec
		self.cboAudioCodec.append_text( "none" )
		for acodec in self.form.acodecs:
			# Add the rest of the audio codecs
			self.cboAudioCodec.append_text(acodec)
			
			
		# set the dropdown boxes
		self.set_project_type_dropdown()
		self.set_export_to_dropdown()
		
		#load the simple project type dropdown
		presets = []
		for file in os.listdir(self.project.EXPORT_PRESETS_DIR):
			xmldoc = xml.parse(os.path.join(self.project.EXPORT_PRESETS_DIR,file))
			type = xmldoc.getElementsByTagName("type")
			presets.append(_(type[0].childNodes[0].data))
		#exclude duplicates
		presets = list(set(presets))
		for item in sorted(presets):
			self.cboSimpleProjectType.append_text(item)
			
		#indicate that exporting cancelled
		self.cancelled = False
		
		# create the infobar displaying the missing codec message
		self.use_infobar = True
		self.last_error = None
		try:
			self.infobar = gtk.InfoBar()
			self.content = self.infobar.get_content_area()
			self.label = gtk.Label()
			
			self.image = gtk.Image()
			self.image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
			
			self.content.add(self.image)
			self.content.add(self.label)
			self.vbox1.pack_start(self.infobar)
			self.vbox1.reorder_child(self.infobar, 3)
			self.infobar.set_message_type(gtk.MESSAGE_WARNING)
		except:
			# older version of pygtk can not create an InfoBar
			self.use_infobar = False

		
	def set_project_type_dropdown(self):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cmbProjectType.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)
			
			# check for the matching project type
			if self.project.project_type == value:			
				
				# set the item as active
				self.cmbProjectType.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
	def on_expander_activate(self, widget, *args):
		#print "on_expander_activate"
		#self.frmExportVideo.set_size_request(0,0)
		pass
		
			
	def set_selection_dropdown(self):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboSelection.get_model()
		iter = model.get_iter_first()
		

		# set the item as active
		self.cboSelection.set_active_iter(iter)
		
	def set_export_to_dropdown(self):
		
		# get reference to gettext
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboExportTo.get_model()
		iter = model.get_iter_first()

		# set the item as active
		self.cboExportTo.set_active_iter(iter)
		
		
	def on_cboExportType_changed(self, widget, *args):
		print "on_cboExportType_changed"
		_ = self._
		
		export_type = self.cboExportType.get_active_text()
		
		if export_type == _("Export to Folder"):
			self.fileExportFolder.set_property("visible", True)
			self.cboUploadServices.set_property("visible", False)
		else:
			# show upload services
			self.fileExportFolder.set_property("visible", False)
			self.cboUploadServices.set_property("visible", True)

			# auto select related profiles for this upload service
			self.refresh_profiles_for_uploads()
		
	def on_cboUploadServices_changed(self, widget, *args):
		print "on_cboUploadServices_changed"
		
		# auto select related profiles for this upload service
		self.refresh_profiles_for_uploads()


	def refresh_profiles_for_uploads(self):
		
		# get reference to gettext
		_ = self._
		export_type = self.cboExportType.get_active_text()

		if export_type == _("Upload to Web"):
			# get the upload service name
			service_name = self.cboUploadServices.get_active_text()
			service = self.upload_services[service_name]
			
			# get the preferred / related profiles for this upload service
			project_type, project_target = service.get_export_presets()
			
			# init the dropdown boxes
			self.set_dropdown_values(project_type, self.cboSimpleProjectType)
			self.set_dropdown_values(project_target, self.cboSimpleTarget)

	def on_cboSimpleProjectType_changed(self, widget, *args):
		#set the target dropdown based on the selected project type 
		#first clear the combo
		self.cboSimpleTarget.get_model().clear()
		
		# get reference to gettext
		_ = self._
		
		
		#parse the xml files and get targets that match the project type
		selected_project = self.cboSimpleProjectType.get_active_text()
		project_types = []
		for file in os.listdir(self.project.EXPORT_PRESETS_DIR):
			xmldoc = xml.parse(os.path.join(self.project.EXPORT_PRESETS_DIR,file))
			type = xmldoc.getElementsByTagName("type")
			
			if _(type[0].childNodes[0].data) == selected_project:
				titles = xmldoc.getElementsByTagName("title")
				for title in titles:
					project_types.append(_(title.childNodes[0].data))
		
		
		for item in sorted(project_types):
			self.cboSimpleTarget.append_text(item)
		
		if selected_project == _("All Formats"):
			# default to MP4 for this type
			self.set_dropdown_values(_("OGG (theora/vorbis)"), self.cboSimpleTarget)
			
			# default the profile (based on the current project's profile)
			#self.set_dropdown_values(_(self.project.project_type), self.cboSimpleVideoProfile)
			
		else:
			# choose first taret
			self.cboSimpleTarget.set_active(0)
			

		# default to 1st profile
		#if not self.cboSimpleVideoProfile.get_active_text():
		#	# still no profile, choose the 1st one
		#	self.cboSimpleVideoProfile.set_active(0)
		
		# default quality (to lowest)	
		#self.cboSimpleQuality.set_active(0)
		
		
	def on_cboSimpleTarget_changed(self, widget, *args):
		#set the profiles dropdown based on the selected target
		
		# get reference to gettext
		_ = self._
		
		self.cboSimpleVideoProfile.get_model().clear()
		self.cboSimpleQuality.get_model().clear()
		
		#don't do anything if the combo has been cleared
		if self.cboSimpleTarget.get_active_text():
			selected_target = self.cboSimpleTarget.get_active_text()
			profiles_list = []
			
			#parse the xml to return suggested profiles
			for file in os.listdir(self.project.EXPORT_PRESETS_DIR):
				xmldoc = xml.parse(os.path.join(self.project.EXPORT_PRESETS_DIR,file))
				title = xmldoc.getElementsByTagName("title")
				if _(title[0].childNodes[0].data) == selected_target:
					profiles = xmldoc.getElementsByTagName("projectprofile")
					
					#get the basic profile
					if profiles:
						# if profiles are defined, show them
						for profile in profiles:
							profiles_list.append(_(profile.childNodes[0].data))
					else:
						# show all profiles
						for profile_node in self.profile_list:
							profiles_list.append(_(profile_node[0]))
					
					#get the video bit rate(s)
					videobitrate = xmldoc.getElementsByTagName("videobitrate")
					for rate in videobitrate:
						v_l = rate.attributes["low"].value
						v_m = rate.attributes["med"].value
						v_h = rate.attributes["high"].value
						self.vbr = {_("Low"): v_l, _("Med"): v_m, _("High"): v_h}

					#get the audio bit rates
					audiobitrate = xmldoc.getElementsByTagName("audiobitrate")
					for audiorate in audiobitrate:
						a_l = audiorate.attributes["low"].value
						a_m = audiorate.attributes["med"].value
						a_h = audiorate.attributes["high"].value
						self.abr = {_("Low"): a_l, _("Med"): a_m, _("High"): a_h}
					
					#get the remaining values
					vf = xmldoc.getElementsByTagName("videoformat")
					self.videoformat = vf[0].childNodes[0].data
					vc = xmldoc.getElementsByTagName("videocodec")
					self.videocodec = vc[0].childNodes[0].data
					ac = xmldoc.getElementsByTagName("audiocodec")
					self.audiocodec = ac[0].childNodes[0].data
					sr = xmldoc.getElementsByTagName("samplerate")
					self.samplerate = sr[0].childNodes[0].data
					c = xmldoc.getElementsByTagName("audiochannels")
					self.audiochannels = c[0].childNodes[0].data
					
			# init the profiles combo
			for item in sorted(profiles_list):
				self.cboSimpleVideoProfile.append_text(item)

			#set the quality combo
			#only populate with quality settings that exist
			if v_l or a_l:
				self.cboSimpleQuality.append_text(_("Low"))
			if v_m or a_m:
				self.cboSimpleQuality.append_text(_("Med"))
			if v_h or a_h:
				self.cboSimpleQuality.append_text(_("High"))
				
				
			# default the profile (based on the current project's profile)
			self.set_dropdown_values(_(self.project.project_type), self.cboSimpleVideoProfile)

			# default to 1st profile
			if not self.cboSimpleVideoProfile.get_active_text():
				# still no profile, choose the 1st one
				self.cboSimpleVideoProfile.set_active(0)
				
			# default quality (to lowest)	
			self.set_dropdown_values(_("Low"), self.cboSimpleQuality)
			self.set_dropdown_values(_("Med"), self.cboSimpleQuality)
			
		
	def on_cboSimpleVideoProfile_changed(self, widget, *args):
		
		# get reference to gettext
		_ = self._
		
		#don't do anything if the combo has been cleared
		if self.cboSimpleVideoProfile.get_active_text():
			profile = str(self.cboSimpleVideoProfile.get_active_text())
			
			#does this profile exist?
			p = profiles.mlt_profiles(self.project).get_profile(profile)
			
			if str(p.description()) != profile:
				messagebox.show(_("Error!"), _("%s is not a valid OpenShot profile. Profile settings will not be applied." % profile))
				
			self.init_properties(profile)
		
			#set the value of the project type dropdown on the advanced tab
			self.set_dropdown_values(profile,self.cmbProjectType)

		
	def on_cboSimpleQuality_changed(self, widget, *args):
		
		# get reference to gettext
		_ = self._
		
		#don't do anything if the combo has been cleared
		if self.cboSimpleQuality.get_active_text():
		
			# reset the invalid codecs list
			self.invalid_codecs = []
			
			# Get the quality
			quality = str(self.cboSimpleQuality.get_active_text())
			
			#set the attributes in the advanced tab
			#video format
			self.set_dropdown_values(self.videoformat, self.cboVIdeoFormat)
			
			#videocodec
			self.set_dropdown_values(self.videocodec, self.cboVideoCodec)
			
			#audiocode
			self.set_dropdown_values(self.audiocodec, self.cboAudioCodec)
			
			#samplerate
			self.set_dropdown_values(self.samplerate, self.cboSampleRate)
			
			#audiochannels
			self.set_dropdown_values(self.audiochannels, self.cboChannels)
			
			#video bit rate
			self.cboBitRate.insert_text(0,self.vbr[quality])
			self.cboBitRate.set_active(0)
			
			#audio bit rate
			self.cboAudioBitRate.insert_text(0,self.abr[quality])
			self.cboAudioBitRate.set_active(0)
			
			#check for any invalid codecs and disable
			#the export button if required.
			if self.invalid_codecs:

				if self.use_infobar:
					self.label.set_markup(_("The following codec(s) are missing from your system:\n\n{missing_codecs}\n\nYou may need to install packages such as libavformat-extra to enable the missing codecs.\n<a href='https://answers.launchpad.net/openshot/+faq/1040'>Learn More</a>".format(missing_codecs = "\n".join(self.invalid_codecs))))
					self.infobar.show_all()
				else:
					# no infobar available (use messagebox)
					if self.last_error != self.invalid_codecs:
						messagebox.show(_("Error!"), _("The following codec(s) are missing from your system:\n\n{missing_codecs}\n\nYou may need to install packages such as libavformat-extra to enable the missing codecs.".format(missing_codecs = "\n".join(self.invalid_codecs))))
					
				self.last_error = self.invalid_codecs
				self.btnExportVideo.set_sensitive(False)
			else:
				# hide the missing codec message again
				if self.use_infobar:
					self.last_error = None
					self.infobar.hide()
		
			
	def set_dropdown_values(self, value_to_set, combobox):
		
		# get reference to gettext
		_ = self._
		
		model = combobox.get_model()
		iter = model.get_iter_first()
		while iter:
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

	def init_properties(self, profile):
		
		# get correct gettext method
		_ = self._
		
		# get the mlt profile
		localType = profile 
		p = profiles.mlt_profiles(self.project).get_profile(localType)

		# populate the labels with values
		self.lblHeightValue.set_text(str(p.height()))
		self.lblWidthValue.set_text(str(p.width()))
		self.lblAspectRatioValue.set_text("%s:%s" % (p.display_aspect_num(), p.display_aspect_den()))
		self.lblFrameRateValue.set_text("%.2f" % float(p.fps()))
		self.lblPixelRatioValue.set_text("%s:%s" % (p.sample_aspect_num(), p.sample_aspect_den()))
		
		if p.progressive():
			self.lblProgressiveValue.set_text(_("Yes"))
		else:
			self.lblProgressiveValue.set_text(_("No"))
		
		
		


	def on_frmExportVideo_close(self, widget, *args):
		print "on_frmExportVideo_close"

		
	def on_frmExportVideo_destroy(self, widget, *args):
		print "on_frmExportVideo_destroy"
		self.cancelled = True
		
		# update the project type back to the original (before opening this dialog)
		self.project.project_type = self.original_project_type
		self.project.mlt_profile = None		# clear cached mlt_profile
			
		# create new SDL consumer (to resume playback / preview ability)
		self.project.form.MyVideo.set_profile(self.project.project_type, load_xml=False)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=self.project.is_modified, refresh_xml=True)
		self.project.RefreshXML()

		
	def on_cboExportTo_changed(self, widget, *args):
		print "on_cboExportTo_changed"
		
		# get correct gettext method
		_ = self._
		
		# get the "export to" variable
		localcboExportTo = self.cboExportTo.get_active_text()
		localtxtFileName = str.strip(self.txtFileName.get_text())
		localtxtFileName = localtxtFileName.replace("_%d", "")
		
		if localcboExportTo == _("Image Sequence"):
			self.expander3.set_expanded(True)	# image sequence
			self.expander4.set_expanded(False)	# video settings
			self.expander5.set_expanded(False)	# audio settings
			
			# update filename
			self.txtFileName.set_text(localtxtFileName + "_%d") 
			
			
		elif localcboExportTo == _("Video & Audio"):
			self.expander3.set_expanded(False)	# image sequence
			self.expander4.set_expanded(False)	# video settings
			self.expander5.set_expanded(False)	# audio settings
			
			# update filename
			self.txtFileName.set_text(localtxtFileName) 
			
			
		
	def on_cboProjectType_changed(self, widget, *args):
		print "on_cboProjectType_changed"
		
		# init the project type properties
		self.init_properties(self.cmbProjectType.get_active_text())
		
		
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.cancelled=True
		self.frmExportVideo.destroy()
		
	def on_btnExportVideo_clicked(self, widget, *args):
		print "on_btnExportVideo_clicked"
		
		# get correct gettext method
		_ = self._
		
		
		
		# determine if we are UPLOADING or EXPORTING		
		export_type = self.cboExportType.get_active_text()
		if export_type == _("Upload to Web"):
			# Override filename and location (for temp uploading)
			localfileExportFolder = self.project.USER_DIR
			localtxtFileName = "%s-upload" % str.strip(self.txtFileName.get_text())
		else:
			# Get filename and folder location
			localfileExportFolder = str.strip(self.fileExportFolder.get_filename())
			localtxtFileName = str.strip(self.txtFileName.get_text())
		
		# replace any directory separator characters from the filename
		localtxtFileName = localtxtFileName.replace('/', '_')
			
		# Get general settings
		localcboExportTo = self.cboExportTo.get_active_text()
		
		# get project type
		localcmbProjectType = self.cmbProjectType.get_active_text()
		
		# get Image Sequence settings
		localtxtImageFormat = str.strip(self.cboImageFormat.get_active_text())
		
		# get video settings
		localtxtVideoFormat = self.cboVIdeoFormat.get_active_text()
		localtxtVideoCodec = self.cboVideoCodec.get_active_text()
		localtxtBitRate = str.strip(self.cboBitRate.get_active_text())
		BitRateBytes = self.convert_to_bytes(localtxtBitRate)

		# get audio settings
		localtxtAudioCodec = self.cboAudioCodec.get_active_text()
		localtxtSampleRate = str.strip(self.cboSampleRate.get_active_text())
		localtxtChannels = str.strip(self.cboChannels.get_active_text())
		localtxtAudioBitRate = str.strip(self.cboAudioBitRate.get_active_text())
		AudioBitRateBytes = self.convert_to_bytes(localtxtAudioBitRate)

		# Validate the the form is valid
		if (len(localtxtFileName) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid File Name."))

		elif self.notebook1.get_current_page() == 0 and self.cboSimpleProjectType.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Project Type."))
		
		elif self.notebook1.get_current_page() == 0 and self.cboSimpleTarget.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Target."))
		
		elif self.notebook1.get_current_page() == 0 and self.cboSimpleVideoProfile.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Profile."))
			
		elif self.notebook1.get_current_page() == 0 and self.cboSimpleQuality.get_active_iter() == None:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please select a valid Quality."))
			
		elif (localcboExportTo == _("Image Sequence") and len(localtxtImageFormat) == 0):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Image Format."))
			
		elif (localcboExportTo != _("Image Sequence") and (localtxtVideoFormat == "" or localtxtVideoFormat == None)):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Video Format."))
			
		elif (localcboExportTo != _("Image Sequence") and (localtxtVideoCodec == "" or localtxtVideoCodec == None)):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Video Codec."))
			
		elif (localcboExportTo != _("Image Sequence") and (len(BitRateBytes) == 0 or BitRateBytes == "0")):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Bit Rate."))

		elif (localcboExportTo != _("Image Sequence") and (localtxtAudioCodec == "" or localtxtAudioCodec == None)):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Audio Codec."))
			
		elif (localcboExportTo != _("Image Sequence") and localtxtSampleRate == ""):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Sample Rate."))
			
		elif (localcboExportTo != _("Image Sequence") and localtxtChannels == ""):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Audio Channels."))

		elif (localcboExportTo != _("Image Sequence") and (len(AudioBitRateBytes) == 0 or AudioBitRateBytes == "0")):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid Audio Bit Rate."))
			
		else:
			# VALID FORM

			# create dictionary of all options
			self.render_options = {}
			self.render_options["folder"] = localfileExportFolder
			self.render_options["file"] = localtxtFileName
			self.render_options["export_to"] = localcboExportTo
			
			if localcboExportTo == _("Image Sequence"):
				self.render_options["vcodec"] = localtxtImageFormat
				self.render_options["f"] = localtxtImageFormat
				
			elif localcboExportTo == _("Video & Audio"):
				self.render_options["vcodec"] = localtxtVideoCodec
				self.render_options["f"] = localtxtVideoFormat
				
			self.render_options["b"] = BitRateBytes
			self.render_options["acodec"] = localtxtAudioCodec
			self.render_options["ar"] = localtxtSampleRate
			self.render_options["ac"] = localtxtChannels
			self.render_options["ab"] = AudioBitRateBytes
			
			#check the webm render options are correct - webm can only handle
			#libvorbis and libvpx.
			if localtxtVideoFormat == 'webm' and (localtxtAudioCodec != 'libvorbis' or localtxtVideoCodec != 'libvpx'):
				#override the codecs for webm to prevent a libavformat crash.
				print "Invalid WebM codec detected, forcing WebM defaults"
				self.render_options["acodec"] = 'libvorbis'
				self.render_options["vcodec"] = 'libvpx'
				

			# get the complete path to the new file
			folder1 = self.render_options["folder"]
			file1 = self.render_options["file"]
			self.export_path = "%s.%s" % (os.path.join(folder1, file1), self.render_options["f"])
			
			#check we have write access to the export folder, otherwise avformat will crash
			if os.access(folder1, os.W_OK):

				#check for existing filename before export and confirm overwrite
				if os.path.exists(self.export_path) and export_type == _("Export to Folder"):
					messagebox.show(_("Confirm Overwrite"), _("There is already a video file named %s.%s in the selected export folder. Would you like to overwrite it?") % (file1, self.render_options["f"]), gtk.BUTTONS_YES_NO, self.confirm_overwrite_yes)
				else:
					# no existing file, so export now
					self.do_export()
			
			else:
				messagebox.show(_("OpenShot Error"), _("You do not have write permissions to the selected folder, please select another location."))

	def do_export(self):
		
		#gray out the export window
		self.btnExportVideo.set_sensitive(False)
		self.vbox1.set_sensitive(False)
		
		# flag that an export is in-progress
		self.export_in_progress = True
		
		# get project type
		localcmbProjectType = self.cmbProjectType.get_active_text()
		
		# update the project's profile
		self.project.project_type = localcmbProjectType
		self.project.mlt_profile = None		# clear cached mlt_profile object

		# re-load the xml
		self.project.form.MyVideo.set_profile(self.project.project_type, load_xml=False)
		self.project.form.MyVideo.set_project(self.project, self.project.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="render", render_options=self.render_options)
		
		# Refresh the MLT XML file (because a different frame rate could have been selected,
		# which effects the XML file frame numbers)
		self.project.GenerateXML(os.path.join(self.project.USER_DIR, "sequence.mlt"))
		self.project.form.MyVideo.load_xml()


	def confirm_overwrite_yes(self):
		#user agrees to overwrite the file
		self.do_export()
		
	def update_progress(self, new_percentage):
		
		# get correct gettext method
		_ = self._

		# update the percentage complete
		self.progressExportVideo.set_fraction(new_percentage)
		
		# if progress bar is 100%, close window
		if new_percentage == 1 and self.export_in_progress:
			# show message
			if not self.cancelled:
				title = _("Export Complete")
				message = _("The video has been successfully exported to\n%s") % self.export_path
				
				# prompt user that export is completed
				if has_py_notify:
					try:
						# Use libnotify to show the message (if possible)
						if pynotify.init("OpenShot Video Editor"):
							n = pynotify.Notification(title, message)
							n.show()
					except:
						# use a GTK messagebox
						messagebox.show(title, message)
				else:
					# use a GTK messagebox
					messagebox.show(title, message)
					
				# Re-enable the controls on the screen
				self.btnExportVideo.set_sensitive(True)
				self.vbox1.set_sensitive(True)
				
				# Show Upload screen (if needed)
				export_type = self.cboExportType.get_active_text()
				if export_type == _("Upload to Web"):
					localUploadService = self.cboUploadServices.get_active_text()
					localfileExportFolder = self.project.USER_DIR
					localtxtFileName = "%s-upload" % str.strip(self.txtFileName.get_text())
					localtxtVideoFormat = self.cboVIdeoFormat.get_active_text()

					# close this window
					self.frmExportVideo.destroy()
					
					# show upload screen
					frmUploadVideo = UploadVideo.frmUploadVideo(form=self.form, project=self.project, filename=os.path.join(localfileExportFolder, "%s.%s" % (localtxtFileName, localtxtVideoFormat)), service_name=localUploadService)
					frmUploadVideo.frmUploadVideo.show()
					
				else:
					# export is now finished, so close window
					self.frmExportVideo.destroy()
			
			# flag export as completed
			self.export_in_progress = False
		

	def convert_to_bytes(self, BitRateString):
		bit_rate_bytes = 0
		
		# split the string into pieces
		s = BitRateString.lower().split(" ")
		measurement = "kb"
		
		try:
			# Get Bit Rate
			if len(s) >= 2:
				raw_number_string = s[0]
				raw_measurement = s[1]

				# convert string number to float (based on locale settings)
				raw_number = locale.atof(raw_number_string)

				if "kb" in raw_measurement:
					measurement = "kb"
					bit_rate_bytes = raw_number * 1000.0
					
				elif "mb" in raw_measurement:
					measurement = "mb"
					bit_rate_bytes = raw_number * 1000.0 * 1000.0
					
		except:
			pass

		# return the bit rate in bytes
		return str(int(bit_rate_bytes))
	
	def on_cboVIdeoFormat_changed(self, widget, *args):
		
		self.btnExportVideo.set_sensitive(True)
		
	
	def on_cboVideoCodec_changed(self, widget, *args):
		
		self.btnExportVideo.set_sensitive(True)
		
	
	def on_cboAudioCodec_changed(self, widget, *args):
		
		self.btnExportVideo.set_sensitive(True)
	
			
def main():
	frmExportVideo1 = frmExportVideo()
	frmExportVideo1.run()

if __name__ == "__main__":
	main()

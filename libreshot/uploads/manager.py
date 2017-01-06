import gobject
import gtk
import os, sys
from classes import messagebox

# init the foreign language
from language import Language_Init

vimeo_imported = False
try:
	from vimeo import VimeoClient
	vimeo_imported = True
except:
	print "Failed to import VimeoClient.  Removed Vimeo from upload screen, to allow OpenShot to continue working."


class UploadManager():
	def __init__(self, project, settings):
		self.project = project
		self.settings = settings
	
	def get_services(self):
		services = {}
		services["YouTube"] = YouTubeService(self.project, self.settings)
		if sys.version_info[0] == 2 and sys.version_info[1] == 6 and vimeo_imported == True:
			# vimeo only works on Python 2.6 right now
			services["Vimeo"] = VimeoService(self.project, self.settings)
		return services
	
class YouTubeService():
	def __init__(self, project, settings):
		self.project = project
		self.filename = None
		self.settings = settings
		self.form = None
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
	def initialize(self, form):
		""" Prepare the upload form for this service """
		self.form = form
		
		form.login_divider.set_property("visible", True)
		form.lblUsername.set_property("visible", True)
		form.txtUsername.set_property("visible", True)
		form.lblPassword.set_property("visible", True)
		form.txtPassword.set_property("visible", True)
		form.btnAuthorize.set_property("visible", False)
		form.lblVerification.set_property("visible", False)
		form.txtVerification.set_property("visible", False)
		form.lnkForgot.set_label("http://www.youtube.com")
		form.lnkForgot.set_uri("http://www.youtube.com")
		
		# get saved username (if any)
		if self.settings.app_state["upload_username"]:
			form.txtUsername.set_text(self.settings.app_state["upload_username"])
			
	def get_export_presets(self):
		""" Get a tuple of related export presets for this service (if any) """
		
		# get reference to gettext
		_ = self._
		
		return (_("Web"), _("YouTube-HD"))
			
	def get_authorization_url(self):
		return None
	
	def get_logo(self):
		logo_path = os.path.join(self.project.BASE_DIR, "openshot", "uploads", "logos", "youtube.png")
		return gtk.gdk.pixbuf_new_from_file(logo_path)
	
	def validate(self, form):
		""" Validate the upload form... check for missing values. """
		
		# get reference to gettext
		_ = self._
		
		# get settings
		title = form.txtTitle.get_text()
		start, end = form.txtDescription.get_buffer().get_bounds()
		description = form.txtDescription.get_buffer().get_text(start, end)
		username = form.txtUsername.get_text()
		password = form.txtPassword.get_text()

		# Validate the the form is valid
		if not os.path.isfile(str(self.filename)):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please choose a valid video file."))
			return False

		if not title:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid title."))
			return False

		if not description:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid description."))
			return False

		if not username:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid username."))
			return False
		else:
			# save username
			self.settings.app_state["upload_username"] = username

		if not password:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid password."))
			return False
		
		# form is valid
		return True
	
	def set_file(self, filename):
		self.filename = filename
	
	def start_upload(self, form):
		
		# get reference to gettext
		_ = self._
		
		# Get the absolute path of this project
		import os, sys
		google_api_path = os.path.join(self.project.BASE_DIR, "openshot", "uploads", "youtube")
		if google_api_path not in sys.path:
			sys.path.append(google_api_path)
		
		# get settings
		username = form.txtUsername.get_text()
		password = form.txtPassword.get_text()
		title = form.txtTitle.get_text()
		start, end = form.txtDescription.get_buffer().get_bounds()
		description = form.txtDescription.get_buffer().get_text(start, end)
		
		# remember username (but not password)
		self.settings.app_state["upload_username"] = username
		
		import getopt
		import mimetypes
		import atom.data
		import gdata.youtube
		import gdata.youtube.service
		import gdata.client
		import gdata.data
		import gdata.gauth
		import gdata.youtube.client
		import gdata.youtube.data
		import gdata.sample_util
		import helper

		# prepare a media group object to hold our video's meta-data
		my_media_group = gdata.media.Group(
		  title=gdata.media.Title(text=title),
		  description=gdata.media.Description(description_type='plain',
		                                      text=description),
		  keywords=gdata.media.Keywords(text=''),
		  category=[gdata.media.Category(
		      text='People',
		      scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
		      label='People')],
		  player=None
		)
		
		# create the gdata.youtube.YouTubeVideoEntry to be uploaded
		video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group)

		# create 
		try:
			# disable upload button
			form.btnUpload.set_sensitive(False)
			
			# start upload
			uploader = helper.ResumableUploadDemo(self.filename, chunk_size=1024*64, convert="false", ssl=False, debug=False, host="uploads.gdata.youtube.com", username=username, password=password)
			
			# upload chunks
			entry = uploader.UploadInManualChunks(video_entry, os.path.split(self.filename)[-1], self.on_chunk_complete)
		
		except:
			# Show error message
			messagebox.show(_("Validation Error!"), _("There was an error uploading this video to YouTube.  Please check your username, password, and be sure a valid video file is selected and try again."))
			
			# enable upload button
			form.btnUpload.set_sensitive(True)
			return False


		# enable upload button
		form.btnUpload.set_sensitive(True)
		
		# successful
		return True
	
	def on_chunk_complete(self, *args):
		#print "on_chunk_complete"
		
		total_size = args[0]
		current_bytes = args[1]
		
		if current_bytes >= total_size:
			# don't exceed the total bytes
			current_bytes = total_size
			
		# calculate percentage
		percent = float(current_bytes) / float(total_size)
		gobject.idle_add(self.form.update_progressbar, percent)
		
		# allow other gtk operations to happen
		while gtk.events_pending():
			gtk.main_iteration()
			
			
	
class VimeoService():
	def __init__(self, project, settings):
		self.project = project
		self.filename = None
		self.settings = settings
		self.token = None
		self.token_secret = None
		self.verifier = None
		self.form = None
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		# get tokens (if already authorized)
		if self.settings.app_state["vimeo_token"]:
			self.token = self.settings.app_state["vimeo_token"]
		if self.settings.app_state["vimeo_token_secret"]:
			self.token_secret = self.settings.app_state["vimeo_token_secret"]
		if self.settings.app_state["vimeo_verifier"]:
			self.verifier = self.settings.app_state["vimeo_verifier"]


	def initialize(self, form):
		""" Prepare the upload form for this service """
		
		# test the authentication
		if self.token:
			try:
				self.v = VimeoClient(token=self.token, token_secret=self.token_secret, verifier=self.verifier)
				self.v.cache_timeout = 0
				self.uploader = self.v.get_uploader()
			except:
				# failed to authenticate, erase tokens
				self.token = None
				self.token_secret = None
				self.verifier = None
				self.settings.app_state["vimeo_token"] = ""
				self.settings.app_state["vimeo_token_secret"] = ""
				self.settings.app_state["vimeo_verifier"] = ""
				
				# Show error message
				messagebox.show(_("Validation Error!"), _("Vimeo authentication has expired."))
		
		self.form = form
		form.lblUsername.set_property("visible", False)
		form.txtUsername.set_property("visible", False)
		form.lblPassword.set_property("visible", False)
		form.txtPassword.set_property("visible", False)
		if self.token:
			# already authorized
			form.login_divider.set_property("visible", False)
			form.btnAuthorize.set_property("visible", False)
			form.lblVerification.set_property("visible", False)
			form.txtVerification.set_property("visible", False)
		else:
			# user needs to authorize OpenShot
			form.login_divider.set_property("visible", True)
			form.btnAuthorize.set_property("visible", True)
			form.lblVerification.set_property("visible", True)
			form.txtVerification.set_property("visible", True)			
		form.lnkForgot.set_label("http://www.vimeo.com")
		form.lnkForgot.set_uri("http://www.vimeo.com")
		
	def get_logo(self):
		logo_path = os.path.join(self.project.BASE_DIR, "openshot", "uploads", "logos", "vimeo.png")
		return gtk.gdk.pixbuf_new_from_file(logo_path)
	
	def get_export_presets(self):
		""" Get a tuple of related export presets for this service (if any) """
		
		# get reference to gettext
		_ = self._
		
		return (_("Web"), _("Vimeo-HD"))
	
	def get_authorization_url(self):
		self.v = VimeoClient()
		self.v.cache_timeout = 0
		return self.v.get_authorization_url(permission="write")
	
	def validate(self, form):
		""" Validate the upload form... check for missing values. """

		# get reference to gettext
		_ = self._

		# get code
		verification_code = form.txtVerification.get_text()
		title = form.txtTitle.get_text()
		start, end = form.txtDescription.get_buffer().get_bounds()
		description = form.txtDescription.get_buffer().get_text(start, end)
		
		# Validate the the form is valid
		if not os.path.isfile(str(self.filename)):
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please choose a valid video file."))
			return False

		if not title:
			# Show error message
			messagebox.show(_("Validation Error!"), _("Please enter a valid title."))
			return False

		if not self.token:
			if not description:
				# Show error message
				messagebox.show(_("Validation Error!"), _("Please enter a valid description."))
				return False
	
			if not verification_code:
				# Show error message
				messagebox.show(_("Validation Error!"), _("Please enter a valid verification code.  Click the 'Authorize' button and login to the website.  Confirm the authorization, and copy the verification code."))
				return False
		
		# form is valid
		return True

	def set_file(self, filename):
		self.filename = filename
			
	def start_upload(self, form):

		# get reference to gettext
		_ = self._

		if not self.token:
			# Not Authorized Yet.  
			# get code
			verification_code = form.txtVerification.get_text()

			try:
				# pass code and authorize OpenShot (hopefully)
				self.v.set_verifier(verification_code)
				access_token = self.v.get_access_token()
				
				# save tokens in settings
				self.verifier = verification_code
				self.settings.app_state["vimeo_verifier"] = self.verifier
				
				self.token = access_token.key
				self.settings.app_state["vimeo_token"] = self.token
				
				self.token_secret = access_token.secret
				self.settings.app_state["vimeo_token_secret"] = self.token_secret
				
				# Get uploader object
				self.uploader = self.v.get_uploader()
				
			except:
				# Show error message
				messagebox.show(_("Validation Error!"), _("There was an error authorizing OpenShot.  Please be sure to enter the correct verification code from vimeo.com."))
		
		# get settings
		title = form.txtTitle.get_text()
		start, end = form.txtDescription.get_buffer().get_bounds()
		description = form.txtDescription.get_buffer().get_text(start, end)
		
		try:
			# enable upload button
			form.btnUpload.set_sensitive(False)
			
			# Upload the file to Vimeo
			output = self.uploader.upload(self.filename,chunk=True, chunk_size=64*1024, chunk_complete_hook=self.on_chunk_complete)
			upload_ticket_id = output.get("id")
			output = self.v.videos_upload_complete(ticket_id=upload_ticket_id)
			video_id = output.get("video_id")
			
			# Set the name and description of the video
			self.v.videos_setTitle(title=title, video_id=video_id)
			self.v.videos_setDescription(description=description, video_id=video_id)
		
		except:
			# Show error message
			messagebox.show(_("Validation Error!"), _("There was an error uploading to Vimeo."))
			
			# enable upload button
			form.btnUpload.set_sensitive(True)
			return False
		
		
		# enable upload button
		form.btnUpload.set_sensitive(True)
		
		# successful
		return True

	def on_chunk_complete(self, *args):
		#print "on_chunk_complete"
		
		total_size = args[0]["total_size"]
		chunk_size = args[0]["chunk_size"]
		chunk_id = args[0]["chunk_id"] + 1 # zero based
		
		# calculate current bytes transferred
		current_bytes = chunk_id * chunk_size
		
		if current_bytes >= total_size:
			# don't exceed the total bytes
			current_bytes = total_size
			
		# calculate percentage
		percent = float(current_bytes) / float(total_size)
		gobject.idle_add(self.form.update_progressbar, percent)
		
		# allow other gtk operations to happen
		while gtk.events_pending():
			gtk.main_iteration()


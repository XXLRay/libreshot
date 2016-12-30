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


import os, sys
import operator
import copy
import re
import gobject
import gtk
import goocanvas
import pango
import webbrowser
import subprocess
import shutil
from widgets import openshotwidgets

import classes.effect as effect
from classes import files, lock, messagebox, open_project, project, timeline, tree, video, inputbox, av_formats, clip
from windows import About, FileProperties, NewProject, OpenProject, preferences, Profiles
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
from windows import AddFiles, ClipProperties, ExportVideo, UploadVideo, ImportImageSeq, Titles, TransitionProperties, TreeFiles, IcvTransitions, TreeEffects, TreeHistory, BlenderGenerator, AddToTimeline, ImportTransitions, ExportXML

# init the foreign language
from language import Language_Init
from xdg.IconTheme import *



# Main window of OpenShot
class frmMain(SimpleGtkBuilderApp):


	def __init__(self, path="Main.ui", root="frmMain", domain="OpenShot", project=None, version="0.0.0", **kwargs):
		"""Init the main window"""

		# Load the Glade form using the SimpleGtkBuilderApp module	
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		# project instance
		self.project = project
		self.project.form = self
		self.MyVideo = None
		self.version = version
		self.is_exiting = False
		self.is_edit_mode = False
		self.is_maximized = False
		self.import_files_dialog = None
		self.import_image_seq_dialog = None
		self._SHIFT = False
		self._ALT = False
		self._CTRL = False
		
		# variable for file filtering
		self.filter_category = "Show All"
		
		# initializes history stack
		self.history_index = 0
		self.history_stack = []
		
		# determine the directory OpenShot is running in.  This is used 
		# to correctly load images, themes, etc...
		self.openshot_path = self.project.BASE_DIR

		# variable for timeline drag n drop
		self.dragging = False
		self.timeline_clip_y = 0
		
		# variable for middle mouse clicking / dragging the timeline
		self.is_timeline_scrolling = False
		self.timeline_scroll_start_x = 0
		self.timeline_scroll_start_y = 0
		
		# Init Effects List
		self.effect_list = effect.get_effects(self.project)
		self.blender_list = effect.get_effects(self.project, self.project.BLENDER_DIR)
		
		# Init track variables
		self.AllTracks = []
		(self.CurrentTrack_X, self.CurrentTrack_Y) = 10, 10
		(self.Scroll_Vertical_Value, self.Scroll_Horizontal_Value) = 10, 10

		# Create the Canvas Widget
		hboxTimeline = self.scrolledwindow_Left
		isinstance(hboxTimeline, gtk.HBox)

		# Get reference to the window
		self.App1Window = self.frmMain
		isinstance(self.App1Window, gtk.Window)

		# Create new GooCanvas (and add to form)
		self.MyCanvas_Left = goocanvas.Canvas()
		self.MyCanvas_Left.connect("scroll-event", self.on_scrolledwindow_Left_scroll_event)
		self.MyCanvas_Left.show()

		self.MyCanvas = goocanvas.Canvas()
		self.MyCanvas.connect("scroll-event", self.on_scrolledwindow_Right_scroll_event)
		self.MyCanvas.connect("motion-notify-event", self.on_scrolledwindow_Right_motion)
		self.MyCanvas.connect("button-press-event", self.on_scrolledwindow_Right_press)
		self.MyCanvas.connect("button-release-event", self.on_scrolledwindow_Right_release)
		hboxTimeline.set_border_width(0)
		self.MyCanvas.show()
		
		#canvas for the timeline
		self.TimelineCanvas_Left = goocanvas.Canvas()
		self.TimelineCanvas_Left.connect("scroll-event", self.on_scrolledwindow_Left_scroll_event)
		self.TimelineCanvas_Left.show()
		
		self.TimelineCanvas_Right = goocanvas.Canvas()
		self.TimelineCanvas_Right.connect("scroll-event", self.on_scrolledwindow_Right_scroll_event)
		#self.TimelineCanvas_Right.connect("motion-notify-event", self.on_scrolledwindow_Right_motion)
		#self.TimelineCanvas_Right.connect("button-press-event", self.on_scrolledwindow_Right_press)
		#self.TimelineCanvas_Right.connect("button-release-event", self.on_scrolledwindow_Right_release)
		self.TimelineCanvas_Right.show()

		self.scrolled_win = self.scrolledwindow_Left
		self.scrolled_win.add(self.MyCanvas_Left)
		self.scrolled_win.show()	  

		self.scrolled_win_Right = self.scrolledwindow_Right
		self.scrolled_win_Right.add(self.MyCanvas)
		self.scrolled_win_Right.show()
		
		self.scrolled_win_timeline = self.timelineWindowLeft
		self.scrolled_win_timeline.add(self.TimelineCanvas_Left)
		self.scrolled_win_timeline.show()
		
		self.scrolled_win_timeline_right = self.timelinewindowRight
		self.scrolled_win_timeline_right.add(self.TimelineCanvas_Right)
		self.scrolled_win_timeline_right.show()
		
		# Init the size variables of the main timeline scrolled window.  These are
		# used to offset the drag n drop X,Y by the scrollbar positions.
		self.timeline_scrolled_window_height = 0
		self.timeline_scrolled_window_width = 0

		# Add default node to the tree
		self.myTree = self.treeFiles
		treestore = gtk.TreeStore
		NoItemSelected = gtk.TreeIter

		#set multiple selection on the iconview
		self.icvFileIcons.set_selection_mode(gtk.SELECTION_MULTIPLE)

		# ---------------------------------
		self.drag_type = ""
		self.new_transition = ""
		self.OSTreeFiles = TreeFiles.OpenShotTree(self.treeFiles, self.project)
		self.OSIcvTransitions = None	# this tree is inited in the nbFiles_switch_page signal
		self.OSTreeEffects = None 		# this tree is inited in the nbFiles_switch_page signal
		self.OSTreeBlender = None 		# this tree is inited when the blender dialog is opened
		self.OSTreeHistory = TreeHistory.OpenShotTree(self.treeHistory, self.project)
		# ---------------------------------
		
		#Add a recent projects menu item
		manager = gtk.recent_manager_get_default()
		recent_menu_chooser = gtk.RecentChooserMenu(manager)
		recent_menu_chooser.set_limit(10)
		recent_menu_chooser.set_sort_type(gtk.RECENT_SORT_MRU)
		recent_menu_chooser.set_show_not_found(False)
		recent_menu_chooser.set_show_tips(True)
		filter = gtk.RecentFilter()
		filter.add_pattern("*.osp")
		recent_menu_chooser.add_filter(filter)
		recent_menu_chooser.connect('item-activated', self.recent_item_activated)

		mnurecent = self.mnuRecent
		mnurecent.set_submenu(recent_menu_chooser)

		###################
		
		#load the settings
		self.settings = preferences.Settings(self.project)
		self.settings.load_settings_from_xml()
		
		# limit for the history stack size
		self.max_history_size = int(self.settings.general["max_history_size"])		
		
		#set some application state settings
		x = int(self.settings.app_state["window_width"])
		y = int(self.settings.app_state["window_height"])
		is_max = self.settings.app_state["window_maximized"]

		# resize window		
		self.frmMain.resize(x, y)

		if is_max == "True":
			# maximize window
			self.frmMain.maximize()

		self.vpaned2.set_position(int(self.settings.app_state["vpane_position"]))
		self.hpaned2.set_position(int(self.settings.app_state["hpane_position"]))
		
		if self.settings.app_state["toolbar_visible"] == "True":
			self.tlbMain.show()
		else:
			self.mnuToolbar.set_active(False)
			self.tlbMain.hide()
		
		if self.settings.app_state["history_visible"] == "True":
			self.mnuHistory.set_active(True)
			self.scrolledwindowHistory.show()
			self.nbFiles.set_current_page(0)

		self.project.project_type = self.settings.general["default_profile"]
		self.project.set_theme(self.settings.general["default_theme"])
		
		# Load Autosave settings
		self.load_autosave_settings()
		
		#get the formats/codecs
		melt_command = self.settings.general["melt_command"]
		self.get_avformats(melt_command)
		
		# Show Window
		self.frmMain.show()

		# init the track menu
		self.mnuTrack1 = mnuTrack(None, None, form=self, project=self.project)
		
		# init the clip menu
		self.mnuClip1 = mnuClip(None, None, form=self, project=self.project)
		
		# init the marker menu
		self.mnuMarker1 = mnuMarker(None, None, form=self, project=self.project)
		
		# init the transition menu
		self.mnuTransition1 = mnuTransition(None, None, form=self, project=self.project)
		
		
		# init sub menus
		self.mnuFadeSubMenu1 = mnuFadeSubMenu(None, None, form=self, project=self.project)
		self.mnuRotateSubMenu1 = mnuRotateSubMenu(None, None, form=self, project=self.project)
		self.mnuAnimateSubMenu1 = mnuAnimateSubMenu(None, None, form=self, project=self.project)
		self.mnuPositionSubMenu1 = mnuPositionSubMenu(None, None, form=self, project=self.project)
		self.mnuPlayheadSubMenu1 = mnuPlayheadSubMenu(None, None, form=self, project=self.project)
		self.mnuClip1.mnuFade.set_submenu(self.mnuFadeSubMenu1.mnuFadeSubMenuPopup)
		self.mnuClip1.mnuRotate.set_submenu(self.mnuRotateSubMenu1.mnuRotateSubMenuPopup)
		self.mnuClip1.mnuAnimate.set_submenu(self.mnuAnimateSubMenu1.mnuAnimateSubMenuPopup)
		self.mnuClip1.mnuPosition.set_submenu(self.mnuPositionSubMenu1.mnuPositionSubMenuPopup)
		
		###################

		self.TARGET_TYPE_URI_LIST = 80
		dnd_list = [ ( 'text/uri-list', 0, self.TARGET_TYPE_URI_LIST ) ]	

		# Enable drag n drop on the Treeview and Canvas
		self.file_drop_history = {}	# track the time and filename of each file drag n dropped for this session.
		self.file_drop_messages = []	# track the timestamp of each image sequence drag n drop for this session.
		
		self.myTree.connect('drag_data_received', self.on_drag_data_received)
		self.myTree.connect("button_release_event", self.on_drop_clip_from_tree)
		self.tree_drag_context = None
		self.tree_drag_time = None
		self.myTree.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
		self.myTree.connect('drag_motion', self.motion_tree)

		self.icvFileIcons.connect('drag_data_received', self.on_drag_data_received)
		self.icvFileIcons.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
		self.icvFileIcons.connect('drag_motion', self.motion_tree)

		self.icvTransitions.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
		self.icvTransitions.connect('drag_motion', self.motion_tree)
		
		self.icvEffects.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
		self.icvEffects.connect('drag_motion', self.motion_tree)
		
		self.icvFileIcons.connect_after('drag_begin', self.on_treeFiles_drag_begin)
		
		
		self.icvFileIcons.enable_model_drag_source(gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY)
		
		self.icvTransitions.enable_model_drag_source(gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY)
		
		self.icvEffects.enable_model_drag_source(gtk.DEST_DEFAULT_MOTION |
										 gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,
										 dnd_list, gtk.gdk.ACTION_COPY)


		# Drag signals for the main canvas widget
		self.MyCanvas.drag_dest_set(0, [], 0)
		self.MyCanvas.connect('drag_motion', self.motion_cb)
		self.MyCanvas.connect('drag_drop', self.drop_cb)
		self.MyCanvas.connect('motion_notify_event', self.canvas_motion_notify)
		self.last_files_added = ""
		
		# Drag signals for the track names (left canvas)
		self.MyCanvas_Left.drag_dest_set(0, [], 0)
		self.MyCanvas_Left.connect('drag_motion', self.motion_over_tracks)
		self.MyCanvas_Left.connect('drag_drop', self.drop_cb)
		self.MyCanvas_Left.connect('motion_notify_event', self.canvas_motion_notify)
		self.dropped_on_tracks = False
		
		
		
		# track the cursor, and what position it was last changed
		self.current_cursor = [None, 0, 0, ""]  # Cursor Name, X, Y, Cursor Source

		
		# track when a dragged item reaches the goocanvas
		self.item_detected = False
		self.new_clip = None
		self.new_clip_object = None
		self.new_trans_object = None
		self.new_transition = None
		
		# Init modified status
		self.project.set_project_modified(is_modified=False, refresh_xml=True)
		
		# Refresh the MLT XML file
		# and INIT the video thread
		self.project.RefreshXML()
		
		# Check for files being passed into OpenShot
		self.check_args()
		
		# put initial event on history stack
		history_state = (_("Session started"), self.project.state)
		self.history_stack.append(history_state)
		
		# Start the /queue/ watcher thread
		self.queue_watcher = lock.queue_watcher()
		self.queue_watcher.set_form(self)
		self.queue_watcher.start()
		
		# Set focus on the project files tree, which prevents a focus_in event 
		# on the filter gtkEntry, which messes up the keyboard shortcuts.
		self.treeFiles.grab_focus()


	def load_autosave_settings(self):
		#autosave settings
		self.autosave_object = None
		self.autosave_enabled = False
		if self.settings.general["autosave_enabled"] == "True":
			self.autosave_enabled = True
		self.save_before_playback = False
		if self.settings.general["save_before_playback"] == "True":
			self.save_before_playback = True
		self.autosave_interval = int(self.settings.general["save_interval"]) * 60000 #convert minutes to milliseconds 	

		
	def translate(self, text):
		""" Translate any string to the current locale. """
		return self._(text)


	def get_avformats(self, melt_command):
		
		# get translation object
		_ = self._
		
		# output message
		print "\nDetecting formats, codecs, and filters..."
		
		#populate the codecs
		formats = av_formats.formats(melt_command)
		#video codecs
		self.vcodecs = formats.get_vcodecs()
		#audio codecs	
		self.acodecs = formats.get_acodecs()
		#formats
		self.vformats = formats.get_formats()
		#mlt filters
		self.filters = formats.get_filters()
		#check for frei0r effect library
		self.has_frei0r_installed = formats.has_frei0r_installed()
		
		# show warning about frei0r effects
		if self.has_frei0r_installed == False:
			# warning
			messagebox.show(_("Error"), _("Not all effects can be loaded. OpenShot can not find the frei0r effect library installed. Please install the frei0r-plugins package from your package manager.\n\nOpenShot will still continue to work, but will have less effects to choose from."))
		

	def	save_project_state(self, type):
		print "project state modified"
			
		# if history has changed in the middle of the stack (clear the rest of the stack)
		if self.history_index < (len(self.history_stack) - 1):
			
			# Clear the rest of the history stack
			remove_range = range(self.history_index + 1, len(self.history_stack))
			remove_range.reverse()

			for remove_index in remove_range:
				# remove history item
				self.history_stack.pop(remove_index)
		
		# Increment index
		self.history_index += 1
		
		# retrieves project state property (returns a StringIO object)
		state = self.project.state
		
		# builds a tuple with action description string and StringIO object
		history_state = (type, state)
		
		# appends to history stack
		self.history_stack.append(history_state)
		
		# if history stack is longer than the maximum allowed, it deletes oldest event
		if len(self.history_stack) > self.max_history_size:
			self.history_stack.pop(0)
			self.history_index -= 1
		
		# refreshes history tree in main window
		self.refresh_history()

	
	def refresh_history(self):
		# Tree History refresh
		
		# set the project reference
		self.OSTreeHistory.set_project(self.project)
		
		# repopulate tree
		self.OSTreeHistory.populate_tree(self.history_index)
		
		
	def undo_last(self):
		
		# check if there is something to undo
		if len(self.history_stack) >= 2 and self.history_index > 0:

			# gets last state in history stack
			self.history_index -= 1

			# Get last item in the history stack
			previous_state = self.history_stack[self.history_index]

			# restores project to previous state
			self.project.restore(previous_state[1])
			
			# refreshes history tree in main window and renders project
			self.refresh_history()
			self.refresh()
			

	def redo_last(self):
		
		# check if there is something to redo
		if (self.history_index + 1) <= (len(self.history_stack) - 1):
			
			# gets next state in history stack
			self.history_index += 1

			# Get last item in the history stack
			next_state = self.history_stack[self.history_index]
			
			# restores project to previous state
			self.project.restore(next_state[1])
			
			# refreshes history tree in main window and renders project
			self.refresh_history()
			self.refresh()
			
			
	# double-click signal for a file in the tree
	def on_treeHistory_row_activated(self, widget, *args):
		print "on_treeHistory_row_activated"
		
		# Get the selection
		selection = self.treeHistory.get_selection()
		# Get the selected path(s)
		rows, selected = selection.get_selected_rows()
		
		# Get index of selected history tree item
		if self.history_index != selected[0][0]:
			# get new index
			self.history_index = selected[0][0]
	
			# Get last item in the history stack
			new_state = self.history_stack[self.history_index]
			
			# restores project to previous state
			self.project.restore(new_state[1])
			
			# refreshes history tree in main window and renders project
			self.refresh_history()
			self.refresh()
			
	def on_nbFiles_switch_page(self, widget, *args):
		print "on_nbFiles_switch_page"
		
		# get translation object
		_ = self._
		
		# new page position
		new_page_pos = args[1]
		
		# get main widget in tab
		tabChild = widget.get_nth_page(new_page_pos)
		tabLabel = widget.get_tab_label(tabChild)
		
		# init transitions & effects (if needed)
		if new_page_pos == 1:
			# initialise transitions tab
			if not self.OSIcvTransitions:
				# change cursor to "please wait"
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				
				# init transitions tab
				self.OSIcvTransitions = IcvTransitions.OpenShotTree(self.icvTransitions, self.project)
				print "Init Transitions tab"
				
				# set cursor to normal
				tabLabel.window.set_cursor(None)
			
		elif new_page_pos == 2:	
			# initialise effects tab
			if not self.OSTreeEffects:
				# change cursor to "please wait"
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				tabLabel.window.set_cursor(gtk.gdk.Cursor(150))
				
				# init effects tab
				self.OSTreeEffects = TreeEffects.OpenShotTree(self.icvEffects, self.project)

				print "Init Effects tab"
				
				# set cursor to normal
				tabLabel.window.set_cursor(None)


	def on_txtTransFilter_changed(self, widget, *args):
		print "on_txtTransFilter_changed"
		
		if self.OSIcvTransitions:
			
			# get selected filter
			filter = self.txtTransFilter.get_text()
			
			# clear and re-add effects
			self.OSIcvTransitions.populate(filter=filter)
		
	def on_btnTransFilterCommon_toggled(self, widget, *args):
		print "on_btnTransFilterCommon_toggled"
		
		if self.OSIcvTransitions:
			
			# get selected filter
			filter = self.txtEffectFilter.get_text()
			
			# clear and re-add effects
			self.OSIcvTransitions.populate(category="Common", filter=filter)
		
	def on_btnTransFilterAll_toggled(self, widget, *args):
		print "on_btnTransFilterAll_toggled"
		
		if self.OSIcvTransitions:
			
			# get selected filter
			filter = self.txtEffectFilter.get_text()
			
			# clear and re-add effects
			self.OSIcvTransitions.populate(category="Show All", filter=filter)
			
		
	def on_txtFilesFilter_changed(self, widget, *args):
		print "on_txtFilesFilter_changed"
		
		if self.OSTreeFiles:
			
			# get selected filter
			filter = self.txtFilesFilter.get_text()
			
			# clear and re-add effects
			self.refresh_files(filter=filter)
		
	def on_btnFilesFilterAudio_toggled(self, widget, *args):
		print "on_btnFilesFilterAudio_toggled"
		
		if self.OSTreeFiles:
			
			# get selected filter
			filter = self.txtFilesFilter.get_text()
			
			# clear and re-add effects
			self.refresh_files(category="Audio", filter=filter)

	def on_btnFilesFilterImage_toggled(self, widget, *args):
		print "on_btnFilesFilterImage_toggled"
		
		if self.OSTreeFiles:
			
			# get selected filter
			filter = self.txtFilesFilter.get_text()
			
			# clear and re-add effects
			self.refresh_files(category="Image", filter=filter)
			
	
	def on_btnFilesFilterVideo_toggled(self, widget, *args):
		print "on_btnFilesFilterVideo_toggled"
		
		if self.OSTreeFiles:
			
			# get selected filter
			filter = self.txtFilesFilter.get_text()
			
			# clear and re-add effects
			self.refresh_files(category="Video", filter=filter)
	
	def on_btnFilesFilterAll_toggled(self, widget, *args):
		print "on_btnFilesFilterAll_toggled"
		
		if self.OSTreeFiles:
			
			# get selected filter
			filter = self.txtFilesFilter.get_text()
			
			# clear and re-add effects
			self.refresh_files(category="Show All", filter=filter)


	def on_icvTransitions_drag_begin(self, widget, *args):
		context = args[0]
		
		# update drag type
		self.project.form.drag_type = "transition"
	
		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()
		context.set_icon_pixbuf(pixbuf, 15, 10)
		
	def on_txtFilesFilter_icon_press(self, widget, *args):
		print "on_txtFilesFilter_icon_press"

		if self.OSTreeFiles:
			
			# clear textbox
			self.txtFilesFilter.set_text("")
		
	def on_txtTransFilter_icon_press(self, widget, *args):
		print "on_txtTransFilter_icon_press"

		if self.OSIcvTransitions:
			
			# clear textbox
			self.txtTransFilter.set_text("")
				
	def on_txtEffectFilter_icon_press(self, widget, *args):
		print "on_txtEffectFilter_icon_press"

		if self.OSTreeEffects:
			
			# clear textbox
			self.txtEffectFilter.set_text("")
			
				
	def on_txtEffectFilter_focus_in_event(self, widget, *args):
		# set edit mode
		self.is_edit_mode = True
		
	def on_txtEffectFilter_focus_out_event(self, widget, *args):
		# set edit mode
		self.is_edit_mode = False
		
				
	def on_btnAllEffects_toggled(self, widget, *args):
		print "on_btnAllEffects_toggled"
		
		if self.OSTreeEffects:
			
			# get selected effect filter
			effect_filter = self.txtEffectFilter.get_text()
			
			# clear and re-add effects
			self.OSTreeEffects.populate_tree(category="Show All", filter=effect_filter)
		
	def on_btnVideoEffects_toggled(self, widget, *args):
		print "on_btnVideoEffects_toggled"
		
		if self.OSTreeEffects:
			
			# get selected effect filter
			effect_filter = self.txtEffectFilter.get_text()
			
			# clear and re-add effects
			self.OSTreeEffects.populate_tree(category="Video", filter=effect_filter)
		
	def on_btnAudioEffects_toggled(self, widget, *args):
		print "on_btnAudioEffects_toggled"
		
		if self.OSTreeEffects:
			
			# get selected effect filter
			effect_filter = self.txtEffectFilter.get_text()
			
			# clear and re-add effects
			self.OSTreeEffects.populate_tree(category="Audio", filter=effect_filter)

	def on_txtEffectFilter_changed(self, widget, *args):
		print "on_txtEffectFilter_changed"
		
		if self.OSTreeEffects:
			
			# get selected effect filter
			effect_filter = self.txtEffectFilter.get_text()
			
			# clear and re-add effects
			self.OSTreeEffects.populate_tree(filter=effect_filter)
			
			
	def does_match_filter(self, file_object, filter):
		""" Determine if a filter matches a project file """
		
		# get correct gettext method
		_ = self._
		
		# get just the filename (not the entire path)
		(dirName, file_name) = os.path.split(file_object.name)
		
		# 1st match the filter category
		if self.filter_category == "Show All":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(file_name).lower() or _(filter).lower() in _(file_object.label).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True
			
		elif self.filter_category == "Video" and file_object.file_type == "video":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(file_name).lower() or _(filter).lower() in _(file_object.label).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True
			
		elif self.filter_category == "Audio" and file_object.file_type == "audio":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(file_name).lower() or _(filter).lower() in _(file_object.label).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True
			
		elif self.filter_category == "Image" and file_object.file_type in ("image", "image sequence"):
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(file_name).lower() or _(filter).lower() in _(file_object.label).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True

		# no match to one of these rules
		# show the effect, just incase
		return False

		
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

		
	def on_tlbUndo_clicked(self, widget, *args):
		print "on_tlbUndo_clicked"
		
		# Undo last action
		self.undo_last()
		
	def on_tlbRedo_clicked(self, widget, *args):
		print "on_tlRedo_clicked"
		
		# Undo last action
		self.redo_last()
		
		
	def on_hpanel2_size_allocate(self, widget, *args):
		#print "on_hpanel2_size_allocate"
		if self.MyVideo:
			# refresh sdl
			self.MyVideo.refresh_sdl()
			

	def check_args(self):
		""" Loop through args collection passed to OpenShot, and look for media files,
		or project files """

		# ignore first arg (which is always the path of the python script)
		if len(sys.argv) > 1:

			# loop through the remaining args
			for arg in sys.argv[1:]:

				# is this a file?
				if os.path.exists(arg):

					# is project file?
					if ".osp" in arg:
						# project file, open this project
						self.open_project(arg)
					else:
						# a media file, add it to the project tree
						# if the path isn't absolute, make it absolute
						if not os.path.isabs(arg):
							arg = os.path.abspath(arg)
						self.project.project_folder.AddFile(arg)
						self.project.set_project_modified(is_modified=True, refresh_xml=False)
						
			# refresh window
			self.refresh()


	def recent_item_activated(self, widget):
		"""Activated when an item from the recent projects menu is clicked"""
		import urllib
		
		uri = widget.get_current_item().get_uri()
		
		# clean path to video
		uri = urllib.unquote(uri)
		
		# Strip 'file://' from the beginning
		file_to_open = uri[7:]
		
		# Open the project file
		self.open_project(file_to_open)

		
	def open_project(self, file_to_open):
		# Open the project file
		self.project.Open(file_to_open)

		# set the profile settings in the video thread
		self.project.form.MyVideo.set_profile(self.project.project_type, load_xml=False)
		self.project.form.MyVideo.set_project(self.project, self.project.form, os.path.join(self.project.USER_DIR, "sequence.mlt"), mode="preview")
		self.project.form.MyVideo.load_xml()
		
		#setup autosave
		self.setup_autosave()
		
		# refresh sdl
		self.project.form.MyVideo.refresh_sdl()

		# Update the main form
		self.refresh()
		

	def new(self):
		print "A new %s has been created" % self.__class__.__name__

	def update_icon_theme(self):
		""" Update the icons / buttons with the correct Theme paths """
		
		# be sure theme exists
		if os.path.exists(os.path.join(self.project.THEMES_DIR, self.project.theme)) == False:
			# default back to basic theme
			self.project.set_theme("blue_glass")
		
		# stock icons or not?
		all_buttons = []
		if self.settings.general["use_stock_icons"] == "No":
			# all buttons that need their icon updated
			all_buttons = [(self.tlbPrevious, "image", "previous.png"),
					 (self.tlbPreviousMarker, "image", "previous_marker.png"),
					 (self.tlbSeekBackward, "image", "seek_backwards.png"),
					 (self.tlbPlay, "image", "play_big.png"),
					 (self.tlbSeekForward, "image", "seek_forwards.png"),
					 (self.tlbNextMarker, "image", "next_marker.png"),
					 (self.tlbNext, "image", "next.png"),
					 (self.tlbAddTrack, "image", "plus.png"),
					 (self.tlbArrow, "image", "arrow.png"),
					 (self.tlbRazor, "image", "razor.png"),
					 (self.tlbResize, "image", "resize.png"),
					 (self.tlbSnap, "image", "snap.png"),
					 (self.tlbAddMarker, "image", "add_marker.png"),
					]
		else:
			# elementary icon path (i.e. simple icons)
			elementary_path = os.path.join(self.project.THEMES_DIR, "elementary", "icons")

			# remove images
			all_buttons = [(self.tlbPrevious, "stock", gtk.STOCK_MEDIA_PREVIOUS),
					 (self.tlbPreviousMarker, "stock", gtk.STOCK_GOTO_FIRST),
					 (self.tlbSeekBackward, "stock", gtk.STOCK_MEDIA_REWIND),
					 (self.tlbPlay, "stock", gtk.STOCK_MEDIA_PLAY),
					 (self.tlbSeekForward, "stock", gtk.STOCK_MEDIA_FORWARD),
					 (self.tlbNextMarker, "stock", gtk.STOCK_GOTO_LAST),
					 (self.tlbNext, "stock", gtk.STOCK_MEDIA_NEXT),
					 (self.tlbAddTrack, "stock", gtk.STOCK_ADD),
					 (self.tlbArrow, "image", os.path.join(elementary_path, "arrow.png")),
					 (self.tlbRazor, "stock", gtk.STOCK_CUT),
					 (self.tlbResize, "image", os.path.join(elementary_path, "resize.png")),
					 (self.tlbSnap, "image", os.path.join(elementary_path, "snap.png")),
					 (self.tlbAddMarker, "stock", gtk.STOCK_GOTO_BOTTOM),
					]
		
		# loop through buttons
		for button in all_buttons:
			# get themed icon
			if button[1] == "image":
				theme_img = gtk.Image()
				theme_img.set_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", button[2]))
				theme_img.show()
				
				# set new icon image
				button[0].set_icon_widget(theme_img)
				
			elif button[1] == "stock":
				# set stock id
				button[0].set_icon_widget(None)
				button[0].set_stock_id(button[2])


	def refresh(self, refresh_files = True):

		# get correct gettext method
		_ = self._

		"""Called when the Treeview is active"""
		# Set the title of the window
		self.frmMain.set_title("OpenShot - %s" % (self.project.name))
		
		#set the project reference
		self.OSTreeFiles.set_project(self.project)
		
		# Set the zoom scale
		self.hsZoom.set_value(self.project.sequences[0].scale)

		# render timeline
		self.project.Render()

		# get list of files
		if refresh_files:
			self.refresh_files()
			
		# set icon theme
		self.project.set_theme(self.settings.general["default_theme"])
		self.update_icon_theme()

		
	def refresh_files(self, category=None, filter=None):
		
		# get correct gettext method
		_ = self._
		
		# Clear the file treeview
		self.OSTreeFiles.store.clear()
		
		# set filter category (if any)
		if category:
			self.filter_category = category
			
		# check for an existing filter text
		filter = self.txtFilesFilter.get_text()
		
		if self.scrFileTree.get_property('visible') == True:
			mode = "treeFiles"
		else:
			mode = "icvFileIcons"
		
		if mode == "treeFiles":
			#sort the list of items so parent folders are added before
			#the child items, otherwise files that belong to a folder won't get added.
			items = self.project.project_folder.items
			items.sort(key=operator.attrgetter('parent'))
	
			# Loop through the files, and add them to the project tree
			for item in items:
	
				if isinstance(item, files.OpenShotFile):
					
					# check if a filter matches (if any)
					if not self.does_match_filter(item, filter):
						# NO match, so skip to next filter
						continue
					
					#format the file length field
					milliseconds = item.length * 1000
					time = timeline.timeline().get_friendly_time(milliseconds)
		
					hours = time[2]
					mins = time[3]
					secs = time[4]
					milli = time[5]
					
					if milli > 500:
						secs += 1
					time_str =  "%02d:%02d:%02d" % (hours, mins, secs)
					
		
					# get the thumbnail (or load default)
					pbThumb = item.get_thumbnail(51, 38)
					
					#find parent (if any)
					parent_name = item.parent
					if parent_name == None:
						match_iter = None
					else:
						match_iter = self.search_tree(self.OSTreeFiles.store, self.OSTreeFiles.store.iter_children(None), self.search_match, (1, "%s" % parent_name))
	
					# Add the file to the treeview
					(dirName, fileName) = os.path.split(item.name)
					(fileBaseName, fileExtension)=os.path.splitext(fileName)
					
					self.OSTreeFiles.store.append(match_iter, [pbThumb, fileName, time_str, item.label, item.unique_id])
				   
				elif isinstance(item, files.OpenShotFolder):
					#add folders
					pbThumb = self.treeFiles.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_DIALOG)
					self.OSTreeFiles.store.append(None, [pbThumb, "%s" % item.name, None, item.label, item.unique_id])
			
			# Check for NO files
			if self.project.project_folder.items.__len__() == 0:
				# Add the NO FILES message to the tree
				self.OSTreeFiles.store.append(None, [None, _("Choose a Video or Audio File to Begin"), "", "", ""])
		
		else:
			
			# Refresh the Thumbnail View
			self.refresh_thumb_view("refresh")
		
			
	def search_tree(self,model, iter, func, data):
		while iter:
			if func(model, iter, data):
				return iter
			result = self.search_tree(model, model.iter_children(iter), func, data)
			if result: return result
			iter = model.iter_next(iter)
			
			
	def search_match(self,model, iter, data):
		column, key = data # data is a tuple containing column number, key
		value = model.get_value(iter, column)
		return value == key
	

	def refresh_thumb_view(self, mode=None):
		"""Called when the thumbnail view is active"""
		
		# check for an existing filter text
		filter = self.txtFilesFilter.get_text()
		
		view = self.icvFileIcons
		store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
		
		for item in self.project.project_folder.items:
			#don't show folders in this view
			if isinstance(item, files.OpenShotFile):
				
				# check if a filter matches (if any)
				if not self.does_match_filter(item, filter):
					# NO match, so skip to next filter
					continue
				
				# get resized thumbnail image from the file object
				pbThumb = item.get_thumbnail(102, 76)
				
				# Add the file to the treeview
				(dirName, fileName) = os.path.split(item.name)
				
				# Customize the display text (and combine the label and filename)
				display_text = fileName
				if item.label:
					display_text = "%s (%s)" % (fileName, item.label)

				# add to tree data
				store.append([pbThumb, fileName, display_text, item.unique_id])
	
		# set the iconview settings
		view.set_item_width(130)
		view.set_model(store)
		view.set_pixbuf_column(0)
		view.set_text_column(2)
			
			
		# Check for NO files
		if mode == None and self.project.project_folder.items.__len__() == 0:
			#switch to the detail view
			mnu = mnuTree(None, None, form=self, project=self.project)
			mnu.on_mnuDetailView_activate(None)
			

	def canvas_motion_notify(self, target, event):

		# update cursor variable
		if self.current_cursor[0] != None and self.current_cursor[3] == "canvas":
			# update cursor
			self.current_cursor = [None, int(event.x), int(event.y), ""]
		
			# reset the cursor icon
			self.MyCanvas.window.set_cursor(None)

		
		# update source of the cursor update
		self.current_cursor[3] = "canvas"
		
		
	def on_drop_clip_from_tree (self, wid, event):
		# always drop a clip item (no matter where the cursor is)
		if self.new_clip:
			self.drop_cb(self.new_clip, self.tree_drag_context, self.new_clip.get_bounds().x1, 0.0, self.tree_drag_time)


	def on_drop_trans_from_tree (self, wid, event):
		# always drop a transition item (no matter where the cursor is)
		if self.new_transition:
			self.drop_cb(self.new_transition, self.tree_drag_context, self.new_transition.get_bounds().x1, 0.0, self.tree_drag_time)
		
		
	#////////////////////
	def motion_cb(self, wid, context, x, y, time):
		
		# track context object
		self.tree_drag_context = context
		self.tree_drag_time = time

		# set the drag status
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		
		# This was not dropped on the track names
		self.dropped_on_tracks = False
		
		if self.drag_type == "file":
			# call file drag method
			self.motion_file_drag(wid, context, x, y, time)
			
		elif self.drag_type == "transition":
			# call transition drag method
			self.motion_transition_drag(wid, context, x, y, time)
		
		return True
	
	#////////////////////
	def motion_over_tracks(self, wid, context, x, y, time):
		
		# track context object
		self.tree_drag_context = context
		self.tree_drag_time = time

		# set the drag status
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		
		if self.drag_type == "effect":
			# Yes, dropped on the track names
			self.dropped_on_tracks = True
			
			# Only allow effects
			return True
		else:
			return False
	

	def motion_tree(self, wid, context, x, y, time):
		
		# set the drag status to copy
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		
		return True

	def motion_file_drag(self, wid, context, x, y, time):
		
		# get the veritcal scrollbar value
		vertical_scroll_value = self.vscrollbar2.get_value()
		horizontal_scroll_value = self.hscrollbar2.get_value()

		# Add clip to canvas (upon the first event... but not subsequent events)
		if (self.item_detected == False):
			self.item_detected = True
			detail_view_visible = self.scrFileTree.get_property('visible')
			if detail_view_visible:
				# get the file info from the tree
				selection = self.myTree.get_selection()
				rows, selected = selection.get_selected_rows()
				iters = [rows.get_iter(path) for path in selected]
				# Loop through selected files
				for iter in iters:
					# get file name and id of each file
					file_name = self.myTree.get_model().get_value(iter, 1)
					unique_id = self.myTree.get_model().get_value(iter, 4)
					
					# get the actual file object
					file_object = self.project.project_folder.FindFileByID(unique_id)
					if file_object:
						file_length = file_object.length
					else:
						return
				
			else:
				#get the file info from the iconview
				selected = self.icvFileIcons.get_selected_items()
				if len(selected) > 1:
					return
				i = selected[0][0]
				model = self.icvFileIcons.get_model()
				# Get the name and id of the selected file
				file_name = model[i][1]
				unique_id = model[i][3]
				
				# Get the actual file object
				file_object = self.project.project_folder.FindFileByID(unique_id)
				if file_object:
					file_length = file_object.length
				else:
					return

			# get a new track object
			self.new_clip_object = self.project.sequences[0].tracks[0].AddClip(file_name, "Gold", 0, float(0.0), float(file_length), file_object)

			# get pixels per second
			pixels_per_second = self.new_clip_object.parent.parent.get_pixels_per_second()
			self.new_clip_object.position_on_track = x / pixels_per_second
			
			# Render clip to timeline (at the current drag X coordinate)
			self.new_clip = self.new_clip_object.RenderClip()
			
			# Arrange canvas items
			self.project.sequences[0].raise_transitions()
			self.project.sequences[0].play_head.raise_(None)
			self.project.sequences[0].play_head_line.raise_(None)

		try:
			# get the x and y coordinate of the clip boundry
			new_x = x - self.new_clip.get_bounds().x1 + horizontal_scroll_value
			new_y = y - self.new_clip.get_bounds().y1 + vertical_scroll_value
	
			# don't allow the clip to slide past the beginning of the canvas
			total_x_diff = new_x - 40
			if (self.new_clip.get_bounds().x1 + total_x_diff < 0):
				total_x_diff = 0 - self.new_clip.get_bounds().x1
			
			# be sure that the clip is being dragged over a valid drop target (i.e. a track)
			if self.new_clip_object.get_valid_drop(self.new_clip.get_bounds().x1 + total_x_diff, self.new_clip.get_bounds().y1 + new_y - 25):

				# move the clip based on the event data
				self.new_clip.translate (total_x_diff, new_y - 25)
		
		except:
			# reset the drag n drop 
			self.item_detected = False
			self.new_clip_object = None
			
			
	def motion_transition_drag(self, wid, context, x, y, time):
		
		# get the veritcal scrollbar value
		vertical_scroll_value = self.vscrollbar2.get_value()
		horizontal_scroll_value = self.hscrollbar2.get_value()
		
		# get pixels per second
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		
		transition_name = ""
		transition_desc = ""

		# Add clip to canvas (upon the first event... but not subsequent events)
		if (self.item_detected == False):
			self.item_detected = True

			# get the file info from the iconview
			selected = self.icvTransitions.get_selected_items()
			if len(selected) > 1:
				return
			i = selected[0][0]
			model = self.icvTransitions.get_model()
			transition_name = model[i][1]
			transition_path = model[i][2]

			# get a new transition object
			self.new_trans_object = self.project.sequences[0].tracks[0].AddTransition(transition_name, float(0.0), float(6.0), transition_path)

			# update the position as the user drags the transition around
			self.new_trans_object.position_on_track = x / pixels_per_second

			# Render clip to timeline (at the current drag X coordinate)
			self.new_transition = self.new_trans_object.Render()
			
			# Arrange canvas items
			self.project.sequences[0].raise_transitions()
			self.project.sequences[0].play_head.raise_(None)
			self.project.sequences[0].play_head_line.raise_(None)
	
		try:
			# get the x and y coordinate of the clip boundry
			new_x = x - self.new_transition.get_bounds().x1 + horizontal_scroll_value
			new_y = y - self.new_transition.get_bounds().y1 + vertical_scroll_value

			# don't allow the clip to slide past the beginning of the canvas
			total_x_diff = new_x - 40
			if (self.new_transition.get_bounds().x1 + total_x_diff < 0):
				total_x_diff = 0 - self.new_transition.get_bounds().x1

			# move the clip based on the event data
			self.new_transition.translate (total_x_diff, new_y - 25)
						
			# update the position as the user drags the transition around
			self.new_trans_object.position_on_track = self.new_transition.get_bounds().x1 / pixels_per_second
		
		except:
			# reset the drag n drop 
			self.item_detected = False
			self.new_trans_object = None



	def drop_cb(self, item, context, x, y, time):

		# complete the drag operation
		context.finish(True, False, time)

		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()
		
		# Drop EFFECT
		if self.drag_type == "effect":
			horizontal_value = self.hscrollbar2.get_value()
			vertical_value = self.vscrollbar2.get_value()
			adjusted_y = y + vertical_value
			adjusted_x = x + horizontal_value

			# get new parent track
			drop_track = self.project.sequences[0].get_valid_track(adjusted_x, adjusted_y)
			
			if drop_track:

				# get pixel settings
				pixels_per_second = self.project.sequences[0].get_pixels_per_second()
				
				# Get Effect service name
				selected = self.icvEffects.get_selected_items()
				if len(selected) > 1:
					return
				i = selected[0][0]
				model = self.icvEffects.get_model()
				Name_of_Effect = model[i][1]
				Effect_Service = model[i][2]
				
				if not self.dropped_on_tracks:
					# ONLY APPLY EFFECT TO 1 CLIP
					for clip in drop_track.clips:
						# Find correct clip
						if adjusted_x >= (clip.position_on_track * pixels_per_second) and adjusted_x <= ((clip.position_on_track + clip.length()) * pixels_per_second):
							# Add Effect to Clip
							clip.Add_Effect(Effect_Service)
							self.project.Render()
				else:
					# APPLY EFFECT TO ALL CLIPS ON THIS TRACK
					for clip in drop_track.clips:
						# Add Effect to all Clips
						clip.Add_Effect(Effect_Service)
						self.project.Render()


		# Drop TRANSITION
		if self.new_trans_object:
			# get new parent track
			drop_track = self.new_trans_object.get_valid_drop(self.new_transition.get_bounds().x1, self.new_transition.get_bounds().y1)
			
			if drop_track == None:
				# keep old parent, if no track found
				drop_track = self.new_trans_object.parent
			
			# update the track_A (the primary track)
			if drop_track:
				
				# Drop transition
				self.new_trans_object.drop_canvas_item (self.new_transition)

			else:
				# remove this transition (from the project)
				self.new_trans_object.parent.transitions.remove(self.new_trans_object)
				
				# remove from canvas
				parent = self.new_transition.get_parent()
				if parent:
					child_num = parent.find_child (self.new_transition)
					parent.remove_child (child_num)
		
		
		if self.new_clip_object == None:
			self.item_detected = False
			self.new_trans_object = None
			return
		

		# get the track that the clip was dropped on		
		drop_track = self.new_clip_object.get_valid_drop(self.new_clip.get_bounds().x1, self.new_clip.get_bounds().y1)

		# update and reorder the clips on this track (in the object model)
		self.new_clip_object.update(self.new_clip.get_bounds().x1, self.new_clip.get_bounds().y1, drop_track)		 
		drop_track.reorder_clips()
		
		# Drop CLIP
		if drop_track:

			# deterime the direction of the drag
			if isSnap:
				distance_from_clip = self.new_clip_object.get_snap_difference(self.new_clip_object, self.new_clip)
			else:
				distance_from_clip = 0.0
			
			# Animate the clip to it's new position
			self.new_clip.animate(distance_from_clip, float(drop_track.y_top) - float(self.new_clip.get_bounds().y1) + 2.0, 1.0, 0.0, False, 200, 4, goocanvas.ANIMATE_FREEZE)
			
			# move the clip object on the timeline to correct position (snapping to the y and x of the track)		
			self.new_clip.translate (distance_from_clip, float(drop_track.y_top) - float(self.new_clip.get_bounds().y1) + 2.0)
			
			# update clip's settings
			self.new_clip_object.update(self.new_clip.get_bounds().x1, self.new_clip.get_bounds().y1, drop_track) 
						
			# check if the timeline needs to be expanded
			self.expand_timeline(self.new_clip_object)
			
			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Added clip"))

		else:
			# Remove clip, because of invalid parent
			self.new_clip_object.parent.clips.remove(self.new_clip_object)
			parent = self.new_clip.get_parent()
			if parent:
				child_num = parent.find_child (self.new_clip)
				parent.remove_child (child_num)

		# reset the drag n drop 
		self.item_detected = False
		self.new_clip_object = None
		self.new_trans_object = None
		self.drag_type = None


		return False
	#////////////////////
	
	def expand_timeline(self, clip_object):
		""" Determine if the timeline needs to be expanded. """
		# get end time of dropped clip
		position = clip_object.position_on_track
		length = clip_object.length()
		end_of_clip = position + length
		
		# get length of timeline
		timeline_length = self.project.sequences[0].length
		
		# does timeline need to be extended?
		if end_of_clip > timeline_length:
			# update length of timeline
			self.project.sequences[0].length = end_of_clip
			
			# refresh timeline, but not the treeview/iconview
			self.refresh(False)

	def on_scrolledwindow_Right_size_allocate(self, widget, rectangle, *args):
		# Track the size of the scrolled window as it's resized.  This is used by the 
		# drag n drop methods, to adjust for the scrollbar position.
		self.timeline_scrolled_window_height = rectangle.height
		self.timeline_scrolled_window_width = rectangle.width
		
		# change the page-size of the scrollbar
		self.vscrollbar2.get_adjustment().set_page_size(self.timeline_scrolled_window_height)
		self.hscrollbar2.get_adjustment().set_page_size(self.timeline_scrolled_window_width)

	def on_frmMain_delete_event(self, widget, *args):
		# get correct gettext method
		_ = self._
		
		# pre-destroy event
		# prompt user to save (if needed)
		#if len(self.project.project_folder.items) > 0:
		if self.project.is_modified == True:
			messagebox.show("", _("Save changes to project \"{0}\" before closing?").format(self.project.name), gtk.BUTTONS_NONE, self.exit_openshot_with_save, self.exit_openshot_with_no_save, gtk.MESSAGE_WARNING, _("If you close without saving, your changes will be discarded."), _("Close _without saving"), gtk.RESPONSE_NO, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_YES)
		
			# don't end OpenShot (yet).  A callback from the messagebox will close OpenShot.
			return True
		else:
			# exit openshot
			self.frmMain.destroy()


	def exit_openshot_with_save(self):
		# mark as exiting
		self.is_exiting = True
		
		# call the save button
		self.on_tlbSave_clicked(None)
		
		
	def exit_openshot_with_no_save(self):
		# mark as exiting
		self.is_exiting = True
		
		# call the save button
		self.frmMain.destroy()
		
		
	def on_frmMain_window_state_event(self, widget, event, *args):
		""" determine if screen is maximized or un-maximized """
		#print "on_frmMain_window_state_event"

		if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
			if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
				# MAXIMIZED
				self.is_maximized = True
			else:
				# Un-Maximized
				self.is_maximized = False
				
		# refresh sdl on window resize
		if self.MyVideo:
			self.MyVideo.refresh_sdl()


	def on_frmMain_destroy(self, widget, *args):
		print "on_frmMain_destroy"
		
		# kill the threads
		if self.MyVideo:
			self.MyVideo.amAlive = False
			
		if self.project.thumbnailer:
			self.project.thumbnailer.amAlive = False
			
		if self.queue_watcher:
			self.queue_watcher.amAlive = False
			
		# wait 1/2 second (for threads to stop)
		import time
		time.sleep(0.500)
		
		#get the main window size
		self.settings.app_state["window_maximized"] = str(self.is_maximized)
		self.settings.app_state["window_width"] = self.width
		self.settings.app_state["window_height"] = self.height
		
		#get the position of the dividers
		self.settings.app_state["vpane_position"] = self.vpaned2.get_position()
		self.settings.app_state["hpane_position"] = self.hpaned2.get_position()
				
		#save the settings
		self.settings.save_settings_to_xml()
		
		# Quit the main loop, and exit the program
		self.frmMain.destroy()
		gtk.main_quit()
		

	def on_frmMain_configure_event(self, widget, *args):
		#handles the resize event of the window
		(self.width, self.height) = self.frmMain.get_size()
		
		# refresh sdl on window resize
		if self.MyVideo:
			self.MyVideo.refresh_sdl()

			
			

	def on_mnuNewProject_activate(self, widget, *args):
		print "on_mnuNewProject_activate called with self.%s" % widget.get_name()
		NewProject.frmNewProject(mode="new", project=self.project)



	def on_mnuOpenProject_activate(self, widget, *args):
		print "on_mnuOpenProject_activate called with self.%s" % widget.get_name()
		OpenProject.frmOpenProject(project=self.project)


	def on_tlbOpenProject_clicked(self, widget, *args):
		OpenProject.frmOpenProject(project=self.project)


	def on_mnuImportFiles_activate(self, widget, *args):
		print "on_mnuImportFiles_activate called with self.%s" % widget.get_name()
		
		# show import file dialog
		self.import_files_dialog = AddFiles.frmAddFiles(form=self, project=self.project)
		
		
	def on_mnuImportImageSequence_activate(self, widget, *args):
		print "on_mnuImportImageSequence_activate called with self.%s" % widget.get_name()
		
		# show import file dialog
		ImportImageSeq.frmImportImageSequence(form=self, project=self.project)
		
	def on_mnuImportTransitions_activate(self, widget, *args):
		ImportTransitions.frmImportTransitions(form=self, project=self.project)


	def on_mnuSaveProject_activate(self, widget, *args):
		print "on_mnuSaveProject_activate called with self.%s" % widget.get_name()
		
		# call the save button
		self.on_tlbSave_clicked(widget)
		
	def setup_autosave(self):
		#if an autosave timer object already exists, remove it.
		if self.autosave_object:
			gobject.source_remove(self.autosave_object)
			
		#setup the autosave callback
		if self.autosave_enabled:
			self.autosave_object = gobject.timeout_add(self.autosave_interval,self.autosave_callback)
		
	def autosave_callback(self):
		self.auto_save()
		return True

	def on_mnuSaveProjectAs_activate(self, widget, *args):
		print "on_mnuSaveProjectAs_activate called with self.%s" % widget.get_name()
		NewProject.frmNewProject(mode="saveas", project=self.project)


	def on_mnuMakeMovie1_activate(self, widget, *args):
		print "on_mnuMakeMovie1_activate called with self.%s" % widget.get_name()

		# call toolbar button
		self.on_tlbMakeMovie_clicked(widget)
		
	def on_mnuExportXML_activate(self, widget, *args):
		print "on_mnuExportXML_activate called with self.%s" % widget.get_name()
		
		# open the export XML window
		ExportXML.frmExportXML(project=self.project)
			
	def on_mnuQuit1_activate(self, widget, *args):
		print "on_mnuQuit1_activate called with self.%s" % widget.get_name()

		# Quit
		self.on_frmMain_delete_event(widget)
		

	def on_mnuPreferences_activate(self, widget, *args):
		print "on_mnuPreferences_activate called with self.%s" % widget.get_name()

		# get correct gettext method
		_ = self._

		# open preferences window
		preferences.PreferencesMgr(project=self.project, form=self)
		
		
	def on_mnuNewTitle_activate(self, widget, *args):
		print "on_mnuNewTitle_activate called with self.%s" % widget.get_name()
		Titles.frmTitles(form=self, project=self.project)


	def on_mnu3dTitle_activate(self, widget, *args):
		print "on_mnu3dTitle_activate called with self.%s" % widget.get_name()
		
		# show import file dialog
		BlenderGenerator.frm3dGenerator(form=self, project=self.project)
		

		
	def on_mnuAbout_activate(self, widget, *args):
		print "on_mnuAbout_activate called with self.%s" % widget.get_name()

		# Open About Dialog
		About.frmAbout(version=self.version, project=self.project)

	def on_mnuHelpContents_activate(self, widget, *args):
		print "on_mnuHelpContents_activate called with self.%s" % widget.get_name()

		# get translation object
		_ = self._

		#show Help contents
		try:
			#need to use the relative path until we can get
			#yelp to properly index the file.
			#then we should be able to use:
			helpfile = "ghelp:openshot"
			screen = gtk.gdk.screen_get_default()
			gtk.show_uri(screen, helpfile, gtk.get_current_event_time())
		except:
			messagebox.show(_("Error!"), _("Unable to open the Help Contents. Please ensure the openshot-doc package is installed."))
		
			
	def on_mnuReportBug_activate(self, widget, *args):
		print "on_mnuReportBug_activate called with self.%s" % widget.get_name()
		
		# get translation object
		_ = self._
		
		#open the launchpad bug page with the users default browser
		try:
			webbrowser.open("https://bugs.launchpad.net/openshot/+filebug")
		except:
			messagebox.show(_("Error!"), _("Unable to open the Launchpad web page."))
			
	
	def on_mnuAskQuestion_activate(self, widget, *args):
		print "on_mnuAskQuestion_activate called with self.%s" % widget.get_name()
		
		# get translation object
		_ = self._
		
		#open the launchpad answers page with the users default browser
		try:
			webbrowser.open("https://answers.launchpad.net/openshot/+addquestion")
		except:
			messagebox.show(_("Error!"), _("Unable to open the Launchpad web page."))
			
	def on_mnuTranslate_activate(self, widget, *args):
		print "on_mnuTranslate_activate called with self.%s" % widget.get_name()
		
		# get translation object
		_ = self._
		
		#open the launchpad answers page with the users default browser
		try:
			webbrowser.open("https://translations.launchpad.net/openshot")
		except:
			messagebox.show(_("Error!"), _("Unable to open the Launchpad web page."))
	
	
	def on_mnuDonate_activate(self, widget, *args):
		# get translation object
		_ = self._
		
		#open the launchpad answers page with the users default browser
		try:
			webbrowser.open("http://www.openshot.org/donate/")
		except:
			messagebox.show(_("Error!"), _("Unable to open the web page."))
	
			
	def on_mnuToolbar_toggled(self, widget, *args):
		print "on_mnuToolbar_toggled called with self.%s" % widget.get_name()
		
		if not self.mnuToolbar.get_active():
			self.tlbMain.hide()
			self.settings.app_state["toolbar_visible"] = "False"
		else:
			self.tlbMain.show()
			self.settings.app_state["toolbar_visible"] = "True"
			
	def on_mnuHistory_toggled(self, widget, *args):
		print "on_mnuHistory_toggled called with self.%s" % widget.get_name()
		
		if not self.mnuHistory.get_active():
			self.settings.app_state["history_visible"] = "False"
			self.scrolledwindowHistory.hide()
		else:
			self.settings.app_state["history_visible"] = "True"
			self.scrolledwindowHistory.show()
			self.nbFiles.set_current_page(3)
			
	def on_mnuFullScreen_toggled(self, widget, *args):
		print "on_mnuFullScreen_toggled called with self.%s" % widget.get_name()
		
		if not self.mnuFullScreen.get_active():
			self.frmMain.unfullscreen()
		else:
			self.frmMain.fullscreen()
			
			
	def on_tlbImportFiles_clicked(self, widget, *args):
		print "on_tlbImportFiles_clicked called with self.%s" % widget.get_name()
		
		# show import file dialog
		self.import_files_dialog = AddFiles.frmAddFiles(form=self, project=self.project)


	def on_tlbSave_clicked(self, widget, *args):
		#print "on_tlbSave_clicked called with self.%s" % widget.get_name()
		
		project_name = self.project.name
		project_folder = self.project.folder

		# determine if this project has been saved before
		if (project_folder != self.project.USER_DIR):

			# save file exists... so just save again
			self.project.Save("%s/%s.osp" % (project_folder, project_name))
			
			# Is openshot exiting?
			if self.is_exiting:
				self.frmMain.destroy()

		else:

			# save file doesn't exist, so open "save as" window
			NewProject.frmNewProject(mode="saveas", project=self.project)


	def auto_save(self):
		
		project_name = self.project.name
		project_folder = self.project.folder

		# determine if this project has been saved before and if the 
		# project needs to be saved.
		if (project_folder != self.project.USER_DIR and self.tlbSave.get_property('sensitive') and self.autosave_enabled):
			# save file exists... so just save again
			print "Autosaving..."

			#normal save
			self.project.Save("%s/%s.osp" % (project_folder, project_name))


	def on_tlbMakeMovie_clicked(self, widget, *args):
		print "on_tlbMakeMovie_clicked called with self.%s" % widget.get_name()
		
		# get translation object
		_ = self._
		
		for track in self.project.sequences[0].tracks:
			# Loop through all clips on this track
			if len(track.clips) == 0:
				emptytimeline = True
			else:
				emptytimeline = False
				# don't bother continuing, as we know the timeline is not empty
				break
		#don't try and render an empty timeline
		if emptytimeline:
			messagebox.show(_("Openshot Error!"), _("The timeline is empty, there is nothing to export."))
			return
		
		# show frmExportVideo dialog
		self.frmExportVideo = ExportVideo.frmExportVideo(form=self, project=self.project)


	def on_mnuUploadVideo_activate(self, widget, *args):
		print "on_mnuUploadVideo_activate called with self.%s" % widget.get_name()

		# show frmExportVideo dialog
		self.frmUploadVideo = UploadVideo.frmUploadVideo(form=self, project=self.project)

	# double-click signal for a file in the tree
	def on_treeFiles_row_activated(self, widget, *args):
		print "on_treeFiles_row_activated"
		
		# Get the selection
		selection = self.treeFiles.get_selection()
		# Get the selected path(s)
		rows, selected = selection.get_selected_rows()

		# call the preview menu signal
		mnu = mnuTree(rows, selected, form=self, project=self.project)
		mnu.on_mnuPreview_activate(None)
		
	# double click event for thumbnail file view
	def on_icvFileIcons_item_activated(self, widget, *args):
		print "on_icvFileIcons_item_activated"
		
		#iconview is active
		selected = self.icvFileIcons.get_selected_items()
		
		#show the right click menu
		mnu = mnuTree(None, selected, form=self, project=self.project)
		mnu.on_mnuPreview_activate(None)
		

	def on_treeFiles_drag_begin(self, widget, *args):
		context = args[0]
		
		# update drag type
		self.project.form.drag_type = "file"

		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()
		context.set_icon_pixbuf(pixbuf, 15, 10)
		
		
	def on_canvas_drag_motion(self, wid, context, x, y, time):
		print " *** motion detected"


	def on_canvas_drag_drop(self, widget, *args):
		print " *** DROP detected"

	def on_hsVideoProgress_change_value(self, widget, *args):

		# get the percentage of the video progress 0 to 100
		video_progress_percent = float(self.hsVideoProgress.get_value()) / 100.0
		
		# Refresh the MLT XML file (if not in preview/override mode)
		if self.MyVideo.mode != "override":
			self.project.RefreshXML()
		
		# determine frame number
		new_frame = int(float(self.MyVideo.get_length() - 1) * video_progress_percent)

		# jump to this frame
		self.MyVideo.seek(new_frame)

	def on_hsVideoProgress_value_changed(self, widget, *args):
		#print "on_hsVideoProgress_value_changed called with self.%s" % widget.get_name()		
		pass

	
	def on_tlbSnapshot_clicked(self, widget, *args):
		print "on_tlbSnapshot_clicked"
		
		self.get_frame_snapshot()
		
	
	def on_tlbPreviousMarker_clicked(self, widget, *args):
		print "on_tlbPreviousMarker_clicked"
		
		# get the previous marker object (if any)
		playhead_position = self.project.sequences[0].play_head_position
		marker = self.project.sequences[0].get_marker("left", playhead_position)
		is_playing = False
		if self.MyVideo:
			is_playing = self.MyVideo.isPlaying
		
		if marker:
			# determine frame number
			frame = self.project.fps() * marker.position_on_track
			
			# seek to this time
			if self.MyVideo:
				# Refresh the MLT XML file
				self.project.RefreshXML()
				
				# Seek and refresh sdl
				self.MyVideo.seek(int(frame))

				# check isPlaying
				if is_playing == False:
					self.MyVideo.pause()
				
			# move play-head
			self.project.sequences[0].move_play_head(marker.position_on_track)
		
	def on_tlbSeekBackward_clicked(self, widget, single_frame=False, *args):
		print "on_tlbSeekBackward_clicked"
		
		# get correct gettext method
		_ = self._

		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# get the current speed
		current_speed = self.MyVideo.get_speed()
		position = self.MyVideo.position()
		
		# check if frame-stepping or rewinding
		if single_frame == False:
			# SEEK BACKWARDS
			# calcualte new speed
			if current_speed >= 0:
				new_speed = -1
			else:
				new_speed = (current_speed * 2) 
			
			# set the new speed
			self.MyVideo.set_speed(new_speed)
			
			# update the preview tab label
			if new_speed == 1:
				self.lblVideoPreview.set_text(_("Video Preview"))
			else:
				self.lblVideoPreview.set_text(_("Video Preview (%sX)" % int(new_speed)))
		else:
			n_frames = 1
			if self._SHIFT:
				# step length is one second
				n_frames = int(round(self.project.fps()))
			# or just step 1 frame
			self.MyVideo.seek(position - n_frames)
			
	
	def on_tlbSeekForward_clicked(self, widget, single_frame=False, *args):
		print "on_tlbSeekForward_clicked"
		
		# get correct gettext method
		_ = self._
		
		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# get the current speed
		current_speed = self.MyVideo.get_speed()
		position = self.MyVideo.position()
		
		# check if frame-stepping or rewinding
		if single_frame == False:
			# SEEK FORWARD
			# calcualte new speed
			if current_speed <= 0:
				new_speed = 2
			else:
				new_speed = current_speed * 2
			
			# set the new speed
			self.MyVideo.set_speed(new_speed)
			
			# update the preview tab label
			if new_speed == 1:
				self.lblVideoPreview.set_text(_("Video Preview"))
			else:
				self.lblVideoPreview.set_text(_("Video Preview (%sX)" % int(new_speed)))
		else:
			n_frames = 1
			if self._SHIFT:
				# step length is one second
				n_frames = int(round(self.project.fps()))
			# or just step 1 frame
			self.MyVideo.seek(position + n_frames)
			
	
	def on_tlbNextMarker_clicked(self, widget, *args):
		print "on_tlbNextMarker_clicked"
		
		# get the previous marker object (if any)
		playhead_position = self.project.sequences[0].play_head_position
		marker = self.project.sequences[0].get_marker("right", playhead_position)
		is_playing = False
		if self.MyVideo:
			is_playing = self.MyVideo.isPlaying
		
		if marker:
			# determine frame number
			frame = self.project.fps() * marker.position_on_track
			
			# Refresh the MLT XML file
			self.project.RefreshXML()
			
			# seek and refresh sdl
			self.MyVideo.seek(int(frame))

			# check isPlaying
			if is_playing == False:
				self.MyVideo.pause()
				
			# move play-head
			self.project.sequences[0].move_play_head(marker.position_on_track)
			
	
	def on_tlbAddMarker_clicked(self, widget, *args):
		print "on_tlbAddMarker_clicked"
		
		# get the current play_head position
		playhead_position = self.project.sequences[0].play_head_position
		
		# add a marker
		m = self.project.sequences[0].AddMarker("marker name", playhead_position)
		
		# refresh the screen
		if m:
			m.Render()
			
			# raise-play head
			self.project.sequences[0].raise_play_head()
		
		
	def on_tlbPrevious_clicked(self, widget, *args):
		print "on_tlbPrevious_clicked called with self.%s" % widget.get_name()

		# get correct gettext method
		_ = self._

		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# seek to the first frame and reset the speed to 1X
		self.MyVideo.set_speed(1)
		self.MyVideo.seek(0)
		
		if self.MyVideo.isPlaying == False:
			self.MyVideo.set_speed(0)
		else:
			self.MyVideo.set_speed(1)
		
		# set the horizontal scrollbar back to zero	
		self.hscrollbar2.set_value(0)
		
		# update video preview tab
		self.lblVideoPreview.set_text(_("Video Preview"))
			

	def on_tlbPlay_clicked(self, widget, *args):
		print "on_tlbPlay_clicked called with self.%s" % widget.get_name()
		
		# get correct gettext method
		_ = self._
		
		# Get the current speed
		current_speed = self.MyVideo.get_speed()
		
		# Refresh the MLT XML file
		self.project.RefreshXML()

		# is video stopped?
		if current_speed == 0:
			
			# start video
			self.MyVideo.play()
			
			# update video preview tab
			self.lblVideoPreview.set_text(_("Video Preview"))

		else:
			
			# stop video
			self.MyVideo.pause()
			
			# update video preview tab
			self.lblVideoPreview.set_text(_("Video Preview (Paused)"))


	def on_tlbNext_clicked(self, widget, *args):
		print "on_tlbNext_clicked called with self.%s" % widget.get_name()

		# get correct gettext method
		_ = self._

		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# seek to the last frame and reset the speed to 1X
		self.MyVideo.set_speed(1)
		self.MyVideo.seek(self.MyVideo.get_length())
		
		if self.MyVideo.isPlaying == False:
			self.MyVideo.set_speed(0)
		else:
			self.MyVideo.set_speed(1)
		
		# update video preview tab
		self.lblVideoPreview.set_text(_("Video Preview"))
			
			
	def on_tlbStop_clicked(self, widget, *args):
		print "on_tlbStop_clicked called with self.%s" % widget.get_name()
		
		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# stop thread from running
		self.MyVideo.pause()

		# refresh sdl
		self.MyVideo.refresh_sdl()
		
		
	def on_frmMain_key_press_event(self, widget, event):
		print "on_frmMain_key_press_event"
		# Get the key name that was pressed
		keyname = str.lower(gtk.gdk.keyval_name(event.keyval))


		if self.is_edit_mode == False:
			# Detect SHIFT, ALT, and CTRL keys
			if event.keyval == gtk.keysyms.Shift_L or event.keyval == gtk.keysyms.Shift_R:
				# Toggle SHIFT mode
				self._SHIFT = True

			elif keyname == 'alt_l' or keyname == 'alt_r' or keyname == 'iso_level3_shift':
				# Toggle ALT mode
				self._ALT = True

			elif (keyname == 'control_l' or keyname == 'control_r') or (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
				# Toggle CTRL mode
				self._CTRL = True
			
			
			# Detect other keys
			if keyname == "c":
				# Cut all tracks at this point (whereever the playhead is)
				self.cut_at_playhead()
				return True
			
			if keyname == "j":
				#print "J Key was Pressed"
				self.on_tlbSeekBackward_clicked(widget)
				return True
				
			elif keyname == "k" or keyname == "space":
				#print "K Key was Pressed"
				self.on_tlbPlay_clicked(widget)
				return True
				
			elif keyname == "l":
				#print "L Key was Pressed"
				self.on_tlbSeekForward_clicked(widget)
				return True
				
			elif keyname == "left":
				#print "LEFT Key was Pressed"
				self.on_tlbSeekBackward_clicked(widget, single_frame=True)
				return True
				
			elif keyname == "right":
				#print "RIGHT Key was Pressed"
				self.on_tlbSeekForward_clicked(widget, single_frame=True)
				return True
				
			elif keyname == "up":
				#print "UP Key was Pressed"
				self.on_tlbPreviousMarker_clicked(widget, event)
				return True
				
			elif keyname == "down":
				#print "DOWN Key was Pressed"
				self.on_tlbNextMarker_clicked(widget, event)
				return True
			
			elif keyname == "tab":
				# toggle the trim / arrow modes
				self.toggle_mode()
				return True
			
			elif keyname == "d" and self._CTRL:
				#snapshot
				self.get_frame_snapshot()
				return True
				
			elif keyname == "m":
				#add a marker when the key is pressed
				self.on_tlbAddMarker_clicked(widget)
				return True
			
				
	def on_frmMain_key_release_event(self, widget, event):
		keyname = str.lower(gtk.gdk.keyval_name(event.keyval))

		if event.keyval == gtk.keysyms.Shift_L or event.keyval == gtk.keysyms.Shift_R:
			# Toggle SHIFT mode
			self._SHIFT = False

		elif keyname == 'alt_l' or keyname == 'alt_r' or keyname == 'iso_level3_shift':
			# Toggle ALT mode
			self._ALT = False

		elif (keyname == 'control_l' or keyname == 'control_r') or (event.state == gtk.gdk.CONTROL_MASK) or (event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK):
			# Toggle CTRL mode
			self._CTRL = False
		
					
	def toggle_mode(self):
		
		# determine what cursor mode is enable (arrow, razor, snap, etc...)
		(isArrow, isRazor, isSnap, isResize) = self.get_toolbar_options()
		
		# only execute code if button is toggled (i.e. this gets called on un-toggle event also)
		if isResize:
			# toggle to arrow
			self.tlbArrow.set_active(True)
		else:
			# toggle to razor
			self.tlbResize.set_active(True)
			
	def cut_at_playhead(self):
		""" Cut all clips and transitions at the current play head position """
		
		canvas_right = self.project.form.MyCanvas
		root_right = canvas_right.get_root_item()
		
		# Get playhead position
		current_position = self.project.sequences[0].play_head_position
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		x = current_position * pixels_per_second

		# Loop through all tracks
		for track in self.project.sequences[0].tracks:
			# Loop through all clips on this track
			for clip in list(track.clips):
				# is playhead overlapping this clip
				if current_position > clip.position_on_track and current_position < (clip.position_on_track + clip.length()):
					# get the canvas object
					canvas_item = clip.get_canvas_child(root_right, clip.unique_id)
					# divide clip
					clip.divide_clip(x, canvas_item)
					
	
	def get_frame_snapshot(self):
		'''Extracts a frame from each (non-audio) clip at the current
		   playhead position'''
		# Get playhead position
		current_position = self.project.sequences[0].play_head_position
		# get frames per second
		fps = self.project.fps()
		# Loop through all tracks
		for track in self.project.sequences[0].tracks:
			# Loop through all clips on this track
			for clip in track.clips:
				# is playhead overlapping this clip
				if current_position > clip.position_on_track and current_position < (clip.position_on_track + clip.length()):
					#only extract frames from non-audio files
					if clip.file_object.file_type != "audio":
						clip_position = (current_position + clip.start_time) - clip.position_on_track
						frame_position = round(clip_position * fps)
						#when extracting a frame, it gets added to the 
						#project as a new file.
						#Here we get the name of the existing clip, and
						#modify it to make it unique.
						filepath = clip.file_object.project.folder
						(fileBaseName, fileExtension)=os.path.splitext(clip.name)
						#add a number to the end of the filename.
						#get the next available number for the file
						blnFind = True 
						intNum = 0
						while blnFind == True:
							intNum += 1
							blnFind = os.path.exists(os.path.join(filepath, fileBaseName + str(intNum) + ".png"))
			
						#this will be the new name of the snapshot image file
						new_name = fileBaseName +  str(intNum) + ".png"
						#extract the frame
						self.project.thumbnailer.get_thumb_at_frame(clip.file_object.name, int(frame_position), new_name)
						#add the file to the project in the project folder
						self.project.project_folder.AddFile(self.project.folder + "/" + new_name)
						#refresh the tree
						self.refresh_files()
					


	def get_toolbar_options(self):
		""" return the options selected on the toolbar """
		
		isArrow = self.tlbArrow.get_active()
		isRazor = self.tlbRazor.get_active()
		isSnap = self.tlbSnap.get_active()
		isResize = self.tlbResize.get_active()
		
		return (isArrow, isRazor, isSnap, isResize)
	

	def on_tlbAddTrack_clicked(self, widget, *args):

		# get correct gettext method
		_ = self._

		# Add a new track to the timeline		
		self.project.sequences[0].AddTrack(_("Track %s") % str(len(self.project.sequences[0].tracks) + 1))
		self.project.Render()


	def on_tlbRemoveTrack_clicked(self, widget, *args):
		print "on_tlbRemoveTrack_clicked called with self.%s" % widget.get_name()


	def on_tlbRazor_toggled(self, widget, *args):
		print "on_tlbRazor_clicked called with self.%s" % widget.get_name()
			
		# get the razor line image
		imgRazorLine = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "razor_line_with_razor.png"))
		pixRazorLine = imgRazorLine.get_pixbuf()
		
		# set cursor to normal
		self.MyCanvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.display_get_default(), pixRazorLine, 0, 28))
			
			

	def on_tlbArrow_toggled(self, widget, *args):
		print "on_tlbArrow_clicked called with self.%s" % widget.get_name()	
			
		# set cursor to normal
		self.MyCanvas.window.set_cursor(None)
			
			
	def on_btnZoomIn_clicked(self, widget, *args):
		print "on_btnZoomIn_clicked"

		# get the value of the zoom slider
		zoom_slider = self.hsZoom.get_value()
		
		# zoom slower if too close
		if zoom_slider > 10:
			
			# subtract 5 units
			self.hsZoom.set_value(zoom_slider - 5)
		
		elif zoom_slider <= 5:
			# Move the zoom slider to the left
			if zoom_slider - 1 > 0:
				# subtract 5 units
				self.hsZoom.set_value(zoom_slider - 1)
			else:
				# set to 0
				self.hsZoom.set_value(0)
		
		elif zoom_slider <= 10:

			# subtract 5 units
			self.hsZoom.set_value(zoom_slider - 2)

		self.center_playhead()
		
	def center_playhead(self):
		# get current scroll position
		current_scroll_pixels = self.hscrollbar2.get_value()
		# get playhead position
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		playhead_time = self.project.sequences[0].play_head_position
		playhead_pixels = playhead_time * pixels_per_second
			
		# get the middle of the window
		screen_width = (self.width / 2) - 100
		
		if playhead_pixels > (current_scroll_pixels + screen_width):
			# scroll to last scroll position
			self.hscrollbar2.set_value(playhead_pixels - screen_width)
			
		
	def on_btnZoomOu_clicked(self, widget, *args):
		print "on_btnZoomOu_clicked"
		
		# get the value of the zoom slider
		zoom_slider = self.hsZoom.get_value()

		# zoom slower if too close
		if zoom_slider > 11:
			
			# Move the zoom slider to the right    
			if zoom_slider + 5 < 200:
				# add 5 units
				self.hsZoom.set_value(zoom_slider + 5)
			else:
				# set to 200 
				self.hsZoom.set_value(200)
		
		elif zoom_slider < 4:
			
				# add 1 units
				self.hsZoom.set_value(zoom_slider + 1)
		
		elif zoom_slider <= 11:

			# add 2 units
			self.hsZoom.set_value(zoom_slider + 2)	
			
		
	def on_hsZoom_value_changed(self, widget, *args):

		# get correct gettext method
		_ = self._
		
		# get current horizontal scroll position & time
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		current_scroll_pixels = self.hscrollbar2.get_value()
		current_scroll_time = current_scroll_pixels / pixels_per_second

		# get the value of the zoom slider (this value represents the number of seconds 
		# between the tick marks on the timeline ruler
		new_zoom_value = widget.get_value()

		# set the scale
		self.project.sequences[0].scale = int(new_zoom_value)
		
		# update zoom label
		self.lblZoomDetail.set_text(_("%s seconds") % int(new_zoom_value))

		# re-render the timeline with the new scale
		self.project.Render()
		
		# scroll to last scroll position
		self.scroll_to_last(current_scroll_time)	

		
	def on_hsZoom_change_value(self, widget, *args):

		# get correct gettext method
		_ = self._
		
		# get the value of the zoom slider (this value represents the number of seconds 
		# between the tick marks on the timeline ruler
		new_zoom_value = widget.get_value()

		# update zoom label
		self.lblZoomDetail.set_text(_("%s seconds") % int(new_zoom_value))
		
		
	def scroll_to_last(self, current_scroll_time):
		# get position of play-head
		pixels_per_second = self.project.sequences[0].get_pixels_per_second()
		goto_pixel = current_scroll_time * pixels_per_second

		# scroll to last scroll position
		self.hscrollbar2.set_value(goto_pixel)


	
	def scroll_to_playhead(self):
		""" scroll the horizontal scroll if the playhead is playing, and moves
		past the center point of the screen. """ 
		
		if self.MyVideo.isPlaying:
			
			self.center_playhead()

		
	def on_tlbResize_toggled(self, widget, *args):
		print "on_tlbResize_toggled called with self.%s" % widget.get_name() 
			
		
	def on_tlbSnap_toggled(self, widget, *args):
		print "on_tlbSnap_toggled called with self.%s" % widget.get_name()
	
		
	def on_drag_motion(self, wid, context, x, y, time):

		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()

		# Set the drag icon
		context.set_icon_pixbuf(pixbuf, 0, 0)


	def on_drag_data_received(self, widget, context, x, y, selection, target_type, timestamp):

		# get correct gettext method
		_ = self._

		# close the AddFile dialog (if it's still open)
		if self.import_files_dialog:
			self.import_files_dialog.frmAddFiles.destroy()

		# get the list of files that were dropped in the tree
		uri = selection.data.strip()
		uri_splitted = uri.split() # we may have more than one file dropped
		
		for uri in uri_splitted:
			# track which files have been added (and the time they were added)
			history_key = "%s-%s" % (uri, timestamp)
			if history_key not in self.file_drop_history:
				self.file_drop_history[history_key] = True
			else:
				# duplicate file, skip to next file
				continue
			
			# change cursor to "please wait"
			self.myTree.window.set_cursor(gtk.gdk.Cursor(150))
			
			# get the file path
			path = self.project.project_folder.get_file_path_from_dnd_dropped_uri(uri)
			
			# The total number of ok files selected (not folders)
			total_ok_files = 0
			# The total number of broken files selected (could not be imported)
			total_broken_files = 0
			# The total number of files already imported selected
			total_duplicate_files = 0
			# The total number of folders selected
			total_folders = 0
			# add file to current project
			result = self.project.project_folder.AddFile(path, session=timestamp)
			
			# parse the results and add to the total
			total_ok_files += result[0]
			total_broken_files += result[1]
			total_duplicate_files += result[2]
			total_folders += result[3]
		
			# The number of total selected files, not including folders
			total_files = total_ok_files + total_broken_files + total_duplicate_files
		
			# print error messages (if needed)
		
			if total_files == 0:
				if total_folders == 1:
					messagebox.show(_("Empty Folder "), _("The selected folder was empty."))
				else:
					messagebox.show(_("Empty Folders"), _("The selected folders were empty."))
			else:
				if total_files == total_broken_files:
					if total_files == 1:
						messagebox.show(_("Unsupported File Type"), _("OpenShot does not support this file type."))
					else:
						messagebox.show(_("Unsupported File Types"), _("OpenShot supports none of the file types of the selected files."))
			
				elif total_files == total_duplicate_files:
					if total_files == 1:
						messagebox.show(_("Already Imported File"), _("The selected file has already been imported to the project."))
					else:
						messagebox.show(_("Already Imported Files"), _("All of the selected files have already been imported to the project."))
			
				elif total_ok_files == 0:
					messagebox.show(_("File Import Error"), _("The selected files either have an unsupported file type or have already been imported to the project."))
				
				elif total_ok_files > 0:
					#update the last used folder setting
					(dirName, fileName) = os.path.split(path)
					self.settings.app_state["import_folder"] = dirName
			
		# refresh the form (i.e. add new items to the treeview)
		self.refresh_files()
		
		# set cursor to normal
		self.myTree.window.set_cursor(None)

		return False


	def on_scrolledwindow_Left_scroll_event(self, widget, *args):
		# Don't bubble up the scroll event.  This prevents the scroll wheel from 
		# scrolling the individual canvas.
		self.on_scrolledwindow_Right_scroll_event(widget, *args)
		return True


	def on_scrolledwindow_Right_scroll_event(self, widget, *args):

		# Is the CTRL key pressed?
		if args[0].state & gtk.gdk.CONTROL_MASK:
			# CTRL Key - thus we need to zoom in or out
			if args[0].direction == gtk.gdk.SCROLL_DOWN:
				# Zoom Out
				self.on_btnZoomOu_clicked(widget)
			else:
				# Zoom In
				self.on_btnZoomIn_clicked(widget)
			
			
		else:
			
			# Regular scroll... scroll canvas vertical
			## Manually scroll the scrollbars
			if args[0].direction == gtk.gdk.SCROLL_DOWN:
				widget = self.vscrollbar2  
				vertical_value = widget.get_value() + 10
	
				# Update vertical scrollbar value
				widget.set_value(vertical_value)
	
				# Get horizontal value
				horizontal_scrollbar = self.hscrollbar2
				horizontal_value = horizontal_scrollbar.get_value()
	
				# scroll the canvases
				self.MyCanvas.scroll_to(horizontal_value, vertical_value)
				self.MyCanvas_Left.scroll_to(0, vertical_value)
			else:
				widget = self.vscrollbar2	   
				vertical_value = widget.get_value() - 10
	
				# Update vertical scrollbar value
				widget.set_value(vertical_value)
	
				# Get horizontal value
				horizontal_scrollbar = self.hscrollbar2
				horizontal_value = horizontal_scrollbar.get_value()
	
				# scroll the canvases
				self.MyCanvas.scroll_to(horizontal_value, vertical_value)
				self.MyCanvas_Left.scroll_to(0, vertical_value)

		# Don't bubble up the scroll event.  This prevents the scroll wheel from 
		# scrolling the individual canvas.   
		return True

	def on_scrolledwindow_Right_motion(self, item, event, *args):
		#print "on_scrolledwindow_Right_motion"

		# Is the middle mouse button pressed?
		if self.is_timeline_scrolling:
			
			# determine how much to move the canvas
			x_diff = self.timeline_scroll_start_x - event.x
			y_diff = self.timeline_scroll_start_y - event.y
			
			# Update vertical scrollbar value
			vertical_scrollbar = self.vscrollbar2
			vertical_value = vertical_scrollbar.get_value()  
			vertical_scrollbar.set_value(vertical_value + y_diff)
	
			# Update horizontal scrollbar value
			horizontal_scrollbar = self.hscrollbar2
			horizontal_value = horizontal_scrollbar.get_value()
			horizontal_scrollbar.set_value(horizontal_value + x_diff)

		return False

	def on_scrolledwindow_Right_press(self, item, event, *args):
		# toggle timeline dragging ON
		if event.button == 2:
			self.is_timeline_scrolling = True
			self.timeline_scroll_start_x = event.x
			self.timeline_scroll_start_y = event.y
			
		return False
			
	def on_scrolledwindow_Right_release(self, item, event, *args):
		# toggle timeline dragging OFF
		if event.button == 2:
			self.is_timeline_scrolling = False
			
		return False

	def on_vscrollbar2_value_changed(self, widget, *args):

		isinstance(widget, gtk.VScrollbar)		
		vertical_value = widget.get_value()

		# Get horizontal value
		horizontal_scrollbar = self.hscrollbar2
		horizontal_value = horizontal_scrollbar.get_value()

		# scroll the canvases
		self.MyCanvas.scroll_to(horizontal_value, vertical_value)
		self.MyCanvas_Left.scroll_to(horizontal_value, vertical_value)

	def on_treeFiles_button_press_event(self,treeview, event, *args):
		"""This shows the right click menu"""
		#print "on_treeFiles_button_press_event"
		
		# Right click
		if (event.button == 3):
			
			results = treeview.get_path_at_pos(int(event.x),int(event.y))
			# Get the selection
			selection = treeview.get_selection()
			# if an item was right clicked
			if results:
				
				# Get the path to the right clicked item
				path = results[0]
				
				# if the item wasn't selected, unselect all items
				if not selection.path_is_selected(path):
					selection.unselect_all()
				
				# Select the clicked item
				selection.select_path(path)
				
				# Get the model and paths of the selected items
				model, paths = selection.get_selected_rows()
				
				# Item menu
				mnu = mnuTree(model, paths, form=self, project=self.project)
			   	
			else:
				# Basic menu
				mnu = mnuTree(None, None, form=self, project=self.project)
			
			# Display the menu
			mnu.showmnu(event, treeview)
				
			return True
		
	# double click event for thumbnail file view
	def on_icvFileIcons_button_press_event(self, widget, event, *args):
		"""This shows the right click menu"""

		#Right click
		if (event.button == 3):
			model = self.icvFileIcons.get_model()
			
			# Get the path to the right clicked item
			path = self.icvFileIcons.get_path_at_pos(int(event.x),int(event.y))
			
			# if an item was right clicked
			if path:
				# if the item wasn't selected, unselect all items
				if not self.icvFileIcons.path_is_selected(path):
					self.icvFileIcons.unselect_all()
			
				# Select the clicked item
				self.icvFileIcons.select_path(path)
				
				# Get a list of the paths of all selected items
				paths = self.icvFileIcons.get_selected_items()
				
				# Item menu
				mnu = mnuTree(model, paths, form=self, project=self.project)
			else:
				# Basic menu
				mnu = mnuTree(None, None, form=self, project=self.project)
			
			# Show the right click menu
			mnu.showmnu(event, widget)


	def on_hscrollbar2_value_changed(self, widget, *args):

		isinstance(widget, gtk.HScrollbar)		
		horizontal_value = widget.get_value()

		# Get vertical value
		vertical_scrollbar = self.vscrollbar2
		vertical_value = vertical_scrollbar.get_value()

		# scroll the canvases
		self.MyCanvas.scroll_to(horizontal_value, vertical_value)
		self.TimelineCanvas_Right.scroll_to(horizontal_value, 0.0)

		
		
class mnuTrack(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_track_menu.ui", root="mnuTrackPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project
		
	def showmnu(self, event, widget):
		# show the popup menu
		self.mnuTrackPopup.show_all()
		self.mnuTrackPopup.popup( None, None, None, event.button, event.time)
		
		# selected track
		self.selected_track = widget


	def on_mnuAddTrackAbove_activate(self, event, *args):
		print "on_mnuAddTrackAbove_activate clicked"
		
		# get correct gettext method
		_ = self._
		
		# Add track
		self.project.sequences[0].AddTrack(_("Track %s") % str(len(self.project.sequences[0].tracks) + 1), position="above", existing_track=self.selected_track)
		
		# refresh the interface
		self.project.Render()

		
	def on_mnuAddTrackBelow_activate(self, event, *args):
		print "on_mnuAddTrackBelow_activate clicked"
		
		# get correct gettext method
		_ = self._
		
		# Add Track
		self.project.sequences[0].AddTrack(_("Track %s") % str(len(self.project.sequences[0].tracks) + 1), position="below", existing_track=self.selected_track)
		
		# refresh the interface
		self.project.Render()
		
		
	def on_mnuRenameTrack_activate(self, event, *args):
		print "on_mnuRenameTrack_activate clicked"
		
		# get correct gettext method
		_ = self._
		
		# replace bad characters
		track_name = self.selected_track.name.replace("&amp;", "&")
		
		# get the new name of the track
		text = inputbox.input_box(title="Openshot", message=_("Please enter a track name."), default_text=track_name)
		
		if text:
			# replace bad characters
			text = text.replace("&", "&amp;")
			
			# rename track
			self.project.sequences[0].rename_track(self.selected_track, text)
			
			#refresh the interface
			self.project.Render()
	
	def on_mnuClearTrack_activate(self, event, *args):
		print "on_mnuClearTrack_activate clicked"

		# remove clip from parent track
		self.selected_track.clips = []
			
		# remove clip from parent track
		self.selected_track.transitions = []
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Cleared track"))
		# refresh the interface
		self.form.refresh()
		
	def on_mnuRemoveTrack_activate(self, event, *args):
		print "on_mnuRemoveTrack_activate clicked"
		
		# remove this track from it's parent sequence
		self.selected_track.parent.tracks.remove(self.selected_track)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed track"))
		# refresh the interface
		self.form.refresh()
		
	def on_mnuMoveTrackUp_activate(self, event, *args):
		print "on_mnuMoveTrackUp_activate clicked"
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Moved track up"))
		
		# get index of current track
		index_existing_track = self.selected_track.parent.tracks.index(self.selected_track)
		
		if index_existing_track > 0:
			# remove existing track
			self.selected_track.parent.tracks.remove(self.selected_track)
			
			# insert at new position
			self.selected_track.parent.tracks.insert(index_existing_track - 1, self.selected_track)
			
			# refresh the interface
			self.project.Render()
			
		
	def on_mnuMoveTrackDown_activate(self, event, *args):
		print "on_mnuMoveTrackDown_activate clicked"
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Moved track down"))
		
		# get index of current track
		index_existing_track = self.selected_track.parent.tracks.index(self.selected_track)
		
		if index_existing_track < len(self.selected_track.parent.tracks) - 1:
			# remove existing track
			self.selected_track.parent.tracks.remove(self.selected_track)
			
			# insert at new position
			self.selected_track.parent.tracks.insert(index_existing_track + 1, self.selected_track)
			
			# refresh the interface
			self.project.Render()
		
class mnuMarker(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_marker_menu.ui", root="mnuMarkerPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project
		
		
	def showmnu(self, event, widget):
		# show the popup menu
		self.mnuMarkerPopup.show_all()
		self.mnuMarkerPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_marker = widget
		
		
	def on_mnuRemoveMarker_activate(self, event, *args):
		print "on_mnuRemoveMarker_activate clicked"
		
		# remove this marker
		self.selected_marker.parent.markers.remove(self.selected_marker)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed marker"))
				
		# refresh timeline
		self.form.refresh()
		
		
class mnuTransition(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_transition_properties.ui", root="mnuTransitionPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project
		
		
	def showmnu(self, event, object, canvas_item):
		
		# get correct gettext method
		_ = self._
		
		if object.type == "transition":
			self.mnuMask.get_children()[0].set_label(_("Convert to Mask"))
			self.mnuRemoveTransition.get_children()[0].set_label(_("Remove Transition"))
			self.mnuReverseTransition.set_sensitive(True)
		elif object.type == "mask":
			self.mnuMask.get_children()[0].set_label(_("Convert to Transition"))
			self.mnuRemoveTransition.get_children()[0].set_label(_("Remove Mask"))
			self.mnuReverseTransition.set_sensitive(False)
		
		# show the popup menu
		self.mnuTransitionPopup.show_all()
		self.mnuTransitionPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_transition = object
		self.selected_transition_item = canvas_item
		
		
	def on_mnuTransitionProperties_activate(self, event, *args):
		print "on_mnuTransitionProperties_activate"
		
		# show frmExportVideo dialog
		self.frmTransitionProperties = TransitionProperties.frmTransitionProperties(form=self, project=self.project, current_transition=self.selected_transition)
		
		
		
	def on_mnuDuplicate_activate(self, event, *args):
		print "on_mnuDuplicate_activate"
		
		# create new transition
		parent_track = self.selected_transition.parent
		new_trans = parent_track.AddTransition(self.selected_transition.name, self.selected_transition.position_on_track + 3, self.selected_transition.length, self.selected_transition.resource)
		new_trans.reverse = self.selected_transition.reverse
		new_trans.softness = self.selected_transition.softness
		new_trans.type = self.selected_transition.type
		new_trans.mask_value = self.selected_transition.mask_value
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Duplicated transition")
		
		# render to timeline
		new_trans.Render()

		
	def on_mnuMask_activate(self, event, *args):
		print "on_mnuMask_activate"
		
		# get correct gettext method
		_ = self._
		
		# update type
		if self.selected_transition.type == "transition":
			self.selected_transition.type = "mask"

		elif self.selected_transition.type == "mask":
			self.selected_transition.type = "transition"
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Changed transition type"))
		
		# remove from canvas
		parent = self.selected_transition_item.get_parent()
		child_num = parent.find_child (self.selected_transition_item)
		parent.remove_child (child_num)
		
		# refresh timeline
		self.selected_transition.Render()
		
		
	def on_mnuRemoveTransition_activate(self, event, *args):
		print "on_mnuRemoveTransition_activate clicked"
		
		# find middle x coordinate
		clip_length_pixels = self.selected_transition_item.get_bounds().x2  - self.selected_transition_item.get_bounds().x1
		x_middle = self.selected_transition_item.get_bounds().x1 #+ (clip_length_pixels / 2.0)
		
		# find middle y coordinate
		clip_height_pixels = self.selected_transition_item.get_bounds().y2  - self.selected_transition_item.get_bounds().y1
		y_middle = self.selected_transition_item.get_bounds().y1 + (clip_height_pixels / 2.0)
		
		# animate the clip to turn invisible
		self.selected_transition_item.connect("animation-finished", self.transition_removed)
		self.selected_transition_item.animate(x_middle, y_middle, 0.0, 0.0, True, 200, 4, goocanvas.ANIMATE_FREEZE)

		
	def transition_removed(self, *args):
		# remove this clip (from the project)
		self.selected_transition.parent.transitions.remove(self.selected_transition)
		
		# remove from canvas
		parent = self.selected_transition_item.get_parent()
		child_num = parent.find_child (self.selected_transition_item)
		parent.remove_child (child_num)
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed transition"))

		
	def on_mnuShiftTransitions_activate (self, event, *args):
		print "on_mnuShiftTransitions_activate clicked"
		
		shift = 0.0
		start_of_selected = float(self.selected_transition.position_on_track)
		
		# Get previous transition (if any)
		previous_transition = None
		transitions_on_track = self.selected_transition.parent.transitions
		index_of_selected_transition = transitions_on_track.index(self.selected_transition) - 1
		if index_of_selected_transition >= 0:
			previous_transition = transitions_on_track[index_of_selected_transition]

		# get correct gettext method
		_ = self._
		
		# get the amount of time the transitions are shifted
		text = inputbox.input_box(title="OpenShot", message=_("Please enter the # of seconds to shift the transitions:"), default_text="5.0")
		if text:
			# convert to peroid decimal
			text = text.replace(',', '.')
			try:
				# amount to shift
				shift = float(text)
				
				# is shift negative (i.e. shifting to the left)
				if shift < 0.0:
					# negative shift
					if previous_transition:
						end_of_previous = previous_transition.position_on_track + float(previous_transition.length)
						if shift + start_of_selected < end_of_previous:
							# get difference between previous clip, and selected clip
							shift = end_of_previous - start_of_selected
					
					else:
						# no previous clip, is clip going to start before timeline?
						if shift + start_of_selected < 0.0:
							# get difference between clip and beginning of timeline
							shift = 0.0 - start_of_selected
			except:
				# invalid shift amount... default to 0
				shift = 0.0
				
		if shift:
			# loop through clips, and shift
			for tr in self.selected_transition.parent.transitions:
				start = float(tr.position_on_track)
				if start >= start_of_selected:
					tr.position_on_track = start + shift

			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Shifted transitions"))

			# render timeline
			self.form.refresh()



	def on_mnuReverseMarker_activate(self, event, *args):
		print "on_mnuReverseMarker_activate clicked"
		
		# set the reverse property
		if self.selected_transition.reverse:
			self.selected_transition.reverse = False
		else:
			self.selected_transition.reverse = True
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True)
		
		# remove from canvas
		parent = self.selected_transition_item.get_parent()
		child_num = parent.find_child (self.selected_transition_item)
		parent.remove_child (child_num)
		
		# refresh timeline
		self.selected_transition.Render()
		
		
class mnuFadeSubMenu(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_fade_menu.ui", root="mnuFadeSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuFadeSubMenuPopup.show_all()
		self.mnuFadeSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuFade_activate(self, event, *args):
		print "on_mnuFade_activate"
		
		# update the gettext method
		_ = self._
		
		# get name of animation
		fade_name = ""
		try:
			fade_name = event.get_label()
		except:
			# older versions of pygtk need this prop
			fade_name = event.children()[0].get_text()
		
		if fade_name == _("No Fade"):
			# remove fade from clip
			self.selected_clip.audio_fade_in = False
			self.selected_clip.audio_fade_out = False
			self.selected_clip.audio_fade_in_amount = 2.0
			self.selected_clip.audio_fade_out_amount = 2.0
			self.selected_clip.video_fade_in = False
			self.selected_clip.video_fade_out = False
			self.selected_clip.video_fade_in_amount = 2.0
			self.selected_clip.video_fade_out_amount = 2.0
			
		elif fade_name == _("Fade In (Fast)"):
			# fade in (fast)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = False
			self.selected_clip.audio_fade_in_amount = 2.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = False
			self.selected_clip.video_fade_in_amount = 2.0
			
		elif fade_name == _("Fade Out (Fast)"):
			# fade out (fast)
			self.selected_clip.audio_fade_in = False
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_out_amount = 2.0
			self.selected_clip.video_fade_in = False
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_out_amount = 2.0
			
		elif fade_name == _("Fade In and Out (Fast)"):
			# fade in and out (fast)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_in_amount = 2.0
			self.selected_clip.audio_fade_out_amount = 2.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_in_amount = 2.0
			self.selected_clip.video_fade_out_amount = 2.0
			
		elif fade_name == _("Fade In (Slow)"):
			# fade in (slow)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = False
			self.selected_clip.audio_fade_in_amount = 4.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = False
			self.selected_clip.video_fade_in_amount = 4.0
			
		elif fade_name == _("Fade Out (Slow)"):
			# fade out (slow)
			self.selected_clip.audio_fade_in = False
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_out_amount = 4.0
			self.selected_clip.video_fade_in = False
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_out_amount = 4.0
			
		elif fade_name == _("Fade In and Out (Slow)"):
			# fade in and out (slow)
			self.selected_clip.audio_fade_in = True
			self.selected_clip.audio_fade_out = True
			self.selected_clip.audio_fade_in_amount = 4.0
			self.selected_clip.audio_fade_out_amount = 4.0
			self.selected_clip.video_fade_in = True
			self.selected_clip.video_fade_out = True
			self.selected_clip.video_fade_in_amount = 4.0
			self.selected_clip.video_fade_out_amount = 4.0
			
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip fade")
		
class mnuRotateSubMenu(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_rotate_menu.ui", root="mnuRotateSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuRotateSubMenuPopup.show_all()
		self.mnuRotateSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuRotate_activate(self, event, *args):
		print "on_mnuRotate_activate"
		
		# update the gettext method
		_ = self._
		
		# get name of animation
		rotate_name = ""
		try:
			rotate_name = event.get_label()
		except:
			# older versions of pygtk need this prop
			rotate_name = event.children()[0].get_text()
			
		if rotate_name == _("No Rotation"):
			# clear rotation
			self.selected_clip.rotation = 0.0

		elif rotate_name == _("Rotate 90 (Right)"):
			# rotate 90 to the right
			self.selected_clip.rotation += 90.0
			
		elif rotate_name == _("Rotate 90 (Left)"):
			# rotate 90 to the left
			self.selected_clip.rotation += -90.0
			
		elif rotate_name == _("Rotate 180 (Flip)"):
			# flip video clip
			self.selected_clip.rotation += 180
			
		# prevent unneeded high numbers
		if abs(self.selected_clip.rotation) == 360:
			print "back to zero"
			self.selected_clip.rotation = 0
			
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip rotation")
		
class mnuPlayheadSubMenu(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_playhead_menu.ui", root="mnuPlayheadSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuPlayheadSubMenuPopup.show_all()
		self.mnuPlayheadSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		
	def on_mnuCutAllClips_activate(self, event, *args):
		print "on_mnuCutAllClips_activate"
		
		# call the cut at playhead method
		self.form.cut_at_playhead()
		

		
		
class mnuAnimateSubMenu(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_animate_menu.ui", root="mnuAnimateSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuAnimateSubMenuPopup.show_all()
		self.mnuAnimateSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuAnimate_activate(self, event, *args):
		print "on_mnuAnimate_activate"
		
		# update the gettext method
		_ = self._
		
		# get name of animation
		animation_name = ""
		try:
			animation_name = event.get_label()
		except:
			# older versions of pygtk need this prop
			animation_name = event.children()[0].get_text()
		
		# init vars
		start = self.selected_clip.keyframes["start"]
		end = self.selected_clip.keyframes["end"]
		halign = "centre"
		valign = "centre"
		
		# calculate the center coordinates (based on height & width)
		center_x = 0.0
		center_y = 0.0
		if start.width != 100:
			center_x = start.width / 2.0
		if start.height != 100:
			center_y = start.height / 2.0
		top = -100 + center_y
		bottom = 100 + center_y
		left = -100 + center_x
		right = 100 + center_x


		if animation_name == _("No Animation"):
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)



		######### ZOOM ...
		elif animation_name == _("Zoom In (100% to 150%)"):
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(150.0, 150.0, -25.0, -25.0, None)

		elif animation_name == _("Zoom In (50% to 100%)"):
			start.set_all(50.0, 50.0, 25.0, 25.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)

		elif animation_name == _("Zoom In (75% to 100%)"):
			start.set_all(75.0, 75.0, 12.5, 12.5, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)

		elif animation_name == _("Zoom Out (100% to 75%)"):
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(75.0, 75.0, 12.5, 12.5, None)

		elif animation_name == _("Zoom Out (100% to 50%)"):
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(50.0, 50.0, 25.0, 25.0, None)
			
		elif animation_name == _("Zoom Out (150% to 100%)"):
			start.set_all(150.0, 150.0, -25.0, -25.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)
			

		######### CENTER TO ...
		elif animation_name == _("Center to Top"):
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, center_x, top, None)

		elif animation_name == _("Center to Left"):
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, left, center_y, None)
			
		elif animation_name == _("Center To Right"):
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, right, center_y, None)
			
		elif animation_name == _("Center to Bottom"):
			start.set_all(None, None, center_x, center_y, None)
			end.set_all(None, None, center_x, bottom, None)

		######### TO CENTER ...
		elif animation_name == _("Left to Center"):
			start.set_all(None, None, left, center_y, None)
			end.set_all(None, None, center_x, center_y, None)
			
		elif animation_name == _("Right to Center"):
			start.set_all(None, None, right, center_y, None)
			end.set_all(None, None, center_x, center_y, None)
			
		elif animation_name == _("Top to Center"):
			start.set_all(None, None, center_x, top, None)
			end.set_all(None, None, center_x, center_y, None)
			
		elif animation_name == _("Bottom to Center"):
			start.set_all(None, None, center_x, bottom, None)
			end.set_all(None, None, center_x, center_y, None)
			
		######### ACROSS
		elif animation_name == _("Left to Right"):
			start.set_all(None, None, left, center_y, None)
			end.set_all(None, None, right, center_y, None)

		elif animation_name == _("Right to Left"):
			start.set_all(None, None, right, center_y, None)
			end.set_all(None, None, left, center_y, None)

		elif animation_name == _("Top to Bottom"):
			start.set_all(None, None, center_x, top, None)
			end.set_all(None, None, center_x, bottom, None)

		elif animation_name == _("Bottom to Top"):
			start.set_all(None, None, center_x, bottom, None)
			end.set_all(None, None, center_x, top, None)


		# update clip properties
		self.selected_clip.halign = halign
		self.selected_clip.valign = valign
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip animation")
		


class mnuPositionSubMenu(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_layout_menu.ui", root="mnuPositionSubMenuPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuPositionSubMenuPopup.show_all()
		self.mnuPositionSubMenuPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = None
		self.selected_clip_item = None
		
		
	def on_mnuPosition_activate(self, event, *args):
		print "on_mnuPosition_activate"
		
		# update the gettext method
		_ = self._
		
		# get name of animation
		position_name = ""
		try:
			position_name = event.get_label()
		except:
			# older versions of pygtk need this prop
			position_name = event.children()[0].get_text()
		
		# init vars
		start = self.selected_clip.keyframes["start"]
		end = self.selected_clip.keyframes["end"]
		halign = "centre"
		valign = "centre"
		
		if position_name == _("Reset Layout"):
			start.set_all(100.0, 100.0, 0.0, 0.0, None)
			end.set_all(100.0, 100.0, 0.0, 0.0, None)


		######### 1/4 Size
		elif position_name == _("1/4 Size - Top Left"):
			start.set_all(50.0, 50.0, 0.0, 0.0, None)
			end.set_all(50.0, 50.0, 0.0, 0.0, None)

		elif position_name == _("1/4 Size - Top Right"):
			start.set_all(50.0, 50.0, 50.0, 0.0, None)
			end.set_all(50.0, 50.0, 50.0, 0.0, None)

		elif position_name == _("1/4 Size - Bottom Left"):
			start.set_all(50.0, 50.0, 0.0, 50.0, None)
			end.set_all(50.0, 50.0, 0.0, 50.0, None)

		elif position_name == _("1/4 Size - Bottom Right"):
			start.set_all(50.0, 50.0, 50.0, 50.0, None)
			end.set_all(50.0, 50.0, 50.0, 50.0, None)

		elif position_name == _("1/4 Size - Center"):
			start.set_all(50.0, 50.0, 25.0, 25.0, None)
			end.set_all(50.0, 50.0, 25.0, 25.0, None)
			
		elif position_name == _("Show All (Distort)"):
			# Show All Clips at the same time
			self.show_all_clips(stretch=True)
			
		elif position_name == _("Show All (Maintain Ratio)"):
			# Show All Clips at the same time
			self.show_all_clips(stretch=False)

		# update clip properties
		self.selected_clip.halign = halign
		self.selected_clip.valign = valign
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Changed clip layout")
		
	def show_all_clips(self, stretch=False):
		""" Show all clips  """
		from math import sqrt
		
		# get starting position
		start_position = self.selected_clip.position_on_track
		available_clips = []
		
		# Get the number of clips that start near the start of this clip (on any track)
		for track in self.project.sequences[0].tracks:
			# loop through clips
			for clip in track.clips:
				# only look at images, videos, and image sequences
				if clip.file_object.file_type in ["image", "video", "image sequence"]:
					# only look at clips that start near this clip
					if clip.position_on_track >= (start_position - 0.5) and clip.position_on_track <= (start_position + 0.5):
						# add to list
						available_clips.append(clip)
						
		# Get the number of rows
		number_of_clips = len(available_clips)
		number_of_rows = int(sqrt(number_of_clips))
		max_clips_on_row = float(number_of_clips) / float(number_of_rows)
		
		# Determine how many clips per row
		if max_clips_on_row > float(int(max_clips_on_row)):
			max_clips_on_row = int(max_clips_on_row + 1)
		else:
			max_clips_on_row = int(max_clips_on_row)
			
		# Calculate Height & Width
		height = 100.0 / float(number_of_rows)
		width = 100.0 / float(max_clips_on_row)
		
		clip_index = 0
		
		# Loop through each row of clips
		for row in range(0, number_of_rows):

			# Loop through clips on this row
			column_string = " - - - "
			for col in range(0, max_clips_on_row):
				if clip_index < number_of_clips:
					# Calculate X & Y
					X = float(col) * width
					Y = float(row) * height
					
					# Modify clip layout settings
					selected_clip = available_clips[clip_index]
					selected_clip.halign = "centre"
					selected_clip.valign = "centre"
					
					if stretch:
						selected_clip.distort = True
						selected_clip.fill = True
					else:
						selected_clip.distort = False
						selected_clip.fill = True						
					
					start = selected_clip.keyframes["start"]
					end = selected_clip.keyframes["end"]
					start.set_all(height, width, X, Y, None)
					end.set_all(height, width, X, Y, None)
			
					# Increment Clip Index
					clip_index += 1
		
		
		
		
class mnuClip(SimpleGtkBuilderApp):
	
	def __init__(self, rows, selected, path="Main_clip_properties.ui", root="mnuClipPopup", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.form = form
		self.project = project

		
	def showmnu(self, event, object, canvas_item):
		# show the popup menu
		self.mnuClipPopup.show_all()
		self.mnuClipPopup.popup( None, None, None, event.button, event.time)
		
		# get selected widget
		self.selected_clip = object
		self.selected_clip_item = canvas_item
		
		# update sub-menu references
		self.form.mnuFadeSubMenu1.selected_clip = object
		self.form.mnuFadeSubMenu1.selected_clip_item = canvas_item
		self.form.mnuRotateSubMenu1.selected_clip = object
		self.form.mnuRotateSubMenu1.selected_clip_item = canvas_item
		self.form.mnuAnimateSubMenu1.selected_clip = object
		self.form.mnuAnimateSubMenu1.selected_clip_item = canvas_item
		self.form.mnuPositionSubMenu1.selected_clip = object
		self.form.mnuPositionSubMenu1.selected_clip_item = canvas_item
		
		f = self.selected_clip.file_object
		
		if not f.file_type == "video":
			self.mnuConvertPartToImageSequence.hide()
			self.menuitem2.hide()
			self.menuitem3.hide()
		
		if ".svg" in self.selected_clip.name:
			self.mnuClipEditTitle.show()
		else:
			self.mnuClipEditTitle.hide()
		
		# temporarily block the callbacks otherwise they trigger when 
		# setting the toggle menu state
		self.mnuMuteAudio.handler_block_by_func(self.on_mnuMuteAudio_toggled)
		self.mnuHideVideo.handler_block_by_func(self.on_mnuHideVideo_toggled)
			
		if self.selected_clip.play_audio == True:
			self.mnuMuteAudio.set_active(False)
		else:
			self.mnuMuteAudio.set_active(True)
			
		if self.selected_clip.play_video == True:
			self.mnuHideVideo.set_active(False)
		else:
			self.mnuHideVideo.set_active(True)
			
		# unblock the callbacks
		self.mnuMuteAudio.handler_unblock_by_func(self.on_mnuMuteAudio_toggled)
		self.mnuHideVideo.handler_unblock_by_func(self.on_mnuHideVideo_toggled)
		
	def on_mnuHideVideo_toggled(self, event, *args):
		self.selected_clip.play_video = not self.selected_clip.play_video
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Changed visibility of clip"))
		
		# render timeline
		self.project.Render()
		
	def on_mnuMuteAudio_toggled(self, event, *args):
		print "on_mnuMuteAudio_toggled"
		self.selected_clip.play_audio = not self.selected_clip.play_audio
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Changed audio of clip"))
		
		# render timeline
		self.project.Render()	
		
	def on_mnuClipEditTitle_activate(self, event, *args):
		#print "on_mnuClipEditTitle_activate"
		
		#edit a title using the title editor		
		Titles.frmTitles(form=self.form, project=self.project, file=os.path.join(self.project.folder, self.selected_clip.file_object.name))
		
		
	def on_mnuClipProperties_activate(self, event, *args):
		print "on_mnuClipProperties_activate"

		# show frmExportVideo dialog
		self.frmClipProperties = ClipProperties.frmClipProperties(form=self.form, project=self.project, current_clip=self.selected_clip, current_clip_item=self.selected_clip_item)


	def on_mnuRemoveClip_activate(self, event, *args):
		print "on_mnuRemoveClip_activate clicked"
		
		if self.form._SHIFT == True:
			
			# close the gap between removed clips
			# (this only works on a single track)
			length_of_clip = self.selected_clip.length()
			
			shift = 0.0
			start_of_selected = float(self.selected_clip.position_on_track)
			
			# no need to animate the clip removal,
			# as the other clips will be shifted to where it was.
			self.clip_removed(self.selected_clip)
			
			try:
				# amount to shift
				shift = float(length_of_clip * -1)
					
					
			except:
				# invalid shift amount... default to 0
				shift = 0.0
					
			if shift:
				# loop through clips, and shift
				for clip in self.selected_clip.parent.clips:
					start = float(clip.position_on_track)
					if start >= start_of_selected:
						clip.position_on_track = start + shift
						
				# loop through transitions, and shift
				for tran in self.selected_clip.parent.transitions:
					start = float(tran.position_on_track)
					if start >= start_of_selected:
						tran.position_on_track = start + shift
						
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Shifted clips"))
							
			# render timeline
			self.form.refresh()
			
		else:
			
			# find middle x coordinate
			clip_length_pixels = self.selected_clip_item.get_bounds().x2  - self.selected_clip_item.get_bounds().x1
			x_middle = self.selected_clip_item.get_bounds().x1 #+ (clip_length_pixels / 2.0)
			
			# find middle y coordinate
			clip_height_pixels = self.selected_clip_item.get_bounds().y2  - self.selected_clip_item.get_bounds().y1
			y_middle = self.selected_clip_item.get_bounds().y1 + (clip_height_pixels / 2.0)
			
			# animate the clip to turn invisible
			self.selected_clip_item.connect("animation-finished", self.clip_removed)
			self.selected_clip_item.animate(x_middle, y_middle, 0.0, 0.0, True, 200, 4, goocanvas.ANIMATE_FREEZE)

				
		
	def clip_removed(self, item, *args):

		# remove this clip
		self.selected_clip.parent.clips.remove(self.selected_clip)
		
		# remove from canvas
		parent = self.selected_clip_item.get_parent()
		child_num = parent.find_child (self.selected_clip_item)
		parent.remove_child (child_num)
		
		# Remove the thumbnail
		self.selected_clip.remove_thumbnail()
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Removed clip"))
		
		
	def on_mnuShiftClips_activate (self, event, *args):
		print "on_mnuShiftClips_activate clicked"
		
		shift = 0.0
		start_of_selected = float(self.selected_clip.position_on_track)
		
		# Get previous clip (if any)
		previous_clip = None
		clips_on_track = self.selected_clip.parent.clips
		index_of_selected_clip = clips_on_track.index(self.selected_clip) - 1
		if index_of_selected_clip >= 0:
			previous_clip = clips_on_track[index_of_selected_clip]

		# get correct gettext method
		_ = self._
		
		# get the amount of time the clips are shifted
		text = inputbox.input_box(title="OpenShot", message=_("Please enter the # of seconds to shift the clips:"), default_text="5.0")
		if text:
			# convert to peroid decimal
			text = text.replace(',', '.')
			try:
				# amount to shift
				shift = float(text)
				
				# is shift negative (i.e. shifting to the left)
				if shift < 0.0:
					# negative shift
					if previous_clip:
						end_of_previous_clip = previous_clip.position_on_track + float(previous_clip.length())
						if shift + start_of_selected < end_of_previous_clip:
							# get difference between previous clip, and selected clip
							shift = end_of_previous_clip - start_of_selected
					
					else:
						# no previous clip, is clip going to start before timeline?
						if shift + start_of_selected < 0.0:
							# get difference between clip and beginning of timeline
							shift = 0.0 - start_of_selected
			except:
				# invalid shift amount... default to 0
				shift = 0.0
				
		if shift:
			# loop through clips, and shift
			for cl in self.selected_clip.parent.clips:
				start = float(cl.position_on_track)
				if start >= start_of_selected:
					cl.position_on_track = start + shift

			# mark project as modified
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type = _("Shifted clips"))

			# render timeline
			self.form.refresh()


	def on_mnuDuplicate_activate(self, event, *args):
		print "on_mnuDuplicate_activate"
		
		# create new clip
		parent_track = self.selected_clip.parent
		is_title = False
		
		#if the file is a title, create a unique copy
		#to make each title unique and editable	
		if self.selected_clip.file_object.file_type == "image" and ".svg" in self.selected_clip.file_object.name:
			is_title = True
			(filepath, filename) = os.path.split(self.selected_clip.file_object.name)
			(shortname, extension) = os.path.splitext(filename)
		
			#add a number to the end of the shortname.
			#get the next available number for the file
			blnFind = True 
			intNum = 0
			while blnFind == True:
				intNum += 1
				blnFind = os.path.exists(os.path.join(filepath, shortname + str(intNum) + extension))
			
			#append the number to the filename 			
			shortname = shortname + str(intNum)
			#create a copy of the selected file with the new name
			shutil.copy(os.path.join(filepath, filename), os.path.join(filepath, shortname + extension))
			#Add the new file to the project so it shows up in the tree view
			self.project.project_folder.AddFile(os.path.join(filepath, shortname + extension))
			#Add the new file object to the timeline
			new_file_object = self.project.project_folder.FindFile(os.path.join(filepath, shortname + extension))
			
			# Duplidate title clip
			new_clip = parent_track.AddClip(shortname + extension, self.selected_clip.color, self.selected_clip.position_on_track + 3, self.selected_clip.start_time, self.selected_clip.end_time, new_file_object)
			
		else:
			# Not a title (i.e. regular videos, images, and audio)
			new_clip = parent_track.AddClip(self.selected_clip.name, self.selected_clip.color, self.selected_clip.position_on_track + 3, self.selected_clip.start_time, self.selected_clip.end_time, self.selected_clip.file_object)
		
		
		# set all properties from the clip on the new duplicated clip
		new_clip.max_length = self.selected_clip.max_length
		new_clip.fill = self.selected_clip.fill
		new_clip.distort = self.selected_clip.distort
		new_clip.composite = self.selected_clip.composite
		new_clip.speed = self.selected_clip.speed
		new_clip.play_video = self.selected_clip.play_video
		new_clip.play_audio = self.selected_clip.play_audio
		new_clip.halign = self.selected_clip.halign
		new_clip.valign = self.selected_clip.valign
		new_clip.reversed = self.selected_clip.reversed
		new_clip.volume = self.selected_clip.volume
		new_clip.audio_fade_in = self.selected_clip.audio_fade_in
		new_clip.audio_fade_out = self.selected_clip.audio_fade_out
		new_clip.audio_fade_in_amount = self.selected_clip.audio_fade_in_amount
		new_clip.audio_fade_out_amount = self.selected_clip.audio_fade_out_amount
		new_clip.video_fade_in = self.selected_clip.video_fade_in
		new_clip.video_fade_out = self.selected_clip.video_fade_out
		new_clip.video_fade_in_amount = self.selected_clip.video_fade_in_amount
		new_clip.video_fade_out_amount = self.selected_clip.video_fade_out_amount
		new_clip.keyframes = copy.deepcopy(self.selected_clip.keyframes)
		new_clip.effects = copy.deepcopy(self.selected_clip.effects)
		
		# Update the thumbnail
		new_clip.update_thumbnail()
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type="Duplicated clip")

		# render to timeline
		new_clip.RenderClip()
		
		# Refresh (if title was duplicated)
		if is_title:
			self.form.refresh()
		
	
	def on_mnuReplaceClip_activate (self, event, *args):
		# show import file dialog to select replacement file
		self.import_files_dialog = AddFiles.frmReplaceFiles(form=self, project=self.project, clip=self.selected_clip)
		
	def on_mnuConvertPartToImageSequence_activate (self, event, *args):
		print "on_mnuConvertPartToImageSequence_activate"
		
		# get correct gettext method
		_ = self._
		
		# change cursor to "please wait"
		self.form.frmMain.window.set_cursor(gtk.gdk.Cursor(150))
		
		# get the clip
		clip = self.selected_clip
		f = clip.file_object
		
		# When to start and end the image sequence
		start_time = clip.start_time
		end_time = clip.end_time
		
		# convert to image sequence
		# Use idle_add() to prevent starving the GUI, so it sets the cursor correctly
		# This basically queues up each of these commands... and they are executed one after another.
		gobject.idle_add(self.project.project_folder.ConvertFileToImages, f.name, start_time, end_time)
		gobject.idle_add(self.form.refresh)
		gobject.idle_add(self.project.set_project_modified, True, True, _("Video converted to Image Sequence"))
		gobject.idle_add(self.form.frmMain.window.set_cursor, None)

		
	def replace_clip(self, selected_clip, new_clip):
		#this replaces the selected clip with a new clip
		(filepath, filename) = os.path.split(new_clip)
		file = self.project.project_folder.FindFile(filename)
		# Only proceed if the file path is valid and isn't the same as the file that's being replaced
		if file:
				
			# get original file properties
			original_clip_length = selected_clip.length()
			original_start_time = selected_clip.start_time
			original_end_time = selected_clip.end_time
			original_file_length = selected_clip.file_object.length
			
			# swap the file object
			selected_clip.file_object = file
			selected_clip.name = filename
			selected_clip.thumb_location = selected_clip.file_object.thumb_location
			# Only reset start and end time if the files have different durations
			if file.length != original_file_length:
				selected_clip.start_time = 0.0 # reset IN to 0.0
				selected_clip.end_time = original_clip_length # reset OUT
			
			# change the in / out points (if needed, due to length of new file)
			if file.length < original_clip_length:
				# change clip size, to account for shorter size
				selected_clip.end_time = file.length
			
			#force a refresh of the xml
			self.project.set_project_modified(is_modified=True, refresh_xml=True, type=_("Replaced Clip"))
			self.project.Render()
			self.form.refresh()
		
	
		
class mnuTree(SimpleGtkBuilderApp):

	def __init__(self, rows, selected, path="Main_tree_popup.ui", root="mnuTreePopUp", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		self.mnuTree  = self.mnuTreePopUp
		self.model = rows
		self.selected = selected
		self.form = form
		self.project = project


	def showmnu(self, event, widget):

		# get correct gettext method
		_ = self._
		
		# Show the right click menu.
		# dynamically show menu items depending on tree contents.
		# The Add Folder & Add File items are in the ui file - we always want them.
		
		if self.form.scrFileTree.get_property('visible') == True:
			name = "treeFiles"
		else:
			name = "icvFileIcons"

		# Option Construction
		# Create Import Files
		mnuImportFiles = gtk.ImageMenuItem(gtk.STOCK_ADD)
		mnuImportFiles.get_children()[0].set_label(_("Import Files..."))
		mnuImportFiles.connect('activate',self.on_mnuAddFile_activate)

		# Create Folder
		mnuCreateFolder = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		mnuCreateFolder.get_children()[0].set_label(_("Create Folder"))
		mnuCreateFolder.connect('activate',self.on_mnuAddNewFolder_activate)

		# Add to Timeline...
		mnuAddToTimeline = gtk.ImageMenuItem(gtk.STOCK_ADD)
		mnuAddToTimeline.get_children()[0].set_label(_("Add to Timeline..."))
		mnuAddToTimeline.connect('activate',self.on_mnuAddToTimeline_activate)
		
		# Preview File
		mnuPreview = gtk.ImageMenuItem(gtk.STOCK_MEDIA_PLAY)
		mnuPreview.get_children()[0].set_label(_("Preview File"))
		mnuPreview.connect('activate',self.on_mnuPreview_activate)
				
		# Convert To Image Sequence
		mnuConvertToImages = gtk.ImageMenuItem(gtk.STOCK_CONVERT)
		mnuConvertToImages.get_children()[0].set_label(_("Convert To Image Sequence"))
		mnuConvertToImages.connect('activate',self.on_mnuConvertToImages_activate)
				
		# Thumbnail View
		mnuThumbView = gtk.ImageMenuItem(gtk.STOCK_FULLSCREEN)
		mnuThumbView.get_children()[0].set_label(_("Thumbnail View"))
		mnuThumbView.connect('activate',self.on_mnuThumbView_activate)
		
		# Detail View
		mnuDetailView = gtk.ImageMenuItem(gtk.STOCK_LEAVE_FULLSCREEN)
		mnuDetailView.get_children()[0].set_label(_("Detail View"))
		mnuDetailView.connect('activate',self.on_mnuDetailView_activate)
		
		# Move File(s) to folder
		mnuMoveFile = gtk.ImageMenuItem(gtk.STOCK_GO_FORWARD)
		mnuMoveFile.get_children()[0].set_label(_("Move File(s) to Folder"))
			
		# Populate the sub menu with available folders
		folders =  self.project.project_folder.ListFolders()
		mnuSubMenu = gtk.Menu()
		for folder in folders:
			item = gtk.ImageMenuItem(gtk.STOCK_OPEN)
			item.get_children()[0].set_label(folder)					
			item.connect("activate", self.move_file_to_folder, folder)
			mnuSubMenu.add(item)
		
		# Remove from Folder
		if folders:
			mnuSeparator = gtk.SeparatorMenuItem()
			mnuSubMenu.add(mnuSeparator)
					
			item = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
			item.get_children()[0].set_label(_("Remove from Folder"))					
			item.connect("activate", self.move_file_to_folder, _("Remove from Folder"))
			mnuSubMenu.add(item)
		else:
			# Gray out the "Move File(s) to Folder" option
			mnuMoveFile.set_sensitive(False)
		
		# Add folders sub-menu to menu
		mnuMoveFile.set_submenu(mnuSubMenu)
				
		# Edit Title (Simple)
		mnuEditTitle = gtk.ImageMenuItem(gtk.STOCK_EDIT)
		mnuEditTitle.get_children()[0].set_label(_("Edit Title (Simple)"))
		mnuEditTitle.connect('activate',self.on_mnuEditTitle_activate, "simple")
		
		# Edit Title (Inkscape)
		mnuEditTitle1 = gtk.ImageMenuItem(gtk.STOCK_EDIT)
		mnuEditTitle1.get_children()[0].set_label(_("Edit Title (Inkscape)"))
		mnuEditTitle1.connect('activate',self.on_mnuEditTitle_activate, "advanced")
		
		# Remove From Project
		mnuRemoveFile = gtk.ImageMenuItem(gtk.STOCK_DELETE)
		mnuRemoveFile.get_children()[0].set_label(_("Remove from Project"))
		mnuRemoveFile.connect('activate',self.on_mnuRemoveFile_activate)
		
		# Upload to Web
		mnuUploadToWeb = gtk.ImageMenuItem(gtk.STOCK_NETWORK)
		mnuUploadToWeb.get_children()[0].set_label(_("Upload to Web"))
		mnuUploadToWeb.connect('activate',self.on_mnuUploadToWeb_activate)

		# File Properties
		mnuFileProperties = gtk.ImageMenuItem(gtk.STOCK_PROPERTIES)
		mnuFileProperties.get_children()[0].set_label(_("File Properties"))
		mnuFileProperties.connect('activate', self.on_FileProperties_activate)
		
		is_video_selected = False
		is_svg_selected = False
		is_folder_selected = False
		selected_count = 0
		
		# Determine the types of files selected (if any)
		if self.selected:
			
			# Loop through each selected file / folder
			iters = [self.model.get_iter(path) for path in self.selected]
			selected_count = len(iters)
			for iter in iters:
				# remove from the file object
				filename = self.model.get_value(iter, 1)
				if name == "treeFiles":
					unique_id = self.model.get_value(iter, 4)
				else:
					unique_id = self.model.get_value(iter, 3)
			
				# get file object
				f = self.project.project_folder.FindFileByID(unique_id)
				if f:
					if f.file_type == "video":
						is_video_selected = True
					if f.file_type == "image" and ".svg" in f.name:
						is_svg_selected = True
				else:
					is_folder_selected = True
			
			
		# -------------------------
		# ADD MENU ITEMS
		# -------------------------
		if self.selected and not is_folder_selected:
			# Add-to-Timeline + Preview
			self.mnuTree.add(mnuAddToTimeline)
			
			if selected_count == 1:
				# single selection
				self.mnuTree.add(mnuPreview)
				self.mnuTree.add(gtk.SeparatorMenuItem())
				
				if is_video_selected:
					self.mnuTree.add(mnuConvertToImages)
					self.mnuTree.add(gtk.SeparatorMenuItem())

				if is_svg_selected :
					# Edit SVG Titles
					self.mnuTree.add(mnuEditTitle)
					self.mnuTree.add(mnuEditTitle1)
					self.mnuTree.add(gtk.SeparatorMenuItem())

				if is_video_selected:
					self.mnuTree.add(mnuUploadToWeb)
					self.mnuTree.add(gtk.SeparatorMenuItem())
			else:
				# multiple selections
				self.mnuTree.add(gtk.SeparatorMenuItem())
		
		if self.selected:
			# Remove from timeline
			if selected_count == 1:
				self.mnuTree.add(mnuFileProperties)
			self.mnuTree.add(mnuRemoveFile)
			self.mnuTree.add(gtk.SeparatorMenuItem())
				
		# Import Files
		self.mnuTree.add(mnuImportFiles)

		if name == "treeFiles":
			# Create folder
			self.mnuTree.add(mnuCreateFolder)
			if self.selected and not is_folder_selected:
				self.mnuTree.add(mnuMoveFile)

		self.mnuTree.add(gtk.SeparatorMenuItem())
		
		if name == "treeFiles":
			# Add Thumbnail View
			self.mnuTree.add(mnuThumbView)
		else:
			# Add Detail View
			self.mnuTree.add(mnuDetailView)

		self.mnuTree.show_all()
		self.mnuTree.popup( None, None, None, event.button, event.time)
		
	
		
	def on_mnuAddToTimeline_activate(self, event, *args):
		""" Show the Add to Timeline dialog, with all selected files added to the dialog. """

		# list of selected file objects
		selected_files = []

		frm = self.form
		detail_view = frm.scrFileTree.get_property('visible')
		if detail_view == True:
			iters = [self.model.get_iter(path) for path in self.selected]
			for iter in iters:
				# get file object
				unique_id = self.model.get_value(iter, 4)
				file_object = self.project.project_folder.FindFileByID(unique_id)
				
				if file_object:
					# only add non-folder items
					selected_files.append(file_object)
	
		else:
			#iconview is active
			selected = frm.icvFileIcons.get_selected_items()
			for item in selected:
				i = item[0]
				model = frm.icvFileIcons.get_model()
				unique_id = model[i][3]

				# get file object
				file_object = self.project.project_folder.FindFileByID(unique_id)
				
				if file_object:
					# only add non-folder items
					selected_files.append(file_object)
		
		# show frmExportVideo dialog
		self.frmAddToTimeline = AddToTimeline.frmAddToTimeline(form=self.form, project=self.project, selected_files=selected_files)
		

		
	def move_file_to_folder(self, widget, folder):
		frm = self.form
		iters = [self.model.get_iter(path) for path in self.selected]
		for iter in iters:
			filename = self.model.get_value(iter, 1)
			
			if folder == _("Remove from Folder"):
				self.project.project_folder.RemoveParent(filename, folder)
			else:
				self.project.project_folder.AddParentToFile(filename, folder)
				
		frm.refresh() 
			
	def on_mnuPreview_activate(self, event, *args):
		print "on_mnuPreview_activate"
		
		# get translation method
		_ = self._

		if self.form.scrFileTree.get_property('visible') == True:

			# loop through all selected files
			iters = [self.model.get_iter(path) for path in self.selected]
			if iters:
				for iter in iters:

					# get the file object
					unique_id = self.model.get_value(iter, 4)
					f = self.project.project_folder.FindFileByID(unique_id)

					if f:
						
						# get file name, path, and extention
						if not os.path.isfile(f.name) and f.file_type != "image sequence":
							messagebox.show("OpenShot", _("The following file(s) no longer exist.") + "\n\n" + f.name)
							break
						
						(dirName, filename) = os.path.split(f.name)
						(fileBaseName, fileExtension)=os.path.splitext(filename)
						
						# ****************************
						# re-load the xml
						if self.form.MyVideo:
							# determine length of clip (needed for the slider)
							if f.file_type == "image":
								calculate_length = 9000.0
							elif f.file_type == "image sequence":
								calculate_length = (f.max_frames * f.ttl) / f.fps
							else:
								calculate_length = f.max_frames / f.fps
							
							# create temp clip object
							temp_clip = clip.clip("temp clip", "gold", 0.0, 0.0, calculate_length, self.project.sequences[0].tracks[0], f)
							
							# generate the preview xml for this clip
							temp_clip.GeneratePreviewXML(os.path.join(self.project.USER_DIR, "preview.mlt"))

							# Load XML
							self.form.MyVideo.set_project(self.project, self.form, os.path.join(self.project.USER_DIR, "preview.mlt"), mode="override", override_path="preview.mlt")
							self.form.MyVideo.load_xml()
						
						# start and stop the video
						self.project.form.MyVideo.play()
								
						# refresh sdl
						self.project.form.MyVideo.refresh_sdl()
						break
		else:
			# thumbnail view
			#get the file info from the iconview
			selected = self.form.icvFileIcons.get_selected_items()
			model = self.form.icvFileIcons.get_model()
			
			# loop through all selected files
			iters = [model.get_iter(path) for path in selected]
			if iters:
				for iter in iters:
			
					# get the file object
					unique_id = model.get_value(iter, 3)
					f = self.project.project_folder.FindFileByID(unique_id)

					if f:
						# get file name, path, and extention
						if not os.path.isfile(f.name) and f.file_type != "image sequence":
							messagebox.show("OpenShot", _("The following file(s) no longer exist.") + "\n\n" + f.name)
							break
						
						# get file name, path, and extention
						(dirName, filename) = os.path.split(f.name)
						(fileBaseName, fileExtension)=os.path.splitext(filename)
						
						# ****************************
						# re-load the xml
						if self.form.MyVideo:
							# create temp clip object
							temp_clip = clip.clip("temp clip", "gold", 0.0, 0.0, 9000.0, self.project.sequences[0].tracks[0], f)
							
							# generate the preview xml for this clip
							temp_clip.GeneratePreviewXML(os.path.join(self.project.USER_DIR, "preview.mlt"))

							# Load XML
							self.form.MyVideo.set_project(self.project, self.form, os.path.join(self.project.USER_DIR, "preview.mlt"), mode="override", override_path="preview.mlt")
							self.form.MyVideo.load_xml()
						
						# start and stop the video
						self.project.form.MyVideo.play()
						
						# refresh sdl
						self.project.form.MyVideo.refresh_sdl()
						break
		
			
	def on_mnuConvertToImages_activate(self, event, *args):
		print "on_mnuConvertToImages_activate"
		
		# get translation method
		_ = self._
		
		# change cursor to "please wait"
		self.form.frmMain.window.set_cursor(gtk.gdk.Cursor(150))

		# determine if detail view is visible
		detail_view_visible = self.form.scrFileTree.get_property('visible')
		
		# loop through all selected files
		iters = [self.model.get_iter(path) for path in self.selected]
		for iter in iters:

			unique_id = ""
			
			# find the unique id of the file
			if detail_view_visible:
				unique_id = self.model.get_value(iter, 4)
			else:
				unique_id = self.model.get_value(iter, 3)

			# Get the file object
			f = self.project.project_folder.FindFileByID(unique_id)
			
			# convert to image sequence
			# Use idle_add() to prevent starving the GUI, so it sets the cursor correctly
			# This basically queues up each of these commands... and they are executed one after another.
			gobject.idle_add(self.project.project_folder.ConvertFileToImages, f.name)
			gobject.idle_add(self.form.refresh)
			gobject.idle_add(self.project.set_project_modified, True, False, _("Video converted to Image Sequence"))
			gobject.idle_add(self.form.frmMain.window.set_cursor, None)


		
	def on_mnuAddFile_activate(self, event, *args):
		self.import_files_dialog = AddFiles.frmAddFiles(form=self.form, project=self.project)

	def on_mnuAddNewFolder_activate(self, event, *args):
		frm = frmFolders(form=self.form, project=self.project)
		frm.show()
		
		
	def on_mnuEditTitle_activate(self, event, mode="simple", *args):
		print "on_mnuEditTitle_activate"
		prog = "inkscape"
		
		# get correct gettext method
		_ = self._
		
		#use an external editor to edit the image
		try:
			
			# find selected file
			frm = self.form
			detail_view = frm.scrFileTree.get_property('visible')
			
			if detail_view == True:
				iters = [self.model.get_iter(path) for path in self.selected]
				for iter in iters:
					# get file name and unique id
					filename = self.model.get_value(iter, 1)
					unique_id = self.model.get_value(iter, 4)
					
					file_item = self.project.project_folder.FindFileByID(unique_id)
					if file_item and mode == "advanced":
						# ADVANCED EDIT MODE
						#use an external editor to edit the image
						try:
							#check if inkscape is installed
							if subprocess.call('which ' + prog + ' 2>/dev/null', shell=True) == 0:
								# launch Inkscape
								p=subprocess.Popen([prog, file_item.name])
								
								# wait for process to finish (so we can updated the thumbnail)
								p.communicate()
								
								# Update thumbnail
								self.project.thumbnailer.get_thumb_at_frame(file_item.name)
								self.form.refresh()
							else:
								messagebox.show(_("OpenShot Error"), _("Please install %s to use this function.") % (prog.capitalize()))
							
						except OSError:
							messagebox.show(_("OpenShot Error"), _("There was an error opening '%s', is it installed?") % prog)


					if file_item and mode == "simple":
						# SIMPLE EDIT MODE
						#edit a title using the title editor		
						Titles.frmTitles(form=self.form, project=self.project, file=os.path.join(self.project.folder, file_item.name))
						
						# Update thumbnail
						self.project.thumbnailer.get_thumb_at_frame(file_item.name)
						self.form.refresh()
		
					#mark the project as modified
					self.project.set_project_modified(is_modified=True, refresh_xml=True)
			
		except:
			messagebox.show(_("OpenShot Error"), _("There was an error opening '%s', is it installed?" % (prog)))

		

	def on_mnuRemoveFile_activate(self, event, *args):
		"""Removes a file from the treeview & project"""
		frm = self.form
		detail_view = frm.scrFileTree.get_property('visible')
		if detail_view == True:
			iters = [self.model.get_iter(path) for path in self.selected]
			for iter in iters:
				#remove from the file object
				
				length = self.model.get_value(iter, 2)
				unique_id = self.model.get_value(iter, 4)
				
				if unique_id and length:
					file_item = self.project.project_folder.FindFileByID(unique_id)
					self.model.remove(iter)
					self.project.project_folder.RemoveFile(file_item.name)
				else:
					#folders don't have a unique id, so use the name field.
					filename = self.remove_markup(self.model.get_value(iter, 1))
					self.model.remove(iter)
					self.project.project_folder.RemoveFile(filename)
								
			frm.refresh()		
		else:
			#iconview is active
			selected = frm.icvFileIcons.get_selected_items()
			for item in selected:
				i = item[0]
				model = frm.icvFileIcons.get_model()
				unique_id = model[i][3]
				file_item = self.project.project_folder.FindFileByID(unique_id)
				#remove the item from the project items list	
				self.project.project_folder.RemoveFile(file_item.name)
				
			frm.refresh_thumb_view()
			
		#mark the project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True)

	def remove_markup(self,data):
		p = re.compile(r'<[^<]*?/?>')
		return p.sub('', data)		

	def on_mnuUploadToWeb_activate(self, event):
		print "on_mnuUploadToWeb_activate"
		
		#show the upload to web dialog
		frm = self.form

		detail_view = frm.scrFileTree.get_property('visible')
		if detail_view == True:
			if len(self.selected) > 1:
				#if more than 1 row selected, don't try and show the dialog
				return
			if len(self.selected) > 0:
				iters = [self.model.get_iter(path) for path in self.selected]
				for iter in iters:
					file = self.model.get_value(iter, 1)
					unique_id = self.model.get_value(iter, 4)
			else: #nothing selected
				return
			
		else:
			#iconview is active
			selected = frm.icvFileIcons.get_selected_items()
			if len(selected) > 1:
				#more than 1 row selected, don't show the dialog
				return
			if len(selected) > 0:
				i = selected[0][0]
				model = frm.icvFileIcons.get_model()
				file = model[i][1]
				unique_id = model[i][3]
			else: #nothing selected
				return
			
		#pass the file item to the upload to web dialog
		file_item = self.project.project_folder.FindFileByID(unique_id)
		if file_item:
			UploadVideo.frmUploadVideo(form=self.form, project=self.project, filename=file_item.name)

			

	def on_FileProperties_activate(self, event):
		#show the file properties window
		frm = self.form
		
		detail_view = frm.scrFileTree.get_property('visible')
		if detail_view == True:
			if len(self.selected) > 1:
				#if more than 1 row selected, don't try and show the dialog
				return
			if len(self.selected) > 0:
				iters = [self.model.get_iter(path) for path in self.selected]
				for iter in iters:
					file = self.model.get_value(iter, 1)
					unique_id = self.model.get_value(iter, 4)
			else: #nothing selected
				return
			
		else:
			#iconview is active
			selected = frm.icvFileIcons.get_selected_items()
			if len(selected) > 1:
				#more than 1 row selected, don't show the dialog
				return
			if len(selected) > 0:
				i = selected[0][0]
				model = frm.icvFileIcons.get_model()
				file = model[i][1]
				unique_id = model[i][3]
			else: #nothing selected
				return
			
		#pass the file item to the file properties window
		file_item = self.project.project_folder.FindFileByID(unique_id)
		if file_item:
			FileProperties.frmFileproperties(file_item, form=self, project=self.project)
			
		

	def on_mnuThumbView_activate(self, event, *args):
		"""switch the view to the thumbnail view"""

		frm = self.form
		frm.scrFileTree.set_property('visible', False)
		frm.scrFileIcons.set_property('visible', True)
		frm.refresh_thumb_view()
		
		# resize the icon window so the icons don't all spread out
		frm.icvFileIcons.resize_children()
		frm.scrFileIcons.resize_children()
		frm.icvFileIcons.set_reallocate_redraws(True)
		frm.scrFileIcons.set_reallocate_redraws(True)
		

	def on_mnuDetailView_activate(self, event, *args):
		"""switch the view to the treeview"""
		frm = self.form
		frm.scrFileIcons.set_property('visible', False)
		frm.scrFileTree.set_property('visible', True)
		frm.refresh()

		
class frmFolders(SimpleGtkBuilderApp):

	def __init__(self, path="Main_folder_menu.ui", root="frmFolder", domain="OpenShot", form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)
		
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		self.FolderDlg  = self.frmFolder
		self.form = form
		self.project = project
		
		if getIconPath("openshot"):
			self.FolderDlg.set_icon_from_file(getIconPath("openshot"))
		
	def show(self):
		self.FolderDlg.run()
		
	def on_btnCancel_clicked(self, widget, *args):
		self.FolderDlg.destroy()
		
	def on_txtFolderName_key_press_event(self, widget, event):

		# Get the key name that was pressed
		keyname = str.lower(gtk.gdk.keyval_name(event.keyval))
		
		# Check for the "return/enter" key
		if keyname == "return":
			# Save folder
			self.on_btnOK_clicked(widget)
		else:
			# Let GTK handle key
			return False
		
	def on_btnOK_clicked(self, widget, *args):
		if self.txtFolderName.get_text() != "":
			folder_name = self.txtFolderName.get_text()
			self.project.project_folder.AddFolder(folder_name)		
		self.FolderDlg.destroy()




def run(self):

	self.frmMain.show_all()
	SimpleGtkBuilderApp.run(self)
	

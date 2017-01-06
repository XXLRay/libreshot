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

import os
import gtk, gobject, pango, shutil
from classes import project, messagebox

# init the foreign language
from language import Language_Init


class LibreShotTree:
	
	def __init__(self, view, project):
	
		# Add language support
		self._ = Language_Init.Translator(project).lang.gettext
		_ = self._
	
		# init vars
		self.view = view
		self.project = project
		self.view.set_item_width(130)
		self.filter_category = "Show All"
		
		# create a TreeStore
		self.store = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
	
		# Set the treeview's data model
		self.view.set_model(self.store)

		# Populate transitions
		self.populate()
		
		# connect signals
		self.view.connect_after('drag_begin', self.on_icvTransitions_drag_begin)
		
	def populate(self, category=None, filter=None):
		
		_ = self._
		
		# clear store
		self.store.clear()
		
		# set filter category (if any)
		if category:
			self.filter_category = category
			
		# Get icon size from settings
		icon_size = self.project.form.settings.general["icon_size"]
		if icon_size == "small":
			self.view.set_item_width(90)
		else:
			self.view.set_item_width(130)
		
		# ADD DEFAULT TRANSITIONS
		file_path = os.path.join(self.project.TRANSITIONS_DIR, "icons", icon_size, "sand.png")
		
		# get the pixbuf
		pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)
			
		self.view.set_pixbuf_column(0)
		self.view.set_text_column(2)
		self.view.set_text_column(1)
		
		if self.does_match_filter("Dissolve", filter):
			# add transition to tree
			item = self.store.append(None)
			self.store.set_value(item, 0, pbThumb)
			self.store.set_value(item, 1, _("Dissolve"))
			self.store.set_value(item, 2, "")

		# get a list of files in the LibreShot /transitions directory
		file_list = os.listdir(os.path.join(self.project.TRANSITIONS_DIR))

		for fname in sorted(file_list):
			(dirName, file_name) = os.path.split(fname)
			(fileBaseName, fileExtension)=os.path.splitext(file_name)
			file_path = os.path.join(self.project.TRANSITIONS_DIR, "icons", icon_size, fileBaseName + ".png")
			
			if fileBaseName == "icons":
				# ignore the 'icons' folder
				continue
			
			# get the pixbuf
			pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)
			
			# resize thumbnail
			#pbThumb1 = pbThumb.scale_simple(80, 62, gtk.gdk.INTERP_BILINEAR)
			#
			# perminately save resized icon
			#pbThumb1.save(os.path.join("/home/jonathan/Desktop/thumbnails", fileBaseName + ".png"), "png", {})
			
			# get name of transition
			trans_name = fileBaseName.replace("_", " ").capitalize()
			
			# check if a filter matches (if any)
			if not self.does_match_filter(trans_name, filter):
				# NO match, so skip to next filter
				continue

			# add transition to tree
			item = self.store.append(None)
			self.store.set_value(item, 0, pbThumb)
			self.store.set_value(item, 1, _(trans_name))
			self.store.set_value(item, 2, os.path.join(self.project.TRANSITIONS_DIR, file_name))
			
		#get any user created transitions
		if os.path.exists(self.project.USER_TRANSITIONS_DIR):
			
			# Check for missing icon paths, and create them
			if not os.path.exists(os.path.join(self.project.USER_TRANSITIONS_DIR, "icons")):
				os.makedirs(os.path.join(self.project.USER_TRANSITIONS_DIR, "icons"))
				
			if not os.path.exists(os.path.join(self.project.USER_TRANSITIONS_DIR, "icons", "small")):
				os.makedirs(os.path.join(self.project.USER_TRANSITIONS_DIR, "icons", "small"))
				
			if not os.path.exists(os.path.join(self.project.USER_TRANSITIONS_DIR, "icons", "medium")):
				os.makedirs(os.path.join(self.project.USER_TRANSITIONS_DIR, "icons", "medium"))
			
			# Get list of user transitions
			user_list = os.listdir(self.project.USER_TRANSITIONS_DIR)
			
			try:
				
				# Loop through each user transition (and add it to the IconView)
				for fname in sorted(user_list):
					(dirName, file_name) = os.path.split(fname)
					(fileBaseName, fileExtension)=os.path.splitext(file_name)
					file_path = os.path.join(self.project.USER_TRANSITIONS_DIR, "icons", icon_size, fileBaseName + ".png")
					
					# ignore the 'icons' folder
					if fileBaseName == "icons":
						continue
					
					# verify the icon actually exists
					if not os.path.exists(file_path):

						# copy the transition into the icon folder
						shutil.copyfile(os.path.join(self.project.USER_TRANSITIONS_DIR, fname), file_path)
						
						# Load pixbuf of transition
						pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)
						
						if icon_size == "small":
							# resize icon
							pbThumb = pbThumb.scale_simple(80, 62, gtk.gdk.INTERP_BILINEAR)
	
						elif icon_size == "medium":
							# resize icon
							pbThumb = pbThumb.scale_simple(120, 96, gtk.gdk.INTERP_BILINEAR)
							
						# Save the new icon
						pbThumb.save(file_path, fileExtension.replace(".", ""), {})
				
				
					# Load the pixbuf
					pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)
	
					# get name of transition
					trans_name = fileBaseName.replace("_", " ").capitalize()
					
					# check if a filter matches (if any)
					if not self.does_match_filter(trans_name, filter):
						# NO match, so skip to next filter
						continue
	
					# add transition to tree
					item = self.store.append(None)
					self.store.set_value(item, 0, pbThumb)
					self.store.set_value(item, 1, _(trans_name))
					self.store.set_value(item, 2, os.path.join(self.project.USER_TRANSITIONS_DIR, file_name))
			except:
				messagebox.show("Openshot Error!", _("There was an error loading user created transitions."))
		
	
	def does_match_filter(self, my_trans, filter):
		""" Determine if a filter matches """
		
		# get correct gettext method
		_ = self._
		
		# 1st match the filter category
		if self.filter_category == "Show All":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(my_trans).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True
			
		elif self.filter_category == "Common" and my_trans in ("Dissolve", "Wipe bottom to top", 
															   "Wipe top to bottom", "Wipe left to right", 
															   "Wipe right to left", "Circle in to out",
															   "Circle out to in"):
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(my_trans).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True

		# no match to one of these rules
		# show the effect, just incase
		return False
		
		
	def clear(self):
		self.store.clear()
		
		for column in self.view.get_columns():
			self.view.remove_column(column)
	
	def on_icvTransitions_drag_begin(self, widget, *args):
		context = args[0]
		
		# update drag type
		self.project.form.drag_type = "transition"
	
		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()
		context.set_icon_pixbuf(pixbuf, 15, 10)


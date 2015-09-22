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
import gtk, gobject, pango, mlt
from classes import project, effect

# init the foreign language
from language import Language_Init


class OpenShotTree:
	
	def __init__(self, treeview, project):
	
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _

		# init vars
		self.treeview = treeview
		self.project = project
		self.filter_category = "Show All"
		
		self.store = None
	
		# Setup columns for treeview or iconview
		if type(treeview) == gtk.TreeView:
			# tree view
			# create a TreeStore
			self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str, str)
			
			self.treeviewAddGeneralPixbufColumn(self.treeview, _("Thumb"), 0, resizable=False, reorderable=False, project=self.project)
			self.treeviewAddGeneralTextColumn(self.treeview, _("Name"), 1, resizable=False, reorderable=True, editable=False, visible=True, elipses=False, autosize=True, project=self.project)
			self.treeviewAddGeneralTextColumn(self.treeview, "service", 2, resizable=True, reorderable=True, editable=False, visible=False, project=self.project)
			self.treeviewAddGeneralTextColumn(self.treeview, "unique_id", 3, resizable=True, reorderable=True, editable=False, visible=False, project=self.project)
			self.treeviewAddGeneralTextColumn(self.treeview, "description", 4, resizable=True, reorderable=True, editable=False, visible=False, project=self.project)
		else:
			# icon view
			# create a ListStore
			self.store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str, str)

			self.treeview.set_pixbuf_column(0)
			self.treeview.set_text_column(2)
			self.treeview.set_text_column(1)


		# Set the treeview's data model
		self.treeview.set_model(self.store)

		# populate tree 
		self.populate_tree()

		# connect signals
		self.treeview.connect_after('drag_begin', self.on_treeEffects_drag_begin)
		
		# set tooltip column
		self.treeview.set_tooltip_column(4)
		
		
	def populate_tree(self, clip_effects=None, category=None, filter=None):
		
		# get correct gettext method
		_ = self._
		
		# set filter category (if any)
		if category:
			self.filter_category = category
		
		# clear the tree data
		self.store.clear()

		
		# Init List of Effects
		EFFECTS_DIR = self.project.EFFECTS_DIR
		my_effects = []
		unique_ids = []
		if isinstance(clip_effects, list):
			# loop through clip effects, and build list of real effect objects (with ALL meta-data)
			for clip_effect1 in clip_effects:
				# get real clip effect object
				real_effect = self.get_real_effect(service=clip_effect1.service)
				my_effects.append(real_effect)
				unique_ids.append(clip_effect1.unique_id)
		else:	
			my_effects = self.project.form.effect_list
		
		# Get icon size from settings
		icon_size = self.project.form.settings.general["icon_size"]
		if type(self.treeview) == gtk.IconView:
			# only resize IconView
			if icon_size == "small":
				self.treeview.set_item_width(98)
			else:
				self.treeview.set_item_width(130)
		
		
		# Add effects to dropdown
		counter = 0
		for my_effect in my_effects:

			# get image for filter
			file_path = os.path.join(EFFECTS_DIR, "icons", icon_size, my_effect.icon)
			
			# get the pixbuf
			pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)

			# resize thumbnail
			#pbThumb = pbThumb.scale_simple(120, 96, gtk.gdk.INTERP_BILINEAR)
			
			# perminately save resized icon
			#pbThumb.save(os.path.join("/home/jonathan/Desktop/thumbnails", my_effect.icon), "png", {})
			
			# is frei0r effect library installed?
			if self.project.form.has_frei0r_installed == False and my_effect.service.startswith("frei0r"):
				# frei0r not installed, and this is a frei0r effect
				# skip to next item in loop
				continue
			
			# does the frei0r installation include this effect?
			if my_effect.service.startswith("frei0r"):
				if my_effect.service not in self.project.form.filters:
					# don't add this effect, skip to the next one
					print "Warning: effect not found in your version of Frei0r: %s" % my_effect.service
					continue

			# The way sox effects filters are indentified in MLT
			# changed in 0.7.4. Previously, there was just a generic 'sox' filter.
			# From 0.7.4, each sox effect is output individually.
			# The following check will only work with versions 0.7.4 and above
			# of MLT.
			if self.project.form.MyVideo:
				if self.project.form.MyVideo.check_version(0, 7, 4):
					# does the sox installation include this effect?
					if my_effect.service.startswith("sox"):
						if ("sox.%s" % my_effect.audio_effect) not in self.project.form.filters:
							# don't add this effect, skip to the next one
							print "Warning: effect not found in your version of Sox: %s" % ("sox:%s" % my_effect.audio_effect)
							continue
			
			# check if a filter matches (if any)
			if not self.does_match_filter(my_effect, filter):
				# NO match, so skip to next filter
				continue
			
			# add effect to tree
			item = self.store.append(None)
			self.store.set_value(item, 0, pbThumb)
			self.store.set_value(item, 1, _(my_effect.title))
			if my_effect.audio_effect:
				self.store.set_value(item, 2, "%s:%s" % (my_effect.service, my_effect.audio_effect))
			else:
				self.store.set_value(item, 2, my_effect.service)
			
			if clip_effects:
				self.store.set_value(item, 3, unique_ids[counter])
			else:
				self.store.set_value(item, 3, None)
				
			self.store.set_value(item, 4, _(my_effect.description))
				
			counter += 1
			
			
	def does_match_filter(self, my_effect, filter):
		""" Determine if a filter matches """
		
		# get correct gettext method
		_ = self._
		
		# 1st match the filter category
		if self.filter_category == "Show All":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(my_effect.title).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True
			
		elif self.filter_category == "Video" and my_effect.category == "Video":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(my_effect.title).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True
			
		elif self.filter_category == "Audio" and my_effect.category == "Audio":
			
			if filter:
				# match text of filter
				if _(filter).lower() in _(my_effect.title).lower():
					# text matches
					return True
			else:
				# no additional text filter 
				return True

		# no match to one of these rules
		# show the effect, just incase
		return False
				
		
	def get_real_effect(self, service=None, title=None):
		""" Get the actual effect object from the service name """
		
		# get correct gettext method
		_ = self._
		
		# loop through the effects
		for my_effect in self.project.form.effect_list:

			if service:
				# find matching effect
				if my_effect.service == service or my_effect.service + ":" + my_effect.audio_effect == service:
					return my_effect
			
			if title:
				# find matching effect
				if _(my_effect.title) == _(title):
					return my_effect
			
		# no match found
		return None
			
	
	def on_treeEffects_drag_begin(self, widget, *args):
		context = args[0]
		
		# update drag type
		self.project.form.drag_type = "effect"
	
		# Get the drag icon
		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
		pixbuf = play_image.get_pixbuf()
		context.set_icon_pixbuf(pixbuf, 15, 10)
		
	
	def treeviewAddGeneralTextColumn(self, treeview, name, pos = 0, resizable=True, reorderable=False, editable=False, visible=True, elipses=False, autosize=False, project=None):
		'''Add a new text column to the model'''
	
		cell = gtk.CellRendererText()
		cell.set_property('editable', editable)
		if (elipses):
			cell.set_property("ellipsize", pango.ELLIPSIZE_END)
		col = gtk.TreeViewColumn(name, cell, markup = pos)
		if (autosize):
			col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
			col.set_expand(False)
		col.set_resizable(resizable)
		col.set_reorderable(reorderable)
		col.set_property("visible", visible)
		treeview.append_column(col)
		treeview.set_headers_clickable(True)
		
		if (editable):
			model = treeview.get_model()
			cell.connect('edited', self.cell_edited,model, project)
		
		if (reorderable):
			col.set_sort_column_id(pos)
	
		return cell, col
	
	def treeviewAddGeneralPixbufColumn(self, treeview, name, pos = 0, resizable=True, reorderable=False, project=None):
		
		'''Add a new gtk.gdk.Pixbuf column to the model'''
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(name, cell, pixbuf = pos)
		col.set_resizable(resizable)
		col.set_reorderable(reorderable)
		col.set_alignment(0.0)
		treeview.append_column(col)
		treeview.set_headers_clickable(True)
	
		if (reorderable):
			col.set_sort_column_id(pos)
	
		return cell, col
	
	
	def cell_edited(self, cell, row, new_text, model, project=None):
		
		##Fired when the editable label cell is edited
		#get the row that was edited
		#iter = model.get_iter_from_string(row)
		#column = cell.get_data(_("Label"))
		#set the edit in the model
		#model.set(iter,3,new_text)
		#update the file object with the label edit
		#filename = model.get_value(iter, 1)
		#project.project_folder.UpdateFileLabel(filename, new_text, 0)
		pass



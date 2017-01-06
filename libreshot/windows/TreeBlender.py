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
import gtk, gobject, pango, mlt
from classes import project, effect

# init the foreign language
from language import Language_Init


class LibreShotTree:
	
	def __init__(self, treeview, project):
	
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
	
		# init vars
		self.treeview = treeview
		self.project = project
		
		# create a TreeStore
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str)
	
		# Set the treeview's data model
		self.treeview.set_model(self.store)
		self.treeviewAddGeneralPixbufColumn(self.treeview, _("Thumb"), 0, resizable=False, reorderable=False, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, _("Name"), 1, resizable=False, reorderable=True, editable=False, visible=True, elipses=False, autosize=True, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, "blend_file", 2, resizable=True, reorderable=True, editable=False, visible=False, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, "unique_id", 3, resizable=True, reorderable=True, editable=False, visible=False, project=self.project)

		# populate tree 
		self.populate_tree()

		# connect signals
		#self.treeview.connect_after('drag_begin', self.on_treeEffects_drag_begin)
		
		
	def populate_tree(self, clip_effects=None):
		
		# get correct gettext method
		_ = self._
		
		# clear the tree data
		self.store.clear()

		# Init List of Blender Files
		BLENDER_DIR = self.project.BLENDER_DIR
		my_effects = []
		unique_ids = []
		my_effects = self.project.form.blender_list
		
		
		# Add effects to dropdown
		counter = 0
		for my_effect in my_effects:

			# get image for filter
			file_path = os.path.join(BLENDER_DIR, "icons", my_effect.icon)
			
			# get the pixbuf
			pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)

			# resize thumbnail
			pbThumb = pbThumb.scale_simple(80, 62, gtk.gdk.INTERP_BILINEAR)
			
			# perminately save resized icon
			# pbThumb.save(os.path.join("/home/jonathan/Desktop/thumbnails", my_effect.icon), "png", {})
				
			
			# add transition to tree
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
				
			counter += 1
				
		
	def get_real_effect(self, service=None, title=None):
		""" Get the actual effect object from the service name """
		
		# get correct gettext method
		_ = self._
		
		# loop through the effects
		for my_effect in self.project.form.blender_list:

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
			
	
#	def on_treeEffects_drag_begin(self, widget, *args):
#		context = args[0]
#		
#		# update drag type
#		self.project.form.drag_type = "effect"
#	
#		# Get the drag icon
#		play_image = gtk.image_new_from_file(os.path.join(self.project.THEMES_DIR, self.project.theme, "icons", "plus.png"))
#		pixbuf = play_image.get_pixbuf()
#		context.set_icon_pixbuf(pixbuf, 15, 10)
		
	
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



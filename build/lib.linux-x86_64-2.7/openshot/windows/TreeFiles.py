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
import gtk, gobject, pango
from classes import project

# init the foreign language
from language import Language_Init


class OpenShotTree:
	
	def __init__(self, treeview, project):
	
		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
	
		# init vars
		self.treeview = treeview
		self.project = project
	
		# create a TreeStore
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, str, str)

		#set multiple selection mode on the tree
		selection = treeview.get_selection()
		selection.set_mode(gtk.SELECTION_MULTIPLE)
		
		# Set the treeview's data model
		self.treeview.set_model(self.store)
		self.treeviewAddGeneralPixbufColumn(self.treeview, _("Thumb"), 0, resizable=False, reorderable=False, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, _("File"), 1, resizable=True, reorderable=True, editable=False, visible=True, elipses=False, autosize=True, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, _("Length"), 2, resizable=True, reorderable=True, editable=False, visible=True, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, _("Label"), 3, resizable=True, reorderable=True, editable=True, visible=True, elipses=False, autosize=True, project=self.project)
		self.treeviewAddGeneralTextColumn(self.treeview, "unique_id", 4, resizable=True, reorderable=True, editable=True, visible=False, elipses=True, project=self.project)
	
		#self.row = {}
		#self.row["0"] = [None, "Choose a Video or Audio File to Begin", "", "", ""]
		#self.store.append(None, [self.row["0"]])
		#item = self.store.append(None, [[gtk.STOCK_OPEN, _("Choose a Video or Audio File to Begin"), "", "", ""]])	
		item = self.store.append(None)
		self.store.set_value(item, 0, None)
		self.store.set_value(item, 1, _("Choose a Video or Audio File to Begin"))
		self.store.set_value(item, 2, "")
		self.store.set_value(item, 3, "")
		self.store.set_value(item, 4, "")

		# connect signals
		self.treeview.connect_after('drag_begin', self.on_treeFiles_drag_begin)

		
	def on_treeFiles_drag_begin(self, widget, *args):
		context = args[0]
	
		# update drag type
		self.project.form.drag_type = "file"
	
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
		col = gtk.TreeViewColumn(name, cell, text = pos)
		if (autosize):
			col.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
			col.set_expand(False)
		col.set_resizable(resizable)
		col.set_reorderable(reorderable)
		col.set_visible(visible)
		treeview.append_column(col)
		treeview.set_headers_clickable(True)
		
		if (editable):
			model = treeview.get_model()
			cell.connect('edited', self.cell_edited,model, project)
			cell.connect('editing_started',self.cell_start_editing,model)
		
		if (reorderable):
			col.set_sort_column_id(pos)
	
		return cell, col
	
	
	def cell_start_editing(self,widget,*args):
		# update flag on form (for stop capturing keys)
		self.project.form.is_edit_mode = True
	
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
		
		# update flag on form (for stop capturing keys)
		self.project.form.is_edit_mode = False
		
		##Fired when the editable label cell is edited
		#get the row that was edited
		iter = model.get_iter_from_string(row)
		column = cell.get_data(_("Label"))
		#set the edit in the model
		model.set(iter,3,new_text)
		#update the file object with the label edit
		unique_id = model.get_value(iter, 4)
		self.project.project_folder.UpdateFileLabel(unique_id, new_text, 0)
		
	def set_project(self, project):
		self.project = project
		

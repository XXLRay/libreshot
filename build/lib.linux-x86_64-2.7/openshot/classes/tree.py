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

import gtk, gobject, pango
from classes.project import project

def treeviewAddGeneralTextColumn(treeview, name, pos = 0, resizable=True, reorderable=False, editable=False, visible=True, elipses=False, autosize=False, project=None):
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
		cell.connect('edited',cell_edited,model, project)
	
	if (reorderable):
		col.set_sort_column_id(pos)

	return cell, col

def treeviewAddGeneralPixbufColumn(treeview, name, pos = 0, resizable=True, reorderable=False, project=None):
	
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

def cell_edited(cell, row, new_text, model, project=None):
	
	##Fired when the editable label cell is edited
	#get the row that was edited
	iter = model.get_iter_from_string(row)
	column = cell.get_data("Label")
	#set the edit in the model
	model.set(iter,3,new_text)
	#update the file object with the label edit
	#filename = model.get_value(iter, 1)
	#project.project_folder.UpdateFileLabel(filename, new_text, 0)
	unique_id = model.get_value(iter, 4)
	project.project_folder.UpdateFileLabel(unique_id, new_text, 0)
	

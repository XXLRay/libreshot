#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   Copyright (C) 2009  Jonathan Thomas
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

import os
import gtk
from classes import messagebox, project, effect
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp

# init the foreign language
from language import Language_Init

class frmAddEffect(SimpleGtkBuilderApp):

	def __init__(self, path="AddEffect.ui", root="frmAddEffect", domain="LibreShot", parent=None, form=None, project=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext

		self.form = form
		self.project = project
		self.parent = parent
		EFFECTS_DIR = self.project.EFFECTS_DIR

		# Init Dropdown and model
		# create a ListStore
		self.store = gtk.ListStore(gtk.gdk.Pixbuf, str)
		self.sort_model = gtk.TreeModelSort(self.store)
		
		# Sort Effects ListStore
		self.sort_model.set_sort_column_id(1, gtk.SORT_ASCENDING)

		# Set the treeview's data model
		self.cboEffects.set_model(self.sort_model)
		
		# Init List of Effects
		effect_list = self.form.effect_list
		
		# Add effects to dropdown
		sorted_list = []
		for my_effect in effect_list:
			
			# is frei0r effect library installed?
			if self.form.has_frei0r_installed == False and my_effect.service.startswith("frei0r"):
				# frei0r not installed, and this is a frei0r effect
				# skip to next item in loop
				continue
			
			# does the frei0r installation include this effect?
			if my_effect.service.startswith("frei0r"):
				if my_effect.service not in self.form.filters:
					# don't add this effect, skip to the next one
					continue
			
			# get image for filter
			file_path = os.path.join(EFFECTS_DIR, "icons", "small", my_effect.icon)
			
			# get the pixbuf
			pbThumb = gtk.gdk.pixbuf_new_from_file(file_path)

			# add effect to tree
			item = self.store.append(None)
			self.store.set_value(item, 0, pbThumb)
			self.store.set_value(item, 1, _(my_effect.title))

		# show all controls
		self.frmAddEffect.show_all()
		
		
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmAddEffect.destroy()
		
		
	def on_frmAddEffect_destroy(self, widget, *args):
		print "on_frmAddEffect_destroy"
		
	def on_frmAddEffect_close(self, widget, *args):
		print "on_frmAddEffect_close"
		self.frmAddEffect.destroy()
		
	def on_frmAddEffect_destroy(self, widget, *args):
		print "on_frmAddEffect_destroy"
		
	def on_frmAddEffect_response(self, widget, *args):
		print "on_frmAddEffect_response"
		
	def on_btnOk_clicked(self, widget, *args):
		print "on_btnOk_clicked"

		# get Service name
		iter = self.cboEffects.get_active_iter()
		
		if not iter:
			# don't do anything if no effect is selected
			return
		
		# Get effect name
		effect_title = self.cboEffects.get_model().get_value(iter, 1)
		
		# Add the effect
		if effect_title:
			# get real effect object
			real_effect = self.parent.OSTreeEffects.get_real_effect(title=effect_title)
			
			# add effect
			if real_effect.audio_effect:
				# audio effect
				self.parent.copy_of_clip.Add_Effect("%s:%s" % (real_effect.service, real_effect.audio_effect))
			else:
				# service
				self.parent.copy_of_clip.Add_Effect(real_effect.service)
			
			# update effect tree
			self.parent.update_effects_tree()
		
		# close window
		self.frmAddEffect.destroy()


		
		
			
def main():
	frmImportImageSequence1 = frmImportImageSequence()
	frmImportImageSequence1.run()

if __name__ == "__main__":
	main()

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

import gtk, os, sys
from xdg.IconTheme import *

class EntryDialog(gtk.Dialog):

	def __init__(self, message="", default_text="", modal=True):


		gtk.Dialog.__init__(self)
		self.connect("destroy", self.quit)
		self.connect("delete_event", self.quit)
		if modal:
			self.set_modal(True)

		self.set_title("Openshot")

		self.set_resizable(False)

		if getIconPath("openshot"):
			self.set_icon_from_file(getIconPath("openshot"))

		box = gtk.VBox(spacing=10)
		box.set_border_width(10)
		self.vbox.pack_start(box)
		box.show()
		if message:
			label = gtk.Label(message)
		box.pack_start(label)

		label.show()
		self.entry = gtk.Entry()
		#Enable the user to hit the enter key
		self.entry.connect("activate",self.ok_clicked)
		self.entry.set_text(default_text)
		box.pack_start(self.entry)
		self.entry.show()
		self.entry.grab_focus()

		cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
		cancel_button.connect("clicked", self.quit)
		cancel_button.set_flags(gtk.CAN_DEFAULT)
		self.action_area.pack_start(cancel_button)
		cancel_button.show()

		ok_button = gtk.Button(stock=gtk.STOCK_OK)
		ok_button.connect("clicked", self.ok_clicked)
		ok_button.set_flags(gtk.CAN_DEFAULT)
		self.action_area.pack_start(ok_button)
		ok_button.show()
		ok_button.grab_default()

		self.ret = None

		self.run()


	def quit(self, w=None, event=None):

		self.hide()
		self.destroy()



	def ok_clicked(self, button):

		self.ret = self.entry.get_text()
		self.quit()


#call this to display an input box
def input_box(title="", message="", default_text="", modal=True):

	win = EntryDialog(message, default_text, modal=modal)

	return win.ret

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

import gtk, os, sys
from xdg.IconTheme import *

# init the foreign language
from language import Language_Init

def get_response(*args):
	
	# look for extra parameters
	parameters = None
	for arg in args:
		if type(arg) == dict:
			parameters = arg
			break
	
	# hide message dialog
	args[0].destroy()

	if args[1] == gtk.RESPONSE_YES:
		# call callback function (if any)
		if args[2]:
			# call callback
			if parameters:
				args[2](parameters)
			else:
				args[2]()
	elif args[1] == gtk.RESPONSE_NO:
		# call callback function (if any)
		if args[3]:
			# call callback
			if parameters:
				args[3](parameters)
			else:
				args[3]()
	else:
		pass
		

# show an error message (i.e. gtkDialog)
def show(title, error_message, buttons=gtk.BUTTONS_OK, yes_callback_function=None, no_callback_function=None, dialog_type=gtk.MESSAGE_INFO, secondary_message=None, *args):

	# parse out any dictionaries (needed for custom parameters)
	button_list = []
	parameters = None
	buttonA = None
	buttonB = None
	for arg in args:
		if not type(arg) == dict:
			if buttonA == None:
				buttonA = arg
			elif buttonB == None:
				buttonB = arg
				button_list.append((buttonA, buttonB))
				buttonA = None
				buttonB = None
		else:
			parameters = arg

	# create an error message dialog
	dialog = gtk.MessageDialog(
		parent		 = None,
		flags		  = gtk.DIALOG_MODAL,
		type		   = dialog_type,
		buttons		= buttons,
		message_format = error_message)
	dialog.set_title(title)
	dialog.format_secondary_text(secondary_message)
	
	for button in button_list:
		dialog.add_button(button[0], button[1])
	
	if getIconPath("libreshot"):
		dialog.set_icon_from_file(getIconPath("libreshot"))
		
	dialog.connect('response', get_response, yes_callback_function, no_callback_function, parameters)
	dialog.show()





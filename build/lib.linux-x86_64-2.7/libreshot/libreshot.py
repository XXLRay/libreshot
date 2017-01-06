#!/usr/bin/env python
#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#   It's a fork from OpenShot
#   Copyright (C) 2009  Jonathan Thomas, TJ
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

import os, sys
import gtk, locale
from classes import info

# Ensure GTK minimum version is met (this is a new requirement needed 
# for using GtkBuilder instead of Glade
gtk_major_version = gtk.gtk_version[0]
gtk_minor_version = gtk.gtk_version[1]
if not (gtk_major_version >= 2 and gtk_minor_version >= 18):
	print "Error: You must have GTK 2.18 or greater to run LibreShot.  Exiting..."
	sys.exit()

# Ensure the libreshot module directory is in the system path so relative 'import' statements work
base_path = os.path.dirname(os.path.abspath(__file__))
if sys.path.count(base_path) == 0:
	sys.path.insert(0, base_path)
	

# This method starts LibreShot
def main():
	""""Initialise common settings and check the operating environment before starting the application."""

	# Display version and exit (if requested)
	if( "--version" in sys.argv ):
		print "LibreShot version %s" % info.VERSION
		exit()

	print "--------------------------------"
	print "   LibreShot (version %s)" % info.SETUP['version']
	print "--------------------------------"

	# only allow 1 instance of LibreShot to run
	from classes import lock
	lock.check_pid(os.path.join(os.path.expanduser("~"), ".libreshot"))

	# import the locale, and set the locale. This is used for 
	# locale-aware number to string formatting
	locale.setlocale(locale.LC_ALL, '')

	# init threads - this helps support the 
	# multi-threaded architecture of mlt
	gtk.gdk.threads_init()
	gtk.gdk.threads_enter()

	# Create a default project object
	from classes import project
	current_project = project.project()

	# Create form object & refresh the data
	from windows.MainGTK import frmMain
	app = frmMain(project=current_project, version=info.SETUP['version'])
	app.refresh()
	app.run()


if __name__ == '__main__':
	main()

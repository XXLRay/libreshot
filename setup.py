#!/usr/bin/env python
#	LibreShot Video Editor is a program that creates, modifies, and edits video files.
#
#	This file is part of LibreShot Video Editor 
#   Fork of OpenShot (http://launchpad.net/libreshot/).
#   Copyright (C) 2011	TJ, Jonathan Thomas
#
#	LibreShot Video Editor is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	LibreShot Video Editor is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with LibreShot Video Editor.	If not, see <http://www.gnu.org/licenses/>.

import glob, os, sys, subprocess
from distutils.core import setup

print "Execution path: %s" % os.path.abspath(__file__)
from libreshot.classes import info

# Boolean: running as root?
ROOT = os.geteuid() == 0
# For Debian packaging it could be a fakeroot so reset flag to prevent execution of
# system update services for Mime and Desktop registrations.
# The debian/libreshot.postinst script must do those.
if not os.getenv("FAKEROOTKEY") == None:
	print "NOTICE: Detected execution in a FakeRoot so disabling calls to system update services."
	ROOT = False

os_files = [
	 # XDG application description
	 ('share/applications', ['xdg/libreshot.desktop']),
	 # XDG application icon
	 ('share/pixmaps', ['xdg/libreshot.svg']),
	 # XDG desktop mime types cache
	 ('share/mime/packages',['xdg/libreshot.xml']),
	 # launcher (mime.types)
	 ('lib/mime/packages',['xdg/libreshot']),
	 # man-page ("man 1 libreshot")
	 ('share/man/man1',['docs/libreshot.1']),
	 ('share/man/man1',['docs/libreshot-render.1']),
]

# Add all the translations
locale_files = []
for filepath in glob.glob("libreshot/locale/*/LC_MESSAGES/*"):
	filepath = filepath.replace('libreshot/', '')
	locale_files.append(filepath)
	

# Call the main Distutils setup command
# -------------------------------------
dist = setup(
	 scripts	= ['bin/libreshot','bin/libreshot-render'],
	 packages	 = ['libreshot', 'libreshot.widgets', 'libreshot.classes', 'libreshot.language', 'libreshot.windows', 'libreshot.uploads', 'libreshot.uploads.vimeo', 'libreshot.uploads.vimeo.httplib2', 'libreshot.uploads.vimeo.httplib2wrap', 'libreshot.uploads.vimeo.oauth2', 'libreshot.uploads.vimeo.oauth2.clients', 'libreshot.uploads.youtube', 'libreshot.uploads.youtube.atom', 'libreshot.uploads.youtube.gdata', 'libreshot.uploads.youtube.gdata.geo', 'libreshot.uploads.youtube.gdata.media', 'libreshot.uploads.youtube.gdata.oauth', 'libreshot.uploads.youtube.gdata.opensearch', 'libreshot.uploads.youtube.gdata.tlslite', 'libreshot.uploads.youtube.gdata.tlslite.integration', 'libreshot.uploads.youtube.gdata.tlslite.utils', 'libreshot.uploads.youtube.gdata.youtube'],
	 package_data = {
	 				'libreshot' : ['export_presets/*', 'images/*', 'locale/LibreShot/*', 'locale/README', 'profiles/*', 'themes/*/*.png', 'themes/*/*.xml', 'themes/*/icons/*.png', 'titles/*/*.svg', 'transitions/icons/medium/*.png', 'transitions/icons/small/*.png', 'transitions/*.pgm', 'transitions/*.png', 'transitions/*.svg', 'effects/icons/medium/*.png', 'effects/icons/small/*.png', 'effects/*.xml', 'blender/blend/*.blend', 'blender/icons/*.png', 'blender/earth/*.jpg', 'blender/scripts/*.py', 'blender/*.xml'] + locale_files,
	 				'libreshot.windows' : ['ui/*.ui', 'ui/icons/*'],
	 				'libreshot.uploads' : ['logos/*.png'],
	 				},
	 data_files = os_files,
	 **info.SETUP
)
# -------------------------------------


FAILED = 'Failed to update.\n'

if ROOT and dist != None:
	#update the XDG Shared MIME-Info database cache
	try: 
		sys.stdout.write('Updating the Shared MIME-Info database cache.\n')
		subprocess.call(["update-mime-database", os.path.join(sys.prefix, "share/mime/")])
	except:
		sys.stderr.write(FAILED)

	#update the mime.types database
	try: 
		sys.stdout.write('Updating the mime.types database\n')
		subprocess.call("update-mime")
	except:
		sys.stderr.write(FAILED)

	# update the XDG .desktop file database
	try:
		sys.stdout.write('Updating the .desktop file database.\n')
		subprocess.call(["update-desktop-database"])
	except:
		sys.stderr.write(FAILED)
	sys.stdout.write("\n-----------------------------------------------")
	sys.stdout.write("\nInstallation Finished!")
	sys.stdout.write("\nRun LibreShot by typing 'libreshot' or through the Applications menu.")
	sys.stdout.write("\n-----------------------------------------------\n")

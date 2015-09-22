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

import os, sys, threading, time, uuid


def check_directory_present(path, permissions = 0750):
	"""Confirm a directory exists and has the requested permissions.
	Returns False if the directory cannot be re-created."""

	ret = False

	if not os.path.exists(path):
		try:
			os.mkdir(path, permissions)
			ret = True

		except OSError:
			# TODO: Friendlier, GUI-based, non-fatal, exception handling needed
			sys.exit("Fatal: cannot create %s" % path)
	else:
		# TODO: check the permissions match and if not attempt to correct them
		ret = True

	return ret

def check_folders_exist(path):
	# ensure the user's ~/.openshot directory exists
	if not check_directory_present(path):
		# TODO: Friendlier, GUI-based, non-fatal, exception handling needed
		sys.exit("Fatal: cannot create %s" % path)

	# check that all sub-directories exist
	if not check_directory_present(os.path.join(path, "queue")):
		# TODO: Friendlier, GUI-based, non-fatal, exception handling needed
		sys.exit("Fatal: cannot create %s" % os.path.join(path, "queue"))

	if not check_directory_present(os.path.join(path, "thumbnail")):
		# TODO: Friendlier, GUI-based, non-fatal, exception handling needed
		sys.exit("Fatal: cannot create %s" % os.path.join(path, "thumbnail"))
		
	if not check_directory_present(os.path.join(path, "user_profiles")):
		# TODO: Friendlier, GUI-based, non-fatal, exception handling needed
		sys.exit("Fatal: cannot create %s" % os.path.join(path, "user_profiles"))
		
	if not check_directory_present(os.path.join(path, "blender")):
		# TODO: Friendlier, GUI-based, non-fatal, exception handling needed
		sys.exit("Fatal: cannot create %s" % os.path.join(path, "blender"))


def check_pid(path):
	""" Check and see if this is the only instance of OpenShot. If not, then kill this instance. """

	# ensure folders exist
	check_folders_exist(path)

	# get path to lock file
	pidPath = os.path.join(path, "pid.lock")
	
	if os.path.exists(pidPath):
		pid = 0
		is_running = False
		number_of_files = 0
		
		# get pid and check if pid is running (this doesn't kill it)
		try:
			# pid file exists
			f = open(pidPath, 'r')
			pid=int(f.read().strip())
			f.close()
			
			# does process exist?
			os.kill(pid, 0)
			
			# OpenShot is already running, so...
			is_running = True
			
		except:
			print "Process no longer exists: %s.  Creating new pid lock file." % pid
			
			# not running anymore (maybe program crashed... and left this pid file)
			fp=open(pidPath, 'w')
			fp.write(str(os.getpid()))
			fp.close()
			
			# OpenShot is not currently running, so...
			is_running = False
		
		# OpenShot is alreay running, so kill this instance (ONLY KILL IF IT CONTAINS ARGS)
		# The user should be able to run as many instances of OpenShot as needed... but when ARGS
		# are passed, it should only allow 1 instance
		if len(sys.argv) > 1:

			# loop through the remaining args
			print "Adding files to the watch queue:"
			for arg in sys.argv[1:]:
				
				# a media file, add it to the project tree
				# if the path isn't absolute, make it absolute
				if not os.path.isabs(arg):
					arg = os.path.abspath(arg)
				
				# ignore OSP project files
				if ".osp" not in arg:
					# print the path of the media file
					print arg
					
					# create a import queue file for the primary instance of OpenShot
					fp=open(os.path.join(path, "queue", str(uuid.uuid1())), 'w')
					fp.write(arg)
					fp.close()
					
					# increment counter
					number_of_files += 1
				
			# exit the program (if OpenShot is already running) and ARGV is passed in
			if is_running and number_of_files:
				sys.exit("Another instance of this program is already running")

	else:
		# pid file doesn't exist
		fp=open(pidPath, 'w')
		fp.write(str(os.getpid()))
		fp.close()



class queue_watcher ( threading.Thread ):
	""" This class polls the /queue/ folder, looking for files to import into OpenShot.  When it finds
	a text file, it should get the path out of the file, import the file, and then delete the file.  Only
	1 instance of OpenShot should be polling this folder. """
	
	def set_form(self, main_form):
		self.form = main_form

	def run ( self ):
		""" This is the main method on this thread.  This method should not return anything, or the 
		thread will no longer be active...  """
		
		import gobject

		self.path = self.form.project.USER_DIR
		self.queue_location = os.path.join(self.path, "queue")
		pidPath = os.path.join(self.path, "pid.lock")
		self.amAlive = True
		f = open(pidPath, 'r')
		pid=int(f.read().strip())
		f.close()
		
		# only allow this thread to run if this instance of OpenShot is the primary instance.
		# we can't have 2 instances both watching the /queue/ folder.
		if os.getpid() == pid:

			# this loop will continue as long as OpenShot is running
			while self.amAlive:
				needs_refresh = False

				# check for files in the /queue/ folder
				for filename in os.listdir(self.queue_location):
					# get full file path
					full_filename = os.path.join(self.queue_location, filename)
					
					# read the content of the file
					f = open(full_filename, 'r')
					import_path = f.read().strip()
					f.close()

					# IMPORT FILE
					if self.form.project.project_folder:
						gobject.idle_add(self.form.project.project_folder.AddFile, import_path)
					needs_refresh = True
	
					# delete import file
					os.remove(full_filename)
					
				# refresh project files list (if needed)
				if needs_refresh:
					if self.form:
						# change modified status
						gobject.idle_add(self.form.project.set_project_modified, True, False)
						# refresh form
						gobject.idle_add(self.form.refresh)

				# wait a little
				time.sleep(1) 
		
		else:
			print "Not the primary instance of OpenShot. Not starting queue watcher thread."

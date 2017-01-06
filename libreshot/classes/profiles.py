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

import os, sys

try:
	import mlt
except ImportError:
	print "*** ERROR: MLT Python bindings failed to import ***"
	

class mlt_profiles:
	
	def __init__(self, project):
		# get the path of LibreShot
		self.project = project
		self.path = self.project.BASE_DIR
		
		# get a list of all mlt profiles
		self.profile_list = []
		
		# get a list of files in the LibreShot /profiles directory
		file_list = os.listdir(self.project.PROFILES_DIR)
		
		for fname in file_list:
			file_name = fname
			file_path = os.path.join(self.project.PROFILES_DIR, file_name)
			
			# load profile object
			p = mlt.Profile(file_path)

			# add to list of profiles
			self.profile_list.append([p.description(), p])
			
		#get any user created profiles
		if os.path.exists(self.project.USER_PROFILES_DIR):
			user_list = os.listdir(self.project.USER_PROFILES_DIR)
			
			for fname in user_list:
				file_name = fname
				file_path = os.path.join(self.project.USER_PROFILES_DIR, file_name)
				
				# load profile object
				p = mlt.Profile(file_path)
	
				# add to list of profiles
				self.profile_list.append([p.description(), p])


	def get_profile_list(self):
		#return a list of mlt.Profile() objects
		#use this syntax to get the name:  self.profile_list[0].description()
		return sorted(self.profile_list)
	
	
	def get_profile(self, profile_name):
		# loop through all profiles
		for fname, p in self.profile_list:
			# compare description to param
			if profile_name == p.description():
				return p
		
		# load default profile object... if no match was found
		p = mlt.Profile("DV/DVD NTSC")
		
		# return the profile
		return p
	
	def profile_exists(self, profile_name):
		# loop through all profiles
		for fname, p in self.profile_list:
			# compare description to param
			if profile_name == p.description():
				return p
			
		#profile doesn't exist
		return False
		
		
def main():
	mlt_profiles1 = mlt_profiles()
	profile_list = mlt_profiles1.get_profile_list()
	mlt_profiles1.get_profile("DV/DVD NTSC")

if __name__ == "__main__":
	main()


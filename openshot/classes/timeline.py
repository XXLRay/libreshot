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



class timeline:
	"""This class contains methods to simply displaying time codes"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		

	def get_friendly_time(self, milli):
		"""Convert milliseconds to a tuple of the common time"""
		sec, milli = divmod(milli, 1000)
		min, sec = divmod(sec, 60)
		hour, min = divmod(min, 60)
		day, hour = divmod(hour, 24)
		week, day = divmod(day, 7)
		
		return (week, day, hour, min, sec, int(milli))
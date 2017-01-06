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

import os
import gtk
from classes import messagebox, profiles, project, video
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp
# init the foreign language
from language import Language_Init

class frmTransitionProperties(SimpleGtkBuilderApp):

	def __init__(self, path="TransitionProperties.ui", root="frmTransitionProperties", domain="LibreShot", form=None, project=None, current_transition=None, **kwargs):
		SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

		# Add language support
		_ = Language_Init.Translator(project).lang.gettext
		self._ = _
		
		# add items to direction combo
		options = [_("Transition"), _("Mask")]
		# loop through export to options
		for option in options:
			# append profile to list
			self.cboType.append_text(option)
			
		# add items to direction combo
		options = [_("Up"), _("Down")]
		# loop through export to options
		for option in options:
			# append profile to list
			self.cboDirection.append_text(option)

		self.form = form
		self.project = project
		self.current_transition = current_transition
		self.frmTransitionProperties.show_all()
		
		# init the project type properties
		self.lblName.set_text(self.current_transition.name)
		self.spinbtnStart.set_value(round(self.current_transition.position_on_track, 2))
		self.spinbtnLength.set_value(round(self.current_transition.length , 2))
		self.hsSoftness.set_value(self.current_transition.softness * 100.0)
		self.hsThreshold.set_value(self.current_transition.mask_value)
		
		# set the dropdown boxes
		self.set_type_dropdown()
		self.set_direction_dropdown()

		
	def set_type_dropdown(self):
		
		# get correct gettext method
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboType.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0)

			# check for the matching project type
			if self.current_transition.type == "mask" and value.lower() == _("Mask").lower():			
				# set the item as active
				self.cboType.set_active_iter(iter)
				break
			
			# check for the matching project type
			if self.current_transition.type == "transition" and value.lower() == _("Transition").lower():			
				# set the item as active
				self.cboType.set_active_iter(iter)
				break
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
		# disable if mask threshold
		if self.current_transition.type == "transition":
			self.hsThreshold.set_sensitive(False)
		else:
			self.hsThreshold.set_sensitive(True)
			
			
	def set_direction_dropdown(self):
		
		# get correct gettext method
		_ = self._
		
		# get the model and iterator of the project type dropdown box
		model = self.cboDirection.get_model()
		iter = model.get_iter_first()
		while True:
			# get the value of each item in the dropdown
			value = model.get_value(iter, 0).lower()

			# check for the matching project type
			if self.current_transition.reverse == False and value == _("Up").lower():			
				# set the item as active
				self.cboDirection.set_active_iter(iter)
				
			# check for the matching project type
			if self.current_transition.reverse == True and value == _("Down").lower():			
				# set the item as active
				self.cboDirection.set_active_iter(iter)
		
			# get the next item in the list
			iter = model.iter_next(iter)
			
			# break loop when no more dropdown items are found
			if iter is None:
				break
			
		# disable if mask
		if self.current_transition.type == _("Mask").lower():
			self.cboDirection.set_sensitive(False)
		else:
			self.cboDirection.set_sensitive(True)


		
		
	def on_cboType_changed(self, widget, *args):
		print "on_cboType_changed"
		
		# get correct gettext method
		_ = self._
		
		# get new type
		localType = self.cboType.get_active_text()
		
		# disable if mask
		if localType.lower() == _("Mask").lower():
			self.cboDirection.set_sensitive(False)
		else:
			self.cboDirection.set_sensitive(True)
			
		# disable if mask threshold
		if localType.lower() == _("Transition").lower():
			self.hsThreshold.set_sensitive(False)
		else:
			self.hsThreshold.set_sensitive(True)

	def on_spinbtnStart_value_changed(self, widget, *args):
		"""Prevents any part of the transition to go outside the timeline.
		A transition outside the timeline is a worthless transition."""
	
		start = self.spinbtnStart.get_value()
		length = self.spinbtnLength.get_value()
		end = start + length
		timeline_length = self.project.sequences[0].length
		
		if end > timeline_length:
			self.spinbtnStart.set_value(timeline_length - length)
	
	def on_spinbtnLength_value_changed(self, widget, *args):
		"""Prevents any part of the transition to go outside the timeline.
		A transition outside the timeline is a worthless transition."""
	
		start = self.spinbtnStart.get_value()
		length = self.spinbtnLength.get_value()
		end = start + length
		timeline_length = self.project.sequences[0].length
		
		if end > timeline_length:
			self.spinbtnLength.set_value(timeline_length - start)
	
	def on_btnCancel_clicked(self, widget, *args):
		print "on_btnCancel_clicked"
		self.frmTransitionProperties.destroy()
		
		
	def on_btnApply_clicked(self, widget, *args):
		print "on_btnApply_clicked"
		
		# get correct gettext method
		_ = self._
		
		# Get settings
		localStart = self.spinbtnStart.get_value()
		localLength = self.spinbtnLength.get_value()
		localcboType = self.cboType.get_active_text()
		localcboDirection = self.cboDirection.get_active_text().lower()
		localhsSoftness = self.hsSoftness.get_value()
		localhsThreshold = self.hsThreshold.get_value()
		
		# update position and length
		self.current_transition.position_on_track = localStart
		self.current_transition.length = localLength
		
		# update transition object
		if localcboType.lower() == _("Mask").lower():
			self.current_transition.type = "mask"
		else:
			self.current_transition.type = "transition"
		if localcboDirection == _("Up").lower():
			self.current_transition.reverse = False
		else:
			self.current_transition.reverse = True
		self.current_transition.softness = float(localhsSoftness) / 100.0
		self.current_transition.mask_value = localhsThreshold
		
		# mark project as modified
		self.project.set_project_modified(is_modified=True, refresh_xml=True, type = self._("Modified transition properties"))
		
		# Refresh the MLT XML file
		self.project.RefreshXML()
		
		# Refresh form
		self.project.form.refresh()
		
		# close window
		self.frmTransitionProperties.destroy()
		
	
			
def main():
	frmTransitionProperties = frmTransitionProperties()
	frmTransitionProperties.run()

if __name__ == "__main__":
	main()

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

import os, sys, subprocess, locale, gettext, datetime
import xml.dom.minidom as xml
import libreshot.classes.info as info

# This file helps you generate the POT file that contains all of the translatable
# strings / text in LibreShot.  Because some of our text is in custom XML files,
# the xgettext command can't correctly generate the POT file.  Thus... the 
# existance of this file. =)

# Command to create the individual language PO files (Ascii files)
#		$ msginit --input=LibreShot.pot --locale=fr_FR
#		$ msginit --input=LibreShot.pot --locale=es

# Command to update the PO files (if text is added or changed)
#		$ msgmerge en_US.po LibreShot.pot -U
#		$ msgmerge es.po LibreShot.pot -U

# Command to compile the Ascii PO files into binary MO files
#		$ msgfmt en_US.po --output-file=en_US/LC_MESSAGES/LibreShot.mo
#		$ msgfmt es.po --output-file=es/LC_MESSAGES/LibreShot.mo

# Command to compile all PO files in a folder
#		$ find -iname "*.po" -exec msgfmt {} -o {}.mo \;

# Command to combine the 2 pot files into 1 file
#       $ msgcat ~/libreshot/locale/LibreShot/LibreShot_source.pot ~/libreshot/libreshot/locale/LibreShot/LibreShot_glade.pot -o ~/libreshot/main/locale/LibreShot/LibreShot.pot


# get the path of the main LibreShot folder
langage_folder_path = os.path.dirname(os.path.abspath(__file__))
libreshot_path = os.path.dirname(langage_folder_path)
effects_path = os.path.join(libreshot_path, 'effects')
blender_path = os.path.join(libreshot_path, 'blender')
transitions_path = os.path.join(libreshot_path, 'transitions')
export_path = os.path.join(libreshot_path, 'export_presets')
locale_path = os.path.join(libreshot_path, 'locale', 'LibreShot')

print "-----------------------------------------------------"
print " Creating 4 temp POT files"
print "-----------------------------------------------------"

# create empty temp files in the /libreshot/language folder (these are used as temp POT files)
temp_files = ['LibreShot_source', 'LibreShot_glade', 'LibreShot_effects', 'LibreShot_export', 'LibreShot_transitions']
for temp_file in temp_files:
	if os.path.exists(temp_file):
		os.remove(temp_file)
	f = open(temp_file, "w")
	f.close()
	
print "-----------------------------------------------------"
print " Using xgettext to generate .Glade and .py POT files"
print "-----------------------------------------------------"

# Generate POT for Source Code strings (i.e. strings marked with a _("translate me"))
subprocess.call('find %s -iname "*.py" -exec xgettext -j -o %s --keyword=_ {} \;' % (libreshot_path, os.path.join(langage_folder_path, 'LibreShot_source')), shell=True)
subprocess.call('find %s -iname "*.ui" -exec xgettext -j -L Glade -o %s --keyword=translatable {} \;' % (libreshot_path, os.path.join(langage_folder_path, 'LibreShot_glade')), shell=True)

print "-----------------------------------------------------"
print " Updating auto created POT files to set CharSet"
print "-----------------------------------------------------"

temp_files = ['LibreShot_source', 'LibreShot_glade']
for temp_file in temp_files:
	# get the entire text
	f = open(os.path.join(langage_folder_path, temp_file), "r")
	# read entire text of file
	entire_source = f.read()
	f.close()
	
	# replace charset
	entire_source = entire_source.replace("charset=CHARSET", "charset=UTF-8")
	
	# Create Updated POT Output File
	if os.path.exists(os.path.join(langage_folder_path, temp_file)):
		os.remove(os.path.join(langage_folder_path, temp_file))
	f = open(os.path.join(langage_folder_path, temp_file), "w")
	f.write(entire_source)
	f.close()
	

print "-----------------------------------------------------"
print " Scanning custom XML files and finding text"
print "-----------------------------------------------------"

# Loop through the Effects XML
effects_text = {}
for file in os.listdir(effects_path):
	if os.path.isfile(os.path.join(effects_path, file)):
		# load xml effect file
		full_file_path = os.path.join(effects_path, file)
		xmldoc = xml.parse(os.path.join(effects_path, file))

		# add text to list
		effects_text[xmldoc.getElementsByTagName("title")[0].childNodes[0].data] = full_file_path
		effects_text[xmldoc.getElementsByTagName("description")[0].childNodes[0].data] = full_file_path
		
		# get params
		params = xmldoc.getElementsByTagName("param")
		
		# Loop through params
		for param in params:
			if param.attributes["title"]:
				effects_text[param.attributes["title"].value] = full_file_path
				
				
# Loop through the Blender XML
for file in os.listdir(blender_path):
	if os.path.isfile(os.path.join(blender_path, file)):
		# load xml effect file
		full_file_path = os.path.join(blender_path, file)
		xmldoc = xml.parse(os.path.join(blender_path, file))

		# add text to list
		effects_text[xmldoc.getElementsByTagName("title")[0].childNodes[0].data] = full_file_path
		#effects_text[xmldoc.getElementsByTagName("description")[0].childNodes[0].data] = full_file_path
		
		# get params
		params = xmldoc.getElementsByTagName("param")
		
		# Loop through params
		for param in params:
			if param.attributes["title"]:
				effects_text[param.attributes["title"].value] = full_file_path


# Loop through the Export Settings XML
export_text = {}
for file in os.listdir(export_path):
	if os.path.isfile(os.path.join(export_path, file)):
		# load xml export file
		full_file_path = os.path.join(export_path, file)
		xmldoc = xml.parse(os.path.join(export_path, file))

		# add text to list
		export_text[xmldoc.getElementsByTagName("type")[0].childNodes[0].data] = full_file_path
		export_text[xmldoc.getElementsByTagName("title")[0].childNodes[0].data] = full_file_path

# Loop through transitions and add to POT file
transitions_text = {}
for file in os.listdir(transitions_path):
	# load xml export file
	full_file_path = os.path.join(transitions_path, file)
	(fileBaseName, fileExtension)=os.path.splitext(file)
	
	# get transition name
	name = fileBaseName.replace("_", " ").capitalize()
	
	# add text to list
	transitions_text[name] = full_file_path



print "-----------------------------------------------------"
print " Creating the custom XML POT files"
print "-----------------------------------------------------"

# header of POT file
header_text = ""
header_text = header_text + '# LibreShot Video Editor POT Template File.\n'
header_text = header_text + '# Copyright (C) 2009  Jonathan Thomas\n'
header_text = header_text + '# This file is distributed under the same license as the PACKAGE package.\n'
header_text = header_text + '# Jonathan Thomas <Jonathan.Oomph@gmail.com>, 2009.\n'
header_text = header_text + '#\n'
header_text = header_text + '#, fuzzy\n'
header_text = header_text + 'msgid ""\n'
header_text = header_text + 'msgstr ""\n'
header_text = header_text + '"Project-Id-Version: LibreShot Video Editor (version: %s)\\n"\n' % info.VERSION
header_text = header_text + '"Report-Msgid-Bugs-To: Jonathan Thomas <Jonathan.Oomph@gmail.com>\\n"\n'
header_text = header_text + '"POT-Creation-Date: %s\\n"\n' % datetime.datetime.now()
header_text = header_text + '"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n'
header_text = header_text + '"Last-Translator: Jonathan Thomas <Jonathan.Oomph@gmail.com>\\n"\n'
header_text = header_text + '"Language-Team: https://translations.launchpad.net/+groups/launchpad-translators\\n"\n'
header_text = header_text + '"MIME-Version: 1.0\\n"\n'
header_text = header_text + '"Content-Type: text/plain; charset=UTF-8\\n"\n'
header_text = header_text + '"Content-Transfer-Encoding: 8bit\\n"\n'

# Create POT files for the custom text (from our XML files)
temp_files = [['LibreShot_effects',effects_text], ['LibreShot_export',export_text], ['LibreShot_transitions',transitions_text]]
for temp_file, text_dict in temp_files:
	f = open(temp_file, "w")
	
	# write header
	f.write(header_text)
	
	# loop through each line of text
	for k,v in text_dict.items():
		if k:
			f.write('\n')
			f.write('#: %s\n' % v)
			f.write('msgid "%s"\n' % k)
			f.write('msgstr ""\n')
	
	# close file
	f.close()
	
	
print "-----------------------------------------------------"
print " Combine all 5 temp POT files using msgcat command (this removes dupes) "
print "-----------------------------------------------------"
	
temp_files = ['LibreShot_source', 'LibreShot_glade', 'LibreShot_effects', 'LibreShot_export', 'LibreShot_transitions']
command = "msgcat"
for temp_file in temp_files:
	# append files
	command = command + " " + os.path.join(langage_folder_path, temp_file)
command = command + " -o " + os.path.join(locale_path, "LibreShot.pot")

print command

# merge all 4 temp POT files
subprocess.call(command, shell=True)
	
	
print "-----------------------------------------------------"
print " Create FINAL POT File from 4 temp POT files "
print "-----------------------------------------------------"

# get the entire text of LibreShot.POT
f = open(os.path.join(locale_path, "LibreShot.pot"), "r")
# read entire text of file
entire_source = f.read()
f.close()

# Create Final POT Output File
if os.path.exists(os.path.join(locale_path, "LibreShot.pot")):
	os.remove(os.path.join(locale_path, "LibreShot.pot"))
final = open(os.path.join(locale_path, "LibreShot.pot"), "w")
final.write(header_text)
final.write("\n")

# Trim the beginning off of each POT file
start_pos = entire_source.find("#: ")
trimmed_source = entire_source[start_pos:]

# Add to Final POT File
final.write(trimmed_source)
final.write("\n")
	
# Close final POT file
final.close()


print "-----------------------------------------------------"
print " Remove 4 temp POT files "
print "-----------------------------------------------------"

# Delete all 4 temp files
temp_files = ['LibreShot_source', 'LibreShot_glade', 'LibreShot_effects', 'LibreShot_export', 'LibreShot_transitions']
for temp_file in temp_files:
	if os.path.exists(temp_file):
		os.remove(temp_file)
		
# output success
print "-----------------------------------------------------"
print " The /libreshot/locale/LibreShot/LibreShot.pot file has"
print " been successfully created with all text in LibreShot."
print "-----------------------------------------------------"



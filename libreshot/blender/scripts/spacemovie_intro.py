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


# Import Blender's python API.  This only works when the script is being
# run from the context of Blender.  Blender contains it's own version of Python
# with this library pre-installed.
import bpy

# Load a font
def load_font(font_path):
	""" Load a new TTF font into Blender, and return the font object """
	# get the original list of fonts (before we add a new one)
	original_fonts = bpy.data.fonts.keys()
	
	# load new font
	bpy.ops.font.open(filepath=font_path)
	
	# get the new list of fonts (after we added a new one)
	for font_name in bpy.data.fonts.keys():
		if font_name not in original_fonts:
			return bpy.data.fonts[font_name]
		
	# no new font was added
	return None

# Debug Info:
# ./blender -b test.blend -P demo.py
# -b = background mode
# -P = run a Python script within the context of the project file

# Init all of the variables needed by this script.  Because Blender executes
# this script, OpenShot will inject a dictionary of the required parameters
# before this script is executed.
params = {		
			'title' : 'Oh Yeah! OpenShot!',
			'Alongtimeago' : 'Some cycles ago, in The Grid\nfar, far inside....',
			'Episode' : 'Episode I.V',
			'EpisodeTitle' : 'A NEW OPENSHOT',
			'TitleSpaceMovie' : 'Space\nMovie',
			'MainText' : 'It is a period of software war. Free software developers have won some battles with free, and open-source applications. They leave the source code available for everybody in the Galaxy, allowing people to access software knowledge and truth.\n\nBut the EULA Galactic Empire is not dead and prepares its revenge with an ultimate weapon: the blue screen of DEATH. This armored system can anihilate an entire device by a simple segfault.\n\nBut the rebel hackers have a secret weapon too: an atomic penguin which protects them from almost all digital injuries...',

			'extrude' : 0.1,
			'bevel_depth' : 0.02,
			'spacemode' : 'CENTER',
			'text_size' : 1.5,
			'width' : 1.0,
			'fontname' : 'Bfont',
			
			'color' : [0.8,0.8,0.8],
			'alpha' : 1.0,
'alpha_mode' : 'TRANSPARENT',
			
			'output_path' : '/tmp/',
			'fps' : 24,
			'quality' : 90,
			'file_format' : 'PNG',
			'color_mode' : 'RGBA',
			'horizon_color' : [0.0, 0.0, 0.0],
			'resolution_x' : 1920,
			'resolution_y' : 1080,
			'resolution_percentage' : 100,
			'start_frame' : 1,
			'end_frame' : 2232,
			'animation' : True,
		}

#INJECT_PARAMS_HERE

# The remainder of this script will modify the current Blender .blend project
# file, and adjust the settings.  The .blend file is specified in the XML file
# that defines this template in OpenShot.
#----------------------------------------------------------------------------

# Modify Text / Curve settings
#print (bpy.data.curves.keys())
bpy.data.objects['Alongtimeago'].data.body = params['Alongtimeago']
bpy.data.objects['Episode'].data.body = params['Episode']
bpy.data.objects['EpisodeTitle'].data.body = params['EpisodeTitle']
bpy.data.objects['TitleStarWars'].data.body = params['TitleSpaceMovie']
bpy.data.objects['MainText'].data.body = params['MainText']

# Set the render options.  It is important that these are set
# to the same values as the current OpenShot project.  These
# params are automatically set by OpenShot
bpy.context.scene.render.filepath = params["output_path"]
bpy.context.scene.render.fps = params["fps"]
try:
	bpy.context.scene.render.file_format = params["file_format"]
	bpy.context.scene.render.color_mode = params["color_mode"]
except:
	bpy.context.scene.render.image_settings.file_format = params["file_format"]
	bpy.context.scene.render.image_settings.color_mode = params["color_mode"]

# Set background transparency (SKY or TRANSPARENT)
try:
    bpy.context.scene.render.alpha_mode = params["alpha_mode"]
except:
    pass

bpy.data.worlds[0].horizon_color = params["horizon_color"]
bpy.context.scene.render.resolution_x = params["resolution_x"]
bpy.context.scene.render.resolution_y = params["resolution_y"]
bpy.context.scene.render.resolution_percentage = params["resolution_percentage"]
bpy.context.scene.frame_start = params["start_frame"]
bpy.context.scene.frame_end = params["end_frame"]

# Animation Speed (use Blender's time remapping to slow or speed up animation)
animation_speed = int(params["animation_speed"])	# time remapping multiplier
new_length = int(params["end_frame"]) * animation_speed	# new length (in frames)
bpy.context.scene.frame_end = new_length
bpy.context.scene.render.frame_map_old = 1
bpy.context.scene.render.frame_map_new = animation_speed
if params["start_frame"] == params["end_frame"]:
	bpy.context.scene.frame_start = params["end_frame"]
	bpy.context.scene.frame_end = params["end_frame"]

# Render the current animation to the params["output_path"] folder
bpy.ops.render.render(animation=params["animation"])

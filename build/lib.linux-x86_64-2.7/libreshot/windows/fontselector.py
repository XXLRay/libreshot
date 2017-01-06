#    This file is part of LibreShot Video Editor (http://launchpad.net/openshot/).
#
#    LibreShot Video Editor is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    LibreShot Video Editor is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with LibreShot Video Editor.  If not, see <http://www.gnu.org/licenses/>.

########################################################
# This is a custom font selector window
# that displays each font name in it's own font
#
########################################################

import os
import gtk, pango
from windows.SimpleGtkBuilderApp import SimpleGtkBuilderApp

# init the foreign language
from language import Language_Init


class frmFontProperties(SimpleGtkBuilderApp):

    def __init__(self, instance, path="fontselector.ui", root="frmFontProperties", domain="LibreShot", project=None, **kwargs):
        SimpleGtkBuilderApp.__init__(self, os.path.join(project.UI_DIR, path), root, domain, **kwargs)

        # Add language support
        _ = Language_Init.Translator(project).lang.gettext

        self.calling_form = instance

        #get the list of available fonts
        fonts = gtk.ListStore(str)
        self.init_treeview(self.treeFontList)

        pc = self.frmFontProperties.get_pango_context()
        for family in pc.list_families():
            fonts.append([family.get_name()])


        self.treeFontList.set_model(fonts)

        #sort the fonts alphabetically
        fonts.set_sort_column_id(0, gtk.SORT_ASCENDING)

        #add the callbacks
        self.treeFontList.connect("cursor-changed", self.family_changed_cb)
        self.btnItalic.connect("toggled", self.style_changed_cb)
        self.btnBold.connect("toggled", self.weight_changed_cb)
        
        self.frmFontProperties.show_all()

    def init_treeview(self, tv):
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Font family", cell, text=0, family=0)
        tv.append_column(column)

    def family_changed_cb(self, widget): 
        index = self.treeFontList.get_cursor()[0][0]
        font_family = self.treeFontList.get_model()[index][0]

        pc = self.treeFontList.get_pango_context()
        fd = pc.get_font_description()
        fd.set_family(font_family)
        
        size = int(30) * pango.SCALE
        fd.set_size(size)
        
        self.preview.modify_font(fd)

        self.btnBold.set_active(False)
        self.btnItalic.set_active(False)


    def style_changed_cb(self, widget):
        pc = self.preview.get_pango_context()
        fd = pc.get_font_description()
        if self.btnItalic.get_active():
            fd.set_style(pango.STYLE_ITALIC)
            self.calling_form.font_style = 'italic'
        else:
            fd.set_style(pango.STYLE_NORMAL)
            self.calling_form.font_style = 'normal'

        self.preview.modify_font(fd)

    def weight_changed_cb(self, widget):
        pc = self.preview.get_pango_context()
        fd = pc.get_font_description()
        if self.btnBold.get_active():
            fd.set_weight(pango.WEIGHT_BOLD)
            self.calling_form.font_weight = 'bold'
        else:
            fd.set_weight(pango.WEIGHT_NORMAL)
            self.calling_form.font_weight = 'normal'

        self.preview.modify_font(fd)

    def on_btnCancel_clicked(self, widget):
        self.frmFontProperties.destroy()

    def on_btnOK_clicked(self, widget):
        index = self.treeFontList.get_cursor()[0][0]
        font_family = self.treeFontList.get_model()[index][0]

        self.calling_form.font_family = font_family
        
        self.calling_form.set_font_style()

        self.frmFontProperties.destroy()

def main():
    frm_fontProperties = frmFontProperties()
    frm_fontProperties.run()

if __name__ == "__main__":
    main()	



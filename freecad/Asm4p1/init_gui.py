#!/usr/bin/env python3
# coding: utf-8

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  init_gui.py


import os
import sys
import re

import FreeCAD as App
import FreeCADGui as Gui

from . import asm4_locator
code_path  = os.path.dirname(asm4_locator.__file__)
sys.path.insert(1, code_path)

from . import asm4_libs as Asm4


class Assembly4p1Workbench(Gui.Workbench):

    def __init__(self):
        self.MenuText = "Assembly 4.1"
        self.ToolTip = "Assembly 4.1 workbench"
        self.Icon = os.path.join(Asm4.iconPath, "Assembly4")


    def Initialize(self):

        # Translations
        Gui.addLanguagePath(os.path.join(code_path, "../Resources/translations"))
        Gui.updateLocale()

        package_xml  = os.path.join(code_path, "../../package.xml")

        # If FreeCAD version >= 0.21
        try:
            package_data = App.Metadata(package_xml)
            release_date = package_data.Date
            version = package_data.Version
        except:
            release_date, version = self._get_version()

        App.Console.PrintMessage(f"Initializing Assembly4.1 workbench ({version}, {release_date}).")
        Gui.updateGui()

        from . import selection_filter
        self.selection_filter = selection_filter

        from . import new_assembly_cmd       # created an App::Part container called 'Assembly'
        from . import new_datum_cmd          # creates a new LCS in 'Model'
        from . import new_part_cmd           # creates a new App::Part container called 'Model'
        from . import insert_link_cmd        # inserts an App::Link to a 'Model' in another file
        from . import place_link_cmd         # places a linked part by snapping LCS (in the Part and in the Assembly)
        from . import import_datum_cmd       # creates an LCS in assembly and attaches it to an LCS relative to an external file
        from . import release_attachment_cmd # creates an LCS in assembly and attaches it to an LCS relative to an external file
        from . import make_binder_cmd        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        from . import variables_lib          # creates an LCS in assembly and attaches it to an LCS relative to an external file
        from . import animation_lib          # creates an LCS in assembly and attaches it to an LCS relative to an external file
        from . import update_assembly_cmd    # updates all parts and constraints in the assembly
        from . import make_array_cmd         # creates a new array of App::Link
        from . import variant_link_cmd       # creates a variant link
        from . import goto_document_cmd      # opens the documentof the selected App::Link
        from . import asm4_measure           # Measure tool in the Task panel
        from . import list_linked_files      # Explore assembly structure
        from . import export_files           # export assembly in a zip file preserving structure
        from . import show_hide_lcs_cmd      # shows/hides all the LCSs
        from . import configuration_engine   # save/restore configuration
        # from . import HelpCmd              # shows a basic help window

        # Fasteners is an external addon, so check if the user has it.
        if self._workbench_exists("FastenersWorkbench"):
            from . import fasteners_lib
            self.FastenersCmd = "Asm4_Fasteners"
        else:
            from . import fasteners_dummy
            self.FastenersCmd = "Asm4_insertScrew"

        # Create menus
        self.appendMenu("&Assembly", self._assembly_menu())
        self.appendMenu("&Constraints", self._constraints_menu())

        # Create toolbars
        self.appendToolbar("Assembly", self._assembly_toolbar())
        self.appendToolbar("Selection Filter", self._selection_toolbar())


    def Activated(self):
        from PySide import QtGui

        toolbar = None
        for tb in Gui.getMainWindow().findChildren(QtGui.QToolBar):
            if tb.objectName() == "Selection Filter":
                toolbar = tb
                break

        # make all buttons except last one (clear selection filter) checkable
        if toolbar is not None:
            for button in toolbar.actions()[0:-1]:
                button.setCheckable(True)


    def Deactivated(self):
        if self.selection_filter:
            self.selection_filter.observerDisable()


    def GetClassName(self):
        return "Gui::PythonWorkbench"


    def ContextMenu(self, recipient):

        # This is executed whenever the user right-clicks on screen
        # The recipient will be either "view" or "tree"

        context_menu = [
            "Asm4_gotoDocument",
            "Asm4_showLcs",
            "Asm4_hideLcs"
        ]

        # Commands to appear in the "Assembly" sub-menu in the contextual menu (right-click)
        assembly_submenu = [
            "Asm4_insertLink",
            "Asm4_placeLink",
            "Asm4_importDatum",
            "Asm4_FSparameters",
            "Separator",
            "Asm4_applyConfiguration"
        ]

        # Commands to appear in the "Create" sub-menu in the contextual menu (right-click)
        create_submenu =[
            "Asm4_newSketch",
            "Asm4_newBody",
            "Asm4_newLCS",
            "Asm4_newAxis",
            "Asm4_newPlane",
            "Asm4_newPoint",
            "Asm4_newHole",
            "Asm4_insertScrew",
            "Asm4_insertNut",
            "Asm4_insertWasher",
            "Separator",
            "Asm4_newConfiguration"
        ]

        self.appendContextMenu("", "Separator")
        self.appendContextMenu("", context_menu)
        self.appendContextMenu("Assembly", assembly_submenu)
        self.appendContextMenu("Create", create_submenu)
        self.appendContextMenu("", "Separator")


    def _get_version(package_xml):
        with open(package_xml, "r") as f:
            package_data = f.read()
        match_version = re.search(r"<version>(.*?)</version>", package_data)
        match_date = re.search(r"<date>(.*?)</date>", package_data)
        if match_version:
            version = match_version.group(1)
        if match_date:
            release_date = match_version.group(1)
        return release_date, version


    def _assembly_menu(self):
        cmds = [
            "Asm4_newAssembly",
            "Asm4_newPart",
            "Asm4_newBody",
            "Asm4_newGroup",
            "Asm4_newSketch",
            "Asm4_createDatum",
            self.FastenersCmd,
            "Separator",
            "Asm4_insertLink",
            "Asm4_mirrorArray",
            "Asm4_linearArray",
            "Asm4_circularArray",
            "Asm4_expressionArray",
            "Asm4_variantLink",
            "Separator",
            "Asm4_cloneFastenersToAxes",
            "Asm4_importDatum",
            "Asm4_shapeBinder",
            "Separator",
            "Asm4_listLinkedFiles",
            "Asm4_ExportFiles",
            "Asm4_Measure",
            "Asm4_showLcs",
            "Asm4_hideLcs",
            "Asm4_addVariable",
            "Asm4_delVariable",
            "Asm4_Animate",
            "Asm4_openConfigurations"
        ]
        return cmds


    def _constraints_menu(self):
        cmds = [
            "Asm4_placeLink",
            "Asm4_releaseAttachment",
            "Separator",
            "Asm4_updateAssembly"
        ]
        return cmds


    def _assembly_toolbar(self):
        cmds = [
            "Asm4_newAssembly",
            "Asm4_newPart",
            "Asm4_newBody",
            "Asm4_newGroup",
            "Asm4_insertLink",
            "Asm4_variantLink",
            self.FastenersCmd,
            "Separator",
            "Asm4_newSketch",
            'Asm4_createDatum',
            "Asm4_importDatum",
            "Asm4_shapeBinder",
            "Separator",
            "Asm4_placeLink",
            "Asm4_releaseAttachment",
            "Asm4_updateAssembly",
            "Separator",
            "Asm4_mirrorArray",
            "Asm4_linearArray",
            "Asm4_circularArray",
            "Asm4_expressionArray",
            "Asm4_addVariable",
            "Asm4_delVariable",
            "Separator",
            "Asm4_Animate",
            "Asm4_Measure",
            "Asm4_listLinkedFiles",
            "Asm4_ExportFiles",
            'Asm4_showLcs',
            'Asm4_hideLcs',
            "Asm4_openConfigurations"
        ]
        return cmds


    def _selection_toolbar(self):
        cmds =  [
            "Asm4_SelectionFilterVertexCmd",
            "Asm4_SelectionFilterEdgeCmd",
            "Asm4_SelectionFilterFaceCmd",
            "Asm4_selObserver3DViewCmd" ,
            "Asm4_SelectionFilterClearCmd"
        ]
        return cmds


    def _workbench_exists(self, workbench_name):
        workbenches = Gui.listWorkbenches()
        for wb in workbenches.keys():
            if wb == workbench_name:
                return True
        return False





wb = Assembly4p1Workbench()
Gui.addWorkbench(wb)

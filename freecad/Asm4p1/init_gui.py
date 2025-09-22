# -*- coding: utf-8 -*-
###################################################################################
#
#  InitGui.py
#
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
#
###################################################################################


import os, sys

import FreeCAD as App
import FreeCADGui as Gui

from . import asm4_locator

global Asm4_path, Asm4_icon, Asm4_code, Asm4_trans
Asm4_path  = os.path.dirname( asm4_locator.__file__ )
Asm4_code  = os.path.join(Asm4_path, "./")
Asm4_icon  = os.path.join(Asm4_path, '../Resources/icons/Assembly4.svg' )
Asm4_trans = os.path.join(Asm4_path, "../Resources/translations")

# insert python search path
sys.path.insert(1, Asm4_code)

# I don't like this being here
from . import selection_filter


"""
    +-----------------------------------------------+
    |            Initialize the workbench           |
    +-----------------------------------------------+
"""
class Assembly4p1Workbench(Gui.Workbench):

    global Asm4_path, Asm4_icon, Asm4_code, Asm4_trans
    global selectionFilter
    MenuText = "Assembly 4.1"
    ToolTip = "Assembly 4.1 workbench"
    Icon = Asm4_icon

    def __init__(self):
        "This function is executed when FreeCAD starts"

    def Activated(self):
        "This function is executed when the workbench is activated"
        # make buttons of the selection toolbar checkable
        from PySide import QtGui
        mainwin = Gui.getMainWindow()
        sf_tb = None
        for tb in mainwin.findChildren(QtGui.QToolBar):
            if tb.objectName()=='Selection Filter':
                sf_tb = tb
        # make all buttons except last one (clear selection filter) checkable
        if sf_tb is not None:
            for button in sf_tb.actions()[0:-1]:
                button.setCheckable(True)
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        selection_filter.observerDisable()
        return

    def GetClassName(self):
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"


        """
    +-----------------------------------------------+
    |        This is where all is defined           |
    +-----------------------------------------------+
        """
    def Initialize(self):

        # Translations
        # from Asm4_Translate import Qtranslate
        Gui.addLanguagePath(Asm4_trans)
        Gui.updateLocale()

        # Assembly4 version info
        # with file package.xml (FreeCAD ≥0.21)
        packageFile  = os.path.join( Asm4_path, '../../package.xml' )

        # with file VERSION (FreeCAD > 0.20)
        try:
            metadata     = App.Metadata(packageFile)
            Asm4_date    = metadata.Date
            Asm4_version = metadata.Version

        # with file VERSION (FreeCAD ≤ 0.20)
        except:
            import re
            with open(packageFile, "r") as f:
                xml = f.read()  # single string with the entire file content
            match_version = re.search(r"<version>(.*?)</version>", xml)
            match_date = re.search(r"<date>(.*?)</date>", xml)
            if match_version:
                Asm4_version = match_version.group(1)
            if match_date:
                Asm4_date = match_version.group(1)
        
        App.Console.PrintMessage("Initializing Assembly4.1 workbench"+ ' ('+Asm4_version+') .')
        Gui.updateGui()
        # import all stuff
        from . import new_assembly_cmd    # created an App::Part container called 'Assembly'
        self.dot()
        from . import new_datum_cmd         # creates a new LCS in 'Model'
        self.dot()
        from . import new_part_cmd          # creates a new App::Part container called 'Model'
        self.dot()
        from . import info_part_cmd         # edits part information for BoM
        self.dot()
        from . import insert_link_cmd       # inserts an App::Link to a 'Model' in another file
        self.dot()
        from . import place_link_cmd        # places a linked part by snapping LCS (in the Part and in the Assembly)
        self.dot()
        from . import import_datum_cmd      # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        from . import release_attachment_cmd# creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        from . import make_binder_cmd       # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        from . import variables_lib        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        from . import animation_lib        # creates an LCS in assembly and attaches it to an LCS relative to an external file
        self.dot()
        from . import update_assembly_cmd   # updates all parts and constraints in the assembly
        self.dot()
        from . import make_array_cmd        # creates a new array of App::Link
        self.dot()
        from . import variant_link_cmd      # creates a variant link
        self.dot()
        from . import goto_document_cmd     # opens the documentof the selected App::Link
        self.dot()
        from . import asm4_measure        # Measure tool in the Task panel
        self.dot()
        from . import make_bom_cmd          # creates the parts list
        self.dot()
        from . import check_interference   # check interferences btween parts inside the Assembly
        self.dot()
        from . import export_files         # creates a hierarchical tree listing of files in an assembly
        self.dot()
        # import HelpCmd             # shows a basic help window
        # self.dot()
        from . import show_hide_lcs_cmd      # shows/hides all the LCSs
        self.dot()
        from . import configuration_engine # save/restore configuration
        self.dot()

        # Fasteners
        if self.checkWorkbench('FastenersWorkbench'):
            # a library to handle fasteners from the FastenersWorkbench
            from . import fasteners_lib
            self.FastenersCmd = 'Asm4_Fasteners'
        else:
            # a dummy library if the FastenersWorkbench is not installed
            from . import fasteners_dummy
            self.FastenersCmd = 'Asm4_insertScrew'
        self.dot()


        # Define Menus
        # commands to appear in the Assembly4 menu 'Assembly'
        self.appendMenu("&Assembly", self.assemblyMenuItems())
        self.dot()

        # put all constraints related commands in a separate menu
        self.appendMenu("&Constraints", self.constraintsMenuItems())
        self.dot()

        # self.appendMenu("&Geometry",["Asm4_newPart"])

        # Define Toolbars
        # commands to appear in the Assembly4 toolbar
        self.appendToolbar("Assembly", self.assemblyToolbarItems())
        self.dot()

        # build the selection toolbar
        self.appendToolbar("Selection Filter", self.selectionToolbarItems())
        self.dot()

        # self.appendToolbar("Geometry",["Asm4_newPart"])

        App.Console.PrintMessage(" " + "done" + ".\n")
        """
    +-----------------------------------------------+
    |           Initialisation finished             |
    +-----------------------------------------------+
        """



    """
    +-----------------------------------------------+
    |            Assembly Menu & Toolbar            |
    +-----------------------------------------------+
    """
    def assemblyMenuItems(self):
        commandList = [ "Asm4_newAssembly",
                        "Asm4_newPart",
                        "Asm4_newBody",
                        "Asm4_newGroup",
                        "Asm4_newSketch",
                        'Asm4_createDatum',
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
                        "Asm4_infoPart",
                        "Asm4_makeLocalBOM",
                        "Asm4_makeBOM",
                        "Asm4_listLinkedFiles",
                        "Asm4_checkInterference",
                        "Asm4_Measure",
                        'Asm4_showLcs',
                        'Asm4_hideLcs',
                        "Asm4_addVariable",
                        "Asm4_delVariable",
                        "Asm4_Animate",
                        "Asm4_openConfigurations"
                        ]
        return commandList

    def constraintsMenuItems(self):
        commandList = [ "Asm4_placeLink",
                        "Asm4_releaseAttachment",
                        "Separator",
                        "Asm4_updateAssembly",
                        "Separator",
                        ]
        return commandList

    def assemblyToolbarItems(self):
        commandList = [ "Asm4_newAssembly",
                        "Asm4_newPart",
                        "Asm4_newBody",
                        "Asm4_newGroup",
                        "Asm4_infoPart",
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
                        "Asm4_variablesCmd",
                        "Separator",
                        "Asm4_Animate",
                        "Asm4_Measure",
                        "Asm4_makeBOM",
                        "Asm4_listLinkedFiles",
                        'Asm4_showLcs',
                        'Asm4_hideLcs',
                        "Asm4_checkInterference",
                        "Asm4_openConfigurations"
                        ]
        return commandList


    """
    +-----------------------------------------------+
    |                 Selection Toolbar             |
    +-----------------------------------------------+
    """
    def selectionToolbarItems(self):
        # commands to appear in the Selection toolbar
        commandList =  ["Asm4_SelectionFilterVertexCmd",
                        "Asm4_SelectionFilterEdgeCmd",
                        "Asm4_SelectionFilterFaceCmd",
                        "Asm4_selObserver3DViewCmd" ,
                        "Asm4_SelectionFilterClearCmd"]
        return commandList


    """
    +-----------------------------------------------+
    |                Contextual Menus               |
    +-----------------------------------------------+
    """
    def ContextMenu(self, recipient):
        # This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        contextMenu  = ['Asm4_gotoDocument'  ,
                        'Asm4_showLcs'       ,
                        'Asm4_hideLcs'       ]
        # commands to appear in the 'Assembly' sub-menu in the contextual menu (right-click)
        assemblySubMenu =[ "Asm4_insertLink" ,
                        "Asm4_placeLink"     ,
                        "Asm4_importDatum"   ,
                        'Asm4_FSparameters'  ,
                        'Separator'          ,
                        'Asm4_applyConfiguration']
        # commands to appear in the 'Create' sub-menu in the contextual menu (right-click)
        createSubMenu =["Asm4_newSketch",
                        "Asm4_newBody",
                        "Asm4_newLCS",
                        "Asm4_newAxis",
                        "Asm4_newPlane",
                        "Asm4_newPoint",
                        "Asm4_newHole",
                        "Asm4_insertScrew",
                        "Asm4_insertNut",
                        "Asm4_insertWasher",
                        'Separator',
                        'Asm4_newConfiguration']

        self.appendContextMenu("", "Separator")
        self.appendContextMenu("", contextMenu)  # add commands to the context menu
        self.appendContextMenu("Assembly", assemblySubMenu)  # add commands to the context menu
        self.appendContextMenu("Create", createSubMenu)  # add commands to the context menu
        self.appendContextMenu("", "Separator")



    """
    +-----------------------------------------------+
    |               helper functions                |
    +-----------------------------------------------+
    """
    def checkWorkbench( self, workbench ):
        # checks whether the specified workbench (a 'string') is installed
        listWB = Gui.listWorkbenches()
        hasWB = False
        for wb in listWB.keys():
            if wb == workbench:
                hasWB = True
        return hasWB

    # prints a dot in the consome window to show progress
    def dot(self):
        App.Console.PrintMessage(".")
        Gui.updateGui()





"""
    +-----------------------------------------------+
    |          actually make the workbench          |
    +-----------------------------------------------+
"""
wb = Assembly4p1Workbench()
Gui.addWorkbench(wb)

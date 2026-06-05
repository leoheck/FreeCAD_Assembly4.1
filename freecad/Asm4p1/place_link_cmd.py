#!/usr/bin/env python3
# coding: utf-8

# insert_link_cmd.py
#
# LGPL
# Copyright HUBERT Zoltán

import os
import time

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

from . import asm4_libs as Asm4
from .place_link_ui import PlaceLinkUI
from .place_part_ui import placePartUI
from . import selection_filter



class PlaceLinkCmd():

    def __init__(self):
        super(PlaceLinkCmd, self).__init__()


    def GetResources(self):
        return {
            "MenuText": "Edit Placement of a Part",
            "Accel": "A, E",
            "ToolTip": "Move/Attach a Part in the assembly",
            "Pixmap" : os.path.join(Asm4.iconPath , "Place_Link.svg")
        }


    def IsActive(self):
        if len(Asm4.findAssemblies()) >= 1:
            obj = Asm4.SELECTED_INSTANCE
            if not obj:
                if Gui.Selection.getSelection():
                    obj = Gui.Selection.getSelection()[0]
            if obj and Asm4.isAsm4EE(obj) and Asm4.isLinkToPart(obj):
                return True
        return False


    def Activated(self):

        selection = Asm4.SELECTED_INSTANCE
        if selection is None:
            if Gui.Selection.getSelection():
                Asm4.SELECTED_INSTANCE = Gui.Selection.getSelection()[0]
                selection = Asm4.SELECTED_INSTANCE

        # may-be an Asm4::VariantLink?
        if selection is None:
            selection = Asm4.getSelectedVarLink()

        if selection is None:
            return False

        # if we found a valid link
        if selection is not None:
            # check that it's in the root assembly
            # parent = selection.getParentGeoFeatureGroup()
            parent = Asm4.TARGET_ASM
            if parent is None:
                parent = selection.getParentGeoFeatureGroup()

            if parent is None:
                return

            # if parent and parent == Asm4.getAssembly():
            if parent:

                # if it's a valid assembly and part
                if Asm4.isAsm4EE(selection):
                    # BUGFIX: if the part was corrupted by Assembly4 v0.11.5:
                    if hasattr(selection,'MapMode'):
                        Asm4.warningBox("This Part has the Attachment extension, it can only be placed manually")
                    else:
                        # launch the UI in the task panel
                        ui = PlaceLinkUI()
                        Gui.Control.showDialog(ui)
                # else try to convert it
                else:
                    convert = Asm4.confirmBox("This Part wasn't assembled with this Assembly4 WorkBench, but I can convert it.")
                    if convert:
                        Asm4.makeAsmProperties( selection, reset=True )
                        # launch the UI in the task panel
                        ui = PlaceLinkUI()
                        Gui.Control.showDialog(ui)
            else:
                Asm4.warningBox('Please select a link in the assembly Model.')
        else:
            # or any part that has a Placement ?
            if len(Gui.Selection.getSelection())==1:
                selection = Gui.Selection.getSelection()[0]
                # object has a Placement property
                if hasattr(selection,'Placement') and selection.getTypeIdOfProperty('Placement')=='App::PropertyPlacement':
                    # we don't want to mess with obects that are attached with the Attacher (MapMode)
                    if hasattr(selection,'MapMode') and not Asm4.isAsm4EE(selection):
                        # FCC.PrintMessage('Object has MapMode property, you should use that\n')
                        Gui.runCommand('Part_EditAttachment')
                    else:
                        # check that it's in the root assembly
                        parent = selection.getParentGeoFeatureGroup()
                        if parent and parent == Asm4.getAssembly():
                            # is it's a virgin object, give it Asm4 properties
                            if not hasattr(selection,'SolverId'):
                                Asm4.makeAsmProperties(selection)
                            # if it's a valid assembly and part
                            if Asm4.isAsm4EE(selection):
                                # launch the UI in the task panel
                                ui = placePartUI()
                                Gui.Control.showDialog(ui)
                            # else try to convert it
                            else:
                                convert = Asm4.confirmBox("This Part wasn't assembled with this Assembly4 WorkBench, but I can convert it.")
                                if convert:
                                    Asm4.makeAsmProperties( selection, reset=True )
                                    # launch the UI in the task panel
                                    ui = placePartUI()
                                    Gui.Control.showDialog(ui)
                        # the selected object doesn't belong to the root assembly
                        else:
                            Asm4.warningBox('Please select an object in the assembly Model.')
                            return

    

Gui.addCommand("Asm4_placeLink", PlaceLinkCmd())

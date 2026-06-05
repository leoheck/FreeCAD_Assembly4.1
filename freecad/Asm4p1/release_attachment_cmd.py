#!/usr/bin/env python3
# coding: utf-8

# releaseAttachmentCmd.py
#
# LGPL
# Copyright HUBERT Zoltán

import math
import re
import os
from textwrap import dedent

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

from . import asm4_libs as Asm4



class ReleaseAttachment:

    def __init__(self):
        super(ReleaseAttachment, self).__init__()
        self.selectedObj = []


    def GetResources(self):
        return {
            "MenuText": "Release from Attachment",
            "ToolTip": "Release an object from all attachments to any geometry",
            "Pixmap": os.path.join( Asm4.iconPath , "Asm4_releaseAttachment.svg")
        }


    def IsActive(self):
        if len(Asm4.findAssemblies()) >= 1:
            obj = Asm4.SELECTED_INSTANCE
            if not obj:
                if Gui.Selection.getSelection():
                    obj = Gui.Selection.getSelection()[0]
            if obj and Asm4.isAsm4EE(obj) and Asm4.isLinkToPart(obj) and obj.AttachedTo:
                return True
        return False


    def checkSelection(self):
        selectedObj = None
        # check that there is an Assembly
        if Asm4.getAssembly() and len(Gui.Selection.getSelection()) == 1:
            # set the (first) selected object as global variable
            selection = Gui.Selection.getSelection()[0]
            if Asm4.isAsm4EE(selection) and selection.SolverId != '':
                selectedObj = selection
        # now we should be safe
        return selectedObj
    

    def Activated(self):

        # check what we have selected
        selectedObj = self.checkSelection()
        if not selectedObj:
            return

        obj_type = selectedObj.TypeId
        obj_label_name = Asm4.formated_label_name(selectedObj)

        confirmed_action = Asm4.confirmBox(
            dedent(f"""
            <p>
            By ignoring placement will release the attachment(s) of {obj_label_name} 
            and switch it to manual positioning while preserving its current placement.
            </p>
            """),
            "Ignore Placement"
        )

        if not confirmed_action:
            return

        # the root Assembly
        target_assembly = Asm4.getAssembly()

        # handle object types differently
        # an App::Link
        if obj_type == 'App::Link':
            # unset the ExpressionEngine for the Placement
            selectedObj.setExpression("Placement", None)
            # reset Asm4 properties
            Asm4.makeAsmProperties(selectedObj, reset=True)
        # a datum object
        else:
            # reset Asm4 properties
            Asm4.makeAsmProperties(selectedObj, reset=True)
            # unset both Placements (who knows what confusion the user has done)
            selectedObj.setExpression("Placement", None)
            selectedObj.setExpression("AttachmentOffset", None)

            # if it's a datum object
            if obj_type == "PartDesign::CoordinateSystem" or obj_type == "PartDesign::Plane" or obj_type == "PartDesign::Line" or obj_type == "PartDesign::Point":
                # unset the MapMode; this actually keeps the MapMode parameters intact, 
                # so it's easy for the user to re-enable it
                selectedObj.MapMode = "Deactivated"

        selectedObj.recompute(True)
        target_assembly.recompute(True)
        App.ActiveDocument.recompute()


Gui.addCommand("Asm4_releaseAttachment", ReleaseAttachment())

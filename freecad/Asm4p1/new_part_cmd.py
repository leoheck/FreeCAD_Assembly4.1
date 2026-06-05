#!/usr/bin/env python3
# coding: utf-8

# LGPL
# Copyright HUBERT Zoltán
#
# new_part_cmd.py

import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

from . import asm4_libs as Asm4
from .asm4_translate import translate


class NewPart:

    def __init__(self, part_name):

        self.part_name = part_name

        if self.part_name == "Part":
            self.part_type = "App::Part"
            self.menutext = "New Part"
            self.tooltip = translate("Commands1", "Create a new Part")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Part.svg")

        elif self.part_name == "Body":
            self.part_type = "PartDesign::Body"
            self.menutext = "New Body"
            self.tooltip = translate("Commands1", "Create a new Body")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Body.svg")

        elif self.part_name == "Group":
            self.part_type = "App::DocumentObjectGroup"
            self.menutext = "New Group"
            self.tooltip = translate("Commands1", "Create a new Group")
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Group.svg")


    def GetResources(self):
        if self.part_name == "Part":
            acell = "A, P"
        elif self.part_name == "Body":
            acell = "A, B"
        elif self.part_name == "Group":
            acell = "A, G"
        return {
            "MenuText": self.menutext,
            "Accel": acell,
            "ToolTip": self.tooltip,
            "Pixmap": self.icon,
        }


    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False


    def Activated(self):
        self._create_obj()
        if self.part_type in Asm4.containerTypes:
            self._create_origin_lcs()
            self._customize_object_origin()
        self._organize_document()
        self.obj.recompute()
        App.ActiveDocument.recompute()


    def _create_obj(self):
        self.obj = App.ActiveDocument.addObject(self.part_type, self.part_name)
        if Asm4.allow_duplicate_labels:
            self.obj.Label = self.part_name


    def _create_origin_lcs(self):
        obj = Asm4.newLCS(self.obj, "PartDesign::CoordinateSystem", "LCS_Origin", [(self.obj.Origin.OriginFeatures[0], "")])
        if Asm4.allow_duplicate_labels:
            obj.Label = "LCS_Origin"
        obj.MapMode = "ObjectXY"
        obj.MapReversed = False
        obj.Visibility = False


    def _customize_object_origin(self):

        for feature in self.obj.Origin.OriginFeatures:
            if feature.Name[1:6] == "_Axis":
                feature.Visibility = False
            if feature.Name[0:8] == "XY_Plane":
                feature.ViewObject.ShapeColor = Asm4.LCS_XY_Plane_Color
            if feature.Name[0:8] == "YZ_Plane":
                feature.ViewObject.ShapeColor = Asm4.LCS_YZ_Plane_Color
            if feature.Name[0:8] == "XZ_Plane":
                feature.ViewObject.ShapeColor = Asm4.LCS_XZ_Plane_Color

        if self.part_type == "PartDesign::Body":
            self.obj.Origin.Visibility = True


    def _organize_document(self):

        # Move the created object to the selected Part/Group container.
        if not Asm4.isAssembly(self.obj):
            destiny_container = None

            # If an App::Part or a Group container is selected, put the created object there.
            selection = Gui.Selection.getSelection()
            if len(selection) == 1:
                obj = selection[0]
                if Asm4.isContainer(obj):
                    destiny_container = obj

            # Otherwise, if it is an Asm4p1 project, try to use an existing Parts group.
            elif len(Asm4.findAssemblies()) >= 1:
                parts_group = App.ActiveDocument.getObject("Parts")
                if parts_group and parts_group.TypeId == "App::DocumentObjectGroup" and self.obj.TypeId != "App::DocumentObjectGroup":
                    destiny_container = parts_group

            if destiny_container:
                destiny_container.addObject(self.obj)


Gui.addCommand("Asm4_newPart", NewPart("Part"))
Gui.addCommand("Asm4_newBody", NewPart("Body"))
Gui.addCommand("Asm4_newGroup", NewPart("Group"))

#!/usr/bin/env python3
# coding: utf-8

# LGPL
# Copyright HUBERT Zoltán
#
# new_assembly_cmd.py

import os
import re

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

from . import asm4_libs as Asm4
from .asm4_translate import translate


class NewAssemblyCmd:

    def GetResources(self):
        return {
            "MenuText": "New Assembly",
            "Accel": "A, A",
            "ToolTip": translate("Commands", "<p>Create a new Assembly container</p>"),
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_Model.svg")
        }


    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False


    def Activated(self):
        self._create_parts_group()
        self._create_assembly_part()
        self._create_origin_lcs()
        self._create_variables_obj()
        self._create_constraints_group()
        self._create_configs_group()
        self._organize_document()
        self.assembly.recompute()
        App.ActiveDocument.recompute()


    def _create_parts_group(self):
        self.group = App.ActiveDocument.getObject("Parts")
        if self.group is None:
            self.group = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Parts")


    def _create_assembly_part(self):
        self.assembly = App.ActiveDocument.addObject("App::Part", "Assembly")
        self.assembly.Type = "Assembly"
        if Asm4.allow_duplicate_labels:
            self.assembly.Label = "Assemby"
        self.assembly.addProperty("App::PropertyString", "AssemblyType", "Assembly")
        self.assembly.AssemblyType = "Part::Link"
        self._customize_assembly_origin()


    def _customize_assembly_origin(self):
        for feature in self.assembly.Origin.OriginFeatures:
            if feature.Name[1:6] == "_Axis":
                feature.Visibility = False
            if feature.Name[0:8] == "XY_Plane":
                feature.ViewObject.ShapeColor = Asm4.LCS_XY_Plane_Color
            if feature.Name[0:8] == "YZ_Plane":
                feature.ViewObject.ShapeColor = Asm4.LCS_YZ_Plane_Color
            if feature.Name[0:8] == "XZ_Plane":
                feature.ViewObject.ShapeColor = Asm4.LCS_XZ_Plane_Color


    def _create_origin_lcs(self):
        obj = Asm4.newLCS(self.assembly, "PartDesign::CoordinateSystem", "LCS_Origin", [(self.assembly.Origin.OriginFeatures[0], "")])
        if Asm4.allow_duplicate_labels:
            obj.Label = "LCS_Origin"
        obj.MapMode = "ObjectXY"
        obj.MapReversed = False
        obj.Visibility = False


    def _create_variables_obj(self):
        obj = Asm4.makeVarContainer()
        self.assembly.addObject(obj)
        if Asm4.allow_duplicate_labels:
            obj.Label = "Variables"


    def _create_constraints_group(self):
        group = self.assembly.newObject("App::DocumentObjectGroup", "Constraints")
        if Asm4.allow_duplicate_labels:
            group.Label = "Constraints"
        group.Visibility = False


    def _create_configs_group(self):
        group = self.assembly.newObject("App::DocumentObjectGroup", "Configurations")
        if Asm4.allow_duplicate_labels:
            group.Label = "Configurations"
        group.Visibility = False


    def _organize_document(self):
        if hasattr(self.group, "TypeId") and self.group.TypeId == "App::DocumentObjectGroup":
            for obj in App.ActiveDocument.Objects:
                if Asm4.isAsm4Part(obj):
                    self.group.addObject(obj)


Gui.addCommand("Asm4_newAssembly", NewAssemblyCmd())

#!/usr/bin/env python3
# coding: utf-8

# LGPL
# Copyright HUBERT Zoltán
#
# new_datum_cmd.py

import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

from . import asm4_libs as Asm4


class NewDatum:

    def __init__(self, obj_name):

        self.obj_name = obj_name

        self.containers = [
            "App::Part",
            "PartDesign::Body",
            "App::DocumentObjectGroup"
        ]

        if self.obj_name == "Point":
            self.obj_type = "PartDesign::Point"
            self.menutext = "New Point"
            self.tooltip = "Create a new Datum Point"
            self.accel = "N, T"
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Point.svg")
            self.obj_color = (0.00, 0.00, 0.00)
            self.obj_alpha = []

        elif self.obj_name == "Axis":
            self.obj_type = "PartDesign::Line"
            self.menutext = "New Axis"
            self.tooltip = "Create a new Datum Axis"
            self.accel = "N, A"
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Axis.svg")
            self.obj_color = (0.00, 0.00, 0.50)
            self.obj_alpha = []

        elif self.obj_name == "Plane":
            self.obj_type = "PartDesign::Plane"
            self.menutext = "New Plane"
            self.tooltip = "Create a new Datum Plane"
            self.accel = "N, P"
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Plane.svg")
            self.obj_color = (0.50, 0.50, 0.50)
            self.obj_alpha = 80

        elif self.obj_name == "LCS":
            self.obj_type = "PartDesign::CoordinateSystem"
            self.menutext = "New Coordinate System"
            self.tooltip = "Create a new Coordinate System"
            self.accel = "N, X"
            self.icon = os.path.join(Asm4.iconPath, "Asm4_CoordinateSystem.svg")
            self.obj_color = []
            self.obj_alpha = []

        elif self.obj_name == "Sketch":
            self.obj_type = "Sketcher::SketchObject"
            self.menutext = "New Sketch"
            self.tooltip = "Create a new Sketch"
            self.accel = "N, S"
            self.icon = os.path.join(Asm4.iconPath, "Asm4_Sketch.svg")
            self.obj_color = []
            self.obj_alpha = []


    def GetResources(self):
        return {
            "MenuText": self.menutext,
            "Accel": self.accel,
            "ToolTip": self.tooltip,
            "Pixmap": self.icon
        }


    def IsActive(self):
        if App.ActiveDocument:
            if self._get_selected_object():
                return True
        return False


    def Activated(self):

        selected_obj = self._get_selected_object()

        parent_container = None
        if selected_obj.TypeId in self.containers:
            parent_container = selected_obj

        # if a datum object is selected
        elif selected_obj.TypeId in Asm4.datumTypes or selected_obj.TypeId == "Sketcher::SketchObject":
            parent = selected_obj.getParentGeoFeatureGroup()
            if parent.TypeId in self.containers:
                parent_container = parent

        elif Asm4.getTargetAssembly():
            parent_container = Asm4.getTargetAssembly()

        else:
            Asm4.warningBox(f"Can't create a {self.obj_type} with the current selections.")


        if parent_container:

            obj = App.ActiveDocument.addObject(self.obj_type, self.obj_name)
            if Asm4.allow_duplicate_labels:
                obj.Label = self.obj_name

            parent_container.addObject(obj)

            # automatic resizing of datum Plane sucks, so we set it to manual
            if self.obj_type == "PartDesign::Plane":
                obj.ResizeMode = "Manual"
                obj.Length = 100
                obj.Width = 100

            elif self.obj_type == "PartDesign::Line":
                obj.ResizeMode = "Manual"
                obj.Length = 200

            if self.obj_color:
                Gui.ActiveDocument.getObject(obj.Name).ShapeColor = self.obj_color

            if self.obj_alpha:
                Gui.ActiveDocument.getObject(obj.Name).Transparency = self.obj_alpha

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(App.ActiveDocument.Name, parent_container.Name, obj.Name + '.')

            Gui.runCommand("Part_EditAttachment")


    def _get_selected_object(self):

        selection = Gui.Selection.getSelection()

        if selection:
            obj = selection[0]

            if obj.TypeId in Asm4.containerTypes or obj.TypeId in Asm4.datumTypes or obj.TypeId == "Sketcher::SketchObject":
                return obj

            # When the selected item is a feature of a Body, it returns the Body itself.
            elif obj.getParentGeoFeatureGroup().TypeId in Asm4.containerTypes:
                return obj.getParentGeoFeatureGroup()

        assembly = Asm4.getTargetAssembly()
        if assembly is not None:
            return assembly

        return None



class NewHole:

    def GetResources(self):
        return {
            "MenuText": "New Circle Axis",
            "ToolTip": "Create a Datum Axis attached to a circle",
            "Accel": "N, H",
            "Pixmap": os.path.join(Asm4.iconPath , "Asm4_Hole.svg")
        }


    def IsActive(self):
        if self._get_circular_edges_selected() is None:
            return False
        else:
            return True


    def Activated(self):

        (obj, edges) = self._get_circular_edges_selected()

        for i in range(len(edges)):
            edge_obj = edges[i][0]
            edge_name = edges[i][1]
            parent_container = obj.getParentGeoFeatureGroup()

            # we can create a datum only in a container
            if parent_container:

                parent_container_doc = parent_container.Document

                # if the solid having the edge is indeed in an App::Part
                if parent_container and (parent_container.TypeId == "App::Part" or parent_container.TypeId == "PartDesign::Body"):

                    axis = Asm4.newLCS(parent_container, "PartDesign::Line", "CircleAxis", [(obj, (edge_name,))])
                    if Asm4.allow_duplicate_labels:
                        axis.Label = "CircleAxis"

                    axis.MapMode = "AxisOfCurvature"
                    axis.MapReversed = False
                    axis.ResizeMode = "Manual"
                    axis.Length = 2 * edge_obj.BoundBox.DiagonalLength
                    axis.ViewObject.ShapeColor = (0.0, 0.0, 1.0)
                    axis.ViewObject.Transparency = 50

                    axis.recompute()
                    parent_container.recompute()
            else:
                FCC.PrintMessage("Datum objects can only be created inside a Part or Body.")


    def _get_circular_edges_selected(self):

        selection = None
        parent = None
        edges = []

        # 1 selection means a single parent
        if App.ActiveDocument and len(Gui.Selection.getSelection()) == 1:
            parent = Gui.Selection.getSelection()[0]

            # parse all sub-elemets of the selection
            for i in range(len(Gui.Selection.getSelectionEx()[0].SubObjects)):
                edge_obj  = Gui.Selection.getSelectionEx()[0].SubObjects[i]
                edge_name = Gui.Selection.getSelectionEx()[0].SubElementNames[i]

                # if the edge is circular
                if Asm4.isCircle(edge_obj):
                    edges.append([edge_obj, edge_name])

        # if we found circular edges
        if len(edges) > 0:
            selection = (parent, edges)

        return selection



Gui.addCommand("Asm4_newSketch", NewDatum("Sketch"))
Gui.addCommand("Asm4_newLCS",    NewDatum("LCS"))
Gui.addCommand("Asm4_newAxis",   NewDatum("Axis"))
Gui.addCommand("Asm4_newPlane",  NewDatum("Plane"))
Gui.addCommand("Asm4_newPoint",  NewDatum("Point"))
Gui.addCommand("Asm4_newHole",   NewHole())

# Defines dropdown button Datum objects
createDatumList = [
    "Asm4_newLCS",
    "Asm4_newPlane",
    "Asm4_newAxis",
    "Asm4_newPoint",
    "Asm4_newHole"
]

Gui.addCommand("Asm4_createDatum", Asm4.DropDownCmd(createDatumList, "Create Datum Object"))

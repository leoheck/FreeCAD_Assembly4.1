#!/usr/bin/env python3
# coding: utf-8
 
# update_assembly_cmd.py 


import math
import re
import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

from . import asm4_libs as Asm4



class UpdateAssembly:

    def GetResources(self):
        return {
            "MenuText": "Solve and Update Assembly",
            "ToolTip": "Update Assembly",
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_Solver.svg")
        }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        return(False)


    def Activated(self):
        for obj in App.ActiveDocument.Objects:
            if obj.TypeId in Asm4.containerTypes:
                obj.recompute(True)



Gui.addCommand("Asm4_updateAssembly", UpdateAssembly())

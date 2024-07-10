#!/usr/bin/env python3
# coding: utf-8
# 
# updateAssembly.py 


import math, re, os
import Asm4_locator

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part
from Asm4_Translate import _atr, QT_TRANSLATE_NOOP, translate

import Asm4_libs as Asm4
global Asm4_icon, Asm4_path, Asm4_trans

Asm4_path = os.path.dirname( Asm4_locator.__file__ )
Asm4_trans = os.path.join(Asm4_path, "Resources/translations")
Gui.addLanguagePath(Asm4_trans)
Gui.updateLocale()

class updateAssembly:

    def GetResources(self):
        return {"MenuText": translate("Asm4_updateAssembly", "Solve and Update Assembly"),
                "ToolTip": translate("Asm4_updateAssembly", "Update Assembly"),
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Solver.svg')
                }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        return(False)


    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # find every Part in the document ...
        for obj in App.ActiveDocument.Objects:
            # ... and update it
            if obj.TypeId == 'App::Part':
                obj.recompute(True)
        #App.ActiveDocument.recompute()


# add the command to the workbench
Gui.addCommand( 'Asm4_updateAssembly', updateAssembly() )

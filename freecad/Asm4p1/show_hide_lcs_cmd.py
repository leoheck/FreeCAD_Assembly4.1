#!/usr/bin/env python3
# coding: utf-8

# show_hide_lcs_cmd.py

import os

import FreeCADGui as Gui
import FreeCAD as App

from . import asm4_libs as Asm4
from .asm4_translate import translate



def _show_all_nested_lcs(show=True):

    processed_links = []

    selection = Gui.Selection.getSelection()

    if selection:
        for sel in Gui.Selection.getSelection():
            if sel.isDerivedFrom('App::Link'):
                _show_child_lcs(sel, show, processed_links)
            elif sel.TypeId in Asm4.containerTypes:
                for obj in sel.getSubObjects(1):
                    _show_child_lcs(sel.getSubObject(obj, 1), show, processed_links)

    # if not, apply it to all assemblies
    elif Asm4.findAssemblies():
        for asm in Asm4.findAssemblies():
            for obj in asm.getSubObjects(1):
                _show_child_lcs(asm.getSubObject(obj, 1), show, processed_links)


def _show_child_lcs(obj, show, processed_links):

    if obj.TypeId in Asm4.datumTypes:
        obj.Visibility = show

    elif obj.TypeId == "App::Link" and obj.Name not in processed_links:
        processed_links.append(obj.Name)
        for sub_obj_name in obj.LinkedObject.getSubObjects(1):
            linked_obj = obj.LinkedObject.Document.getObject(sub_obj_name[0:-1])
            _show_child_lcs(linked_obj, show, processed_links)

    # if it's a container or a group
    elif obj.TypeId in Asm4.containerTypes or obj.TypeId == "App::DocumentObjectGroup":
        for sub_obj_name in obj.getSubObjects(1):
            sub_obj = obj.getSubObject(sub_obj_name, 1)
            if sub_obj is not None:
                _show_child_lcs(sub_obj, show, processed_links)



class ShowLCSCmd:

    def __init__(self):
        super(ShowLCSCmd, self).__init__()

    def GetResources(self):
        return {
            "MenuText": translate("Asm4_showLcs", "Show LCS"),
            "Accel": "A, S",
            "ToolTip": translate("Asm4_showLcs", "Show LCS and Datums of selected part and its children"),
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_showLCS.svg")
        }

    def IsActive(self):
        if Gui.Selection.hasSelection() or Asm4.findAssemblies():
            return True
        return False

    def Activated(self):
        _show_all_nested_lcs(show=True)



class HideLCSCmd:
    def __init__(self):
        super(HideLCSCmd, self).__init__()

    def GetResources(self):
        return {
            "MenuText": translate("Asm4_hideLcs", "Hide LCS"),
            "Accel": "A, H",
            "ToolTip": translate("Asm4_hideLcs", "Hide LCS and Datums of selected part and its children"),
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_hideLCS.svg")
        }

    def IsActive(self):
        if Gui.Selection.hasSelection() or Asm4.findAssemblies():
            return True
        return False

    def Activated(self):
        _show_all_nested_lcs(show=False)



Gui.addCommand("Asm4_showLcs", ShowLCSCmd())
Gui.addCommand("Asm4_hideLcs", HideLCSCmd())

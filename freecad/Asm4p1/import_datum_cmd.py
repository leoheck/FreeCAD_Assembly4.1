#!/usr/bin/env python3
# coding: utf-8

# LGPL
# Copyright HUBERT Zoltán
#
# import_datum_cmd.py


import os
from textwrap import dedent

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

from . import asm4_libs as Asm4



class ImportDatumCmd():

    def __init__(self):
        super(ImportDatumCmd, self).__init__()


    def GetResources(self):

        tooltip = dedent(
            f"""
            Imports the selected Datum object(s) from a sub-part into the root assembly.
            This creates a new datum of the same type with the same global placement.

            This command can also be used to override the placement of an existing datum:
            select a second datum in the same root container as the first selected datum
            to use is as the target
            """
        )

        return {
            "MenuText": "Import Datum object",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(Asm4.iconPath , "Import_Datum.svg")
        }


    def IsActive(self):
        if App.ActiveDocument and self._get_selected_datums():
            return True
        else:
            return False


    def Activated(self):

        (datum, selection_tree) = Asm4.getSelectionTree()

        if selection_tree:
            # the root parent container is the first in the selection tree
            rootContainer = App.ActiveDocument.getObject(selection_tree[0])
            selection = self._get_selected_datums()

            # special case where 2 objects are selected in order to update the placement of the second one
            if len(selection)==2 and selection[0].getParentGeoFeatureGroup() == rootContainer:
                confirm = False
                datum = selection[0]
                ( targetDatum, selection_tree ) = Asm4.getSelectionTree(1)

                # target datum is free
                if datum.MapMode == 'Deactivated':
                    message = 'This will superimpose '+Asm4.labelName(datum)+' in '+Asm4.labelName(rootContainer)+' on:\n\n'
                    for objName in selection_tree[1:-1]:
                        message += '> '+objName+'\n'
                    message += '> '+Asm4.labelName(datum)
                    Asm4.warningBox(message)
                    confirm = True

                # selected datum is attached
                else:
                    message = Asm4.labelName(datum)+' in '+Asm4.labelName(rootContainer)+' is already attached to some geometry. '
                    message += 'This will superimpose its Placement on:\n\n'
                    for objName in selection_tree[1:-1]:
                        message += '> '+objName+'\n'
                    message += '> '+Asm4.labelName(datum)
                    confirm = Asm4.confirmBox(message)

                if confirm:
                    self._setup_target_datum(datum, self._build_datum_expression(selection_tree))
                    # hide initial datum
                    targetDatum.Visibility = False
                    # select the newly created datum
                    Gui.Selection.clearSelection()
                    Gui.Selection.addSelection( App.ActiveDocument.Name, rootContainer.Name, datum.Name+'.' )
                    # recompute assembly
                    rootContainer.recompute(True)
                # Done with the special case, no need to continue with the normal process
                return

            # the selected datum is not deep enough
            if len(selection_tree)<3:
                message = datum.Name + ' is already at the top-level and cannot be imported'
                Asm4.warningBox(message)
                return

        # Single or Multiple selection(s) for regular case
        # Notify user that default names will be used and import all the objects
        proposed_name = f"{selection_tree[-2]}_{datum.Label}"

        if len(selection) == 1:
            message = 'Create a new '+datum.TypeId+' in '+Asm4.labelName(rootContainer)+' \nsuperimposed on:\n\n'
            for objName in selection_tree[1:]:
                message += '> '+objName+'\n'
            message += '\nEnter name for this datum :'+' '*40
            userSpecifiedName,confirm = QtGui.QInputDialog.getText(None,'Import Datum',
                    message, text = proposed_name)
        else:
            message = str(len(selection)) + " selected datum objects will be imported into the root assembly\n"
            message += "with their default names such as:\n"
            message += proposed_name
            confirm = Asm4.confirmBox(message)

        if confirm:
            for index in range(len(selection)):
                ( datum, selection_tree ) = Asm4.getSelectionTree(index)
                # create a new datum object
                if len(selection) == 1:
                    proposed_name = userSpecifiedName
                else:
                    proposed_name = selection_tree[-2]+'_'+datum.Label

                targetDatum = rootContainer.newObject(datum.TypeId, proposed_name)
                targetDatum.Label = proposed_name
                # apply existing view properties if applicable
                if hasattr(datum,'ResizeMode') and datum.ResizeMode == 'Manual':
                    targetDatum.ResizeMode = 'Manual'
                    if hasattr(datum,'Length'):
                        targetDatum.Length = datum.Length
                    if hasattr(datum,'Width'):
                        targetDatum.Width = datum.Width
                targetDatum.ViewObject.ShapeColor   = datum.ViewObject.ShapeColor
                targetDatum.ViewObject.Transparency = datum.ViewObject.Transparency

                self._setup_target_datum(targetDatum, self._build_datum_expression(selection_tree))

                # hide initial datum
                datum.Visibility = False

            # select the last created datum
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection( App.ActiveDocument.Name, rootContainer.Name, targetDatum.Name+'.' )

        # recompute assembly
        rootContainer.recompute(True)


    def _get_selected_datums(self):
        selection = Gui.Selection.getSelection()
        for obj in selection:
            if obj.TypeId not in Asm4.datumTypes:
                return None
        return selection


    def _setup_target_datum(self, target_datum, expr):

        target_datum.MapMode = "Deactivated"

        if hasattr(target_datum, "AttachmentSupport"):
            target_datum.AttachmentSupport = None
        else:
            target_datum.Support = None

        # Set Asm4 properties
        Asm4.makeAsmProperties(target_datum, reset=True)
        target_datum.AttachedBy = "Origin"
        target_datum.SolverId = "Asm4EE"

        # set the Placement's ExpressionEngine
        target_datum.setExpression("Placement", expr)
        target_datum.Visibility = True

        target_datum.recompute()


    def _build_datum_expression(self, selection_tree):
        # Build the Placement expression
        # The 1st object [0] is at the document root and its Placement is ignored
        # The 2nd object [1] gets a special treatment, it is always in the current document

        idx = 1
        obj = App.ActiveDocument.getObject(selection_tree[idx])
        while not hasattr(obj, "Placement"):
            idx += 1
            obj = App.ActiveDocument.getObject(selection_tree[idx])
        expr = f"{selection_tree[idx]}.Placement"

        # the document where an object is
        if obj.isDerivedFrom("App::Link") and obj.LinkedObject.Document != App.ActiveDocument:
            doc = obj.LinkedObject.Document
        else:
            doc = App.ActiveDocument

        for obj_name in selection_tree[idx + 1:]:
            obj = doc.getObject(obj_name)

            if hasattr(obj, "Placement"):
                if doc == App.ActiveDocument:
                    expr += f" * {obj_name}.Placement"
                else:
                    expr += f" * {doc.Name}#{obj_name}.Placement"

            # check whether *this* object is a link to an *external* doc
            if obj.isDerivedFrom("App::Link") and obj.LinkedObject.Document != App.ActiveDocument:
                doc = obj.LinkedObject.Document

        return expr



Gui.addCommand("Asm4_importDatum", ImportDatumCmd())

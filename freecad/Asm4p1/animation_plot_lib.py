#!/usr/bin/env python3
# coding: utf-8

# animation_plot_lib.py


import os
from textwrap import dedent


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

from . import asm4_libs as Asm4
from .animation_lib import AnimationProvider



class AnimationPlotter():

    def __init__(self, animation_provider: AnimationProvider):
        self.animation_provider = animation_provider
        self.num_of_points = 0
        self.num_of_steps = 0
        super(AnimationPlotter, self).__init__()
        self.UI = QtGui.QDialog()


    def openUI(self):
        # get the current active document to avoid errors if user changes tab
        self.active_document = App.ActiveDocument
        self.var_name = '?'
        self.var_value = None
        # for the compatibility with the old Model
        try :
            self.model = self.active_document.Model
        except:
            try:
                self.model = self.active_document.Assembly
            except:
                print("Unrecognized assembly type, this might not work")
        # get the Variables holder
        try :
            self.Variables = self.model.getObject('Variables')
            # the animated variable
            self.var_name = str(self.animation_provider.varList.currentText())
            self.var_value = self.Variables.getPropertyByName(self.var_name)
        except :
            print("This Model deosn't seem to have compatible Variables")
            return

        # show initially the UI
        self.drawUI()
        self.UI.show()

        self.csv_field.clear()
        csv_text = f'# Running animation sequence of {self.var_name}, please wait...\n'
        self.csv_field.setPlainText(csv_text)
        Gui.updateGui()

        # Datum points to be plotted
        self.plotPoints = self._getPoints()
        # Title of the CSV document
        title = '# CVS output'
        header1 = f"Iter;Variable;"
        header2 = f"#;{self.var_name};"

        for i in range(self.num_of_points):
            pt = self.plotPoints[i]
            header1 += pt.Name + ';;;'
            header2 += ' X ; Y ; Z ;'

        self.csv_field.setPlainText(title)
        self.csv_field.appendPlainText(header1)
        self.csv_field.appendPlainText(header2)

        # Calculate all the trajectories
        trajectories = self.grabFrames(self.plotPoints, True)
        self.csv_field.appendPlainText(f"Finished {self.num_of_steps} iterations.")


    # store the intermediate points
    def grabFrames(self, points=[], printCSV=False):

        # create empty lists for each points
        trajectories = []
        for i in range(len(points)+1):
            trajectories.append([])
        first_frame = True
        end_of_cycle = False
        num_of_frame = 0

        # run the animation sequence
        while not end_of_cycle:
            end_of_cycle = self.animation_provider.nextFrame(first_frame)
            first_frame = False
            num_of_frame += 1;
            Gui.updateGui()

            # current variable value
            var_value = self.Variables.getPropertyByName(self.var_name)
            trajectories[0].append(var_value)
            csv_text = str(num_of_frame)+';'+str(var_value)+';'

            for i in range(len(points)):
                pt = points[i]
                pla = pt.Placement
                pos = pla.Base
                trajectories[i+1].append(pla)
                csv_text += str(pos.x) +';'+ str(pos.y) +';'+ str(pos.z) +';'

            if printCSV:
                self.csv_field.appendPlainText(csv_text)

        # Summary
        self.num_of_steps = len(trajectories[0])
        return trajectories


    # gather a table of all visible Datum Points
    def _getPoints(self):
        pts = []
        for obj_name in self.model.getSubObjects():
            obj = self.model.getObject(obj_name[:-1])
            # we only consider Datum Points that are *visible*
            if obj.TypeId == "PartDesign::Point" and obj.Visibility:
                pts.append(obj)
        self.num_of_points = len(pts)
        return pts


    def _on_cancel_button(self):
        self.animation_provider.onStop()
        #document = App.ActiveDocument
        #Gui.Selection.addSelection(document.Name,'BOM')
        self.UI.close()

    def _on_ok_button(self):
        self.animation_provider.onStop()
        #document = App.ActiveDocument
        #Gui.Selection.addSelection(document.Name,'BOM')
        self.UI.close()


    def close(self):
        self.animation_provider.onStop()
        self.UI.close()


    def onRefresh(self):
        self.animation_provider.onStop()
        self.csv_field.clear()
        self.csv_field.setPlainText('# CVS output \n')
        trajectories = self.grabFrames(self.plotPoints)
        self.csv_field.setPlainText("All trajectories calculated")


    def drawUI(self):

        self.UI.setWindowTitle("Plot trajectories of the animation")
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath, 'FreeCad.svg' )))
        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.UI.setMinimumWidth(650)
        # self.UI.resize(800,600)

        # set main window widgets layout
        self.main_layout = QtGui.QVBoxLayout(self.UI)

        # Help and Log
        self.description_label = QtGui.QLabel()
        text = dedent("""
            This tool plots the values of all the variables
            and X,Y,Z coordinates of each visible Datum Point
            for each step of the animation sequence.
        """).strip()

        self.description_label.setText(text)
        self.description_label.setWordWrap(True)
        self.main_layout.addWidget(self.description_label)

        # The CSV file is a plain text field
        self.csv_field = QtGui.QPlainTextEdit()
        self.csv_field.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.main_layout.addWidget(self.csv_field)

        self.button_layout = QtGui.QHBoxLayout()

        # Cancel button
        self.cancel_button = QtGui.QPushButton("Cancel")
        self.cancel_button.setToolTip("Remove trajectories and Exit.")
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()

        # Refresh button
        self.RefreshButton = QtGui.QPushButton("Refresh")
        self.RefreshButton.setToolTip("Recalculate animation sequence.")
        self.button_layout.addWidget(self.RefreshButton)
        #self.button_layout.addStretch()

        # Export button
        self.ExportButton = QtGui.QPushButton("Export")
        self.ExportButton.setToolTip("Save data as .csv file.")
        self.button_layout.addWidget(self.ExportButton)
        self.button_layout.addStretch()

        # OK button
        self.ok_button = QtGui.QPushButton("OK")
        self.ok_button.setToolTip("Leave ploter keeping plots.")
        self.ok_button.setDefault(True)
        self.button_layout.addWidget(self.ok_button)
        self.main_layout.addLayout(self.button_layout)

        self.UI.setLayout(self.main_layout)

        # Actions
        self.ok_button.clicked.connect(self._on_ok_button)
        self.cancel_button.clicked.connect(self._on_cancel_button)

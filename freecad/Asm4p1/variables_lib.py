#!/usr/bin/env python3
# coding: utf-8

# LGPL
# Copyright HUBERT Zoltán
#
# variables_lib.py


import os
import re
from textwrap import dedent

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

from . import asm4_libs as Asm4



light_theme_normal_text_color = f"rgb(0, 0, 0)"
light_theme_bad_text_color    = f"rgb(215, 0, 21)"
dark_theme_normal_text_color  = f"rgb(255, 255, 255)"
dark_theme_bad_text_color     = f"rgb(255, 105, 97)"


def _check_part():
    retval = None
    # if an App::Part is selected
    if Gui.Selection.getSelection():
        selectedObj = Gui.Selection.getSelection()[0]
        if selectedObj.TypeId == "App::Part":
            retval = selectedObj
    return retval


def _is_dark_mode() -> bool:
    pg = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    if re.search("dark", pg.GetString("StyleSheet"), re.IGNORECASE):
        return True
    else:
        return False


def _normal_text_color():
    return dark_theme_normal_text_color if _is_dark_mode() else light_theme_normal_text_color

def _bad_text_color():
    return dark_theme_bad_text_color if _is_dark_mode() else light_theme_bad_text_color


# @trace_class
class AddVariable():

    def __init__(self):
        super(AddVariable, self).__init__()
        self.UI = QtGui.QDialog()
        self._draw_UI()

        self.allowedProperties = [
            "App::PropertyBool",
            "App::PropertyBoolList",
            "App::PropertyColor",
            "App::PropertyEnumeration",
            "App::PropertyFile",
            "App::PropertyFloat",
            "App::PropertyFloatList",
            "App::PropertyInteger",
            "App::PropertyIntegerList",
            "App::PropertyMatrix",
            "App::PropertyPlacement",
            "App::PropertyString",
            "App::PropertyVector",
            "App::PropertyXLink",
            #"App::PropertyLink",
        ]


    def GetResources(self):

        tooltip = dedent(f"""
            <p>
            Adds a variable into the Variables object in the target Assembly.
            </p>
        """).strip()

        return {
            "MenuText": "Add Variable",
            "ToolTip": tooltip,
            "Accel": "V, A",
            "Pixmap": os.path.join(Asm4.iconPath , "Asm4_addVariable.svg")
        }


    def IsActive(self):
        if App.ActiveDocument and Asm4.getTargetAssembly():
            return True
        return False


    def Activated(self):

        self.target_asm = Asm4.getTargetAssembly()
        if self.target_asm is None:
            return

        self.target_var = [obj for obj in self.target_asm.Group if obj.Name.startswith("Variables")][0]
        self._fill_assembly_combo()

        if not self.target_var: # create it
            self.target_var = Asm4.makeVarContainer()
            part = None
            # if an App::Part is selected:
            if _check_part():
                part = _check_part()
            # if an Asm4 Model is present:
            elif Asm4.getAssembly():
                part = Asm4.getAssembly()
            if part:
                part.addObject(self.target_var)

        self._reset_UI()
        self._fill_variable_types_combo()

        self.UI.show()


    def _reset_UI(self):
        self.var_name_field.clear()
        self.var_name_field.setFocus()
        self.var_value_field.setValue(1.0)
        self.var_info_field.clear()


    def _fill_variable_types_combo(self):
        for prop in self.target_var.supportedProperties():
            if prop in self.allowedProperties:
                self.var_types_combo.addItem(prop.removeprefix("App::Property"), prop)

        self.var_types_combo.setCurrentIndex(0)
        property_type = self.var_types_combo.findText("Float")
        if property_type >= 0:
            self.var_types_combo.setCurrentIndex(property_type)


    def _on_create_button(self):
        var_name = self.var_name_field.text()
        var_type = self.var_types_combo.currentData()
        var_value = self.var_value_field.value()
        if var_name and var_value:
            var_group = self.var_group_combo.currentText()
            self.target_var.addProperty(var_type, var_name, var_group, self.var_info_field.toPlainText())
            setattr(self.target_var, var_name, var_value)
            self.target_var.recompute(True)
            self.target_asm.recompute(True)
            Gui.Selection.addSelection(self.target_var)
            self._reset_UI()


    def _on_cancel_button(self):
        self.UI.close()


    # Verify and handle bad and duplicated names
    def _on_name_edited(self):
        var_name = self.var_name_field.text()
        pattern = re.compile("^[A-Za-z][_A-Za-z0-9]*$")

        if pattern.match(self.var_name_field.text()) and var_name not in self.target_var.PropertiesList:
            try:
                App.Units.parseQuantity(self.var_name)
            except:
                self.var_name_field.setStyleSheet(f"color: {_normal_text_color()};")
                self.create_button.setEnabled(True)
            else:
                self.var_name_field.setStyleSheet(f"color:{_bad_text_color()};")
                self.create_button.setEnabled(False)
        else:
                self.var_name_field.setStyleSheet(f"color:{_bad_text_color()};")
                self.create_button.setEnabled(False)


    def _draw_UI(self):

        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setWindowTitle("Add Variable")
        self.UI.setMinimumWidth(450)
        self.UI.setModal(False)

        self.main_layout = QtGui.QVBoxLayout(self.UI)
        self.form_layout = QtGui.QFormLayout()

        self.assemblies_combo = QtGui.QComboBox()
        self.form_layout.addRow(QtGui.QLabel("Assembly"), self.assemblies_combo)

        # Variable Name
        self.var_name_field = QtGui.QLineEdit()
        self.form_layout.addRow(QtGui.QLabel("Name"), self.var_name_field)

        # Variable Type
        self.var_types_combo = QtGui.QComboBox()
        self.form_layout.addRow(QtGui.QLabel("Type"), self.var_types_combo)

        # Variable group
        self.var_group_combo = QtGui.QComboBox()
        self.form_layout.addRow(QtGui.QLabel("Group"), self.var_group_combo)
        self.var_group_combo.addItem("Constants")
        self.var_group_combo.addItem("Variables")
        self.var_group_combo.setItemData(0, "Constants are not shown when creating Animation", QtCore.Qt.ToolTipRole)
        self.var_group_combo.setItemData(1, "Variables that will be used in Animation", QtCore.Qt.ToolTipRole)
        self.var_group_combo.setCurrentIndex(1)

        # Variable Value
        self.var_value_field = QtGui.QDoubleSpinBox()
        self.var_value_field.setRange(-1000000.0, 1000000.0)
        self.var_value_field.setDecimals(6)
        self.form_layout.addRow(QtGui.QLabel("Value"), self.var_value_field)

        # Documentation
        self.var_info_field = QtGui.QTextEdit()
        self.form_layout.addRow(QtGui.QLabel("Description"), self.var_info_field)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addStretch()

        # Buttons
        self.button_layout = QtGui.QHBoxLayout()
        self.cancel_button = QtGui.QPushButton("&Done")
        self.create_button = QtGui.QPushButton("&Create")
        self.create_button.setDefault(True)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.create_button)

        self.main_layout.addLayout(self.button_layout)
        # self.UI.setLayout(self.main_layout)

        # Actions
        self.cancel_button.clicked.connect(self._on_cancel_button)
        self.create_button.clicked.connect(self._on_create_button)
        self.var_name_field.textEdited.connect(self._on_name_edited)

        self.assemblies_combo.currentIndexChanged.connect(self._on_assembly_selected)
        self.assemblies_combo.activated.connect(self._on_assembly_selected)


    def _on_assembly_selected(self):
        self.target_asm = self.assemblies_combo.currentData()
        if self.target_asm is None:
            return

        self.target_var = [obj for obj in self.target_asm.Group if obj.Name.startswith("Variables")][0]
        Gui.Selection.addSelection(self.target_var)


    def _fill_assembly_combo(self):

        asms = Asm4.findAssemblies()
        if asms is None:
            return False

        self.assemblies_combo.clear()

        for obj in asms:
            self.assemblies_combo.addItem(
                QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Model.svg")),
                Asm4.formated_label_name(obj),
                obj
            )

        if len(asms) == 1:
            self.assemblies_combo.setEnabled(False)

        self.target_asm = Asm4.getTargetAssembly()

        self.assemblies_combo.setCurrentIndex(0)
        if self.target_asm:
            search_text = Asm4.formated_label_name(self.target_asm)
            index = self.assemblies_combo.findText(search_text)
            if index != -1:
                self.assemblies_combo.setCurrentIndex(index)


# @trace_class
class DelVariable():

    def __init__(self):
        super(DelVariable, self).__init__()
        self.UI = QtGui.QDialog()
        self._draw_UI()


    def GetResources(self):
        return {
            "MenuText": "Delete Variable",
            "ToolTip": "Delete a Variable",
            "Accel": "V, D",
            "Pixmap": os.path.join(Asm4.iconPath , "Asm4_delVariable.svg")
        }


    def IsActive(self):
        if Asm4.findAssemblies():
            return True
        return False


    def Activated(self):

        self.target_asm = Asm4.getTargetAssembly()
        if self.target_asm is None:
            return

        self.target_var = [obj for obj in self.target_asm.Group if obj.Name.startswith("Variables")][0]
        if not self.target_var:
            return

        self.UI.show()
        self._fill_assembly_combo()


    def _on_select_variable(self):

        prop = self.vars_combo.currentText()
        if prop in self.target_var.PropertiesList:

            var_value = self.target_var.getPropertyByName(prop)
            var_group = self.target_var.getGroupOfProperty(prop)

            self.var_value_field.setText(str(var_value))
            self.var_group_field.setText(var_group)

            try:
                self.var_info_field.setPlainText(self.target_var.getDocumentationOfProperty(prop))
                self.var_info_label.show()
                self.var_info_field.show()
            except:
                self.var_info_label.hide()
                self.var_info_field.hide()

        return


    def _on_delete_button(self):
        prop = self.vars_combo.currentText()
        if prop in self.target_var.PropertiesList:
            self.target_var.removeProperty(prop)
        self._update_variables_combo()


    def _on_cancel_button(self):
        self.UI.close()


    def _draw_UI(self):

        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setWindowTitle("Delete Variable")
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath, "FreeCad.svg")))
        self.UI.setMinimumWidth(400)
        self.UI.setModal(False)

        self.main_layout = QtGui.QVBoxLayout(self.UI)
        self.form_layout = QtGui.QFormLayout()

        # Existing Assemblies
        self.assemblies_combo = QtGui.QComboBox()
        self.form_layout.addRow(QtGui.QLabel("Assembly"), self.assemblies_combo)

        # Existing Variables
        self.vars_combo = QtGui.QComboBox()
        self.form_layout.addRow(QtGui.QLabel("Variable"), self.vars_combo)

        # Variable Value
        self.var_value_field = QtGui.QLineEdit()
        self.form_layout.addRow(QtGui.QLabel("Value"), self.var_value_field)
        self.var_value_field.setEnabled(False)

        # Variable Group
        self.var_group_field = QtGui.QLineEdit()
        self.form_layout.addRow(QtGui.QLabel("Group"), self.var_group_field)
        self.var_group_field.setEnabled(False)

        # Variable Info
        self.var_info_field = QtGui.QTextEdit()
        self.var_info_label = QtGui.QLabel("Description")
        self.form_layout.addRow(self.var_info_label, self.var_info_field)
        self.var_info_field.setEnabled(False)
        self.var_info_label.hide()
        self.var_info_field.hide()

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addStretch()

        # Buttons
        self.button_layout = QtGui.QHBoxLayout()
        self.cancel_button = QtGui.QPushButton("&Done")
        self.delete_button = QtGui.QPushButton("&Delete")

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.delete_button)

        self.main_layout.addLayout(self.button_layout)
        # self.UI.setLayout(self.main_layout)

        # Actions
        self.vars_combo.currentIndexChanged.connect(self._on_select_variable)
        self.cancel_button.clicked.connect(self._on_cancel_button)
        self.delete_button.clicked.connect(self._on_delete_button)

        self.assemblies_combo.currentIndexChanged.connect(self._on_assembly_selected)
        self.assemblies_combo.activated.connect(self._on_assembly_selected)


    def _fill_assembly_combo(self):

        asms = Asm4.findAssemblies()
        if asms is None:
            return

        self.assemblies_combo.clear()

        for obj in asms:
            self.assemblies_combo.addItem(
                QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Model.svg")),
                Asm4.formated_label_name(obj),
                obj
            )

        if len(asms) == 1:
            self.assemblies_combo.setEnabled(False)

        self.target_asm = Asm4.getTargetAssembly()

        self.assemblies_combo.setCurrentIndex(0)
        if self.target_asm:
            search_text = Asm4.formated_label_name(self.target_asm)
            index = self.assemblies_combo.findText(search_text)
            if index != -1:
                self.assemblies_combo.setCurrentIndex(index)

        self._update_variables_combo()


    def _on_assembly_selected(self):
        self.target_asm = self.assemblies_combo.currentData()
        self._update_variables_combo()


    def _update_variables_combo(self):

        self.vars_combo.clear()
        self.var_value_field.clear()
        self.var_group_field.clear()
        self.var_info_field.clear()

        if self.target_asm is None:
            return

        variables_obj = [obj for obj in self.target_asm.Group if obj.Name.startswith("Variables")][0]
        if variables_obj:
            for var in variables_obj.PropertiesList:
                if variables_obj.getGroupOfProperty(var) == "Constants" or variables_obj.getGroupOfProperty(var) == "Variables":
                    self.vars_combo.addItem(var)

        if self.vars_combo.count() > 0:
            self.vars_combo.setCurrentIndex(0)


Gui.addCommand("Asm4_addVariable", AddVariable())
Gui.addCommand("Asm4_delVariable", DelVariable())

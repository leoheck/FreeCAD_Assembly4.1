#!/usr/bin/env python3
# coding: utf-8

# insert_link_cmd.py
#
# LGPL
# Copyright HUBERT Zoltán

import os
import re
from textwrap import dedent

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

from . import asm4_libs as Asm4


class InsertLink(QtGui.QDialog):

    def __init__(self):
        super(InsertLink, self).__init__()

    def GetResources(self):

        tooltip = dedent("""
            <p>
            Insert Part creates an instance of a part (Part or Body)
            in the target assembly. The part must be in an open document.
            </p>

            <p>
            <b>Usage</b>: The document containing the part to be inserted
            must be open in the current session.
            </p>

            <p>
            This command can also be used to repair broken instances.
            To do so, select the broken instance, launch this command,
            and select a new source part from the list.
            </p>
        """)

        return {
            "MenuText": "Insert Part",
            "Accel": "A, X",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(Asm4.iconPath, "Link_Part.svg")
        }


    def IsActive(self):

        if Gui.Selection.getSelection() and Gui.Selection.getSelection()[0].isDerivedFrom("App::Link"):
            return True

        elif Asm4.getAssembly() or Asm4.getSelectedRootPart():
            return True
        return False


    def Activated(self):

        # Assembly can be selected or anything inside of it to preselect it
        # When there is a selected instance (aka link)
        # - if the link is broken, fix it
        # - if the link is good, pre-select it for duplication

        self.active_doc = App.ActiveDocument
        self.target_asm = Asm4.getTargetAssembly()

        self.selected_instance = None
        self.is_broken_link = False

        self.docs = []
        self.parts = []

        if not self.layout():
            self._draw_UI()
        self._init_UI()

        selected_instance, is_valid_link = Asm4.get_selected_link(allow_broken_link=True)
        if selected_instance:
            self.selected_instance = selected_instance
            if is_valid_link:
                self.is_broken_link = False
                self._valid_link_mode()
            else:
                self.is_broken_link = True
                self._broken_link_mode()

        self.show()


    def _preselect_part(self):
        if self.selected_instance:
            selected_part = self.selected_instance.LinkedObject
            search_text = f"{selected_part.Document.Name}#{Asm4.formated_label_name(selected_part)}"
            part_found = self.parts_list.findItems(search_text, QtCore.Qt.MatchExactly)
            if part_found:
                self.parts_list.setCurrentItem(part_found[0])


    def _valid_link_mode(self):
        self.setWindowTitle("Insert Part to an Assembly")
        self.insert_button.setText("Insert")
        self.instance_name_label.setText("New Instance Name")
        self._preselect_part()


    def _broken_link_mode(self):
        self.setWindowTitle("Fix Broken Instance")
        self.insert_button.setText("Update")
        self.instance_name_label.setText("Update Instance Name")
        self.instance_name_field.setText(self.selected_instance.Label)


    def _update_instance_name(self):
        
        selected_item = self.parts_list.currentItem()
        if selected_item:
            selected_part = selected_item.data(QtCore.Qt.UserRole)

            orig_name = selected_part.Label
            last_char = orig_name[-1]
            if last_char.isnumeric():
                base_name, sep, num = orig_name.rpartition("_")
                if base_name:
                    base_name = re.sub(r"\d+$", "", orig_name)
                instance_name = Asm4.next_instance_name(base_name, start_at_one=True)
            else:
                instance_name = Asm4.next_instance_name(orig_name, start_at_one=False)

            self.instance_name_field.setText(instance_name)


    def _update_docs_and_parts(self):

        self.target_asm = self.assemblies_combo.currentData()

        self.docs = []
        self.parts = []

        docs = App.listDocuments().values()

        # Ignore temporary documents.
        for doc in docs:

            try:
                tmp_doc = doc.Temporary
            except AttributeError:
                tmp_doc = False


            if not tmp_doc:

                print("doc", doc, type(doc))

                for obj in doc.findObjects("App::Part"):
                    if obj != self.target_asm and obj.getParentGeoFeatureGroup() is None:
                        self.parts.append(obj)
                        self.docs.append(doc)

                for obj in doc.findObjects("PartDesign::Body"):
                    if obj.getParentGeoFeatureGroup() is None:
                        self.parts.append(obj)
                        self.docs.append(doc)


        self._update_parts_list()


    def _update_parts_list(self):
        self.target_asm = self.assemblies_combo.currentData()
        self.parts_list.clear()

        if self.target_asm:
            print("self.target_asm:", self.target_asm.Label, type(self.target_asm))
        else:
            print("self.target_asm:", self.target_asm, type(self.target_asm))


        for part in self.parts:
            icon = part.ViewObject.Icon
            label = f"{part.Document.Name}#{Asm4.formated_label_name(part)}"
            item = QtGui.QListWidgetItem(icon, label)
            item.setData(QtCore.Qt.UserRole, part)
            self.parts_list.addItem(item)
            if Asm4.has_cyclic_dependency(self.target_asm, part):
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
                item.setToolTip("Disabled to prevent cyclic dependency.")

        if self.parts_list.count() >= 0:
            self.parts_list.setCurrentRow(0)
            self._on_item_changed()


    def _on_filter_change(self):

        filter_str = self.parts_filter_field.text().strip()
        selected_index = None

        for i in range(self.parts_list.count()):
            item = self.parts_list.item(i)
            match_str = re.search(filter_str, item.text(), flags=re.IGNORECASE)

            if filter_str and not match_str:
                item.setHidden(True)
            else:
                item.setHidden(False)

            if item.isHidden() == False and selected_index == None:
                selected_index = i

        if self.parts_list.count() >= 0:
            if not selected_index:
                selected_index = 0
            self.parts_list.setCurrentRow(selected_index)
            self._on_item_changed()


    def _on_open_file_button(self):

        file_name = None
        import_doc = None
        is_doc_already_open = False

        dialog = QtGui.QFileDialog(
            QtGui.QApplication.activeWindow(),
            "Select FreeCAD document to import part from")

        dialog.setNameFilter(
            "FreeCAD Documents (*.FCStd);;All Files (*)"
        )

        if dialog.exec_():
            file_name = str(dialog.selectedFiles()[0])

            # look only for file_names, not paths, as there are problems on WIN10 (Address-translation??)
            requested_file = os.path.split(file_name)[1]

            # see whether the file is already open
            for doc in App.listDocuments().values():
                recent_file = os.path.split(doc.FileName)[1]
                if requested_file == recent_file:
                    is_doc_already_open = True
                    break

            if not is_doc_already_open:
                if file_name.lower().endswith(".fcstd"):
                    doc = App.openDocument(file_name)
                    App.setActiveDocument(self.active_doc.Name)
                    self._update_docs_and_parts()
                    self.raise_()
                    self.activateWindow()
                    self.parts_filter_field.setFocus()


    def _on_insert_button(self):

        self.target_asm = self.assemblies_combo.currentData()

        selected_item = self.parts_list.currentItem()
        selected_part = selected_item.data(QtCore.Qt.UserRole)
        instance_name = self.instance_name_field.text()

        if selected_part:

            if self.is_broken_link:

                self.selected_instance.Label = instance_name
                self.selected_instance.LinkedObject = selected_part
                self.selected_instance.recompute(True)

                self.close()

                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(self.active_doc.Name, self.target_asm.Name, f"{self.selected_instance.Name}.")

                # Save things it to the next command
                Asm4.TARGET_ASM = self.target_asm
                Asm4.SELECTED_INSTANCE = self.selected_instance
                Asm4.PLACING_NEW_INSTANCE = False

                Gui.runCommand("Asm4_placeLink")

            elif self.target_asm and instance_name:

                if App.ActiveDocument.FileName or App.ActiveDocument == selected_part.Document:

                    new_instance = self.target_asm.newObject("App::Link", "Link")
                    new_instance.Label = instance_name
                    new_instance.LinkedObject = selected_part
                    Asm4.makeAsmProperties(new_instance)
                    new_instance.recompute()

                    self.close()

                    Gui.Selection.clearSelection()
                    Gui.Selection.addSelection(self.active_doc.Name, self.target_asm.Name, f"{new_instance.Name}.")

                    # Save things it to the next command
                    Asm4.TARGET_ASM = self.target_asm
                    Asm4.SELECTED_INSTANCE = new_instance
                    Asm4.PLACING_NEW_INSTANCE = True

                    Gui.runCommand("Asm4_placeLink")

                else:
                    Asm4.warningBox("The document must be saved before inserting a part.")
                    return

        self.close()


    def _on_item_changed(self):
        self.selected_part = self.parts_list.currentItem()
        if not self.is_broken_link:
            self._update_instance_name()

        # row = self.parts_list.currentRow()
        # if row:
        #     doc = self.docs[row]
        #     self.selected_part = self.parts[row]


    def _on_item_double_clicked(self, item):
        self._on_item_changed()
        self._on_insert_button()


    def _on_cancel_button(self):
        self.close()


    def _update_assemblies_combo(self):

        assemblies = Asm4.findAssemblies()

        self.assemblies_combo.clear()

        for obj in assemblies:
            icon = QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Model.svg"))
            self.assemblies_combo.addItem(icon, Asm4.formated_label_name(obj), obj)

        self.assemblies_combo.setEnabled(True)
        if len(assemblies) <= 1:
            self.assemblies_combo.setEnabled(False)

        self.target_asm = Asm4.getTargetAssembly()

        if self.target_asm:
            label = Asm4.formated_label_name(self.target_asm)
            index = self.assemblies_combo.findText(label)
            if index >= 0:
                self.assemblies_combo.setCurrentIndex(index)


    def eventFilter(self, obj, event):

        if obj is self.parts_filter_field and event.type() == QtCore.QEvent.KeyPress:

            if event.key() == QtCore.Qt.Key_Down:
                row = min(
                    self.parts_list.count() - 1,
                    self.parts_list.currentRow() + 1
                )
                self.parts_list.setCurrentRow(row)
                return True

            if event.key() == QtCore.Qt.Key_Up:
                row = max(
                    0,
                    self.parts_list.currentRow() - 1
                )
                self.parts_list.setCurrentRow(row)
                return True

        return super().eventFilter(obj, event)


    def _init_UI(self):
        self._update_assemblies_combo()
        self.parts_filter_field.clear()
        self.parts_filter_field.setFocus()
        self.parts_list.clear()
        self.instance_name_field.clear()
        self._update_docs_and_parts()


    def _draw_UI(self):

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setWindowTitle("Insert Part to an Assembly")
        self.resize(500, 450)

        self.main_layout = QtGui.QVBoxLayout(self)

        self.assemblies_combo = QtGui.QComboBox()
        self.main_layout.addWidget(QtGui.QLabel("Target Assembly"))
        self.main_layout.addWidget(self.assemblies_combo)
        self.main_layout.addSpacing(10)

        self.parts_filter_field = QtGui.QLineEdit()
        self.parts_filter_field.installEventFilter(self)
        self.parts_filter_field.setFocus()
        self.main_layout.addWidget(QtGui.QLabel("Parts Filter"))
        self.main_layout.addWidget(self.parts_filter_field)
        self.main_layout.addSpacing(10)

        self.parts_list = QtGui.QListWidget()
        self.main_layout.addWidget(QtGui.QLabel("Select Part"))
        self.main_layout.addWidget(self.parts_list)
        self.main_layout.addSpacing(10)

        self.instance_name_field = QtGui.QLineEdit()
        self.instance_name_label = QtGui.QLabel("New Instance Name")
        self.main_layout.addWidget(self.instance_name_label)
        self.main_layout.addWidget(self.instance_name_field)
        self.main_layout.addSpacing(10)

        self.buttons_layout = QtGui.QHBoxLayout()

        self.cancel_button = QtGui.QPushButton("&Cancel", self)
        self.open_file = QtGui.QPushButton("&Open File", self)
        self.insert_button = QtGui.QPushButton("&Insert", self)
        self.insert_button.setDefault(True)

        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.cancel_button)
        self.buttons_layout.addWidget(self.open_file)
        self.buttons_layout.addWidget(self.insert_button)

        self.main_layout.addLayout(self.buttons_layout)


        # Actions

        self.assemblies_combo.currentIndexChanged.connect(self._update_docs_and_parts) #_update_parts_list)
        self.assemblies_combo.activated.connect(self._update_docs_and_parts) #_update_parts_list)

        self.parts_list.itemClicked.connect(self._on_item_changed)
        self.parts_list.itemActivated.connect(self._on_item_changed)
        self.parts_list.currentItemChanged.connect(self._on_item_changed)
        self.parts_list.itemDoubleClicked.connect(self._on_item_double_clicked)

        self.parts_filter_field.textChanged.connect(self._on_filter_change)

        self.cancel_button.clicked.connect(self._on_cancel_button)
        self.open_file.clicked.connect(self._on_open_file_button)
        self.insert_button.clicked.connect(self._on_insert_button)


Gui.addCommand("Asm4_insertLink", InsertLink())

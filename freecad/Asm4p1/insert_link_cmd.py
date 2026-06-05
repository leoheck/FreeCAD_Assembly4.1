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


class InsertLink():

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
        # if an App::Link is selected, even a broken one
        if Gui.Selection.getSelection() and Gui.Selection.getSelection()[0].isDerivedFrom('App::Link'):
            return True
        # there is an assembly or a root App::Part is selected
        elif Asm4.getAssembly() or Asm4.getSelectedRootPart():
            return True
        return False


    def Activated(self):

        # initialise stuff
        self.activeDoc    = App.ActiveDocument
        self.rootAssembly = None
        self.origLink     = None
        self.brokenLink   = False

        self.UI = QtGui.QDialog()
        self.drawUI()


        #self.allParts = []
        #self.partsDoc = []
        #self.partList.clear()
        self.filterPartList.clear()
        self.linkNameInput.clear()

        # # if an Asm4 Assembly is present, that's where we put the link
        # if Asm4.getAssembly():
        #     self.rootAssembly  = Asm4.getAssembly()
        # # an App::Part at the root of the document is selected, we insert the link there
        # elif Asm4.getSelectedRootPart():
        #     self.rootAssembly = Asm4.getSelectedRootPart()
        # # if a link is selected, we see if we can duplicate it
        # if Asm4.getSelectedLink():
        #     selObj = Asm4.getSelectedLink()
        #     parent = selObj.getParentGeoFeatureGroup()
        #     # if the selected link is in a root App::Part
        #     if parent is not None and parent.TypeId == 'App::Part' and parent.getParentGeoFeatureGroup() is None:
        #         self.rootAssembly = parent
        #         self.origLink = selObj
        # # if a broken link is selected
        # elif len(Gui.Selection.getSelection())==1 :
        #     selObj = Gui.Selection.getSelection()[0]
        #     if selObj.isDerivedFrom('App::Link') and selObj.LinkedObject is None:
        #         parent = selObj.getParentGeoFeatureGroup()
        #         # if the selected (broken) link is in a root App::Part
        #         if parent.TypeId == 'App::Part' and parent.getParentGeoFeatureGroup() is None:
        #             self.brokenLink = True
        #             self.rootAssembly = parent
        #             self.origLink = selObj
        #             self.UI.setWindowTitle('Re-link broken link')
        #             self.insertButton.setText('Replace')
        #             self.linkNameInput.setText(Asm4.labelName(selObj))
        #             self.linkNameInput.setEnabled(False)

        # if self.rootAssembly is None:
        #     Asm4.warningBox("Create the Assembly object first.")
        #     return

        self.rootAssembly = Asm4.getTargetAssembly()

        # build the list of available parts
        self.create_list_of_parts()

        # if an existing valid App::Link was selected
        if self.origLink and not self.brokenLink:
            origPart = self.origLink.LinkedObject
            # try to find the original part of the selected link
            origPartText = origPart.Document.Name +"#"+ Asm4.labelName(origPart)
            # MatchExactly, MatchContains, MatchEndsWith, MatchStartsWith ...
            partFound = self.partList.findItems( origPartText, QtCore.Qt.MatchExactly )
            if partFound:
                self.partList.setCurrentItem(partFound[0])
                # self.onItemClicked(partFound[0])
                # if the last character is a number, we increment this number
                origName = self.origLink.Label
                lastChar = origName[-1]
                if lastChar.isnumeric():
                    (rootName,sep,num) = origName.rpartition('_')
                    if rootName=="":
                        rootName = origName[:-3]
                    proposedLinkName = Asm4.nextInstance(rootName,startAtOne=True)
                # else we take the next instance
                else:
                    proposedLinkName = Asm4.nextInstance(origName,startAtOne=False)
                # set the proposed name in the entry field
                self.linkNameInput.setText( proposedLinkName )

        if self.partList.count() > 0:
            self.partList.setCurrentRow(0)
            item = self.partList.item(0)
            self.onItemClicked(item)

        # show the UI
        self.UI.show()

    # Search for all App::Parts and PartDesign::Body in all open documents, expect by the current selected Assembly
    # Also store the document of the part
    def create_list_of_parts(self, doc=None):

        self.allParts = []
        self.partsDoc = []

        if doc is None:
            docs = App.listDocuments().values()
        else:
            docs = [doc]

        for doc in docs:

            # don't consider temporary documents. Guard against older versions of FreeCad
            # which don't have the Temporary attribute
            try:
                temp_doc = doc.Temporary 
            except AttributeError:
                temp_doc = False
                
            if not temp_doc:
                for obj in doc.findObjects("App::Part"):
                    # we don't want to link to itself to the 'Model' object
                    # other App::Part in the same document are OK 
                    # but only those at top level (not nested inside other containers)
                    if obj != self.rootAssembly and obj.getParentGeoFeatureGroup() is None:
                        self.allParts.append(obj)
                        self.partsDoc.append(doc)

                for obj in doc.findObjects("PartDesign::Body"):
                    # but only those at top level (not nested inside other containers)
                    if obj.getParentGeoFeatureGroup() is None:
                        self.allParts.append(obj)
                        self.partsDoc.append(doc)

        # build the list
        self.partList.clear()
        for idx, part in enumerate(self.allParts):
            item = QtGui.QListWidgetItem()
            item.setText(f"{part.Document.Name}#{Asm4.labelName(part)}")
            item.setIcon(part.ViewObject.Icon)
            self.partList.addItem(item)
            if Asm4.hasCyclicDependency(self.rootAssembly, part):
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
                item.setToolTip("Disabled to prevent cyclic dependency.")


    def onFilterChange(self):
        filterStr = self.filterPartList.text().strip()

        first_visible_idx = None

        for x in range(self.partList.count()):
            item = self.partList.item(x)

            # check the items's text match the filter ignoring the case
            matchStr =  re.search(filterStr, item.text(), flags=re.IGNORECASE)
            if filterStr and not matchStr:
                item.setHidden(True)
            else:
                item.setHidden(False)

            if item.isHidden() == False and first_visible_idx == None:
                first_visible_idx = x

        if self.partList.count() > 0:
            if first_visible_idx == None:
                first_visible_idx = 0
            self.partList.setCurrentRow(first_visible_idx)
            item = self.partList.item(first_visible_idx)
            self.onItemClicked(item)

    # from A2+
    def openFile(self):
        filename = None
        importDoc = None
        importDocIsOpen = False
        dialog = QtGui.QFileDialog( QtGui.QApplication.activeWindow(),
                                    "Select FreeCAD document to import part from" )
        # set option "DontUseNativeDialog"=True, as native Filedialog shows
        # misbehavior on Unbuntu 18.04 LTS. It works case sensitively, what is not wanted...
        '''
        if a2plib.getNativeFileManagerUsage():
            dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, False)
        else:
            dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, True)
        '''
        dialog.setNameFilter("Supported Formats *.FCStd *.fcstd (*.FCStd *.fcstd);;All files (*.*)")
        if dialog.exec_():
            filename = str(dialog.selectedFiles()[0])
            # look only for filenames, not paths, as there are problems on WIN10 (Address-translation??)
            requestedFile = os.path.split(filename)[1]
            # see whether the file is already open
            for d in App.listDocuments().values():
                recentFile = os.path.split(d.FileName)[1]
                if requestedFile == recentFile:
                    importDoc = d # file is already open...
                    importDocIsOpen = True
                    break
            # if not, open it
            if not importDocIsOpen:
                if filename.lower().endswith('.fcstd'):
                    importDoc = App.openDocument(filename)
                    App.setActiveDocument( self.activeDoc.Name )
                    # update the part list
                    self.create_list_of_parts(importDoc)
        return


    """
    +-----------------------------------------------+
    |         the real stuff happens here           |
    +-----------------------------------------------+
    """

    def get_item_name(self, text):
        if "[" in text and "]" in text:
            return text[text.rfind("[") + 1:text.rfind("]")]
        return text.strip()

    def format_combo_item(self, obj):
        pass

    def onCreateLink(self):

        Asm4.TARGET_ASM = self.assemblies_combo.currentData()
        self.rootAssembly = Asm4.TARGET_ASM

        selected_part = []
        for selected in self.partList.selectedIndexes():
            selected_part = self.allParts[selected.row()]

        instance_name = self.linkNameInput.text()

        # Repair broken link
        if self.brokenLink and selected_part:
            self.instance_link.LinkedObject = selected_part
            self.instance_link.recompute()
            self.UI.close()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(self.activeDoc.Name, self.rootAssembly.Name, self.instance_link.Name + '.')
            Gui.runCommand("Asm4_placeLink")

        # only create link if there is a Part object and a name
        elif self.rootAssembly and selected_part and instance_name:
    
            if App.ActiveDocument.FileName !='' or App.ActiveDocument == selected_part.Document:

                instance_link = self.rootAssembly.newObject("App::Link", "Link")
                instance_link.Label = instance_name

                instance_link.LinkedObject = selected_part
                Asm4.makeAsmProperties(instance_link)
                instance_link.recompute()
                self.UI.close()

                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(self.activeDoc.Name, self.rootAssembly.Name, instance_link.Name + '.')

                Asm4.SELECTED_INSTANCE = instance_link
                Asm4.PLACING_NEW_INSTANCE = True

                Gui.runCommand("Asm4_placeLink")

            else:
                Asm4.warningBox("The document must be saved before inserting a part.")
                return

        # if still open, close the dialog UI
        self.UI.close()


    def onItemClicked(self, item):
        for selected in self.partList.selectedIndexes():
            # get the selected part
            part = self.allParts[selected.row()]
            doc = self.partsDoc[selected.row()]
            proposed_instance_name = part.Label
            # set the proposed name into the text field, unless it's a broken link
            if not self.brokenLink:
                self.linkNameInput.setText(proposed_instance_name)


    def onItemDoubleClicked(self, item):
        self.onItemClicked(item)
        self.onCreateLink()


    def onCancel(self):
        self.UI.close()


    def _create_target_asm_combo(self):
        
        assembly_objs = Asm4.findAssemblies()

        self.assemblies_combo = QtGui.QComboBox()
        for obj in assembly_objs:
            self.assemblies_combo.addItem(
                QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Model.svg")), 
                Asm4.formated_label_name(obj),
                obj
            )

        if len(assembly_objs) == 1:
            self.assemblies_combo.setEnabled(False)

        if not self.rootAssembly:
            self.rootAssembly = Asm4.getTargetAssembly()

        self.assemblies_combo.setCurrentIndex(0)
        if self.rootAssembly:
            search_text = Asm4.formated_label_name(self.rootAssembly)
            index = self.assemblies_combo.findText(search_text)
            if index != -1:
                self.assemblies_combo.setCurrentIndex(index)


    def updatePartsList(self):
        self.rootAssembly = self.assemblies_combo.currentData()
        self.create_list_of_parts()


    def drawUI(self):

        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setModal(False)
        self.UI.setWindowTitle("Insert Part")
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Part.svg")))
        self.UI.resize(500, 450)

        self._create_target_asm_combo()

        self.filterPartList = QtGui.QLineEdit(self.UI)
        self.partList = QtGui.QListWidget(self.UI)
        self.linkNameInput = QtGui.QLineEdit(self.UI)

        self.cancelButton = QtGui.QPushButton("Cancel", self.UI)
        self.openFileButton = QtGui.QPushButton("Open File", self.UI)
        self.insertButton = QtGui.QPushButton("Insert Part", self.UI)
        self.insertButton.setDefault(True)

        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.UI)
        self.mainLayout.addSpacing(10)
        self.mainLayout.addWidget(QtGui.QLabel("Target Assembly"))
        self.mainLayout.addWidget(self.assemblies_combo)
        self.mainLayout.addSpacing(10)
        self.mainLayout.addWidget(QtGui.QLabel("Parts Filter"))
        self.mainLayout.addWidget(self.filterPartList)
        self.mainLayout.addSpacing(10)
        self.mainLayout.addWidget(QtGui.QLabel("Select the Part"))
        self.mainLayout.addWidget(self.partList)
        self.mainLayout.addSpacing(10)
        self.mainLayout.addWidget(QtGui.QLabel("New Instance Name"))
        self.mainLayout.addWidget(self.linkNameInput)
        self.mainLayout.addWidget(QtGui.QLabel(' '))
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.cancelButton)
        self.buttonsLayout.addWidget(self.openFileButton)
        self.buttonsLayout.addWidget(self.insertButton)
        self.mainLayout.addLayout(self.buttonsLayout)
        self.UI.setLayout(self.mainLayout)

        self.assemblies_combo.currentIndexChanged.connect(self.updatePartsList)
        self.assemblies_combo.activated.connect(self.updatePartsList)

        self.partList.itemClicked.connect(self.onItemClicked)
        self.partList.itemActivated.connect(self.onItemClicked)
        self.partList.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.filterPartList.textChanged.connect(self.onFilterChange)

        self.cancelButton.clicked.connect(self.onCancel)
        self.openFileButton.clicked.connect(self.openFile)
        self.insertButton.clicked.connect(self.onCreateLink)


Gui.addCommand("Asm4_insertLink", InsertLink())

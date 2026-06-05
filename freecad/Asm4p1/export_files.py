#!/usr/bin/env python3
# coding: utf-8

# export_files.py

import os
import zipfile

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

from . import asm4_libs as Asm4
from . import list_linked_files

class ExportFiles():

    def __init__(self):
        super(ExportFiles, self).__init__()


    def GetResources(self):
        return {
            "MenuText": "Export Assembly",
            "ToolTip": "Creates a .zip file with all assembly files.",
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_Export_PartsList.svg")
        }


    def IsActive(self):
        if Asm4.findAssemblies():
            return True
        return False


    def Activated(self):

        asm = Asm4.getTargetAssembly()

        self.filename = App.ActiveDocument.Name
        self.relative_file_path = App.ActiveDocument.FileName # GUI uses absolute path, CLI the path given byt the user
        self.doc_root_dirpath = os.path.dirname(self.relative_file_path)

        suggested_zip_file = os.path.join(self.doc_root_dirpath, self.filename + "_asm4.zip")
        self.zip_filepath = QtGui.QFileDialog.getSaveFileName(None, "Export Linked Files (as .zip)", suggested_zip_file, "All files (*)", "")[0]
        if self.zip_filepath == "":
            return

        self.linked_files = list_linked_files.ListLinkedFiles().get_linked_files(asm)
        self._export_zip_package()


    def _export_zip_package(self):

        print("ASM4, Creating a zip package with linked files")

        current_path = os.getcwd()

        common_path = os.path.commonpath(self.linked_files)
        print("ASM4> Common path: \"{}\"".format(common_path))
        root_dirpath = common_path

        # Chdir does not like empty path (when Freecad was opened in the same path of the FCStd file)
        if root_dirpath == "":
            root_dirpath = "./"

        os.chdir(root_dirpath)

        # Create the Zip file
        # TODO: Check if this doc_root_dirpath is always right
        zip_obj = zipfile.ZipFile(self.zip_filepath, 'w', zipfile.ZIP_DEFLATED)
        zip_obj.create_system = 3 # symlink support

        # Add files to the package
        remove_zip = False
        for i, filepath in enumerate(self.linked_files):
            self.relative_file_path = os.path.relpath(filepath, root_dirpath)
            print("ASM4> [ZIP] {}, adding file {}".format(i + 1, self.relative_file_path))
            try:
                zip_obj.write(filepath, self.relative_file_path)
            except:
                print("ASM4> Error: Cannot create the zip package")
                remove_zip = True
                break

            if os.path.splitext(os.path.basename(filepath))[0] == self.filename:
                assembly_symlink_path = self.filename + ".FCStd"
                if not os.path.isfile(assembly_symlink_path):
                    self.relative_file_path = os.path.relpath(filepath, root_dirpath)
                    print("ASM4> [ZIP] {}, creating symlink {} to {}".format("_", assembly_symlink_path, self.relative_file_path))
                    os.symlink(relative_file_path, assembly_symlink_path)
                    print("ASM4> [ZIP] {}, adding symlink {}".format("_", assembly_symlink_path))
                    zip_info = zipfile.ZipInfo(assembly_symlink_path)
                    zip_info.external_attr |= 0xA0000000
                    zip_obj.writestr(zip_info, os.readlink(assembly_symlink_path))
                    os.remove(assembly_symlink_path) # remove symlink created

        zip_obj.close()

        if remove_zip:
            os.remove(self.zip_filepath)
            print("ASM4> Zip could not be created.")
        else:
            print("ASM4> Zip package {} was created.".format(self.zip_filepath))

        os.chdir(current_path)


Gui.addCommand("Asm4_ExportFiles", ExportFiles())

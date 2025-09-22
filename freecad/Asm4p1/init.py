# -*- coding: utf-8 -*-
###################################################################################
#
#  Init.py
#  
#  Copyright 2018 Mark Ganson <TheMarkster>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################

# import os

# import FreeCAD as App

# from . import asm4_locator

# Asm4_path = os.path.dirname( asm4_locator.__file__ )
# packageFile  = os.path.join( Asm4_path, '../../package.xml' )

# try:
#     metadata = FreeCAD.Metadata(packageFile)
#     Asm4_date = metadata.Date
#     Asm4_version = metadata.Version

# except:
#     import re
#     with open(packageFile, "r") as f:
#         xml = f.read()  # single string with the entire file content
#     match_version = re.search(r"<version>(.*?)</version>", xml)
#     match_date = re.search(r"<date>(.*?)</date>", xml)
#     if match_version:
#         Asm4_version = match_version.group(1)
#     if match_date:
#         Asm4_date = match_version.group(1)

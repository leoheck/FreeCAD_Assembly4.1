# Assembly4 workbench for FreeCAD

Current version 0.60.1

## New FreeCAD hosting

We are pleased to announce that FreeCAD version 0.21 is maintained again, and is hosted at European git hosting provider [CodeBerg](https://codeberg.org/). Please visit us and don't hesitate to contribute:

[https://codeberg.org/xCAD/FreeCAD21](https://codeberg.org/xCAD/FreeCAD21)


## Overview

This assembly workbench allows to assemble into a single assembly container other FreeCAD objects, and place them relative to the assembly and to each-other. The parts in the assembly can be in the same document as the assembly or in an external document. When parts are modified in their original document, they are instantly updated in the assembly.

An Assembly4 _Assembly_ is a standard FreeCAD `App::Part` container, therefore it is compatible and can be manipulated with any FreeCAD tool handling `App::Part` objects. In particular, it can be inserted into another _Assembly_ to create nested assemblies to any level. It can also contain solids, datum objects and sketches. A document can contain only 1 _Assembly_. Native FreeCAD _Part_ and _Body_ containers can be used as "part" to be inserted. Being built on standard FreeCAD objects, all Assembly4 assemblies are fully compatible with all standard FreeCAD tools. 

Parts are placed relative to each-other by matching features inside them. Specifically, in Assembly4, these _features_ are virtual objects called LCS (for Local Coordinate System, also called datum coordinate system) and are attached using FreeCAD's built-in `Part::Attacher` and `ExpressionEngine`. No geometry is used to place and constrain parts relative to each other, thus avoiding a lot of the topological naming problems. These built-in tools are also very fast, efficient and stable allowing very large assemblies with many levels of nested sub-assemblies.


![](Resources/media/LaserCutter.png)

**Please Note:** only _Part_ and _Body_ containers at the root of a document can be inserted. Objects nested inside containers cannot be used directly by Assembly4.



## Installation

### Addon Manager (recommended)

[![FreeCAD Addon manager status](https://img.shields.io/badge/FreeCAD%20addon%20manager-available-brightgreen)](https://github.com/FreeCAD/FreeCAD-addons)

Assembly 4 is available through the FreeCAD Addon Manager (menu **Tools > Addon Manager**). It is called _Assembly4_ in the Addon Repository.

**Important Note:** Assembly4 recommends to use the stable FreeCAD v0.21 branch

**Important Note:** Assembly4 has been removed from the Mocrosoft-owned and USA-based GitHub forge, and is now located on the non-profit [codeberg.org](https://codeberg.org/) forge, located in Europe (Germany)



### Manual Installation

It is possible to install this workbench manually into FreeCAD's local workbench directory. See [user instructions](INSTRUCTIONS.md)


## Getting Started

Assembly4 uses extensively FreeCAD's built-in `Part::Attacher`, and you can find documentation [following this link](https://wiki.freecad.org/Part_EditAttachment). It is recommended to be familiar with this function to get best usage of this workbebch.

## Documentation

* Assembly4 documentation has its own repository: [https://codeberg.org/Zolko/Asm4_documentation](https://codeberg.org/Zolko/Asm4_documentation)
* Please read the [User Manual](https://codeberg.org/Zolko/Asm4_documentation/src/branch/main/USER_MANUAL.md), 
* Or the more in-depth [Technical Manual](https://codeberg.org/Zolko/Asm4_documentation/src/branch/main/TECH_MANUAL.md)
* You are invited to follow a tutorial for [a quick assembly from scratch](https://codeberg.org/Zolko/Asm4_documentation/src/branch/main/TUTORIAL_1.md)
* You can learn about the use of a master sketch and animation of assemblies by building [a cinematic assembly in one file](https://codeberg.org/Zolko/Asm4_documentation/src/branch/main/TUTORIAL_2.md)
* For advanced user, you can read how to use variant links with the tutorial of the [Theo Jansen sandwalker](https://codeberg.org/Zolko/Asm4_documentation/src/branch/main/TUTORIAL_3.md)


## Discussion
Please offer feedback or connect with the developers in the [issues section](https://codeberg.org/Zolko/Assembly4/issues) section.


## Addon Repository
This addon is hosted on a [codeberg repository](https://codeberg.org/Zolko/Assembly4).


## Release notes
Release notes can be found in the [CHANGELOG](CHANGELOG.md) file.


## License
Assembly4 is released under the open-source license LGPLv2.1 (see [LICENSE](LICENSE))


## Support
This tool is an external addon to FreeCAD and is not related in any way to the FreeCAD organisation. You can provide your financial support for the continuing development of this open-source workbench :

<a href="https://www.paypal.com/donate/?hosted_button_id=LBA6ZAV9QSQT8" target="_blank"><img src="Resources/media/PayPal_Donate.svg" height="36" alt="PayPal Donate"/></a>
<a href="https://liberapay.com/Zolko/donate" target="_blank"><img src="Resources/media/LiberaPay_donate.svg" height="36" alt="LiberaPay Donate"></a>
<a href="https://www.patreon.com/c/Zolko_123" target="_blank"><img src="Resources/media/Patreon_Donate.svg" height="36" alt="Patreon Donate"></a>







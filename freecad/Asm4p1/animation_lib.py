#!/usr/bin/env python3
# coding: utf-8

# LGPL
# Copyright HUBERT Zoltán
#
# animation_lib.py

import os
from textwrap import dedent

from PySide import QtGui, QtWidgets, QtCore
from enum import Enum
import FreeCADGui as Gui
import FreeCAD as App

from . import asm4_libs as Asm4



def debug_lheck(_var):
    print(f"=======================> ({_var})")


class AnimationProvider:

    def nextFrame(self, resetAnimation) -> bool:

        # Setup the scene for the next frame of the animation.
        # Set resetAnimation True for the first frame
        # Signals that the last frame has been reached by returning True

        raise NotImplementedError("AnimationProvider.nextFrame not implemented.")


    def pendulumWanted(self) -> bool:

        # Optionally flag that pendulum (forth and back animation) is wanted.
        # Prevents the need to capture identical frames on the "returning path"
        # of the animation.

        return False


    class Error(Exception):
        """
        Base class for exceptions thrown when issues with
        animating the scene from an AnimationProvider occur.
        """

        def __init__(self, short_msg: str, detail_msg: str):
            self.short_msg = short_msg
            self.detail_msg = detail_msg



class AnimateVariable(AnimationProvider):

    class AnimationState(Enum):
        IDLE = 0
        RUNNING = 1


    class AnimationRequest(Enum):
        NONE = 0
        START = 1
        STOP = 2


    class UnknownVariableError(AnimationProvider.Error):
        """
        Exception to be raised when animation fails because
        the selected variable is not valid/does not exist.
        """

        def __init__(self, var_name):
            short_msg = "Variable name invalid"
            detail_msg = dedent(f"""
                The selected variable name "{var_name}" is not valid.
                Please select an existing variable.
            """).strip()
            super().__init__(short_msg, detail_msg)
            self.var_name = var_name


    def __init__(self):
        super(AnimateVariable,self).__init__()
        self.UI = QtGui.QDialog()
        self.UI.keyPressEvent = self.keyPressEvent
        self.drawUI()
        self.MDIArea = Gui.getMainWindow().findChild(QtGui.QMdiArea)

        self.active_doc = None
        self.target_doc = None
        self.target_asm = None
        self.target_var = None

        self.known_docs = []
        self.known_asms = []
        self.known_vars = []

        self.animation_state = self.AnimationState.IDLE

        self.force_render = False
        self.reverse_animation = False

        self.timer_ms = QtCore.QTimer()
        self.timer_ms.setInterval(0)
        self.timer_ms.timeout.connect(self.onTimerTick)

        self.plotter = None
        self.exporter = None


    def GetResources(self):
        return {
            "MenuText": "Animate Assembly",
            "ToolTip": "Animate Assembly",
            "Accel": "A, Z",
            "Pixmap": os.path.join(Asm4.iconPath, "Asm4_GearsAnimate.svg")
        }


    def IsActive(self):
        if App.ActiveDocument:
            doc = App.ActiveDocument
            variables = [obj for obj in doc.Objects if obj.Name.startswith("Variables") and obj.Type == "App::PropertyContainer"]
            if variables:
                return True
        return False


    def Activated(self):

        # if the previously animated documents has been closed
        self.active_doc = App.ActiveDocument
        # if self.target_doc not in App.listDocuments().values():
        if self.target_doc not in App.listDocuments().keys():
            self.target_doc = self.active_doc

        # if self.target_doc:
        #     self.target_var = self.target_doc.getObject("Variables")
        #     # the root assembly in the current document is wherever the Variables container is
        #     # self.target_asm = Asm4.getAssembly()
        #     self.target_asm = self.target_var.getParentGeoFeatureGroup()
        # else:
        #     self.target_asm = Asm4.getTargetAssembly()

        self.target_asm = Asm4.getTargetAssembly()

        self._update_docs_list()
        self._update_assemblies_list()
        self._update_vars_list()

        # in case the dialog is newly opened, register for changes of the selected document
        if not self.UI.isVisible():
            self.MDIArea.subWindowActivated.connect(self.onDocChanged)
        self.UI.show()


    """
    +------------------------------------------------+
    |  fill default values when selecting a document |
    +------------------------------------------------+
    """

    def _update_docs_list(self):

        docs = []
        for doc in App.listDocuments():
            docs.append(doc)

        # only update the gui-element if documents actually changed
        if self.known_docs != docs:
            self.docs_combo.clear()
            for doc in docs:
                self.docs_combo.addItem(QtGui.QIcon(Gui.getIcon("Document")), doc, App.listDocuments()[doc])

            self.known_docs = docs

        active_doc = App.ActiveDocument
        if active_doc in App.listDocuments().values():
            idx = list(App.listDocuments().values()).index(active_doc)
            self.docs_combo.setCurrentIndex(idx)
            self.target_doc = self.docs_combo.currentData()
            self._update_assemblies_list()


    def _on_select_doc(self):

        self.update(self.AnimationRequest.STOP)

        selected_doc = self.docs_combo.currentData()
        docs = App.listDocuments()

        if selected_doc and selected_doc in docs:
            self.target_doc = docs[selected_doc]
            self._update_assemblies_list()
        else:
            self.target_doc = None
            self.target_var = None


    def _update_assemblies_list(self):

        # doc = self.docs_combo.currentData()

        if self.target_doc is None:
            return

        asms = Asm4.findAssemblies(self.target_doc)
        # for i in asms:
            # print("ASM:", i.Name, i.Label)
        if len(asms)>1:
            self.target_asm = asms[0]

        self.assemblies_combo.clear()
        if len(asms) >= 1:
            for asm in asms:
                self.assemblies_combo.addItem(
                    QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Model.svg")),
                    Asm4.formated_label_name(asm),
                    asm
                )
            self.assemblies_combo.setCurrentIndex(0)
            self.target_asm = self.assemblies_combo.currentData()

        self._update_vars_list()


    def _on_select_assembly(self):
        self.target_asm = self.assemblies_combo.currentData()
        self._update_vars_list()


    def _update_vars_list(self):

        if self.target_asm is None:
            return

        self.target_var = [obj for obj in self.target_asm.Group if obj.Name.startswith("Variables")][0]
        doc_vars = []

        # Collect all variables currently available in the doc
        if self.target_var:
            for prop in self.target_var.PropertiesList:
                if self.target_var.getGroupOfProperty(prop) == "Variables":
                    if self.target_var.getTypeIdOfProperty(prop) == "App::PropertyFloat":
                        doc_vars.append(prop)

        # only update the gui-element if variables actually changed
        if self.known_vars != doc_vars:
            self.var_combo.clear()
            for var in doc_vars:
                self.var_combo.addItem(
                    QtGui.QIcon(os.path.join(Asm4.iconPath, "Asm4_Variables.svg")), var)
            self.known_vars = doc_vars
            AnimationHints.cleanUp(self.target_var)

        # prevent active gui controls when no valid variable is selected
        self._on_select_var()


    def _on_select_var(self):

        self.update(self.AnimationRequest.STOP)
        # self._stop_animation()

        selected_var = self.var_combo.currentText()

        if self._is_known_variable(selected_var):
            # grab animationsHints related to the variable and init accordingly
            aniHints = AnimationHints.get(self.target_var, selected_var)
            self.initial_value.setValue(aniHints[AnimationHints.Key.RangeBegin])
            self.final_value.setValue(aniHints[AnimationHints.Key.RangeEnd])
            self.step_value.setValue(aniHints[AnimationHints.Key.StepSize])
            self.step_time.setValue(aniHints[AnimationHints.Key.SleepTime])
            self.loop_animation_radio.setChecked(aniHints[AnimationHints.Key.Loop])
            self.pendulum_animation_radio.setChecked(aniHints[AnimationHints.Key.Pendulum])
            self._enable_widgets(True)
        else:
            self._enable_widgets(False)


    def _is_known_variable(self, var_name):
        if var_name and self.target_var and var_name in self.target_var.PropertiesList:
            return True
        return False

    """
    +-----------------------------------------------+
    |            Animation Tick Functions           |
    +-----------------------------------------------+
    """
    def _init_animation(self):
        var_name = self.var_combo.currentText()

        if not self._is_known_variable(var_name):
            self._update_vars_list()
            raise AnimateVariable.UnknownVariableError(var_name)

        # self.run_stop_button.setEnabled(False)
        # self.StopButton.setEnabled(True)

        self.set_current_var_value(self.var_combo.currentText(), self.initial_value.value())
        self.reverse_animation = False


    def _next_animation_step(self, reverse):

        debug_lheck("_next_animation_step")

        var_name = self.var_combo.currentText()
        if not self._is_known_variable(var_name):
            raise AnimateVariable.UnknownVariableError(var_name)

        var_value = self.target_var.getPropertyByName(var_name)

        # Calculate the next variable increment/decrement
        begin = self.initial_value.value()
        end = self.final_value.value()
        step = abs(self.step_value.value())

        if reverse:
            begin, end = end, begin
        if begin < end:
            var_value += step
        elif begin > end:
            var_value -= step

        # Assert var_value is in currently set range (range can now update with the animation running)
        var_value = min(var_value, max(begin, end))
        var_value = max(var_value, min(begin, end))

        # Update document variable and slider
        self.set_current_var_value(var_name, var_value)
        self.slider.setValue(var_value)

        # Flag when the end of one sweep is reached
        return (var_value == begin) or (var_value == end)


    def update(self, req):
        # Flag out for end of cycle
        endOfCycle = False
        # IDLE STATE; NO ANIMATION RUNNING
        if self.animation_state == self.AnimationState.IDLE:
            if req == self.AnimationRequest.START:
                self._init_animation()
                self.animation_state = self.AnimationState.RUNNING

        # RUNNING STATE
        elif self.animation_state == self.AnimationState.RUNNING:
            stop = (req == self.AnimationRequest.STOP)
            if not stop:
                endOfCycle = self._next_animation_step(self.reverse_animation)
            stop |= endOfCycle and not (self.pendulum_animation_radio.isChecked() or self.loop_animation_radio.isChecked())
            if stop:
                self.run_stop_button.setEnabled(True)
                # self.StopButton.setEnabled(False)
                self.animation_state = self.AnimationState.IDLE
            elif endOfCycle:
                if self.loop_animation_radio.isChecked():
                    self._init_animation()
                elif self.pendulum_animation_radio.isChecked():
                    self.reverse_animation = not self.reverse_animation

        # SANITY CHECK
        else:
            print("Unknown State/Transition")

        return endOfCycle


    def onTimerTick(self):
        try:
            self.update(self.AnimationRequest.NONE)
        except AnimationProvider.Error as e:
            self.timer_ms.stop()
            self.animation_state == self.AnimationState.IDLE
            QtGui.QMessageBox.warning(self.UI, e.short_msg, e.detail_msg)
        else:
            if self.force_render:
                Gui.updateGui()
            if self.animation_state == self.AnimationState.IDLE:
                self.timer_ms.stop()


    def set_current_var_value(self, name, value):

        setattr(self.target_var, name, value)

        if App.ActiveDocument == self.target_doc:
            if self.target_asm:
                self.target_asm.recompute(True)
        else:
            App.ActiveDocument.recompute(None, True, True)

        self.current_value_field.setValue(value)


    """
    +-----------------------------------------------+
    |            Loop or Pendulum Selector          |
    +-----------------------------------------------+
    """

    def _on_force_render_checked(self):
        self.force_render = self


    def _on_loop_checked(self):
        animation_hints = AnimationHints.get(self.target_var, self.var_combo.currentText())
        animation_hints[AnimationHints.Key.Loop] = self.loop_animation_radio.isChecked()
        # if self.pendulum_animation_radio.isChecked() and self.loop_animation_radio.isChecked():
            # self.pendulum_animation_radio.setChecked(False)


    def _on_pendulum_checked(self):
        animation_hints = AnimationHints.get(self.target_var, self.var_combo.currentText())
        animation_hints[AnimationHints.Key.Pendulum] = self.pendulum_animation_radio.isChecked()
        # if self.loop_animation_radio.isChecked() and self.pendulum_animation_radio.isChecked():
            # self.loop_animation_radio.setChecked(False)
        # return


    """
    +-----------------------------------------------+
    |                   Slider                      |
    +-----------------------------------------------+
    """
    def _on_slider_moved(self):
        var_name = self.var_combo.currentText()
        var_value = self.slider.value()
        self.set_current_var_value(var_name, var_value)
        return


    def _update_slider(self):

        initial_value = self.initial_value.value()
        final_value = self.final_value.value()

        # Update the slider's ranges
        # The slider will automatically settle to the nearest value possible based on the new begin/end/stepsize.
        self.slider.setRange(initial_value, final_value, self.step_value.value())

        # Update the labels with the actual range of the slider
        self.slider_left_value.setText(str(self.slider.leftValue()))
        self.slider_right_value.setText(str(self.slider.rightValue()))

        var_name = self.var_combo.currentText()
        current_value = self.target_var.getPropertyByName(var_name)
        slider_value = self.slider.value()
        if current_value != slider_value:
            self.set_current_var_value(var_name, slider_value)

        self._indicate_if_final_range_is_not_reachable(initial_value, final_value)


    def _indicate_if_final_range_is_not_reachable(self, initial_value, final_value):
        current_slider_right_value = self.slider.rightValue()
        is_increasing = initial_value < final_value
        is_current_range_short = (
            (is_increasing and current_slider_right_value < final_value) or
            (not is_increasing and current_slider_right_value > final_value)
        )
        self.slider_right_value.setStyleSheet("color: tomato" if is_current_range_short else "")


    def _on_initial_value_changed(self):
        var_name = self.var_combo.currentText()
        animation_hint = AnimationHints.get(self.target_var, var_name)
        animation_hint["rangeBegin"] = self.initial_value.value()
        self._update_slider()

    def _on_final_value_changed(self):
        var_name = self.var_combo.currentText()
        animation_hint = AnimationHints.get(self.target_var, var_name)
        animation_hint["rangeEnd"] = self.final_value.value()
        self._update_slider()

    def _on_step_size_changed(self):
        var_name = self.var_combo.currentText()
        animation_hint = AnimationHints.get(self.target_var, var_name)
        animation_hint["stepSize"] = self.step_value.value()
        self._update_slider()

    def _on_sleep_time_changed(self):
        var_name = self.var_combo.currentText()
        animation_hint = AnimationHints.get(self.target_var, var_name)
        step_time = self.step_time.value()
        animation_hint["sleepTime"] = self.timer_ms.setInterval(step_time * 1000)


    """
    +-----------------------------------------------+
    |                Star/Stop/Close/Export         |
    +-----------------------------------------------+
    """

    def _start_animation(self):
        self.animation_state = self.AnimationState.RUNNING
        try:
            self.update(self.AnimationRequest.START)
        except AnimationProvider.Error as e:
            QtGui.QMessageBox.warning(self.UI, e.short_msg, e.detail_msg)
        else:
            self.timer_ms.start()
        self.run_stop_button.setText("&Stop")
        self.run_stop_button.setChecked(False)


    def _stop_animation(self):
        self.animation_state = self.AnimationState.IDLE
        self.update(self.AnimationRequest.STOP)
        self.timer_ms.stop()
        self.run_stop_button.setText("&Run")
        self.run_stop_button.setChecked(False)


    def _on_run_stop_button(self):
        if self.animation_state == self.AnimationState.RUNNING:
            self.run_stop_button.setText("&Run")
            self.run_stop_button.setChecked(False)
            self._stop_animation()        
        else:
            self.run_stop_button.setText("&Stop")
            self.run_stop_button.setChecked(False)
            self._start_animation()


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self._on_close_button()
            self.UI.reject()
        else:
            # super(self.UI).keyPressEvent(event)
            event.ignore()

    def _on_close_button(self):
        self._stop_animation()
        AnimationHints.cleanUp(self.target_var)
        self.MDIArea.subWindowActivated[QtGui.QMdiSubWindow].disconnect(self.onDocChanged)
        self.UI.close()


    def _on_plot_button(self):
        self._stop_animation()
        # check whether a plotter window has been created before
        if not self.plotter:
            # Only import the export-lib if requested. Helps to keep WB loading times in check.
            from . import animation_plot_lib
            self.plotter = animation_plot_lib.AnimationPlotter(self)
        self.plotter.openUI()


    def _on_export_button(self):
        self._stop_animation()
        if not self.exporter:
            # Only import the export-lib if requested. Helps to keep WB loading times in check.
            from . import animation_export_lib
            self.exporter = animation_export_lib.animationExporter(self)
        self.exporter.openUI()


    def onDocChanged(self):
        if App.ActiveDocument != self.active_doc:
            # Check if target_document still exists
            if not self.target_doc in App.listDocuments().values():
                self.target_doc = None
            self._stop_animation()
            #self.Activated()


    #
    # AnimationProvider Interface
    #
    def nextFrame(self, resetAnimation) -> bool:
        req = AnimateVariable.AnimationRequest.START if resetAnimation else AnimateVariable.AnimationRequest.NONE

        endOfCycle = self.update(req)
        if endOfCycle:
            self.update(AnimateVariable.AnimationRequest.STOP)
        animationEnded = self.animation_state == AnimateVariable.AnimationState.IDLE

        return animationEnded


    def pendulumWanted(self) -> bool:
        return self.pendulum_animation_radio.isChecked()


    def drawUI(self):

        self.UI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.UI.setWindowTitle("Animate Assembly")
        self.UI.setWindowIcon(QtGui.QIcon(os.path.join(Asm4.iconPath, "FreeCad.svg")))
        self.UI.setMinimumWidth(450)
        self.UI.setModal(False)

        self.main_layout = QtGui.QVBoxLayout(self.UI)
        self.form_layout = QtGui.QFormLayout()

        # Document combo
        self.docs_combo = UpdatingComboBox()
        self.form_layout.addRow(QtGui.QLabel("Document"), self.docs_combo)

        # Assemblies combo
        self.assemblies_combo = UpdatingComboBox()
        self.form_layout.addRow(QtGui.QLabel("Assembly"), self.assemblies_combo)

        # Variables
        self.var_combo = UpdatingComboBox()
        self.form_layout.addRow(QtGui.QLabel("Variable"),self.var_combo)


        self.animation_settings_group = QtGui.QGroupBox()
        self.animation_settings_group_layout = QtGui.QFormLayout(self.animation_settings_group)

        self.initial_value = QtGui.QDoubleSpinBox()
        self.initial_value.setRange(float("-inf"), float("inf"))
        self.initial_value.setKeyboardTracking(False)
        self.animation_settings_group_layout.addRow(QtGui.QLabel("Initial value"), self.initial_value)

        # Maximum Range
        self.final_value = QtGui.QDoubleSpinBox()
        self.final_value.setRange(float("-inf"), float("inf"))
        self.final_value.setKeyboardTracking(False)
        self.animation_settings_group_layout.addRow(QtGui.QLabel("Final value"), self.final_value)

        # Step Size
        self.step_value = QtGui.QDoubleSpinBox()
        self.step_value.setRange(0.01, float("inf"))
        self.step_value.setValue(1.0)
        self.step_value.setKeyboardTracking(False)
        self.animation_settings_group_layout.addRow(QtGui.QLabel("Step size"), self.step_value)

        # Step Time
        self.step_time = QtGui.QDoubleSpinBox()
        self.step_time.setRange(0.0, 10.0)
        self.step_time.setValue(0.0)
        self.step_time.setSingleStep(0.01)
        self.step_time.setKeyboardTracking(False)
        self.animation_settings_group_layout.addRow(QtGui.QLabel("Step time (s)"), self.step_time)


        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.animation_settings_group)

        self.dummy_group = QtGui.QGroupBox()
        self.dummy_group_layout = QtGui.QFormLayout(self.dummy_group)
        self.dummy_group_layout.addRow(QtGui.QLabel(""))
        self.main_layout.addWidget(self.dummy_group)

        # Current Value
        self.form2_layout = QtGui.QFormLayout()
        # self.current_value_field = QtGui.QLineEdit()
        self.current_value_field = QtGui.QDoubleSpinBox()
        self.current_value_field.setRange(float("-inf"), float("inf"))
        self.current_value_field.setKeyboardTracking(False)
        self.current_value_field.setEnabled(False)
        self.form2_layout.addRow(QtGui.QLabel("Current value"), self.current_value_field)
        self.main_layout.addLayout(self.form2_layout)

        # Slider
        self.slider_layout = QtGui.QHBoxLayout()
        self.slider = AnimationSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10)
        self.slider.setTickInterval(0)
        self.slider_left_value = QtGui.QLabel("Begin")
        self.slider_right_value = QtGui.QLabel("End")
        tooltip = dedent("""
            The last reachable variable value with the given stepping.
            Flagged red in case this is not equal to the intended value.
            The last step of the animation will be reduced to stay inside the configured limits.
        """).strip()
        self.slider_right_value.setToolTip(tooltip)
        self.slider_layout.addWidget(self.slider_left_value)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.slider_right_value)

        self.main_layout.addLayout(self.slider_layout)



        # Force Render
        self.force_render_checkbox = QtGui.QCheckBox("Force render")
        self.force_render_checkbox.setToolTip("Force GUI to update on every step.")

        # Loop Animation
        self.loop_animation_radio = QtGui.QRadioButton("Loop Animation")
        # self.loop_animation_radio.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.loop_animation_radio.setToolTip("Animate it in an infinity loop.")
        # self.options_layout.addWidget(self.loop_animation_radio)
        # self.animation_mode_group.addButton(self.loop_animation_radio)

        # Pendulum Animation
        self.pendulum_animation_radio = QtGui.QRadioButton("Pendulum Animation")
        # self.pendulum_animation_radio.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pendulum_animation_radio.setToolTip("Back-and-forth pendulum anumation.")
        # self.options_layout.addWidget(self.pendulum_animation_radio)
        # self.animation_mode_group.addButton(self.pendulum_animation_radio)

        # add widgets in order
        self.main_layout.addWidget(self.force_render_checkbox)
        self.main_layout.addWidget(self.loop_animation_radio)
        self.main_layout.addWidget(self.pendulum_animation_radio)
        self.pendulum_animation_radio.setChecked(True)

        # (recommended) set radio exclusivity
        self.animation_mode_group = QtGui.QButtonGroup()
        self.animation_mode_group.addButton(self.loop_animation_radio)
        self.animation_mode_group.addButton(self.pendulum_animation_radio)



        self.button_layout = QtGui.QHBoxLayout()

        # Close button
        self.close_button = QtGui.QPushButton("&Close")
        self.button_layout.addWidget(self.close_button)
        self.close_shortcut = QtGui.QShortcut(QtGui.QKeySequence("C"), self.UI)
        self.close_shortcut.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.close_shortcut.activated.connect(self.close_button.click)

        # Plot button
        self.plot_button = QtGui.QPushButton("&Plot")
        self.plot_button.setToolTip("Plot trajectories of the animation.")
        self.button_layout.addWidget(self.plot_button)
        self.plot_shortcut = QtGui.QShortcut(QtGui.QKeySequence("P"), self.UI)
        self.plot_shortcut.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.plot_shortcut.activated.connect(self.plot_button.click)
        try:
            import cv2
        except:
            self.plot_button.setEnabled(False)
            tooltip = dedent(f"""
                Plot trajectories of the animation.
                Requires Python OpenCV (cv2)  it is not installed.
            """).strip()
            self.plot_button.setToolTip(tooltip)

        # Export button
        self.export_button = QtGui.QPushButton("&Export")
        self.export_button.setToolTip("Export the animation as a video.")
        self.button_layout.addWidget(self.export_button)
        self.export_shortcut = QtGui.QShortcut(QtGui.QKeySequence("E"), self.UI)
        self.export_shortcut.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.export_shortcut.activated.connect(self.export_button.click)
        try:
            import cv2
        except:
            self.export_button.setEnabled(False)
            tooltip = dedent(f"""
                Export the animation as a video.
                Requires Python OpenCV (cv2)  it is not installed.
            """).strip()
            self.export_button.setToolTip(tooltip)


        # Run/Stop button
        self.run_stop_button = QtGui.QPushButton("&Run")
        tooltip = dedent(f"""
            <p>
            Run the animation in the 3D window.
            If the model is large and complex it is advisable to try with 10 frames.
            </p>
        """).strip()
        self.run_stop_button.setToolTip(tooltip)
        self.button_layout.addWidget(self.run_stop_button)
        self.run_stop_shortcut = QtGui.QShortcut(QtGui.QKeySequence("R"), self.UI)
        self.run_stop_shortcut.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.run_stop_shortcut.activated.connect(self.run_stop_button.click)


        # Add an invisibly dummy button to circumvent QDialogs default-button behavior.
        # We need the enter key to trigger spinbox-commits only, without also triggering button actions.
        self.DummyButton = QtGui.QPushButton("Dummy")
        self.DummyButton.setDefault(True)
        self.DummyButton.setVisible(False)
        self.button_layout.addWidget(self.DummyButton)

        self.main_layout.addLayout(self.button_layout)

        # Actions
        self.docs_combo.popupList.connect(self._update_docs_list)
        self.docs_combo.currentIndexChanged.connect(self._on_select_doc)

        self.assemblies_combo.popupList.connect(self._update_assemblies_list)
        self.assemblies_combo.currentIndexChanged.connect(self._on_select_assembly)

        self.var_combo.popupList.connect(self._update_vars_list)
        self.var_combo.currentIndexChanged.connect(self._on_select_var)

        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.valueChanged.connect(self._on_slider_moved)

        self.initial_value.valueChanged.connect(self._on_initial_value_changed)
        self.final_value.valueChanged.connect(self._on_final_value_changed)
        self.step_value.valueChanged.connect(self._on_step_size_changed)
        self.step_time.valueChanged.connect(self._on_sleep_time_changed)

        self.force_render_checkbox.toggled.connect(self._on_force_render_checked)
        self.loop_animation_radio.toggled.connect(self._on_loop_checked)
        self.pendulum_animation_radio.toggled.connect(self._on_pendulum_checked)

        self.close_button.clicked.connect(self._on_close_button)
        self.plot_button.clicked.connect(self._on_plot_button)
        self.export_button.clicked.connect(self._on_export_button)
        self.run_stop_button.clicked.connect(self._on_run_stop_button)


    def _enable_widgets(self, state):
        self.initial_value.setEnabled(state)
        self.final_value.setEnabled(state)
        self.step_value.setEnabled(state)
        self.step_time.setEnabled(state)
        self.slider.setEnabled(state)
        self.loop_animation_radio.setEnabled(state)
        self.pendulum_animation_radio.setEnabled(state)
        try:
            import cv2
            self.plot_button.setEnabled(state)
            self.export_button.setEnabled(state)
        except:
            self.plot_button.setEnabled(False)
            self.export_button.setEnabled(False)
        self.run_stop_button.setEnabled(state)



class AnimationSlider(QtGui.QSlider):

    def __init__(self, parent=None):
        self.left_val = 0.0
        self.right_val = 1.0
        self.step_size = 1.0
        super().__init__(parent)


    def setRange(self, left_val, right_val, step_size=1.0):

        # All ranges will be mapped to positive whole numbers.
        # By definition, the "left hand side value" (begin range) will be reachable.
        # The last reachable "right hand side value" depends on the step-size
        # The functions below translate accordingly

        val = self.value()

        self.left_val = left_val
        self.right_val = right_val
        self.step_size = abs(step_size)
        if left_val > right_val:
            self.step_size *= -1.0

        super().setRange(0, (right_val - left_val) / self.step_size)

        # Ensure that the exposed slider value stays stable and gets capped if needed
        sign = self.step_size / abs(self.step_size)
        val = max(val, left_val * sign)
        val = min(val, right_val * sign)
        self.setValue(val)


    def __calculateInternalValue__(self, value):
        return value * self.step_size + self.left_val


    def value(self):
        return self.__calculateInternalValue__(super().value())


    def leftValue(self):
        return self.__calculateInternalValue__(super().minimum())


    def rightValue(self):
        return self.__calculateInternalValue__(super().maximum())


    def setValue(self, value):
        super().setValue((value - self.left_val) / self.step_size)



class UpdatingComboBox(QtGui.QComboBox):

    """
    Custom Combobox that emits a Signal when
    the user clicks for the popup menu.
    Needed to update the list of variables
    on the fly.
    """

    popupList = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def showPopup(self):
        self.popupList.emit()
        super().showPopup()



class AnimationHints():

    class Key:
        RangeBegin = "rangeBegin"
        RangeEnd = "rangeEnd"
        StepSize = "stepSize"
        SleepTime = "sleepTime"
        Loop = "loop"
        Pendulum = "pendulum"


    @staticmethod
    def get(variables, var_name):
        # Get the hints for the given variable.
        # Ensure that hints with sensible values are created in case there is no entry yet
        var_value = variables.getPropertyByName(var_name)

        defaultHints = {
            AnimationHints.Key.RangeBegin: var_value,
            AnimationHints.Key.RangeEnd: var_value,
            AnimationHints.Key.StepSize: 1.0,
            AnimationHints.Key.SleepTime: 0.0,
            AnimationHints.Key.Loop: False,
            AnimationHints.Key.Pendulum: False
        }

        hintList = AnimationHints.__getHintList__(variables)
        return hintList.setdefault(var_name, defaultHints)


    @staticmethod
    def __getHintList__(variables):
        # Ensure that a hint-dictionary is available and return it
        if "AnimationHintList" not in variables.PropertiesList:
            variables.addProperty("App::PropertyPythonObject", "AnimationHintList", "AnimationHints", "The hintfield for the animation dialog").AnimationHintList = {}
            variables.setPropertyStatus("AnimationHintList", "Hidden")
            # see https://forum.freecad.org/viewtopic.php?p=745163#p700080
            if variables.getPropertyByName("AnimationHintList") == None:
                variables.AnimationHintList = {}
        return variables.getPropertyByName("AnimationHintList")


    @staticmethod
    def cleanUp(variables):
        if not variables:
            return
        # Walk through all variable-entries and collect the relevant hints for them
        newHints = {}
        hintList = AnimationHints.__getHintList__(variables)
        for entry in variables.PropertiesList:
            if variables.getGroupOfProperty(entry) == "Variables":
                hint = hintList.get(entry, None)
                if hint:
                    newHints[entry] = hint
        # Throw old list away and use the new (possibly reduced) one
        setattr(variables, "AnimationHintList", newHints)



Gui.addCommand("Asm4_Animate", AnimateVariable())

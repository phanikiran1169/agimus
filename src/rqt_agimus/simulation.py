import rospy, tf2_ros
from tf_conversions import transformations
from python_qt_binding.QtCore import Qt
from python_qt_binding.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QWidget,
)
from qt_gui.plugin import Plugin
from geometry_msgs.msg import TransformStamped

class _TfFrameEditor (QWidget):
    def __init__ (self, tf_static_broadcast, parent_frame, child_frame, *args):
        super(_TfFrameEditor, self).__init__(*args)
        self.tf_static_broadcast = tf_static_broadcast

        self.msg = TransformStamped()
        self.msg.header.frame_id = parent_frame
        self.msg.child_frame_id = child_frame

        self.layout = QFormLayout (self)
        self.layout.addRow(QLabel("Static pose from {} to {}"
            .format(parent_frame, child_frame)))

        def wdgt(label, trans):
            import math
            sb = QDoubleSpinBox ()
            sb.setValue(0)
            m = 1e3 if trans else math.pi
            sb.setRange(-m, m)
            sb.setDecimals(4)
            sb.setSingleStep(1e-3 if trans else .05)
            sb.setSuffix(" m" if trans else " rad")
            self.layout.addRow(label, sb)
            sb.valueChanged.connect(self.valueChanged)
            return sb
        
        self.tx = wdgt("X"    , True)
        self.ty = wdgt("Y"    , True)
        self.tz = wdgt("Z"    , True)
        self.rr = wdgt("Roll" , False)
        self.rp = wdgt("Pitch", False)
        self.ry = wdgt("Yaw"  , False)
        self.valueChanged()

    def valueChanged (self):
        self.msg.header.stamp = rospy.Time.now()

        self.msg.transform.translation.x = self.tx.value()
        self.msg.transform.translation.y = self.ty.value()
        self.msg.transform.translation.z = self.tz.value()
        q = transformations.quaternion_from_euler(self.rr.value(), self.rp.value(), self.ry.value())
        self.msg.transform.rotation.x = q[0]
        self.msg.transform.rotation.y = q[1]
        self.msg.transform.rotation.z = q[2]
        self.msg.transform.rotation.w = q[3]

        self.tf_static_broadcast.sendTransform(self.msg)

## Tiny simulation UI
#
# To start the GUI, use
# \code
# rosrun rqt_gui rqt_gui --standalone rqt_agimus.simulation.Simulation --args <simulation_arguments>
# \endcode
# Use \c --help after \c --args to see the available arguments.
class Simulation(Plugin):
    def __init__(self, context):
        super(Simulation, self).__init__(context)
        # Give QObjects reasonable names
        self.setObjectName("AgimusSimulation")

        self._tfFrameEditors = []

        # Create QWidget
        self._widget = QWidget()
        self._layout = QVBoxLayout(self._widget)

        self.parseArguments (context)

        # Show _widget.windowTitle on left-top of each plugin (when
        # it's set in _widget). This is useful when you open multiple
        # plugins at once. Also if you open multiple instances of your
        # plugin at once, these lines add number to make it easy to
        # tell from pane to pane.
        if context.serial_number() > 1:
            self._widget.setWindowTitle(
                self._widget.windowTitle() + (" (%d)" % context.serial_number())
            )
        # Add widget to the user interface
        context.add_widget(self._widget)

    def parseArguments(self, context):
        # Process standalone plugin command-line arguments
        from argparse import ArgumentParser
        parser = ArgumentParser()
        # Add argument(s) to the parser.
        parser.add_argument("--tf-editor", type=str, nargs=2, action='append', dest="tf_editors",
                metavar=("parent_frame_id","child_frame_id"),
                help="Add a TF frame editor between the parent and child frame.")
        args, unknowns = parser.parse_known_args(context.argv())

        for parent, child in args.tf_editors:
            self.addTfFrameEditor (parent, child)

    def addTfFrameEditor (self, parent_frame, child_frame):
        if not hasattr(self, 'tf_static_broadcast'):
            self.tf_static_broadcast = tf2_ros.StaticTransformBroadcaster()
        editor = _TfFrameEditor (self.tf_static_broadcast, parent_frame, child_frame)
        self._layout.addWidget(editor)
        def space():
            spacer = QFrame()
            spacer.setFrameShape(QFrame.HLine)
            return spacer
        self._layout.addWidget(space())
        self._tfFrameEditors.append(editor)

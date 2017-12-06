#!/usr/bin/env python
# This code is a modification of the following code:
# https://github.com/cztomczak/cefpython/edit/master/examples/qt.py
import subprocess
from cefpython3 import cefpython as cef
import ctypes
import os
import platform
import sys
import PySide
from PySide import QtCore
from PySide.QtGui import *
from PySide.QtCore import *

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

# Configuration
WIDTH = 800
HEIGHT = 600

# OS differences
CefWidgetParent = QWidget
if LINUX:
    # noinspection PyUnresolvedReferences
    CefWidgetParent = QX11EmbedContainer

def main():
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    app = CefApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    main_window.activateWindow()
    main_window.raise_()
    app.exec_()
    app.stopTimer()
    del main_window  # Just to be safe, similarly to "del app"
    del app  # Must destroy app object before calling Shutdown
    cef.Shutdown()


def check_versions():
    print("[qt.py] CEF Python {ver}".format(ver=cef.__version__))
    print("[qt.py] Python {ver} {arch}".format(
            ver=platform.python_version(), arch=platform.architecture()[0]))
    print("[qt.py] PySide {v1} (qt {v2})".format(
        v1=PySide.__version__, v2=QtCore.__version__))
    # CEF Python version requirement
    assert cef.__version__ >= "55.4", "CEF Python v55.4+ required to run this"


class MainWindow(QMainWindow):
    def __init__(self):
        # noinspection PyArgumentList
        super(MainWindow, self).__init__(None)
        self.cef_widget = None
        self.setWindowTitle("SmartDholes")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setupLayout()

    def setupLayout(self):
        self.resize(WIDTH, HEIGHT)
        self.cef_widget = CefWidget(self)
        layout = QGridLayout()
        self.ActionsMenu = self.menuBar().addMenu("&Actions")
        self.AboutMenu = self.menuBar().addMenu("&About")
        self.ActionsMenu.addAction("New", self.New)
        self.ActionsMenu.addAction("Open", self.Open)
        self.AboutMenu.addAction("About", self.open_opengeostat_about)
        self.AboutMenu.addAction("OpenGeostat Website", self.open_opengeostat)
        self.AboutMenu.addAction("Contact", self.open_opengeostat_contact)
        self.AboutMenu.addAction("Facebok", self.open_facebook)
        self.AboutMenu.addAction("Twitter", self.open_twitter)
        self.AboutMenu.addAction("Google +", self.open_googleplus)
        self.AboutMenu.addAction("Youtube", self.open_youtube)
        self.AboutMenu.addAction("Linkedin", self.open_linkedin)
        self.AboutMenu.addAction("Github", self.open_github)
        # noinspection PyArgumentList
        layout.addWidget(self.cef_widget, 1, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)
        # noinspection PyArgumentList
        frame = QFrame()
        frame.setLayout(layout)
        self.setCentralWidget(frame)

        # Browser can be embedded only after layout was set up
        self.cef_widget.embedBrowser()

    def closeEvent(self, event):
        # Close browser (force=True) and free CEF reference
        if self.cef_widget.browser:
            self.cef_widget.browser.CloseBrowser(True)
            self.clear_browser_references()
    def open_external(self, link):
        if LINUX:
            with open(os.devnull, 'r+b', 0) as DEVNULL:
                p = subprocess.Popen(['xdg-open', link],
                      stdin=DEVNULL, stdout=DEVNULL, close_fds=True)

    def open_opengeostat(self):
        self.open_external("http://opengeostat.com/")
    def open_github(self):
        self.open_external("https://github.com/opengeostat/")
    def open_opengeostat_about(self):
        self.open_external("http://opengeostat.com/about-opengeostat/")
    def open_linkedin(self):
        self.open_external("https://www.linkedin.com/company/opengeostat")
    def open_facebook(self):
        self.open_external("https://www.facebook.com/opengeostat/")
    def open_youtube(self):
        self.open_external("https://www.youtube.com/channel/UCfo5QsMbHGgKW5lxsbWxvHg")
    def open_twitter(self):
        self.open_external("https://twitter.com/OpenGeostat")
    def open_googleplus (self):
        self.open_external("https://plus.google.com/+Opengeostat")
    def open_opengeostat_contact(self):
        self.open_external("http://opengeostat.com/contact/")

    def New(self):
        self.cef_widget.browser.LoadUrl("http://localhost:8000/new/")

    def Open(self):
        self.cef_widget.browser.LoadUrl("http://localhost:8000/open/")

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.cef_widget.browser = None


class CefWidget(CefWidgetParent):
    def __init__(self, parent=None):
        # noinspection PyArgumentList
        super(CefWidget, self).__init__(parent)
        self.parent = parent
        self.browser = None
        self.hidden_window = None  # Required for PyQt5 on Linux
        self.show()

    def focusInEvent(self, event):
        # This event seems to never get called on Linux, as CEF is
        # stealing all focus due to Issue #284.
        if self.browser:
            if WINDOWS:
                WindowUtils.OnSetFocus(self.getHandle(), 0, 0, 0)
            self.browser.SetFocus(True)

    def focusOutEvent(self, event):
        # This event seems to never get called on Linux, as CEF is
        # stealing all focus due to Issue #284.
        if self.browser:
            self.browser.SetFocus(False)

    def embedBrowser(self):
        window_info = cef.WindowInfo()
        rect = [0, 0, self.width(), self.height()]
        window_info.SetAsChild(self.getHandle(), rect)
        self.browser = cef.CreateBrowserSync(window_info,
                                             url="http://localhost:8000/desktop/") # open the desktop version
        self.browser.SetClientHandler(FocusHandler(self))

    def getHandle(self):
        if self.hidden_window:
            # PyQt5 on Linux
            return int(self.hidden_window.winId())
        try:
            # PyQt4 and PyQt5
            return int(self.winId())
        except:
            # PySide:
            # | QWidget.winId() returns <PyCObject object at 0x02FD8788>
            # | Converting it to int using ctypes.
            if sys.version_info[0] == 2:
                # Python 2
                ctypes.pythonapi.PyCObject_AsVoidPtr.restype = (
                        ctypes.c_void_p)
                ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = (
                        [ctypes.py_object])
                return ctypes.pythonapi.PyCObject_AsVoidPtr(self.winId())
            else:
                # Python 3
                ctypes.pythonapi.PyCapsule_GetPointer.restype = (
                        ctypes.c_void_p)
                ctypes.pythonapi.PyCapsule_GetPointer.argtypes = (
                        [ctypes.py_object])
                return ctypes.pythonapi.PyCapsule_GetPointer(
                        self.winId(), None)

    def moveEvent(self, _):
        self.x = 0
        self.y = 0
        if self.browser:
            if WINDOWS:
                WindowUtils.OnSize(self.getHandle(), 0, 0, 0)
            elif LINUX:
                self.browser.SetBounds(self.x, self.y,
                                       self.width(), self.height())
            self.browser.NotifyMoveOrResizeStarted()

    def resizeEvent(self, event):
        size = event.size()
        if self.browser:
            if WINDOWS:
                WindowUtils.OnSize(self.getHandle(), 0, 0, 0)
            elif LINUX:
                self.browser.SetBounds(self.x, self.y,
                                       size.width(), size.height())
            self.browser.NotifyMoveOrResizeStarted()


class CefApplication(QApplication):
    def __init__(self, args):
        super(CefApplication, self).__init__(args)
        self.timer = self.createTimer()
        self.setupIcon()

    def createTimer(self):
        timer = QTimer()
        # noinspection PyUnresolvedReferences
        timer.timeout.connect(self.onTimer)
        timer.start(10)
        return timer

    def onTimer(self):
        cef.MessageLoopWork()

    def stopTimer(self):
        # Stop the timer after Qt's message loop has ended
        self.timer.stop()

    def setupIcon(self):
        icon_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 "resources", "{0}.png".format("none"))
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))


class LoadHandler(object):
    def __init__(self):
        self.initial_app_loading = True

    def OnLoadStart(self, browser, **_):
        if self.initial_app_loading:\
            # Temporary fix no. 2 for focus issue on Linux (Issue #284)
            if LINUX:
                print("[qt.py] LoadHandler.OnLoadStart:"
                      " keyboard focus fix no. 2 (Issue #284)")
                browser.SetFocus(True)
            self.initial_app_loading = False


class FocusHandler(object):
    def __init__(self, cef_widget):
        self.cef_widget = cef_widget

    def OnSetFocus(self, **_):
        pass

    def OnGotFocus(self, browser, **_):
        # Temporary fix no. 1 for focus issues on Linux (Issue #284)
        if LINUX:
            print("[qt.py] FocusHandler.OnGotFocus:"
                  " keyboard focus fix no. 1 (Issue #284)")
            browser.SetFocus(True)

if __name__ == '__main__':
    main()

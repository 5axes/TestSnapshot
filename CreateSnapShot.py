# Copyright (c) 2020
# The SimpleShapes plugin is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QBuffer
from PyQt5 import QtCore


from UM.Extension import Extension
from cura.CuraApplication import CuraApplication

from typing import List

from UM.Application import Application
from UM.Logger import Logger
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType

from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread
from UM.Scene.Camera import Camera
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator


from UM.Message import Message

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class CreateSnapShot(Extension, QObject,):
    

    def __init__(self, parent = None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)

        # attention pas le même nom que le menu
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Snap"), self.doExtendedCreatePics)
        
        self._snapshot = None
       
 
    def doExtendedCreatePics(self):
        PngFile="C:/temp/thumbnail.png"
        self._write(PngFile)
        self._message = Message(catalog.i18nc("@info:status", "Creating .PNG file : %s" % (PngFile)), title = catalog.i18nc("@title", "SNAPSHOT"))
        self._message.show()
        
    def _createSnapshot(self, *args):
        # must be called from the main thread because of OpenGL
        Logger.log("d", "Creating thumbnail image...")
        scene = CuraApplication.getInstance().getController().getScene()
        active_camera = scene.getActiveCamera()
        render_width, render_height = active_camera.getWindowSize()
        Logger.log("d", "Creating thumbnail image Size : %d %d" % (render_width, render_height) )
        try:
            self._snapshot = Snapshot.snapshot(width = 300, height = 300)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")
            self._snapshot = None
            
    @call_on_qt_thread
    def _write(self, Filename: str):

        self._createSnapshot()

        #Store the thumbnail.
        if self._snapshot:
            self._snapshot.save(Filename)
            Logger.log("d", "Thumbnail creation")
            
        else:
            Logger.log("d", "Thumbnail not created, cannot save it")
            

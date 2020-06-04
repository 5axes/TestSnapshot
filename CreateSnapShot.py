# Copyright (c) 2020
# The SimpleShapes plugin is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QBuffer
from PyQt5.QtCore import QIODevice
from PyQt5 import QtCore
from PyQt5.QtGui import QImage

from UM.Extension import Extension
from cura.CuraApplication import CuraApplication
#from cura.Utils.Threading import call_on_qt_thread

import threading

#from cura.Snapshot import Snapshot
from .Snapshot import Snapshot

from UM.Logger import Logger
from UM.Message import Message

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


#
# HACK:
#
# In project loading, when override the existing machine is selected, the stacks and containers that are correctly
# active in the system will be overridden at runtime. Because the project loading is done in a different thread than
# the Qt thread, something else can kick in the middle of the process. One of them is the rendering. It will access
# the current stacks and container, which have not completely been updated yet, so Cura will crash in this case.
#
# This "@call_on_qt_thread" decorator makes sure that a function will always be called on the Qt thread (blocking).
# It can be guaranteed that only after the process is completely done, everything else that needs to occupy the QT thread will be executed.
#
class InterCallObject:
    def __init__(self):
        self.finish_event = threading.Event()
        self.result = None


def call_on_qt_thread(func):
    def _call_on_qt_thread_wrapper(*args, **kwargs):
        def _handle_call(ico, *args, **kwargs):
            ico.result = func(*args, **kwargs)
            ico.finish_event.set()
        
        inter_call_object = InterCallObject()
        new_args = tuple([inter_call_object] + list(args)[:])
        Logger.log("d", "new_args = %s", new_args)
        CuraApplication.getInstance().callLater(_handle_call, *new_args, **kwargs)
        inter_call_object.finish_event.wait()
        return inter_call_object.result
    return _call_on_qt_thread_wrapper
    
    
class CreateSnapShot(Extension):
    

    def __init__(self) -> None:
        # super().__init__()
        # QObject.__init__(self, parent)
        Extension.__init__(self)
        # self._application = CuraApplication.getInstance()

        # attention pas le même nom que le menu
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Snap"), self.doExtendedCreatePics)
        
        #self._snapshot = None
       

    def doExtendedCreatePics(self):
        PngFile="C:/temp/thumbnail.png"
        self._write(PngFile)
        self._message = Message(catalog.i18nc("@info:status", "Creating .PNG file : %s" % (PngFile)), title = catalog.i18nc("@title", "SNAPSHOT"))
        self._message.show()
    
    @call_on_qt_thread  
    def _get_snapshot_image(self, width, height) -> QImage:

        # must be called from the main thread because of OpenGL
        try:
            Logger.log("d", "snapshot = %d / %d", width, height)        
            return Snapshot.snapshot(width = width, height = height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")

        return None

  
    def _write(self, Filename: str):


        self._snapshot = self._get_snapshot_image(300, 300)

        #Store the thumbnail.
        if self._snapshot:
            ba = QtCore.QByteArray()
            thumbnail_buffer = QBuffer(ba)
            thumbnail_buffer.open(QIODevice.WriteOnly)
            image_quality=90
            image_format = "b'png'"
            self._snapshot.save(thumbnail_buffer, image_format, image_quality)
            self._snapshot.save(Filename)
            Logger.log("d", "Thumbnail creation")
            
        else:
            Logger.log("d", "Thumbnail not created, cannot save it")
            

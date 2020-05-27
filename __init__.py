# Copyright (c) 2020 5axes
# The SnapShot plugin is released under the terms of the AGPLv3 or higher.

from . import CreateSnapShot

def getMetaData():
    return {}

def register(app):
    return {"extension": CreateSnapShot.CreateSnapShot()}

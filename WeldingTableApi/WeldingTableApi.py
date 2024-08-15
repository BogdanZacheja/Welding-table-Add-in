# Assuming you have not changed the general structure of the template no modification is needed in this file.
from . import commands
from .lib import fusion360utils as futil
import adsk.core, adsk.fusion, adsk.cam, traceback


def run(context):
    try:
        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.start()

        app = adsk.core.Application.get()
        design = app.activeProduct
        unitsMgr = design.unitsManager
        unitsMgr.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        
        ui = app.userInterface
        ui.messageBox('Units have been set to millimeters.')

    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()

    except:
        futil.handle_error('stop')
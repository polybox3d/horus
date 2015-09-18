# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2015 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import logging
import logging.handlers

# Logger set up
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("horus_logger")
logger.setLevel(logging.DEBUG)
rot_handler = logging.handlers.RotatingFileHandler("horus_log.log", maxBytes=1 * 1024 * 1024, backupCount=0)
rot_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
rot_handler.setLevel(logging.INFO)
logger.addHandler(rot_handler)

try:
    import os
    import wx
    import cv2
    import OpenGL
    import serial
    import numpy
    import scipy
    import matplotlib
except:
    logger.exception("Error when importing modules.")
    exit(1)

from horus.util import resources
resources.setBasePath(os.path.join(os.path.dirname(__file__), "../res"))

from horus.gui import app


def main():
    app.HorusApp().MainLoop()

if __name__ == '__main__':
    main()

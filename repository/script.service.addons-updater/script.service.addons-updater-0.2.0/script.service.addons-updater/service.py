# service.py - starting point of the addon

import xbmc
import xbmcaddon
import sys
import os

this_addon = xbmcaddon.Addon()
addon_path = this_addon.getAddonInfo("path")
sys.path.append(xbmc.translatePath(os.path.join(addon_path, "resources", "lib")))

import addons_updater

addons_updater.run()
# common.py - common functions

import xbmc
import xbmcaddon
import sqlite3
import os


this_addon = xbmcaddon.Addon()
addonID = this_addon.getAddonInfo("id")


def error(message):
    """
    Opens notification window with error message
    :param: message: str - error message
    :return: None
    """
    notify("Error:," + message)


def info(message):
    """
    Opens info windows with message
    :param: message: str - message
    :return: None
    """

    notify("Info:," + message)


def notify(message):
    """
    Opens notification window with message
    :param: message: str - message
    :return: None
    """
    icon = ""  # os.path.join(addonFolder, "icon.png")
    xbmc.executebuiltin(unicode('XBMC.Notification(' + message + ',3000,' + icon + ')').encode("utf-8"))


def debug(content):
    """
    Outputs content to log file
    :param content: content which should be output
    :return: None
    """
    if type(content) is str:
        message = unicode(content, "utf-8")
    else:
        message = content
    log(message, xbmc.LOGDEBUG)


def log_exception(content):
    """
    Outputs content to log file
    :param content: content which should be output
    :return: None
    """

    if type(content) is str:
        message = unicode(content, "utf-8")
    else:
        message = content
    log(message, xbmc.LOGERROR)


def log(msg, level=xbmc.LOGNOTICE):
    """
    Outputs message to log file
    :param msg: message to output
    :param level: debug levelxbmc. Values:
    xbmc.LOGDEBUG = 0
    xbmc.LOGERROR = 4
    xbmc.LOGFATAL = 6
    xbmc.LOGINFO = 1
    xbmc.LOGNONE = 7
    xbmc.LOGNOTICE = 2
    xbmc.LOGSEVERE = 5
    xbmc.LOGWARNING = 3
    """

    log_message = u'{0}: {1}'.format(addonID, msg)
    xbmc.log(log_message.encode("utf-8"), level)


def get_db(db_name):
    """
    Gets connection to database
    :param db_name: name of database
    :return:
    """

    userdata_folder = xbmc.translatePath("special://userdata")
    addon_data_folder = os.path.join(userdata_folder, "addon_data", addonID)
    if not os.path.exists(addon_data_folder):
        os.makedirs(addon_data_folder)
    database_file = os.path.join(addon_data_folder, db_name)
    return sqlite3.connect(database_file)
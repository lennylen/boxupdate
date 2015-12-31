# userdata_files.py - module for updating userdata files from server


import xbmc
import xbmcaddon
import sys
import urllib2
from common import *
import xml.etree.ElementTree as ET
import os
from urlparse import urljoin
from urllib import urlretrieve

xbmcbackup_addon = xbmcaddon.Addon("script.xbmcbackup")
xbmcbackup_addon_path = xbmcbackup_addon.getAddonInfo("path")
sys.path.insert(0, xbmc.translatePath(xbmcbackup_addon_path))

import resources.lib.guisettings as guisettings


def update_userdata_files():
    """
    Updates userdata files from server
    :return: None
    """

    files_list = get_files_from_server()
    for server_file in files_list:
        filename = server_file.get("name")
        version = server_file.get("version")
        if need_update_file(filename, version):
            result = update_file(filename, version)
            if result:
                info(filename + " updated")


def get_files_from_server():
    """
    Gets the list of files from server
    :return: list of dictionaries like {"name": "name", "version": "version"}
    """

    result = []
    files_list_path = this_addon.getSetting("files_list_path")
    try:
        data = urllib2.urlopen(files_list_path)
    except Exception, e:
        log_exception(str(e))
        error("Couldn't get userdata files list from server")
        return result
    try:
        tree = ET.parse(data)
    except Exception, e:
        log_exception(str(e))
        error("Couldn't parse userdata files list")
        return []
    root = tree.getroot()
    for child in root:
        result.append(child.attrib)
    return result


def need_update_file(filename, version):
    """
    Checks if the file needs to be updated from server
    :param filename: str - name of file
    :param version: str - version of file on server
    :return: bool. True - if file needs to be updated, False - otherwise
    """

    userdata_folder = xbmc.translatePath("special://userdata")
    full_filename = os.path.join(userdata_folder, filename)
    if not os.path.exists(full_filename):
        return True
    local_version = get_file_version(filename)
    return version != local_version


def get_file_version(filename):
    """
    Gets local file version
    :param: filename: str - name of file
    :return: str
    """

    db = get_db("files_versions.db")
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='files_versions';")
    if cursor.fetchone():
        cursor.execute("SELECT version FROM files_versions "
                       "WHERE filename = '" + filename + "'")
        res = cursor.fetchone()
        if res:
            return res[0]
        else:
            return ""
    else:
        return ""


def update_file(filename, version):
    """
    Updates file
    :param filename: str - name of file
    :param version: str - new version of file from server
    :return: bool - True - if file successfully updated, False - otherwise
    """

    files_path = this_addon.getSetting("files_path")
    url = urljoin(files_path, filename)
    userdata_folder = xbmc.translatePath("special://userdata")
    full_filename = os.path.join(userdata_folder, filename)
    try:
        urlretrieve(url, full_filename)
    except Exception, e:
        log_exception(str(e))
        error("Couln't get file " + filename + " from server")
        return False

    if filename == "guisettings.xml":
        update_guisettings("special://userdata/guisettings.xml")

    update_file_version(filename, version)

    return True


def update_guisettings(from_file="special://userdata/guisettings.xml"):
    """
    Updates settings in guisettings.xml from server
    :return: None
    """

    manager = guisettings.GuiSettingsManager(from_file)
    manager.run()
    update_skin_settings(from_file)


def update_skin_settings(from_file="special://userdata/guisettings.xml"):
    """
    Updates skins settings in guisettings.xml from server
    :return: None
    """

    current_skin_id = xbmc.getSkinDir()
    debug("Current skin: " + current_skin_id)
    current_skin_id_len = len(current_skin_id)
    full_path = xbmc.translatePath(from_file)
    if not os.path.exists(full_path):
        return
    try:
        tree = ET.parse(full_path)
    except Exception, e:
        log_exception(str(e))
        return
    root = tree.getroot()
    for child in root:
        if child.tag == "skinsettings":
            debug("skinsettings")
            for setting in child:
                setting_name = setting.attrib.get("name", "")
                debug("setting_name: " + setting_name)
                setting_name_len = len(setting_name)
                if setting_name_len > (current_skin_id_len + 1):
                    # first part of setting name - is the id of current skin
                    debug("setting_name_len > cur_skin_id_len")
                    if setting_name[0:current_skin_id_len + 1] == (current_skin_id + "."):
                        setting_id = setting_name[current_skin_id_len + 1:]
                        setting_type = setting.attrib.get("type")
                        if setting_type == "string":
                            setting_value = setting.text
                            if not setting_value:
                                setting_value = ""
                            command = "Skin.SetString({0},{1})".format(setting_id,
                                                                       setting_value)
                            debug(command)
                            xbmc.executebuiltin(command)
                        elif setting_type == "bool":
                            setting_value = setting.text
                            if setting_value == "true":
                                command = "Skin.SetBool({0})".format(setting_id)
                            else:
                                command = "Skin.Reset({0})".format(setting_id)
                            xbmc.executebuiltin(command)


def update_file_version(filename, version):
    """
    Updates file version in local database
    :param filename: str - name of the file
    :param version: str - new version (from server)
    :return: None
    """

    db = get_db("files_versions.db")
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='files_versions';")
    if not cursor.fetchone():
        cursor.execute("CREATE TABLE files_versions "
                       "(filename text, version text)")
    cursor.execute("DELETE FROM files_versions "
                   "WHERE filename ='" + filename + "'")
    cursor.execute("INSERT INTO files_versions "
                   "VALUES ('" + filename + "','" + version + "')")
    db.commit()
    db.close()


def delete_guisettings_restored():
    path = xbmc.translatePath("special://userdata/guisettings.xml.restored")
    if os.path.exists(path):
        os.remove(path)
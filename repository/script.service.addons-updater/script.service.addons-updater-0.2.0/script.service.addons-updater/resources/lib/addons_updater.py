# addons_updater.py - main module of the addon


import xbmc
import xbmcaddon
import urllib2
import xml.etree.ElementTree as ET
from urlparse import urljoin
import os
import cStringIO
import zipfile
import contextlib
from common import *
from userdata_files import update_userdata_files, update_skin_settings, delete_guisettings_restored
import shutil

def run():
    """
    Run the service
    :return: None
    """

    enabled = (this_addon.getSetting("enabled") == "true")
    if not enabled:
        return

    #update_skin_settings("special://userdata/guisettings.xml.restored")
    delete_guisettings_restored()

    addons_list = get_addons_list()

    for server_addon in addons_list:
        server_addon_id = server_addon["id"]
        need_delete_addon = server_addon.get("delete", "false")
        if need_delete_addon == "true":
            if delete_addon(server_addon_id):
                info(server_addon_id + " uninstalled")
        else:
            success = False
            server_version = server_addon["version"]
            install = need_install(server_addon_id,
                                   check_version=True,
                                   version=server_version)
            if install:
                if install_addon(server_addon_id,
                                 official_repo=False):
                    success = True
                    debug(server_addon_id + ": update installed.")
            update_data = need_update_addon_data(server_addon)
            if update_data:
                if update_addon_data(server_addon):
                    success = True
                    debug(server_addon_id + ": addon data updated.")
            if success:
                name = get_addon_name(server_addon_id)
                info(name + " updated")

    update_userdata_files()


def get_addons_list():
    """
    Gets addons list from the server
    :return: list. Elements of list - dictionaries
    """

    result = []
    addons_list_path = this_addon.getSetting("list_path")
    try:
        data = urllib2.urlopen(addons_list_path)
    except Exception, e:
        error("Couldn't get addons list")
        log_exception(str(e))
        return result
    try:
        tree = ET.parse(data)
    except Exception, e:
        error("Couldn't parse addons list")
        log_exception(str(e))
        return result

    root = tree.getroot()
    for child in root:
        result.append(child.attrib)

    return result


def need_install(id, check_version=False, version=""):
    """
    Checks if addon needs to be installed
    :param id: str - server addon id
    :param check_version: bool
    :param version: str
    :return: bool
    :rtype: bool
    """

    standard_modules = ["xbmc.python"]
    if id in standard_modules:
        return False
    already_installed = xbmc.getCondVisibility("System.HasAddon(" + id + ")")
    if not already_installed:
        return True
    if check_version:
        local_addon = xbmcaddon.Addon(id)
        local_version = local_addon.getAddonInfo("version")
        return local_version != version
    else:
        return False


def install_addon(id, official_repo=False):
    """
    Installs addon with given id
    :param id: str - addon id
    :param official_repo: bool
    :param version: str
    :return: bool. True - if success, False - otherwise
    """

    if official_repo:
        data = get_addon_from_official_repo(id)
    else:
        data = get_addon_from_server(id)

    if data is None:
        return False

    home_root = xbmc.translatePath("special://home")
    addons_folder = os.path.join(home_root, "addons")
    buf = cStringIO.StringIO(data.read())
    with contextlib.closing(zipfile.ZipFile(buf, "r")) as addon_zip:
        addon_zip.extractall(addons_folder)

    xbmc.executebuiltin("UpdateLocalAddons()")
    # xbmc.executebuiltin("UpdateAddonRepos()")

    return install_dependencies(id)


def get_addon_from_server(id):
    """
    Gets addon from our server
    :param id: str - id of the addon
    :return: file-like object with addon data or None (if error)
    """

    # local_addon_folder = os.path.join(addons_folder, id)
    # if not os.path.exists(local_addon_folder):
    #     os.makedirs(local_addon_folder)
    files_path = this_addon.getSetting("addons_path")
    url = urljoin(files_path, id + ".zip")
    debug(url)

    try:
        data = urllib2.urlopen(url)
    except Exception, e:
        error("Couldn't get addon " + id + " file")
        log_exception(str(e))
        return None
    return data


def get_addon_from_official_repo(id):
    """
    Gets addon from official Kodi repo
    :param id: str - addon id
    :return:
    """

    data = None
    repo_list = ["jarvis", "isengard", "helix", "gotham"]  # Kodi 16, 15, 14 and 13
    for repo in repo_list:
        #url = "http://mirrors.kodi.tv/addons/" + repo + "/" + id + "/" + id + "-" + version + ".zip"
        url = "http://mirrors.kodi.tv/addons/" + repo + "/addons.xml"
        debug(url)
        try:
            addons_list = urllib2.urlopen(url)
        except Exception:
            continue
        try:
            tree = ET.parse(addons_list)
        except Exception:
            continue
        root = tree.getroot()
        # won't work on Python 2.6
        # addon_node = root.find("addon[@id='" + id + "']")
        addons_nodes = root.findall("addon")
        for addon_node in addons_nodes:
            if addon_node.attrib.get("id") == id:
                version = addon_node.attrib["version"]
                url = "http://mirrors.kodi.tv/addons/" + repo + "/" + id + "/" + id + "-" + version + ".zip"
                debug(url)
                try:
                    data = urllib2.urlopen(url)
                except Exception:
                    continue
                return data
    if data is None:
        error("Couldn't get addon " + id + " file")
    return data


def install_dependencies(id):
    """
    Installs addon dependencies from official Kodi repository
    :param id: str - id of the addon
    :return: bool. True - if successful, False - otherwise.
    """

    #local_addon = xbmcaddon.Addon(id)
    home_folder = xbmc.translatePath("special://home")
    addon_folder = os.path.join(home_folder, "addons", id)
    #addon_folder = local_addon.getAddonInfo("path")
    addon_file = os.path.join(addon_folder, "addon.xml")
    try:
        tree = ET.parse(addon_file)
    except Exception, e:
        error("Couldn't parse " + id + " addon file")
        log_exception(str(e))
        return False
    root = tree.getroot()
    for child in root:
        if child.tag == "requires":
            for import_node in child:
                dependency_id = import_node.attrib["addon"]
                #dependency_version = import_node.attrib["version"]
                if need_install(dependency_id, check_version=False):
                    result = install_addon(dependency_id,
                                           official_repo=True)
                    if not result:
                        return False
    return True


def need_update_addon_data(server_addon):
    """
    Checks if addon data needs to be updated
    :param server_addon: dictionary: {"id": "id",
                                "version": "version"}
    :return: bool
    """

    if server_addon.get("addon_data", "") != "enabled":
        return False
    server_data_version = server_addon["data_version"]
    addon_id = server_addon["id"]
    local_data_version = get_data_version(addon_id)
    return server_data_version != local_data_version


def get_data_version(addon_id):
    """
    Gets local addon data version
    :param addon_id: str - id of the addon
    :return: str - data version
    """

    db = get_db("data_versions.db")
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='data_versions';")
    if cursor.fetchone():
        cursor.execute("SELECT version FROM data_versions "
                       "WHERE id = '" + addon_id + "'")
        res = cursor.fetchone()
        if res:
            return res[0]
        else:
            return ""
    else:
        return ""


def update_addon_data(server_addon):
    """
    Updates addon data folder from server
    :param server_addon: dictionary: {"id": id, "data_version": data_version"}
    :return: bool. True - if success, False - otherwise
    """

    addon_id = server_addon["id"]
    server_data_path = this_addon.getSetting("addons_data_path")
    url = urljoin(server_data_path, addon_id + ".zip")
    try:
        data = urllib2.urlopen(url)
    except Exception, e:
        error("Couldn't download addon data")
        log_exception(str(e))
        return False

    buf = cStringIO.StringIO(data.read())
    with contextlib.closing(zipfile.ZipFile(buf, "r")) as addon_data_zip:
        names_list = addon_data_zip.namelist()
        stop_list = [addon_id]
        stop_list.append(os.path.join(addon_id, ""))
        userdata_folder = xbmc.translatePath("special://userdata")
        addon_data_folder = os.path.join(userdata_folder, "addon_data")
        for member in names_list:
            if member not in stop_list:
                addon_data_zip.extract(member, addon_data_folder)
    new_data_version = server_addon["data_version"]
    update_addon_data_version(addon_id, new_data_version)

    return True


def update_addon_data_version(addon_id, new_version):
    """
    Updates addon data version in db
    :param addon_id: str - addon id
    :param new_version: srt - new version number
    :return: None
    """

    db = get_db("data_versions.db")
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='data_versions';")
    if not cursor.fetchone():
        cursor.execute("CREATE TABLE data_versions "
                       "(id text, version text)")
    cursor.execute("DELETE FROM data_versions "
                   "WHERE id ='" + addon_id + "'")
    cursor.execute("INSERT INTO data_versions "
                   "VALUES ('" + addon_id + "','" + new_version + "')")
    db.commit()
    db.close()


def delete_addon_data_version(addon_id):
    """
    Deletes addon data version in db
    :param addon_id: str - id of the addon
    :return:
    """

    db = get_db("data_versions.db")
    cursor = db.cursor()
    cursor.execute("DELETE FROM data_versions "
                   "WHERE id = '" + addon_id + "'")
    db.commit()
    db.close()


def get_addon_name(id):
    """
    Gets addon name
    :param id: str
    :return: str - addon name
    """
    try:
        local_addon = xbmcaddon.Addon(id)
        name = local_addon.getAddonInfo("name")
        return name
    except Exception, e:
        log_exception(str(e))
        home_folder = xbmc.translatePath("special://home")
        addon_folder = os.path.join(home_folder, "addons", id)
        addon_file = os.path.join(addon_folder, "addon.xml")
        try:
            tree = ET.parse(addon_file)
        except Exception, e:
            log_exception(str(e))
            return id
        root = tree.getroot()
        return root.attrib["name"]


def delete_addon(id):
    """
    Deletes addon with given id
    :param id: str - id of the addon
    :return: bool - True - if addon was successfully uninstalled,
        False - if not
    """

    success = False
    addons_path = xbmc.translatePath("special://home/addons")
    addon_folder = os.path.join(addons_path, id)
    if os.path.exists(addon_folder):
        shutil.rmtree(addon_folder)
        success = True
        xbmc.executebuiltin("UpdateLocalAddons()")
    addondata_path = xbmc.translatePath("special://userdata/addon_data")
    addon_data_folder = os.path.join(addondata_path, id)
    if os.path.exists(addon_data_folder):
        shutil.rmtree(addon_data_folder)
        success = True
    delete_addon_data_version(id)
    return success

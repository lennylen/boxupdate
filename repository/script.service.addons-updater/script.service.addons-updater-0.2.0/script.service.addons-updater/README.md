# Addons Updater
Kodi service for updating addons and its data  
##0. Abstract
Kodi has powerful repository system, that allows automatic plugin updating. But sometimes there is a need to:  
- Install new addons automatically;  
- Change some addons data (in special://userdata/addon_data folder);  
- Change files in userdata folder.  
Addons Updater enhances repository system and helps to download, install and update addons and its data from our server  

##1. Configuration  
1.1 Put on server:  
1.1.1 File addons.xml - [see example](https://github.com/kharts/addons-updater-test/blob/master/addons.xml). It contains list of all addons, its current version number and data version number  
1.1.2 Folder, which must contain .zip files of all addons listed in addons.xml (Addons folder). Each file should be named as id of plugin.  
Example: "script.renegadestv.zip"  
1.1.3 Folder, which must contain .zip files of all addon_data folders of all addons, listed in addons.xml (Addons data folder). Name of files - identically to files in addons folder (ie "script.renegadestv.zip")  
1.1.4 File files.xml - [see example] (https://github.com/kharts/addons-updater-test/blob/master/files.xml). It contains list of userdata files to be updated from server  
1.1.5 Folder with userdata files  
1.2 Before installing addon:  
1.2.1 Unzip file script.service.addons-updater.zip  
1.2.3 Open resources/settings.xml file, and change default values ("default"=...) of the following settings:  
1.2.3.1 "list_path" - path to addons.xml on server (see 1.1.1)  
1.2.3.2 "addons_path" - path to addons folder (1.1.2)  
1.2.3.3 "addons_data_path" - path to addons data folder (1.1.3)  
1.2.3.4 "files_list_path" - path to filex.xml on server (see 1.1.4)  
1.2.3.5 "files_path" - path to folder with userdata files on server (see 1.1.5)  
1.2.4 Repack it back to script.service.addons-updater.zip  
##2. Installation  
2.1 Open Kodi  
2.2 Open System - Settings - Addons - Install from zip file - Choose file from 1.2.4  
2.3 Addon will be installed. By default it is started every time Kodi is started.  
##3. Testing  
For testing you can change content of files inside addons/addons data folder and respectively version/data_version number in addons.xml and restart Kodi. If version number is changed, notification will be shown.
##4. Additional information
4.1 Data version number for every addon from addons.xml is stored in local SQLite database  
4.2 Addon can be turned off - there is setting "Enabled" - if False, it won't be started. It can be done by user inside Kodi.  
4.3 As Kodi doesn't allow to change guisettings.xml file while its running, 'XBMC Backup' addon is used for restoring guisettings  

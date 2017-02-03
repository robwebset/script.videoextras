# -*- coding: utf-8 -*-
import os
import traceback
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import datetime

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import os_path_join

ADDON = xbmcaddon.Addon(id='script.videoextras')
CWD = ADDON.getAddonInfo('path').decode("utf-8")
RES_DIR = xbmc.translatePath(os.path.join(CWD, 'resources').encode("utf-8")).decode("utf-8")


# Ideally we would use an XML parser to do this like ElementTree
# However they all end up re-ordering the attributes, so doing a diff
# between changed files is very hard, so for this reason we do it
# all manually without the aid of an XML parser
class EstuaryUpdate():
    def __init__(self):
        # Find out where the confluence skin files are located
        confAddon = xbmcaddon.Addon(id='skin.estuary')
        self.confpath = xbmc.translatePath(confAddon.getAddonInfo('path'))
        self.confpath = os_path_join(self.confpath, 'xml')
        log("Estuary Location: %s" % self.confpath)
        # Create the timestamp centrally, as we want all files changed for a single
        # run to have the same backup timestamp so it can be easily undone if the
        # user wishes to switch it back
        self.bak_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.errorToLog = False

    # Method to update all of the required Confluence files
    def updateSkin(self):
        # Update the files one at a time
        self._updateDialogVideoInfo()

        # Now either print the complete message or the "check log" message
        if self.errorToLog:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32157), ADDON.getLocalizedString(32152))
        else:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32162), ADDON.getLocalizedString(32159))

    # Save the new contents, taking a backup of the old file
    def _saveNewFile(self, dialogXml, dialogXmlStr):
        log("SaveNewFile: New file content: %s" % dialogXmlStr)

        # Now save the file to disk, start by backing up the old file
        xbmcvfs.copy(dialogXml, "%s.videoextras-%s.bak" % (dialogXml, self.bak_timestamp))

        # Now save the new file
        dialogXmlFile = xbmcvfs.File(dialogXml, 'w')
        dialogXmlFile.write(dialogXmlStr)
        dialogXmlFile.close()

    ##########################################################################
    # UPDATES FOR DialogVideoInfo.xml
    ##########################################################################
    # Makes all the required changes to DialogVideoInfo.xml
    def _updateDialogVideoInfo(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.confpath, 'DialogVideoInfo.xml')
        log("DialogVideoInfo: Estuary dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("DialogVideoInfo: Unable to find the file DialogVideoInfo.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the DialogVideoInfo.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        # Now check to see if the skin file has already had the video extras bits added
        if 'script.videoextras' in dialogXmlStr:
            # Already have video extras referenced, so we do not want to do anything else
            # to this file
            log("DialogVideoInfo: Video extras already referenced in %s, skipping file" % dialogXml, xbmc.LOGINFO)
            self.errorToLog = True
            return

        # Start by adding the onLoad section
        previousOnLoad = '<controls>'

        if previousOnLoad not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("DialogVideoInfo: Could not find controls command, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the Video Extras onLoad command after the allowoverlay one
        DIALOG_VIDEO_INFO_ONLOAD = '<onload condition="System.HasAddon(script.videoextras)">RunScript(script.videoextras,check,"$INFO[ListItem.FilenameAndPath]")</onload>\n\t'
        insertTxt = DIALOG_VIDEO_INFO_ONLOAD + previousOnLoad
        dialogXmlStr = dialogXmlStr.replace(previousOnLoad, insertTxt)

        # Now we need to add the button after the Final button
        previousButton = '<param name="label" value="$LOCALIZE[208]" />'

        if previousButton not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("DialogVideoInfo: Could not find play button, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Check to make sure we use a unique ID value for the button
        idOK = False
        idval = 200
        while not idOK:
            idStr = '<param name="id" value="%d"' % idval
            if idStr not in dialogXmlStr:
                idOK = True
            else:
                idval = idval + 1

        # Now add the Video Extras button after the Play one
        DIALOG_VIDEO_INFO_BUTTON = '''\n\t\t\t\t\t</include>\n\t\t\t\t\t<include content="InfoDialogButton">
\t\t\t\t\t\t<param name="id" value="%d" />
\t\t\t\t\t\t<param name="icon" value="special://masterprofile/../addons/script.videoextras/resources/skins/icons/overlay3.png" />
\t\t\t\t\t\t<param name="label" value="$ADDON[script.videoextras 32001]" />
\t\t\t\t\t\t<param name="onclick_1" value="Action(close)" />
\t\t\t\t\t\t<param name="onclick_2" value="RunScript(script.videoextras,display,$INFO[ListItem.FilenameAndPath])" />
\t\t\t\t\t\t<param name="visible" value="System.HasAddon(script.videoextras) + [String.IsEqual(ListItem.DBType,movie) | String.IsEqual(ListItem.DBType,tvshow) | String.IsEqual(ListItem.DBType,season) | String.IsEqual(ListItem.DBType,episode)] + IsEmpty(Window(movieinformation).Property(HideVideoExtrasButton))" />'''

        insertTxt = previousButton + (DIALOG_VIDEO_INFO_BUTTON % idval)
        dialogXmlStr = dialogXmlStr.replace(previousButton, insertTxt)

        self._saveNewFile(dialogXml, dialogXmlStr)


#########################
# Main
#########################
if __name__ == '__main__':
    log("VideoExtras: Updating Estuary Skin (version %s)" % ADDON.getAddonInfo('version'))

    doUpdate = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32163))

    if doUpdate:
        try:
            estuaryUp = EstuaryUpdate()
            estuaryUp.updateSkin()
            del estuaryUp
        except:
            log("VideoExtras: %s" % traceback.format_exc(), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32164), ADDON.getLocalizedString(32152))

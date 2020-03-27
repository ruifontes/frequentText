#-*- coding: utf-8 -*-
# Part of frequentText add-on for NVDA.
# written by Rui Fontes <rui.fontes@tiflotecnia.com>

import os
import globalVars
import addonHandler

def onInstall():
	configFilePath = os.path.abspath(os.path.join(globalVars.appArgs.configPath, "addons", "frequentText", "globalPlugins", "frequentText", "frequentText.ini"))
	if os.path.isfile(configFilePath):	
		os.remove(os.path.abspath(os.path.join(globalVars.appArgs.configPath, "addons", "frequentText" + addonHandler.ADDON_PENDINGINSTALL_SUFFIX, "globalPlugins", "frequentText", "frequentText.ini")))
		os.rename(configFilePath, os.path.abspath(os.path.join(globalVars.appArgs.configPath, "addons", "frequentText" + addonHandler.ADDON_PENDINGINSTALL_SUFFIX, "globalPlugins", "frequentText", "frequentText.ini")))

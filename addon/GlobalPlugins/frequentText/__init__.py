#-*- coding: utf-8 -*-
# frequentText add-on for NVDA.
# written by Rui Fontes <rui.fontes@tiflotecnia.com> and Ângelo Abrantes <ampa4374@gmail.com>
# Regists, manage and allow to paste  frequently used blocks of text
# Shortcut: WINDOWS+F12

import os
import gui
import wx
import api
from keyboardHandler import KeyboardInputGesture
from configobj import ConfigObj
import time
import watchdog
import globalPluginHandler
from scriptHandler import script
import addonHandler
addonHandler.initTranslation()
import ui

# for the auto update process
import globalVars
import winsound
from threading import Thread
from time import sleep
import speech
import urllib.request
import json
import config
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from gui import guiHelper, nvdaControls
import core
import socket
import shutil
import sys

# Global vars
_ffIniFile = os.path.join(os.path.dirname(__file__), "frequentText.ini")
Catg = ""
dictBlocks = {}
defCatg = ""

# for the auto update process
def initConfiguration():
	confspec = {
		"isUpgrade": "boolean(default=False)",
	}
	config.conf.spec["FrequentText"] = confspec

def getConfig(key):
	value = config.conf["FrequentText"][key]
	return value

def setConfig(key, value):
	try:
		config.conf.profiles[0]["FrequentText"][key] = value
	except:
		config.conf["FrequentText"][key] = value

initConfiguration()
tempPropiedad = getConfig("isUpgrade")
IS_WinON = False
ID_TRUE = wx.NewIdRef()
ID_FALSE = wx.NewIdRef()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		self.dialog = None
		# for the auto update process
		NVDASettingsDialog.categoryClasses.append(FrequentTextPanel)
		self._MainWindows = HiloComplemento(1)
		self._MainWindows.start()
		self.messageObj = None
		self.x = 0

	def readConfig(self):
		global Catg
		if not os.path.isfile(_ffIniFile):
			return None
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		blocks = config[Catg]
		total = len(blocks.keys())
		if not total:
			return None
		if not len(blocks.keys()):
			blocks = None
		return blocks

	@script(
	# For translators: Message to be announced during Keyboard Help
	description = _("Opens a dialog box to registe, manage and paste frequent blocks of text."),
	# For translators: Name of the section in "Input gestures" dialog.
	category = _("Text editing"),
	gesture = "kb:WINDOWS+f12",
	allowInSleepMode = True)
	def script_startFrequentText(self, gesture):
		self.showFrequentTextCatgsDialog(self)

	def showFrequentTextCatgsDialog (self, listCatgs):
		# Displays the categories list dialog box.
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		listCatgs = config.keys()
		# Translators: Title of categories list dialog box.
		self.dialog = FrequentTextCatgsDialog(gui.mainFrame, _("Frequent text"), listCatgs)
		self.dialog.updateCatgs(listCatgs, 0)

		if not self.dialog.IsShown():
			gui.mainFrame.prePopup()
			self.dialog.Show()
			self.dialog.CentreOnScreen()
			gui.mainFrame.postPopup()

	def showFrequentTextDialog(self, dictBlocks):
		# Displays the blocks list dialog box.
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		dictBlocks = config[Catg]
		# Translators: Title of Blocks list dialog boxes.
		self.dialog = FrequentTextDialog(gui.mainFrame, _("Frequent text"), dictBlocks)
		self.dialog.updateBlocks(dictBlocks, 0)

		if not self.dialog.IsShown():
			gui.mainFrame.prePopup()
			self.dialog.Show()
			self.dialog.CentreOnScreen()
			gui.mainFrame.postPopup()

	@script(
	# For translators: Message to be announced during Keyboard Help
	description = _("Opens a dialog box with the text blocks of first or default category"),
	# For translators: Name of the section in "Input gestures" dialog.
	category = _("Text editing"),
	gesture = "kb:Control+WINDOWS+f12",
	allowInSleepMode = True)
	def script_startFrequentTextDefault(self, gesture):
		global Catg, defCatg
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		listCatgs = config.keys()
		if defCatg == "":
			Catg = listCatgs[0]
		else:
			Catg = defCatg
		self.showFrequentTextDialog(self)

	def terminate (self):
		if self.dialog is not None:
			self.dialog.Destroy()


class FrequentTextCatgsDialog(wx.Dialog):

	def __init__(self, parent, title, listCatgs):
		self.title = title
		self.listCatgs = listCatgs
		self.dialogActive = False
		super(FrequentTextCatgsDialog, self).__init__(parent, title=title)
		# Create interface
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		tasksSizer = wx.BoxSizer(wx.VERTICAL)
		tasksSizer1 = wx.BoxSizer(wx.VERTICAL)
		# Create a label and a list view for categories list.
		# Label is above the list view.
		# Translators: Label the list view that contains the categories
		tasksLabel = wx.StaticText(self, -1, label = _("Categories list"))
		tasksSizer.Add(tasksLabel)

		# create a list view.
		self.listBoxCatgs = wx.ListCtrl(self, size=(800, 250), style = wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SORT_ASCENDING)
		tasksSizer.Add(self.listBoxCatgs, proportion=8)

		# Create buttons.
		# Buttons are in a horizontal row
		buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)

		showButtonID = wx.Window.NewControlId()
		# Translators: Button Label to show the entries in the selected category
		self.showButton = wx.Button(self, showButtonID, _("&Show entries"))
		buttonsSizer.Add (self.showButton)

		addButtonID = wx.Window.NewControlId()
		# Translators: Button Label to add a new category
		self.addButton = wx.Button(self, addButtonID, _("&Add"))
		buttonsSizer.Add (self.addButton)

		renameButtonID = wx.Window.NewControlId()
		# Translators: Button Label that renames the name of the selected block.
		self.renameButton = wx.Button(self, renameButtonID, _("Re&name"))
		buttonsSizer.Add (self.renameButton)

		setAsDefaultButtonID = wx.Window.NewControlId()
		# Translators: Button Label to set the selected category as default
		self.setAsDefaultButton = wx.Button(self, setAsDefaultButtonID, _("Set &category as default"))
		buttonsSizer.Add (self.setAsDefaultButton)

		removeButtonID = wx.Window.NewControlId()
		# Translators: Button Label that removes the selected block.
		self.removeButton = wx.Button (self, removeButtonID, _("&Remove"))
		buttonsSizer.Add (self.removeButton)

		# Translators: Button Label that closes the add-on.
		cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Close"))
		buttonsSizer.Add(cancelButton)

		if len(self.listCatgs) == 0:
			buttonsSizer.Hide(self.showButton)
			buttonsSizer.Hide(self.renameButton)
			buttonsSizer.Hide(self.setAsDefaultButton)
			buttonsSizer.Hide(self.removeButton)

		tasksSizer.Add(buttonsSizer)
		mainSizer.Add(tasksSizer)

		# Bind the buttons.
		self.Bind(wx.EVT_BUTTON, self.onShow, id = showButtonID)
		self.Bind(wx.EVT_BUTTON, self.onAdd, id = addButtonID)
		self.Bind(wx.EVT_BUTTON, self.onRename, id = renameButtonID)
		self.Bind(wx.EVT_BUTTON, self.onSetAsDefault, id = setAsDefaultButtonID)
		self.Bind(wx.EVT_BUTTON, self.onRemove, id = removeButtonID)
		self.listBoxCatgs.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)

	def onAdd (self, evt):
		# Add a new category
		evt.Skip()
		# Translators: Message dialog box to add a name to a new category
		dlg = wx.TextEntryDialog(gui.mainFrame, _("Enter a name for the category"), self.title)
		dlg.SetValue("")
		if dlg.ShowModal() == wx.ID_OK:
			nameCatg = dlg.GetValue()
			nameCatg = nameCatg.upper()

			if nameCatg != "":
				if self.listBoxCatgs.FindItem (0, nameCatg) != -1:
					# Translators: Announcement that the category name already exists in the list.
					gui.messageBox (_("There is already a category with this name!"), self.title)
					self.onAdd(evt)
					return
				else:
					#Saving the category
					config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
					config[nameCatg] = {}
					config.write()
					# Puts the focus on the inserted category
					listCatgs = config.keys()
					self.updateCatgs(listCatgs, 0)
					idx = self.listBoxCatgs.FindItem(0, nameCatg)
					self.listBoxCatgs.Focus(idx)
					self.listBoxCatgs.Select(idx)
					self.listBoxCatgs.SetFocus()
					# Redraw the dialog box to adapt the buttons
					if len(listCatgs) == 1:
						self.Close()
						GlobalPlugin.showFrequentTextCatgsDialog(self, listCatgs)
					return
		else:
			dlg.Destroy()

	def onRename(self, evt):
		# Renames the selected category
		evt.Skip()
		index = self.listBoxCatgs.GetFocusedItem()
		nameCatg = self.listBoxCatgs.GetItemText(index)
		self.dialogActive = True
		# Translators: Message dialog to rename the category
		newKeyCatg = wx.GetTextFromUser(_("Enter a new name for %s") %nameCatg, self.title).strip().upper()
		if  newKeyCatg != "":
			if self.listBoxCatgs.FindItem(0, newKeyCatg) == -1:
				# update the dictionaries
				config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
				config.rename(nameCatg, newKeyCatg)
				config.write()
				self.listCatgs = config.keys()
				listCatgs = config.keys()
				# update the list view.
				self.updateCatgs(listCatgs, index)
				idx = self.listBoxCatgs.FindItem(0, newKeyCatg)
				self.listBoxCatgs.Focus(idx)
				self.listBoxCatgs.Select(idx)
				self.listBoxCatgs.SetFocus()
				return

			else:
				gui.messageBox (_("There is already a category with this name!"), self.title)
		self.dialogActive = False

	def onSetAsDefault(self, evt):
		# Set the selected category as default
		evt.Skip()
		global defCatg, listCatgs
		index = self.listBoxCatgs.GetFocusedItem()
		defCatg = self.listBoxCatgs.GetItemText(index)
		self.listBoxCatgs.Focus(index)
		self.listBoxCatgs.Select(index)
		self.listBoxCatgs.SetFocus()

	def onRemove (self, evt):
		# Removes the selected category
		evt.Skip()
		index = self.listBoxCatgs.GetFocusedItem()
		nameCatg = self.listBoxCatgs.GetItemText(index)
		self.dialogActive = True
		# Translators: Message dialog box to remove the selected category
		if gui.messageBox(_("Are you sure you want to remove %s?") %nameCatg, self.title, style=wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
			config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
			config.__delitem__(nameCatg)
			config.write()
			self.listBoxCatgs.DeleteItem(index)
			if self.listBoxCatgs.GetItemCount():
				self.listBoxCatgs.Select(self.listBoxCatgs.GetFocusedItem())
				self.dialogActive = False
				self.listBoxCatgs.SetFocus()
				return
			else:
				self.Close()
				GlobalPlugin.showFrequentTextCatgsDialog(self, self.listCatgs)

	def onKeyPress(self, evt):
		# Sets enter key  to show the entries and delete to remove it.
		evt.Skip()
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_RETURN and self.listBoxCatgs.GetItemCount():
			self.onShow(evt)
		elif keycode == wx.WXK_RETURN and not self.listBoxCatgs.GetItemCount():
			self.onAdd(evt)
		elif keycode == wx.WXK_DELETE and self.listBoxCatgs.GetItemCount():
			self.onRemove(evt)

	def onShow(self, evt):
		global Catg
		index = self.listBoxCatgs.GetFocusedItem()
		Catg = self.listBoxCatgs.GetItemText(index)
		self.Close()
		GlobalPlugin.showFrequentTextDialog(self, dictBlocks)
		return

	def updateCatgs(self, listCatgs, index):
		config = ConfigObj(_ffIniFile, list_values = True)
		listCatgs = config.keys()
		self.listBoxCatgs.ClearAll()
		# Translators: Title of the column of the list view.
		self.listBoxCatgs.InsertColumn(0, _("Name"))
		self.listBoxCatgs.SetColumnWidth (0,250)
		if listCatgs == None:
			return
		x = 0
		while  x <= len(listCatgs)-1:
			listCatgs[x]
			self.listBoxCatgs.Append([listCatgs[x]])
			x = x+1
		self.listBoxCatgs.Select(0)
		self.listBoxCatgs.Focus(0)


class FrequentTextDialog(wx.Dialog):

	def __init__(self, parent, title, dictBlocks):
		self.title = title
		self.dictBlocks = dictBlocks
		self.dialogActive = False
		super(FrequentTextDialog, self).__init__(parent, title=title)
		# Create interface
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		tasksSizer = wx.BoxSizer(wx.VERTICAL)
		tasksSizer1 = wx.BoxSizer(wx.VERTICAL)
		# Create a label and a list view for Frequent Text list.
		# Label is above the list view.
		# Translators: Label the list view that contains the Blocks.
		tasksLabel = wx.StaticText(self, -1, label = _("List of text blocks of %s category") %Catg)
		tasksSizer.Add(tasksLabel)

		# create a list view.
		self.listBox = wx.ListCtrl(self, size=(800, 250), style = wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SORT_ASCENDING)
		tasksSizer.Add(self.listBox, proportion=8)

		# Create buttons.
		# Buttons are in a horizontal row
		buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)

		addButtonID = wx.Window.NewControlId()
		# Translators: Button Label to add a new block.
		self.addButton = wx.Button(self, addButtonID, _("&Add"))
		buttonsSizer.Add (self.addButton)

		pasteButtonID = wx.Window.NewControlId()
		# Translators: Button Label that paste the block to the edit box.
		self.pasteButton = wx.Button (self, pasteButtonID, _("&Paste"))
		buttonsSizer.Add(self.pasteButton)

		renameButtonID = wx.Window.NewControlId()
		# Translators: Button Label that renames the name of the selected block.
		self.renameButton = wx.Button(self, renameButtonID, _("Re&name"))
		buttonsSizer.Add (self.renameButton)

		changeButtonID = wx.Window.NewControlId()
		# Translators: Button Label that change the blocks of text.
		self.changeButton = wx.Button(self, changeButtonID, _("&Change blocks"))
		buttonsSizer.Add (self.changeButton)

		moveButtonID = wx.Window.NewControlId()
		# Translators: Label  for btton to move the selected block to other category.
		self.moveButton = wx.Button (self, moveButtonID, _("&Move"))
		buttonsSizer.Add (self.moveButton)

		removeButtonID = wx.Window.NewControlId()
		# Translators: Button Label that removes the selected block.
		self.removeButton = wx.Button (self, removeButtonID, _("&Remove"))
		buttonsSizer.Add (self.removeButton)

		goBackButtonID = wx.Window.NewControlId()
		# Translators: Label  for button to go back to categories list.
		self.goBackButton = wx.Button (self, goBackButtonID, _("&Back to categories"))
		buttonsSizer.Add (self.goBackButton)

		# Translators: Button Label that closes the add-on.
		cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Close"))
		buttonsSizer.Add(cancelButton)

		if len(dictBlocks) == 0:
			buttonsSizer.Hide(self.pasteButton)
			buttonsSizer.Hide(self.renameButton)
			buttonsSizer.Hide(self.changeButton)
			buttonsSizer.Hide(self.moveButton)
			buttonsSizer.Hide(self.removeButton)

		tasksSizer.Add(buttonsSizer)
		mainSizer.Add(tasksSizer)

		# Bind the buttons.
		self.Bind(wx.EVT_BUTTON, self.onAdd, id = addButtonID)
		self.Bind (wx.EVT_BUTTON, self.onPaste, id = pasteButtonID )
		self.Bind(wx.EVT_BUTTON, self.onRename, id = renameButtonID)
		self.Bind(wx.EVT_BUTTON, self.onChangeBlocks, id = changeButtonID)
		self.Bind(wx.EVT_BUTTON, self.onMove, id = moveButtonID)
		self.Bind(wx.EVT_BUTTON, self.onRemove, id = removeButtonID)
		self.Bind(wx.EVT_BUTTON, self.goBack, id = goBackButtonID)
		self.listBox.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)

	def onAdd (self, evt):
		# Add a new block of text.
		evt.Skip()
		# Translators: Message dialog box to add a name to a new block.
		dlg = wx.TextEntryDialog(gui.mainFrame, _("Enter a name for the block"), self.title)
		dlg.SetValue("")
		if dlg.ShowModal() == wx.ID_OK:
			name = dlg.GetValue()
			name = name.upper()

			if name != "":
				if self.listBox.FindItem (0, name) != -1:
					# Translators: Announcement that the block name already exists in the list.
					gui.messageBox (_("There is already a block with this name!"), self.title)
					self.onAdd(evt)
					return
				else:
					self._addBlock(name)	
		else:
			dlg.Destroy()

	def _addBlock(self, name):
		# Translators: Message dialog box to add a new block of text.
		dlg = wx.TextEntryDialog(gui.mainFrame, _("Enter the block of text"), self.title, style = wx.OK | wx.CANCEL | wx.TE_MULTILINE)
		dlg.SetValue("")
		if dlg.ShowModal() == wx.ID_OK:
			nBlock = dlg.GetValue()
		else:
			dlg.Destroy()
			return
		if nBlock != "":
			newBlock = nBlock.split("\n")
		else:
			dlg.Destroy()
			return

		# Saving the block
		config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
		if Catg in config.sections:
			blocks = config[Catg]
			blocks.__setitem__(name, newBlock)
		else:
			config[Catg] = {name:newBlock}
		config.write()
		self.listBox.Append([name])
		newIndex = self.listBox.FindItem(0,name)
		# Puts the focus on the inserted block.
		self.listBox.Focus (newIndex)
		self.listBox.Select(newIndex)
		self.listBox.SetFocus()
		# Redraw the dialog box to adapt the buttons
		self.Close()
		GlobalPlugin.showFrequentTextDialog(self, dictBlocks)
		return

	def onPaste (self, evt):
		# Simulates typing the block of text in the edit area.
		self.Hide()
		evt.Skip()
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		blocks = config[Catg]
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		paste = blocks[name]
		pasteStr = "\r\n".join(paste)
		if len(paste) >= 2:
			pasteStr += "\r\n"
		try:
			clipboardBackup = api.getClipData()
		except OSError:
			api.copyToClip(pasteStr)
			time.sleep(0.1)
			api.processPendingEvents(False)
			focus = api.getFocusObject()
			if focus.windowClassName == "ConsoleWindowClass":
				# Windows console window - Control+V doesn't work here, so using an alternative method here
				WM_COMMAND = 0x0111
				watchdog.cancellableSendMessage(focus.windowHandle, WM_COMMAND, 0xfff1, 0)
			else:
				KeyboardInputGesture.fromName("Control+v").send()
		else:
			api.copyToClip(pasteStr)
			time.sleep(0.1)
			api.processPendingEvents(False)
			focus = api.getFocusObject()
			if focus.windowClassName == "ConsoleWindowClass":
				# Windows console window - Control+V doesn't work here, so using an alternative method here
				WM_COMMAND = 0x0111
				watchdog.cancellableSendMessage(focus.windowHandle, WM_COMMAND, 0xfff1, 0)
			else:
				KeyboardInputGesture.fromName("Control+v").send()
			core.callLater(300, lambda: api.copyToClip(clipboardBackup))

	def onRename(self, evt):
		# Renames the selected block.
		evt.Skip()
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		self.dialogActive = True
		# Translators: Message dialog to rename the block of text.
		newKey = wx.GetTextFromUser(_("Enter a new name for %s") %name, self.title).strip().upper()
		if newKey != "":
			if self.listBox.FindItem(0, newKey) == -1:
				config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
				blocks = config[Catg]
				paste = blocks[name]
				# update the dictionary.
				blocks.rename(name, newKey)
				config.write()

				# update the list view.
				keys = blocks.keys()
				keys.sort()
				newIndex = keys.index (newKey)
				self.updateBlocks (blocks, newIndex)
				self.listBox.SetFocus()

			else:
				gui.messageBox (_("There is already a block with this name!"), self.title)
		self.dialogActive = False

	def onChangeBlocks(self, evt):
		evt.Skip()
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
		blocks = config[Catg]
		paste = blocks[name]
		oldBlock = ""
		for x in range(len(paste)):
			oldBlock += ("%s \n")%paste[x]
			x = x+1
		self.dialogActive = True

		# Translators: Message dialog box to change a block of text.
		dlg = wx.TextEntryDialog(gui.mainFrame, _("Change the block of text as you want and press Tab to Ok button and Enter to confirm"), self.title, style = wx.OK | wx.CANCEL | wx.TE_MULTILINE)
		dlg.SetValue(oldBlock)
		if dlg.ShowModal() == wx.ID_OK:
			nBlock = dlg.GetValue()
		else:
			dlg.Destroy()
			return

		if nBlock != "":
			changeBlock = nBlock.split("\n")
		else:
			dlg.Destroy()
			return

		# update the dictionary.
		blocks.__delitem__(name)
		blocks.__setitem__(name, changeBlock)
		config.write()

		# update the list view.
		keys = blocks.keys()
		keys.sort()
		newIndex = keys.index (name)
		self.updateBlocks (blocks, newIndex)
		self.listBox.SetFocus()

	def onMove (self, evt):
		# Moves the selected block to other category.
		evt.Skip()
		config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		blocks = config[Catg]
		textBlock = blocks[name]
		self.dialogActive = True
		# Translators: Message dialog box to move the selected block to other category.
		newCatg = wx.GetTextFromUser(_("If you really want to move %s from %s category, enter the name of the new, already existing, category") %(name, Catg), self.title).strip().upper()
		if newCatg != "":
			listCatgs = config.keys()
			if str(newCatg) in listCatgs:
				blocks = config[newCatg]
				blocks.__setitem__ (name, textBlock)
				blocks = config[Catg]
				blocks.__delitem__(name)
				config.write()
				self.listBox.DeleteItem(index)
				if self.listBox.GetItemCount():
					self.listBox.Select(self.listBox.GetFocusedItem())
				self.dialogActive = False
				self.listBox.SetFocus()
			else:
				# Translators: Announcement that the category does not exists.
				gui.messageBox (_("There is no such category!"), self.title)
				self.onMove(evt)
		else:
			self.onMove()
		# Redraw the dialog box to adapt the buttons
		self.Close()
		GlobalPlugin.showFrequentTextDialog(self, dictBlocks)

	def onRemove (self, evt):
		# Removes the selected block.
		evt.Skip()
		self.removeItem()

	def removeItem (self):
		# Removes the selected block.
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		self.dialogActive = True
		# Translators: Message dialog box to remove the selected block.
		if gui.messageBox(_("Are you sure you want to remove %s?") %name, self.title, style=wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
			config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
			blocks = config[Catg]
			blocks.__delitem__(name)
			config.write()
			self.listBox.DeleteItem(index)
			if self.listBox.GetItemCount():
				self.listBox.Select(self.listBox.GetFocusedItem())
		self.dialogActive = False
		self.listBox.SetFocus()
		# Redraw the dialog box to adapt the buttons
		self.Close()
		GlobalPlugin.showFrequentTextDialog(self, dictBlocks)

	def goBack(self, evt):
		# Returns to categories list dialog
		evt.Skip()
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		listCatgs = config.keys()
		self.Close()
		GlobalPlugin.showFrequentTextCatgsDialog(self, listCatgs)

	def onKeyPress(self, evt):
		# Sets enter key  to paste the text and delete to remove it.
		evt.Skip()
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_RETURN and self.listBox.GetItemCount():
			self.onPaste(evt)
		elif keycode == wx.WXK_RETURN and not self.listBox.GetItemCount():
			self.onAdd(evt)
		elif keycode == wx.WXK_DELETE and self.listBox.GetItemCount():
			self.removeItem()

	def updateBlocks(self, dictBlocks, index):
		self.listBox.ClearAll()
		# Translators: Title of the column of the list view.
		self.listBox.InsertColumn(0, _("Name"))
		self.listBox.SetColumnWidth (0,250)
		if dictBlocks == None:
			return
		keys = dictBlocks.keys()
		keys.sort()
		for item in keys:
			k = item
			self.listBox.Append ([k])
		self.listBox.Focus(index)
		self.listBox.Select(index)


# for the auto update process
class FrequentTextPanel(SettingsPanel):
	title = _("Frequent text")

	def makeSettings(self, sizer):
		helper=guiHelper.BoxSizerHelper(self, sizer=sizer)
		# Translators: Checkbox name in the configuration dialog
		self.FreqTxtChk = helper.addItem(wx.CheckBox(self, label=_("Check for updates at startup")))
		self.FreqTxtChk.Bind(wx.EVT_CHECKBOX, self.onChk)

		self.FreqTxtChk.Value = tempPropiedad

	def onSave(self):
		setConfig("isUpgrade", self.FreqTxtChk.Value)

	def onChk(self, event):
		global tempPropiedad
		tempPropiedad = self.FreqTxtChk.Value


class HiloComplemento(Thread):
	def __init__(self, opcion):
		super(HiloComplemento, self).__init__()
		self.opcion = opcion
		self.daemon = True

	def run(self):
		def upgradeVerify():
			if IS_WinON == False:
				if tempPropiedad == True:
					p = urllib.request.Request("https://api.github.com/repos/ruifontes/frequentText/releases")
					r = urllib.request.urlopen(p).read()
					githubApi = json.loads(r.decode('utf-8'))
					for addon in addonHandler.getAvailableAddons():
						if addon.manifest['name'] == "frequentText":
							installedVersion = addon.manifest['version']
							if githubApi[0]["tag_name"] != installedVersion:
								self._MainWindows = UpdateDialog(gui.mainFrame)
								gui.mainFrame.prePopup()
								self._MainWindows.Show()

		def startUpgrade():
			if IS_WinON == False:
				self._MainWindows = ActualizacionDialogo(gui.mainFrame)
				gui.mainFrame.prePopup()
				self._MainWindows.Show()

		if self.opcion == 1:
			wx.CallAfter(upgradeVerify)
		elif self.opcion == 2:
			wx.CallAfter(startUpgrade)

class HiloActualizacion(Thread):
	def __init__(self, frame):
		super(HiloActualizacion, self).__init__()

		self.frame = frame

		p = urllib.request.Request("https://api.github.com/repos/ruifontes/frequentText/releases")
		r = urllib.request.urlopen(p).read()
		githubApi = json.loads(r.decode('utf-8'))
		self.nombreUrl = githubApi[0]['assets'][0]['browser_download_url']

		self.directorio = os.path.join(globalVars.appArgs.configPath, "tempFreqText")

		self.daemon = True
		self.start()

	def generaFichero(self):
		if os.path.exists(self.directorio) == False:
			os.mkdir(self.directorio)
		nuevoIndex = len(os.listdir(self.directorio))
		return os.path.join(self.directorio, "temp%s.nvda-addon" % nuevoIndex)

	def humanbytes(self, B): # Convierte bytes
		B = float(B)
		KB = float(1024)
		MB = float(KB ** 2) # 1,048,576
		GB = float(KB ** 3) # 1,073,741,824
		TB = float(KB ** 4) # 1,099,511,627,776

		if B < KB:
			return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
		elif KB <= B < MB:
			return '{0:.2f} KB'.format(B/KB)
		elif MB <= B < GB:
			return '{0:.2f} MB'.format(B/MB)
		elif GB <= B < TB:
			return '{0:.2f} GB'.format(B/GB)
		elif TB <= B:
			return '{0:.2f} TB'.format(B/TB)

	def __call__(self, block_num, block_size, total_size):
		readsofar = block_num * block_size
		if total_size > 0:
			percent = readsofar * 1e2 / total_size
			wx.CallAfter(self.frame.onDescarga, percent)
			sleep(1 / 995)
			wx.CallAfter(self.frame.TextoRefresco, _("Please wait\n" + "Downloading %s" % self.humanbytes(readsofar)))
			if readsofar >= total_size:
				pass
		else:
			wx.CallAfter(self.frame.TextoRefresco, _("Please wait...\n" + "Downloading  %s" % self.humanbytes(readsofar)))

	def run(self):
		try:
			fichero = self.generaFichero()
			socket.setdefaulttimeout(15)
			opener = urllib.request.build_opener()
			opener.addheaders = [('User-agent', 'Mozilla/5.0')]
			urllib.request.install_opener(opener)
			urllib.request.urlretrieve(self.nombreUrl, fichero, reporthook=self.__call__)
			bundle = addonHandler.AddonBundle(fichero)
			if not addonHandler.addonVersionCheck.hasAddonGotRequiredSupport(bundle):
				pass
			else:
				bundleName = bundle.manifest['name']
				isDisabled = False
				for addon in addonHandler.getAvailableAddons():
					if bundleName == addon.manifest['name']:
						if addon.isDisabled:
							isDisabled = True
						if not addon.isPendingRemove:
							addon.requestRemove()
						break
				addonHandler.installAddonBundle(bundle)
			# Translators: Mensaje que anuncia la finalización del proceso.
			wx.CallAfter(self.frame.done, _("Update finished.\nYou must restart NVDA for these changes to take effect.\nPress the Confirm button to restart or the Close to terminate without restarting"))
		except:
			# Translators: Mensaje que anuncia la existencia de un error
			wx.CallAfter(self.frame.error, _("Error.\n" + "Check the Internet connection and try again.\n" + "You may close this window"))
		try:
			shutil.rmtree(self.directorio, ignore_errors=True)
		except:
			pass

class UpdateDialog(wx.Dialog):
	def __init__(self, parent):
		super(UpdateDialog, self).__init__(parent, -1, title=_("Frequent text"), size=(350, 150))

		global IS_WinON
		IS_WinON = True
		Panel = wx.Panel(self)

		#Translators: Mensaje que informa de una nueva versión
		label1 = wx.StaticText(Panel, wx.ID_ANY, label=_("Available a new version of this add-on. Do you want to download and install it now?"))
		self.downloadButton = wx.Button(Panel, wx.ID_ANY, _("&Download and install"))
		self.downloadButton.Bind(wx.EVT_BUTTON, self.download)
		self.closeButton = wx.Button(Panel, wx.ID_CANCEL, _("&Close"))
		self.closeButton.Bind(wx.EVT_BUTTON, self.close, id=wx.ID_CANCEL)

		sizerV = wx.BoxSizer(wx.VERTICAL)
		sizerH = wx.BoxSizer(wx.HORIZONTAL)

		sizerV.Add(label1, 0, wx.EXPAND | wx.ALL)

		sizerH.Add(self.downloadButton, 2, wx.CENTER)
		sizerH.Add(self.closeButton, 2, wx.CENTER)

		sizerV.Add(sizerH, 0, wx.CENTER)
		Panel.SetSizer(sizerV)

		self.CenterOnScreen()

	def download(self, event):
		global IS_WinON
		IS_WinON = False
		self._MainWindows = HiloComplemento(2)
		self._MainWindows.start()
		self.Destroy()
		gui.mainFrame.postPopup()

	def close(self, event):
		global IS_WinON
		IS_WinON = False
		self.Destroy()
		gui.mainFrame.postPopup()

class ActualizacionDialogo(wx.Dialog):
	def __init__(self, parent):

		#Translators: título de la ventana
		super(ActualizacionDialogo, self).__init__(parent, -1, title=_("Updating Frequent text"), size=(550, 400))

#		self.SetSize((400, 130))
		self.CenterOnScreen()

		global IS_WinON
		IS_WinON = True

		self.Panel = wx.Panel(self)

		self.ProgressDescarga=wx.Gauge(self.Panel, wx.ID_ANY, range=100, style = wx.GA_HORIZONTAL)
		self.textorefresco = wx.TextCtrl(self.Panel, wx.ID_ANY, style =wx.TE_MULTILINE|wx.TE_READONLY)
		self.textorefresco.Bind(wx.EVT_CONTEXT_MENU, self.skip)

		#Translators: nombre del botón aceptar
		self.AceptarTRUE = wx.Button(self.Panel, ID_TRUE, _("&Confirm"))
		self.Bind(wx.EVT_BUTTON, self.onAceptarTRUE, id=self.AceptarTRUE.GetId())
		self.AceptarTRUE.Disable()

		self.AceptarFALSE = wx.Button(self.Panel, ID_FALSE, "&Cerrar")
		self.Bind(wx.EVT_BUTTON, self.onAceptarFALSE, id=self.AceptarFALSE.GetId())
		self.AceptarFALSE.Disable()

		self.Bind(wx.EVT_CLOSE, self.onNull)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer_botones = wx.BoxSizer(wx.HORIZONTAL)

		sizer.Add(self.ProgressDescarga, 0, wx.EXPAND)
		sizer.Add(self.textorefresco, 1, wx.EXPAND)

		sizer_botones.Add(self.AceptarTRUE, 2, wx.CENTER)
		sizer_botones.Add(self.AceptarFALSE, 2, wx.CENTER)

		sizer.Add(sizer_botones, 0, wx.EXPAND)

		self.Panel.SetSizer(sizer)

		HiloActualizacion(self)

		self.textorefresco.SetFocus()

	def skip(self, event):
		return

	def onNull(self, event):
		pass

	def onDescarga(self, event):
		self.ProgressDescarga.SetValue(event)

	def TextoRefresco(self, event):
		self.textorefresco.Clear()
		self.textorefresco.AppendText(event)

	def done(self, event):
		winsound.MessageBeep(0)
		self.AceptarTRUE.Enable()
		self.AceptarFALSE.Enable()
		self.textorefresco.Clear()
		self.textorefresco.AppendText(event)
		self.textorefresco.SetInsertionPoint(0) 

	def error(self, event):
		winsound.MessageBeep(16)
		self.AceptarFALSE.Enable()
		self.textorefresco.Clear()
		self.textorefresco.AppendText(event)
		self.textorefresco.SetInsertionPoint(0) 

	def onAceptarTRUE(self, event):
		global IS_WinON
		IS_WinON = False
		self.Destroy()
		gui.mainFrame.postPopup()
		core.restart()

	def onAceptarFALSE(self, event):
		global IS_WinON
		IS_WinON = False
		self.Destroy()
		gui.mainFrame.postPopup()

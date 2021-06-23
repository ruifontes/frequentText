#-*- coding: utf-8 -*-
# frequentText add-on for NVDA.
# written by Rui Fontes <rui.fontes@tiflotecnia.com> and Ângelo Abrantes <ampa4374@gmail.com>
# Regists the frequently used blocks of text
# Shortcut: WINDOWS+F12

import os
import api
import gui
import wx
from keyboardHandler import KeyboardInputGesture
import ui
from configobj import ConfigObj
import time
import core
import watchdog
import globalPluginHandler
import addonHandler
addonHandler.initTranslation()

_ffIniFile = os.path.join(os.path.dirname(__file__), "frequentText.ini")
Catg = ""
dictBlocks = {}


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		self.dialog = None

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

	def script_startFrequentText(self, gesture):
		self.showFrequentTextCatgsDialog(self)

	# For translators: Message to be announced during Keyboard Help
	script_startFrequentText.__doc__ = _("Opens a dialog box to registe and paste frequent blocks of text.")
	# For translators: Name of the section in "Input gestures" dialog.
	script_startFrequentText.category = _("Frequent text")

	def showFrequentTextCatgsDialog (self, listCatgs):
		# Displays the add-on dialog box.
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		listCatgs = config.keys()
		# Translators: Title of categories list dialog boxes.
		self.dialog = FrequentTextCatgsDialog(gui.mainFrame, _("Categories list"), listCatgs)
		self.dialog.updateCatgs(listCatgs, 0)

		if not self.dialog.IsShown():
			gui.mainFrame.prePopup()
			self.dialog.Show()
			self.dialog.Centre()
			gui.mainFrame.postPopup()

	def showFrequentTextDialog(self, dictBlocks):
		# Displays the add-on dialog box.
		config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
		dictBlocks = config[Catg]
		# Translators: Title of Blocks list dialog boxes.
		self.dialog = FrequentTextDialog(gui.mainFrame, _("Blocks list"), dictBlocks)
		self.dialog.updateBlocks(dictBlocks, 0)

		if not self.dialog.IsShown():
			gui.mainFrame.prePopup()
			self.dialog.Show()
			self.dialog.Centre()
			gui.mainFrame.postPopup()

	def terminate (self):
		if self.dialog is not None:
			self.dialog.Destroy()

	__gestures={
		"kb:WINDOWS+f12": "startFrequentText",
	}

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

		removeButtonID = wx.Window.NewControlId()
		# Translators: Button Label that removes the selected block.
		self.removeButton = wx.Button (self, removeButtonID, _("&Remove"))
		buttonsSizer.Add (self.removeButton)

		# Translators: Button Label that closes the add-on.
		cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Close"))
		buttonsSizer.Add(cancelButton)

		tasksSizer.Add(buttonsSizer)
		mainSizer.Add(tasksSizer)

		# Bind the buttons.
		self.Bind(wx.EVT_BUTTON, self.onShow, id = showButtonID)
		self.Bind(wx.EVT_BUTTON, self.onAdd, id = addButtonID)
		self.Bind(wx.EVT_BUTTON, self.onRename, id = renameButtonID)
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
					self.listBoxCatgs.Append([nameCatg])
					# Puts the focus on the inserted category
					listCatgs = config.keys()
					self.updateCatgs(listCatgs, 0)
					idx = self.listBoxCatgs.FindItem(0, nameCatg)
					self.listBoxCatgs.Focus(idx)
					self.listBoxCatgs.Select(idx)
					self.listBoxCatgs.SetFocus()
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
				#self.listCatgs.append(newKeyCatg)
				#self.listCatgs.remove(nameCatg)
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

	def onKeyPress(self, evt):
		# Sets enter key  to show the entries and delete to remove it.
		evt.Skip()
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_RETURN and self.listBoxCatgs.GetItemCount():
			self.onShow(evt)
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

		# Translators: Button Label that closes the add-on.
		cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Close"))
		buttonsSizer.Add(cancelButton)

		tasksSizer.Add(buttonsSizer)
		mainSizer.Add(tasksSizer)

		# Bind the buttons.
		self.Bind(wx.EVT_BUTTON, self.onAdd, id = addButtonID)
		self.Bind (wx.EVT_BUTTON, self.onPaste, id = pasteButtonID )
		self.Bind(wx.EVT_BUTTON, self.onRename, id = renameButtonID)
		self.Bind(wx.EVT_BUTTON, self.onChangeBlocks, id = changeButtonID)
		self.Bind(wx.EVT_BUTTON, self.onMove, id = moveButtonID)
		self.Bind(wx.EVT_BUTTON, self.onRemove, id = removeButtonID)
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
		#name = ""
		#newBlock = []
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
		self.dialogActive = True

		changeBlock = []
		for x in range(len(paste)):
			# Translators: Message dialog box to change a block of text.
			dlg = wx.TextEntryDialog(gui.mainFrame, _("Enter the new block of text or press Enter to confirm"), self.title)
			dlg.SetValue(paste[x])
			if dlg.ShowModal() == wx.ID_OK:
				nBlock = dlg.GetValue()
			else:
				dlg.Destroy()
				return

			if nBlock != "":
				changeBlock.append(nBlock)
			elif nBlock == paste[x]:
				changeBlock.append(nBlock)
			else:
				dlg.Destroy()
				return

		# update the dictionary.
		blocks.__delitem__(name) #, paste)
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

	def onKeyPress(self, evt):
		# Sets enter key  to paste the text and delete to remove it.
		evt.Skip()
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_RETURN and self.listBox.GetItemCount():
			self.onPaste(evt)
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


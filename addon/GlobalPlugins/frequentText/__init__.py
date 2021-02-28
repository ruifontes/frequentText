#-*- coding: utf-8 -*-
# frequentText add-on for NVDA.
# written by Rui Fontes <rui.fontes@tiflotecnia.com>
# Registes the frequently used blocks of text
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

_ffIniFile = os.path.join (os.path.dirname(__file__),'frequentText.ini')

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		self.dialog = None

	def readConfig (self):
		if not os.path.isfile (_ffIniFile):
			return None
		config = ConfigObj(_ffIniFile, list_values=True)
		blocks = config['Blocks']
		total = len(blocks.keys())
		if not total:
			return None
		if not len (blocks.keys()):
			blocks = None
		return blocks

	def script_startFrequentText(self, gesture):
		self.showFrequentTextDialog (self)

	script_startFrequentText.__doc__ = _("Opens a dialog box to registe and paste frequent blocks of text.")

	def showFrequentTextDialog (self, dictBlocks):
		# Displays the add-on dialog box.
		dictBlocks = self.readConfig()

		# Translators: Title of add-on, present in the dialog boxes.
		self.dialog = FrequentTextDialog (gui.mainFrame, _("Frequent Text"), dictBlocks)
		self.dialog.updateBlocks(dictBlocks,0)
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
		tasksLabel = wx.StaticText(self, -1, label=_('Text blocks list'))
		tasksSizer.Add(tasksLabel)

		# create a list view.
		self.listBox = wx.ListCtrl(self, size=(800, 250), style = wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_SORT_ASCENDING)
		tasksSizer.Add(self.listBox, proportion=8)

		# Create buttons.
		# Buttons are in a horizontal row
		buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)

		addButtonID = wx.Window.NewControlId()
		# Translators: Button Label to add a new block.
		self.addButton = wx.Button(self, addButtonID, _('&Add'))
		buttonsSizer.Add (self.addButton)

		pasteButtonID = wx.Window.NewControlId()
		# Translators: Button Label that paste the block to the edit box.
		self.pasteButton = wx.Button (self, pasteButtonID, _('&Paste'))
		buttonsSizer.Add(self.pasteButton)

		renameButtonID = wx.Window.NewControlId()
		# Translators: Button Label that renames the name of the selected block.
		self.renameButton = wx.Button(self, renameButtonID, _('Re&name'))
		buttonsSizer.Add (self.renameButton)

		changeButtonID = wx.Window.NewControlId()
		# Translators: Button Label that change the blocks of text.
		self.changeButton = wx.Button(self, changeButtonID, _('Change &blocks'))
		buttonsSizer.Add (self.changeButton)

		removeButtonID = wx.Window.NewControlId()
		# Translators: Button Label that removes the selected block.
		self.removeButton = wx.Button (self, removeButtonID, _('&Remove'))
		buttonsSizer.Add (self.removeButton)

		# Translators: Button Label that closes the add-on.
		cancelButton = wx.Button(self, wx.ID_CANCEL, _('&Close'))
		buttonsSizer.Add(cancelButton)

		tasksSizer.Add(buttonsSizer)
		mainSizer.Add(tasksSizer)

		# Bind the buttons.
		self.Bind(wx.EVT_BUTTON, self.onAdd, id = addButtonID)
		self.Bind (wx.EVT_BUTTON, self.onPaste, id = pasteButtonID )
		self.Bind(wx.EVT_BUTTON, self.onRename, id = renameButtonID)
		self.Bind(wx.EVT_BUTTON, self.onChangeBlocks, id = changeButtonID)
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

		#Saving the block
		config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
		if 'Blocks' in config.sections:
			blocks = config['Blocks']
			blocks.__setitem__ (name, newBlock)
		else:
			config['Blocks'] = {name:newBlock}
		self.dictBlocks = {name:newBlock}
		config.write()
		self.listBox.Append([name])
		newIndex = self.listBox.FindItem(0,name)
		list = [self.dictBlocks.items()]
		list.append ((name, newBlock))
		# Puts the focus on the inserted block.
		self.listBox.Focus (newIndex)
		self.listBox.Select(newIndex)
		self.listBox.SetFocus()
		name = ""
		newBlock = []
		return

	def onPaste (self, evt):
		# Simulates typing the block of text in the edit area.
		self.Hide()
		evt.Skip()
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		paste = self.dictBlocks [name]
		pasteStr = "\r\n".join(paste)
		if len(paste) >= 2:
			pasteStr += "\r\n"
		clipboardBackup = api.getClipData()
		api.copyToClip(pasteStr)
		time.sleep(0.1)
		api.processPendingEvents(False)
		focus = api.getFocusObject()
		if focus.windowClassName == 'ConsoleWindowClass':
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
		if  newKey != '':
			if self.listBox.FindItem(0, newKey) == -1:
				config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
				blocks = config['Blocks']
				paste = blocks[name]
				# update the dictionary.
				list = self.dictBlocks.items()
				list.append ((newKey, paste))
				list.remove ((name, paste))
				self.dictBlocks = dict (list)
				blocks.rename(name, newKey)
				config.write()

				# update the list view.
				blocks = config['Blocks']
				keys = blocks.keys()
				keys.sort()
				newIndex = keys.index (newKey)
				self.updateBlocks (blocks, newIndex)

			else:
				gui.messageBox (_("There is already a block with this name!"), self.title)
		self.dialogActive = False

	def onChangeBlocks(self, evt):
		evt.Skip()
		index=self.listBox.GetFocusedItem()
		name = self.listBox.GetItemText(index)
		config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
		blocks = config['Blocks']
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
			else:
				dlg.Destroy()
				return

		# update the dictionary.
		name1 = name
		config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
		blocks = config['Blocks']
		list = self.dictBlocks.items()
		list.append ((name1, changeBlock))
		list.remove ((name1, paste))
		self.dictBlocks = dict (list)
		blocks[name1] = changeBlock
		config.write()

		# update the list view.
		blocks = config['Blocks']
		keys = blocks.keys()
		keys.sort()
		newIndex = keys.index (name)
		self.updateBlocks (blocks, newIndex)

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
		if gui.messageBox(_('Are you sure you want to remove %s?') %name, self.title, style=wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
			config = ConfigObj(_ffIniFile, list_values=True, encoding = "utf-8")
			blocks = config['Blocks']
			blocks.__delitem__(name)
			config.write()
			self.listBox.DeleteItem(index)
			if self.listBox.GetItemCount():
				self.listBox.Select(self.listBox.GetFocusedItem())
		self.dialogActive = False

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
		self.listBox.InsertColumn(0, _('Name'))
		self.listBox.SetColumnWidth (0,250)
		if dictBlocks == None:
			return
		keys = dictBlocks.keys()
		keys.sort()
		cont = 0
		for item in keys:
			k = item
			self.listBox.Append ([k])
			cont += 1
		self.listBox.Focus(index)
		self.listBox.Select(index)


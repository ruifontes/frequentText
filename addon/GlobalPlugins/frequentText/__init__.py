#-*- coding: utf-8 -*-
# frequentText add-on for NVDA.
# Regists, manage and allow to paste  frequently used blocks of text
# Shortcut: WINDOWS+F12
# written by Rui Fontes <rui.fontes@tiflotecnia.com>, Ângelo Abrantes <ampa4374@gmail.com> and Abel Passos do Nascimento Jr. <abel.passos@gmail.com>
# Copyright (C) 2020-2023 Rui Fontes <rui.fontes@tiflotecnia.com>
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.


# Import the necessary modules
import globalPluginHandler
import globalVars
import os
import core
import api
import wx
import gui
from keyboardHandler import KeyboardInputGesture
from configobj import ConfigObj
import time
import watchdog
from scriptHandler import script
import addonHandler

# To start the translation process
addonHandler.initTranslation()

# Global vars
_ffIniFile = os.path.join(os.path.dirname(__file__), "frequentText.ini")
config = ConfigObj(_ffIniFile, list_values = True, encoding = "utf-8")
defCatg = 0
category = 0

def listCategories():
	listCatgs = config.keys()
	listCatgs.sort(key=str.lower)
	return listCatgs

def listTextBlocks(catg):
	listCatgs = listCategories()
	listBlocks = []
	Catg = catg
	catg = listCatgs[Catg]
	dictBlocks = config[catg]
	keys = dictBlocks.keys()
	keys.sort()
	for item in keys:
		k = item
		listBlocks.append(k)
	return listBlocks, dictBlocks

# To avoid use on secure screens
if globalVars.appArgs.secure:
	# Override the global plugin to disable it.
	GlobalPlugin = globalPluginHandler.GlobalPlugin


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		self.dialog = None

	@script(
		# Translators: Message to be announced during Keyboard Help
		description = _("Opens a dialog box to registe, manage and paste frequent blocks of text."),
		# Translators: Name of the section in "Input gestures" dialog.
		category = _("Text editing"),
		gesture = "kb:WINDOWS+f12",
		allowInSleepMode = True)
	def script_startFrequentText(self, gesture):
		# Invoke the corresponding dialog
		try:
			gui.mainFrame.popupSettingsDialog(FrequentTextCatgsDialog)
		except AttributeError:
			gui.mainFrame._popupSettingsDialog(FrequentTextCatgsDialog)

	@script(
		# Ttranslators: Message to be announced during Keyboard Help
		description = _("Opens a dialog box with the text blocks of first or default category"),
		# Translators: Name of the section in "Input gestures" dialog.
		category = _("Text editing"),
		gesture = "kb:Control+WINDOWS+f12",
		allowInSleepMode = True)
	def script_startFrequentTextDefault(self, gesture):
		# Invoke the corresponding dialog
		global defCatg, category
		if defCatg == 0:
			category = 0
		else:
			category = defCatg
		try:
			gui.mainFrame.popupSettingsDialog(FrequentTextDialog)
		except AttributeError:
			gui.mainFrame._popupSettingsDialog(FrequentTextDialog)

	def terminate (self):
		if self.dialog is not None:
			self.dialog.Destroy()


class FrequentTextCatgsDialog(wx.Dialog):
	def __init__(self, *args, **kwds):
		kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE
		wx.Dialog.__init__(self, *args, **kwds)
		self.title = _("Frequent text")
		if not os.path.isfile(_ffIniFile):
			with open(_ffIniFile, "w") as file:
				pass
		self.listCatgs = listCategories()

		sizer_1 = wx.BoxSizer(wx.VERTICAL)

		# Create a label and a list view for categories list. Label is above the list view.
		# Translators: Label the list view that contains the categories
		listLabel = wx.StaticText(self, wx.ID_ANY, _("Categories list"))
		sizer_1.Add(listLabel, 0, 0, 0)

		self.CatgsList = wx.ListBox(self, wx.ID_ANY, choices=self.listCatgs, style=wx.LB_SINGLE | wx.LB_SORT)
		self.CatgsList.SetFocus()
		if len(self.listCatgs) != 0:
			self.CatgsList.SetSelection(0)
		sizer_1.Add(self.CatgsList, 0, 0, 0)

		sizer_2 = wx.StdDialogButtonSizer()
		sizer_1.Add(sizer_2, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 4)

		# Translators: Button Label to show the entries of a category
		self.showButton = wx.Button(self, wx.ID_ANY, _("&Show entries"))
		if len(self.listCatgs) != 0:
			self.showButton.SetDefault()
		sizer_2.Add(self.showButton, 0, 0, 0)

		# Translators: Button Label to add a new category
		self.addButton = wx.Button(self, wx.ID_ANY, _("&Add"))
		if len(self.listCatgs) == 0:
			self.addButton.SetDefault()
		sizer_2.Add(self.addButton, 0, 0, 0)

		# Translators: Button Label that renames the name of the selected block.
		self.renameButton = wx.Button(self, wx.ID_ANY, _("Re&name"))
		sizer_2.Add(self.renameButton, 0, 0, 0)

		# Translators: Button Label to set the selected category as default
		self.setAsDefaultButton = wx.Button(self, wx.ID_ANY, _("Set &category as default"))
		sizer_2.Add(self.setAsDefaultButton, 0, 0, 0)

		# Translators: Button Label that removes the selected category.
		self.removeButton = wx.Button(self, wx.ID_ANY, _("&Remove"))
		sizer_2.Add(self.removeButton, 0, 0, 0)

		self.button_CLOSE = wx.Button(self, wx.ID_CLOSE, "")
		sizer_2.AddButton(self.button_CLOSE)

		if len(self.listCatgs) == 0:
			self.showButton.Hide()
			self.renameButton.Hide()
			self.setAsDefaultButton.Hide()
			self.removeButton.Hide()

		sizer_2.Realize()

		self.SetSizer(sizer_1)
		sizer_1.Fit(self)

		self.SetEscapeId(self.button_CLOSE.GetId())

		self.Layout()
		self.Centre()

		self.Bind(wx.EVT_BUTTON, self.onShow, self.showButton)
		self.Bind(wx.EVT_BUTTON, self.onAdd, self.addButton)
		self.Bind(wx.EVT_BUTTON, self.onRename, self.renameButton)
		self.Bind(wx.EVT_BUTTON, self.onSetAsDefault, self.setAsDefaultButton)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.removeButton)
		self.CatgsList.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)

	def onShow(self, evt):
		index = self.CatgsList.GetSelection()
		catgIDX = self.listCatgs.index(self.CatgsList.GetString(index))
		self.Close()
		global category
		category = catgIDX
		try:
			gui.mainFrame.popupSettingsDialog(FrequentTextDialog)
		except AttributeError:
			gui.mainFrame._popupSettingsDialog(FrequentTextDialog)

	def onAdd (self, evt):
		# Add a new category
		evt.Skip()
		# Translators: Message dialog box to add a name to a new category
		nameCatg = wx.GetTextFromUser(_("Enter a name for the category"), self.title).strip().upper()
		if nameCatg != "":
			if nameCatg in self.listCatgs:
				# Translators: Announcement that the category name already exists in the list.
				wx.MessageBox (_("There is already a category with this name!"), self.title)
				self.onAdd(evt)
				return
			else:
				# Saving the category
				config[nameCatg] = {}
				config.write()
				# Update the list of categories and the listbox
				self.listCatgs = config.keys()
				self.CatgsList.Set(self.listCatgs)
				# Place the focus on the inserted category
				idx = self.CatgsList.FindString(nameCatg)
				self.CatgsList.SetSelection(idx)
				self.CatgsList.SetFocus()
				# Redraw the dialog box to adapt the buttons
				if len(self.listCatgs) == 1:
					self.Destroy()
					try:
						gui.mainFrame.popupSettingsDialog(FrequentTextCatgsDialog)
					except AttributeError:
						gui.mainFrame._popupSettingsDialog(FrequentTextCatgsDialog)
					return
		else:
			return

	def onRename(self, evt):
		# Renames the selected category
		evt.Skip()
		index = self.CatgsList.GetSelection()
		nameCatg = self.CatgsList.GetString(index)
		self.dialogActive = True
		# Translators: Message dialog to rename the category
		newKeyCatg = wx.GetTextFromUser(_("Enter a new name for %s") %nameCatg, self.title).strip().upper()
		if  newKeyCatg != "":
			if newKeyCatg not in self.listCatgs:
				# update the dictionaries
				config.rename(nameCatg, newKeyCatg)
				config.write()
				# Update the list of categories and the listbox
				self.listCatgs = config.keys()
				self.CatgsList.Set(self.listCatgs)
				# Place the focus on the inserted category
				idx = self.CatgsList.FindString(newKeyCatg)
				self.CatgsList.SetSelection(idx)
				self.CatgsList.SetFocus()
				return

		else:
				wx.MessageBox (_("There is already a category with this name!"), self.title)
		self.dialogActive = False

	def onSetAsDefault(self, evt):
		# Set the selected category as default
		evt.Skip()
		global defCatg
		index = self.CatgsList.GetSelection()
		defCatg = self.listCatgs.index(self.CatgsList.GetString(index))
		# Return focus to the listbox
		self.CatgsList.SetFocus()
		return

	def onRemove (self, evt):
		# Removes the selected category
		evt.Skip()
		index = self.CatgsList.GetSelection()
		nameCatg = self.CatgsList.GetString(index)
		self.dialogActive = True
		# Translators: Message asking if user wants to remove the selected category
		if wx.MessageBox(_("Are you sure you want to remove %s?") %nameCatg, self.title, style=wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
			config.__delitem__(nameCatg)
			config.write()
			# Update the list of categories and the listbox
			self.listCatgs = config.keys()
			self.CatgsList.Set(self.listCatgs)
			# If list box have itens, select the first
			if len(self.listCatgs) != 0:
				self.CatgsList.SetSelection(0)
				self.dialogActive = False
				self.CatgsList.SetFocus()
				return
			else:
				self.Destroy()
				try:
					gui.mainFrame.popupSettingsDialog(FrequentTextCatgsDialog)
				except AttributeError:
					gui.mainFrame._popupSettingsDialog(FrequentTextCatgsDialog)

	def onKeyPress(self, evt):
		# Sets enter key  to show the entries and delete to remove it.
		evt.Skip()
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_RETURN and self.CatgsList.GetCount():
			self.onShow(evt)
		elif keycode == wx.WXK_RETURN and self.CatgsList.GetCount() == 0:
			self.onAdd(evt)
		elif keycode == wx.WXK_DELETE and self.CatgsList.GetCount():
			self.onRemove(evt)


class FrequentTextDialog(wx.Dialog):
	def __init__(self, *args, **kwds):
		kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE
		wx.Dialog.__init__(self, *args, **kwds)
		self.title = _("Frequent text")
		self.category = category
		self.listCatgs = listCategories()
		self.catg = category
		catg = self.listCatgs[self.catg]
		self.listBlocks, self.dictBlocks = listTextBlocks(self.catg)

		sizer_1 = wx.BoxSizer(wx.VERTICAL)

		# Create a label and a list view for categories list.
		# Label is above the list view.
		# Translators: Label the list view that contains the categories
		listLabel = wx.StaticText(self, wx.ID_ANY, _("List of text blocks of %s category") %catg)
		sizer_1.Add(listLabel, 0, 0, 0)

		self.BlocksList = wx.ListBox(self, wx.ID_ANY, choices=self.listBlocks, style=wx.LB_SINGLE | wx.LB_SORT)
		self.BlocksList.SetFocus()
		if len(self.listBlocks) != 0:
			self.BlocksList.SetSelection(0)
		sizer_1.Add(self.BlocksList, 0, 0, 0)

		sizer_2 = wx.StdDialogButtonSizer()
		sizer_1.Add(sizer_2, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 4)

		# Translators: Button Label to add a new category
		self.addButton = wx.Button(self, wx.ID_ANY, _("&Add"))
		if len(self.listBlocks) == 0:
			self.addButton.SetDefault()
		sizer_2.Add(self.addButton, 0, 0, 0)

		# Translators: Button Label that paste the block to the edit box.
		self.pasteButton = wx.Button(self, wx.ID_ANY, _("&Paste"))
		if len(self.listBlocks) != 0:
			self.pasteButton.SetDefault()
		sizer_2.Add(self.pasteButton, 0, 0, 0)

		# Translators: Button Label that renames the name of the selected block.
		self.renameButton = wx.Button(self, wx.ID_ANY, _("Re&name"))
		sizer_2.Add(self.renameButton, 0, 0, 0)

		# Translators: Button Label that change the blocks of text.
		self.changeButton = wx.Button(self, wx.ID_ANY, _("&Change blocks"))
		sizer_2.Add(self.changeButton, 0, 0, 0)

		# Translators: Label  for button to move the selected block to other category.
		self.moveButton = wx.Button(self, wx.ID_ANY, _("&Move"))
		sizer_2.Add(self.moveButton, 0, 0, 0)

		# Translators: Button Label that removes the selected block.
		self.removeButton = wx.Button(self, wx.ID_ANY, _("&Remove"))
		sizer_2.Add(self.removeButton, 0, 0, 0)

		# Translators: Label  for button to go back to categories list.
		self.goBackButton = wx.Button(self, wx.ID_ANY, _("&Back to categories"))
		sizer_2.Add(self.goBackButton, 0, 0, 0)

		self.button_CLOSE = wx.Button(self, wx.ID_CLOSE, "")
		sizer_2.AddButton(self.button_CLOSE)

		if self.BlocksList.GetCount() == 0:
			self.pasteButton.Hide()
			self.renameButton.Hide()
			self.changeButton.Hide()
			self.moveButton.Hide()
			self.removeButton.Hide()

		sizer_2.Realize()

		self.SetSizer(sizer_1)
		sizer_1.Fit(self)

		self.SetEscapeId(self.button_CLOSE.GetId())

		self.Layout()
		self.Centre()

		self.Bind(wx.EVT_BUTTON, self.onAdd, self.addButton)
		self.Bind(wx.EVT_BUTTON, self.onPaste, self.pasteButton)
		self.Bind(wx.EVT_BUTTON, self.onRename, self.renameButton)
		self.Bind(wx.EVT_BUTTON, self.onChangeBlocks, self.changeButton)
		self.Bind(wx.EVT_BUTTON, self.onMove, self.moveButton)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.removeButton)
		self.Bind(wx.EVT_BUTTON, self.onGoBack, self.goBackButton)
		self.BlocksList.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)

	def onAdd(self, evt):
		# Add a new block of text.
		evt.Skip()
		# Translators: Message dialog box to add a name to a new block.
		name = wx.GetTextFromUser(_("Enter a name for the block"), self.title).strip().upper()
		if name != "":
			if name in self.listBlocks:
				# Translators: Announcement that the block name already exists in the list.
				wx.MessageBox (_("There is already a block with this name!"), self.title)
				self.onAdd(evt)
				return
			else:
				self._addBlock(name)
		else:
			self.BlocksList.SetFocus()

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
		catg = self.listCatgs[self.catg]
		if catg in config.sections:
			blocks = config[catg]
			blocks.__setitem__(name, newBlock)
		else:
			config[catg] = {name:newBlock}
		config.write()
		# Update listBlocks e blocksList
		self.listBlocks, self.dictBlocks = listTextBlocks(self.catg)
		self.BlocksList.Set(self.listBlocks)
		# Puts the focus on the inserted block.
		idx = self.BlocksList.FindString(name)
		self.BlocksList.SetSelection(idx)
		self.BlocksList.SetFocus()
		if self.BlocksList.GetCount() == 1:
			self.pasteButton.Show()
			self.renameButton.Show()
			self.changeButton.Show()
			self.moveButton.Show()
			self.removeButton.Show()
		return

	def onPaste(self, evt):
		# Simulates typing the block of text in the edit area.
		self.Hide()
		evt.Skip()
		# Get the name of selected block
		name = self.BlocksList.GetString(self.BlocksList.GetSelection())
		# Get blocks list and blocks dictionary of the category
		blocks, dictBlocks = listTextBlocks(self.catg)
		# Gets the selected block contents
		paste = dictBlocks[name]
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
			time.sleep(0.01)
			api.processPendingEvents(False)
			focus = api.getFocusObject()
			if focus.windowClassName == "ConsoleWindowClass":
				# Windows console window - Control+V doesn't work here, so using an alternative method here
				WM_COMMAND = 0x0111
				watchdog.cancellableSendMessage(focus.windowHandle, WM_COMMAND, 0xfff1, 0)
			else:
				KeyboardInputGesture.fromName("Control+v").send()
			core.callLater(300, lambda: api.copyToClip(clipboardBackup))
		self.Destroy()

	def onRename(self, evt):
		# Renames the selected block.
		evt.Skip()
		index=self.BlocksList.GetSelection()
		name = self.BlocksList.GetString(index)
		catg = self.listCatgs[self.catg]
		self.dialogActive = True
		# Translators: Message dialog to rename the block of text.
		newKey = wx.GetTextFromUser(_("Enter a new name for %s") %name, self.title).strip().upper()
		if newKey != "":
			if newKey not in self.listBlocks:
				# Save the new name
				blocks = config[catg]
				# update the dictionary.
				blocks.rename(name, newKey)
				config.write()
				# Update listBlocks e blocksList
				self.listBlocks, self.dictBlocks = listTextBlocks(self.catg)
				self.BlocksList.Set(self.listBlocks)
				# Puts the focus on the inserted block.
				idx = self.BlocksList.FindString(newKey)
				self.BlocksList.SetSelection(idx)
				self.BlocksList.SetFocus()
			else:
				gui.messageBox (_("There is already a block with this name!"), self.title)
		self.dialogActive = False

	def onChangeBlocks(self, evt):
		evt.Skip()
		index=self.BlocksList.GetSelection()
		name = self.BlocksList.GetString(index)
		catg = self.listCatgs[self.catg]
		self.dialogActive = True
		blocks = config[catg]
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
		# Update listBlocks e blocksList
		self.listBlocks, self.dictBlocks = listTextBlocks(self.catg)
		self.BlocksList.Set(self.listBlocks)
		# Puts the focus on the inserted block.
		idx = self.BlocksList.FindString(name)
		self.BlocksList.SetSelection(idx)
		self.BlocksList.SetFocus()

	def onMove(self, evt):
		# Moves the selected block to other category.
		evt.Skip()
		index=self.BlocksList.GetSelection()
		name = self.BlocksList.GetString(index)
		catg = self.listCatgs[self.catg]
		blocks = config[catg]
		textBlock = blocks[name]
		self.dialogActive = True
		# Translators: Message dialog box to move the selected block to other category.
		newCatg = wx.GetTextFromUser(_("If you really want to move %s from %s category, enter the name of the new, already existing, category") %(name, catg), self.title).strip().upper()
		if newCatg != "":
			listCatgs = config.keys()
			if str(newCatg) in listCatgs:
				blocks = config[newCatg]
				blocks.__setitem__ (name, textBlock)
				blocks = config[catg]
				blocks.__delitem__(name)
				config.write()
				# Update listBlocks e blocksList
				self.listBlocks, self.dictBlocks = listTextBlocks(self.catg)
				self.BlocksList.Set(self.listBlocks)
				# Put focus on the blocks list and in the first block.
				if self.BlocksList.GetCount():
					self.BlocksList.Select(0)
				elif self.BlocksList.GetCount() == 0:
					self.pasteButton.Hide()
					self.renameButton.Hide()
					self.changeButton.Hide()
					self.moveButton.Hide()
					self.removeButton.Hide()
				self.BlocksList.SetFocus()
			else:
				# Translators: Announcement that the category does not exists.
				gui.messageBox (_("There is no such category!"), self.title)
				self.onMove(evt)
		else:
			self.onMove()

	def onRemove(self, evt):
		# Removes the selected block.
		evt.Skip()
		self.removeItem()

	def removeItem(self):
		# Removes the selected block.
		index=self.BlocksList.GetSelection()
		name = self.BlocksList.GetString(index)
		catg = self.listCatgs[self.catg]
		self.dialogActive = True
		# Translators: Message dialog box to remove the selected block.
		if gui.messageBox(_("Are you sure you want to remove %s?") %name, self.title, style=wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
			blocks = config[catg]
			blocks.__delitem__(name)
			config.write()
			self.BlocksList.Delete(index)
		# Adapt the show/hide state of buttons
		if self.BlocksList.GetCount() > 0:
			self.BlocksList.Select(0)
		elif self.BlocksList.GetCount() == 0:
			self.pasteButton.Hide()
			self.renameButton.Hide()
			self.changeButton.Hide()
			self.moveButton.Hide()
			self.removeButton.Hide()
		self.dialogActive = False
		self.BlocksList.SetFocus()

	def onGoBack(self, evt):
		# Returns to categories list dialog
		evt.Skip()
		self.Close()
		try:
			gui.mainFrame.popupSettingsDialog(FrequentTextCatgsDialog)
		except AttributeError:
			gui.mainFrame._popupSettingsDialog(FrequentTextCatgsDialog)

	def onKeyPress(self, evt):
		# Sets enter key  to paste the text and delete to remove it.
		evt.Skip()
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_RETURN and self.BlocksList.GetCount():
			self.onPaste(evt)
		elif keycode == wx.WXK_RETURN and not self.BlocksList.GetCount():
			self.onAdd(evt)
		elif keycode == wx.WXK_DELETE and self.BlocksList.GetCount():
			self.removeItem()


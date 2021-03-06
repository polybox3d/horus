# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2015 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import wx._core
from collections import OrderedDict

from horus.util import profile, resources


class ExpandableControl(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent

        self.isExpandable = True
        self.panels = OrderedDict()

        # Layout
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.vbox)
        self.Layout()

    def addPanel(self, name, panel):
        self.panels.update({name: panel})
        self.vbox.Add(panel, 0, wx.EXPAND, 0)
        panel.titleText.title.Bind(wx.EVT_LEFT_DOWN, self._onTitleClicked)
        panel.content.Show()
        if panel.hasUndo:
            panel.undoButton.Show()
        if panel.hasRestore:
            panel.restoreButton.Show()

    def initPanels(self):
        for i, panel in enumerate(self.panels.values()):
            if i == 0:
                panel.content.Show()
                if panel.hasUndo:
                    panel.undoButton.Show()
                if panel.hasRestore:
                    panel.restoreButton.Show()
            else:
                panel.content.Hide()
                if panel.hasUndo:
                    panel.undoButton.Hide()
                if panel.hasRestore:
                    panel.restoreButton.Hide()

    def setExpandable(self, value):
        self.isExpandable = value

    def _onTitleClicked(self, event):
        if self.isExpandable:
            title = event.GetEventObject()
            for panel in self.panels.values():
                if panel.titleText.title is title:
                    panel.show()
                    if panel.hasUndo:
                        panel.undoButton.Show()
                    if panel.hasRestore:
                        panel.restoreButton.Show()
                else:
                    panel.content.Hide()
                    if panel.hasUndo:
                        panel.undoButton.Hide()
                    if panel.hasRestore:
                        panel.restoreButton.Hide()
                panel.Layout()
            self.Layout()
            self.GetParent().Layout()
            self.GetParent().GetParent().Layout()

    def updateCallbacks(self):
        for panel in self.panels.values():
            panel.updateCallbacks()

    def enableContent(self):
        for panel in self.panels.values():
            panel.content.Enable()

    def disableContent(self):
        for panel in self.panels.values():
            panel.content.Disable()

    def updateProfile(self):
        for panel in self.panels.values():
            panel.updateProfile()

    def enableRestore(self, value):
        for panel in self.panels.values():
            panel.enableRestore(value)


class ExpandablePanel(wx.Panel):

    def __init__(self, parent, title="", callback=None, hasUndo=True, hasRestore=True):
        wx.Panel.__init__(self, parent, size=(-1,-1))

        # Elements
        self.callback = callback
        self.hasUndo = hasUndo
        self.hasRestore = hasRestore
        self.title = title
        self.titleText = TitleText(self, title, bold=True)
        if self.hasUndo:
            self.undoButton = wx.BitmapButton(
                self, wx.NewId(),
                wx.Bitmap(resources.getPathForImage("undo.png"), wx.BITMAP_TYPE_ANY))
        if self.hasRestore:
            self.restoreButton = wx.BitmapButton(
                self, wx.NewId(),
                wx.Bitmap(resources.getPathForImage("restore.png"), wx.BITMAP_TYPE_ANY))
        self.content = wx.Panel(self)
        self.sections = OrderedDict()

        if self.hasUndo:
            self.undoButton.Disable()
        self.content.Hide()

        # Events
        if self.hasUndo:
            self.undoButton.Bind(wx.EVT_BUTTON, self.onUndoButtonClicked)
        if self.hasRestore:
            self.restoreButton.Bind(wx.EVT_BUTTON, self.onRestoreButtonClicked)

        # Layout
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.titleText, 1, wx.ALIGN_CENTER_VERTICAL)
        if self.hasUndo:
            self.hbox.Add(
                self.undoButton, 0, wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        if self.hasRestore:
            self.hbox.Add(
                self.restoreButton, 0, wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.vbox.Add(self.hbox, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)

        self.contentBox = wx.BoxSizer(wx.VERTICAL)
        self.content.SetSizer(self.contentBox)

        self.vbox.Add(self.content, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(self.vbox)
        self.Layout()

        # Undo
        self.undoObjects = []

    def createSection(self, name, title=None, tag=None):
        section = SectionPanel(self.content, title, tag=tag)
        section.setUndoCallbacks(self.appendUndo, self.releaseUndo)
        self.sections.update({name: section})
        self.contentBox.Add(section, 0, wx.ALL | wx.EXPAND, 5)
        self.Layout()
        self.GetParent().Layout()
        return section

    def clearSections(self):
        self.sections.clear()
        self.contentBox.Clear()

    def updateCallbacks(self):
        pass

    def resetProfile(self):
        for section in self.sections.values():
            section.resetProfile()

    def updateProfile(self):
        for section in self.sections.values():
            section.updateProfile()

    def onUndoButtonClicked(self, event):
        if self.undo():
            self.undoButton.Enable()
        else:
            self.undoButton.Disable()

    def onRestoreButtonClicked(self, event):
        dlg = wx.MessageDialog(
            self,
            _("This will reset all section settings to defaults.\n"
              "Unless you have saved your current profile, all section settings will be lost!\n"
              "Do you really want to reset?"), self.title, wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        if result:
            self.resetProfile()
            self.restoreButton.Disable()
            if self.hasUndo:
                del self.undoObjects[:]
                self.undoButton.Disable()

    def appendUndo(self, _object):
        if self.hasUndo:
            self.undoObjects.append(_object)

    def releaseUndo(self):
        if self.hasUndo:
            self.undoButton.Enable()
        if self.hasRestore:
            self.restoreButton.Enable()

    def undo(self):
        if len(self.undoObjects) > 0:
            objectToUndo = self.undoObjects.pop()
            objectToUndo.undo()
        return len(self.undoObjects) > 0

    def enableRestore(self, value):
        if hasattr(self, 'restoreButton'):
            if value:
                self.restoreButton.Enable()
            else:
                self.restoreButton.Disable()

    def show(self):
        if self.callback is not None:
            self.callback()
        self.content.Show()


class SectionPanel(wx.Panel):

    def __init__(self, parent, title=None, tag=None):
        wx.Panel.__init__(self, parent)
        self.tag = tag

        # Elements
        if title is not None:
            self.title = TitleText(self, title, bold=False)
        self.items = OrderedDict()

        self.appendUndoCallback = None
        self.releaseUndoCallback = None

        # Layout
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        if title is not None:
            self.vbox.Add(self.title, 0, wx.BOTTOM | wx.TOP | wx.RIGHT | wx.EXPAND, 5)
        self.SetSizer(self.vbox)
        self.Layout()

    # TODO: improve tooltip implementation

    def addItem(self, _type, _name, tooltip=None):
        item = _type(self, _name)
        item.setUndoCallbacks(self.appendUndoCallback, self.releaseUndoCallback)
        if tooltip is None:
            self.items.update({_name: item})
        else:
            self.items.update({_name: (item, tooltip)})
        self.vbox.Add(item, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)
        self.Layout()
        return self

    def updateCallback(self, _name, _callback):
        if isinstance(self.items[_name], tuple):
            self.items[_name][0].setEngineCallback(_callback)
        else:
            self.items[_name].setEngineCallback(_callback)

    def getItem(self, _name):
        return self.items[_name]

    def resetProfile(self):
        for item in self.items.values():
            if isinstance(item, tuple):
                if item[0].IsEnabled():
                    item[0].resetProfile()
            else:
                if item.IsEnabled():
                    item.resetProfile()

    def enable(self, _name):
        if isinstance(self.items[_name], tuple):
            self.items[_name][0].Enable()
        else:
            self.items[_name].Enable()

    def disable(self, _name):
        if isinstance(self.items[_name], tuple):
            self.items[_name][0].Disable()
        else:
            self.items[_name].Disable()

    def updateProfile(self):
        for item in self.items.values():
            if isinstance(item, tuple):
                item[0].updateProfile()
                item[0].label.SetToolTip(wx.ToolTip(item[1]))
            else:
                item.updateProfile()

    def setUndoCallbacks(self, appendUndoCallback=None, releaseUndoCallback=None):
        self.appendUndoCallback = appendUndoCallback
        self.releaseUndoCallback = releaseUndoCallback

    def showItem(self, _name):
        self.items[_name].Show()
        self.Layout()

    def hideItem(self, _name):
        self.items[_name].Hide()
        self.Layout()


class SectionItem(wx.Panel):

    def __init__(self, parent, name, engineCallback=None):
        wx.Panel.__init__(self, parent)
        self.engineCallback = engineCallback
        self.appendUndoCallback = None
        self.releaseUndoCallback = None

        self.undoValues = []

        self.control = None

        self.name = name
        self.setting = profile.settings.getSetting(self.name)

    def setEngineCallback(self, engineCallback=None):
        self.engineCallback = engineCallback

    def setUndoCallbacks(self, appendUndoCallback=None, releaseUndoCallback=None):
        self.appendUndoCallback = appendUndoCallback
        self.releaseUndoCallback = releaseUndoCallback

    def isVisible(self):
        # if profile.settings['basic_mode']:
        #    return self.setting.getCategory() is 'basic'
        # else:
        return True

    def update(self, value, trans=False):
        if self.isVisible():
            self.Show()
            if trans:
                self.control.SetValue(_(value))
            else:
                self.control.SetValue(value)
            self._updateEngine(value)
        else:
            self.Hide()
        self.Layout()
        self.GetParent().Layout()

    def _updateEngine(self, value):
        if self.engineCallback is not None:
            self.engineCallback(value)

    def undo(self):
        if len(self.undoValues) > 0:
            value = self.undoValues.pop()
            profile.settings[self.name] = value
            self.update(value)

    def resetProfile(self):
        profile.settings.resetToDefault(self.name)
        del self.undoValues[:]
        self.updateProfile()


class TitleText(wx.Panel):

    def __init__(self, parent, title, bold=True, handCursor=True):
        wx.Panel.__init__(self, parent)

        # Elements
        self.title = wx.StaticText(self, label=title)
        if bold:
            fontWeight = wx.FONTWEIGHT_BOLD
        else:
            fontWeight = wx.FONTWEIGHT_NORMAL
        self.title.SetFont((wx.Font(wx.SystemSettings.GetFont(
            wx.SYS_ANSI_VAR_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, fontWeight)))
        self.line = wx.StaticLine(self)

        if handCursor:
            self.title.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            self.line.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.title, 0, wx.ALL ^ wx.BOTTOM | wx.EXPAND, 10)
        vbox.Add(self.line, 1, wx.ALL ^ wx.BOTTOM | wx.EXPAND, 5)
        self.SetSizer(vbox)
        self.Layout()


class Slider(SectionItem):
    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        self.flagFirstMove = True

        # Elements
        self.label = wx.StaticText(self, label=self.setting._label)

        self.control = wx.Slider(self, wx.ID_ANY,
                                 profile.settings[name],
                                 profile.settings.getMinValue(name),
                                 profile.settings.getMaxValue(name),
                                 size=(150, -1),
                                 style=wx.SL_LABELS)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_COMMAND_SCROLL_LINEUP, self.onSlider)
        self.control.Bind(wx.EVT_COMMAND_SCROLL_LINEDOWN, self.onSlider)
        self.control.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onSliderReleased)
        self.control.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onSliderTracked)

    def onSlider(self, event):
        value = profile.settings[self.name]
        self.undoValues.append(value)

        if self.appendUndoCallback is not None:
            self.appendUndoCallback(self)

        value = self.control.GetValue()
        profile.settings[self.name] = value
        self._updateEngine(value)

        if self.releaseUndoCallback is not None:
            self.releaseUndoCallback()

    def onSliderReleased(self, event):
        self.flagFirstMove = True
        if self.releaseUndoCallback is not None:
            self.releaseUndoCallback()

    def onSliderTracked(self, event):
        if self.flagFirstMove:
            value = profile.settings[self.name]
            self.undoValues.append(value)
            if self.appendUndoCallback is not None:
                self.appendUndoCallback(self)
            self.flagFirstMove = False
        value = self.control.GetValue()
        profile.settings[self.name] = value
        self._updateEngine(value)

    def updateProfile(self):
        if hasattr(self, 'control'):
            value = profile.settings[self.name]
            self.update(value)


class ComboBox(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        choices = self.setting._possible_values
        _choices = [_(i) for i in choices]

        self.keyDict = dict(zip(_choices, choices))

        # Elements
        self.label = wx.StaticText(self, label=self.setting._label, size=(130, -1))
        self.control = wx.ComboBox(self, wx.ID_ANY,
                                   value=_(profile.settings[self.name]),
                                   choices=_choices,
                                   size=(150, -1),
                                   style=wx.CB_READONLY)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_COMBOBOX, self.onComboBoxChanged)

    def onComboBoxChanged(self, event):
        value = self.keyDict[self.control.GetValue()]
        profile.settings[self.name] = value
        self._updateEngine(value)

    def updateProfile(self):
        if hasattr(self, 'control'):
            value = unicode(profile.settings[self.name])
            self.update(value, trans=True)


class CheckBox(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.label = wx.StaticText(self, label=self.setting._label)
        self.control = wx.CheckBox(self)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_CHECKBOX, self.onCheckBoxChanged)

    def onCheckBoxChanged(self, event):
        self.undoValues.append(profile.settings[self.name])
        value = self.control.GetValue()
        profile.settings[self.name] = value
        self._updateEngine(value)
        if self.appendUndoCallback is not None:
            self.appendUndoCallback(self)
        if self.releaseUndoCallback is not None:
            self.releaseUndoCallback()

    def updateProfile(self):
        if hasattr(self, 'control'):
            value = profile.settings[self.name]
            self.update(value)


class RadioButton(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.label = wx.StaticText(self, label=self.setting._label)
        self.control = wx.RadioButton(self, style=wx.ALIGN_RIGHT)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.TOP | wx.RIGHT | wx.EXPAND, 15)
        hbox.Add(self.control, 1, wx.TOP | wx.EXPAND, 16)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_RADIOBUTTON, self.onRadioButtonChanged)

    def onRadioButtonChanged(self, event):
        self.undoValues.append(profile.settings[self.name])
        value = self.control.GetValue()
        profile.settings[self.name] = value
        self._updateEngine(value)
        if self.appendUndoCallback is not None:
            self.appendUndoCallback(self)
        if self.releaseUndoCallback is not None:
            self.releaseUndoCallback()

    def updateProfile(self):
        if hasattr(self, 'control'):
            value = profile.settings[self.name]
            self.update(value)


class TextBox(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.label = wx.StaticText(self, size=(140, -1), label=self.setting._label)
        self.control = wx.TextCtrl(self, size=(120, -1), style=wx.TE_RIGHT)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_KILL_FOCUS, self.onTextBoxChanged)

    def onTextBoxChanged(self, event):
        self.undoValues.append(profile.settings[self.name])
        value = self.control.GetValue()
        profile.settings[self.name] = value
        self._updateEngine(value)
        if self.appendUndoCallback is not None:
            self.appendUndoCallback(self)
        if self.releaseUndoCallback is not None:
            self.releaseUndoCallback()

    def updateProfile(self):
        if hasattr(self, 'control'):
            value = profile.settings[self.name]
            self.update(value)


class FloatTextBox(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.label = wx.StaticText(self, size=(140, -1), label=self.setting._label)
        self.control = wx.TextCtrl(self, size=(120, -1), style=wx.TE_RIGHT)

        self.control.SetValue_original = self.control.SetValue
        self.control.SetValue = self.SetValue_overwrite
        self.control.GetValue_original = self.control.GetValue
        self.control.GetValue = self.GetValue_overwrite

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_KILL_FOCUS, self.onTextBoxLostFocus)

    def SetValue_overwrite(self, value):
        self.control.SetValue_original(str(value))

    def GetValue_overwrite(self):
        return float(self.control.GetValue_original())

    def onTextBoxLostFocus(self, event):
        self.undoValues.append(profile.settings[self.name])
        try:
            value = self.control.GetValue()
        except:
            self.control.SetValue(profile.settings[self.name])
        else:
            self.control.SetValue(value)
            profile.settings[self.name] = value
            self._updateEngine(value)
            if self.appendUndoCallback is not None:
                self.appendUndoCallback(self)
            if self.releaseUndoCallback is not None:
                self.releaseUndoCallback()

    def updateProfile(self):
        if hasattr(self, 'control'):
            value = profile.settings[self.name]
            self.update(float(value))


# TODO: Create TextBoxArray


class Button(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.control = wx.Button(self, label=self.setting._label)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.control, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_BUTTON, self.onButtonClicked)

    def onButtonClicked(self, event):
        if self.engineCallback is not None:
            self.engineCallback()

    def updateProfile(self):
        if hasattr(self, 'control'):
            self.update(None)

    def update(self, value):
        if self.isVisible():
            self.Show()
        else:
            self.Hide()


class CallbackButton(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.control = wx.Button(self, label=self.setting._label)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.control, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_BUTTON, self.onButtonClicked)

    def onButtonClicked(self, event):
        if self.engineCallback is not None:
            self.control.Disable()
            self.waitCursor = wx.BusyCursor()
            self.engineCallback(lambda r: wx.CallAfter(self.onFinishCallback, r))

    def onFinishCallback(self, ret):
        self.control.Enable()
        if hasattr(self, 'waitCursor'):
            del self.waitCursor

    def updateProfile(self):
        if hasattr(self, 'control'):
            self.update(None)

    def update(self, value):
        if self.isVisible():
            self.Show()
        else:
            self.Hide()


class ToggleButton(SectionItem):

    def __init__(self, parent, name, engineCallback=None):
        SectionItem.__init__(self, parent, name, engineCallback)

        # Elements
        self.control = wx.ToggleButton(self, label=self.setting._label)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.control, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_TOGGLEBUTTON, self.onButtonToggle)

    def onButtonToggle(self, event):
        if self.engineCallback is not None:
            if event.IsChecked():
                function = 0
            else:
                function = 1

            if self.engineCallback[function] is not None:
                self.engineCallback[function]()

    def updateProfile(self):
        if hasattr(self, 'control'):
            self.update(None)

    def update(self, value):
        if self.isVisible():
            self.Show()
        else:
            self.Hide()

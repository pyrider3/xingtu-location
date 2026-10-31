#!/usr/bin/env python3
import os, sys, subprocess, socket, time, threading, urllib.request, json
from pathlib import Path
import gi
gi.require_version('Gtk','3.0')
gi.require_version('WebKit2','4.1')
from gi.repository import Gtk, WebKit2, GLib
D=Path(__file__).resolve().parent
class Window(Gtk.Window):
 def __init__(self):
  super().__init__(title='星图定位')
  self.set_default_size(1280,800)
  self.set_position(Gtk.WindowPosition.CENTER)
  try:self.set_icon_from_file(str(D/'icon.svg'))
  except Exception:pass
  self.view=WebKit2.WebView()
  self.add(self.view)
  self.view.load_uri('http://127.0.0.1:8765/')
  self.connect('delete-event',self.on_close)
  self.connect('destroy',Gtk.main_quit)
  self.show_all()
 def on_close(self, *args):
  self.set_sensitive(False)
  self.set_title('星图定位 · 正在关闭…')
  def cleanup():
   cleared=False
   try:
    req=urllib.request.Request('http://127.0.0.1:8765/shutdown',data=b'{}',headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=20) as response: cleared=json.load(response).get('cleared',False)
   except Exception: pass
   def finish():
    if not cleared:
     dialog=Gtk.MessageDialog(transient_for=self,modal=True,message_type=Gtk.MessageType.INFO,buttons=Gtk.ButtonsType.OK,text='后台已停止')
     dialog.format_secondary_text('未能确认真实定位已恢复。如果手机位置仍不正常，请重启 iPhone。')
     dialog.run();dialog.destroy()
    self.destroy()
    return False
   GLib.idle_add(finish)
  threading.Thread(target=cleanup,daemon=True).start()
  return True

def port_open():
 try:
  with socket.create_connection(('127.0.0.1',8765),timeout=.5):return True
 except OSError:return False
if not port_open():
 subprocess.Popen([sys.executable,str(D/'app.py')],cwd=str(D),start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(50):
  if port_open():break
  time.sleep(.1)
 if not port_open():
  print('无法启动本地服务',file=sys.stderr);sys.exit(1)
Window();Gtk.main()

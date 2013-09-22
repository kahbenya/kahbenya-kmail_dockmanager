#!/usr/bin/env python

#  
#  Copyright (C) 2013 Yuri Lee
# 
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import atexit
import gobject
import glib
import sys
import dbus
import os
import operator
import subprocess
import time

try:
	from dockmanager.dockmanager import DockManagerItem, DockManagerSink, DOCKITEM_IFACE
	from xml.dom import minidom
	from signal import signal, SIGTERM
	from sys import exit
except ImportError, e:
	print e
	exit()

monitor_with_inotify = False #not watching any system files
try:
	import pyinotify
except ImportError, e:
	print "pyinotify not available - not monitoring for new configurations"
	monitor_with_inotify = False

class clientItem(DockManagerItem):
	def __init__(self, sink, path):
		DockManagerItem.__init__(self, sink, path)

		self.map = {} #k,v => action_name, action_method
		self.items = []
                self.sessionBus = dbus.SessionBus()

                self.kmail_connect()
		self.add_options() #add to the menu the list of quick links for mail

        def kmail_connect(self):
                #dbus setup
                #test for kontact being up and hence the kmail2 bus available
                if not filter ((lambda x: 'org.kde.kmail2' in str(x).lower()),self.sessionBus.list_names()):
                    #TODO: investigate starting in background/minimized
                    #subprocess.call('kontact')
                    os.system('kontact --iconify &')
                    time.sleep(3) #ensure kmail is started and registered before getting object
                self.kmail2 = self.sessionBus.get_object('org.kde.kmail2','/KMail')


        def add_options(self):
                self.map['New Message'] = 'newMessage'
                self.items.append(self.add_menu_item("New Message","mail-send",""))
                
	def menu_pressed(self, menu_id):
               #check if kmail is running
            self.kmail_connect() 
	    for actionName, actionMethodName in self.map.iteritems():
                if self.id_map[menu_id] == actionName:
                    #get the function from the service
                    actionMethod = self.kmail2.get_dbus_method(actionMethodName)
                    if actionName == "New Message":
		        actionMethod("","","",False,False,"","")

	def clear_items(self):
                for id in self.items:
                        self.remove_menu_item(id)
                self.map = {}
                self.items = []

	def update_menu(self):
		self.clear_items()
		self.read_places()
		self.add_remote()
		

if monitor_with_inotify:
	class GobjectNotifier(pyinotify.Notifier):
		"""
		This notifier uses a gobject io watch to trigger event processing.

		"""
		def __init__(self, watch_manager, default_proc_fun=None, read_freq=0, threshold=0, timeout=None):
			"""
			Initializes the gobject notifier. See the
			Notifier class for the meaning of the parameters.

			"""
			pyinotify.Notifier.__init__(self, watch_manager, default_proc_fun, read_freq, threshold, timeout)
			gobject.io_add_watch(self._fd, gobject.IO_IN|gobject.IO_PRI, self.handle_read)

		def handle_read(self, source, condition):
			"""
			When gobject tells us we can read from the fd, we proceed processing
			events. This method can be overridden for handling a notification
			differently.

			"""
			self.read_events()
			self.process_events()
			return True

	class clientMonitor(pyinotify.ProcessEvent):
		def my_init(self, item):
			self._item = item

		def process_IN_CREATE(self, event):
			self._item.update_menu()

		def process_IN_DELETE(self, event):
			self._item.update_menu()

class clientSink(DockManagerSink):
	def item_path_found(self, pathtoitem, item):
		if item.Get(DOCKITEM_IFACE, "DesktopFile", dbus_interface="org.freedesktop.DBus.Properties").lower().find("kontact") != -1:
			self.items[pathtoitem] = clientItem(self, pathtoitem)
	def clear_items(self):
		for itempath in self.items:
			self.items[itempath].clear_items()

csink = clientSink()

def cleanup():
	csink.clear_items()
	csink.dispose()

if __name__ == "__main__":
	mainloop = gobject.MainLoop(is_running=True)

	atexit.register(cleanup)
	signal(SIGTERM, lambda signum, stack_frame: exit(1))
	mainloop.run()

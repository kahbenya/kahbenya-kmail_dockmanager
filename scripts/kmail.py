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

kdedir = os.path.expanduser("~/.kde/share/apps")
if not os.path.exists(kdedir):
        kdedir = os.path.expanduser("~/.kde4/share/apps")
if not os.path.exists(kdedir):
	kdedir = None
        print "Can't find $KDEHOME dir"
	exit()

#places = "%s/%s" % (kdedir, "kfileplaces")
#remotes = "%s/%s" % (kdedir, "remoteview")

class clientItem(DockManagerItem):
	def __init__(self, sink, path):
		DockManagerItem.__init__(self, sink, path)

		self.map = {}
		self.items = []
		self.read_places()
		self.add_remote()

		if monitor_with_inotify:
			wm = pyinotify.WatchManager()
			handler = clientMonitor(item=self)
			notifier = GobjectNotifier(wm, default_proc_fun=handler)
			wm.add_watch(places, pyinotify.ALL_EVENTS)
			wm.add_watch(remotes, pyinotify.ALL_EVENTS)

	def read_places(self):
		dom = minidom.parse("%s/%s" % (places, "bookmarks.xml"))
		for node in dom.getElementsByTagName('bookmark'):
			uri=node.getAttribute("href")
			node_list=node.getElementsByTagName("title")[0]
			title=node_list.childNodes[0].nodeValue
			metadata_node = node.getElementsByTagName("bookmark:icon")[0]
			icon = metadata_node.getAttribute("name")
			is_hidden = False
			try:
				node_hidden = node.getElementsByTagName("OnlyInApp")[0]
				is_hidden = True
			except: pass
			try:
				node_hidden = node.getElementsByTagName("IsHidden")[0]
				is_hidden = node_hidden.childNodes[0].nodeValue
			except: pass
			if title in self.id_map.values():
				title = uri
			if is_hidden == "false":
				self.map[uri] = title
				self.items.append(self.add_menu_item(title, icon, ""))

	def add_remote(self):
		ls = os.listdir(remotes)
		for file in ls:
			name = file.replace(".desktop", "")
			self.map[remotes + '/' + file] = name
			self.items.append(self.add_menu_item(name, "folder-remote", ""))

	def menu_pressed(self, menu_id):
		for uri, title in self.map.iteritems():
			if self.id_map[menu_id] == title:
				os.system("dolphin %s &" % uri)

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
		if item.Get(DOCKITEM_IFACE, "DesktopFile", dbus_interface="org.freedesktop.DBus.Properties").lower().find("dolphin") != -1:
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

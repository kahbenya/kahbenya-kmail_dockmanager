Introduction
============
These are some notes made while exploring creating a Dockmanager plugin. Documentation was hard to find and searches resulted in docks and not this specific technology.

Other plugins were looked at and experimented with in the process.

Notes
=====

### Standard across all plugins

    class classItem (DockmanagerItem)
This class seeems to be used to populate the list of items (options) that will appear in the menu.

### Functions
  * `clear_items` - clears the list of items (need to use the remove_menu_item)
  * `menu_pressed` - trigger action on item press
  * `update_menu` - reload the menu items
  * *populate menu* - a custom method that populates the menu properties
  * `self.map` - dictionary that seems to hold custom mappings (not used by all plugins eg kate). This is then used to compare properties when making decisions about menu items (eg dolphin).

Registering of items is done with `self.items.append(self.add_menu_item(<menu-item-name>,<icon-string>, ""))`. This can be used without a mapping in `self.map`. The *&lt;menu-item-name&gt;* is the text seen in the menu when selected. The *&lt;icon-string&gt;* is a reference to a KDE recognized icon name. 
The names were retrieved from the "Select Icon" dialog from the Kmenu editor (right click Kickoff > Edit Applications). Any subsystem which involves icon selection would yield the same dialog and hence information.

DockManager plugins seem to use inotify for some reason, not sure what it is yet.

Boilerplate - `GObjectNotifier` class, `clientsink` class and cleanup functions. These are the same in all the existing plugins viewed and can be copied as is to a new plugin.
 
`clientSink` - seems to get some link to the concerned application.

DBus
====
Depending on the plugin being writtent DBus may be needed. See [Resources](#references).

### DBus Tools
 *qdbusviewer - Using qdbusviewer to find dbus info for relevant program*

Double-click the methods to find their signatures (haven't found (or much looked for) a way to use command line tool qdbus to do this )

Signature will contain the type and the name of the parameters. 
Note: Python not statically typed but the underlying DBus system is and will throw an error if the wrong type is passed. `None` can't be passed, no translation for it.

The signature can be extracted using the Introspection method. The signature is given in the resulting xml data. The translation to Python types is contained in the DBus documentation.

Debugging
=========
Use existing script (eg dolphin) to check out features and effects of methods and techniques
 
 * Issue: Can't see output and don't know what is happening when the plugin is loaded 
 * Solved: Run the script directly with python. When execution of script is ok, the plugin is loaded and theprocess is in foreground. Killing the process unloads the plugin.

In `clientsink` class the check 
  ``` python
  if item.Get(DOCKITEM_IFACE, "DesktopFile", 
        dbus_interface="org.freedesktop.DBus.Properties").lower().find("dolphin") != -1:
  ```
seems to determine the icon(program) to attach the items to, but not sure how to debug this line or how to determine
(with certainty) the program names that it will recognize. At the moment the lowercase name of the 
program(or executable) seems to work. There may be variations on how this check is done but it is still there.


`<plugin>.info` file 
====================
This file is found in the metadata folder in the dockmanager location (eg ~/.local/share/dockmanager).

The appname section does not seem to affect anything, since in testing the menu showed up on Kontact icon when the  value was dolphin(for testing)

icon name/id string - may be the same name used in the code or something else. The source is the same as in the code.



Dev System
==========
`$ lsb_release -a`

 > Distributor ID:	Ubuntu
 > Description:	Ubuntu 13.04
 > Release:	13.04
 > Codename:	raring

`$ uname -r`
> Linux 3.8.0-29-generic #42-Ubuntu SMP  x86_64 GNU/Linux

kdebase-runtime    4:4.10.97-0ubuntu1~ubuntu13.04~ppa1

System tried to located Qt tools under non existent `/usr/lib/x86_64-linux-gnu/qt5/bin/` folder. They were present 
under `/usr/lib/x86_64-linux-gnu/qt4/bin/qdbusviewer`.


References
==========
http://techbase.kde.org/index.php?title=Development/Tutorials/D-Bus/Introduction
https://en.wikibooks.org/wiki/Python_Programming/Dbus
http://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html#interfaces-and-methods
http://www.documentroot.net/en/linux/python-dbus-tutorial (shows how to create dbus service and query it)
http://www.freedesktop.org/wiki/Software/dbus/

Examples
========
Located in the python-dbus-doc package.

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
#         Luis A. Bastião Silva <luis.kop@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import re
import os
import gtk

from ConfigParser import NoSectionError, NoOptionError, DuplicateSectionError

from umit.core.Paths import Path
from umit.core.ScanProfileConf import scan_profile_file
from umit.core.UmitLogging import log
from umit.core.UmitConfigParser import UmitConfigParser
from umit.core.I18N import _

class UmitConf(object):
    def __init__(self):
        self.parser = Path.config_parser

    def save_changes(self):
        self.parser.save_changes()

    def get_colored_diff(self):
        try:
            cd = self.parser.get('diff', 'colored_diff')
            if cd == "False" or \
                cd == "false" or \
                cd == "0" or \
                cd == "" or \
                cd == False:
                return False
            return True
        except:
            return True

    def set_colored_diff(self, enable):
        if not self.parser.has_section('diff'):
            self.parser.add_section('diff')

        self.parser.set('diff', 'colored_diff', str(enable))

    def get_diff_mode(self):
        try: return self.parser.get('diff', 'diff_mode')
        except: return "compare"

    def set_diff_mode(self, diff_mode):
        if not self.parser.has_section('diff'):
            self.parser.add_section('diff')
        
        self.parser.set('diff', 'diff_mode', diff_mode)

    colored_diff = property(get_colored_diff, set_colored_diff)
    diff_mode = property(get_diff_mode, set_diff_mode)


class SearchConfig(UmitConfigParser, object):
    def __init__(self):
        self.parser = Path.config_parser

        self.section_name = "search"
        if not self.parser.has_section(self.section_name):
            self.create_section()

    def save_changes(self):
        self.parser.save_changes()

    def create_section(self):
        self.parser.add_section(self.section_name)
        self.directory = ""
        self.file_extension = "usr"
        self.save_time = "60;Days"
        self.store_results = True
        self.search_db = True

    def _get_it(self, p_name, default):
        return self.parser.get(self.section_name, p_name, default)

    def _set_it(self, p_name, value):
        self.parser.set(self.section_name, p_name, value)
        
    def boolean_sanity(self, attr):
        if attr == True or \
           attr == "True" or \
           attr == "true" or \
           attr == "1":

            return 1

        return 0

    def get_directory(self):
        return self._get_it("directory", "")

    def set_directory(self, directory):
        self._set_it("directory", directory)

    def get_file_extension(self):
        return self._get_it("file_extension", "usr").split(";")

    def set_file_extension(self, file_extension):
        if isinstance(file_extension, list):
            self._set_it("file_extension", ";".join(file_extension))
        elif isinstance(file_extension, basestring):
            self._set_it("file_extension", file_extension)

    def get_save_time(self):
        return self._get_it("save_time", "60;Days").split(";")

    def set_save_time(self, save_time):
        if isinstance(save_time, list):
            self._set_it("save_time", ";".join(save_time))
        elif isinstance(save_time, basestring):
            self._set_it("save_time", save_time)

    def get_store_results(self):
        return self.boolean_sanity(self._get_it("store_results", True))

    def set_store_results(self, store_results):
        self._set_it("store_results", self.boolean_sanity(store_results))

    def get_search_db(self):
        return self.boolean_sanity(self._get_it("search_db", True))

    def set_search_db(self, search_db):
        self._set_it("search_db", self.boolean_sanity(search_db))

    def get_converted_save_time(self):
        try:
            return int(self.save_time[0]) * self.time_list[self.save_time[1]]
        except:
            # If something goes wrong, return a save time of 60 days
            return 60 * 60 * 24 * 60

    def get_time_list(self):
        # Time as key, seconds a value
        return {_("Hours"): 60 * 60,
                _("Days"): 60 * 60 * 24,
                _("Weeks"): 60 * 60 * 24 * 7,
                _("Months"): 60 * 60 * 24 * 7 * 30,
                _("Years"): 60 * 60 * 24 * 7 * 30 * 12,
                _("Minutes"): 60,
                _("Seconds"): 1}
    
    directory = property(get_directory, set_directory)
    file_extension = property(get_file_extension, set_file_extension)
    save_time = property(get_save_time, set_save_time)
    store_results = property(get_store_results, set_store_results)
    search_db = property(get_search_db, set_search_db)
    converted_save_time = property(get_converted_save_time)
    time_list = property(get_time_list)


class Profile(UmitConfigParser, object):
    def __init__(self, user_profile=None, *args):
        UmitConfigParser.__init__(self, *args)

        if not user_profile:
            user_profile = scan_profile_file

        fconf = open(user_profile, 'r')
        self.readfp(fconf, user_profile)

        fconf.close()
        del(fconf)

        self.attributes = {}

    def _get_it(self, profile, attribute):
        if self._verify_profile(profile):
            return self.get(profile, attribute)
        return ""

    def _set_it(self, profile, attribute, value=''):
        if self._verify_profile(profile):
            return self.set(profile, attribute, value)

    def add_profile(self, profile_name, **attributes):
        log.debug(">>> Add Profile '%s': %s" % (profile_name, attributes))
        try:
            self.add_section(profile_name)
        except DuplicateSectionError:
            return None
        except ValueError:
            return None

        for attr in attributes:
            if attr != "options":
                self._set_it(profile_name, attr, attributes[attr])

        options = attributes["options"]
        if isinstance(options, basestring):
            self._set_it(profile_name, "options", options)
            # Assuming there are no values for these options
            options = {}
        elif isinstance(options, dict):
            self._set_it(profile_name, "options", ",".join(options))

        for opt in options:
            if options[opt]:
                self._set_it(profile_name, opt, options[opt])
        self.save_changes()

    def remove_profile(self, profile_name):
        try: self.remove_section(profile_name)
        except: pass
        self.save_changes()

    def _verify_profile(self, profile_name):
        if profile_name not in self.sections():
            return False
        return True

class CommandProfile (Profile, object):
    def __init__(self, user_profile=''):
        if not user_profile:
            user_profile = scan_profile_file
        
        Profile.__init__(self, user_profile)
        
    def get_command(self, profile):
        return self._get_it(profile, 'command')

    def get_hint(self, profile):
        return self._get_it(profile, 'hint')

    def get_description(self, profile):
        return self._get_it(profile, 'description')
    
    def get_annotation(self, profile):
        return self._get_it(profile, 'annotation')
    
    def get_tool(self, profile):
        return self._get_it(profile, 'tool')

    def get_options(self, profile):
        dic = {}
        options_result = self._get_it(profile, 'options')
        if options_result.strip()=='':
            return dic
        
        for opt in options_result.split(','):
            try:
                dic[unicode(opt.strip())] = self._get_it(profile, opt)
            except NoOptionError:
                dic[unicode(opt.strip())] = None
        return dic

    def set_command(self, profile, command=''):
        self._set_it(profile, 'command', command)

    def set_hint(self, profile, hint=''):
        self._set_it(profile, 'hint', hint)
    
    def set_description(self, profile, description=''):
        self._set_it(profile, 'description', description)
    
    def set_annotation (self, profile, annotation=''):
        self._set_it(profile, 'annotation', annotation)
        
    def set_tool (self, profile, tool='nmap'):
        self._set_it(profile, 'tool', tool)
    
    def set_options(self, profile, options={}):
        for opt in options:
            if options[opt]:
                self._set_it(profile, opt, options[opt])
        self._set_it(profile, 'options', ",".join(options))

    def get_profile(self, profile_name):
        return {'profile':profile_name, \
                'command':self.get_command(profile_name), \
                'hint':self.get_hint(profile_name), \
                'description':self.get_description(profile_name), \
                'annotation':self.get_annotation(profile_name),\
                'options':self.get_options(profile_name), \
                'tool':self.get_tool(profile_name)}
    
    
# Preferences


"""
General Settings Configuration class (Core)
"""

class GeneralSettingsConf(UmitConfigParser, object):
    """ 
    General Settings defining the settings like enable splash/warnings
    nmap command, remove history (using targets, and recents class), etc
    """
    def __init__(self):
        """ Constructor generalsettings conf"""
        self.parser = Path.config_parser
        self.section_name = "general_settings"
        if not self.parser.has_section(self.section_name):
            self.create_section()
        self.attributes = {} 
    def create_section(self):
        print "creating general_settings section"
        self.parser.add_section(self.section_name)
        self.splash = True
        self.warnings_extensions = False
        self.silent_root = False
        self.crash_report = True
        self.log = "None"
        self.warnings_save = True
    def boolean_sanity(self, attr):
        if attr == True or \
           attr == "True" or \
           attr == "true" or \
           attr == "1":

            return 1

        return 0

    def _get_it(self, p_name, default):
        return self.parser.get(self.section_name, p_name, default)

    def _set_it(self, p_name, value):
        self.parser.set(self.section_name, p_name, value)
        
    def save_changes(self):
        log.debug('call save changes')
        self.parser.save_changes()
        
    # API
    def get_splash(self):
        return self.boolean_sanity(self._get_it("splash", True))
    def set_splash(self, splash):
        self._set_it("splash", self.boolean_sanity(splash))
    
    def set_warnings_extensions(self, extensions):
        self._set_it("warnings", self.boolean_sanity(extensions))
    def get_warnings_extensions(self):
        return self.boolean_sanity(self._get_it("warnings", True))

    def set_silent_root(self, root):
        self._set_it("silent_root", self.boolean_sanity(root))
    def get_silent_root(self):
        return self.boolean_sanity(self._get_it("silent_root", False))
   
    def set_crash_report(self, crash):
        self._set_it("crash_report", self.boolean_sanity(crash))
    def get_crash_report(self):
        return self.boolean_sanity(self._get_it("crash_report", True))
    
    def get_log(self):
        """
        return str: (None, Debug or File)
        """
        return self._get_it("log", "None")
    def set_log(self, log):
        self._set_it("log", log)
        
    def get_log_file(self):
        return self._get_it("log_file", "umit.log")
    def set_log_file(self, filename):
        self._set_it("log_file", filename)
    
    
    def set_warnings_save(self, save):
        self._set_it("warnings_save", self.boolean_sanity(save))
    def get_warnings_save(self):
        return self.boolean_sanity(self._get_it("warnings_save", True))
        
    splash = property(get_splash, set_splash)
    warnings_extensions = property(get_warnings_extensions, \
                                   set_warnings_extensions)
    silent_root = property(get_silent_root, set_silent_root)
    crash_report = property(get_crash_report, set_crash_report)
    log = property(get_log, set_log)
    log_file = property(get_log_file, set_log_file)
    warnings_save = property(get_warnings_save, set_warnings_save) 

"""
Expose settings 
"""

class ExposeConf(UmitConfigParser, object):
    """ 
    Expose 
    """
    def __init__(self):
        """ Constructor expose_settings conf"""
        self.parser = Path.config_parser
        self.section_name = "expose"
        if not self.parser.has_section(self.section_name):
            self.create_section()
        self.attributes = {} 
    def create_section(self):
        self.parser.add_section(self.section_name)
        self.icons_toolbar = "Both"
        self.show_toolbar = True
        self.host_list = True
        self.details = True
        self.page_inside = True
        
    def boolean_sanity(self, attr):
        if attr == True or \
           attr == "True" or \
           attr == "true" or \
           attr == "1":

            return 1

        return 0

    def _get_it(self, p_name, default):
        return self.parser.get(self.section_name, p_name, default)

    def _set_it(self, p_name, value):
        self.parser.set(self.section_name, p_name, value)
        
    def save_changes(self):
        log.debug('call save changes')
        self.parser.save_changes()
        
    def get_icons_toolbar_size(self):
        return self._get_it("icons_toolbar_size", "")
    def set_icons_toolbar_size(self, icons):
        self._set_it("icons_toolbar_size", icons)
        
    def get_icons_toolbar(self):
        return self._get_it("icons_toolbar", "")
    def set_icons_toolbar(self, icons):
        self._set_it("icons_toolbar", icons)
            
    def get_show_toolbar(self):
        return self.boolean_sanity(self._get_it("show_toolbar", True))
    
    def set_show_toolbar(self, toolbar):
        self._set_it("show_toolbar", self.boolean_sanity(toolbar))
        
    def get_host_list(self):
        return self.boolean_sanity(self._get_it("host_list", True))
    
    def set_host_list(self, hl):
        self._set_it("host_list", self.boolean_sanity(hl)) 
        
    def set_details(self, details):
        self._set_it("details", self.boolean_sanity(details)) 
    def get_details(self):
        return self.boolean_sanity(self._get_it("details", True))
    
    def get_page_inside(self):
        return self.boolean_sanity(self._get_it("page_inside", True))
    
    def set_page_inside(self, page):
        self._set_it("page_inside", self.boolean_sanity(page)) 
      
    icons_toolbar_size = property(get_icons_toolbar_size,set_icons_toolbar_size)
    icons_toolbar = property(get_icons_toolbar,set_icons_toolbar)
    show_toolbar = property(get_show_toolbar, set_show_toolbar)
    host_list = property(get_host_list, set_host_list)
    details = property(get_details, set_details)
    page_inside = property(get_page_inside, set_page_inside)
    
    
class ProfilesConf(UmitConfigParser, object):
    """ 
    Profiles
    """
    def __init__(self):
        """ Constructor profiles conf"""
        self.parser = Path.config_parser
        self.section_name = "profiles"
        if not self.parser.has_section(self.section_name):
            self.create_section()
        self.attributes = {} 
    def create_section(self):
        self.parser.add_section(self.section_name)

    def _get_it(self, p_name, default):
        return self.parser.get(self.section_name, p_name, default)

    def _set_it(self, p_name, value):
        self.parser.set(self.section_name, p_name, value)
        
    def get_profile(self):
        return self._get_it("profile", "")
    def set_profile(self, profile):
        self._set_it("profile", profile)
        
    def get_wizard(self):
        return self._get_it("wizard", "")
    def set_wizard(self, wizard):
        self._set_it("wizard", wizard)
    
    def get_options(self):
        return self._get_it("options", "")
    def set_options(self, options):
        self._set_it("options", options)
        
    def get_scan_profiles(self):
        return self._get_it("scan_profile", "")
    def set_scan_profiles(self, profile):
        self._set_it("scan_profile", profile)
        
    profile = property(get_profile, set_profile)
    scan_profiles = property(get_scan_profiles, set_scan_profiles)
    options = property(get_options, set_options)
    wizard = property(get_wizard, set_wizard)
    
    
"""
Network settings 
"""

class NetworkConf(UmitConfigParser, object):
    """ 
    Network Settings
    """
    def __init__(self):
        """ Constructor network_settings conf"""
        self.parser = Path.config_parser
        self.section_name = "network"
        if not self.parser.has_section(self.section_name):
            self.create_section()
        self.attributes = {} 
    def create_section(self):
        self.parser.add_section(self.section_name)
        self.proxy_enable = False 
        self.hostname = ""
        self.port = ""
        self.username = ""
        self.password = ""
        
    def boolean_sanity(self, attr):
        if attr == True or \
           attr == "True" or \
           attr == "true" or \
           attr == "1":

            return 1

        return 0

    def _get_it(self, p_name, default):
        return self.parser.get(self.section_name, p_name, default)

    def _set_it(self, p_name, value):
        self.parser.set(self.section_name, p_name, value)
        
    def save_changes(self):
        log.debug('call save changes - network settings')
        self.parser.save_changes()
   
    # API
    
    def get_proxy(self):
        return self.boolean_sanity(self._get_it("proxy", False))   
    def set_proxy(self, proxy):
        self._set_it("proxy", self.boolean_sanity(proxy))
    
    def get_hostname(self):
        return self._get_it("hostname", "")
    def set_hostname(self, hostname):
        self._set_it("hostname", hostname)
        
    def get_port(self):
        return self._get_it("port", "80")
    def set_port(self, port):
        self._set_it("port", str(port))
        
    def get_username(self):
        return self._get_it("username", "")
    def set_username(self, username):
        self._set_it("username", username)
        
    def get_password(self):
        return self._get_it("username", "")
    def set_password(self, password):
        self._set_it("password", password)
        
    
        
    proxy = property(get_proxy, set_proxy)
    hostname = property(get_hostname, set_hostname)
    port = property(get_port, set_port)
    username = property(get_username, set_username)
    password = property(get_password, set_password)    


class NmapOutputHighlight(object):
    setts = ["bold", "italic", "underline", "text", "highlight", "regex"]
    
    def __init__(self):
        self.parser = Path.config_parser

    def save_changes(self):
        self.parser.save_changes()

    def __get_it(self, p_name):
        property_name = "%s_highlight" % p_name

        try:
            return self.sanity_settings([self.parser.get(property_name,
                                                         prop,
                                                         True) \
                                         for prop in self.setts])
        except:
            settings = []
            prop_settings = self.default_highlights[p_name]
            settings.append(prop_settings["bold"])
            settings.append(prop_settings["italic"])
            settings.append(prop_settings["underline"])
            settings.append(prop_settings["text"])
            settings.append(prop_settings["highlight"])
            settings.append(prop_settings["regex"])

            self.__set_it(p_name, settings)

            return self.sanity_settings(settings)

    def __set_it(self, property_name, settings):
        property_name = "%s_highlight" % property_name
        settings = self.sanity_settings(list(settings))

        for pos in xrange(len(settings)):
            self.parser.set(property_name, self.setts[pos], settings[pos])

    def sanity_settings(self, settings):
        """This method tries to convert insane settings to sanity ones ;-)
        If user send a True, "True" or "true" value, for example, it tries to
        convert then to the integer 1.
        Same to False, "False", etc.

        Sequence: [bold, italic, underline, text, highlight, regex]
        """
        #log.debug(">>> Sanitize %s" % str(settings))
        
        settings[0] = self.boolean_sanity(settings[0])
        settings[1] = self.boolean_sanity(settings[1])
        settings[2] = self.boolean_sanity(settings[2])

        tuple_regex = "[\(\[]\s?(\d+)\s?,\s?(\d+)\s?,\s?(\d+)\s?[\)\]]"
        if isinstance(settings[3], basestring):
            settings[3] = [int(t) \
                           for t in re.findall(tuple_regex, settings[3])[0]]

        if isinstance(settings[4], basestring):
            settings[4]= [int(h) \
                          for h in re.findall(tuple_regex, settings[4])[0]]

        return settings

    def boolean_sanity(self, attr):
        if attr == True or attr == "True" or attr == "true" or attr == "1":
            return 1
        return 0

    def get_date(self):
        return self.__get_it("date")

    def set_date(self, settings):
        self.__set_it("date", settings)

    def get_hostname(self):
        return self.__get_it("hostname")

    def set_hostname(self, settings):
        self.__set_it("hostname", settings)

    def get_ip(self):
        return self.__get_it("ip")

    def set_ip(self, settings):
        self.__set_it("ip", settings)

    def get_port_list(self):
        return self.__get_it("port_list")

    def set_port_list(self, settings):
        self.__set_it("port_list", settings)

    def get_open_port(self):
        return self.__get_it("open_port")

    def set_open_port(self, settings):
        self.__set_it("open_port", settings)

    def get_closed_port(self):
        return self.__get_it("closed_port")

    def set_closed_port(self, settings):
        self.__set_it("closed_port", settings)

    def get_filtered_port(self):
        return self.__get_it("filtered_port")

    def set_filtered_port(self, settings):
        self.__set_it("filtered_port", settings)

    def get_details(self):
        return self.__get_it("details")

    def set_details(self, settings):
        self.__set_it("details", settings)
        
    def get_enable(self):
        enable = True
        try:
            enable = self.parser.get("output_highlight", "enable_highlight")
        except NoSectionError:
            self.parser.set("output_highlight", "enable_highlight", str(True))
        
        if enable == "False" or enable == "0" or enable == "":
            return False
        return True

    def set_enable(self, enable):
        if enable == False or enable == "0" or enable is None or enable == "":
            self.parser.set("output_highlight", "enable_highlight", str(False))
        else:
            self.parser.set("output_highlight", "enable_highlight", str(True))

    date = property(get_date, set_date)
    hostname = property(get_hostname, set_hostname)
    ip = property(get_ip, set_ip)
    port_list = property(get_port_list, set_port_list)
    open_port = property(get_open_port, set_open_port)
    closed_port = property(get_closed_port, set_closed_port)
    filtered_port = property(get_filtered_port, set_filtered_port)
    details = property(get_details, set_details)
    enable = property(get_enable, set_enable)

    # These settings are made when there is nothing set yet. They set
    # the "factory" default to highlight colors
    default_highlights = {
            "date": {
                "bold": str(True),
                "italic": str(False),
                "underline": str(False),
                "text": [0, 0, 0],
                "highlight": [65535, 65535, 65535],
                "regex": "\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}\s.{1,4}"
                },
            "hostname": {
                "bold": str(True),
                "italic": str(True),
                "underline": str(True),
                "text": [0, 111, 65535],
                "highlight": [65535, 65535, 65535],
                "regex":"(\w{2,}://)?(([a-zA-Z0-9]|-)+\.)+([a-zA-Z]{2,}|com|org|net|gov|mil|biz|info|mobi|name|aero|jobs|museum)([\w\d#/])*"
                },
            "ip": {
                "bold": str(True),
                "italic": str(False),
                "underline": str(False),
                "text": [0, 0, 0],
                "highlight": [65535, 65535, 65535],
                "regex": "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                },
            "port_list": {
                "bold": str(True),
                "italic": str(False),
                "underline": str(False),
                "text": [0, 1272, 28362],
                "highlight": [65535, 65535, 65535],
                "regex": "PORT\s+STATE\s+SERVICE(\s+VERSION)?[^\n]*"
                },
            "open_port": {
                "bold": str(True),
                "italic": str(False),
                "underline": str(False),
                "text": [0, 41036, 2396],
                "highlight": [65535, 65535, 65535],
                "regex": "\d{1,5}/.{1,5}\s+open\s+.*"
                },
            "closed_port": {
                "bold": str(False),
                "italic": str(False),
                "underline": str(False),
                "text": [65535, 0, 0],
                "highlight": [65535, 65535, 65535],
                "regex":"\d{1,5}/.{1,5}\s+closed\s+.*"
                },
            "filtered_port": {
                "bold": str(False),
                "italic": str(False),
                "underline": str(False),
                "text": [38502, 39119, 0],
                "highlight": [65535, 65535, 65535],
                "regex": "\d{1,5}/.{1,5}\s+filtered\s+.*"
                },
            "details": {
                    "bold": str(True),
                    "italic": str(False),
                    "underline": str(True),
                    "text": [0, 0, 0],
                    "highlight": [65535, 65535, 65535],
                    "regex": "^(\w{2,}[\s]{,3}){,4}:"
                    }
            }

class DiffColors(object):
    def __init__(self):
        self.parser = Path.config_parser
        self.section_name = "diff_colors"

    def save_changes(self):
        self.parser.save_changes()

    def __get_it(self, p_name):
        return self.sanity_settings(self.parser.get(self.section_name, p_name))

    def __set_it(self, property_name, settings):
        settings = self.sanity_settings(settings)
        self.parser.set(self.section_name, property_name, settings)

    def sanity_settings(self, settings):
        log.debug(">>> Sanitize %s" % str(settings))
        
        tuple_regex = "[\(\[]\s?(\d+)\s?,\s?(\d+)\s?,\s?(\d+)\s?[\)\]]"
        if isinstance(settings, basestring):
            settings = [int(t) for t in re.findall(tuple_regex, settings)[0]]

        return settings

    def get_unchanged(self):
        return self.__get_it("unchanged")

    def set_unchanged(self, settings):
        self.__set_it("unchanged", settings)

    def get_added(self):
        return self.__get_it("added")

    def set_added(self, settings):
        self.__set_it("added", settings)

    def get_modified(self):
        return self.__get_it("modified")

    def set_modified(self, settings):
        self.__set_it("modified", settings)

    def get_not_present(self):
        return self.__get_it("not_present")

    def set_not_present(self, settings):
        self.__set_it("not_present", settings)

    unchanged = property(get_unchanged, set_unchanged)
    added = property(get_added, set_added)
    modified = property(get_modified, set_modified)
    not_present = property(get_not_present, set_not_present)

class Plugins(object):
    def __init__(self):
        self.parser = Path.config_parser
        self.section_name = "plugins"
        self.separator = os.pathsep

        if not self.parser.has_section(self.section_name):
            self.create_section()

    def save_changes(self):
        self.parser.save_changes()

    def create_section(self):
        from os.path import join
        self.paths = [join(Path.config_dir, "plugins")]
        self.plugins = ""

    def __get_it(self, p_name):
        value = None

        try:
            try:
                value = self.parser.get(self.section_name, p_name)
            except:
                pass
        finally:
            return self.sanity_settings(value)

    def __set_it(self, property_name, settings):
        settings = self.sanity_settings(settings)
        self.parser.set(self.section_name, property_name, settings)

    def sanity_settings(self, settings):
        # FIXME: more sensed :D
        if not settings:
            return ""
        return settings

    def get_paths(self):
        return filter(None, self.__get_it("paths").split(self.separator))

    def set_paths(self, settings):
        self.__set_it("paths", self.separator.join(settings))

    def get_plugins(self):
        return filter(None, self.__get_it("plugins").split(self.separator))

    def set_plugins(self, settings):
        self.__set_it("plugins", self.separator.join(settings))

    paths = property(get_paths, set_paths)
    plugins = property(get_plugins, set_plugins)
    

def boolean_sanity_(attr):
    if attr == True or attr == "True" or attr == "true" or attr == "1":
        return True
    return False

def simple_property(to_python, from_python):
    def _property(attrname, default):
        def get(self):
            result = default
            try:
                result = to_python(self.parser.get(self.section_name, attrname))
            except (NoSectionError, NoOptionError):
                self.parser.set(self.section_name, attrname, from_python(default))
            return result

        def set(self, value):
            self.parser.set(self.section_name, attrname, from_python(value))

        return (attrname, get, set)
    return _property

def enum_property(enum_list):
    to_python_dict = dict(enum_list)
    from_python_dict = dict([(v, k) for k, v in enum_list])
    return simple_property(to_python_dict.get, from_python_dict.get)

def list_property():
    def to_python(x):
        return [s.strip() for s in x.split(';')]
    def from_python(x):
        return ";".join(x)
    return simple_property(to_python, from_python)

bool_property = simple_property(boolean_sanity_, str)
int_property = simple_property(int, str)
str_property = simple_property(str, str)
float_property = simple_property(float, str)
color_property = simple_property(lambda x: gtk.gdk.Color(*color_sanity(x)),
                                 lambda x: str([x.red, x.green, x.blue]))
wrap_property = enum_property([('none', gtk.WRAP_NONE),
                               ('char', gtk.WRAP_CHAR),
                               ('word', gtk.WRAP_WORD)])
columns_property = list_property()
    
class metaConfig(type):
    def __new__(cls, classname, bases, classdict):
        params = classdict.get('__params__', [])
        for attrname, get, set in params:
            classdict['get_' + attrname] = get
            classdict['set_' + attrname] = set
            classdict[attrname] = property(get, set)
        return type.__new__(cls, classname, bases, classdict)
    
class NSEManagerConfig(object):
    __metaclass__ = metaConfig
    __params__ = [
        bool_property('use_internal_editor', True),
        str_property('external_command', 'gedit %%s'),
        columns_property('columns_visible', ['I', 'Name', 'Type', 'ID']),
        columns_property('columns_order',
                      ['I', 'Name', 'Type', 'Description', 'Author', 'Categories', 'ID']),
        bool_property('view_categories', True),
        bool_property('view_description', True),
        bool_property('view_toolbar', True),
        bool_property('view_statusbar', True),
        str_property('http_proxy', ":3128"),
        str_property('ftp_proxy', ":3128")
        ]

    def __init__(self, *args):
        self.parser = Path.config_parser
        self.section_name = "script_manager"
        
    def save_changes(self):
        pass
        
class EditorConfig(object):
    __metaclass__ = metaConfig
    __params__ = [
        bool_property('show_line_numbers', True),
        bool_property('use_system_font', True),
        str_property('font', 'Monospace 10'),
        bool_property('auto_indent', True),
        bool_property('check_brackets', True),
        int_property('tabs_width', 8),
        bool_property('insert_spaces_instead_of_tabs', True),
        bool_property('highlight_current_line', True),
        wrap_property('wrap_mode', gtk.WRAP_NONE),
        bool_property('show_margin', True),
        int_property('margin', 80),
        bool_property('smart_home_end', True),
        bool_property('use_default_theme', True),
        color_property('text_color', gtk.gdk.Color(0, 0, 0)),
        color_property('background_color', gtk.gdk.Color(65535, 65535, 65535)),
        color_property('selected_color', gtk.gdk.Color(65535, 65535, 65535)),
        color_property('selection_color', gtk.gdk.Color(0, 0, 40092)),
        bool_property('view_toolbar', True),
        bool_property('view_statusbar', True),
        bool_property('enable_highlight', True),
        str_property('wizard_author', ''),
        str_property('wizard_version', '1.0.0'),
        str_property('wizard_license', 'See nmaps COPYING for licence')
        ]

    def __init__(self):
        self.parser = Path.config_parser
        self.section_name = "editor"
        
        
        
class MapperConf(object):
    """ 
    Topology Settings
    """        
    __metaclass__ = metaConfig
    __params__ = [
        int_property('frames', 69),
        int_property('interpolation', 1),
        int_property('layout', 1),
        float_property('zoom', 1.0),
        int_property('ring', 33),
        int_property('lower_ring', 11),
        columns_property('view', ['address','hostname','icon','ring','region','slow'])
        ]

    def __init__(self, *args):
        self.parser = Path.config_parser
        self.section_name = "mapper"
    

# Exceptions
class ProfileNotFound:
    def __init__ (self, profile):
        self.profile = profile
    def __str__ (self):
        return "No profile named '"+self.profile+"' found!"

class ProfileCouldNotBeSaved:
    def __init__ (self, profile):
        self.profile = profile
    def __str__ (self):
        return "Profile named '"+self.profile+"' could not be saved!"


if __name__ == "__main__":
    pass

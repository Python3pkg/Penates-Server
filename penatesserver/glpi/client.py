# -*- coding: utf-8 -*-
import xmlrpclib

__author__ = 'Matthieu Gallet'


# Just get hostname from a GLPI webservices
class Glpi_arbiter(object):
    def __init__(self, mod_conf):
        self.uri = getattr(mod_conf, 'uri', 'http://localhost/glpi/plugins/webservices/xmlrpc.php')
        self.login_name = getattr(mod_conf, 'login_name', 'shinken')
        self.login_password = getattr(mod_conf, 'login_password', 'shinken')
        self.tag = getattr(mod_conf, 'tag', '')
        self.tags = getattr(mod_conf, 'tags', '')

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        self.con = xmlrpclib.ServerProxy(self.uri)
        arg = {'login_name': self.login_name, 'login_password': self.login_password}
        res = self.con.glpi.doLogin(arg)
        self.session = res['session']

    # Ok, main function that will load config from GLPI
    def get_objects(self):
        r = {'commands': [],
             'timeperiods': [],
             'hosts': [],
             'hostgroups': [],
             'servicestemplates': [],
             'services': [],
             'contacts': []}
        if len(self.tags) == 0:
            self.tags = self.tag

        try:
            self.tags = self.tags.split(',')
        except:
            pass

        for tag in self.tags:
            tag = tag.strip()

            # iso8859 is necessary because Arbiter does not deal with UTF8 objects !
            arg = {'session': self.session, 'iso8859': '1', 'tag': tag}

            # Get commands
            all_commands = self.con.monitoring.shinkenCommands(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for command_info in all_commands:
                h = command_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['commands']:
                    r['commands'].append(h)

            # Get hosts
            all_hosts = self.con.monitoring.shinkenHosts(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for host_info in all_hosts:
                h = host_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['hosts']:
                    r['hosts'].append(h)

            # Get hostgroups
            all_hostgroups = self.con.monitoring.shinkenHostgroups(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for hostgroup_info in all_hostgroups:
                h = hostgroup_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['hostgroups']:
                    r['hostgroups'].append(h)

            # Get templates
            all_templates = self.con.monitoring.shinkenTemplates(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for template_info in all_templates:
                h = template_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['servicestemplates']:
                    r['servicestemplates'].append(h)

            # Get services
            all_services = self.con.monitoring.shinkenServices(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for service_info in all_services:
                h = service_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['services']:
                    r['services'].append(h)

            # Get contacts
            all_contacts = self.con.monitoring.shinkenContacts(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for contact_info in all_contacts:
                h = contact_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['contacts']:
                    r['contacts'].append(h)

            # Get timeperiods
            all_timeperiods = self.con.monitoring.shinkenTimeperiods(arg)
            # List attributes provided by Glpi and that need to be deleted for Shinken
            deleted_attributes = []
            for timeperiod_info in all_timeperiods:
                h = timeperiod_info
                for attribute in deleted_attributes:
                    if attribute in h:
                        del h[attribute]

                if h not in r['timeperiods']:
                    r['timeperiods'].append(h)

        r['services'] = r['services'] + r['servicestemplates']
        del r['servicestemplates']

        return r

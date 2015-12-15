# -*- coding: utf-8 -*-
from django.contrib import admin

from penatesserver.models import Host, MountPoint, Service

__author__ = 'Matthieu Gallet'


class HostAdmin(admin.ModelAdmin):
    fields = (
        ('fqdn', 'owner'),
        ('main_ip_address', 'main_mac_address'),
        ('admin_ip_address', 'admin_mac_address'),
        ('serial', 'model_name', 'location', ),
        ('os_name', 'bootp_filename', ),
        ('proc_model', 'proc_count', 'core_count', ),
        ('memory_size', 'disk_size', ),
    )
    list_display = ('fqdn', 'main_ip_address', 'admin_ip_address', 'serial', 'proc_count', 'core_count',
                    'memory_size', 'disk_size', )
    ordering = ('fqdn', )
    search_fields = ('fqdn', 'serial', 'main_ip_address', 'admin_ip_address', )


admin.site.register(Host, admin_class=HostAdmin)
admin.site.register(MountPoint)
admin.site.register(Service)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse

from django.core.management import BaseCommand

from penatesserver.glpi.models import ShinkenService

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('host_name', help='Host fqdn')
        parser.add_argument('check_command', help='Nagios check_command')
        parser.add_argument('--delete', help='Service description', default=False, action='store_true')
        parser.add_argument('--hostgroup_name', default=None)
        parser.add_argument('--service_description', default=None)
        parser.add_argument('--display_name', default=None)
        parser.add_argument('--servicegroups', default=None)
        parser.add_argument('--is_volatile', default=None)
        parser.add_argument('--initial_state', default=None)
        parser.add_argument('--max_check_attempts', default=None)
        parser.add_argument('--check_interval', default=None, type=int)
        parser.add_argument('--retry_interval', default=None, type=int)
        parser.add_argument('--active_checks_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--passive_checks_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--check_period', default=None)
        parser.add_argument('--obsess_over_service', default=None)
        parser.add_argument('--check_freshness', default=None)
        parser.add_argument('--freshness_threshold', default=None)
        parser.add_argument('--event_handler', default=None)
        parser.add_argument('--event_handler_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--low_flap_threshold', default=None)
        parser.add_argument('--high_flap_threshold', default=None)
        parser.add_argument('--flap_detection_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--flap_detection_options', default=None)
        parser.add_argument('--process_perf_data', default=None)
        parser.add_argument('--retain_status_information', default=None)
        parser.add_argument('--retain_nonstatus_information', default=None)
        parser.add_argument('--notification_interval', default=None, type=int)
        parser.add_argument('--first_notification_delay', default=None)
        parser.add_argument('--notification_period', default=None)
        parser.add_argument('--notification_options', default=None)
        parser.add_argument('--notifications_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--contacts', default=None)
        parser.add_argument('--contact_groups', default=None)
        parser.add_argument('--stalking_options', default=None)
        parser.add_argument('--notes', default=None)
        parser.add_argument('--notes_url', default=None)
        parser.add_argument('--action_url', default=None)
        parser.add_argument('--poller_tag', default=None)
        parser.add_argument('--icon_set', default=None)
        parser.add_argument('--icon_image', default=None)
        parser.add_argument('--icon_image_alt', default=None)
        parser.add_argument('--reactionner_tag', default=None)
        parser.add_argument('--duplicate_foreach', default=None)
        parser.add_argument('--service_dependencies', default=None)
        parser.add_argument('--business_impact', default=None)
        parser.add_argument('--maintenance_period', default=None)
        parser.add_argument('--host_dependency_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--labels', default=None)
        parser.add_argument('--business_rule_output_template', default=None)
        parser.add_argument('--business_rule_smart_notifications', default=None)
        parser.add_argument('--business_rule_downtime_as_ack', default=None)
        parser.add_argument('--business_rule_host_notification_options', default=None)
        parser.add_argument('--business_rule_service_notification_options', default=None)
        parser.add_argument('--snapshot_enabled', default=None, choices=['0', '1'])
        parser.add_argument('--snapshot_command', default=None)
        parser.add_argument('--snapshot_period', default=None)
        parser.add_argument('--snapshot_criteria', default=None)
        parser.add_argument('--snapshot_interval', default=None, type=int)
        parser.add_argument('--trigger_name', default=None)
        parser.add_argument('--trigger_broker_raise_enabled', default=None, choices=['0', '1'])

    def handle(self, *args, **options):
        values = {k: options[k] for k in ShinkenService.get_field_list() if options[k] is not None}
        check_command = options['check_command']
        host_name = options['host_name']
        if ShinkenService.objects.filter(host_name=host_name, check_command=check_command)\
                .update(**values) == 0:
            ShinkenService(**values).save()
            self.stdout.write(self.style.WARNING('%s:%s created') % (host_name, check_command))
        elif options['delete']:
            ShinkenService.objects.filter(host_name=host_name, check_command=check_command).delete()
            self.stdout.write(self.style.ERROR('%s:%s deleted') % (host_name, check_command))


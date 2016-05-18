# -*- coding: utf-8 -*-
from django.db import models
from django.utils import six
from django.utils.six import text_type

from penatesserver.utils import clean_string

__author__ = 'Matthieu Gallet'


class ShinkenService(models.Model):
    host_name = models.CharField('host_name', max_length=255, db_index=True)
    hostgroup_name = models.CharField('hostgroup_name', max_length=255, default=None, null=True, blank=True)
    service_description = models.CharField('service_description', max_length=255, default=None, null=True, blank=True)
    display_name = models.CharField('display_name', max_length=255, default=None, null=True, blank=True)
    servicegroups = models.CharField('servicegroups', max_length=255, default=None, null=True, blank=True)
    is_volatile = models.IntegerField('is_volatile', default=None, null=True, blank=True,
                                      choices=[(0, '0'), (1, '1')])
    check_command = models.CharField('check_command', max_length=255, default=None, null=True, blank=True)
    initial_state = models.CharField('initial_state', max_length=255, default=None, null=True, blank=True,
                                     choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    max_check_attempts = models.IntegerField('max_check_attempts', default=None, null=True, blank=True)
    check_interval = models.IntegerField('check_interval', default=None, null=True, blank=True)
    retry_interval = models.IntegerField('retry_interval', default=None, null=True, blank=True)
    active_checks_enabled = models.IntegerField('active_checks_enabled', default=None, null=True, blank=True,
                                                choices=[(0, '0'), (1, '1')])
    passive_checks_enabled = models.IntegerField('active_checks_enabled', default=None, null=True, blank=True,
                                                 choices=[(0, '0'), (1, '1')])
    check_period = models.CharField('check_period', max_length=255, default=None, null=True, blank=True)
    obsess_over_service = models.IntegerField('obsess_over_service', default=None, null=True, blank=True,
                                              choices=[(0, '0'), (1, '1')])
    check_freshness = models.IntegerField('check_freshness', default=None, null=True, blank=True,
                                          choices=[(0, '0'), (1, '1')])
    freshness_threshold = models.IntegerField('freshness_threshold', default=None, null=True, blank=True)
    event_handler = models.CharField('event_handler', max_length=255, default=None, null=True, blank=True)
    event_handler_enabled = models.IntegerField('event_handler_enabled', default=None, null=True, blank=True,
                                                choices=[(0, '0'), (1, '1')])
    low_flap_threshold = models.FloatField('low_flap_threshold', default=None, null=True, blank=True)
    high_flap_threshold = models.FloatField('high_flap_threshold', default=None, null=True, blank=True)
    flap_detection_enabled = models.IntegerField('flap_detection_enabled', default=None, null=True, blank=True,
                                                 choices=[(0, '0'), (1, '1')])
    flap_detection_options = models.CharField('flap_detection_options', max_length=255, default=None, null=True,
                                              blank=True,
                                              choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    process_perf_data = models.IntegerField('process_perf_data', default=None, null=True, blank=True,
                                            choices=[(0, '0'), (1, '1')])
    retain_status_information = models.IntegerField('retain_status_information', default=None, null=True, blank=True,
                                                    choices=[(0, '0'), (1, '1')])
    retain_nonstatus_information = models.IntegerField('retain_nonstatus_information', default=None, null=True,
                                                       blank=True, choices=[(0, '0'), (1, '1')])
    notification_interval = models.IntegerField('notification_interval', default=None, null=True, blank=True)
    first_notification_delay = models.IntegerField('first_notification_delay', default=None, null=True, blank=True)
    notification_period = models.CharField('notification_period', max_length=255, default=None, null=True, blank=True)
    notification_options = models.CharField('notification_options', max_length=255, default=None, null=True, blank=True,
                                            choices=[('r', 'r'), ('w', 'w'), ('u', 'u'), ('c', 'c'), ('f', 'f'),
                                                     ('s', 's')])
    notifications_enabled = models.IntegerField('notifications_enabled', default=None, null=True,
                                                blank=True, choices=[(0, '0'), (1, '1')])
    contacts = models.CharField('contacts', max_length=255, default=None, null=True, blank=True)
    contact_groups = models.CharField('contact_groups', max_length=255, default=None, null=True, blank=True)
    stalking_options = models.CharField('stalking_options', max_length=255, default=None, null=True,
                                        blank=True, choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    notes = models.CharField('notes', max_length=255, default=None, null=True, blank=True)
    notes_url = models.CharField('notes_url', max_length=255, default=None, null=True, blank=True)
    action_url = models.CharField('action_url', max_length=255, default=None, null=True, blank=True)
    poller_tag = models.CharField('poller_tag', max_length=255, default=None, null=True, blank=True)
    icon_set = models.CharField('icon_set', max_length=255, default=None, null=True, blank=True)
    icon_image = models.CharField('icon_image', max_length=255, default=None, null=True, blank=True)
    icon_image_alt = models.CharField('icon_image_alt', max_length=255, default=None, null=True, blank=True)
    reactionner_tag = models.CharField('reactionner_tag', max_length=255, default=None, null=True, blank=True)
    duplicate_foreach = models.CharField('duplicate_foreach', max_length=255, default=None, null=True, blank=True)
    service_dependencies = models.CharField('service_dependencies', max_length=255, default=None, null=True, blank=True)
    business_impact = models.CharField('business_impact', max_length=255, default=None, null=True, blank=True)
    maintenance_period = models.CharField('maintenance_period', max_length=255, default=None, null=True, blank=True)
    host_dependency_enabled = models.IntegerField('host_dependency_enabled', default=None, null=True,
                                                  blank=True, choices=[(0, '0'), (1, '1')])
    labels = models.CharField('labels', max_length=255, default=None, null=True, blank=True)
    business_rule_output_template = models.CharField('business_rule_output_template', max_length=255, default=None,
                                                     null=True, blank=True)
    business_rule_smart_notifications = models.IntegerField('business_rule_smart_notifications', default=None,
                                                            null=True,
                                                            blank=True, choices=[(0, '0'), (1, '1')])
    business_rule_downtime_as_ack = models.IntegerField('business_rule_downtime_as_ack', default=None, null=True,
                                                        blank=True, choices=[(0, '0'), (1, '1')])
    business_rule_host_notification_options = models.CharField('business_rule_host_notification_options',
                                                               max_length=255, default=None, null=True, blank=True,
                                                               choices=[('r', 'r'), ('d', 'd'), ('u', 'u'), ('f', 'f'),
                                                                        ('s', 's')])
    business_rule_service_notification_options = models.CharField('business_rule_service_notification_options',
                                                                  max_length=255, default=None, null=True, blank=True,
                                                                  choices=[('r', 'r'), ('w', 'w'), ('u', 'u'),
                                                                           ('c', 'c'), ('f', 'f'), ('s', 's')])
    snapshot_enabled = models.IntegerField('snapshot_enabled', default=None, null=True,
                                           blank=True, choices=[(0, '0'), (1, '1')])
    snapshot_command = models.CharField('snapshot_command', max_length=255, default=None, null=True, blank=True)
    snapshot_period = models.CharField('snapshot_period', max_length=255, default=None, null=True, blank=True)
    snapshot_criteria = models.CharField('snapshot_criteria', max_length=255, default=None, null=True,
                                         blank=True, choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    snapshot_interval = models.IntegerField('snapshot_interval', default=None, null=True, blank=True)
    trigger_name = models.CharField('trigger_name', max_length=255, default=None, null=True, blank=True)
    trigger_broker_raise_enabled = models.IntegerField('trigger_broker_raise_enabled', default=None, null=True,
                                                       blank=True, choices=[(0, '0'), (1, '1')])

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        if six.PY3:
            return self.__unicode__()
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        return '%s on %s' % (self.check_command, self.host_name)

    def to_dict(self):
        values = {k: text_type(getattr(self, k)) for k in self.get_field_list() if getattr(self, k) is not None}
        values['use'] = 'generic-service'
        values.setdefault('service_description', '%s on %s' % (self.check_command, self.host_name))
        values['service_description'] = clean_string(values['service_description'])
        return values

    @classmethod
    def get_field_list(cls):
        # noinspection PyProtectedMember
        return [x.name for x in cls._meta.get_fields() if x.name != 'id']

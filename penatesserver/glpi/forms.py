# -*- coding: utf-8 -*-
from django import forms

__author__ = 'Matthieu Gallet'


class ShinkenServiceForm(forms.Form):
    hostgroup_name = forms.CharField(initial=None, max_length=255, required=False)
    service_description = forms.CharField(initial=None, max_length=255, required=False)
    display_name = forms.CharField(initial=None, max_length=255, required=False)
    servicegroups = forms.CharField(initial=None, max_length=255, required=False)
    is_volatile = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    initial_state = forms.ChoiceField(initial=None, required=False,
                                      choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    max_check_attempts = forms.IntegerField(initial=None, required=False)
    check_interval = forms.IntegerField(initial=None, required=False)
    retry_interval = forms.IntegerField(initial=None, required=False)
    active_checks_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    passive_checks_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    check_period = forms.CharField(initial=None, max_length=255, required=False)
    obsess_over_service = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    check_freshness = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    freshness_threshold = forms.IntegerField(initial=None, required=False)
    event_handler = forms.CharField(initial=None, max_length=255, required=False)
    event_handler_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    low_flap_threshold = forms.FloatField(initial=None, required=False)
    high_flap_threshold = forms.FloatField(initial=None, required=False)
    flap_detection_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    flap_detection_options = forms.ChoiceField(initial=None, required=False,
                                               choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    process_perf_data = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    retain_status_information = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    retain_nonstatus_information = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    notification_interval = forms.IntegerField(initial=None, required=False)
    first_notification_delay = forms.IntegerField(initial=None, required=False)
    notification_period = forms.CharField(initial=None, max_length=255, required=False)
    notification_options = forms.ChoiceField(initial=None, required=False,
                                             choices=[('r', 'r'), ('w', 'w'), ('u', 'u'), ('c', 'c'), ('f', 'f'),
                                                      ('s', 's')])
    notifications_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    contacts = forms.CharField(initial=None, max_length=255, required=False)
    contact_groups = forms.CharField(initial=None, max_length=255, required=False)
    stalking_options = forms.ChoiceField(initial=None, required=False,
                                         choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    notes = forms.CharField(initial=None, max_length=255, required=False)
    notes_url = forms.CharField(initial=None, max_length=255, required=False)
    action_url = forms.CharField(initial=None, max_length=255, required=False)
    poller_tag = forms.CharField(initial=None, max_length=255, required=False)
    icon_set = forms.CharField(initial=None, max_length=255, required=False)
    icon_image = forms.CharField(initial=None, max_length=255, required=False)
    icon_image_alt = forms.CharField(initial=None, max_length=255, required=False)
    reactionner_tag = forms.CharField(initial=None, max_length=255, required=False)
    duplicate_foreach = forms.CharField(initial=None, max_length=255, required=False)
    service_dependencies = forms.CharField(initial=None, max_length=255, required=False)
    business_impact = forms.CharField(initial=None, max_length=255, required=False)
    maintenance_period = forms.CharField(initial=None, max_length=255, required=False)
    host_dependency_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    labels = forms.CharField(initial=None, max_length=255, required=False)
    business_rule_output_template = forms.CharField(initial=None, max_length=255, required=False)
    business_rule_smart_notifications = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    business_rule_downtime_as_ack = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    business_rule_host_notification_options = forms.ChoiceField(initial=None, required=False,
                                                                choices=[('r', 'r'), ('d', 'd'), ('u', 'u'), ('f', 'f'),
                                                                         ('s', 's')])
    business_rule_service_notification_options = forms.ChoiceField(initial=None, required=False,
                                                                   choices=[('r', 'r'), ('w', 'w'), ('u', 'u'),
                                                                            ('c', 'c'), ('f', 'f'), ('s', 's')])
    snapshot_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])
    snapshot_command = forms.CharField(initial=None, max_length=255, required=False)
    snapshot_period = forms.CharField(initial=None, max_length=255, required=False)
    snapshot_criteria = forms.ChoiceField(initial=None, required=False,
                                          choices=[('o', 'o'), ('w', 'w'), ('u', 'u'), ('c', 'c')])
    snapshot_interval = forms.IntegerField(initial=None, required=False)
    trigger_name = forms.CharField(initial=None, max_length=255, required=False)
    trigger_broker_raise_enabled = forms.ChoiceField(initial=None, required=False, choices=[(0, '0'), (1, '1')])

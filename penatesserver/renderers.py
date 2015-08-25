# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.template import Context, loader
from django.utils import six
from rest_framework import serializers
from rest_framework.renderers import AdminRenderer, HTMLFormRenderer

__author__ = 'Matthieu Gallet'

default_styles = HTMLFormRenderer.default_style
default_styles[serializers.ListField] = {
    'base_template': 'list_field.html'
}


class HTMLListFormRenderer(HTMLFormRenderer):

    def render_field(self, field, parent_style):
        # noinspection PyProtectedMember
        if isinstance(field._field, serializers.HiddenField):
            return ''

        style = dict(self.default_style[field])
        style.update(field.style)
        if 'template_pack' not in style:
            style['template_pack'] = parent_style.get('template_pack', self.template_pack)
        style['renderer'] = self

        # Get a clone of the field with text-only value representation.
        original_field = field
        field = field.as_form_field()

        if style.get('input_type') == 'datetime-local' and isinstance(field.value, six.text_type):
            field.value = field.value.rstrip('Z')

        if 'template' in style:
            template_name = style['template']
        else:
            template_name = style['template_pack'].strip('/') + '/' + style['base_template']

        template = loader.get_template(template_name)
        context = Context({'field': field, 'style': style, 'original_field': original_field})
        return template.render(context)


class ListAdminRenderer(AdminRenderer):
    form_renderer_class = HTMLListFormRenderer

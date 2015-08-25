# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

__author__ = 'Matthieu Gallet'


class PasswordForm(forms.Form):
    password_1 = forms.CharField(widget=forms.PasswordInput)
    password_2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        super(PasswordForm, self).clean()
        if self.cleaned_data.get('password_1') != self.cleaned_data.get('password_2'):
            raise ValidationError(_('Both passwords must match'))
        return self.cleaned_data

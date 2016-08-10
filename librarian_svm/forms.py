"""
Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from bottle_utils import form
from bottle_utils.i18n import lazy_gettext as _

from .svm import Overlay


class OverlayForm(form.Form):
    ACTIONS = (
        ('install', _("Install")),
        ('uninstall', _("Uninstall")),
        ('remove', _("Remove")),
    )
    messages = {
        # Translators, used as error message when an invalid overlay has been
        # chosen
        'invalid_overlay': _("Invalid overlay selected."),
        # Translators, used as error message when an operation over an
        # overlay failed
        'operation_failed': _("The requested operation failed: {error}"),
    }
    action = form.SelectField(validators=[form.Required()], choices=ACTIONS)
    overlay = form.StringField(validators=[form.Required()])

    def postprocess_overlay(self, value):
        try:
            return Overlay(value)
        except Overlay.InvalidFilename:
            raise form.ValidationError('invalid_overlay', {})

    def validate(self):
        action = self.processed_data['action']
        overlay = self.processed_data['overlay']
        method = getattr(overlay, action)
        try:
            method()
        except Overlay.InstallError as exc:
            raise form.ValidationError('operation_failed', {'error': exc})

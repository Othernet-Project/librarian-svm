"""
Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import logging
import os

from bottle_utils import form
from bottle_utils.i18n import lazy_gettext as _

from librarian.core.exts import ext_container as exts

from .svm import Overlay


class OverlayForm(form.Form):
    ENABLE_OPERATION = 'enable'
    DISABLE_OPERATION = 'disable'
    REMOVE_OPERATION = 'remove'
    UPLOAD_OPERATION = 'upload'
    ACTIONS = (
        (ENABLE_OPERATION, _("Enable")),
        (DISABLE_OPERATION, _("Disable")),
        (REMOVE_OPERATION, _("Remove")),
        (UPLOAD_OPERATION, _("Upload")),
    )
    messages = {
        # Translators, used as error message when no valid overlay image was
        # uploaded
        'image_required': _("An overlay image is required."),
        # Translators, used as error message when overlay image saving failed
        'upload_failed': _("Overlay image saving failed: {error}"),
        # Translators, used as error message when an invalid overlay has been
        # chosen
        'invalid_overlay': _("No valid overlay was selected."),
        # Translators, used as error message when an operation over an
        # overlay failed
        'operation_failed': _("The requested operation failed: {error}"),
    }
    action = form.SelectField(validators=[form.Required()], choices=ACTIONS)
    overlay = form.StringField()
    # Translators, used as label for overlay image upload field
    image = form.FileField(_("Overlay"))

    def postprocess_overlay(self, value):
        if not value:
            return value
        # try lookup only if an overlay was selected
        try:
            return Overlay(value)
        except Overlay.InvalidFilename:
            raise form.ValidationError('invalid_overlay', {})

    def validate(self):
        action = self.processed_data['action']
        if action == self.UPLOAD_OPERATION:
            self._process_upload()
        else:
            self._process_action()

    def _save_image(self, image):
        """
        Store overlay image in 'svm.stashdir'
        """
        stashdir = exts.config['svm.stashdir']
        # ensure stashdir exists
        if not os.path.exists(stashdir):
            os.makedirs(stashdir)
        # attempt saving image to stashdir
        dest = os.path.join(stashdir, image.filename)
        if os.path.exists(dest):
            logging.debug('Replacing overlay image.')
            os.remove(dest)
        logging.debug('Saving overlay image at %s', dest)
        image.save(dest)

    def _process_upload(self):
        """
        Stores a freshly uploaded overlay.
        """
        image = self.processed_data['image']
        if not image:
            raise form.ValidationError('image_required', {})
        # validate image filename
        if not Overlay.is_valid(image.filename):
            raise form.ValidationError('invalid_overlay', {})
        # attempt saving overlay image
        try:
            self._save_image(image)
        except Exception as exc:
            logging.exception('Failed to save firmware update.')
            raise form.ValidationError('upload_failed', {'error': exc})

    def _process_action(self):
        """
        Perform enable / disable / removal of an existing overlay.
        """
        overlay = self.processed_data['overlay']
        if not overlay:
            raise form.ValidationError('invalid_overlay', {})
        # perform requested operation over overlay
        method = getattr(overlay, self.processed_data['action'])
        try:
            method()
        except Overlay.OperationalError as exc:
            raise form.ValidationError('operation_failed', {'error': exc})

"""
Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""
from bottle_utils.i18n import lazy_gettext as _
from streamline import XHRPartialFormRoute

from librarian.core.contrib.templates.renderer import template

from .forms import OverlayForm
from .svm import Overlay


class SVMRoute(XHRPartialFormRoute):
    name = 'svm:manage'
    path = '/svm/'
    template_func = template
    template_name = 'svm/svm'
    partial_template_name = 'svm/_svm_form'
    form_factory = OverlayForm

    def get_bound_form(self):
        form_factory = self.get_form_factory()
        return form_factory(self.request.POST)

    def get_context(self):
        context = super(SVMRoute, self).get_context()
        context.update(manifest=Overlay.manifest())
        return context

    def form_valid(self):
        if self.form.processed_data['action'] == self.form.UPLOAD_OPERATION:
            # Translators, message displayed when overlay upload was successful
            return dict(message=_("Overlay successfully uploaded."))
        # Translators, message displayed when overlay operation was successful
        return dict(message=_("Overlay operation successfully completed. "
                              "Please restart the device for the changes "
                              "to take effect."))

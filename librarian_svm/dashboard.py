"""
Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""
from bottle_utils.i18n import lazy_gettext as _

from librarian.presentation.dashboard.dashboard import DashboardPlugin

from .forms import OverlayForm
from .svm import Overlay


class SVMDashboardPlugin(DashboardPlugin):
    # Translators, used as dashboard section title
    heading = _('Software Version Management')
    name = 'svm'

    def get_template(self):
        return self.name + '/dashboard.tpl'

    def get_context(self):
        return dict(form=OverlayForm(),
                    manifest=Overlay.manifest())

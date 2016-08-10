"""
Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""
from streamline import TemplateRoute

from librarian.core.contrib.templates.renderer import template

from .svm import Overlay


class SVMRoute(TemplateRoute):
    name = 'svm:manage'
    path = '/svm/'
    template_name = 'svm/svm'
    template_func = template

    def get(self):
        return dict(manifest=Overlay.manifest())

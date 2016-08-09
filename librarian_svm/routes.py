from streamline import TemplateRoute

from librarian.core.contrib.templates.renderer import template


class SVMRoute(TemplateRoute):
    name = 'svm:main'
    path = '/svm/'
    template_name = 'svm/svm'
    template_func = template

    def get(self):
        return dict()

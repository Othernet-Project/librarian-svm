<%namespace name="forms" file="/ui/forms.tpl"/>

% if message:
    ${forms.form_message(message)}
% endif

% if error:
    ${forms.form_errors([error])}
% endif

<form action="${i18n_url('svm:main')}" method="POST">

</form>


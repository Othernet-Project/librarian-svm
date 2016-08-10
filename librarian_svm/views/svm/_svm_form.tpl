<%namespace name="forms" file="/ui/forms.tpl"/>

% if message:
    ${forms.form_message(message)}
% endif

% if error:
    ${forms.form_errors([error])}
% endif

<ol class="overlays">
    % for overlay_name, family in manifest.items():
    <li class="overlay-instance">
        <form action="${i18n_url('svm:manage')}" method="POST">
            <span class="overlay-name">${overlay_name}</span>
            <select name="overlay">
                ## Translators, placeholder for overlay version selection select list
                <option value="">${_('Select a version')}</option>
                % for overlay in family['versions']:
                <option value="overlay.filename"${ 'selected' if overlay.version == family['installed'] else ''}>${overlay.version}</option>
                % endfor
            </select>
            % if family['installed']:
            ## Translators, button title to perform uninstallation of an overlay
            <button type="submit" name="uninstall">${_('Uninstall')}</button>
            % else:
            ## Translators, button title to perform installation of an overlay
            <button type="submit" name="install">${_('Install')}</button>
            % endif
            ## Translators, button title to perform removal of an overlay
            <button type="submit" name="remove">${_('Remove')}</button>
        </form>
    </li>
    % endfor
</ol>

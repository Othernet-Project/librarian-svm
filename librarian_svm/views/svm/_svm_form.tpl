<%namespace name="forms" file="/ui/forms.tpl"/>

% if message:
    ${forms.form_message(message)}
% endif

% if form.error:
    ${forms.form_errors([form.error])}
% endif

% if not manifest:
## Translators, message is displayed when no overlays are installed or stashed
<p class="no-overlays">${_("No overlays detected on this system.")}</p>
% else:
<ol class="overlays">
    % for overlay_name, family in manifest.items():
    <li class="overlay-instance">
        <form action="${i18n_url('svm:manage')}" method="POST">
            <span class="overlay-name">${overlay_name}</span>
            <select name="overlay">
                ## Translators, placeholder for overlay version selection select list
                <option value="">${_('Select a version')}</option>
                % for overlay in family['versions']:
                <option value="overlay.path"${ 'selected' if overlay.version == family['installed'] else ''}>${overlay.version}</option>
                % endfor
            </select>
            % if form.overlay.error:
            ${forms.field_error(form.overlay.error)}
            % endif
            % if family['installed']:
            ## Translators, button title to perform uninstallation of an overlay
            <button type="submit" name="action" value="uninstall">${_('Uninstall')}</button>
            % else:
            ## Translators, button title to perform installation of an overlay
            <button type="submit" name="action" value="install">${_('Install')}</button>
            % endif
            ## Translators, button title to perform removal of an overlay
            <button type="submit" name="action" value="remove">${_('Remove')}</button>
            % if form.action.error:
            ${forms.field_error(form.action.error)}
            % endif
        </form>
    </li>
    % endfor
</ol>
% endif

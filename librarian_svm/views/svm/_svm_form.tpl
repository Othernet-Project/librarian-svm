<%namespace name="forms" file="/ui/forms.tpl"/>

<div class="svm">
    % if message:
        ${forms.form_message(message)}
    % endif

    % if form.error:
        ${forms.form_errors([form.error])}
    % endif
    % if form.action.error:
        ## Translators, message displayed when action attributes have been
        ## tempered with manually
        ${forms.form_errors([_("Form submission error")])}
    % endif

    % if not manifest:
    ## Translators, message is displayed when no overlays are installed or stashed
    <p class="no-overlays">${_("No overlays detected on this system.")}</p>
    % else:
    <table class="overlays">
        % for overlay_name, family in manifest.items():
        <tr class="overlay-instance">
            <form action="${i18n_url('svm:manage')}" method="POST">
                <td class="overlay-name">${overlay_name}</td>
                <td class="overlay-version">
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
                </td>
                <td class="actions">
                    % if family['installed']:
                    ## Translators, button title to perform uninstallation of an overlay
                    <button type="submit" name="action" value="${form.UNINSTALL_OPERATION}">${_('Uninstall')}</button>
                    % else:
                    ## Translators, button title to perform installation of an overlay
                    <button type="submit" name="action" value="${form.INSTALL_OPERATION}">${_('Install')}</button>
                    % endif
                    ## Translators, button title to perform removal of an overlay
                    <button type="submit" name="action" value="${form.REMOVE_OPERATION}">${_('Remove')}</button>
                    % if form.action.error:
                    ${forms.field_error(form.action.error)}
                    % endif
                </td>
            </form>
        </tr>
        % endfor
    </table>
    % endif

    <form action="${i18n_url('svm:manage')}" method="POST" enctype="multipart/form-data">
        ${forms.field(form.image)}
        ## Translators, button title to perform upload of a new overlay
        <button type="submit" name="action" value="${form.UPLOAD_OPERATION}">${_('Upload')}</button>
    </form>

</div>

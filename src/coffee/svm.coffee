((window, $, templates) ->
  partialSelector = ".svm"
  actionFormSelector = ".overlay-version form"
  actionMapSelector = "#svm-action-map"
  uploadFormId = "#overlay-upload"

  container = $ "#dashboard-svm-panel"
  section = container.parents '.o-collapsible-section'
  actionMap = {}
  messages = {
    'uploading': null,
  }
  iframe = null
  uploadForm = null


  setMessage = (msg) ->
    container.find('.messages').remove()
    if msg
      container.prepend msg
    section.trigger 'remax'


  replacePartial = (data) ->
    partial = container.find partialSelector
    partial.replaceWith data
    initPlugin()
    section.trigger 'remax'


  uploadStart = (e) ->
    iframe.on 'load', uploadDone
    button = uploadForm.find 'button'
    button.prop 'disabled', true
    setMessage messages.uploading
    return


  uploadDone = (e) ->
    setMessage null
    partial = iframe.contents().find partialSelector
    replacePartial partial


  loadMessages = () ->
    for msgId of messages
      if messages[msgId] == null
        $("##{msgId}").loadTemplate()
        messages[msgId] = templates[msgId]


  appendActionValue = (form) ->
    # JS intercepted form submissions do not carry over the button value
    button = form.find 'button'
    action = $ '<input>', {
      type: 'hidden',
      name: 'action',
      value: button.attr 'value'
    }
    form.append action


  patchUploadForm = () ->
    iframe = container.find 'iframe'
    uploadForm = container.find uploadFormId
    uploadForm.on 'submit', uploadStart
    uploadForm.prop 'target', (iframe.prop 'name')
    appendActionValue uploadForm


  addButton = (form, action) ->
    buttonContainer = form.find '.actions'
    button = $ '<button>', {
      type: 'submit',
      name: 'action',
      value: action,
    }
    button.text actionMap[action]
    buttonContainer.append button


  changeVersion = () ->
    select = $ @
    form = select.closest 'form'
    form.find('button').remove()
    defaultValue = select.data 'default'
    value = select.val()
    if value == defaultValue
      # selected version is the same one as the currently active
      # allow 'disable' and 'remove' options
      addButton form, 'disable'
      addButton form, 'remove'
    else if value
      # a valid version is selected that's not currently active
      # allow 'enable' and 'remove' options
      addButton form, 'enable'
      addButton form, 'remove'
    # when no version is selected, no actions are allowed at all
    return


  submitAction = (e) ->
    e.preventDefault()
    form = $ @
    appendActionValue form
    url = form.attr 'action'
    res = $.post url, form.serialize()
    res.done (data) ->
      replacePartial data
    res.fail () ->
      setMessage templates.dashboardPluginError 
      return


  prepareActionHandlers = () ->
    actionMap = JSON.parse $(actionMapSelector).html()
    forms = container.find actionFormSelector
    forms.on 'submit', submitAction
    selects = forms.find 'select'
    selects.on 'change', changeVersion
    selects.each changeVersion


  initPlugin = (e) ->
    # capture dynamically loaded templates
    loadMessages()
    # patch upload form to submit through iframe
    patchUploadForm()
    # handle overlay actions with ajax
    prepareActionHandlers()


  section.on 'dashboard-plugin-loaded', initPlugin


) this, this.jQuery, this.templates



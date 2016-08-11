((window, $, templates) ->
  partialSelector = ".svm"
  actionFormSelector = ".overlay-version form"
  uploadFormId = "#overlay-upload"

  container = $ "#dashboard-svm-panel"
  section = container.parents '.o-collapsible-section'
  messages = {
    'uploading': null,
  }
  iframe = null
  uploadForm = null
  uploadButton = null


  setMessage = (msg) ->
    container.find('.messages').remove()
    container.prepend msg
    section.trigger 'remax'


  uploadStart = (e) ->
    iframe.on 'load', uploadDone
    uploadButton.prop 'disabled', true
    setMessage messages.uploading
    return


  uploadDone = (e) ->
    partial = iframe.contents().find partialSelector
    container.html partial
    section.trigger 'remax'
    initPlugin()


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


  submitAction = (e) ->
    e.preventDefault()
    form = $ @
    appendActionValue form
    url = form.attr 'action'
    res = $.post url, form.serialize()
    res.done (data) ->
      container.html data
      initPlugin()
    res.fail () ->
      setMessage templates.dashboardPluginError 
      return


  initPlugin = (e) ->
    # capture dynamically loaded templates
    loadMessages()
    # patch upload form to submit through iframe
    patchUploadForm()
    # handle overlay actions with ajax
    forms = container.find actionFormSelector
    forms.on 'submit', submitAction


  section.on 'dashboard-plugin-loaded', initPlugin


) this, this.jQuery, this.templates



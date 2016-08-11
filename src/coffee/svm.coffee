((window, $, templates) ->
  partialSelector = ".svm"
  formId = "#overlay-upload"
  container = $ "#dashboard-svm-panel"
  section = container.parents '.o-collapsible-section'
  messages = {
    'uploading': null,
  }
  form = null
  iframe = null
  button = null


  setMessage = (msg) ->
    container.find('.messages').remove()
    container.prepend msg
    section.trigger 'remax'


  uploadStart = (e) ->
    iframe.on 'load', uploadDone
    button.prop 'disabled', true
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


  initPlugin = (e) ->
    loadMessages()
    iframe = container.find 'iframe'
    form = container.find formId
    form.on 'submit', uploadStart
    form.prop 'target', (iframe.prop 'name')
    button = form.find 'button'
    action = $ '<input>', {
      type: 'hidden',
      name: 'action',
      value: button.attr 'value'
    }
    form.append action

  section.on 'dashboard-plugin-loaded', initPlugin


) this, this.jQuery, this.templates



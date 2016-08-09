<%inherit file="/narrow_base.tpl"/>
<%namespace name="svm_form" file="_svm_form.tpl"/>

<%block name="title">
${_('Software Version Management')}
</%block>

<h2>${_('Software Version Management')}</h2>

${svm_form.body()}

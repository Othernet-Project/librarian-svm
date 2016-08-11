<%namespace name="svm_form" file="_svm_form.tpl"/>
${svm_form.body()}

<script type="application/json" id="svm-action-map">${form.action_map()}</script>

<script type="text/templates" id="uploading">
    <p class="messages">
        <span class="icon icon-spinning-loader"></span>
        <span>${_("Upload in progress...")}</span>
    </p>
</script>

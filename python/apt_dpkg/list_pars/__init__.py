params = {}
list_old_params = ['RECLASS_MODEL_URL', 'RECLASS_MODEL_BRANCH',
                   'COOKIECUTTER_TEMPLATE_PATH',
                   'COOKIECUTTER_TEMPLATE_CONTEXT',
                   'COOKIECUTTER_TEMPLATE_CREDENTIALS',
                   'COOKIECUTTER_TEMPLATE_URL', 'EMAIL_ADDRESS',
                   'RECLASS_MODEL_CREDENTIALS', 'COOKIECUTTER_TEMPLATE_BRANCH']
for param in list_old_params:
    params.pop('RECLASS_MODEL_BRANCH', '')
    del params[param]

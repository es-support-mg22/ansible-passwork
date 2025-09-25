from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleError
from module_utils.passwork_common_v7 import  get_vault, pw_login

DOCUMENTATION = r'''
---
module: pw_pass_get

short_description: Модуль для обновления пароля в passwork

options:
    api_server:
        description: HTTP путь до API сервера https://example.ru/api/v4
        required: true
        type: str
    access_token:
        description: Access API токен
        required: true
        type: str
    refresh_token:
        description: Refresh API токен
        required: false
        type: str
    master_key:
        description: Ключ шифрования для шифрования на стороне клиента.
        required: false
        type: str
    password_id:
        description: ID пароля
        required: false
        type: str
    search_args:
        description: Аргументы поиска пароля
        required: false
        type: dict
    pass_args:
        description: Аргументы пароля
        required: true
        type: dict
author:
    - Ширяев Дмитрий (dshi@efsystem.ru)
'''

RETURN = r'''
response:
    description: Ответ от сервера
    type: dict
    returned: always
'''

def _password_update(
    api_server: str,
    access_token: str,
    refresh_token: str,
    master_key: str | None,
    vault: str,
    password_id: str,
    pass_args: dict[str, Any],
    search_args: dict[str, Any]
):
    with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:

        pass_args['vaultId'] = get_vault(pwClient, vault)['id']

        if password_id is None:
            
            searched_password= pwClient.call("GET", f"/api/v1/items/search",payload=search_args)['items'][0]
            password_id=searched_password['id']

        response = pwClient.update_item(password_id, pass_args)
        return response



def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'password_id': {'required': False, 'no_log': True},
            'search_args': {
                'required': False,
                'type': 'dict',
                'options': {
                    'query': {
                        'required': True,
                    },
                    'tags': {
                        'required': False,
                        'type': 'list',
                        'default': [],
                    },
                    'colors': {
                        'required': False,
                        'type': 'list',
                        'elements': 'int',
                        'default': [],
                    },
                    'vault': {
                        'required': False,
                        'default': None,
                    },
                    'includeShared': {
                        'required': False,
                        'type': 'bool',
                        'default': False,
                    },
                    'includeShortcuts': {
                        'required': False,
                        'type': 'bool',
                        'default': False,
                    },
                },

            },
            'pass_args': {
                'required': True,
                'type': 'raw',
                'no_log': True,
            },
        },
        supports_check_mode=True,
    )

    result = {'changed': False, 'message': ''}
    if module.check_mode:
        module.exit_json(**result)

    api_server: str = module.params['api_server']
    access_token: str = module.params['access_token']
    refresh_token: str | None = module.params['refresh_token']
    master_key: str | None = module.params['master_key']
    search_args: dict[str, Any] | None  = module.params['search_args']
    pass_args: dict[str, Any]  = module.params['pass_args']
    password_id: str | None = module.params['password_id']

    if not password_id and not search_args:
        raise AnsibleError('Нужно указать "password_id".')
    if 'vault' not in pass_args:
        raise AnsibleError('Поле vault в pass_args обязательно.')
    
    password_create_result = _password_update(
        api_server,
        access_token,
        refresh_token,
        master_key,
        pass_args['vault'],
        password_id,
        pass_args,
        search_args
    )

    result['response'] = password_create_result

    module.exit_json(**result)


if __name__ == '__main__':
    main()

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from module_utils.passwork_common_v7 import (
  get_vault,
  pw_login
)

DOCUMENTATION = r'''
---
module: pw_pass_search

short_description: Модуль для поиска паролей в passwork

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
        description: Access API токен
        required: false
        type: str
    master_key:
        description: Мастер-пароль
        required: false
        type: str
    search_args:
        description: Аргументы поиска пароля
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


def _search_passwords(
    api_server: str,
    access_token: str,
    refresh_token: str,
    master_key: str | None,
    search_args: dict[str, Any],
):
    with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:

        vault_name = search_args.pop('vault')
        search_args['vaultId'] = get_vault(pwClient, vault_name)['id']
        
        response= pwClient.call("GET", f"/api/v1/items/search",payload=search_args)

        return response


def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'search_args': {
                'required': True,
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
    search_args: str = module.params['search_args']

    result['response'] = _search_passwords(api_server,access_token,refresh_token,master_key,search_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleError
from passwork_common import get_pw_session, get_vault
from passwork_api import PassworkAPI


DOCUMENTATION = r'''
---
module: pw_pass_search

short_description: Модуль для поиска паролей в passwork

options:
    api_server:
        description: HTTP путь до API сервера https://example.ru/api/v4
        required: true
        type: str
    token:
        description: API токен
        required: true
        type: str
    master_key:
        description:
            - Ключ шифрования для шифрования на стороне клиента.
            - Не указывайте его, если шифрование на стороне клиента не требуется.
        required: false
        type: str
    password_id:
        description: ID пароля
        required: true
        type: str

author:
    - Дарий Сагитов (dsa@git.efsystem.ru)
'''

RETURN = r'''
response:
    description: Ответ от сервера
    type: dict
    returned: always
'''


def _search_passwords(
    api_server: str,
    token: str,
    master_key: str | None,
    search_args: dict[str, Any],
):
    api = PassworkAPI({'host': api_server, 'api_key': token, 'master_password': master_key})
    api.login()
    try:
        return api.search_password(**search_args)
    finally:
        api.logout()


def _precompile(api_server: str, api_token: str, master_key: str | None, search_args: dict[str, Any]) -> str:
    vault_name = search_args.pop('vault')

    if vault_name is None:
        search_args['vaultId'] = None
    else:
        with get_pw_session(api_server, api_token, master_key) as session:
            search_args['vaultId'] = get_vault(session, api_server, vault_name)['id']


def main():
    # Define module args and check mode support
    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'token': {'required': True, 'no_log': True},
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
    token: str = module.params['token']
    master_key: str | None = module.params.get('master_key')
    search_args: str = module.params['search_args']
    assert api_server.endswith('/api/v4')

    _precompile(api_server, token, master_key, search_args)

    result['response'] = _search_passwords(
        api_server,
        token,
        master_key,
        search_args,
    )
    module.exit_json(**result)


if __name__ == '__main__':
    main()

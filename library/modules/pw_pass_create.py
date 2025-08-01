from typing import Any
from ansible.module_utils.basic import AnsibleModule
from passwork_common import get_pw_session, get_vault, get_folder, get_field
from passwork_api import PassworkAPI


DOCUMENTATION = r'''
---
module: pw_pass_create

short_description: Модуль для создания пароля в passwork

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
    vault_id:
        description: ID сейфа
        required: true
        type: str
    pass_args:
        description: Аргументы
        required: true
        type: dict

author:
    - Дарий Сагитов (dsa@git.efsystem.ru)
'''

EXAMPLES = r'''
- name: Create password
  pw_pass_create:
    api_server: https://example.ru/api/v4
    token: aaaaaaaaaaaaaaaaaaaaaaaaaaaa
    master_key: bbbbbbbbbbbbbbbbbbbbbbb
    vault_id: ccccccccccccccccccccccccc
    pass_args: {
        "vault": str,
        "name": str,
        "url": str,
        "login": str,
        "description": str,
        "folder": str | None,
        "password": str,
        "shortcutId": str | None,
        "tags": list[str],
        "snapshot": str | None,
        "color": int,
        "custom": [
            {
                "name": str,
                "value": str,
                "type": str
            }
        ],
        "attachments": [
            {
                "path": str,
                "name": str
            }
        ]
    }
'''

RETURN = r'''
response:
    description: Ответ от сервера
    type: dict
    returned: always
'''


def _password_pass_create(
    api_server: str,
    token: str,
    master_key: str | None,
    vault_id: str,
    pass_args: dict[str, Any],
):
    api = PassworkAPI({'host': api_server, 'api_key': token, 'master_password': master_key})
    api.login()
    try:
        vault_item = api.get_vault(vault_id)
        vault_password = api.get_vault_password(vault_item)
        return api.add_password(pass_args, vault_item, vault_password)
    finally:
        api.logout()


def _precompile(api_server: str, api_token: str, master_key: str | None, pass_args: dict[str, Any]) -> tuple[str, str | None]:
    vault: str = get_field(pass_args, 'vault')
    folder: str = pass_args.pop('folder', None)

    with get_pw_session(api_server, api_token, master_key) as session:
        vault_id = get_vault(session, api_server, vault)['id']
        pass_args['vaultId'] = vault_id
        if folder is None:
            return
        pass_args['folderId'] = get_folder(session, api_server, folder, vault_id)['id']


def main():
    # Define module args and check mode support
    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'token': {'required': True, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'pass_args': {
                'required': True,
                'type': 'dict',
                'no_log': True,
                'options': {
                    'vault': {
                        'required': True,
                    },
                    'name': {
                        'required': True,
                    },
                    'url': {
                        'required': False,
                    },
                    'login': {
                        'required': True,
                    },
                    'description': {
                        'required': False,
                    },
                    'folder': {
                        'required': False,
                        'deafault': None,
                    },
                    'password': {
                        'required': True,
                        'no_log': True,
                    },
                    'shortcutId': {
                        'required': False,
                    },
                    'tags': {
                        'required': False,
                        'type': 'list',
                        'elements': 'str',
                        'default': [],
                    },
                    'snapshot': {
                        'required': False,
                    },
                    'color': {
                        'required': False,
                        'type': 'int',
                    },
                    'custom': {
                        'required': False,
                        'type': 'list',
                        'elements': 'dict',
                        'default': [],
                    },
                    'attachments': {
                        'required': False,
                        'type': 'list',
                        'elements': 'dict',
                        'default': [],
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
    pass_args: dict[str, Any] = module.params['pass_args']
    assert api_server.endswith('/api/v4')

    _precompile(api_server, token, master_key, pass_args)

    result['response'] = _password_pass_create(
        api_server,
        token,
        master_key,
        pass_args['vaultId'],
        pass_args,
    )
    module.exit_json(**result)


if __name__ == '__main__':
    main()

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from module_utils.passwork_common_v7 import (
  pw_login, 
  get_vault, 
  get_folder
)

DOCUMENTATION = r'''
---
module: pw_folder_create

short_description: Модуль для создания пароля в passwork

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
        description: Ключ шифрования для шифрования на стороне клиента
        required: false
        type: str
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


def _password_password_create(
    api_server: str,
    access_token: str,
    refresh_token: str | None,
    master_key: str | None,
    pass_args: dict[str, Any],
):
        with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:
            
            vault= pass_args.pop('vault', None)
            vault_id = get_vault(pwClient, vault)['id']

            folder= pass_args.pop('folder', None)
            folder_id = get_folder(pwClient,folder,vault_id)['id']

            custom_fields = pass_args.pop('custom', None)
            tags = pass_args.pop('tags', None)
            name = pass_args.pop('name', None)
            login = pass_args.pop('login', None)
            passw = pass_args.pop('password', None)
            url = pass_args.pop('url', None)
            description = pass_args.pop('description', None)
            color = pass_args.pop('color', None)

            item_data = {
                "vaultId": vault_id,
                "name": name,
                "login": login,
                "password": passw,
                "url": url,
                "description": description,
                "color": color,
                "tags": tags,
                "customs": custom_fields,
                "folderId": folder_id
            }

            response = pwClient.create_item(item_data)

            return response
        

def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
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
    access_token: str = module.params['access_token']
    refresh_token: str | None = module.params['refresh_token']
    master_key: str | None = module.params['master_key']
    pass_args: dict[str, Any] = module.params['pass_args']

    result['response'] = _password_password_create(api_server, access_token, refresh_token, master_key, pass_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from passwork_common_v7 import get_vault, pw_login, get_folder


DOCUMENTATION = r'''
---
module: pw_pass_get

short_description: Модуль для получения конкретной редакции пароля в Passwork

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
    password_id:
        description: ID пароля, чьи редакции необходимо получить
        required: true
        type: str
    snapshot_id:
        description: ID редакции, которую необходимо получить
        required: true
        type: str

author:
    - Ширяев Дмитрий (dshi@efsystem.ru)
'''

RETURN = r'''
response:
    description: Ответ от сервера
    type: dict
    returned: always
'''

def _get_snapshot_by_id(
    api_server: str,
    access_token: str,
    refresh_token: str,
    master_key: str | None,
    search_args: dict[str, Any],
):
    with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:

        vault= search_args.pop('vault', None)
        vault_id = get_vault(pwClient, vault)['id']

        folder= search_args.pop('folder', None)
        folder_id=get_folder(pwClient, folder, vault_id,None)['id']
        
        snap_name= search_args.pop('query', None)

        vaults_ids=[]
        folders_ids=[]

        vaults_ids.append(vault_id)
        folders_ids.append(folder_id)
        
        response = pwClient.search_and_decrypt_shortcut(query=snap_name, vault_ids=vaults_ids, folder_ids=folders_ids)
        
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
                    'vault': {
                        'required': False,
                        'default': None,
                    },
                    'folder': {
                        'required': True,
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

    result['response'] = _get_snapshot_by_id(api_server,access_token,refresh_token,master_key,search_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

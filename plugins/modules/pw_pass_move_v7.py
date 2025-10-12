from typing import Any
from ansible.errors import AnsibleError
from ansible.module_utils.basic import AnsibleModule
from module_utils.passwork_common_v7 import pw_login

DOCUMENTATION = r'''
---
module: pw_pass_move

short_description: Модуль переноса пароля в passwork

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
        description: ID пароля
        required: false
        type: str
    search_args:
        description: Аргументы поиска
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

def _move_password(api_server:str,access_token:str,refresh_token:str,master_key:str, password_id: str, folder_args: dict[str, Any]
):
    with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:

        vault = folder_args.pop('vault', None)
        vault_id = get_vault(pwClient,  vault)['id']
        folder_args['vaultId'] = vault_id

        response = pwClient.call("POST", f"/api/v1/items/{password_id}/move", payload = folder_args)
        return response

def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'password_id': {'required': False, 'no_log': True},
            'folder_args': {
                'required': True,
                'type': 'raw',
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
    password_id: dict | None = module.params['password_id']
    folder_args: dict[str, Any] = module.params['folder_args']

    if not password_id:
        raise AnsibleError('Нужно указать "password_id".')

    if password_id:

        result['response'] =_move_password(api_server, access_token,refresh_token, master_key,password_id , folder_args)
        
    module.exit_json(**result)


if __name__ == '__main__':
    main()

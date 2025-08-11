from typing import Any
from ansible.module_utils.basic import AnsibleModule
from passwork_common_v7 import pw_login


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
    password_id: str,
    snapshot_id: str,
):
    with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:

        response = pwClient.call("GET", f"/api/v1/items/{password_id}/snapshot/{snapshot_id}")
        
        return response

def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'password_id': {'required': True, 'no_log': True},
            'snapshot_id': {'required': True, 'no_log': True},
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
    password_id: str = module.params['password_id']
    snapshot_id: str = module.params['snapshot_id']

    result['response'] = _get_snapshot_by_id(api_server,access_token,refresh_token,master_key,password_id,snapshot_id)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

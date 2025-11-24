from typing import Any
from ansible.module_utils.basic import AnsibleModule
from passwork_common_v7 import pw_login


DOCUMENTATION = r'''
---
module: pw_refresh_tokens

short_description: Модуль для обновления токена

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

author:
    - Ширяев Дмитрий (dshi@efsystem.ru)
'''

RETURN = r'''
response:
    description: Ответ от сервера
    type: dict
    returned: always
'''

def _refresh_token(
    api_server: str,
    access_token: str,
    refresh_token: str | None,
    master_key: str | None
):

        pwClient = PassworkClient(api_server,False)
        pwClient.set_tokens(access_token,refresh_token)
        response = pwClient.update_tokens()
        return response


def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
        },
        supports_check_mode=True,
    )

    result = {'changed': False, 'message': ''}
    if module.check_mode:
        module.exit_json(**result)

    api_server: str = module.params['api_server']
    access_token: str = module.params['access_token']
    refresh_token: str | None = module.params['refresh_token']
    master_key: str | None = module.params.get('master_key')

    result['response'] = _refresh_token(api_server, access_token,refresh_token,master_key)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

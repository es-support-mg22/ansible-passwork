from ansible.module_utils.basic import AnsibleModule
from passwork_common_v7 import  get_password_by_path, pw_login


DOCUMENTATION = r'''
---
module: pw_pass_get_by_path

short_description: Модуль для получения пароля в passwork по полному пути

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
    path:
        description: Путь до пароля
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


def main():

    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'access_token': {'required': True, 'no_log': True},
            'refresh_token': {'required': False, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'path': {'required': True, 'no_log': True}
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False,
        'message': '',
    }

    if module.check_mode:
        module.exit_json(**result)

    api_server: str = module.params['api_server']
    access_token: str = module.params['access_token']
    refresh_token: str | None = module.params['refresh_token']
    master_key: str | None = module.params['master_key']
    path: str = module.params['path']

    with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:
        result['response'] = get_password_by_path(pwClient,path)

    module.exit_json(**result)


if __name__ == '__main__':
    main()

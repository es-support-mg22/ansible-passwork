from ansible.module_utils.basic import AnsibleModule
from passwork_common import get_pw_session, get_password_by_path


DOCUMENTATION = r'''
---
module: pw_pass_get_by_path

short_description: Модуль для получения пароля в passwork

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
    path:
        description: Путь пароля
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


def main():
    # Define module args and check mode support
    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'token': {'required': True, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'path': {'required': True, 'no_log': True},
        },
        supports_check_mode=True,
    )
    # Define module's output
    result = {
        'changed': False,
        'message': '',
    }
    # Exit if module run in check mode
    if module.check_mode:
        module.exit_json(**result)

    api_server: str = module.params['api_server']
    token: str = module.params['token']
    master_key: str | None = module.params.get('master_key')
    path: str = module.params['path']
    assert api_server.endswith('/api/v4')

    with get_pw_session(api_server, token, master_key) as session:
        result['response'] = get_password_by_path(
            session,
            api_server,
            path,
        )
    module.exit_json(**result)


if __name__ == '__main__':
    main()

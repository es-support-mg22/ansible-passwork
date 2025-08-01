from typing import Any
from ansible.errors import AnsibleError
from ansible.module_utils.basic import AnsibleModule
from passwork_common import get_pw_session, get_vault, get_folder, get_field


DOCUMENTATION = r'''
---
module: pw_folder_create

short_description: Модуль для создания папки в passwork

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
    folder_args:
        description: Аргументы
        required: true
        type: dict

author:
    - Дарий Сагитов (dsa@git.efsystem.ru)
'''

RETURN = r'''
response:
    description: Ответ от сервера
    type: dict
    returned: always
'''


def _password_folder_create(
    api_server: str,
    token: str,
    master_key: str | None,
    folder_args: dict[str, Any],
):
    vault: str = get_field(folder_args, 'vault')
    with get_pw_session(api_server, token, master_key) as session:
        vault_id = get_vault(session, api_server, vault)['id']
        folder_args['vaultId'] = vault_id

        parent_folder: str | None = folder_args.pop('parent', None)
        if parent_folder is not None:
            folder_args['parentId'] = get_folder(session, api_server, parent_folder, vault_id)['id']

        response = session.post(f'{api_server}/folders', json=folder_args)
    if response.status_code != 201:
        raise AnsibleError(f'Ошибка при создании папки: {response.text}')
    return response.json()


def main():
    # Define module args and check mode support
    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'token': {'required': True, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
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
    token: str = module.params['token']
    master_key: str | None = module.params.get('master_key')
    folder_args: dict[str, Any] = module.params['folder_args']
    assert api_server.endswith('/api/v4')

    result['response'] = _password_folder_create(api_server, token, master_key, folder_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

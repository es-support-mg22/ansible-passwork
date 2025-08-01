from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleError
from passwork_common import get_pw_session, get_folder, get_field, get_vault


DOCUMENTATION = r'''
---
module: pw_folder_update

short_description: Модуль для обновления папки в passwork

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


def _password_folder_update(
    api_server: str,
    token: str,
    master_key: str | None,
    folder_args: dict[str, Any],
):
    with get_pw_session(api_server, token, master_key) as session:
        if (folder_id := folder_args.pop('folder_id', None)) is not None:
            response = session.put(f'{api_server}/folders/{folder_id}', json=folder_args)
            if response.status_code != 200:
                raise AnsibleError(f'Ошибка при обновлении папки с ID {folder_id}: {response.text}')
            return response.json()

        folder: str = get_field(folder_args, 'folder', ', если не указан folde_id!')
        vault: str = get_field(folder_args, 'vault', ', если не указан folde_id!')

        vault_id = get_vault(session, api_server, vault)['id']
        folder_id: str = get_folder(session, api_server, folder, vault_id)['id']
        response = session.put(f'{api_server}/folders/{folder_id}', json=folder_args)
    if response.status_code != 200:
        raise AnsibleError(f'Ошибка при обновлении папки {folder}: {response.text}')
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

    result['response'] = _password_folder_update(api_server, token, master_key, folder_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

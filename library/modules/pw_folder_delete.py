from typing import Any
from ansible.module_utils.basic import AnsibleModule
from passwork_common import get_pw_session, get_folder, get_vault, get_field
from ansible.errors import AnsibleError


DOCUMENTATION = r'''
---
module: pw_folder_delete

short_description: Модуль для удаления папки в passwork

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


def _password_folder_delete(
    api_server: str,
    token: str,
    master_key: str | None,
    folder_args: dict[str, Any],
):
    with get_pw_session(api_server, token, master_key) as session:
        if (folder_id := folder_args.pop('folder_id', None)) is not None:
            response = session.delete(f'{api_server}/folders/{folder_id}')
            if response.status_code != 200:
                raise AnsibleError(f'Не удалось удалить папку {folder_id}: {response.text}')
            return

        name = get_field(folder_args, 'name', ', если не указан folder_id.')
        vault = get_field(folder_args, 'vault', ', если не указан folder_id.')

        vault_id = get_vault(session, api_server, vault)['id']
        folder_id = get_folder(session, api_server, name, vault_id)['id']
        response = session.delete(f'{api_server}/folders/{folder_id}')
    if response.status_code != 200:
        raise AnsibleError(f'Не удалось удалить папку {name}: {response.text}')


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

    _password_folder_delete(api_server, token, master_key, folder_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

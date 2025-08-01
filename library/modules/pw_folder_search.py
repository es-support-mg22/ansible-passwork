from typing import Any
from ansible.module_utils.basic import AnsibleModule
from passwork_common import (
    get_pw_session,
    search_folder,
    get_folder,
    get_vault,
    get_field,
)


DOCUMENTATION = r'''
---
module: pw_folder_search

short_description: Модуль для поиска папок в passwork

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
    vault:
        description: ID сейфа
        required: true
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


def _password_folder_search(
    api_server: str,
    token: str,
    master_key: str | None,
    folder_args: dict[str, Any],
):
    name: str = get_field(folder_args, 'name')
    vault: str = get_field(folder_args, 'vault')
    parent_folder: str | None = folder_args.get('parent_folder')
    with get_pw_session(api_server, token, master_key) as session:
        vault_id = get_vault(session, api_server, vault)['id']
        folders = search_folder(session, api_server, name, vault_id)
        if parent_folder is None:
            return folders
        parent_folders_ids = [folder['id'] for folder in search_folder(session, api_server, parent_folder, vault_id)]
    return [
        folder
        for folder in folders
        if folder['parentId'] in parent_folders_ids
    ]


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

    result['response'] = _password_folder_search(api_server, token, master_key, folder_args)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

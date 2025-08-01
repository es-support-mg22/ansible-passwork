import requests
from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible.errors import AnsibleError
from passwork_common import get_pw_session, get_vault, get_folder, get_field
from passwork_api import PassworkAPI

from rest_modules import is_failed_status_code
from utils import (
    generate_password,
    encrypt_string,
    use_key_encryption,
    validate_customs,
    encrypt_customs,
    format_attachments,
)


DOCUMENTATION = r'''
---
module: pw_pass_update

short_description: Модуль для обновления пароля в passwork

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
    vault_id:
        description: ID сейфа
        required: true
        type: str
    pass_args:
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


def _get_password(
    api_server: str,
    token: str,
    master_key: str | None,
    password_id: str,
) -> dict:
    api = PassworkAPI({'host': api_server, 'api_key': token, 'master_password': master_key})
    api.login()
    try:
        return api.get_password(password_id)
    finally:
        api.logout()


def _precompile_search_args(api_server: str, api_token: str, master_key: str | None, search_args: dict[str, Any]) -> str:
    vault_name = get_field(search_args, 'vault', ' в search_args!')
    with get_pw_session(api_server, api_token, master_key) as session:
        search_args['vaultId'] = get_vault(session, api_server, vault_name)['id']


def _search_passwords(
    api_server: str,
    token: str,
    master_key: str | None,
    search_args: dict[str, Any],
):
    api = PassworkAPI({
        'host': api_server,
        'api_key': token,
        'master_password': master_key,
    })
    api.login()
    try:
        passwords = api.search_password(**search_args)
        if len(passwords) != 1:
            raise AnsibleError(f'Найдено более одного или ни одного пароля: {passwords}')
        return passwords[0]
    finally:
        api.logout()


def _proceed_password(fields: dict, vault: dict, vault_password: str, options):
    encryption_key = (
        generate_password() if options.use_master_password else vault_password
    )

    if 'password' in fields:
        fields["cryptedPassword"] = encrypt_string(fields["password"], encryption_key, options)
        if use_key_encryption(vault):
            fields["cryptedKey"] = encrypt_string(encryption_key, vault_password, options)
        fields.pop("password", None)

    if "custom" in fields and len(fields["custom"]) > 0:
        validate_customs(fields["custom"])
        fields["custom"] = encrypt_customs(fields["custom"], encryption_key, options)

    if "attachments" in fields and len(fields["attachments"]) > 0:
        fields["attachments"] = format_attachments(fields["attachments"], encryption_key)

    fields.setdefault("name", "")


def _password_update(
    api_server: str,
    token: str,
    master_key: str | None,
    vault_id: str,
    password_id: str,
    pass_args: dict[str, Any],
):
    api = PassworkAPI({
        'host': api_server,
        'api_key': token,
        'master_password': master_key,
    })
    api.login()
    try:
        vault_item = api.get_vault(vault_id)
        vault_password = api.get_vault_password(vault_item)
        _proceed_password(pass_args, vault_item, vault_password, api.session_options)
        response = requests.put(
            url=f"{api.session_options.host}/passwords/{password_id}",
            json=pass_args,
            headers=api.session_options.request_headers,
            timeout=30,
        )

        if is_failed_status_code(
            status_code=response.status_code,
            prefix="Error when adding a new password"
        ):
            raise Exception
        return response.json()

    except:
        api.logout()
        raise


def _precompile_update_args(api_server: str, api_token: str, master_key: str | None, pass_args: dict[str, Any]) -> tuple[str, str | None]:
    vault: str = get_field(pass_args, 'vault', ' в update_args!')

    with get_pw_session(api_server, api_token, master_key) as session:
        vault_id = get_vault(session, api_server, vault)['id']
        pass_args['vaultId'] = vault_id
        if 'folder' in pass_args:
            folder = pass_args['folder']
            if folder is None:
                pass_args['folderId'] = None
            else:
                pass_args['folderId'] = get_folder(session, api_server, folder, vault_id)['id']


def main():
    # Define module args and check mode support
    module = AnsibleModule(
        argument_spec={
            'api_server': {'required': True},
            'token': {'required': True, 'no_log': True},
            'master_key': {'required': False, 'no_log': True},
            'password_id': {'required': False, 'no_log': True},
            'search_args': {
                'required': False,
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
                    'colors': {
                        'required': False,
                        'type': 'list',
                        'elements': 'int',
                        'default': [],
                    },
                    'vault': {
                        'required': False,
                        'default': None,
                    },
                    'includeShared': {
                        'required': False,
                        'type': 'bool',
                        'default': False,
                    },
                    'includeShortcuts': {
                        'required': False,
                        'type': 'bool',
                        'default': False,
                    },
                },

            },
            'pass_args': {
                'required': True,
                # валидация ansible не позволяет сделать опциональный параметр,
                # поэтому вот так. Если параметра нет, то и его не должно быть,
                # например, чтобы не менялось его значение вовсе. А ansible пытается
                # None подставить.
                'type': 'raw',
                'no_log': True,
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
    password_id: str = module.params.get('password_id')
    search_args: str = module.params.get('search_args')
    pass_args: dict[str, Any] = module.params['pass_args']
    assert api_server.endswith('/api/v4')

    if not password_id and not search_args:
        raise AnsibleError('Нужно указать либо "password_id", либо "search_args"')
    if 'vault' not in pass_args:
        raise AnsibleError('Поле vault в pass_args обязательно')

    if password_id:
        pswd = _get_password(api_server, token, master_key, password_id)
    else:
        _precompile_search_args(api_server, token, master_key, search_args)
        pswd = _search_passwords(
            api_server,
            token,
            master_key,
            search_args,
        )

    _precompile_update_args(api_server, token, master_key, pass_args)
    password_create_result = _password_update(
        api_server,
        token,
        master_key,
        pass_args['vaultId'],
        pswd['id'],
        pass_args,
    )
    result['response'] = password_create_result

    module.exit_json(**result)


if __name__ == '__main__':
    main()

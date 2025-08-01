from contextlib import contextmanager
from typing import Any, Generator
from ansible.errors import AnsibleError
from passwork_client import PassworkClient

# Change this var to False if you want to disable SSL verification
VERIFY_SSL=True

@contextmanager
def pw_login(api_server: str, access_token: str, refresh_token: str | None, master_key: str | None)-> Generator[PassworkClient, None, None]:
    try:
        passwork = PassworkClient(api_server,VERIFY_SSL)
        passwork.set_tokens(access_token, refresh_token)
        if bool(master_key):
            passwork.set_master_key(master_key)
    except Exception as e:
        raise AnsibleError(f'Ошибка соединения с Passwork: {e}')
    yield passwork


def get_vault(pwClient: PassworkClient, vault_name: str):
    try:
        vaults_resp = pwClient.call("GET", f"/api/v1/vaults")
        vault = {
            vault['name']: vault
            for vault in vaults_resp['items']
        }.get(vault_name)
    except Exception as e:
        raise AnsibleError(f'Ошибка соединения получения сейфа: {e}')
    return vault

def search_folder (pwClient: PassworkClient, folder_name: str, vault_id: str | None, parent_folder : str | None):
    try:
        body = {'query': folder_name}
        if vault_id is not None:
            body['vaultId'] = vault_id
        if parent_folder is not None:
            body['parentFolderId']=parent_folder
        folders= pwClient.call("GET", f"/api/v1/folders/search",payload=body)
    except Exception as e:
        raise AnsibleError(f'Ошибка поиска папки: {e}')
    return folders

def get_folder(pwClient: PassworkClient, folder_name: str, vault_id: str | None, parent_folder: str|None):
    
    folders= search_folder(pwClient,folder_name,vault_id,parent_folder)
    matched_folders = [
            folder
            for folder in folders['items']
            if folder['vaultId'] == vault_id and folder['name'] == folder_name
        ]
    if len(matched_folders) == 1:
        return (matched_folders[0])
    raise AnsibleError(f'Папка {folder_name} не найдена или же найдено более одной папки с таким именем: {matched_folders}')

def get_folder_by_id(pwClient: PassworkClient, folder_id: str):
    response = pwClient.call("GET", f"/api/v1/folders/{folder_id}")
    return response

def _get_passwords(pwClient: PassworkClient, password_name: str):
    try:
        passwords_response = pwClient.call("GET",f'/api/v1/items/search', payload={'query': password_name})

        passwords = passwords_response['items']
        matched_passwords = [
            password
            for password in passwords
            if password['name'] == password_name
        ]
        return matched_passwords
    except Exception as e:
        raise AnsibleError(f'Ошибка получения пароля: {e}')


def get_password_by_path(pwClient: PassworkClient, path: str) -> dict | None:

    vault_folders, pass_name = path.rsplit('/', maxsplit=1)
    if not vault_folders or not pass_name:
        raise AnsibleError((
            'Путь невалидный, должен состоять минимум из трех частей: '
            f'наименование сейфа/папки(через /)/название пароля. {path=}'
        ))
    matched_by_path_passwords = []
    passwords = _get_passwords(pwClient, pass_name)
    for password in passwords:
        matched_by_path_passwords.append(password)

    if len(matched_by_path_passwords) > 1:
        raise AnsibleError((
            f'Не удалось найти единственный пароль по пути {path}. '
        ))
    if len(matched_by_path_passwords) == 0:
        return None
    return matched_by_path_passwords[0]


from contextlib import contextmanager
from typing import Any, Generator
from ansible.errors import AnsibleError
from module_utils.passwork_client import PassworkClient

VERIFY_SSL=False

@contextmanager
def pw_login(api_server: str, access_token: str, refresh_token: str | None, master_key: str | None)-> Generator[PassworkClient, None, None]:
    try:
        passwork = PassworkClient(api_server,VERIFY_SSL)
        passwork.set_tokens(access_token, None)
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

def search_folder (pwClient: PassworkClient, folder_name: str, vault_id: str | None):
    try:
        
        body = {'query': folder_name}

        if vault_id is not None:
            body['vaultId'] = vault_id
        folders= pwClient.call("GET", f"/api/v1/folders/search",payload=body)['items']

        for folder in folders:
            if 'path' in folder:
                folder['pathStr']= path_to_string(folder['path'])

    except Exception as e:
        raise AnsibleError(f'Ошибка поиска папки: {e}')
    return folders

def get_folder_by_path(pwClient: PassworkClient, folder_name: str, path: str, vault_id: str | None) -> dict | None:


    body = {'query': folder_name}

    folders= pwClient.call("GET", f"/api/v1/folders/search",payload=body)['items']

    if len(folders) == 0:
        return None

    for folder in folders:
        if 'path' in folder:
            folder['pathStr']= path_to_string(folder['path'])

    matched_folders = [
                folder
                for folder in folders
                if folder['vaultId'] == vault_id and folder['name'] == folder_name and folder['pathStr'] in path
            ]
    
    if len(matched_folders) == 0:
        return None

    if len(matched_folders) > 1:
        raise AnsibleError((
            f'Не удалось найти единственную папку по пути {path}. '
        ))

    return matched_folders[0]

def get_folder(pwClient: PassworkClient, folder_name: str, vault_id: str | None):
    
    folders= search_folder(pwClient,folder_name,vault_id)
    matched_folders = [
            folder
            for folder in folders
            if folder['vaultId'] == vault_id and folder['name'] == folder_name
        ]

    if len(matched_folders) == 1:
        return (matched_folders[0])
    return None

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
        
        for match_pass in matched_passwords:
            if 'path' in match_pass:
                match_pass['pathStr']= path_to_string(match_pass['path'])+password_name

        
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
        if password['pathStr']==path:
            matched_by_path_passwords.append(password)

    if len(matched_by_path_passwords) > 1:
        raise AnsibleError((
            f'Не удалось найти единственный пароль по пути {path}. '
        ))
    if len(matched_by_path_passwords) == 0:
        return None
    return matched_by_path_passwords[0]

def path_to_string(path: dict):
    pathStr=""
    for p in path:
        pathStr+=p['name']+"/"
    return pathStr


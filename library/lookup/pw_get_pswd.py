DOCUMENTATION = r"""
  name: pw_get_pswd
  author: Дарий Сагитов <dsa@efsystem.ru>
  version_added: "1.0"
  short_description: Получает пароль из passwork по указанному пути
  description:
      - Получает пароль из passwork по указанному пути.
  options:
    api_server:
      description: Passwork API URL.
      required: True
      type: string
    token:
      description: Passwork API token.
      required: True
      type: string
    master_key:
      description: Passwork master ключ.
      required: False
      type: string
    path:
      description: Путь пароля, с указанием сейфа.
      required: True
      type: string
"""
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from passwork_api import PassworkAPI
from passwork_common import get_pw_session, get_password_by_path

display = Display()

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        api_server: str = self.get_option('api_server')
        token: str = self.get_option('token')
        master_key: str = self.get_option('master_key')
        password_path: str = self.get_option('path')

        with get_pw_session(api_server, token, master_key) as session:
            password = get_password_by_path(session, api_server, password_path)

        api = PassworkAPI({'host': api_server, 'api_key': token, 'master_password': master_key})
        api.login()
        try:
            pswd = api.get_password(password['id'])
            vault_id = pswd['vaultId']
            vault_item = api.get_vault(vault_id)
            vault_password = api.get_vault_password(vault_item)
            pswd['password_clear_text'] = api.get_password_plain_text(pswd, api.get_password_encryption_key(pswd, vault_password))
            return [pswd]
        finally:
            api.logout()

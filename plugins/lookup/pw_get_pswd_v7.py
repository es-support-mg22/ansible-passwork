DOCUMENTATION = r'''
---
module: pw_get_pswd

short_description: Лукап для получения пароля по пути

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
    password_path:
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
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from module_utils.passwork_common_v7 import get_password_by_path,pw_login

display = Display()

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)


        api_server: str = self.get_option('api_server')
        access_token: str = self.get_option('access_token')
        refresh_token: str = self.get_option('refresh_token')
        master_key: str = self.get_option('master_key')
        password_path: str = self.get_option('path')


        with pw_login(api_server,access_token,refresh_token,master_key) as pwClient:
            password = get_password_by_path(pwClient,password_path)
            response= pwClient.get_item(password['id'])
            return [response]
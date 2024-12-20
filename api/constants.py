import requests
from django.conf import settings

KVDATA_BASE_URL = "https://kvdata.net/api/"
KVDATA_PROVIDER_TOKEN = "663c72ffcb3f18a99b8ddf213b60ed1862a9866d"

BaseUrl = 'https://api.payvessel.com/'
api_key = 'PVKEY-3ZO1QOSQH83C5Q3PBCVUT1' # api-key
api_secret = 'Bearer PVSECRET-OZJD0SZ2F2WOTXAF' # api-secret

NETWORK_ID = {
    'MTN': '1',
    'GLO': '2',
    '9MOBILE': '3',
    'AIRTEL': '4',
    'SMILE': '5',
}

ELECTRIC_DISCO_ID = {
    "Ikeja Electric": '1',
    "EKO Electric": '2',
    "Abuja Electric": '3',
    "Kano Electric": '4',
    "Enugu Electric": '5',
    "Port Harcourt": '6',
    "Ibadan Electric": '7',
    "Kaduna Electric": '8',
    "Jos Electric": '9',
    "Benin Electric": '10',
    "Yola Electric": '11',
}

CABLE_PROVIDER_ID = {
    'GOTV': 1,
    'DSTV': 2,
    'STARTIMES': 3
}

EXAM_RESULT_CHECKER = {
    "WAEC":"1",
    "NECO":"2"
}


class RequestWrapper:
    url = None,
    endpoint = '',
    provider_token = None
    
    def req_headers(self):
        return {
            'Authorization': f'Token {self.provider_token}',
            'Content-Type': 'application/json'
        }

    def req_post(self, data = {}):
        
        response =  requests.post(
            url= self.url + self.endpoint,
            json=data,
            headers=self.req_headers()
        )

        return response
    
    def req_get(self, params = {}):
        response = requests.get(
            url=self.url + self.endpoint,
            params=params,
        )
        return response
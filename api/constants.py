import requests
from django.conf import settings

KVDATA_BASE_URL = "https://kvdataapi.net/api/"
KVDATA_PROVIDER_TOKEN = "95fa17cc2db34652b231cedd500d368789002382"

# 247api.org
API_BASE_URL = "https://247api.com.ng/api/" 
API_PROVIDER_TOKEN =   "442|C3aS8UIFZcHitFpZy8BMpJjvWyB3YlM7hwJ4xQuB5b79f621"                 #"432|npdAZDLe630CJ9JN3x6G6SBawWoKacduccVbDv7w2a451163"   # 2471pi.org


BaseUrl = 'https://api.payvessel.com/'
api_key = 'PVKEY-3ZO1QOSQH83C5Q3PBCVUT1' # api-key
api_secret = 'Bearer PVSECRET-OZJD0SZ2F2WOTXAF' # api-secret

# NETWORK_ID = {
#     'MTN': '1',
#     'GLO': '2',
#     '9MOBILE': '3',
#     'AIRTEL': '4',
#     'SMILE': '5',
# }

NETWORK_ID = {
    'MTN': '1',
    'AIRTEL': '2',
    'GLO': '3',
    '9MOBILE': '4',
    # 'SMILE': '5',
}

# ELECTRIC_DISCO_ID = {
#     "Ikeja Electric": '1',
#     "EKO Electric": '2',
#     "Abuja Electric": '3',
#     "Kano Electric": '4',
#     "Enugu Electric": '5',
#     "Port Harcourt": '6',
#     "Ibadan Electric": '7',
#     "Kaduna Electric": '8',
#     "Jos Electric": '9',
#     "Benin Electric": '10',
#     "Yola Electric": '11',
# }


ELECTRIC_DISCO_ID = {
    "Abuja Electric": '10',
    "Benin Electric": '11',
    "Eko Electric": '12',
    "Enugu Electric": '13',
    "Ibadan Electric": '14',
    "Ikeja Electric": '15',
    "Jos Electric": '16',
    "Kaduna Electric": '17',
    "Kano Electric": '18',
    "Port Harcourt": '19',
    "Yola Electric": '20',
}


CABLE_PROVIDER_ID = {
    'GOTV': 10,
    'DSTV': 11,
    'STARTIMES': 12
}

EXAM_RESULT_CHECKER = {
    "WAEC":"10",
    "NECO":"11",
    "NABTEB":"12",
    "JAMB":"13"
}


class RequestWrapper:
    url = API_BASE_URL,
    endpoint = '',
    provider_token = API_PROVIDER_TOKEN
    
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
            headers={
            'Authorization': f'Token {self.provider_token}',
            'Content-Type': 'application/json'
        },
            url=self.url + self.endpoint,
            params=params,
        )
        return response

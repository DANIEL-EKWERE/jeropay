from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

# request
from requests import get

# constants
from api.constants import KVDATA_BASE_URL,KVDATA_PROVIDER_TOKEN

class ProviderAPIBalanceView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        headers = {
            'Authorization': f'Token {KVDATA_PROVIDER_TOKEN}',
            'Content-Type': 'application/json'
        }
        # get data providers balance
        data_provider = get(
            'https://kvdata.net/api/user/',
            headers=headers
        )
        data_provider_response = data_provider.json()



        # # get airime provider balance
        # airtime_parameters = {
        #         'username': settings.PG_USERNAME,
        #         'password': settings.PG_PASSWORD,
        #     }
        # url = 'https://paygold.ng/wp-json/api/v1/balance'
        # airtime_provider_response = get(url, params=airtime_parameters).json()
        
        
        return Response(
            data={
                 'data_provider_balance': str(data_provider_response['user']['Account_Balance']),
                # 'airtime_provider_balance': airtime_provider_response['data']['balance']
            }, 
            status=200
        )
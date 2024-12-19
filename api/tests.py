from django.test import TestCase
import requests,json

# Create your tests here.
'''
# check user details - GET
curl --location 'https://datastation.com.ng/api/user/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json'

# buy data - POST
curl --location 'https://datastation.com.ng/api/data/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{"network":network_id,
"mobile_number": "09095263835",
"plan": plan_id,
"Ported_number":true
}'

# get all data transaction - GET
curl --location 'https://datastation.com.ng/api/data/'

# Query Data Transaction - GET
curl --location 'https://datastation.com.ng/api/data/58'

# Buy Airtime TopUp and Get all Airtime Transaction  - POST
curl --location 'https://datastation.com.ng/api/topup/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{"network":network_id,
"amount":amount,
"mobile_number":phone,
"Ported_number":true
"airtime_type":"VTU"

}'

# Query Airtime Transaction - GET
curl --location 'https://datastation.com.ng/api/data/id' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json'

# Buy Electricity Bill Payment and Get all Transaction - POST
curl --location 'https://datastation.com.ng/api/billpayment/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{"disco_name":disco,
"amount":amount to pay,
"meter_number": meter number,
"MeterType": meter type id (PREPAID:1,POSTPAID:2)

}'

# Query Bill Payment - GET
curl --location 'https://datastation.com.ng/api/billpayment/id' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92'

# Buy Cable and get all transaction - POST
curl --location 'https://datastation.com.ng/api/cablesub/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{
    "cablename":cablename id,
    "cableplan": cableplan id,
    "smart_card_number": meter
}'

# Query Cablesub - GET
curl --location 'https://datastation.com.ng/api/cablesub/id' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json'


# Validate IUC - GET 
curl --location 'https://datastation.com.ng/ajax/validate_iuc?smart_card_number=iuc&cablename=cable_name' \
--header 'Authorization: Token acc78d46fd61bb7657777eb52100d65730c61429' \
--header 'Content-Type: application/json'

# Validate Meter - GET
curl --location 'https://datastation.com.ng/ajax/validate_meter_number?meternumber=meternumber&disconame=disconame&mtype=metertype' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json'

# Generate Airtime pin - POST
curl --location 'https://datastation.com.ng/api/rechargepin/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5' \
--header 'Content-Type: application/json' \
--data '{"network":network_id,
"network_amount": network_amount.id,
"quantity": quantity,
"name_on_card": "name_on_card"
}'

# Generate Result/Education pins - POST
curl --location 'https://datastation.com.ng/api/epin/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5' \
--header 'Content-Type: application/json' \
--data '{"exam_name":exam_name ,
"quantity": quantity,
}'

'''

# KVDATA


'''
# check user details - GET
curl --location 'https://kvdata.net/api/user/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json'

# buy data - POST
curl --location 'https://kvdata.net/api/data/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{"network":network_id,
"mobile_number": "09095263835",
"plan": plan_id,
"Ported_number":true
}'

# buy data Epin - POST
curl --location 'https://kvdata.net/api/data_plan/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{"network":"MTN",
"mobile_number": "09095263835",
"data_plan": "1",
"quantity": "1",
"name_on_card":""
}'

# buy result checker - POST
curl --location 'https://kvdata.net/api/epin/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{"network":"MTN",
"exam_name": "WAEC",
"quantity": "1",
}'

# get all data transaction - GET
curl --location 'https://kvdata.net/api/data/'

# Query Data Transaction - GET
curl --location 'https://kvdata.net/api/data/58'

# Buy Airtime TopUp and Get all Airtime Transaction  - POST
curl --location 'https://kvdata.net/api/topup/' \
--header 'Authorization: Token {{Token}}' \
--header 'Content-Type: application/json' \
--data '{"network":network_id,
"amount":amount,
"mobile_number":phone,
"Ported_number":true
"airtime_type":"VTU"

}'


# Query Airtime Transaction - GET
curl --location 'https://kvdata.net/api/data/id' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json'


# Buy Electricity Bill Payment and Get all Transaction - POST
curl --location 'https://kvdata.net/api/billpayment/' \
--header 'Authorization: Token {{Token}}' \
--header 'Content-Type: application/json' \
--data '{"disco_name":disco,
"amount":amount to pay,
"meter_number": meter number,
"MeterType": meter type id (PREPAID:1,POSTPAID:2)

}'


# Query Bill Payment - GET
curl --location 'https://kvdata.net/api/billpayment/id' \
--header 'Authorization: Token {{Token}}'

# Buy Cable and get all transaction - POST
curl --location 'https://kvdata.net/api/cablesub/' \
--header 'Authorization: Token 66f2e5c39ac8640f13cd888f161385b12f7e5e92' \
--header 'Content-Type: application/json' \
--data '{
    "cablename":cablename id,
    "cableplan": cableplan id,
    "smart_card_number": meter
}'


# Query Cablesub - GET
curl --location 'https://kvdata.net/api/cablesub/id' \
--header 'Authorization: Token {{Token}}' \
--header 'Content-Type: application/json'

# Validate IUC - GET 
curl --location 'https://kvdata.net/api/validateiuc?smart_card_number=iuc&%20=null&cablename=id' \
--header 'Authorization: Token {{Token}}' \
--header 'Content-Type: application/json'

# Validate Meter - GET
curl --location 'https://kvdata.net/api/validatemeter?meternumber=meter&disconame=di&mtype=metertype' \
--header 'Authorization: Token {{Token}}' \
--header 'Content-Type: application/json'

'''
'''
from django.conf import settings
from constants import KVDATA_BASE_URL
print(KVDATA_BASE_URL)

data ={
    'username':'DANIEL',
    'password':'123450'
}

login = requests.post('http://127.0.0.1:1000/api/user/login-user/',data=data)
if login.status_code == 200:
    print('login successfull')
else:
    print('not logged in')
data={'username':'DANIEL','password':'123450'}
obtain_token = requests.post('http://127.0.0.1:1000/api/token/',data=data)
if obtain_token.status_code == 200:
    tokens = obtain_token.json()
    access_token = tokens.get('access')
    print(access_token)
else:
    print(obtain_token.status_code)
headers = {
    'Authorization':f'Bearer {access_token}'
}
response = requests.get('http://127.0.0.1:1000/api/admin/wallet/',headers=headers)
if response.status_code == 200:
    print('the balance is =',response.json()[0]['balance'])
else:
    print(response.status_code)
'''
''' reserve acct doc from payvessel '''

'''
REQUEST HEADERS
headers = {
'api-key': 'PVKEY-FNLYA8DW2LGZE6KFI0K4AA7N5JP',
'api-secret': 'Bearer PVSECRET-5LZNFFNT8N9NF6SXUZPWEYQ0Q2Y',
'Content-Type': 'application/json'
}
https://api.payvessel.com/api/external/request/customerReservedAccount/ - POST

REQUEST BODY

{
    "email":"oyefgdgf@gmail.com",
    "name":"MUSA OLA",
    "phoneNumber":"09011111112",
    "bankcode":["120001"],
    "businessid":"061C074E2F91F944B93993B4"

}

Response Body

{
    "status": true,
    "service": "CREATE_VIRTUAL_ACCOUNT",
    "business": "061C074E2F91F944B93993B4",
    "banks": [
        {
            "bankName": "9Payment Service Bank",
            "accountNumber": "5030200545",
            "accountName": "Payvessel-MUSA OLA",
            "trackingReference": "40HTTGT96CDF360C3DRVGV3J"
        },
       
    ]
}


PAYMENT NOTIFICATION


SECURITY TIPS TO PROTECT YOUR WEBHOOK ENDPOINT
1.Verify Payvessel Hash Signature:
When receiving data from a webhook, it's crucial to ensure the data hasn't been tampered with during transmission. To achieve this, follow these steps:
1.1 Retrieve Payvessel Signature: Extract the Payvessel signature from the request's metadata. In most cases, this will be available in the HTTP_PAYVESSEL_HTTP_SIGNATURE header.
1.2 Generate Hash for Payload: Use your secret key as the key for an HMAC (Hash-based Message Authentication Code) with the SHA-512 algorithm. The payload of the webhook request is used as the message input for this HMAC function. This will generate a hash value.
1.3 Compare Hashes: Compare the generated hash with the Payvessel signature received in the request's metadata. If they match, it indicates that the data hasn't been tampered with, ensuring the authenticity of the webhook request.
1.4 Verify Payvessel IP Address:
To enhance security further, you can validate that the incoming webhook request originates from a trusted Payvessel server. Here's how:
1.5 Retrieve IP Address: Obtain the IP address of the incoming webhook request. You can usually find this in the REMOTE_ADDR field of the request's metadata.
1.6 Compare IP Address: Check if the IP address matches a predefined list of trusted Payvessel server IP addresses. In your case, it appears that the trusted IP address is "162.246.254.36." If the IP address doesn't match, it may be an unauthorized request, and you should reject it.
1.7 Prevent Duplicate Transactions:
Webhooks can sometimes be delivered multiple times due to network issues or retries. To avoid processing the same transaction multiple times:
1.8 Transaction History Check: Before processing the webhook data, query your payment transaction database to check if a transaction with the same reference or identifier already exists. If a matching transaction is found, it may indicate a duplicate request, and you can choose to ignore it or handle it as necessary.
By implementing these security tips, you can protect your webhook endpoint from tampered data, ensure that requests come from trusted sources, and prevent duplicate processing of transactions, ultimately enhancing the security and reliability of your webhook integration with Payvessel.


PYTHON DJANGO SAMPLE WEBHOOK

@require_POST
@csrf_exempt
def payvessel_payment_done(request):
        payload = request.body
        payvessel_signature = request.META.get('HTTP_PAYVESSEL_HTTP_SIGNATURE')
        #this line maybe be differ depends on your server
        #ip_address = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))
        ip_address = u'{}'.format(request.META.get('REMOTE_ADDR'))
        secret = bytes("PVSECRET-", 'utf-8')
        hashkey = hmac.new(secret,request.body, hashlib.sha512).hexdigest()
        if payvessel_signature == hashkey  and ip_address == "162.246.254.36":
                data = json.loads(payload)
                print(data)
                amount = float(data['order']["amount"])
                settlementAmount = float(data['order']["settlement_amount"])
                fee = float(data['order']["fee"])
                reference = data['transaction']["reference"]
                description = data['order']["description"]
                settlementAmount = settlementAmount 
                
                ###check if reference already exist in your payment transaction table   
                if not paymentgateway.objects.filter(reference=reference).exists():
                   
                    #fund user wallet here
                    return JsonResponse({"message": "success",},status=200) 
                        
                else:
                    return JsonResponse({"message": "transaction already exist",},status=200) 
        
        else:
            return JsonResponse({"message": "Permission denied, invalid hash or ip address.",},status=400) 
'''

# import requests

# headers = {
#     'api-key': 'PVKEY-K6AICOC1BP6W8TVSQD3WOJM2SIWCX57K',
#     'api-secret': 'Bearer PVSECRET-5CQIJKA16EBCVL6WY7DH8OQ57DZQDZ2YXGA76NK64QRBGT5OCRWQ8KBZTYYA603S',
#     'Content-Type': 'application/json'
# }

# data = {
#     "email": "ekweredaniel8@gmail.com",
#     "name": "Daniel Ekwere",
#     "phoneNumber": "07013116710",
#     "bankcode": ["120001"],
#     "businessid": "064A4A647B0E4C3D8D83F68985FA31A9"
# }

# response = requests.post(
#     'https://api.payvessel.com/api/external/request/customerReservedAccount/',
#     headers=headers,
#     json=data  # Use the 'json' parameter to send the data as JSON
# )

# print(response.status_code)
# dat = response.json()
# print(dat['banks'][0]['bankName'],)
# print(dat['banks'][0]['accountNumber'],)
# print(dat['banks'][0]['accountName'],)
# print(dat['banks'][0]['trackingReference'],)
# print(requests.user)

# res = {
#     "status": "true",
#     "service": "CREATE_VIRTUAL_ACCOUNT",
#     "business": "061C074E2F91F944B93993B4",
#     "banks": [
#         {
#             "bankName": "9Payment Service Bank",
#             "accountNumber": "5030200545",
#             "accountName": "Payvessel-MUSA OLA",
#             "trackingReference": "40HTTGT96CDF360C3DRVGV3J"
#         },
       
#     ]
# }

# print(res['banks'][0]['bankName'])
# print(res['banks'][0]['accountNumber'])
# print(res['banks'][0]['trackingReference'])

# https://github.com/DANIEL-EKWERE/databank-api.git

# import requests,json
# res = requests.post('http://127.0.0.1:8000/api/user/login-user/',data={'username':'DANIEL1','password':'123450'})
# if res.status_code == 200:
#     print(res.json())
# response = requests.post('http://127.0.0.1:8000/api/token/',data={'username':'DANIEL@','password':'123450'})
# if response.status_code == 200:
#     res_data = response.json()
#     access_token = res_data.get('access')
#     print(access_token)
#     print(res_data)
# else:
#     print('404',response.status_code)

# dic = {
#      "status": "success",
#      "message": {
#          "id": "842bf3af-e36f-4e30-8058-ea0d686af17f",
#          "detail": "You have purchased 2GB Data from MTN",
#          "date_and_time": "2023-11-11T15:22:10.191570Z",
#          "old_balance": "7213.00",
#          "new_balance": "6753.00",
#          "phone_number": "07013116710",
#          "status": "Success",
#          "amount": "460.00",
#          "type": "Data"
#         }
#  }

# # print(dic)
# print(dic['message']['id'])

import random
num_3 = random.randint(7, 9)
print(num_3)

# https://github.com/codewithsheriga/paystackIntegration.git/

# api.paystack.co/transaction/initialize

# curl https://api.paystack.co/transaction/initialize 
# -H "Authorization: Bearer sk_test_DEFAULT"
# -H "Content-Type: application/json"
# -X POST


# curl https://api.paystack.co/transaction/initialize 
# -H "Authorization: Bearer sk_test_DEFAULT"
# -H "Content-Type: application/json"
# -d {"amount": _, "email": _}
# -X POST

# for sending money

# curl https://api.paystack.co/transferrecipient 
# -H "Authorization: Bearer sk_test_DEFAULT"
# -H "Content-Type: application/json"
# -X POST

data = {
    'username':'moses2',
    'password':'interpo1',
}
login = requests.post('http://127.0.0.1:8000/api/user/login-user/',data=data)

if login.status_code == 200 or login.status_code == 201:
    print('login successful');
    access = login.json()
    token = access.get('token')
   # print(token)
    print(access)
print(login.status_code)



access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA3NDUyMDM2LCJpYXQiOjE3MDM4NTIwMzYsImp0aSI6IjMzY2I3ZTdiYzY1MzRkYzZhMmQ4MTNkYWRkYmM0ZjdhIiwidXNlcl9pZCI6NX0.-gDFYkAB0U9ADeQ0lcM5c14YTbs5e_H_k9zCGhmjGVk'
header = {
    'Content-Type': 'application/json',
    'Authorization' : f'Bearer {access_token}',
}

data1 = {
"location":"Nigeria",
"phone":"07065919223",
"state":"Akwa Ibom",
"recommended_by":"dany4",
} 
create_profile = requests.post('http://127.0.0.1:8000/api/user/create/profile/',headers=header, json=data1)

if create_profile.status_code == 201:
    print('profile creation successful')
print(create_profile.status_code)
# response = json.loads(create_profile.text)
print(create_profile.text)
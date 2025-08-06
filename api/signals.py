from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Profile
import requests
from api.models import VirtualAccount

@receiver(post_save, sender=Profile)
def create_virtual_accounts(sender, instance, created, **kwargs):
    if created:
        bank_codes = ['PALMPAY', '9PSB', 'SAFEHAVEN']  # Example bank codes
        for bank_code in bank_codes:
            headers = {
                'Authorization': 'Bearer Bill_Stack-SEC-KEY-5a72c6e35a87d7e00a3a0b7885199bec',
                'Content-Type': 'application/json'
            }
            data = {
                "email": instance.user.email,
                "reference": f"sna{instance.phone}-{bank_code}",
                "firstName": instance.user.first_name,
                "lastName": instance.user.last_name,
                "phone": instance.phone,
                "bank": bank_code,
            }
            try:
                response = requests.post(
                    'https://api.billstack.co/v2/thirdparty/generateVirtualAccount/',
                    headers=headers,
                    json=data
                )

                # ...inside your for bank_code in bank_codes loop:
                if response.status_code == 200:
                    resp_data = response.json()
                    account_info = resp_data["data"]["account"][0]
                    VirtualAccount.objects.create(
                        profile=instance,
                        bank_name=account_info.get("bank_name"),
                        account_number=account_info.get("account_number"),
                        account_name=account_info.get("account_name"),
                        bank_code=bank_code
                    )
                    print(account_info.get("bank_name"))
                    print(account_info.get("account_number"))
                    print(account_info.get("account_name"))
                else:
                    print(f"Failed to create virtual account for {bank_code}: {response.text}")
            except Exception as e:
                print(f"Error creating virtual account for {bank_code}: {e}")
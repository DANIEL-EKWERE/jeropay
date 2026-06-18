from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail
from api.models import Profile
import requests
from api.models import VirtualAccount

BILLSTACK_KEY = 'Bearer Bill_Stack-SEC-KEY-5a72c6e35a87d7e00a3a0b7885199bec'
BILLSTACK_URL = 'https://api.billstack.co/v2/thirdparty/generateVirtualAccount/'
BANK_CODES = ['PALMPAY', '9PSB', 'SAFEHAVEN']


def _create_virtual_account_for(profile, bank_code):
    """Attempt to create one virtual account. Returns True on success."""
    headers = {
        'Authorization': BILLSTACK_KEY,
        'Content-Type': 'application/json',
    }
    data = {
        "email": profile.user.email,
        "reference": f"sna{profile.phone}-{bank_code}",
        "firstName": profile.user.first_name or profile.user.username,
        "lastName": profile.user.last_name or '',
        "phone": profile.phone,
        "bank": bank_code,
    }
    response = requests.post(BILLSTACK_URL, headers=headers, json=data, timeout=15)
    print(f"Billstack [{bank_code}] {response.status_code}: {response.text[:300]}")

    if response.status_code != 200:
        print(f"Billstack non-200 for {bank_code}: {response.text}")
        return False

    resp_data = response.json()
    data_block = resp_data.get("data", {})
    accounts = data_block.get("account", [])
    if not accounts:
        print(f"Billstack empty account list for {bank_code}: {resp_data}")
        return False

    account_info = accounts[0]
    VirtualAccount.objects.create(
        profile=profile,
        bank_name=account_info.get("bank_name", ""),
        account_number=account_info.get("account_number", ""),
        account_name=account_info.get("account_name", ""),
        bank_code=bank_code,
    )
    print(f"Virtual account created [{bank_code}]: {account_info.get('account_number')}")
    return True


@receiver(post_save, sender=Profile)
def create_virtual_accounts(sender, instance, created, **kwargs):
    if not created:
        return

    any_failed = False
    for bank_code in BANK_CODES:
        try:
            success = _create_virtual_account_for(instance, bank_code)
            if not success:
                any_failed = True
        except Exception as e:
            print(f"Error creating virtual account for {bank_code}: {e}")
            any_failed = True

    if any_failed:
        Profile.objects.filter(pk=instance.pk).update(account_generation_failed=True)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    token = reset_password_token.key
    send_mail(
        'JeroPay Password Reset',
        (
            f'Hello {reset_password_token.user.username},\n\n'
            f'Your password reset token is:\n\n'
            f'    {token}\n\n'
            f'Open the JeroPay app, go to "Forgot Password", and enter this token along with your new password.\n\n'
            f'This token expires in 24 hours. If you did not request a password reset, ignore this email.'
        ),
        'no-reply@jeropay.com.ng',
        [reset_password_token.user.email]
    )
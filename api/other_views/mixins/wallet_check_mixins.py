from django.db import transaction
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from api.models import Wallet, Profile, Transaction

class WalletCheckMixin:

    def req_data(self, data):
        return {
            "exam": data["exam_name"],
            "quantity": data["quantity"]
        }

    def check_wallet_inst(self):
        # wallet = Wallet.objects.get(user=self.check_profile())
        try:
            wallet = Wallet.objects.get(user=self.check_profile())

        except:
            raise ValidationError( 'This Account does not have a Wallet, Contact support.',)
        
        return wallet
    
    def check_profile(self):
        try:
            profile = Profile.objects.get(user=self.request.user)
            
        except:
            raise ValidationError('This Account does not have a Profile')
            
        return profile

    def check_wallet_balance(self, amount):
        wallet = self.check_wallet_inst()
        balance = wallet.balance
        
        if balance >= amount :
            return balance
        else:
            raise ValidationError('Wallet balance is too low for the transaction, Please fund your Wallet.')

    def create_transaction_record(self, **other_params):
        return Transaction.objects.create(
            user=self.request.user,
            **other_params
        )


    def deduct_amount_from_balance(self, amount):
        old_balance = self.check_wallet_balance(amount)
        with transaction.atomic():
            new_balance = old_balance - amount
            Wallet.objects.filter(user= self.check_profile()).update(balance=new_balance)
            
        return old_balance, new_balance
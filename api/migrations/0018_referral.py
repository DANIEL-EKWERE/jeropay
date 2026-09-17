from django.db import migrations, models


class Migration(migrations.Migration):
    """
    No table changes: a proxy model so admin can list referrals, and a new
    'Bonus' choice on Transaction.type (choices aren't stored in the database).
    """

    dependencies = [
        ('api', '0017_inappnotification'),
    ]

    operations = [
        migrations.CreateModel(
            name='Referral',
            fields=[],
            options={
                'verbose_name': 'Referral',
                'verbose_name_plural': 'Referrals',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('api.profile',),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.CharField(choices=[('Data', 'Data'), ('Airtime', 'Airtime'), ('Cable', 'Cable'), ('Electricity', 'Electricity'), ('Exam', 'Exam'), ('Deposit', 'Deposit'), ('AdminCredit', 'AdminCredit'), ('AdminDebit', 'AdminDebit'), ('Transfer', 'Transfer'), ('Bonus', 'Bonus')], max_length=20),
        ),
    ]

# Generated by Django 3.2.1 on 2024-01-23 06:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Airtime',
            fields=[
                ('amount', models.DecimalField(decimal_places=2, max_digits=11)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('network', models.CharField(choices=[('MTN', 'MTN'), ('GLO', 'GLO'), ('AIRTEL', 'AIRTEL'), ('9MOBILE', '9MOBILE')], max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='CableSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('cable_service', models.CharField(choices=[('DStv Yanga + ExtraView', 'DStv Yanga + ExtraView'), ('DStv Premium French', 'DStv Premium French'), ('GOtv Max', 'GOtv Max'), ('Classic - 1200 Naira - 1 Week', 'Classic - 1200 Naira - 1 Week'), ('Nova - 900 Naira - 1 Month', 'Nova - 900 Naira - 1 Month'), ('Nova - 90 Naira - 1 Day', 'Nova - 90 Naira - 1 Day'), ('Gotv supa', 'Gotv supa'), ('Smart - 700 Naira - 1 Week', 'Smart - 700 Naira - 1 Week'), ('DStv Compact + Extra View', 'DStv Compact + Extra View'), ('GOtv Smallie - Yearly', 'GOtv Smallie - Yearly'), ('Classic - 320 Naira - 1 Day', 'Classic - 320 Naira - 1 Day'), ('DStv Padi + ExtraView', 'DStv Padi + ExtraView'), ('DStv Compact Plus', 'DStv Compact Plus'), ('ExtraView Access', 'ExtraView Access'), ('Smart - 2,200 Naira - 1 Month', 'Smart - 2,200 Naira - 1 Month'), ('DStv Confam + ExtraView', 'DStv Confam + ExtraView'), ('Nova - 90 Naira - 1 Day', 'Nova - 90 Naira - 1 Day'), ('Basic - 1,700 Naira - 1 Month', 'Basic - 1,700 Naira - 1 Month'), ('DStv Compact', 'DStv Compact'), ('Super - 1,500 Naira - 1 Week', 'Super - 1,500 Naira - 1 Week'), ('DStv Premium Asia', 'DStv Premium Asia'), ('DStv Asia', 'DStv Asia'), ('GOtv Jinja', 'GOtv Jinja'), ('Super - 400 Naira - 1 Day', 'Super - 400 Naira - 1 Day'), ('DStv Confam', 'DStv Confam'), ('DStv Premium + Extra View', 'DStv Premium + Extra View'), ('Super - 4,200 Naira - 1 Month', 'Super - 4,200 Naira - 1 Month'), ('Smart - 200 Naira - 1 Day', 'Smart - 200 Naira - 1 Day'), ('DStv Premium', 'DStv Premium'), ('DStv Compact Plus - Extra View', 'DStv Compact Plus - Extra View'), ('GOtv Smallie - Quarterly', 'GOtv Smallie - Quarterly'), ('Nova - 300 Naira - 1 Week', 'Nova - 300 Naira - 1 Week'), ('Basic - 160 Naira - 1 Day', 'Basic - 160 Naira - 1 Day'), ('Classic - 2,500 Naira - 1 Mont', 'Classic - 2,500 Naira - 1 Mont'), ('GOtv Smallie - Monthly', 'GOtv Smallie - Monthly'), ('Basic - 600 Naira - 1 Week', 'Basic - 600 Naira - 1 Week'), ('GOtv Jolli', 'GOtv Jolli'), ('DStv Padi', 'DStv Padi'), ('DStv HDPVR Access Service', 'DStv HDPVR Access Service'), ('DStv Yanga', 'DStv Yanga')], default='', max_length=50)),
                ('provider', models.CharField(choices=[('DSTV', 'DSTV'), ('GOTV', 'GOTV'), ('STARTIMES', 'STARTIMES')], default='', max_length=50)),
                ('amount', models.DecimalField(choices=[(5850, 5850), (29300, 29300), (4150, 4150), (1200, 1200), (900, 900), (90, 90), (5500, 5500), (700, 700), (11900, 11900), (7000, 7000), (320, 320), (5050, 5050), (14250, 14250), (2950, 2950), (2600, 2600), (8200, 8200), (90, 90), (1850, 1850), (9000, 9000), (1500, 1500), (23500, 23500), (7100, 7100), (1900, 1900), (400, 400), (5300, 5300), (23900, 23900), (4900, 4900), (200, 200), (21000, 21000), (17150, 17150), (2400, 2400), (300, 300), (160, 160), (2750, 2750), (900, 900), (600, 600), (2800, 2800), (2150, 2150), (2950, 2950), (4150, 4150)], decimal_places=2, default='', max_digits=15)),
                ('plan_id', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Data',
            fields=[
                ('amount', models.DecimalField(decimal_places=2, max_digits=11)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('network', models.CharField(choices=[('MTN', 'MTN'), ('GLO', 'GLO'), ('AIRTEL', 'AIRTEL'), ('9MOBILE', '9MOBILE')], max_length=30)),
                ('plan_type', models.CharField(choices=[('SME', 'SME'), ('SME2', 'SME2'), ('GIFTING', 'GIFTING'), ('CORPORATE GIFTING', 'CORPORATE GIFTING')], max_length=20)),
                ('bandwidth', models.CharField(choices=[('100MB', '100MB'), ('150MB', '150MB'), ('200MB', '200MB'), ('300MB', '300MB'), ('500MB', '500MB'), ('520MB', '520MB'), ('750MB', '750MB'), ('1GB', '1GB'), ('1.5GB', '1.5GB'), ('1.8GB', '1.8GB'), ('2GB', '2GB'), ('3GB', '3GB'), ('3.9GB', '3.9GB'), ('4.5GB', '4.5GB'), ('5GB', '5GB'), ('5.2GB', '5.2GB'), ('5.9GB', '5.9GB'), ('6GB', '6GB'), ('9.2GB', '9.2GB'), ('10GB', '10GB'), ('10.8GB', '10.8GB'), ('11GB', '11GB'), ('15GB', '15GB'), ('20GB', '20GB'), ('50GB', '50GB')], max_length=15)),
                ('network_id', models.CharField(default='', max_length=3)),
                ('price_desc', models.CharField(default='', max_length=100)),
                ('data_plan_id', models.CharField(default='', max_length=3)),
                ('reseller_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=11)),
            ],
            options={
                'ordering': ['amount'],
            },
        ),
        migrations.CreateModel(
            name='Deduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ElectricitySubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('electric_service', models.CharField(choices=[('Abuja Electricity Distribution Plc', 'AEDC'), ('Benin Electricity Distribution Plc', 'BEDC'), ('Eko Electricity Distribution Plc', 'EKEDC'), ('Enugu Electricity Distribution Plc', 'EEDC'), ('Ibadan Electricity Distribution Plc', 'IBEDC'), ('Ikeja Electricity Distribution Company', 'IKEDC'), ('Jos Electricity Distribution Plc', 'JEDPLC'), ('Kaduna Electricity Distribution Plc', 'KAEDCO'), ('Kano Electricity Distribution Plc', 'KEDCO'), ('Port Harcourt Electricity Distribution Plc', 'PHEDC'), ('Yola Electricity Distribution Company Plc', 'YEDC')], max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('location', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=11)),
                ('reseller', models.BooleanField()),
                ('state', models.CharField(choices=[('Abuja', 'Abuja'), ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'), ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'), ('Benue', 'Benue'), ('Borno', 'Borno'), ('Cross River', 'Cross River'), ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'), ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'), ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'), ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'), ('Lagos', 'Lagos'), ('Nassarawa', 'Nassarawa'), ('Niger', 'Niger'), ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'), ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'), ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'), ('Zamfara', 'Zamfara')], max_length=20)),
                ('profile_picture', models.ImageField(blank=True, upload_to='profile-pic/')),
                ('bank_name', models.CharField(blank=True, max_length=100)),
                ('account_number', models.CharField(blank=True, max_length=20)),
                ('account_name', models.CharField(blank=True, max_length=100)),
                ('code', models.CharField(blank=True, default='', max_length=10)),
                ('recommended_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='ref_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=11)),
                ('gateway', models.CharField(default='', max_length=100)),
                ('commission_balance', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('total_deposit', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True)),
                ('total_purchase', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='api.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('detail', models.CharField(max_length=300)),
                ('date_and_time', models.DateTimeField(auto_now_add=True)),
                ('old_balance', models.DecimalField(decimal_places=2, max_digits=11)),
                ('new_balance', models.DecimalField(decimal_places=2, max_digits=11)),
                ('phone_number', models.CharField(max_length=11)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Success', 'Success')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=11)),
                ('type', models.CharField(choices=[('Data', 'Data'), ('Airtime', 'Airtime'), ('Cable', 'Cable'), ('Electricity', 'Electricity')], max_length=20)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReservedAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservedaccountNumber', models.CharField(blank=True, max_length=100, null=True)),
                ('reservedbankName', models.CharField(blank=True, max_length=100, null=True)),
                ('reservedaccountName', models.CharField(blank=True, max_length=100, null=True)),
                ('accounts', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DepositRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=11)),
                ('date_and_time', models.DateTimeField(auto_now_add=True)),
                ('gateway', models.CharField(default='', max_length=100)),
                ('status', models.CharField(default='', max_length=100)),
                ('reference', models.CharField(default='', max_length=100)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.wallet')),
            ],
        ),
        migrations.CreateModel(
            name='ConfirmPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='confirmation-picture/')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

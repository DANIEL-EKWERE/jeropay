from django.urls import path

from .views import (
    CableSubscriptionAPIView,
    SingleDataNetworkView,
    AllDataNetworkView,
    ElectricitySubscriptionAPIView,
    SingleCableProviderPlan,
    )

# authetntication
from api.other_views.auth_views import CreateUserAccountView, CreateProfileAPIView, ChangePasswordView, UpdateProfileView,LoginUser,LogOut

# dashboard views
from api.other_views.user_views import (
    UserDashboardView,
    PaymentProofView,
    SingleTransaction,
    GetAllReservedAccount,
    ReservedAccountCreation,
    RecentTransactions,
    ToBeFilteredTransactions,
    AnnouncementApiView,

    # transactions for certain periods
    TransactionsToday,
    TransactionsYesterday,
    TransactionsLastWeek,
    TransactionsThisWeek,
    TransactionsLastMonth,
    TransactionsThisMonth,
    TransactionByRange,
    AllTransactionRecords,

    # customer phone numbers and other views
    FilterPhoneNumbersFromTransactions,
    FCMDeviceInfoConnectorAPI,

    # get wallet statistics
    WalleStatistic
    )

# purchase views
from api.other_views.purchase_views import (
    PurchaseAirtimeView,
    PurchaseDataView,
    DeductTest,
    DeductData,
    DataPriceListAPI,

    # exam epin
    PurchaseExamEpin,

    # electricity
    ValidateMeterNumberAPI,
    PurchaseElectricityView,

    # cable subscribptions
    ValidateCableNumberAPI,
    PurchaseCableSubscriptionView,
)

'''#admin only views'''

# sales tracking
from api.other_views.admin_only.sales_tracking_views import (
    DailySalesTracking,
    YesterdaySalesTracking,
    SalesTrackingForThisWeek,
    SalesTrackingForLastWeek,
    SalesTrackingForThisMonth,
    SalesTrackingForLastMonth,
    FilterTransactionsByRangeView,
)

# notification
from api.other_views.admin_only.notification_view import (
    AnnouncementNotificationView,
)

# Accont funding
from api.other_views.admin_only.fund_acct import (
    FundCustomerAccount,
    DisplayDepositRecordsView,
    DisplayDepositRecordsPerUserView,
    payment_webhook,

)

# Wallets
from api.other_views.admin_only.wallet_balance import CustomersWalletBalances ,UserWalletBalance

# Provider api balance view
from api.other_views.admin_only.provider_api_views import ProviderAPIBalanceView
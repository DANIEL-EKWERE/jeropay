from functools import wraps
from django.http import HttpResponseForbidden

def admin_whitelist_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Define your whitelist of IP addresses or other criteria
        whitelist = ['127.0.0.1', ]  # Example: Allow only localhost

        # Check if the user's IP is in the whitelist
        user_ip = request.META.get('REMOTE_ADDR', None)
        if user_ip not in whitelist:
            return HttpResponseForbidden("Access denied")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
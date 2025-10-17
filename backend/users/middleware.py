from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout

class AutoLogoutMiddleware:
    """
    Logs out users automatically after a set period of inactivity.
    Stores last activity in session under 'last_activity_auto_logout'.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        now = datetime.now()
        last_activity = request.session.get('last_activity_auto_logout')
        timeout_seconds = getattr(settings, 'AUTO_LOGOUT_TIMEOUT', 600)  # default 10 minutes

        if last_activity:
            last_activity = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
            inactivity = (now - last_activity).total_seconds()
            if inactivity > timeout_seconds:
                logout(request)
                try:
                    del request.session['last_activity_auto_logout']
                except KeyError:
                    pass
                return redirect('users:login')

        # Update last activity
        request.session['last_activity_auto_logout'] = now.strftime('%Y-%m-%d %H:%M:%S')
        return self.get_response(request)

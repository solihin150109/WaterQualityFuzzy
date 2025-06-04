# middleware.py
from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Periksa waktu terakhir aktivitas
            last_activity = request.session.get('last_activity')
            now = timezone.now().timestamp()

            if last_activity and (now - last_activity > settings.SESSION_COOKIE_AGE):
                # Logout pengguna jika sesi kedaluwarsa
                logout(request)
                return redirect('login')  # Redirect ke halaman login

            # Perbarui waktu terakhir aktivitas
            request.session['last_activity'] = now

        response = self.get_response(request)
        return response
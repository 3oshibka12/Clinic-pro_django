# clinic/middleware.py

from django.db import connection

class DatabaseRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        target_role = None
        user_id = -1 
        
        if request.user.is_authenticated:
            if request.user.is_superuser:
                target_role = None 
            elif request.user.is_staff:
                target_role = 'registrar'
            elif request.user.username == 'analyst':
                target_role = 'analyst'
            elif hasattr(request.user, 'doctor'):
                target_role = 'doctor_role'
                user_id = request.user.doctor.id_doc
            elif hasattr(request.user, 'patient'):
                target_role = 'patient_role'
                user_id = request.user.patient.id_pat
        
        if target_role:
            # === ОТЛАДКА: Выводим в консоль ===
            print(f"🔵 [Middleware] Роль: {target_role}, ID: {user_id}")
            # ==================================

            with connection.cursor() as cursor:
                cursor.execute(f"SET ROLE '{target_role}'")
                cursor.execute("SELECT set_config('app.user_id', %s, false)", [str(user_id)])

        try:
            response = self.get_response(request)
        finally:
            if target_role:
                with connection.cursor() as cursor:
                    cursor.execute("RESET ROLE")

        return response
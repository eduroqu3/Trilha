from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def papel_requerido(*papeis):
    papeis = set(papeis)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role not in papeis:
                messages.error(
                    request, "Este espaço é reservado a outro perfil de acesso."
                )
                return redirect("home")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator

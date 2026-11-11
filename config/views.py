from django.shortcuts import render


def landing_page(request):
    return render(request, "landing.html")


def anonimato(request):
    return render(request, "anonimato.html")

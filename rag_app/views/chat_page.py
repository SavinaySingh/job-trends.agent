from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


@csrf_exempt
def chat_page(request, *args, **kwargs):
    return render(request, "index.html")

from django.shortcuts import render


def index(request):
    template_name = 'index.html'

    context = {
        'is_authenticated': request.user.is_authenticated,
        'is_index': True,
    }
    return render(request, template_name, context)

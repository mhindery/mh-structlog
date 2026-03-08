from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path


def my_view(request):
    return HttpResponse("Hello, world!")


urlpatterns = [path("", my_view, name="main-view")]

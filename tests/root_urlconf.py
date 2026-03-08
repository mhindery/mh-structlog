from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path


def my_view(request):
    return HttpResponse("Hello, world!")


def redirect(request):
    return HttpResponseRedirect("/redirect_to/")


def http_404_view(request):
    return HttpResponse("Not found", status=404)


urlpatterns = [path("", my_view, name="main-view")]

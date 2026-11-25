"""Where a form goes after Save: the page the user came from."""
from django.utils.http import url_has_allowed_host_and_scheme


def came_from(request):
    """?next= or the posted next (kept from when the form opened), else the referring page of
    this site when the form opens. None when there is none (or it is the form itself)."""
    url = request.POST.get("next") or request.GET.get("next")
    if not url and request.method == "GET":
        url = request.META.get("HTTP_REFERER")
    if not url or not url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return None
    if url.split("?")[0].endswith(request.path):  # reloading the form itself is not "where they came from"
        return None
    return url

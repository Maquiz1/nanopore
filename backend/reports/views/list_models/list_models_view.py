from utils import access
from utils.access_mixins import require_feature
from django.shortcuts import redirect

@require_feature(access.EXPORTS)
def list_all_models_view(request):
    """The data export now lives on the Codebook & Data Export page."""
    return redirect("reports:codebook")

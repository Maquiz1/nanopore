from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# @login_required
# def user_dashboard(request):
#     return render(request, 'dashboard/home.html', {'user': request.user})


from django.shortcuts import render
from locations.models import Country
from clinical.models import Disease
from mentorship.models import Visit

def user_dashboard(request):
    country_count = Country.objects.count()
    disease_count = Disease.objects.count()
    visit_count = Visit.objects.count()
    recent_visits = Visit.objects.select_related('site', 'mentor').order_by('-start_date')[:5]

    return render(request, 'dashboard/home.html', {
        'country_count': country_count,
        'disease_count': disease_count,
        'visit_count': visit_count,
        'recent_visits': recent_visits,
    })

from django.urls import path
from . import views
from .views import VisitListView, VisitDetailView,VisitCreateView,VisitDeleteView,VisitDayUpdateView, VisitDayDeleteView
from .views import AssignCompetenceView, VisitDayDetailView,AssignedCompetenceUpdateView,MentorGradeView,MenteeSelfAssessmentView

app_name = 'mentorship'

urlpatterns = [
    path("", views.index, name="index"),
]

urlpatterns += [
    path('visit-day/<int:pk>/edit/', VisitDayUpdateView.as_view(), name='edit-visit-day'),
    path('visit-day/<int:pk>/delete/', VisitDayDeleteView.as_view(), name='delete-visit-day'),
]

urlpatterns += [
    path('visit/add/', VisitCreateView.as_view(), name='add-visit'),
    path('visit/<int:pk>/delete/', VisitDeleteView.as_view(), name='delete-visit'),
]

urlpatterns += [
    path('visits/', VisitListView.as_view(), name='visit-list'),
    path('visit/<int:pk>/', VisitDetailView.as_view(), name='visit-detail'),
]


urlpatterns += [
    path('visit_day/<int:visit_day_id>/', VisitDayDetailView.as_view(), name='visit-day-detail'),
    path('visit_day/<int:visit_day_id>/assign/', AssignCompetenceView.as_view(), name='assign-ompetence'),
    path('assigned_competence/<int:pk>/edit/', AssignedCompetenceUpdateView.as_view(), name='assigned-competence-edit'),
    path('assignment/<int:pk>/mentor-grade/', MentorGradeView.as_view(), name='mentor-grade'),
    path('assignment/<int:pk>/self-assess/', MenteeSelfAssessmentView.as_view(), name='mentee-self-assess'),
    path('assignment/<int:pk>/view/', views.AssignedCompetenceDetailView.as_view(), name='assigned-competence-view'),
]



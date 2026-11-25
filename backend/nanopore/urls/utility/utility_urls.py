from django.urls import path

from nanopore.views.history_view import RecordHistoryView
from nanopore.views import CheckPIDView, SystemControlsView, MasterDataListView
from nanopore.views.study_views import PostLockCorrectionsView, RecordVerifyView, VerificationView

urlpatterns = [
    path("history/<str:form_key>/<int:pk>/", RecordHistoryView.as_view(), name="record-history"),
    path("check-pid/", CheckPIDView.as_view(), name="check-pid"),
    path("system-controls/", SystemControlsView.as_view(), name="system-controls"),
    path("post-lock-corrections/", PostLockCorrectionsView.as_view(), name="post-lock-corrections"),
    path("verify-record/", RecordVerifyView.as_view(), name="record-verify"),
    path("verification/", VerificationView.as_view(), name="verification"),
    path("master-data/", MasterDataListView.as_view(), name="master-data-list"),
]

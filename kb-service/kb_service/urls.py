from django.contrib import admin
from django.urls import path

from app.views import (
    KBBehaviorEventView,
    KBCollectView,
    KBHealthView,
    KBRecommendTopView,
    KBRecommendView,
    KBSemanticSearchView,
    KBSyncStatusView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/kb/health/", KBHealthView.as_view(), name="kb-health"),
    path("api/kb/collect/", KBCollectView.as_view(), name="kb-collect"),
    path("api/kb/search/semantic/", KBSemanticSearchView.as_view(), name="kb-search-semantic"),
    path("api/kb/sync/status/", KBSyncStatusView.as_view(), name="kb-sync-status"),
    path("api/kb/behavior/", KBBehaviorEventView, name="kb-behavior-event"),
    path("api/kb/recommend/", KBRecommendView, name="kb-recommend"),
    path("api/kb/recommend/top/", KBRecommendTopView, name="kb-recommend-top"),
]

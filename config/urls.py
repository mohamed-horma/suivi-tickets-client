from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tickets.views import LotViewSet, PhaseViewSet, ProjectViewSet, TicketViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"phases", PhaseViewSet, basename="phase")
router.register(r"lots", LotViewSet, basename="lot")
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]

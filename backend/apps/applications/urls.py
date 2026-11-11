from rest_framework.routers import DefaultRouter

from apps.applications.views import JobApplicationViewSet

router = DefaultRouter()
router.register("applications", JobApplicationViewSet, basename="application")

urlpatterns = router.urls

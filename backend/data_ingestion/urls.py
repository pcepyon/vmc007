"""URL Configuration for data_ingestion project."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from data_ingestion.api.views import (
    UploadViewSet,
    StatusViewSet,
    ResearchFundingView,
    StudentDashboardView,
    PublicationDashboardView,
    DepartmentKPIView,
    FilterOptionsView
)

# DRF Router setup
router = DefaultRouter()

# No router registration needed for custom routes

urlpatterns = [
    # Upload endpoint: POST /api/upload/
    path('api/upload/', UploadViewSet.as_view({'post': 'create'}), name='upload-files'),

    # Status endpoint: GET /api/upload/status/<job_id>/
    path('api/upload/status/<str:pk>/', StatusViewSet.as_view({'get': 'retrieve'}), name='upload-status'),

    # Research Funding Dashboard endpoint: GET /api/dashboard/research-funding/
    path('api/dashboard/research-funding/', ResearchFundingView.as_view({'get': 'list'}), name='research-funding-list'),

    # Student Dashboard endpoint: GET /api/dashboard/students/
    path('api/dashboard/students/', StudentDashboardView.as_view({'get': 'list'}), name='student-dashboard-list'),

    # Publication Dashboard endpoint: GET /api/dashboard/publications/
    path('api/dashboard/publications/', PublicationDashboardView.as_view({'get': 'list'}), name='publication-dashboard-list'),

    # Department KPI Dashboard endpoint: GET /api/dashboard/department-kpi/
    path('api/dashboard/department-kpi/', DepartmentKPIView.as_view({'get': 'list'}), name='department-kpi-list'),

    # Filter Options endpoint: GET /api/dashboard/filter-options/
    path('api/dashboard/filter-options/', FilterOptionsView.as_view({'get': 'list'}), name='filter-options-list'),
]

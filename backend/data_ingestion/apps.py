"""
Django app configuration for data_ingestion.
"""

from django.apps import AppConfig


class DataIngestionConfig(AppConfig):
    """Configuration for data ingestion app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_ingestion'
    verbose_name = 'Data Ingestion'

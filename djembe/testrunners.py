from django.core import mail
from django.conf import settings

from django_coverage.coverage_runner import CoverageRunner


class TestSuiteRunner(CoverageRunner):
    """
    Just resets EMAIL_BACKEND to whatever was specified in settings.
    """

    def setup_test_environment(self, **kwargs):
        super(TestSuiteRunner, self).setup_test_environment(**kwargs)
        settings.EMAIL_BACKEND = mail.original_email_backend

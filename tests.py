import os
import sys

test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

os.environ['DJANGO_SETTINGS_MODULE'] = 'djembe.testsettings'

from django.test.utils import get_runner
from django.conf import settings


def main():
    test_runner = get_runner(settings)(interactive=False, verbosity=2)
    failures = test_runner.run_tests(['djembe'])
    sys.exit(failures)

if __name__ == '__main__':
    main()

import os
import sys

test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

os.environ['DJANGO_SETTINGS_MODULE'] = 'djembe.testsettings'

def django_setup():
    pass

try:
    from django import setup as django_setup
except:
    pass

from django.test.utils import get_runner
from django.conf import settings


def main():
    django_setup()
    test_runner = get_runner(settings)(interactive=False, verbosity=2)
    failures = test_runner.run_tests(['djembe.tests'])
    sys.exit(failures)

if __name__ == '__main__':
    main()

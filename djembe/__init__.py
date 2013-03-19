"""
A Django email backend that encrypts outgoing mail with S/MIME.
"""
VERSION = (0, 1, 0)


def get_version():
    return '.'.join((str(d) for d in VERSION))

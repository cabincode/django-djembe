=============
django-djembe
=============

A Django email backend that encrypts outgoing mail with S/MIME.

Features
--------

It automatically encrypts messages to recipients for whom certificates are
available, falling back to cleartext for any recipients that don't have
certificates on file.

Add certificates for the addresses in settings.ADMINS and you can relax (a
little) about emailing notifications, Django error reports, or other
potentially sensitive information.

It supports multiple certificates per recipient address, so you can define
ADMINS as an alias, configure each recipient's address and certificate and
they'll all be able to read the messages.

If a private key is associated with a sending address, messages from that
sender will also be signed.

License
-------

It's in the public domain.

Installation
------------

``pip install django-djembe``

Configuration
-------------

#. Add ``djembe`` to your ``INSTALLED_APPS`` setting.

#. Create its model tables with ``manage.py migrate djembe``.

#. To use it as your default email backend, add this setting::

    EMAIL_BACKEND = 'djembe.backends.EncryptingSMTPBackend'

#. To use a cipher other than the default AES-256, specify it in
   settings.DJEMBE_CIPHER::

    DJEMBE_CIPHER = 'des_ede3_cbc'  # triple DES

   The intersection of M2Crypto's ciphers and RFC 3851 are:

   * ``des_ede3_cbc`` (required by the RFC)
   * ``aes_128_cbc`` (recommended, not required, by the RFC)
   * ``aes_192_cbc`` (recommended, not required, by the RFC)
   * ``aes_256_cbc`` (recommended, not required, by the RFC)
   * ``rc2_40_cbc`` (RFC requires support, but it's weak -- don't use it)

   RFC 5751 requires AES-128, and indicates that higher key lengths are of
   course the future. It marks tripleDES with "SHOULD-", meaning it's on its
   way out.

   The following mail clients have worked fine with AES-256 in my testing.

   * Mail.app 6.2 (Mac)
   * Thunderbird 17 (Mac, Linux)
   * Windows Live Mail (Windows 7)

   I'd recommend you try the default and fall back to 3DES if necessary.

#. Use the Django admin to add recipients that should receive encrypted mail.

   The simplest case is an Identity with a certificate. Any mail sent to that
   Identity will be encrypted.

   To create signing Identities, supply both a certificate and a private key --
   which must not have a passphrase, obviously. Any mail sent *from* the
   Identity's address will be signed with the private key.

   You can create multiple Identity records with the same address, but
   different certificates. This is how you encrypt mail to an alias or mailing
   list.

Contributing
------------

The project is on Github_. If you find a bug or have a feature request, please
add an issue there. Patches or pull requests are of course welcome, too. I
won't even make you add tests; just make sure you don't break what's already
there -- you can check by running ``python setup.py test`` in your working
copy.

.. _Github: https://github.com/cabincode/django-djembe/

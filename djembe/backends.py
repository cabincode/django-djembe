import email
import logging
import smtplib
import sys

from django.conf import settings
from django.core.mail.backends import base
from django.core.mail.backends import smtp
from django.core.mail.message import make_msgid
from django.core.mail.message import sanitize_address

from M2Crypto import BIO
from M2Crypto import SMIME
from M2Crypto import X509

from djembe.models import Identity


class EncryptingBackendMixin(object):
    """
    A mixin to encrypt, possibly sign, and finally deliver messages.

    Backends built with this should implement deliver(), and call send() for
    each message in send_messages().
    """
    logger = logging.getLogger('djembe.backends.EncryptingBackendMixin')

    payload_mime_headers = [
        'Content-Disposition',
        'Content-Type',
        'Mime-Version',
    ]

    def analyze_recipients(self, email_message):
        """
        Determine which recipients should get encrypted messages.
        """
        encrypting_identities = plaintext_recipients = None

        if email_message.recipients():
            recipients = set([
                sanitize_address(addr, email_message.encoding)
                for addr in email_message.recipients()
            ])

            encrypting_identities = Identity.objects.filter(address__in=recipients)
            encrypting_recipients = set([r.address for r in encrypting_identities])
            plaintext_recipients = recipients - encrypting_recipients

        return (encrypting_identities, encrypting_recipients, plaintext_recipients)

    def deliver(self, sender_address, recipients, message):
        """
        Handles the actual delivery of a message.
        """
        raise NotImplementedError

    def encrypt(self, sender_address, encrypting_identities, message):
        """
        Encrypts the given message for all the supplied recipients.
        """

        if not encrypting_identities:
            raise ValueError('Encrypting recipient identities not supplied.')

        if not message:
            raise ValueError('Valid Message not supplied.')

        s = SMIME.SMIME()

        cipher = getattr(settings, 'DJEMBE_CIPHER', 'aes_256_cbc')
        s.set_cipher(SMIME.Cipher(cipher))

        self.logger.debug("Encrypting message for %s" % encrypting_identities)

        # Gather all the recipient certificates
        sk = X509.X509_Stack()
        for identity in encrypting_identities:
            sk.push(identity.x509)
        s.set_x509_stack(sk)

        # prepare the payload for encryption
        payload_msg = self.extract_payload(message)

        # encrypt the payload
        payload = BIO.MemoryBuffer(payload_msg.as_string())
        pkcs7_encrypted_data = s.encrypt(payload)
        payload.close()

        # get the PKCS7 object into a string
        payload = BIO.MemoryBuffer()
        s.write(payload, pkcs7_encrypted_data)
        pkcs7_string = payload.read()
        payload.close()

        encrypted_message = email.message_from_string(pkcs7_string)

        message.set_payload(encrypted_message.get_payload())

        for header, value in encrypted_message.items():
            del message[header]
            message[header] = value
        del message['Message-ID']
        message['Message-ID'] = make_msgid()

        return message

    def extract_payload(self, message):
        payload_msg = email.message.Message()
        payload_msg.set_payload(message.get_payload())
        for header in self.payload_mime_headers:
            payload_msg[header] = message[header]
        return payload_msg

    def get_sender_identity(self, address):
        """
        Looks for an Identity matching the sender address.
        """
        sender_identity = None
        if address:
            sender_identities = Identity.objects.filter(
                address=address,
            ).exclude(key='')
            sender_count = sender_identities.count()
            if sender_count > 0:
                if sender_count == 1:
                    sender_identity = sender_identities[0]
                else:
                    self.logger.warning('Sender matches multiple identities; cannot sign the message.')
        else:
            raise ValueError('Sender address not supplied.')

        return sender_identity

    def send(self, email_message):
        """
        Sends a message, possibly signed, possibly encrypted.

        If the sender has a key, the message will be signed with it.

        Recipients for whom an Identity can be found will be sent an encrypted
        version, any others get plaintext.
        """
        sender_address = sanitize_address(
            email_message.from_email,
            email_message.encoding
        )
        sender_identity = self.get_sender_identity(sender_address)

        encrypting_identities, encrypting_recipients, plaintext_recipients = self.analyze_recipients(email_message)

        # work with the regular standard library message instead of Django's wrapper
        message = email_message.message()

        if sender_identity:
            message = self.sign(sender_identity, message)

        sent = 0
        if plaintext_recipients:
            try:
                self.deliver(
                    sender_address,
                    plaintext_recipients,
                    message.as_string()
                )
                sent += 1
            except:
                if self.fail_silently is False:
                    raise

        if encrypting_identities:
            try:
                encrypted_message = self.encrypt(
                    sender_address,
                    encrypting_identities,
                    message
                )

                self.deliver(
                    sender_address,
                    encrypting_recipients,
                    encrypted_message.as_string()
                )
                sent += 1
            except:
                if self.fail_silently is False:
                    if not sent:
                        raise
                    else:
                        exc_class, exc, tb = sys.exc_info()
                        new_exc = exc_class("Only partial success (messages sent before error: %s)" % sent)
                        raise new_exc.__class__, new_exc, tb

        return sent

    def sign(self, sender_identity, message):
        """
        Signs an email message.
        """

        self.logger.debug('Signing message as %s' % sender_identity)

        s = SMIME.SMIME()

        signing_cert = BIO.MemoryBuffer(str(sender_identity.certificate))
        signing_key = BIO.MemoryBuffer(str(sender_identity.key))
        s.load_key_bio(signing_key, signing_cert)

        # extract the payload from the original message, construct a temporary
        # message without all the header info, and sign that message's string
        # representation
        payload_msg = self.extract_payload(message)
        content_to_sign = payload_msg.as_string()

        pkcs7_signed_data = s.sign(
            BIO.MemoryBuffer(content_to_sign),
            flags=SMIME.PKCS7_DETACHED
        )

        # get the PKCS7 object into a string
        payload = BIO.MemoryBuffer()
        s.write(
            payload,
            pkcs7_signed_data,
            BIO.MemoryBuffer(content_to_sign),
            flags=SMIME.PKCS7_DETACHED
        )
        pkcs7_string = payload.read()
        payload.close()

        signed_message = email.message_from_string(pkcs7_string)

        message.set_payload(signed_message.get_payload())

        for header, value in signed_message.items():
            del message[header]
            message[header] = value

        return message


class EncryptingSMTPBackend(EncryptingBackendMixin, smtp.EmailBackend):
    """
    Delivers encrypted messages via SMTP.
    """

    def deliver(self, sender_address, recipients, message):
        """
        Handles the actual delivery of a message.
        """
        self.logger.info("Delivering message from %s to %s" % (sender_address, recipients))
        return self.connection.sendmail(
            sender_address,
            recipients,
            message
        )

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        self._lock.acquire()
        try:
            new_conn_created = self.open()
            if not self.connection and self.fail_silently is False:
                raise smtplib.SMTPConnectError('Cannot send without a valid connection')
            num_sent = 0
            for message in email_messages:
                num_sent += self.send(message)
            if new_conn_created:
                self.close()
        finally:
            self._lock.release()
        return num_sent


class EncryptingTestBackend(EncryptingBackendMixin, base.BaseEmailBackend):
    """
    Collects encrypted messages for review, instead of actually delivering them.
    """

    messages = []

    def deliver(self, sender_address, recipients, message):

        # poison pill #1
        if sender_address == 'breakerbreaker@example.com' and 'recipient1@example.com' in recipients:
            raise ValueError("He has a secret CB RADIO!")

        # poison pill #2
        if sender_address == 'breakerofthings@example.com':
            raise ValueError("He just can't help it.")

        self.messages.append({
            'sender': sender_address,
            'recipients': recipients,
            'message': message
        })

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        num_sent = 0
        for message in email_messages:
            num_sent += self.send(message)

        return num_sent

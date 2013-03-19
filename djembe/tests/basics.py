from django.core import mail
from django.test import TestCase

from djembe.models import Identity
from djembe.tests import data

from M2Crypto import BIO
from M2Crypto import SMIME
from M2Crypto import X509


class EncryptionTest(TestCase):

    def setUp(self):
        self.recipient1 = Identity.objects.create(
            certificate=data.RECIPIENT1_CERTIFICATE,
            key=data.RECIPIENT1_KEY
        )

        self.recipient2 = Identity.objects.create(
            certificate=data.RECIPIENT2_CERTIFICATE
        )

        self.list_member = Identity.objects.create(
            certificate=data.RECIPIENT1_CERTIFICATE,
            address='list@example.com'
        )

        self.list_member = Identity.objects.create(
            certificate=data.RECIPIENT2_CERTIFICATE,
            address='list@example.com'
        )

        self.text_template = 'S/MIME multipart test %s'
        self.html_template = '<h1>S/MIME Test</h1><p>Message <strong>%s</strong></p>'

    def testAllTheThings(self):
        """
        Test the full scenario: multiple encrypted and plaintext recipients.

        Tests that multiple recipients can all read a message, and that
        recipients with no Identity records get plain text.
        """
        count = 1
        sender = Identity.objects.get(address='recipient1@example.com')
        recipients = [identity.address for identity in Identity.objects.all()]
        recipients.extend([
            'recipient3@example.com',
            'recipient4@example.com'
        ])
        message = mail.EmailMultiAlternatives(
            self.text_template % count,
            self.text_template % count,
            sender.address,
            recipients
        )
        message.attach_alternative(self.html_template % count, "text/html")
        message.send()

        backend = mail.get_connection()
        self.assertEqual(len(backend.messages), 2)

        #
        # verify the encryption and signature
        #
        s = SMIME.SMIME()

        # Load the sender's cert.
        x509 = X509.load_cert_string(data.RECIPIENT1_CERTIFICATE)
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)

        # Load the sender's CA cert.
        st = X509.X509_Store()
        st.add_x509(x509)
        s.set_x509_store(st)

        # Decrypt the message as both encrypted recipients

        #
        # recipient 1
        #
        recipient1_cert = BIO.MemoryBuffer(data.RECIPIENT1_CERTIFICATE)
        recipient1_key = BIO.MemoryBuffer(data.RECIPIENT1_KEY)
        s.load_key_bio(recipient1_key, recipient1_cert)

        msg = BIO.MemoryBuffer(backend.messages[1]['message'])
        p7, msg_data = SMIME.smime_load_pkcs7_bio(msg)
        out = s.decrypt(p7)

        # Verify the message
        msg = BIO.MemoryBuffer(out)
        p7, msg_data = SMIME.smime_load_pkcs7_bio(msg)
        verified_msg = s.verify(p7, msg_data)
        self.assertTrue(verified_msg)

        #
        # recipient 2
        #
        recipient2_cert = BIO.MemoryBuffer(data.RECIPIENT2_CERTIFICATE)
        recipient2_key = BIO.MemoryBuffer(data.RECIPIENT2_KEY)
        s.load_key_bio(recipient2_key, recipient2_cert)

        msg = BIO.MemoryBuffer(backend.messages[1]['message'])
        p7, msg_data = SMIME.smime_load_pkcs7_bio(msg)
        out = s.decrypt(p7)

        # Verify the message
        msg = BIO.MemoryBuffer(out)
        p7, msg_data = SMIME.smime_load_pkcs7_bio(msg)
        self.assertTrue(s.verify(p7, msg_data))

        # verify that the plaintext also got through
        msg = BIO.MemoryBuffer(backend.messages[1]['message'])

    def testEncryptedDeliveryProblem(self):
        subject = 'No! Not the radio!'
        body = "10-4 good buddy!"
        sender = "breakerbreaker@example.com"
        recipient = "recipient1@example.com"

        try:
            mail.send_mail(subject, body, sender, [recipient])
            self.fail("Unless you're four-wheeling, CB radio is a problem.")
        except ValueError:
            pass

    def testIdentityInstance(self):
        self.assertEqual('C6:AF:98:41:75:D4:10:E9:BE:0A:5C:D8:7F:0E:6F:BB:A7:E1:B0:0E', self.recipient1.fingerprint)

    def testMixedMessages(self):
        message1 = mail.message.EmailMessage(
            subject='This is a poison message.',
            body="And will cause an exception.",
            from_email="breakerbreaker@example.com",
            to=["somebody@example.com", "recipient1@example.com"]
        )

        backend = mail.get_connection()

        try:
            backend.send_messages([message1])
            self.fail("Poison message should have thrown an exception.")
        except ValueError:
            pass

    def testNoMessageToEncrypt(self):
        backend = mail.get_connection()
        try:
            backend.encrypt('recipient1@example.com', ['recipient2@example.com'], '')
            self.fail('Lack of recipients should have raised an exception from encrypt method.')
        except ValueError:
            pass

    def testNoMessages(self):
        backend = mail.get_connection()
        sent = backend.send_messages([])
        self.assertEqual(0, sent)

    def testNoRecipientsToEncrypt(self):
        backend = mail.get_connection()
        try:
            backend.encrypt('recipient1@example.com', [], '')
            self.fail('Lack of recipients should have raised an exception from encrypt method.')
        except ValueError:
            pass

    def testPlainTextDeliveryProblem(self):
        subject = 'This is a poison message.'
        body = "And will cause an exception."
        sender = "breakerofthings@example.com"
        recipient = "deadletteroffice@example.com"

        try:
            mail.send_mail(subject, body, sender, [recipient])
            self.fail("Poison message should have thrown an exception.")
        except ValueError:
            pass

    def testSenderIdentity(self):
        backend = mail.get_connection()

        # should get an error with no address
        try:
            sender = backend.get_sender_identity('')
            self.fail('Lack of sender address should have raised an exception')
        except ValueError:
            pass

        # a single valid sender should return a valid Identity
        sender_address = 'multisender@example.com'
        Identity.objects.create(
            certificate=data.RECIPIENT1_CERTIFICATE,
            key=data.RECIPIENT1_KEY,
            address=sender_address
        )
        sender = backend.get_sender_identity(sender_address)
        self.assertTrue(sender is not None)
        self.assertEqual(sender.address, sender_address)

        # No Identity should be returned when more than one is found with a
        # given address
        Identity.objects.create(
            certificate=data.RECIPIENT1_CERTIFICATE,
            key=data.RECIPIENT1_KEY,
            address=sender_address
        )
        sender = backend.get_sender_identity(sender_address)
        self.assertTrue(sender is None)

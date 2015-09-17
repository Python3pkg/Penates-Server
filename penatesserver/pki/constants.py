# -*- coding: utf-8 -*-
from __future__ import unicode_literals, with_statement, print_function
from django.utils.translation import ugettext as _
__author__ = 'Matthieu gallet'


ENCIPHERMENT = "Encipherment"
SIGNATURE = "Signature"
EMAIL = "Email"
USER = "User"
CONFIGURATION = "Configuration"
KERBEROS_DC = "Kerberos DC"
OCSPSIGNING = "OCSPSigning"
COMPUTER = "Computer"
CA = "CA"
SERVICE = "Service"
SERVICE_1024 = 'Service1024'
PRINTER = "Printer"
RESOURCE = "Resource"
TIME_SERVER = "Time Server"
CA_TEST = "CA_TEST"
COMPUTER_TEST = "Computer_TEST"
TEST_DSA = 'TEST_DSA'
TEST_SHA256 = 'TEST_SHA256'

# digest types
MD2, MD5, MDC2, SHA1, SHA256, SHA512 = 'md2', 'md5', 'mdc2', 'sha1', 'sha256', 'sha512'
DIGEST_TYPES = ((SHA1, _('SHA1')), (MD5, _('MD5')), (MDC2, _('MDC2')), (SHA256, _('SHA256')), (SHA512, _('SHA512')))
# key types
RSA, DSA = 'rsa', 'dsa'
KEY_TYPES = ((RSA, _('RSA')), (DSA, _('DSA')), )
# cypher types
DES, DES3, CAMELLIA256, CAMELLIA192, AES192, AES256 = 'des', 'des3', 'camellia256', 'camellia192', 'aes192', 'aes256'
CYPHER_TYPES = ((AES256, _('AES 265')), (DES3, _('DES 3')), (DES, _('DES')), (CAMELLIA192, _('Camellia 192')),
                (CAMELLIA256, _('Camellia 256')), (AES192, _('AES 192')), )
# key lengths
KEY_LENGTHS = ((8192, _('8192')), (4096, _('4096')), (2048, _('2048')), (1024, _('1024')), (512, _('512')),
               (256, _('256')), )

# alternatives names
ALT_EMAIL, ALT_DNS, ALT_URI = 'email', 'DNS', 'URI'
ALT_TYPES = ((ALT_EMAIL, _('email')), (ALT_URI, _('URI')), (ALT_DNS, _('DNS')), )

CA_FALSE, CA_TRUE = 'CA:FALSE', 'critical, CA:TRUE'
BASIC_CONSTRAINTS = ((CA_FALSE, _('CA:FALSE')), (CA_TRUE, _('critical, CA:TRUE')), )
IDENTIFIER_OPTIONAL, IDENTIFIER_ALWAYS = 'keyid:optional, issuer:optional', 'keyid, issuer:always'
AUTHORITY_KEY_IDENTIFIER = ((IDENTIFIER_ALWAYS, IDENTIFIER_ALWAYS), (IDENTIFIER_OPTIONAL, IDENTIFIER_OPTIONAL), )
HASH_IDENTIFIER = 'hash'
SUBJECT_KEY_IDENTIFIER = ((HASH_IDENTIFIER, HASH_IDENTIFIER), )
# reasons for revoking a certificate
UNSPECIFIED, KEY_COMPROMISE, CA_COMPROMISE, AFFILIATION_CHANGED, SUPERSEDED, CESSATION_OF_OPERATION, CERTIFICATE_HOLD, \
    REMOVE_FROM_CRL = 'unspecified', 'keyCompromise', 'CACompromise', 'affiliationChanged', 'superseded', \
                      'cessationOfOperation', 'certificateHold', 'removeFromCRL'
CRL_REASONS = (
    (UNSPECIFIED, _('Unspecified')), (KEY_COMPROMISE, _('Compromised key')), (CA_COMPROMISE, _('Compromised CA')),
    (AFFILIATION_CHANGED, _('Changed affiliation')), (SUPERSEDED, _('Superseded')),
    (CESSATION_OF_OPERATION, _('Cessation of operation')),
    (CERTIFICATE_HOLD, _('Hold certificate')), (REMOVE_FROM_CRL, _('Remove from CRL'))
)

KEY_USAGES = ["keyEncipherment", "dataEncipherment", "keyAgreement", "digitalSignature", "nonRepudiation",
              "cRLSign", "keyCertSign", ]
NS_CERT_TYPES = ["client", "objCA", "emailCA", "sslCA", "server", "email", "objsign", ]
EXTENDED_KEY_USAGES = {"clientAuth": "clientAuth", "emailProtection": "emailProtection", "serverAuth": "serverAuth",
                       "nsSGC": "nsSGC", "1.3.6.1.5.2.3.5": "KDC Authentication", "timeStamping": "timeStamping",
                       "codeSigning": "codeSigning", "OCSPSigning": "OCSPSigning",
                       "1.3.6.1.5.2.3.4": "pkinit KPClientAuth",
                       "1.3.6.1.4.1.311.20.2.2": "Microsoft Smart Card Logon", "1.3.6.1.5.5.7.3.7": "IP Security User",
                       "1.3.6.1.5.5.8.2.2": "IP Security IKE Intermediate",
                       "1.3.6.1.4.1.311.10.3.12": "MS document signing", "1.3.6.1.5.5.7.3.5": "IP Security End System",
                       "1.3.6.1.5.5.7.3.6": "IP Security Tunnel Endpoint"}

ROLES = {
    TIME_SERVER: {
        "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096, "cypherType": AES256,
        "extendedKeyUsage": ["clientAuth", "nsSGC", "serverAuth", "timeStamping"],
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment", "nonRepudiation"],
        "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000,
        "nsCertType": ["client"], "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    RESOURCE: {
        "nsCertType": ["client"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"],
        "cypherType": AES256, "extendedKeyUsage": ["clientAuth"], "digest": SHA256, "keyType": RSA,
        "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000, "basicConstraints": CA_FALSE
    },
    PRINTER: {
        "nsCertType": ["client", "server"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 2048, "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"],
        "cypherType": AES256, "extendedKeyUsage": ["clientAuth", "serverAuth"], "digest": SHA256, "keyType": RSA,
        "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 2048, "days": 1000, "basicConstraints": CA_FALSE
    },
    SERVICE: {
        "nsCertType": ["client", "server"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 4096, "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"],
        "cypherType": AES256, "extendedKeyUsage": ["clientAuth", "nsSGC", "serverAuth"], "digest": SHA256, "keyType": RSA,
        "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000, "basicConstraints": CA_FALSE
    },
    SERVICE_1024: {
        "nsCertType": ["client", "server"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 1024, "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"],
        "cypherType": AES256, "extendedKeyUsage": ["clientAuth", "nsSGC", "serverAuth"], "digest": SHA256, "keyType": RSA,
        "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 1024, "days": 1000, "basicConstraints": CA_FALSE
    },
    CA: {
        "nsCertType": ["emailCA", "objCA", "sslCA"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 4096, "keyUsage": ["cRLSign", "digitalSignature", "keyCertSign"], "cypherType": AES256,
        "extendedKeyUsage": ["serverAuth"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER,
        "rsaBits": 4096, "days": 8000, "basicConstraints": CA_TRUE, "keyType": RSA,
    },
    CA_TEST: {
        "nsCertType": ["emailCA", "objCA", "sslCA"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 1024, "keyUsage": ["cRLSign", "digitalSignature", "keyCertSign"], "cypherType": AES256,
        "extendedKeyUsage": ["serverAuth"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER,
        "rsaBits": 1024, "days": 8000, "basicConstraints": CA_TRUE, "keyType": RSA,
    },
    COMPUTER: {
        "nsCertType": ["client"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"], "cypherType": AES256,
        "extendedKeyUsage": ["clientAuth"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096,
        "days": 1000, "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    COMPUTER_TEST: {
        "nsCertType": ["client"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 1024,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"], "cypherType": DES,
        "extendedKeyUsage": ["clientAuth"], "digest": MD5, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 1024,
        "days": 1000, "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    TEST_DSA: {
        "nsCertType": ["client"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 1024,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"], "cypherType": AES256,
        "extendedKeyUsage": ["clientAuth"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 1024,
        "days": 1000, "basicConstraints": CA_FALSE, "keyType": DSA,
    },
    TEST_SHA256: {
        "nsCertType": ["client"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 1024,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"], "cypherType": AES256,
        "extendedKeyUsage": ["clientAuth"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 1024,
        "days": 1000, "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    OCSPSIGNING: {
        "nsCertType": ["client", "server"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 4096, "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"],
        "cypherType": AES256, "extendedKeyUsage": ["OCSPSigning", "clientAuth", "nsSGC", "serverAuth"],
        "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000,
        "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    KERBEROS_DC: {
        "nsCertType": ["client"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment", "nonRepudiation"],
        "cypherType": AES256, "extendedKeyUsage": ["1.3.6.1.5.2.3.5", "clientAuth", "nsSGC", "serverAuth"],
        "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000,
        "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    CONFIGURATION: {
        "nsCertType": ["objsign"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096,
        "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment", "nonRepudiation"],
        "cypherType": AES256, "extendedKeyUsage": ["clientAuth", "codeSigning", "nsSGC"], "digest": SHA256,
        "keyType": RSA, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000,
        "basicConstraints": CA_FALSE
    },
    USER: {
        "nsCertType": ["client", "email"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 4096, "keyUsage": ["dataEncipherment", "digitalSignature", "keyAgreement", "keyEncipherment"],
        "cypherType": AES256, "basicConstraints": CA_FALSE, "keyType": RSA,
        "extendedKeyUsage": ["1.3.6.1.4.1.311.10.3.12", "1.3.6.1.4.1.311.20.2.2", "1.3.6.1.5.2.3.4",
                             "1.3.6.1.5.5.7.3.7", "1.3.6.1.5.5.8.2.2", "clientAuth", "emailProtection"],
        "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000,
    },
    EMAIL: {
        "nsCertType": ["email"], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30,
        "dsaBits": 4096, "keyUsage": ["dataEncipherment"], "cypherType": AES256,
        "extendedKeyUsage": ["emailProtection"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER,
        "rsaBits": 4096, "days": 1000, "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    SIGNATURE: {
        "nsCertType": [], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096,
        "keyUsage": ["digitalSignature", "keyAgreement", "keyEncipherment"], "cypherType": AES256,
        "extendedKeyUsage": ["1.3.6.1.4.1.311.10.3.12"], "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER,
        "rsaBits": 4096, "days": 1000, "basicConstraints": CA_FALSE, "keyType": RSA,
    },
    ENCIPHERMENT: {
        "nsCertType": [], "authorityKeyIdentifier": IDENTIFIER_ALWAYS, "crlDays": 30, "dsaBits": 4096,
        "keyUsage": ["dataEncipherment", "keyEncipherment"], "cypherType": AES256, "extendedKeyUsage": [],
        "digest": SHA256, "subjectKeyIdentifier": HASH_IDENTIFIER, "rsaBits": 4096, "days": 1000,
        "basicConstraints": CA_FALSE, "keyType": RSA,
    },
}

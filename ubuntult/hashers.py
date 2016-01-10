from collections import OrderedDict
from passlib.hash import phpass

from django.contrib.auth.hashers import BasePasswordHasher


class PHPassPasswordHasher(BasePasswordHasher):

    algorithm = 'phpass'

    def encode(self, password, salt):
        return 'phpass' + phpass.encrypt(password, salt=salt, ident='H')

    def verify(self, password, encoded):
        if encoded.startswith('phpass'):
            encoded = encoded[6:]
        return phpass.verify(password, encoded)

    def safe_summary(self, encoded):
        if encoded.startswith('phpass'):
            encoded = encoded[6:]
        h = phpass.from_string(encoded)
        return OrderedDict([
            ('algorithm', h.name),
            ('ident', h.ident.strip('$')),
            ('salt', h.salt),
            ('hash', h.checksum),
        ])

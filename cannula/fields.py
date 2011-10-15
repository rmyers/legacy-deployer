"""
This code is based on the djangosnippet #1095 and django-fields package.

You can find the originals:

* http://www.djangosnippets.org/snippets/1095/
* https://github.com/svetlyak40wt/django-fields

# TODO: maybe we should just require django-fields >= 0.1.1?
"""
import binascii
import datetime
import random
import string
import sys

from django import forms
from django.db import models
from django.conf import settings
from django.utils.encoding import smart_str, force_unicode

import pickle

class BaseEncryptedField(models.Field):

    def __init__(self, *args, **kwargs):
        cipher = kwargs.pop('cipher', 'AES')
        try:
            imp = __import__('Crypto.Cipher', globals(), locals(), [cipher], -1)
        except:
            imp = __import__('Crypto.Cipher', globals(), locals(), [cipher])
        self.cipher = getattr(imp, cipher).new(settings.SECRET_KEY[:32])
        self.prefix = '$%s$' % cipher

        max_length = kwargs.get('max_length', 40)
        self.unencrypted_length = max_length
        # always add at least 2 to the max_length:
        # one for the null byte, one for padding
        max_length += 2
        mod = max_length % self.cipher.block_size
        if mod > 0:
            max_length += self.cipher.block_size - mod
        kwargs['max_length'] = max_length * 2 + len(self.prefix)

        models.Field.__init__(self, *args, **kwargs)

    def _is_encrypted(self, value):
        return isinstance(value, basestring) and value.startswith(self.prefix)

    def _get_padding(self, value):
        # We always want at least 2 chars of padding (including zero byte),
        # so we could have up to block_size + 1 chars.
        mod = (len(value) + 2) % self.cipher.block_size
        return self.cipher.block_size - mod + 2


    def to_python(self, value):
        if self._is_encrypted(value):
            return force_unicode(
                self.cipher.decrypt(
                    binascii.a2b_hex(value[len(self.prefix):])
                ).split('\0')[0]
            )
        return value

    def get_db_prep_value(self, value):
        value = smart_str(value)

        if value is not None and not self._is_encrypted(value):
            padding = self._get_padding(value)
            if padding > 0:
                value += "\0" + ''.join([random.choice(string.printable)
                    for index in range(padding-1)])
            value = self.prefix + binascii.b2a_hex(self.cipher.encrypt(value))
        return value


class EncryptedTextField(BaseEncryptedField):
    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return 'TextField'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super(EncryptedTextField, self).formfield(**defaults)


class EncryptedCharField(BaseEncryptedField):
    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super(EncryptedCharField, self).formfield(**defaults)

    def get_db_prep_value(self, value):
        if value is not None and not self._is_encrypted(value):
            if len(value) > self.unencrypted_length:
                raise ValueError("Field value longer than max allowed: " +
                    str(len(value)) + " > " + str(self.unencrypted_length))
        return super(EncryptedCharField, self).get_db_prep_value(value)
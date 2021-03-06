##############################################################################
#
#    GNU Condo: The Free Management Condominium System
#    Copyright (C) 2016- M. Alonso <port02.server@gmail.com>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.modules.party.contact_mechanism import _PHONE_TYPES

try:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat, PhoneNumberType, NumberParseException
except ImportError:
    phonenumbers = None

__all__ = ['ContactMechanism']


class ContactMechanism(metaclass=PoolMeta):
    __name__ = 'party.contact_mechanism'

    @classmethod
    def __setup__(cls):
        super(ContactMechanism, cls).__setup__()
        cls.value.depends.append('value_compact')
        cls._error_messages.update(
            {'invalid_phonenumber': ('The phone number "%(phone)s" of ' 'party "%(party)s" is not valid.')}
        )

    @classmethod
    def format_value(cls, value=None, type_=None):
        if phonenumbers and type_ in _PHONE_TYPES:

            Configuration = Pool().get('party.configuration')
            config = Configuration(1)
            if config.party_phonecountry:
                code = config.party_phonecountry.code

            try:
                phonenumber = phonenumbers.parse(value, region=code)
            except NumberParseException:
                pass
            else:
                if phonenumbers.is_possible_number(phonenumber) and phonenumbers.is_valid_number(phonenumber):
                    if code and phonenumbers.is_valid_number_for_region(phonenumber, code):
                        value = phonenumbers.format_number(phonenumber, PhoneNumberFormat.NATIONAL)
                    else:
                        value = phonenumbers.format_number(phonenumber, PhoneNumberFormat.INTERNATIONAL)
        return value

    @classmethod
    def format_value_compact(cls, value=None, type_=None):
        if phonenumbers and type_ in _PHONE_TYPES:

            Configuration = Pool().get('party.configuration')
            config = Configuration(1)
            if config.party_phonecountry:
                code = config.party_phonecountry.code

            try:
                phonenumber = phonenumbers.parse(value, region=code)
            except NumberParseException:
                pass
            else:
                value = phonenumbers.format_number(phonenumber, PhoneNumberFormat.E164)
        return value

    @classmethod
    def validate(cls, mechanisms):
        super(ContactMechanism, cls).validate(mechanisms)

        for mechanism in mechanisms:
            mechanism.check_valid_phonenumber()

    def check_valid_phonenumber(self):
        if not phonenumbers or self.type not in _PHONE_TYPES:
            return

        Configuration = Pool().get('party.configuration')
        config = Configuration(1)
        if config.party_phonecountry:
            code = config.party_phonecountry.code

        try:
            phonenumber = phonenumbers.parse(self.value, region=code)
        except NumberParseException:
            self.raise_user_error('invalid_phonenumber', {'phone': self.value, 'party': self.party.rec_name})
        else:
            if not phonenumbers.is_possible_number(phonenumber) or not phonenumbers.is_valid_number(phonenumber):
                self.raise_user_error('invalid_phonenumber', {'phone': self.value, 'party': self.party.rec_name})
            elif phonenumbers.number_type(phonenumber) == PhoneNumberType.FIXED_LINE and self.type == 'mobile':
                self.raise_user_warning(
                    'warn_fixed_line_phone.%d' % self.id,
                    'The phone number "%(phone)s" is a fixed line number.',
                    {'phone': self.value},
                )
            elif phonenumbers.number_type(phonenumber) == PhoneNumberType.MOBILE and self.type != 'mobile':
                self.raise_user_warning(
                    'warn_mobile_line_phone.%d' % self.id,
                    'The phone number "%(phone)s" is a mobile line number.',
                    {'phone': self.value},
                )

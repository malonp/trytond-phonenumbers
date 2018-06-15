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

try:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat, PhoneNumberType, NumberParseException
except ImportError:
    phonenumbers = None

_PHONE_TYPES = {
    'phone',
    'mobile',
    'fax',
    }

__all__ = ['ContactMechanism']


class ContactMechanism(metaclass=PoolMeta):
    __name__ = 'party.contact_mechanism'

    value_compact = fields.Char('Value Compact', readonly=True)

    @classmethod
    def __setup__(cls):
        super(ContactMechanism, cls).__setup__()
        cls.value.depends.append('value_compact')
        cls._error_messages.update({
                'invalid_phonenumber': ('The phone number "%(phone)s" of '
                    'party "%(party)s" is not valid.'),
                })

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
                if phonenumbers.is_possible_number(phonenumber) and\
                    phonenumbers.is_valid_number(phonenumber):
                    if code and phonenumbers.is_valid_number_for_region(phonenumber, code):
                        value = phonenumbers.format_number(
                            phonenumber, PhoneNumberFormat.NATIONAL)
                    else:
                        value = phonenumbers.format_number(
                            phonenumber, PhoneNumberFormat.INTERNATIONAL)
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
                value = phonenumbers.format_number(
                    phonenumber, PhoneNumberFormat.E164)
        return value

    def _change_value(self, value, type_):
        self.value = self.format_value(value=value, type_=type_)
        self.value_compact = self.format_value_compact(
            value=value, type_=type_)
        self.website = value
        self.email = value
        self.skype = value
        self.sip = value
        self.other_value = value
        self.url = self.get_url(value=value)

    @fields.depends('value', 'type')
    def on_change_type(self):
        self.url = self.get_url(value=self.value)

    @fields.depends('value', 'type')
    def on_change_value(self):
        return self._change_value(self.value, self.type)

    @fields.depends('website', 'type')
    def on_change_website(self):
        return self._change_value(self.website, self.type)

    @fields.depends('email', 'type')
    def on_change_email(self):
        return self._change_value(self.email, self.type)

    @fields.depends('skype', 'type')
    def on_change_skype(self):
        return self._change_value(self.skype, self.type)

    @fields.depends('sip', 'type')
    def on_change_sip(self):
        return self._change_value(self.sip, self.type)

    @fields.depends('other_value', 'type')
    def on_change_other_value(self):
        return self._change_value(self.other_value, self.type)

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('value',) + tuple(clause[1:]),
            ('value_compact',) + tuple(clause[1:]),
            ]

    @classmethod
    def create(cls, vlist):
        table =  cls.__table__()
        cursor = Transaction().connection.cursor()

        mechanisms = super(ContactMechanism, cls).create(vlist)

        for mechanism in mechanisms:
            value = mechanism.format_value(
                value=mechanism.value, type_=mechanism.type)
            value_compact = mechanism.format_value_compact(
                value=mechanism.value, type_=mechanism.type)

            if value != mechanism.value:
                cursor.execute(*table.update(
                                columns=[table.value, table.value_compact],
                                values=[value, value_compact],
                                where=(table.id==mechanism.id)))
            elif value_compact != mechanism.value_compact:
                cursor.execute(*table.update(
                                columns=[table.value_compact],
                                values=[value_compact],
                                where=(table.id==mechanism.id)))

        return mechanisms

    @classmethod
    def write(cls, *args):
        table =  cls.__table__()
        cursor = Transaction().connection.cursor()

        super(ContactMechanism, cls).write(*args)

        actions = iter(args)
        for mechanisms, values in zip(actions, actions):
            for mechanism in mechanisms:
                value = mechanism.format_value(
                    value=mechanism.value, type_=mechanism.type)
                value_compact = mechanism.format_value_compact(
                    value=mechanism.value, type_=mechanism.type)

                if value != mechanism.value:
                    cursor.execute(*table.update(
                                    columns=[table.value, table.value_compact],
                                    values=[value, value_compact],
                                    where=(table.id==mechanism.id)))
                elif value_compact != mechanism.value_compact:
                    cursor.execute(*table.update(
                                    columns=[table.value_compact],
                                    values=[value_compact],
                                    where=(table.id==mechanism.id)))

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
            self.raise_user_error(
                'invalid_phonenumber', {
                    'phone': self.value,
                    'party': self.party.rec_name
                    })
        else:
            if not phonenumbers.is_possible_number(phonenumber) or\
               not phonenumbers.is_valid_number(phonenumber):
                self.raise_user_error(
                    'invalid_phonenumber', {
                        'phone': self.value,
                        'party': self.party.rec_name
                        })
            elif phonenumbers.number_type(phonenumber)==PhoneNumberType.FIXED_LINE and\
                self.type=='mobile':
                self.raise_user_warning('warn_fixed_line_phone.%d' % self.id,
                    'The phone number "%(phone)s" is a fixed line number.', {
                    'phone': self.value,
                    })
            elif phonenumbers.number_type(phonenumber)==PhoneNumberType.MOBILE and\
                self.type!='mobile':
                self.raise_user_warning('warn_mobile_line_phone.%d' % self.id,
                    'The phone number "%(phone)s" is a mobile line number.', {
                    'phone': self.value,
                    })

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


from trytond.model import ModelSQL, ValueMixin, fields
from trytond.modules.party.configuration import _ConfigurationValue
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

try:
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberFormat, PhoneNumberType
except ImportError:
    phonenumbers = None


__all__ = ['Configuration', 'ConfigurationPhoneCountry']


_PHONE_TYPES = {'phone', 'mobile', 'fax'}


party_phonecountry = fields.Many2One('country.country', 'Party Phonenumbers Country')


class Configuration(metaclass=PoolMeta):
    __name__ = 'party.configuration'

    party_phonecountry = fields.MultiValue(party_phonecountry)

    @classmethod
    def write(cls, *args):
        config = cls(1)

        if config.party_phonecountry:
            party_phonecountry_code = config.party_phonecountry.code
        else:
            party_phonecountry_code = ''

        super(Configuration, cls).write(*args)

        if config.party_phonecountry:
            party_phonecountry_code_new = config.party_phonecountry.code
        else:
            party_phonecountry_code_new = ''

        if phonenumbers and party_phonecountry_code_new != party_phonecountry_code:

            ContactMechanism = Pool().get('party.contact_mechanism')
            table = ContactMechanism.__table__()
            cursor = Transaction().connection.cursor()

            for contact in ContactMechanism.search([('type', 'in', _PHONE_TYPES)]):
                values = {}

                # value_compact use PhoneNumberFormat.E164
                phonenumber = phonenumbers.parse(contact.value_compact)
                region_code = phonenumbers.region_code_for_country_code(phonenumber.country_code)

                if region_code == party_phonecountry_code:
                    # consider phonenumber with extensions p.e. 918041213 ext.412
                    phonenumber = phonenumbers.parse(contact.value, region_code)
                    value = phonenumbers.format_number(phonenumber, PhoneNumberFormat.INTERNATIONAL)
                    cursor.execute(*table.update(columns=[table.value], values=[value], where=(table.id == contact.id)))

                elif region_code == party_phonecountry_code_new:
                    phonenumber = phonenumbers.parse(contact.value)
                    value = phonenumbers.format_number(phonenumber, PhoneNumberFormat.NATIONAL)
                    cursor.execute(*table.update(columns=[table.value], values=[value], where=(table.id == contact.id)))


class ConfigurationPhoneCountry(_ConfigurationValue, ModelSQL, ValueMixin):
    'Party Configuration PhoneCountry'
    __name__ = 'party.configuration.party_phonecountry'

    party_phonecountry = party_phonecountry
    _configuration_value_field = 'party_phonecountry'

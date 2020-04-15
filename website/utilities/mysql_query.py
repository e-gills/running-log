import pymysql
import datetime
import re


class Query(object):

    TYPE_RE = re.compile(r'\).*')
    STRING_TYPES = ['varchar', 'text', 'datetime', 'timestamp', 'date', 'time', 'year', 'char', 'blob',
                    'tinyblob', 'tinytext', 'mediumblob', 'mediumtext', 'longblob', 'longtext']
    NUMBER_TYPES = ['int', 'float', 'double', 'decimal', 'tinyint', 'smallint', 'mediumint', 'bigint']

    def __init__(self, conn: pymysql.Connection, table: str):
        self.conn = conn
        self.table = table
        # used to cache field info for multiple queries to same table
        self.field_information = {}
        # used to determine batch row size
        self.byte_limit = 500000

    def connect_to_db(self, db, create_if_missing=False):
        try:
            self.conn.select_db(db)
        except pymysql.DatabaseError:
            if create_if_missing:
                query = 'CREATE DATABASE IF NOT EXISTS {}'.format(db)
                self.execute_query(query)
                self.conn.select_db(db)
            else:
                raise pymysql.DatabaseError

    def select_query(self, query) -> list:
        with self.conn as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return rows

    def execute_query(self, query):
        with self.conn as cur:
            cur.execute(query)

    def delete_query(self, query):
        with self.conn as cur:
            cur.execute(query)

    def create_table_if_missing(self, create_table_syntax):
        query = 'SHOW TABLES LIKE "{}"'.format(self.table)
        table = self.select_query(query)
        if not table:
            self.execute_query(create_table_syntax)

    def select_count_star(self, count_field, fields=None, where=None) -> list:
        query = "SELECT count(*) as {}".format(count_field)
        if fields:
            query = "{}, {}".format(query, ", ".join(fields))
        query = "{} FROM {}".format(query, self.table)
        if where:
            query = "{} WHERE {}".format(query, where)
        count = self.select_query(query)
        return count[0] if len(count) > 0 else {}

    def select(self, fields, where=None, limit=None, order_by=None) -> list:
        """
        generate and executes select query
        :param fields: list of fields to select
        :param where: where query, without the 'where' text
        :param limit: optional limit to the query
        :param order_by: optional order by in list format [field, direction]
        :return: list of result rows
        """
        # max execution time of 10 seconds: avoids query killer and
        # also who wants a query running longer than 10 seconds anyways
        query = "SELECT {} FROM {}".format(', '.join(fields), self.table)
        if where:
            query = "{} WHERE {}".format(query, where)
        if order_by:
            query = "{} ORDER BY {}".format(query, self.create_order_by(order_by))

        if limit:
            query = "{} LIMIT {}".format(query, limit)

        return self.select_query(query)

    def create_order_by(self, order_by):
        if isinstance(order_by[0], list):
            order_by_string = []
            for order in order_by:
                order_by_string.append(u'{} {}'.format(order[0], order[1]))
            order_by_string = u', '.join(order_by_string)
        else:
            order_by_string = u'{} {}'.format(order_by[0], order_by[1])
        return order_by_string

    def get_table_field_types(self):
        """
        :return: dictionary with fields as keys
        """
        # return cached field info if there
        if self.field_information.get(self.table):
            return self.field_information.get(self.table)

        query = 'DESCRIBE {}'.format(self.table)
        raw_fields = self.select_query(query)
        fields = {}
        for field in raw_fields:
            type_long = field.get('Type').split('(')

            fields[field['Field']] = {'type': type_long[0]}

            if field['Null'] == 'YES':
                null = True
            else:
                null = False
            fields[field['Field']]['null'] = null

            if len(type_long) > 1:
                fields[field['Field']]['length'] = re.sub(self.TYPE_RE, '', type_long[1])

        # cache field info for next time
        self.field_information[self.table] = fields

        return fields

    def insert_update(self, data):
        """
        Insert update mySQL Statement
        :param data: list of data dictionaries
        :return:
        """
        # parse fields and values out of data
        fields = self.get_table_field_types()
        ft, vl = self.create_fields_values_for_query(data, fields)

        # create update list
        update_fields = []
        for field in ft:
            update_fields.append(u"{0}=VALUES({0})".format(field))
        update = u', '.join(update_fields)
        values = u', '.join(vl)
        fields = u'({})'.format(u', '.join(ft))

        query = u"INSERT INTO {} {} VALUES {} ON DUPLICATE KEY UPDATE {}".format(self.table, fields, values, update)
        self.execute_query(query)

    def insert(self, data):
        """
        Insert mySQL Statement
        :param data: list of data dictionaries
        :return:
        """
        # parse fields and values out of data
        fields = self.get_table_field_types()
        ft, vl = self.create_fields_values_for_query(data, fields)

        values = ', '.join(vl)
        fields = '({})'.format(u', '.join(ft))

        query = "INSERT INTO {} {} VALUES {}".format(self.table, fields, values)
        self.execute_query(query)

    def create_fields_values_for_query(self, data, field_info):
        """
        :param data: a list of dictionaries
        :param field_info: dictionary of fields
        :return: ft contains tuple of fields; vl are the values in a list (rows) of tuples (row)
        """
        # set fields as fields from the first row
        fields = list(data[0].keys())
        values = []
        for row in data:
            row_values = []

            # loop through fields because query will break if all rows don't have the same fields
            for field in fields:

                value = row.get(field)
                info = field_info.get(field)

                if value is not None:
                    if isinstance(value, datetime.datetime):
                        value = '"{}"'.format(value.strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(value, list):
                        value = '^'.join(value)
                    elif info.get('type') in self.STRING_TYPES:
                        value = value.replace('"', "'")
                        value = '"{}"'.format(value)
                    elif info.get('type') in self.NUMBER_TYPES:
                        value = str(value)
                else:
                    if info.get('null'):
                        value = 'null'
                    else:
                        value = '""'

                row_values.append(value)

            values.append('({})'.format(', '.join(row_values)))

        return fields, values

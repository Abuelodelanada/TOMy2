#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import copy
import sqlite3
import pymysql
import argparse
import configparser


from termcolor import colored, cprint
from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import History
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.lexers import SqlLexer
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle

sql_completer = WordCompleter(['create', 'select', 'insert', 'drop',
                               'delete', 'from', 'where', 'table'], ignore_case=True)

class DocumentStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    }
    styles.update(DefaultStyle.styles)


class TOMy:

    def __init__(self, db):
        """Constructor"""
        self.get_color_config()
        self.arguments()
        self.database = db
        self.connect()


    def arguments(self):
        """
        Parse arguments
        """
        parser = argparse.ArgumentParser(description='Connect to a MySQL\
                                         server')
        parser.add_argument("-u", "--user", dest='user',
                            help="The MySQL user name to use when connecting\
                            to the server.")
        parser.add_argument("-p", "--password", dest='password',
                            help="The password to use when connecting \
                            to the server.")

        parser.add_argument("-hs", "--host", dest='host',
                            help="Connect to the MySQL server on the \
                            given host.")

        parser.add_argument("-D", "--database", dest='database',
                            help="Database name.")

        parser.add_argument("-P", "--port", dest='port',
                            help="The TCP/IP port number to use for \
                            the connection.")

        parser.add_argument("-cnt", "--connection", dest='connection',
                            help="Select a conection saved in\
                            .connections file")

        self.args = parser.parse_args()

        if(self.args.connection is None):
            self.default_args = copy.copy(self.args)


    def connect(self):
        self.connection = pymysql.connect(
            host = self.args.host,
            user = self.args.user,
            passwd = self.args.password,
            db = self.args.database,
            cursorclass=pymysql.cursors.DictCursor
        )
        print(self.connection)


    def format_output(self, headers_tuple, result):
        """
        This method formats the query output
        Code inspired in http://code.activestate.com/recipes/\
                577202-render-tables-for-text-interface/
        """

        column_names = list()
        rows = list(result)

        for h in headers_tuple:
            column_names.append(h[0])

        headers = column_names
        fieldlen = []

        ncols = len(headers)
        print(result)
        print(rows)
        for i in headers:
            _max = 0
            for j in rows:
                if len(str(j[i])) > _max:
                    _max = len(str(j[i]))
            fieldlen.append(_max)

        for i in range(len(headers)):
            if len(str(headers[i])) > fieldlen[i]:
                fieldlen[i] = len(str(headers[i]))

        width = sum(fieldlen) + (ncols - 1) * 3 + 4

        bar = "-" * (width - 2)
        bar = "+" + bar + "+"
        pipe = '|'

        if(self.color_config_dict['borders'] in self.colors):
            bar = colored(bar, self.color_config_dict['borders'])
            pipe = colored(pipe, self.color_config_dict['borders'])

        #if(self.color_config_dict['borders_bold'] == 'True'):
        #    bar = colored(bar, 'bold')
        #    pipe = colored(pipe, 'bold')

        out = [bar]
        header = ""
        for i in range(len(headers)):
            header += pipe + " %s" % (str(headers[i]))\
                + " " * (fieldlen[i] - len(str(headers[i]))) + " "
        header += pipe
        out.append(header)
        out.append(bar)

        for i in rows:
            line = ""
            for j in i:
                field_value = self.None2NULL(str(i[j]))

                if(self.color_config_dict['result'] in self.colors):
                    r = colored(field_value,
                                      self.color_config_dict['result'])
                else:
                    r = field_value

                if(self.color_config_dict['result_bold'] == 'True'):
                    r = colored(r, 'bold')

                if(self.is_number(field_value) is True):
                    line += pipe + " " * (len(str(i[j])) - len(field_value)) +\
                        " %s " % r
                else:
                    line += pipe + " %s" % r + " " * (len(str(i[j])) -
                                                      len(field_value)) + " "
            out.append(line + pipe)

        out.append(bar)
        print("\r\n".join(out))


    def get_color_config(self):
        # Custom settings if you don't have set up in .config file
        self.color_config_dict = {'borders': 'red', 'borders_bold': 'True',
                                  'result': None, 'result_bold': 'False'}
        self.colors = ('red', 'cyan', 'green', 'magenta', 'blue')
        self.color_config = configparser.ConfigParser()
        self.color_config.read('.config')

        _color = self.color_config.get('colors', "borders",
                                       vars=self.color_config_dict)
        _borders_bold = self.color_config.get('colors', "borders_bold",
                                              vars=self.color_config_dict)
        _result = self.color_config.get('colors', "result",
                                        vars=self.color_config_dict)
        _result_bold = self.color_config.get('colors', "result_bold",
                                             vars=self.color_config_dict)
        self.color_config_dict['borders'] = _color
        self.color_config_dict['borders_bold'] = _borders_bold
        self.color_config_dict['result'] = _result
        self.color_config_dict['result_bold'] = _result_bold

    def None2NULL(self, none):
        """
        I should learn how to use MySQLdb convertions
        """
        if(none == 'None'):
            return 'NULL'
        else:
            return none

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False


    def main(self):
        self.database = db
        history = History()

        while True:
            try:
                text = get_input('> ', lexer=SqlLexer, completer=sql_completer, style=DocumentStyle, history=history)

            except EOFError:
                break  # Control-D pressed.

            with self.connection.cursor() as cursor:
                messages = cursor.execute(text)
                result = cursor.fetchall()
                header = cursor.description
                #print(result)
                print(header)
                if(header is not None):
                    self.format_output(header, result)

        print('GoodBye!')




if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]

    tomy = TOMy(db)
    tomy.main()

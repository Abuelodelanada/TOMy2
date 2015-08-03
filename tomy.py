#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import copy
import sqlite3
import pymysql
import argparse
import configparser

from tabulate import tabulate
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

    version = '0.1'
    connection_data = {'host': '', 'user': '', 'pass': '',
                       'database': '', 'port': 3306, 'conn': '',
                       'engine': '', 'autocommit': 'ON'}

    def __init__(self, db):
        """Constructor"""
        self.arguments()
        self.database = db
        self.connect()
        self.get_welcome()
        print(self.prompt)


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

        host = self.args.host
        user = self.args.user
        passwd = self.args.password
        db = self.args.database

        self.connection = pymysql.connect(
            host,
            user,
            passwd,
            db,
            cursorclass=pymysql.cursors.DictCursor
        )

        self.prompt = self.get_prompt(
            user,
            host,
            db)

        self.server_info()


    def get_welcome(self):
        welcome = '.:: Welcome to TOMy %s!' % (self.version)
        print(welcome)


    def get_prompt(self, user, host, database='None', autocommit='ON'):
        """
        Get a prompt
        """
        # Custom settings if you don't have set up in .config file
        prompt_config_dict = {'show_user': 'false', 'show_host': 'false',
                              'show_db': 'false', 'prompt_char': '>>>'}

        self.connection_data['host'] = host
        self.connection_data['user'] = user
        self.connection_data['database'] = database
        self.connection_data['autocommit'] = autocommit

        if(user == 'root'):
            user = colored(user, 'red')

        if(autocommit.upper() == 'ON'):
            autocommit = colored(autocommit, 'red')
        else:
            autocommit = colored(autocommit, 'green')

        try:
            prompt_config = configparser.ConfigParser()
            prompt_config.read('.config')
            prompt_config_dict['show_user'] = prompt_config.get('prompt',
                                                                "show_user"
                                                               ).lower()
            prompt_config_dict['show_host'] = prompt_config.get('prompt',
                                                                "show_host"
                                                               ).lower()
            prompt_config_dict['show_db'] = prompt_config.get('prompt',
                                                              "show_db"
                                                             ).lower()
            prompt_config_dict['prompt_char'] = prompt_config.get('prompt',
                                                                "prompt_char")
        except:
            # TODO: use exceptions in a decent way
            logging.error('Wrong section definition')

        prompt = 'conn: %s\n' % self.connection_data['conn']
        prompt = prompt + 'AutoCommit: %s\n'\
                 % (autocommit)
        if(prompt_config_dict['show_user'] == 'true'):
            if(prompt_config_dict['show_host'] == 'true'):
                prompt = '%s<%s@%s>' % (prompt, user, host)
            else:
                prompt = '%s<%s>' % (prompt, user)
        else:
            if(prompt_config_dict['show_host'] == 'true'):
                prompt = '%s<%s>' % (prompt, host)
            else:
                pass

        if(prompt_config_dict['show_db'] == 'true'):
            prompt = '%s [%s] ' % (prompt, database)

        prompt = prompt + prompt_config_dict['prompt_char'] + ' '
        return prompt

    def server_info(self):
        """
        Shows the server info
        """
        server_version = self.connection.server_version
        server_host = self.connection.host

        print('.:: Server engine: %s' % colored('MySQL', 'green'))
        print('.:: Server version: %s' % colored(server_version, 'green'))
        print('.:: Server host: %s' % colored(server_host, 'green'))


    def None2NULL(self, none):
        """
        I should learn how to use MySQLdb convertions
        """
        if(none == None):
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
                fetchall = cursor.fetchall()
                result = []
                description = cursor.description
                headers = []
                rowcount = cursor.rowcount

                for i in description:
                    headers.append(i[0])

                for record in fetchall:
                    result.append([self.None2NULL(record[d]) for d in headers])

                print(tabulate(result, headers, tablefmt="grid"))
                print(str(rowcount) + ' rows\n')


        print('GoodBye!')




if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]

    tomy = TOMy(db)
    tomy.main()

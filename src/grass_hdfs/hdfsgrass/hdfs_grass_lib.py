from __future__ import print_function
from __future__ import unicode_literals
import inspect
import logging
import os
import sys

path = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),os.pardir)
if not path in sys.path:
    sys.path.append( path)


from hdfswrapper.connections import Connection
from hdfswrapper import settings
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Table
from hdfsgrass.hdfs_grass_util import readDict, saveDict, getTmpFolder
from grass.pygrass.modules import Module
from grass.script.core import PIPE


class ConnectionManager:
    """

    """

    def __init__(self):

        self.conn_id = None
        self.conn_type = None
        self.host = None
        self.port = None
        self.login = None
        self.password = None
        self.schema = None
        self.authMechanism = None
        self.connected = False
        self.uri = None
        self.connectionDict = None
        self.connection = None

        self.session = settings.Session

    def _connect(self):
        if self.uri:
            self.connectionDict = {'uri': self.uri}
        else:
            self.connectionDict = {'host': self.host}
            if self.login:
                self.connectionDict['login'] = self.login
            if self.schema:
                self.connectionDict['schema'] = self.schema
            if self.conn_id:
                self.connectionDict['conn_id'] = self.conn_id
            if self.conn_type:
                self.connectionDict['conn_type'] = self.conn_type
            if self.password:
                self.connectionDict['password'] = self.password
            if self.port:
                self.connectionDict['port'] = self.port
        self.connection = Connection(**self.connectionDict)

    def addNewConnection(self):
        print('***' * 30)
        print("\n     Adding new connection \n       conn_type: %s  \n" % self.conn_type)
        self.session.add(self.connection)
        try:
            self.session.commit()
            self._setActiveConnection(self.conn_type, self.connectionDict['conn_id'])
        except IntegrityError, e:
            print("       ERROR conn_id already exists. Will be overwritten...\n")
            print('***' * 30)
            self.session.rollback()
            self.session.flush()
            self.removeConnById(self.connectionDict['conn_id'])
            self.addNewConnection()
            print('***' * 30)

    def setConenction(self, conn_id, conn_type,
                      host=None, port=None,
                      login=None, password=None,
                      schema=None, authMechanism=None):
        if None in [conn_id, conn_type]:
            print("ERROR: no conn_id or conn_type defined")
            return None
        self.conn_id = conn_id
        self.conn_type = conn_type
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self.schema = schema
        self.authMechanism = authMechanism

        self._connect()

    @staticmethod
    def dropConnectionTable():
        from sqlalchemy import MetaData
        try:
            md = MetaData()
            connTable = Table('connection', md)
            connTable.drop(settings.engine)
            os.remove(settings.grass_config)
            print('***' * 30)
            print("\n     Table of connection has been removed \n")
            print('***' * 30)
        except Exception, e:
            print('***' * 30)
            print("\n     No table exists\n")
            print('***' * 30)



    @staticmethod
    def showConnections():
        cn = settings.engine.connect()
        print('***' * 30)
        print("\n     Table of connection \n")
        try:
            result = cn.execute('select * from connection')
            for row in result:
                print("       %s\n" % row)
            cn.close()
        except Exception, e:
            print(e)
            print("        No connection\n")
        print('***' * 30)

    def setActiveConnection(self, conn_type=None, idc=None):
        self.setConenction(conn_type=conn_type, conn_id=idc)
        self._setActiveConnection()

    def _setActiveConnection(self, conn_type=None, idc=None):
        # print("Saving connection: %s"%settings.grass_config)
        if conn_type is None:
            conn_type = self.conn_type
        if idc is None:
            idc = self.conn_id
        cfg = readDict(settings.grass_config)
        cfg[conn_type] = idc
        saveDict(settings.grass_config, cfg)

    @staticmethod
    def getCurrentId(conn_type):
        cfg = readDict(settings.grass_config)
        if cfg:
            if cfg.has_key(conn_type):
                return cfg.get(conn_type)
        else:
            return None

    @staticmethod
    def showActiveConnections():
        cfg = readDict(settings.grass_config)
        if cfg:
            print('***' * 30)
            print('\n     Primary connection for db drivers\n')
            for key, val in cfg.iteritems():
                print('       conn_type: %s -> conn_id: %s\n' % (key, val))
        else:
            print('      No connection defined\n')
        print('***' * 30)

    def getCurrentConnection(self, conn_type):
        idc = self.getCurrentId(conn_type)
        if id:
            self.setConenction(conn_id=idc, conn_type=conn_type)
            self._connect()
        else:
            self.connection = None

    def getHook(self):
        if self.connection:
            return self.connection.get_hook()
        return None

    @staticmethod
    def removeConnById(id):
        cn = settings.engine.connect()
        print('***' * 30)
        print("\n     Removing connection %s " % id)
        try:
            print('       conn_id= %s \n' % id)
            cn.execute('DELETE FROM connection WHERE conn_id="%s"' % id)
            cn.close()
        except Exception, e:
            print("       ERROR: %s \n" % e)
            # print('     No connection with conn_id %s'%id)
        print('***' * 30)

    def setConnectionURI(self, uri):
        self.uri = uri
        self._connect()

    def testConnection(self, conn_type=None):
        if conn_type is not None:
            self.getCurrentConnection(conn_type)

        hook = self.getHook()
        if hook:
            if not hook.test():
                print('Cannot establish connection')
                return False


                # def HOW_TO+USE():
                #     conn = ConnectionManager()
                #     conn.setConenction(conn_type='hiveserver2',
                #                       conn_id='testhiveconn1',
                #                       host='172.17.0.2',
                #                       port=10000,
                #                       login='root',
                #                       password='test',
                #                       schema='default')
                #     #conn.dropConnectionTable()
                #     conn.showConnections()
                #     #conn.addNewConnection()
                #     conn.testConnection(conn.getCurrentId())
                #     #conn.removeConnById('testhiveconn1')
                #     #print(conn.getCurrentId())


class JSONBuilder:
    def __init__(self, grass_map=None, json_file=None, json_type=None):

        if grass_map is None:
            if json_file is None and json_type is None:
                print("Must be initialized json_file and json_type")
                raise ValueError
            if not json_type in ['ENCLOSED', 'UNENCLOSED']:
                print("json_type must be 'ENCLOSED' or 'UNENCLOSED'")
                raise ValueError

        self.grass_map = grass_map
        self.json_file = json_file
        self.json_type = json_type
        self.json = str()

    def getJSON(self):
        if self.grass_map:
            self.json_type = 'ENCLOSED'
            self.json = self._getGRASSJSON()
        else:
            filename, file_extension = os.path.splitext(self.json_file)
            self.json = os.path.join(getTmpFolder(), "%s_%s.json" % (filename, self.json_type))
        return self.json

    def rm_last_lines(self, path, rm_last_line=3):
        file = open(path, "r+", )

        # Move the pointer (similar to a cursor in a text editor) to the end of the file.
        file.seek(-rm_last_line, os.SEEK_END)

        # This code means the following code skips the very last character in the file -
        # i.e. in the case the last line is null we delete the last line
        # and the penultimate one
        pos = file.tell() - 1

        # Read each character in the file one at a time from the penultimate
        # character going backwards, searching for a newline character
        # If we find a new line, exit the search
        while pos > 0 and file.read(1) != "\n":
            pos -= 1
            file.seek(pos, os.SEEK_SET)

        # So long as we're not at the start of the file, delete all the characters ahead of this position
        if pos > 0:
            file.seek(pos, os.SEEK_SET)
            file.truncate()

        file.close()

    @staticmethod
    def removeLine2(filename, lineNumber):
        with open(filename, 'r+') as outputFile:
            with open(filename, 'r') as inputFile:

                currentLineNumber = 0
                while currentLineNumber < lineNumber:
                    inputFile.readline()
                    currentLineNumber += 1

                seekPosition = inputFile.tell()
                outputFile.seek(seekPosition, 0)

                inputFile.readline()

                currentLine = inputFile.readline()
                while currentLine:
                    outputFile.writelines(currentLine)
                    currentLine = inputFile.readline()

            outputFile.truncate()

    def _getGRASSJSON(self):
        if self.grass_map['type'] not in ['point', 'line', 'boundary', 'centroid', 'area', 'face', 'kernel', 'auto']:
            self.grass_map['type'] = 'auto'
        out = "%s_%s_%s.json" % (self.grass_map['map'],
                                 self.grass_map['layer'],
                                 self.json_type)

        out = os.path.join(getTmpFolder(), out)
        if os.path.exists(out):
            os.remove(out)
        out1 = Module('v.out.ogr',
                      input=self.grass_map['map'],
                      layer=self.grass_map['layer'],
                      type=self.grass_map['type'],
                      output=out,
                      format='GeoJSON',
                      stderr_=PIPE,
                      overwrite=True)
        self.rm_last_lines(out, 3)
        for i in range(5):  # todo optimize
            self.removeLine2(out, 0)

        print(out1.outputs["stderr"].value.strip())
        print("out", out)

        return out


class GRASS2HDFS(object):
    """Base class for transfering data from GRASS to HDFS"""

    def __init__(self, conn_type):
        self.conn = None
        self.hook = None
        self.conn_type = conn_type
        self._initConnection()
        if self.hook is None:
            print("connection is not established")
            sys.exit()  # TODO

    def _initConnection(self):
        self.conn = ConnectionManager()
        self.conn.getCurrentConnection(self.conn_type)
        self.hook = self.conn.getHook()

    def printInfo(self, hdfs):
        print('***' * 30)
        print('\n   path to hdfs:\n    %s\n' % hdfs)
        print('***' * 30)


class GRASS2HDFSweb(GRASS2HDFS):
    def __init__(self):
        self.conn_type = 'webhdfs'
        super(GRASS2HDFSweb, self).__init__(self.conn_type)

    def cp(self, fs, hdfs, overwrite=True, parallelism=1):
        self.mkdir('/user/test1')
        #sys.exit()
        logging.debug('Trying to connect to: \nfs: %s\nhdfs:%s   ' % (hdfs, fs))
        self.hook.load_file(fs, hdfs, overwrite, parallelism)


    def mkdir(self, hdfs):
        self.hook.mkdir(hdfs)
        self.printInfo(hdfs)

    def write(self, hdfs, data, **kwargs):
        """
        Write file to hdfs
        :param hdfs:
        :type hdfs:
        :param data:
        :type data:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        self.hook.write(hdfs, data, **kwargs)
        self.printInfo(hdfs)


class GRASS2HDFSsnakebite(GRASS2HDFS):
    def __init__(self):
        self.conn_type = 'hdfs'
        super(GRASS2HDFSsnakebite, self).__init__(self.conn_type)

    #def cp(self, fs, hdfs, overwrite=True, parallelism=1):
    ##    self.hook.put(fs, hdfs)
    #    self.printInfo(hdfs)


class HDFS2HIVE(object):
    def __init__(self):
        NotImplemented()

    def connect(self):
        NotImplemented

    def add_jars(self, list):
        NotImplemented

    def add_functions(self):
        NotImplemented

    def load_data(self, table, fs=None, hdfs=None):
        NotImplemented

    def drop_table(self, name):
        NotImplemented

    def execute(self, nsql):
        NotImplemented

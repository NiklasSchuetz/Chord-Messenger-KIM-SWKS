"""
Abstract base class for all object storable in our SQL database
Forces database objects to provide insert update and delete
"""

import abc
import sqlite3

class DatabaseObject(abc.ABC):    
    @abc.abstractmethod
    def update(self, con: sqlite3.Connection):
        """ Provides update function for updating existing object in database
        Will fail if object by internalID does not exist"""
    
    @abc.abstractmethod
    def insert(self, con: sqlite3.Connection):
        """ Provides insert function to add new object to database
        Will fail if object by internalID exists """
    
    @abc.abstractmethod
    def delete(self, con: sqlite3.Connection):
        """ Removes object from database. Does not delete python object.
        This means the same python object can be inserted again
        Will fail if object (by internalID does not exist"""
    
    @staticmethod
    def createTable(con: sqlite3.Connection):
        """ Creates table of object in database if table does not exist.
        Does not check if columns change / match """

class DBException(Exception):
    """ Exception class for DB exceptions that are not raised by sqlite3 itself but needs to be raised by our code """
    pass

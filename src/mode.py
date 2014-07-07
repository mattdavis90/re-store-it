import argparse

from abc import ABCMeta, abstractmethod


class Mode(object):
    __metaclass__ = ABCMeta

    def __init__(self, parent, argv):
        self._parser = argparse.ArgumentParser(parents=[parent])
        self._add_arguments()
        
        args = self._parser.parse_args(argv)
        self._initialise(args)

    @abstractmethod
    def _add_arguments(self):
        return

    @abstractmethod
    def _initialise(self):
        return
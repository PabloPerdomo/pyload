# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import io
import os

from future import standard_library
standard_library.install_aliases()

from pyload.utils import convert
from pyload.utils.path import availspace

from ..datatype.init import Permission, StatusInfo
from ..datatype.task import Interaction
from .base import BaseApi
from .init import Api, requireperm


class CoreApi(BaseApi):
    """
    This module provides methods for general interaction with the core, like status or progress retrieval.
    """
    __slots__ = []

    @requireperm(Permission.All)
    def get_server_version(self):
        """
        PyLoad Core version.
        """
        return convert.from_version(self.pyload.version)

    def is_ws_secure(self):
        # needs to use TLS when either requested or webui is also using
        # encryption
        if not self.pyload.config.get('ssl', 'activated'):
            return False

        if not os.path.exists(self.pyload.config.get('ssl', 'cert')) or not os.path.exists(
                self.pyload.config.get('ssl', 'key')):
            self.pyload.log.warning(_('SSL key or certificate not found'))
            return False

        return True

    @requireperm(Permission.All)
    def get_ws_address(self):
        """
        Gets and address for the websocket based on configuration.
        """
        if self.is_ws_secure():
            ws = "wss"
        else:
            ws = "ws"

        return "{0}://{{0}}:{1:d}".format(ws,
                                        self.pyload.config.get('rpc', 'port'))

    @requireperm(Permission.All)
    def get_status_info(self):
        """
        Some general information about the current status of pyLoad.

        :return: `StatusInfo`
        """
        queue = self.pyload.files.get_queue_stats(self.primary_uid)
        total = self.pyload.files.get_download_stats(self.primary_uid)

        server_status = StatusInfo(0,
                                   total[0], queue[0],
                                   total[1], queue[1],
                                   self.is_interaction_waiting(
                                       Interaction.All),
                                   not self.pyload.dlm.pause,  #: and self.is_time_download(),
                                   self.pyload.dlm.pause,
                                   # and self.is_time_reconnect(),
                                   self.pyload.config.get(
                                       'reconnect', 'activated'),
                                   self.get_quota())

        for pyfile in self.pyload.dlm.active_downloads(self.primary_uid):
            server_status.speed += pyfile.get_speed()  #: bytes/s

        return server_status

    @requireperm(Permission.All)
    def get_progress_info(self):
        """
        Status of all currently running tasks

        :rtype: list of :class:`ProgressInfo`
        """
        return (self.pyload.dlm.get_progress_list(self.primary_uid) +
                self.pyload.thm.get_progress_list(self.primary_uid))

    def pause_server(self):
        """
        Pause server: It won't start any new downloads, but nothing gets aborted.
        """
        self.pyload.dlm.pause = True

    def unpause_server(self):
        """
        Unpause server: New Downloads will be started.
        """
        self.pyload.dlm.pause = False

    def toggle_pause(self):
        """
        Toggle pause state.

        :return: new pause state
        """
        self.pyload.dlm.pause ^= True
        return self.pyload.dlm.pause

    def toggle_reconnect(self):
        """
        Toggle reconnect activation.

        :return: new reconnect state
        """
        self.pyload.config['reconnect']['activated'] ^= True
        return self.pyload.config.get('reconnect', 'activated')

    def avail_space(self):
        """
        Available free space at download directory in bytes.
        """
        return availspace(self.pyload.config.get('general', 'storage_folder'))

    def shutdown(self):
        """
        Clean way to quit pyLoad.
        """
        self.pyload._shutdown = True

    def restart(self):
        """
        Restart pyload core.
        """
        self.pyload._restart = True

    # def stop(self):
        # """
        # Stop pyload core.
        # """
        # self.pyload._stop = True

    def get_log(self, offset=0):
        """
        Returns most recent log entries.

        :param offset: line offset
        :return: List of log entries
        """
        filename = os.path.join(self.pyload.config.get(
            'log', 'logfile_folder'), 'log.txt')
        try:
            with io.open(filename) as fp:
                lines = fp.readlines()
            if offset >= len(lines):
                return []
            return lines[offset:]
        except Exception:
            return ['No log available']

    # @requireperm(Permission.All)
    # def is_time_download(self):
        # """
        # Checks if pyload will start new downloads according to time in
        # config.

        # :return: bool
        # """
        # start = self.pyload.config.get('connection', 'start').split(":")
        # end = self.pyload.config.get('connection', 'end').split(":")
        # return compare_time(start, end)

    # @requireperm(Permission.All)
    # def is_time_reconnect(self):
        # """
        # Checks if pyload will try to make a reconnect

        # :return: bool
        # """
        # start = self.pyload.config.get('reconnect', 'start').split(":")
        # end = self.pyload.config.get('reconnect', 'end').split(":")
        # return compare_time(start, end) and
        # self.pyload.config.get('reconnect', 'activated')

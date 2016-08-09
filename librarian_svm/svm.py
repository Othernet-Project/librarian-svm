"""
Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import functools
import glob
import logging
import os
import re
import shutil
import subprocess

from hwd.storage import mounts
from pkg_resources import parse_version

from librarian.core.exts import ext_container as exts


MOUNT = '/bin/mount'
SYNC = '/bin/sync'
READ_ONLY = 'ro'
READ_WRITE = 'rw'


class IndeterminableMountMode(RuntimeError):
    """
    Raised when the mount mode cannot be determined.
    """
    pass


class InvalidFilename(ValueError):
    """
    Raised when an overlay filename is not in the right format.
    """
    pass


class InstallError(RuntimeError):
    """
    Raised when overlay installation fails.
    """


def get_mount_mode(path):
    """
    Return under which mode is ``path`` currently mounted.
    """
    for mnt in mounts():
        if mnt.mdir == path:
            options = mnt.opts.split(',')
            if READ_WRITE in options:
                return READ_WRITE
            if READ_ONLY in options:
                return READ_ONLY
    raise IndeterminableMountMode(path)


def remount(path, mode):
    """
    Remount ``path`` under the passed in ``mode``.

    On success it returns ``True``, otherwise ``False``.
    """
    cmd = [MOUNT, '-o', 'remount', mode, path]
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        logging.exception(u"SVM: '%s' remount failed.", path)
        return False
    else:
        return True


def sync():
    """
    Write any data buffered in memory out to disk.
    """
    try:
        subprocess.check_call(SYNC)
    except subprocess.CalledProcessError:
        logging.exception("SVM: sync operation failed.")
        return False
    else:
        return True


class Overlay(object):
    """
    Represents a single overlay, so they can be easily compared, by name and
    version.
    """
    #: Boot directory path
    BOOT = '/boot'
    #: Glob pattern used to find overlays installed in ``BOOT``
    GLOB = '/boot/overlay-*.sqfs'
    #: Regex pattern to capture significant portions of an overlay filename
    REGEX = re.compile('^overlay-([A-Za-z0-9]+)-([0-9][\.0-9a-z]+)\.sqfs$')
    #: Extension to temporarily append to overlays while being installed
    NEW_EXT = '.new'
    #: Extension to temporarily append to old overlays that are being replaced
    #: with a new one
    BACKUP_EXT = '.backup'
    #: Exception aliases
    InvalidFilename = InvalidFilename
    InstallError = InstallError

    def __init__(self, path):
        self.path = path
        self.filename = os.path.basename(self.path)
        (self.name, self.version) = self._parse_filename()

    def _parse_filename(self):
        """
        Return the name and parsed version of the overlay filename.
        """
        match = self.REGEX.match(self.filename)
        if not match:
            raise self.InvalidFilename(self.path)

        (name, version) = match.groups()
        return (name, parse_version(version))

    def __eq__(self, other):
        """
        Defines whether two overlay objects are equal.
        """
        return self.name == other.name and self.version == other.version

    def __ne__(self, other):
        """
        Defines whether two overlay objects are not equal.
        """
        return not (self == other)

    def __lt__(self, other):
        """
        Determine whether this overlay has the same name as ``other``, only
        it's version number is less than ``other``'s or not.
        """
        return self.name == other.name and self.version < other.version

    def __gt__(self, other):
        """
        Determine whether this overlay has the same name as ``other``, only
        it's version number is greater than ``other``'s or not.
        """
        return self.name == other.name and self.version > other.version

    @property
    def is_installed(self):
        """
        Return whether this overlay is installed under :py:attr:`~Overlay.BOOT`
        or not.
        """
        return self.path.startswith(self.BOOT)

    @classmethod
    def installed(cls):
        """
        Yield instances of installed overlays found in :py:attr:`~Overlay.BOOT`
        """
        return (cls(path) for path in glob.iglob(cls.GLOB))

    @classmethod
    def stashed(cls):
        """
        Yield instances of available overlays found in 'svm.stashdir'.
        """
        stashdir = exts.config['svm.stashdir']
        return (cls(path) for path in glob.iglob(stashdir))

    def find_installed_relative(self):
        """
        Find and return an overlay that is equally named as this instance,
        (ignoring version differences), and is installed under
        :py:attr:`~Overlay.BOOT`.
        """
        for overlay in self.installed():
            if overlay.name == self.name:
                return overlay

    def install_wrapper(fn):
        """
        Prepare destination for installation, remounting it in read-write mode,
        and returning it to the original mount mode that it was found in after
        installation is done.
        """
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            try:
                mode = get_mount_mode(self.BOOT)
            except IndeterminableMountMode:
                logging.error("Unable to determine mount mode of `/boot`")
                raise InstallError("Unable to determine mount mode of `/boot`")
            # remount /boot in read-write mode if it's not already in it
            if mode != READ_WRITE and not remount(self.BOOT, READ_WRITE):
                logging.error("Cannot remount `/boot` in read-write mode")
                raise InstallError("Cannot remount `/boot` in read-write mode")
            # remount succeeded, now perform installation
            try:
                return fn(self, *args, **kwargs)
            except Exception as exc:
                logging.exception("Installation failed.")
                raise InstallError("Installation failed: " + str(exc))
            finally:
                # remounting in ``READ_ONLY`` mode if that's what it was found
                # in originally, regardless of the result of the installation
                if mode == READ_ONLY:
                    remount(self.BOOT, READ_ONLY)
        return wrapper

    @install_wrapper
    def _install(self):
        """
        Perform the actual installation.
        """
        destpath = os.path.join(self.BOOT, self.filename)
        # check if this overlay has another version of it installed already
        existing = self.find_installed_relative()
        if existing:
            # there is another version of this overlay installed, perform safe
            # replacement of the other version with this one
            safedestpath = destpath + self.NEW_EXT
            shutil.copy2(self.path, safedestpath)
            shutil.move(existing.path, existing.path + self.BACKUP_EXT)
            shutil.move(safedestpath, destpath)
        else:
            # no other version of this overlay is installed, do a simple copy
            shutil.copy2(self.path, destpath)
        # make sure copy operation is finished
        sync()

    def install(self):
        """
        Install this overlay into :py:attr:`~Overlay.BOOT`.

        Raises :py:exc:`InstallError` on failure.
        """
        # proceed only if it's not already installed
        if not self.is_installed:
            return self._install()

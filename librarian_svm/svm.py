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


class OperationalError(RuntimeError):
    """
    Raised when overlay write operation fails.
    """
    pass


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
    options = 'remount,{mode}'.format(mode=mode)
    cmd = [MOUNT, '-o', options, mode, path]
    try:
        subprocess.check_call(cmd)
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
    #: Glob pattern used to find overlays located in ``BOOT``
    GLOB = 'overlay-*.sqfs'
    #: Regex pattern to capture significant portions of an overlay filename
    REGEX = re.compile(r'^overlay-([A-Za-z0-9]+)-([0-9][\.0-9a-z]+)\.sqfs$')
    #: Extension to temporarily append to overlays while being enabled
    NEW_EXT = '.new'
    #: Extension to temporarily append to old overlays that are being replaced
    #: with a new one
    BACKUP_EXT = '.backup'
    #: Exception aliases
    InvalidFilename = InvalidFilename
    OperationalError = OperationalError

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
        if not other or not isinstance(other, Overlay):
            # guard against `None` or non-overlay types
            return False
        # safe to assume that ``other`` is an instance of ``Overlay``
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
        if not other or not isinstance(other, Overlay):
            # guard against `None` or non-overlay types
            return False
        # safe to assume that ``other`` is an instance of ``Overlay``
        return self.name == other.name and self.version < other.version

    def __gt__(self, other):
        """
        Determine whether this overlay has the same name as ``other``, only
        it's version number is greater than ``other``'s or not.
        """
        if not other or not isinstance(other, Overlay):
            # guard against `None` or non-overlay types
            return False
        # safe to assume that ``other`` is an instance of ``Overlay``
        return self.name == other.name and self.version > other.version

    def __str__(self):
        """
        Return human readable string representation of overlay object.
        """
        return self.path

    def __repr__(self):
        """
        Return string representation of overlay object.
        """
        return u"<Overlay: '{path}'>".format(path=self.path)

    @property
    def is_enabled(self):
        """
        Return whether this overlay is located under :py:attr:`~Overlay.BOOT`
        or not.
        """
        if self.path.startswith(self.BOOT):
            return True
        # it's possible this overlay is in stash, but it has a copy in /boot
        relative = self.find_enabled_relative()
        return relative == self

    @classmethod
    def enabled(cls):
        """
        Yield instances of enabled overlays found in :py:attr:`~Overlay.BOOT`
        """
        pattern = os.path.join(cls.BOOT, cls.GLOB)
        return (cls(path) for path in glob.iglob(pattern))

    @classmethod
    def stashed(cls):
        """
        Yield instances of available overlays found in 'svm.stashdir'.
        """
        pattern = os.path.join(exts.config['svm.stashdir'], cls.GLOB)
        return (cls(path) for path in glob.iglob(pattern))

    @classmethod
    def manifest(cls):
        """
        Return a unified view of all enabled and stashed overlays.
        """
        enabled = cls.enabled()
        stashed = cls.stashed()
        # prepare a dict of overlay name: list of overlay instances mapping
        manifest = dict((overlay.name, {'versions': [overlay],
                                        'enabled': overlay.version})
                        for overlay in enabled)
        # update manifest with other available overlays, extending the list
        # of overlays in case of matching names
        for overlay in stashed:
            family = manifest.get(overlay.name, {'versions': [],
                                                 'enabled': None})
            if overlay not in family['versions']:
                family['versions'].append(overlay)
                family['versions'].sort()
            manifest[overlay.name] = family
        return manifest

    def find_enabled_relative(self):
        """
        Find and return an overlay that is equally named as this instance,
        (ignoring version differences), and is located under
        :py:attr:`~Overlay.BOOT`.
        """
        for overlay in self.enabled():
            if overlay.name == self.name:
                return overlay

    def remount_boot(fn):
        """
        Prepare destination for write operation, remounting it in read-write
        mode and returning it to the original mount mode that it was found in
        after the operation is finished.
        """
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            try:
                mode = get_mount_mode(self.BOOT)
            except IndeterminableMountMode:
                msg = "Unable to determine mount mode of `/boot`"
                logging.error(msg)
                raise OperationalError(msg)
            # remount /boot in read-write mode if it's not already in it
            if mode != READ_WRITE and not remount(self.BOOT, READ_WRITE):
                msg = "Cannot remount `/boot` in read-write mode"
                logging.error(msg)
                raise OperationalError(msg)
            # remount succeeded, now perform write operation
            try:
                return fn(self, *args, **kwargs)
            except Exception as exc:
                logging.exception("Operation failed.")
                raise OperationalError("Operation failed: " + str(exc))
            finally:
                # remounting in ``READ_ONLY`` mode if that's what it was found
                # in originally, regardless of the result of the operation
                if mode == READ_ONLY:
                    remount(self.BOOT, READ_ONLY)
        return wrapper

    @remount_boot
    def _enable(self):
        """
        Perform the actual enabling.
        """
        destpath = os.path.join(self.BOOT, self.filename)
        # check if this overlay has another version of it enabled already
        existing = self.find_enabled_relative()
        if existing:
            # there is another version of this overlay enabled, perform safe
            # replacement of the other version with this one
            safedestpath = destpath + self.NEW_EXT
            shutil.copy2(self.path, safedestpath)
            shutil.move(existing.path, existing.path + self.BACKUP_EXT)
            shutil.move(safedestpath, destpath)
        else:
            # no other version of this overlay is enabled, do a simple copy
            shutil.copy2(self.path, destpath)
        # make sure copy operation is finished
        sync()

    def enable(self):
        """
        Enable this overlay by moving it from 'svm.stashdir' into
        :py:attr:`~Overlay.BOOT`.

        Raises :py:exc:`OperationalError` on failure.
        """
        # proceed only if it's not already enabled
        if not self.is_enabled:
            return self._enable()

    @remount_boot
    def _disable(self):
        """
        Perform the actual disabling.
        """
        stashdir = exts.config['svm.stashdir']
        if not os.path.exists(stashdir):
            os.makedirs(stashdir)
        # move overlay image from boot into stashdir
        src = os.path.join(self.BOOT, self.filename)
        dest = os.path.join(stashdir, self.filename)
        shutil.move(src, dest)
        # make sure the write operation is finished
        sync()

    def disable(self):
        """
        Disable overlay by moving it from :py:attr:`~Overlay.BOOT` back to
        'svm.stashdir'.

        Raises :py:exc:`OperationalError` on failure.
        """
        # proceed only if it's really enabled
        if self.is_enabled:
            return self._disable()

    def remove(self):
        """
        Remove overlay image from 'svm.stashdir' and also disable it if it was
        enabled.
        """
        self.disable()
        # remove from stash if it exists
        stashpath = os.path.join(exts.config['svm.stashdir'], self.filename)
        if os.path.exists(stashpath):
            os.remove(stashpath)

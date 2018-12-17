# ovirt-imageio
# Copyright (C) 2018 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import absolute_import

import logging
import os
import subprocess

from contextlib import contextmanager

from . import testutil

log = logging.getLogger("qemu")


def env():
    """
    Amend PATH to locate qemu-kvm on platforms that hide it in /usr/libexec
    (e.g RHEL).
    """
    env = dict(os.environ)
    env["PATH"] = ":".join((env["PATH"], "/usr/libexec"))
    return env


@contextmanager
def run(image, fmt, qmp_sock, start_cpu=True):
    # NOTES:
    # - Let qemu pick default memory size, since on some platforms memory have
    #   strange alignment. Here is a failure from ppc64le host:
    #       qemu-kvm: Memory size 0x1000000 is not aligned to 256 MiB
    cmd = [
        "qemu-kvm",
        "-drive", "file={},format={}".format(image, fmt),
        "-nographic",
        "-qmp", "unix:{},server,nowait".format(qmp_sock),
    ]

    if not start_cpu:
        cmd.append("-S")

    log.debug("Starting qemu %s", cmd)
    p = subprocess.Popen(cmd, env=env())
    try:
        if not testutil.wait_for_path(qmp_sock, 1):
            raise RuntimeError("Timeout waiting for socket: %s" % qmp_sock)
        yield p
    finally:
        log.debug("Terminating qemu")
        p.terminate()
        p.wait()
        log.debug("qemu terminated with exit code %s", p.returncode)

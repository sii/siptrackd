#!/usr/bin/env python

from distutils.core import setup

setup(name = 'siptrackd',
        version = '1.0.8',
        description = 'Siptrack IP/Device Manager Server',
        author = 'Simon Ekstrand',
        author_email = 'simon@theoak.se',
        url = 'http://siptrack.theoak.se/',
        license = 'BSD',
        packages = ['siptrackdlib', 'siptrackdlib.network', 'siptrackdlib.external',
            'siptrackdlib.storage', 'siptrackdlib.storage.stsqlite',
            'siptrackd_twisted'],
        scripts = ['siptrackd']
        )


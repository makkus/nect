# -*- coding: utf-8 -*-

from nect import Nect
import os
import stat

executable = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH

def default_paths():
    return [p for p in os.environ["PATH"].split(":") if os.path.isdir(p)]

def is_executable(file):
    if not os.path.exists(file):
        return False

    st = os.stat(file)
    mode = st.st_mode
    if mode & executable:
        return True
    else:
        return False


class Executables(Nect):

    def __init__(self, paths=None):

        super().__init__()
        if not paths:
            self.paths = default_paths()
        else:
            self.paths = paths


    def get_executables_map(self):

        executables = {}
        for p in self.paths:

            if 'sbin' in p:
                sudo = True
            else:
                sudo = False

            for e in os.listdir(p):
                if not executables.get(e, None) and is_executable(os.path.join(p, e)):
                    executables[e] = {'dir': p, 'exe': e, 'sudo': sudo}

        return executables

    def nect(self):

        executables = []
        for p in self.paths:

            if 'sbin' in p:
                sudo = True
            else:
                sudo = False

            for e in os.listdir(p):
                if is_executable(os.path.join(p, e)):
                    executables.append({'dir': p, 'exe': e, 'sudo': sudo})

        return executables


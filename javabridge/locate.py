"""locate.py - determine architecture and find Java

python-javabridge is licensed under the BSD license.  See the
accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2013 Broad Institute
All rights reserved.lo

"""

import ctypes
import os
import sys
import logging
import subprocess
import re

# Note: if a matching gcc is available from the shell on Windows, its
#       probably safe to assume the user is in an MINGW or MSYS or Cygwin
#       environment, in which case he/she wants to compile with gcc for
#       Windows, in which case the correct compiler flags will be triggered
#       by is_mingw. This method is not great, improve it if you know a
#       better way to discriminate between compilers on Windows.
def is_mingw():
    # currently this check detects mingw only on Windows. Extend for other
    # platforms if required:
    if (os.name != "nt"):
        return False

    # if the user defines DISTUTILS_USE_SDK or MSSdk, we expect they want
    # to use Microsoft's compiler (as described here:
    # https://github.com/cython/cython/wiki/CythonExtensionsOnWindows):
    if (os.getenv("DISTUTILS_USE_SDK") != None or os.getenv("MSSdk") != None):
        return False

    mingw32 = ""
    mingw64 = ""
    if (os.getenv("MINGW32_PREFIX")):
        mingw32 = os.getenv("MINGW32_PREFIX")
    if (os.getenv("MINGW64_PREFIX")):
        mingw64 = os.getenv("MINGW64_PREFIX")

    # if any invocation of gcc works, then we assume the user wants mingw:
    test = "gcc --version > NUL 2>&1"
    if (os.system(test) == 0 or os.system(mingw32+test) == 0 or os.system(mingw64+test) == 0):
        return True

    return False



is_linux = sys.platform.startswith('linux')
is_mac = sys.platform == 'darwin'
is_win = sys.platform.startswith("win")
is_win64 = (is_win and (os.environ["PROCESSOR_ARCHITECTURE"] == "AMD64"))
is_msvc = (is_win and
           ((sys.version_info.major == 2 and sys.version_info.minor >= 6) or
            (sys.version_info.major == 3)))
is_mingw = is_mingw()

if is_win:
    if sys.version_info.major == 2:
        import _winreg as winreg
        from exceptions import WindowsError
    else:
        import winreg

logger = logging.getLogger(__name__)

def find_javahome():
    """Find JAVA_HOME if it doesn't exist"""
    if 'JAVA_HOME' in os.environ:
        return os.environ['JAVA_HOME']
    else:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from download_java import download_java
        jre_path = download_java()
        return jre_path

def find_jdk():
    """Find the JDK under Windows"""
    if 'JDK_HOME' in os.environ:
        return os.environ['JDK_HOME']
    if is_linux:
        jdk_home = find_javahome()
        if jdk_home.endswith("jre") or jdk_home.endswith("jre/"):
            jdk_home = jdk_home[:jdk_home.rfind("jre")]
        return jdk_home
    if is_mac:
        return find_javahome()
    if is_win:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from download_java import download_jdk
        jdk_path = download_jdk()
        return jdk_path

def find_javac_cmd():
    """Find the javac executable"""
    if is_win:
        jdk_base = find_jdk()
        javac = os.path.join(jdk_base, "bin", "javac.exe")
        if os.path.isfile(javac):
            return javac
        raise RuntimeError("Failed to find javac.exe in its usual location under the JDK (%s)" % javac)
    else:
        # will be along path for other platforms
        return "javac"

def find_jar_cmd():
    """Find the javac executable"""
    if is_win:
        jdk_base = find_jdk()
        javac = os.path.join(jdk_base, "bin", "jar.exe")
        if os.path.isfile(javac):
            return javac
        raise RuntimeError("Failed to find jar.exe in its usual location under the JDK (%s)" % javac)
    else:
        # will be along path for other platforms
        return "jar"


def find_jre_bin_jdk_so():
    """Finds the jre bin dir and the jdk shared library file"""
    jvm_dir = None
    java_home = find_javahome()
    if java_home is not None:
        found_jvm = False
        for jre_home in (java_home, os.path.join(java_home, "jre"), os.path.join(java_home, 'default-java'), os.path.join(java_home, 'default-runtime')):
            jre_bin = os.path.join(jre_home, 'bin')
            jre_libexec = os.path.join(jre_home, 'bin' if is_win else 'lib')
            arches = ('amd64', 'i386', '') if is_linux else ('',)
            lib_prefix = '' if is_win else 'lib'
            lib_suffix = '.dll' if is_win else ('.dylib' if is_mac else '.so')
            for arch in arches:
                for place_to_look in ('client','server'):
                    jvm_dir = os.path.join(jre_libexec, arch, place_to_look)
                    jvm_so = os.path.join(jvm_dir, lib_prefix + "jvm" + lib_suffix)
                    if os.path.isfile(jvm_so):
                        return (jre_bin, jvm_so)
    return (jre_bin, None)

if __name__ == '__main__':
    jdk_path = find_jdk()
    jre_path = find_javahome()

    print(jdk_path)
    print(jre_path)

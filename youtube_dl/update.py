import json
import traceback
import hashlib
from zipimport import zipimporter

from .utils import *
from .version import __version__

def rsa_verify(message, signature, key):
    from struct import pack
    from hashlib import sha256
    from sys import version_info
    def b(x):
        if version_info[0] == 2: return x
        else: return x.encode('latin1')
    assert(type(message) == type(b('')))
    block_size = 0
    n = key[0]
    while n:
        block_size += 1
        n >>= 8
    signature = pow(int(signature, 16), key[1], key[0])
    raw_bytes = []
    while signature:
        raw_bytes.insert(0, pack("B", signature & 0xFF))
        signature >>= 8
    signature = (block_size - len(raw_bytes)) * b('\x00') + b('').join(raw_bytes)
    if signature[0:2] != b('\x00\x01'): return False
    signature = signature[2:]
    if not b('\x00') in signature: return False
    signature = signature[signature.index(b('\x00'))+1:]
    if not signature.startswith(b('\x30\x31\x30\x0D\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20')): return False
    signature = signature[19:]
    if signature != sha256(message).digest(): return False
    return True

def update_self(to_screen, verbose, filename):
    """Update the program file with the latest version from the repository"""

    UPDATE_URL = "http://rg3.github.com/youtube-dl/update/"
    VERSION_URL = UPDATE_URL + 'LATEST_VERSION'
    JSON_URL = UPDATE_URL + 'versions.json'
    UPDATES_RSA_KEY = (0x9d60ee4d8f805312fdb15a62f87b95bd66177b91df176765d13514a0f1754bcd2057295c5b6f1d35daa6742c3ffc9a82d3e118861c207995a8031e151d863c9927e304576bc80692bc8e094896fcf11b66f3e29e04e3a71e9a11558558acea1840aec37fc396fb6b65dc81a1c4144e03bd1c011de62e3f1357b327d08426fe93, 65537)


    if not isinstance(globals().get('__loader__'), zipimporter) and not hasattr(sys, "frozen"):
        to_screen(u'It looks like you installed youtube-dl with pip, setup.py or a tarball. Please use that to update.')
        return

    # Check if there is a new version
    try:
        newversion = compat_urllib_request.urlopen(VERSION_URL).read().decode('utf-8').strip()
    except:
        if verbose: to_screen(compat_str(traceback.format_exc()))
        to_screen(u'ERROR: can\'t find the current version. Please try again later.')
        return
    if newversion == __version__:
        to_screen(u'youtube-dl is up-to-date (' + __version__ + ')')
        return

    # Download and check versions info
    try:
        versions_info = compat_urllib_request.urlopen(JSON_URL).read().decode('utf-8')
        versions_info = json.loads(versions_info)
    except:
        if verbose: to_screen(compat_str(traceback.format_exc()))
        to_screen(u'ERROR: can\'t obtain versions info. Please try again later.')
        return
    if not 'signature' in versions_info:
        to_screen(u'ERROR: the versions file is not signed or corrupted. Aborting.')
        return
    signature = versions_info['signature']
    del versions_info['signature']
    if not rsa_verify(json.dumps(versions_info, sort_keys=True).encode('utf-8'), signature, UPDATES_RSA_KEY):
        to_screen(u'ERROR: the versions file signature is invalid. Aborting.')
        return

    to_screen(u'Updating to version ' + versions_info['latest'] + '...')
    version = versions_info['versions'][versions_info['latest']]

    print_notes(versions_info['versions'])

    if not os.access(filename, os.W_OK):
        to_screen(u'ERROR: no write permissions on %s' % filename)
        return

    # Py2EXE
    if hasattr(sys, "frozen"):
        exe = os.path.abspath(filename)
        directory = os.path.dirname(exe)
        if not os.access(directory, os.W_OK):
            to_screen(u'ERROR: no write permissions on %s' % directory)
            return

        try:
            urlh = compat_urllib_request.urlopen(version['exe'][0])
            newcontent = urlh.read()
            urlh.close()
        except (IOError, OSError) as err:
            if verbose: to_screen(compat_str(traceback.format_exc()))
            to_screen(u'ERROR: unable to download latest version')
            return

        newcontent_hash = hashlib.sha256(newcontent).hexdigest()
        if newcontent_hash != version['exe'][1]:
            to_screen(u'ERROR: the downloaded file hash does not match. Aborting.')
            return

        try:
            with open(exe + '.new', 'wb') as outf:
                outf.write(newcontent)
        except (IOError, OSError) as err:
            if verbose: to_screen(compat_str(traceback.format_exc()))
            to_screen(u'ERROR: unable to write the new version')
            return

        try:
            bat = os.path.join(directory, 'youtube-dl-updater.bat')
            b = open(bat, 'w')
            b.write("""
echo Updating youtube-dl...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "%s.new" "%s"
del "%s"
            \n""" %(exe, exe, bat))
            b.close()

            os.startfile(bat)
        except (IOError, OSError) as err:
            if verbose: to_screen(compat_str(traceback.format_exc()))
            to_screen(u'ERROR: unable to overwrite current version')
            return

    # Zip unix package
    elif isinstance(globals().get('__loader__'), zipimporter):
        try:
            urlh = compat_urllib_request.urlopen(version['bin'][0])
            newcontent = urlh.read()
            urlh.close()
        except (IOError, OSError) as err:
            if verbose: to_screen(compat_str(traceback.format_exc()))
            to_screen(u'ERROR: unable to download latest version')
            return

        newcontent_hash = hashlib.sha256(newcontent).hexdigest()
        if newcontent_hash != version['bin'][1]:
            to_screen(u'ERROR: the downloaded file hash does not match. Aborting.')
            return

        try:
            with open(filename, 'wb') as outf:
                outf.write(newcontent)
        except (IOError, OSError) as err:
            if verbose: to_screen(compat_str(traceback.format_exc()))
            to_screen(u'ERROR: unable to overwrite current version')
            return

    to_screen(u'Updated youtube-dl. Restart youtube-dl to use the new version.')

def print_notes(versions, fromVersion=__version__):
    notes = []
    for v,vdata in sorted(versions.items()):
        if v > fromVersion:
            notes.extend(vdata.get('notes', []))
    if notes:
        to_screen(u'PLEASE NOTE:')
        for note in notes:
            to_screen(note)

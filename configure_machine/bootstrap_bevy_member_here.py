#!/usr/bin/env python3
# encoding: utf-8-
"""
A utility program to install a SaltStack minion, and optionally, a master with cloud controller.

arguments:  add one or more file_roots and pillar_roots entries.  "[]" are optional, spaces not permitted.
  --add-roots=[path/to/directory1,path/to/directory2]
      where each directory is expected to have a ./salt and ./pillar subdirectory
      If you use a definition like:  --add-roots=[/full/path/to/directory1/local_salt=../directory1/local_salt]
      These entries will be mapped as Vagrant shared directories,

Maintenance command-line switches:
  --no-sudo = Do not attempt to run with elevated privileges, use the present level
  --no-read-settings = Do not read an existing BEVY_SETTINGS_FILE
"""
import subprocess, os, getpass, socket, platform, ipaddress, sys, time, shutil, tempfile, traceback
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.request import urlopen

try:
    import yaml  # actually imports the PyYAML module
    import ifaddr
    if platform.system() != 'Linux':
        import passlib
except ImportError:
    print('\nERROR: Python3 setup incomplete. You are missing required prerequisite modules.')
    if platform.system() == 'Windows':
        print('Try something like: "py -3 -m pip install pyyaml ifaddr passlib"')
        print('If "pip" is not found, you may need to exit and re-open your console window.')
    elif platform.system() == 'Darwin':  # MacOS
        print('Try something like: "sudo -H pip3 install pyyaml ifaddr passlib"')
    else:  # Linux
        print('Try something like: "sudo -H pip3 install pyyaml ifaddr"')
        print('If you are using Ubuntu (Debian, etc), you may need to "sudo apt install python3-pip" first.')
    print('Then re-run your command.')
    sys.exit(10)  # Windows ERROR_BAD_ENVIRONMENT

# import my helper modules
#noinspection PyUnresolvedReferences
from helpers import pwd_hash, sudo, salt_call_local, provisioner

# # # # #
# This program attempts to establish a DRY single source of truth as the file
SRV_ROOT = '/srv' if platform.system()!='Darwin' else '/opt/saltdata'  # MacOS 10.15+ prohibits use of /srv
BEVY_SETTINGS_FILE_NAME = SRV_ROOT + '/pillar/01_bevy_settings.sls'  # the default Salt location
VAGRANT_PROJECTS_ROOT = '/projects'
temp_settings_name = os.path.join(tempfile.gettempdir(), 'salt-bevy_my_settings.conf')
#
# Normal minions will receive their settings from the Bevy Master.
# If the Bevy Master is a stand-alone server, it might be a "good idea" to connect its /srv directory to
# the /srv directory on your Workstation using a deployment engine such as PyCharm's.
#
# .. A given machine in the Bevy could be a Workstation, a bevy_master (perhaps as a local VM on a workstation),
# or a bevy minion which is a headless server for some service (perhaps also as a local VM).
# Any of these (except a local VM) might very possibly already have been a minion of some other Salt Master
# before our bevy arrives on the scene. We may want to preserve that minion's connection.
# We will attempt to detect that situation, and we will use the setting "additional_minion_tag" (which may contain
# "" or a string literal "2") to allow both minions to operate side-by-side.
#  It theoretically might work to have "additional_minion_tag" be any of the values "3" through "Z",
#   if we were running three or more minions, but that situation would be really weird.
# # # # #
MY_SETTINGS_FILE_NAME = '/etc/salt-bevy/my_settings.conf'  # settings specific to the currant machine
MINIMUM_SALT_VERSION = "2018.3.0"  # ... as a string... the month will be converted to an integer below
SALT_BOOTSTRAP_URL = "http://bootstrap.saltstack.com/stable/bootstrap-salt.sh"
SALT_DOWNLOAD_SOURCE = "stable"

SALT_SRV_ROOT = SRV_ROOT + '/salt'
SALT_PILLAR_ROOT = SRV_ROOT + '/pillar'
# the path to write the bootstrap Salt Minion configuration file
GUEST_MASTER_CONFIG_FILE = SRV_ROOT + '/bevymaster_config/minion'
GUEST_MINION_CONFIG_FILE = SRV_ROOT + '/guest_config/minion'
WINDOWS_GUEST_CONFIG_FILE = SRV_ROOT + '/windows_config/minion'
MAC_GUEST_CONFIG_FILE = SRV_ROOT + '/macos_config/minion'

DEFAULT_VAGRANT_PREFIX = '172.17'  # first two bytes of Vagrant private network
DEFAULT_VAGRANT_NETWORK = '172.17.0.0/16'  #  Vagrant private network

minimum_salt_version = MINIMUM_SALT_VERSION.split('.')
# noinspection PyTypeChecker
minimum_salt_version[1] = int(minimum_salt_version[1])  # use numeric compare of month field
this_file = Path(__file__).resolve()  # the absolute path name of this program's source
user_ssh_key_file_directory = this_file.parent.parent / 'bevy_srv/salt/ssh_keys'

argv = [s.strip() for s in sys.argv]
if '--help' in argv:
    print(__doc__)
    exit()

settings = {}  # global variable
my_settings = {}
user_name = ''


def minion_tag():
    '''
    tests settings['additional_minion_tag']
    returns "" for the primary minion (tag is blank or "none")
      or "2" for a second minion running on the same machine,
      possibly some other value "3"? if three minions were running, but who would do that?
    :return: '' or '2'
    '''
    amt = my_settings.get('additional_minion_tag', '')
    if amt.lower() == 'none':
        return ''
    return amt


def my_salt_config_file_path():
    if platform.system() == 'Windows':  # TODO: minion_tag not yet actually supported
        return Path('c:\\salt\\conf{}\\minion.d\\00_bevy_boot.conf'.format(minion_tag()))
    # else:
    return Path('/etc/salt{}/minion.d/00_bevy_boot.conf'.format(minion_tag()))


def write_my_config_file():
    conf_file_path = my_salt_config_file_path()
    for other_file in conf_file_path.parent.glob('[0-9][0-9]*.conf'):
        print('xxx other_file->', other_file)
        other_file.unlink()  # delete other (competing) configuration files.
    write_config_file(conf_file_path,
                      is_master=my_settings.get('master', False),
                      virtual=False,  # NOTE: may be a true lie if interactive on a virtual machine.
                      platform=platform.system(),
                      master_host=my_settings.get('master_host', False))


def set_file_owned_by(filename, username):
    if sys.platform != 'win32':  # not on Windows
        if sudo.isUserAdmin():   # must have elevated privileges
            try:
                shutil.chown(str(filename), username, 'staff')
                shutil.chown(str(filename.parent), username, 'staff')
            except (OSError, AttributeError):
                pass


def print_names_of_other_bevy_files():
    # scan for other stored bevy definitions in the settings directory (i.e. /srv/pillar/01_bevy_settings.sls.*)
    bsf = Path(BEVY_SETTINGS_FILE_NAME)
    found_bevys = [bsfx.suffix[1:] for bsfx in bsf.parent.glob('*') if bsfx.stem == bsf.name]
    if found_bevys:
        print('I found the following saved bevys in your {} directory:\n  {}'.format(
            Path(BEVY_SETTINGS_FILE_NAME).parent, found_bevys))


def read_bevy_settings_files(context=None, try_temp=False) -> (str, bool):  # (new_bevy_name, changed)
    """
    This procedure is a complex mess.

    It retrieves remembered state for the bevy from disk storage.
    There are two files, one for the bevy in general, stored in a pillar file (in YAML format),
      and one for only this computer, stored in /etc, in a .conf file, in YAML format.
    In addition, there may be any number of other remembered bevys, with each pair of settings files
      stored in the same directory, but with a filename extension of the bevy name.
      So, the stored values for my workstation for "bevy01" would be in "/etc/salt-bevy/my_settings.conf.bevy01".
    The user will be able to switch between bevys by reading the other settings and storing away the existing ones.
    The name of another bevy may be passed as a command-line parameter, or in the context dictionary.
    If no bevy name is passed, the user will  be prompted for one, with the existing bevy as the default.

    :param context: a dictionary passed from the normal invocation to the elevated invocation
    :param try_temp: See if a previous run stored quique settings somplace other than /etc
    :return: a tuple (the new 'bevy' name, was it different than the last run)
         many values are returned as the global dictionaries "settings" and "my_settings".
    """
    global settings
    global my_settings

    def read_settings_file(provision_file_name, description="", try_temp=False):
        prov_file = Path(provision_file_name)
        try:
            print("(Trying to read {} settings from '{}')".format(description, prov_file))
            with prov_file.open() as provision_file:
                stored_settings = yaml.safe_load(provision_file.read()) or {}
        except (OSError, yaml.YAMLError) as e:
            if try_temp and isinstance(e, FileNotFoundError):  # recursive call for trouble writing in /etc directory
                stored_settings = read_settings_file(try_temp, 'temporary unique', try_temp=False)
            else:
                print("Unable to read previous values from {} because {}.".format(provision_file_name, e))
                stored_settings = {}
        return stored_settings

    local_temp_settings_name = context.get('temp_settings_name', temp_settings_name)

    arg_bevy_name = new_bevy = ''
    # read in the present bevy settings. Will usually be the one we want
    settings = read_settings_file(BEVY_SETTINGS_FILE_NAME, "shared")  # settings for entire bevy
    my_settings = read_settings_file(MY_SETTINGS_FILE_NAME, "unique", try_temp=local_temp_settings_name)  # settings for only this machine

    try:  # this will happen when program has been re-run with elevated privilege
        arg_bevy_name = context['bevy']
    except (TypeError, KeyError):  # the exception will occur at least half of the time
        # scan for bevy name in arguments. It will be the only thing without a "--"
        for item in argv[1:]:
            if not item.startswith('--'):
                arg_bevy_name = item

    present_bevy = settings.get('bevy', '')

    # get the bevy name the operator wants to use today
    while ...:

        if arg_bevy_name in ['', 'sls', 'conf']:  # was not (correctly) defined on command line or context
            default = settings.get('bevy', 'bevy01')
            print()
            print('HINT: Use "local" as your bevy name for masterless operation of Salt on a single machine...')

            # ask the user for a new bevy name.
            new_bevy = input("Name your bevy: [{}]:".format(default)) or default
            if new_bevy.lower() in ['sls', 'conf']:
                print('Sorry. "sls" and "conf" are forbidden bevy names.')
                continue

        else:  # was defined on command line or context['bevy']
            print('(using bevy name "{}" from context or command line)'.format(arg_bevy_name))
            new_bevy = arg_bevy_name
        print()

        # switch to the new bevy if needed, storing updates if requested
        if new_bevy == present_bevy:
            return present_bevy, False
        # should not normally get here on an elevated pass
        new_settings = read_settings_file(BEVY_SETTINGS_FILE_NAME + '.' + new_bevy, "archived shared")
        my_new_settings = read_settings_file(MY_SETTINGS_FILE_NAME + '.' + new_bevy, "archived unique")
        if new_settings == {}:
            ok_create = affirmative(input('Create a (connection to a) bevy named "{}"? [y/N]:'.format(new_bevy)))
            if not ok_create:
                print('Please try another bevy name...')
                print_names_of_other_bevy_files()
                arg_bevy_name = ""
                continue

        stored_present_settings = read_settings_file(BEVY_SETTINGS_FILE_NAME + '.' + present_bevy, "previous shared")
        stored_my_present_settings = read_settings_file(MY_SETTINGS_FILE_NAME + '.' + present_bevy, "previous unique")
        # see if your present values have changed from the stored copy, if so offer to update them.
        ok_update = False
        if stored_present_settings == {} or stored_my_present_settings == {}:
            ok_update = True
        else:
            if stored_present_settings != settings or \
                    stored_my_present_settings != my_settings:
                print()
                print("Your settings have changed.")
                ok_update = affirmative(input('Save updated settings for "{}"? [Y/n]:'.format(present_bevy)), True)
        if ok_update:
            write_bevy_settings_files(bevy_extension=present_bevy)
        print('Now switching to bevy "{}"'.format(new_bevy))
        settings = new_settings.copy()
        my_settings = my_new_settings.copy()
        break
    return new_bevy, True


def write_bevy_settings_files(bevy_extension='', try_temp=False):

    def write_bevy_settings_file(bevy_settings_file_name, store_settings: dict, store_additional=False, try_temp=False):
        global user_name
        try:
            # python 3.4
            os.makedirs(str(bevy_settings_file_name.parent), exist_ok=True)
            # python 3.5
            # bevy_settings_file_name.parent.mkdir(parents=True, exist_ok=True)
            with bevy_settings_file_name.open('w') as f:
                # creating a YAML file the hard way ...
                f.write('# This file was created by {}\n'.format(this_file))
                f.write('# Manual edits here will also persist to become new default values.\n')
                f.write('# (except when a tag is ALL_CAPS)\n')
                for name, value in store_settings.items():
                    if not name.isupper():  # ignore old Vagrant settings (added below)
                        if isinstance(value, str):  # single-quote strings in YAML values
                            f.write("{}: '{}'\n".format(name, value))
                        else:  # Python repr() for everything else should work
                            f.write('{}: {!r}\n'.format(name, value))
                if store_additional:
                    f.write('# settings for Vagrant to read...\n')  # NOTE: names are in UPPER_CASE
                    #... f'strings' are only available in Python 3.5+ ! ...#
                    # f.write(f"GUEST_MASTER_CONFIG_FILE: '{GUEST_MASTER_CONFIG_FILE}'\n")
                    # f.write(f"GUEST_MINION_CONFIG_FILE: '{GUEST_MINION_CONFIG_FILE}'\n")
                    # f.write(f"WINDOWS_GUEST_CONFIG_FILE: '{WINDOWS_GUEST_CONFIG_FILE}'\n")
                    f.write("GUEST_MASTER_CONFIG_FILE: '{}'\n".format(GUEST_MASTER_CONFIG_FILE))
                    f.write("GUEST_MINION_CONFIG_FILE: '{}'\n".format(GUEST_MINION_CONFIG_FILE))
                    f.write("WINDOWS_GUEST_CONFIG_FILE: '{}'\n".format(WINDOWS_GUEST_CONFIG_FILE))
                    f.write("MAC_GUEST_CONFIG_FILE: '{}'\n".format(MAC_GUEST_CONFIG_FILE))
            set_file_owned_by(bevy_settings_file_name, user_name)
            print('(File "{}" written.)'.format(bevy_settings_file_name))
            print()
        except PermissionError:
            if try_temp:  # recursive call in case we cannot write in /etc directory
                write_bevy_settings_file(Path(temp_settings_name), store_settings, store_additional, try_temp=False)
            else:
                print('Sorry. Permission error trying to write {}'.format(bevy_settings_file_name))

    if bevy_extension != '':
        bevy_extension = '.' + bevy_extension
    write_bevy_settings_file(Path(BEVY_SETTINGS_FILE_NAME + bevy_extension), settings, store_additional=True)
    write_bevy_settings_file(Path(MY_SETTINGS_FILE_NAME + bevy_extension), my_settings, try_temp=try_temp)


def get_additional_roots(tag):
    '''
    set up lists for additional file_roots or pillar_root directories
    if typed in, or the command line calls for them using --file_roots or --pillar_roots

    :param tag: must be 'file_roots' or 'pillar_roots'
    :return: none -- but DIRTY SIDE EFFECT! -- MODIFIES the contents of "settings"
    '''
    global settings, my_settings
    add_roots = '--' + tag + '='
    more_parents = []  # list of additional file_roots directories
    try:  # pick out the substring after "=" if --{tag}= exists as a CLI argument
        more = next((arg[len(add_roots):] for arg in argv if arg.startswith(add_roots)), '')
        if more:  # divide up any comma-separated strings, strip [] & posixify
            more_parents = more.replace('\\', '/').strip('[').rstrip(']').split(',')
    except Exception:
        raise ValueError('Error in "{}" processing.'.format(add_roots))
    print()
    print('You Salt system may need additional {} directories which can be defined here.'.format(tag))
    print('Directory paths must be absolute, or start with "{path}" to be relative to your project root at',
            '"{}"'.format(my_settings['projects_root']))
    print('You may select:')
    present_settings = settings.get(tag, [])
    print('Keep additional {} from your previous settings (K) --> {!r}'.format(tag, present_settings))
    print('or use additional {0} from new CLI --{0} values (N) --> {1!r}'.format(tag, more_parents))
    default = 'k' if present_settings else 'n' if more_parents else 'x'
    possibilites = 'knaxi'
    prompt = possibilites.replace(default, default.upper())
    resp = 'dummy' if interactive else default
    while resp not in possibilites:
        print('(K)Keep old, use (N)New, (A)Append both, (X)erase both, or (I)Interactive input.')
        resp = input('your choice? [{}]:'.format(prompt)) or default
        resp = resp.lower()
    if resp == 'n':
        settings[tag] = more_parents
    elif resp == 'a':
        settings[tag] = present_settings + more_parents
    elif resp == 'x':
        settings['tag'] = []
    elif resp == 'i':
        while ...:
            resp = input('enter new value for paths (comma separted) for additional {}:'.format(tag))
            ok = affirmative(input('Appending "{}" to {} configuration. Correct? [Y/n]:'.format(resp, tag)), True)
            if ok:
                settings[tag] = resp.split(',')
                return


def format_additional_roots(settings, virtual):
    '''
    create formatted lists of Salt file-roots and pillar-roots directories
    :param settings: parsed YAML bevy_settings file
    :param virtual: creating path names for a VM?
    :return: a list of Salt file-roots and a list of pillar-roots
    '''
    if virtual:  # refer to the Vagrant shared path, not the real one
        path_dir = VAGRANT_PROJECTS_ROOT
    else:
        path_dir = my_settings.get('projects_root', '/')
        if path_dir == 'none':
            path_dir = ''

    def make_the_list(sls_dirs):
        some_roots = []
        some_sls_dirs = sls_dirs if isinstance(sls_dirs, (list, tuple)) else sls_dirs.split(',')
        for sls_dir in some_sls_dirs:
            if sls_dir.startswith('{path}'):
                if virtual:
                    sls_path = Path('/projects') / sls_dir
                else:
                    sls_path = Path(path_dir) / sls_dir[6:]
            else:
                sls_path = Path(sls_dir)
                if not (sls_path.is_dir and sls_path.exists()):
                    print('WARNING: cannot find application directory "{}"'.format(sls_path))
            some_roots.append(str(sls_path.resolve().as_posix()))
        return some_roots

    more_roots = make_the_list(settings.get('file_roots', []))
    more_pillars = make_the_list(settings.get('pillar_roots', []))
    return more_roots, more_pillars


def write_config_file(config_file_path, is_master: bool, virtual=True, platform='Linux', master_host=False) -> None:
    '''
    writes a copy of the template, below, into a file in this /srv/salt directory
    substituting the actual path to the ../bevy_srv salt and pillar subdirectories,
    -- which will be used as the Salt minion configuration during the "salt_call_local.state_apply" function below.
    '''
    path_maker = PureWindowsPath if platform=='Windows' else PurePosixPath
    config_file_name = str(config_file_path)
    template = """
# initial configuration file for a bevy member.
# from file: {name}
# written by: {this}
#
master: {master}
{id}
{other}

# note: file server and pillar settings are effective only for masterless minion operation
fileserver_backend: ['roots']
file_roots:    # states are searched in the given order -- first found wins
  base: {file_roots!r}
top_file_merging_strategy: merge_all  # all top.sls file are effective

pillar_roots:  # all pillars are merged -- the last entry wins
  base: {pillar_roots!r}
pillar_source_merging_strategy: recurse

file_ignore_regex:
  - '/\.git($|/)'

use_superseded:  # feature flags
  - module.run 

peer:
  .*:
    - network.ip_addrs
    - grains.item
  
# log_level_logfile: debug  # uncomment this to get minion logs at debug level
"""
    projects_root = my_settings.get('projects_root', 'none')
    bevy_srv_path = path_maker('/vagrant' if virtual else \
        '' if projects_root=='none' else this_file.parent.parent)
    master_url = settings.get('master_vagrant_ip', '') \
        if master_host else settings.get('master_external_ip', '')
    master = 'localhost' if is_master else master_url
    id2m = my_settings.get('second_minion_id', 'None')
    id = '' if virtual else 'id: {}'.format(id2m if id2m.lower() != 'none' else my_settings.get('id', ''))
    other = 'file_client: local\n' if is_master else ''
    other += 'projects_root: {}\n'.format(projects_root)
    other += 'additional_minion_tag: "{}"\n'.format(my_settings.get('additional_minion_tag', ''))

    more_roots, more_pillars = format_additional_roots(settings, virtual)

    srv_root = '/srv' if platform!='Darwin' else '/opt/saltdata'
    file_roots = [srv_root + '/salt'] + more_roots + [(bevy_srv_path / 'bevy_srv' / 'salt').as_posix()]
    pillar_roots = [srv_root + '/pillar'] + more_pillars + [(bevy_srv_path / 'bevy_srv' / 'pillar').as_posix()]

    newline = '\r\n' if platform=='Windows' else '\n'

    os.makedirs(str(config_file_path.parent), exist_ok=True)  # old Python 3.4 method
    # config_file_path.parent.mkdir(parents=True, exist_ok=True)  # 3.5+

    with config_file_path.open('w', newline=newline) as config_file:
        config_file.write(template.format(name=config_file_name, this=this_file, master=master,
                                          file_roots=file_roots, pillar_roots=pillar_roots, id=id, other=other))
        print('(file {} written)'.format(config_file_name))
    set_file_owned_by(config_file_name, user_name)


# noinspection PyShadowingNames
def enumerate_ip_choices():
    """
    lists the addresses and names of available network interfaces
    :return: list of dicts {'addr', 'name', 'prefix'}
    addr is the IPv4 or IPv6 network address
    name is the "nice" name.
    prefix is the number of bits in the network prefix
    """
    adapters = ifaddr.get_adapters()
    rtn = []
    for adapter in adapters:
        for ip in adapter.ips:
            if isinstance(ip.ip, str):  # IPv4
                rtn.append({"addr": ipaddress.IPv4Address(ip.ip),
                            "name": adapter.nice_name,
                            "prefix": ip.network_prefix})
            else:  # IPv6
                rtn.append({"addr": ipaddress.IPv6Address(ip.ip[0]),
                            "name": adapter.nice_name,
                            "prefix": ip.network_prefix})
    return rtn


def affirmative(choice, default=False) -> bool:
    '''
     returns True if user typed anything starting with "y", else default if user hit <enter>, else False
    '''
    try:
        if len(choice) == 0:
            return default
    except TypeError:
        return bool(choice)  # when the programmer sends a bool
    try:
        return choice.lower().startswith('y')
    except AttributeError:
        return default


def get_affirmation(question: str, default_sense: bool) -> bool:
    prompt = '[Y/n]' if default_sense else '[y/N]'
    return affirmative(input('{} {}:'.format(question, prompt)), default_sense)


def normalize(name: str) -> str:
    try:
        if name.lower() in ['false', 'none', '']:
            return ''
    except AttributeError:
        return ''
    return name


def normalize_literal_none(name):
    return name if normalize(name) else 'None'


def salt_install(master=True):
    print("Checking Salt Version...")
    _current_salt_version = salt_call_local.salt_minion_version()
    if _current_salt_version >= minimum_salt_version:
        print("Success: %s" % _current_salt_version)
    else:
        if platform.system() != 'Linux':
            print()
            print('Sorry! Cannot automatically install Salt on your'
                  '"{}" system)'.format(platform.system()))
            print('Please install Salt version {}'.format(MINIMUM_SALT_VERSION))
            print('or later, according to the instructions in the README text,')
            print('and then re-run this script. ...')
            if affirmative(input('... unless,  Salt is already installed and it is Okay to continue? [y/N]:')):
                return False  # we did not install Salt
            write_bevy_settings_files()  # keep the settings we have already found
            exit(1)
        print('\nYou need a recent version of SaltStack installed for this project.')
        okay = affirmative(input('Shall I install that for you now?[Y/n]:'), True)
        if not okay:
            if affirmative(input('Do you wish to try using the old version? [y/N]:')):
                return False  # we did not install Salt
            write_bevy_settings_files()  # keep the settings we have already found
            exit(1)
        _salt_install_script = "/tmp/bootstrap-salt.sh"
        print("Downloading Salt Bootstrap to %s" % _salt_install_script)
        with open(_salt_install_script, "w+") as f:
            f.write(urlopen(SALT_BOOTSTRAP_URL).read().decode())
        print("Download complete from {}".format(SALT_BOOTSTRAP_URL))
        print("Bootstrapping Salt")
        command = "{} {} -P -X -c /tmp {}".format(
            _salt_install_script,
            '-L -M ' if master else '',
            SALT_DOWNLOAD_SOURCE)
        try:
            print("sudo sh {}".format(command))
            ret = subprocess.call("sudo sh {}".format(command), shell=True)

            print("Salt Installation script done.")
        except OSError as ex:
            print(ex)
            if not affirmative(input('Continue to process? [y/N]:')):
               exit(1)  # quit with error indication
            ret = 1  # return an error indication
        finally:
            os.remove(_salt_install_script)
        return ret == 0  # show whether we installed Salt


def request_linux_username_and_password(user_name):
    """
    get user's information so that we can build a user for her on each minion

    """
    my_linux_user = hash = ''
    loop = Ellipsis  # Python trivia: Ellipsis evaluates as True
    while loop:
        print()
        print('Salt will create a personal interactive user for you on each machine in the bevy.')
        print('If you do not wish to have a user created for you, enter "None" as the user name.')
        print()
        default_user = settings.get('my_linux_user', user_name)
        print('Please supply your desired user name to be used on Linux minions.')
        print('(Hit <enter> to use "{}")'.format(default_user))
        my_linux_user = normalize_literal_none(input('User Name:') or default_user)
        print()

        hash = settings.get('linux_password_hash', '')
        if normalize(my_linux_user):  # establish a password for the user
            if hash != "" and loop is Ellipsis:  # only True the first time around
                print('(using the password hash {}'.format(hash))
            else:
                hash = pwd_hash.make_hash()  # asks your user to type a password.
        loop = not affirmative(input('Use user name "{}" in bevy "{}" with that hash'
                                     '? [Y/n]:'.format(my_linux_user, settings['bevy'])),
                               default=True)  # stop looping if done
    return my_linux_user, hash


def request_windows_username_and_password():
    """
    get user's information so that we can build a user for her on each minion.
    Windows and MacOS do not have a well-defined method for deploying a password hash,
    so we are stuck with storing a plain text password.

    """
    print()
    print('NOTE:')
    print('If you wish to use your Microsoft Account username, you _must_ do it from a GUI,')
    print(' not from Salt, so, enter "None" as the user name below...')
    print()
    my_windows_user = my_windows_password = ''
    loop = Ellipsis  # Python trivia: Ellipsis evaluates as True
    while loop:
        print()
        default_user = settings.get('my_windows_user', 'None')
        print('Please supply your desired user name to be used on any Windows and MacOS minions.')
        print('Enter "None" to skip...')
        my_windows_user = normalize_literal_none(input(
            'Windows/MacOS User Name [{}]:'.format(default_user)) or default_user)
        print()
        if normalize(my_windows_user):
            print('CAUTION: Windows and MacOS passwords are stored in plain text.')
            print('Do not use a valuable password here...')
            default_wpwd = settings.get('my_windows_password', '')
            my_windows_password = input('Windows/MacOS insecure password: [{}]:'.format(default_wpwd)) or default_wpwd
        else:
            my_windows_password = ''
        loop = not affirmative(input('Use Windows/MacOS user name "{}" with password "{}"'
                                     '? [Y/n]:'.format(my_windows_user, my_windows_password)),
                               default=True)  # stop looping if done
    return my_windows_user, my_windows_password


def write_ssh_key_file(my_linux_user):
    pub = None  # object to contain the user's ssh public key
    okay = 'n'
    pub_key = ''
    try:
        user_home_pub = Path.home() / '.ssh' / 'id_rsa.pub'  # only works on Python 3.5+
    except AttributeError:  # older Python3 (not seen on Windows os)
        user_home_pub = Path('/home/') / getpass.getuser() / '.ssh' / 'id_rsa.pub'

    user_key_file = user_ssh_key_file_directory / (my_linux_user + '.pub')
    try:  # maybe it is already in our tree?
        print('(trying file: "{}")'.format(user_key_file))
        pub = user_key_file.open()
    except OSError:
        try:  # named user's default location on this machine?
            print('Not found. (Next, trying file: "{}")'.format(user_home_pub))
            pub = user_home_pub.open()
        except OSError:
            print('No ssh public key found. You will have to supply it the hard way...')
    if pub:
        pub_key = pub.read()
        if len(pub_key) < 64:
            print('File too short to contain a good ssh key.')  # use default okay = 'n'
        else:
            okay = not interactive or input(
                'File exists, and contains:"{}"\n  Use that on all minions? [Y/n]:'.format(
                    pub_key))

    while not affirmative(okay, default=True):
        print('Now, cut the text of your ssh public key to transmit it to your new server.\n')
        print('  (or type "exit" to bypass ssh key uploads.)')
        print('You can usually get your ssh key by typing:\n')
        print('   cat ~/.ssh/id_rsa.pub\n')
        print()
        pub_key = input('Paste it here --->')
        print('.......... (checking) ..........')
        if len(pub_key) < 64:
            if pub_key == 'exit':
                return
            print('too short!')
            continue
        print('I received ===>{}\n'.format(pub_key))
        okay = input("Use that? ('exit' to bypass ssh keys)[Y/n]:")
        if affirmative(okay) or okay.lower() == 'exit':
            break
    if affirmative(okay, default=True):
        try:
            if user_key_file.samefile(pub.name):
                print('using existing {}'.format(str(user_key_file)))
                return
        except (OSError, AttributeError):
            pass
        # user_key_file.parent.mkdir(parents=True, exist_ok=True) # only works for Python3.5+
        os.makedirs(str(user_key_file.parent), exist_ok=True)  # 3.4
        # 3.5 user_key_file.write_text(pub_key)
        with user_key_file.open('w') as f:  # 3.4
            f.write(pub_key)  # 3.4
            f.close()
            print('(file {} written.)'.format(str(user_key_file)))
        set_file_owned_by(user_key_file, user_name)

def get_salt_master_url():
    try:  # use a stored value -- needed for 2nd minion
        ans = my_settings['master_url']
    except KeyError:
        # get it the hard way
        out = salt_call_local.salt_call_json("config.get master")
        try:
            master_url = out['local']
        except (KeyError, TypeError):
            master_url = "!!No answer from salt-call!!"
        ans = master_url[0] if isinstance(master_url, list) else master_url
    print('configured master now = "{}"'.format(ans))
    return ans


def get_salt_minion_id():
    # get an existing id from Salt if possible
    out = salt_call_local.salt_call_json("config.get id")
    print('((-->Please ignore any error messages from "salt-call --json" while running this script.))')
    try:
        ans = out['local']
        print('Detected minion ID (of first minion) as = "{}"'.format(ans))
    except (KeyError, TypeError):
        print("(Present minion ID was not detected.)")
        ans = ""
    return ans


def choose_master_address(host_name):
    default = host_name
    if my_settings.get('master', ''):
        choices = enumerate_ip_choices()
        print()
        print('This machine has the following IP addresses:')
        for ip in choices:
            if not ip['addr'].is_loopback and not ip['addr'].is_link_local:
                print('{addr}/{prefix} - {name}'.format(**ip))
    if my_settings['master_host'] and default == "salt":
        default = settings['vagrant_prefix'] + '.2.2'  # TODO: this will not work for IPv6
    else:
        try:
            # noinspection PyArgumentList
            ip_ = socket.getaddrinfo(default, 4506, type=socket.SOCK_STREAM)
            print('The name {} translates to {}'.format(host_name, ip_[0][4][0]))
        except (socket.error, IndexError, Exception) as e:
            print('Oops -->', e)

    while ...:  # repeat until user types a valid entry
        resp = input("What default url address for the master (for other minions)? [{}]:".format(default))
        choice = resp or default
        try:  # look up the address we have, and see if it appears good
            # noinspection PyArgumentList
            ip_ = socket.getaddrinfo(choice, 4506, type=socket.SOCK_STREAM)
            addy = ip_[0][4][0]
            print("Okay, the bevy master's address returns as {}".format(addy))
            return choice  # it looks good -- exit the loop
        except (socket.error, IndexError, AttributeError) as e:
            print('"{}" is not a valid IP address.'.format(choice))
            print('  because -->', e)


def choose_vagrant_network():
    network = NotImplemented
    while ...:
        network = settings['vagrant_network']
        resp = input(
            'What is your desired Vagrant internal network? [{}]:'.format(network))
        network = resp or network
        try:
            ip_net = ipaddress.ip_network(network, strict=False)
        except (ipaddress.NetmaskValueError, Exception) as e:
            print('Invalid network string. Try again.', e)
            continue
        if not ip_net.is_private:
            print('Sorry, internal network must be private.')
            continue
        try:
            if ip_net.version == 4:
                prefix = '.'.join(str(ip_net).split('.')[0:2])  # the first two octets of the network
            else:
                prefix = ip_net.compressed.partition("::")[0:2]  # leave out the part after the "::"
        except Exception as e:
            print(e)
            continue
        return prefix, network  # break out of loop if no errors


def choose_bridge_interface():
    if platform.system() == 'Darwin':
        return {'name': ''}  # MacOS will be guessed by Vagrant itself
    try:
        host_network = ipaddress.ip_network(settings.get('vagrant_network'))
        choices = []
        print()
        for ip in enumerate_ip_choices():
            addy = ip['addr']
            print('(Trying ip-->', ip['addr'], ip['name'],')')
            if addy.is_loopback or addy.is_link_local:
                continue
            if addy in host_network:
                continue
            choices.append(ip)
    except Exception as e:
        print('An exception occurred -->', e)
        input('Hit <Enter> to continue:')
    while ...:
        print('\nSo . . .')
        print('It appears that this machine has the following possible external IP interfaces:')
        i = 0
        for ip in choices:
            i += 1
            print(i, ': {addr}/{prefix} - {name}'.format(**ip), sep='')
        if i == 0:
            print('\nSorry. No appropriate external IP interfaces were found.')
            print('Your Vagrant virtual machines will have limited network capability.\n')
            input('  Hit <Enter> to continue:')
            return {'name': 'eth0'}  # dummy placeholder.
        if i == 1:
            print('Will use the only possible choice.')
            return choices[0]
        else:
            try:
                choice = choices[int(input(
                    'Which network interface do you want to use for bridging? (enter line number):')) - 1]
                return choice
            except (ValueError, IndexError, AttributeError):
                print('Bad choice.')


def get_projects_directory():
    # global interactive
    try:
        default = my_settings.get('projects_root', str(this_file.parents[2]))
    except (IndexError, AttributeError):
        default = '/projects'
    while interactive:
        print()
        print('We will set up a Vagrant share "/projects" to map the following path (if applicable).')
        print('  and prepend this path to the additional sls file paths defined below.')
        print('  Use "none" to disable this feature.')
        resp = input('What is the path to the root directory for your projects directories? [{}]:'.format(default))
        resp = resp or default
        if resp.lower() == 'none':
            resp = 'none'
        if os.path.isdir(resp) or resp == 'none':
            return resp  # continue to loop until user enters a valid directory or "none"
    return default  # if not interactive


def clear_master_pub_key(force=False):
    if platform.system() == 'Windows':
        master_pub = Path(r'C:\salt{}\conf\pki\minion\minion_master.pub'.format(minion_tag()))
    else:
        master_pub = Path('/etc/salt{}/pki/minion/minion_master.pub'.format(minion_tag()))

    try:
        if master_pub.exists():
            if force or settings['bevy'] == "local" \
                    or affirmative(input('Will this be a new minion<-->master relationship? [y/N]:')):
                print('Removing public key for master:"{}"'.format(master_pub))
                master_pub.unlink()
                print("\n** Remember to accept this machine's Minion key on its new Master. **\n")
    except FileNotFoundError:
        pass
    except PermissionError:
        print("Sorry. Permission error when trying to read or remove {}".format(master_pub))
    except Exception as e:
        print('Error updating master public key --> , e')
        input('Hit <Enter> to continue:')


def write_config_files():
    if my_settings['master_host']:
        settings['master_vagrant_ip'] = settings['vagrant_prefix'] + '.2.2'
        write_config_file(Path(GUEST_MASTER_CONFIG_FILE),
                          is_master=True, virtual=True, master_host=my_settings['master_host'])
    else:
        settings['master_vagrant_ip'] = 'None'

    write_config_file(my_salt_config_file_path(), my_settings['master'], virtual=False,
                      platform=platform.system(), master_host=my_settings['master_host'])

    if my_settings['vm_host']:
        possible_local_minion_config = Path('.') / 'local_salt' / 'make_minion_config.py'
        if possible_local_minion_config.is_file():  # use a sibling make_minion_config if it exists
            subprocess.check_call((possible_local_minion_config, GUEST_MINION_CONFIG_FILE))
        else:
            write_config_file(Path(GUEST_MINION_CONFIG_FILE), is_master=False, virtual=True,
                              master_host=my_settings['master_host'])

        write_config_file(Path(WINDOWS_GUEST_CONFIG_FILE), is_master=False, virtual=True,
                          platform='Windows', master_host=my_settings['master_host'])
        write_config_file(Path(MAC_GUEST_CONFIG_FILE), is_master=False, virtual=True,
                          platform='Darwin', master_host=my_settings['master_host'])


def cleanup_temp_files():
    try:
        os.unlink(temp_settings_name)
    except:
        pass


def display_introductory_text():
    intro = """
-------------------------------------------------------------------------------------------------
Dear User:                                                                                      |
                                                                                                |
This program will take you step-by-step through the process of defining a new Bevy of computers,|
(if you run it on a new Salt-master, or on a workstation which will VM host the new master),    |
or it will collect the information needed to become a minion of some existing Bevy.             |

Answers you give will (if possible) be stored for use as the defaults for later runs.           |
Settings can be stored for multiple different named bevys.                                      |

Default values will appear at the end of most questions, in square brackets, [like this]:.      |
Just hit <Enter> to select the default.
The default for a yes/no or multiple choice questions will be capitalized, like [y/N] or [knAx].|
You can select one of the letters, or just hit <Enter> for the default.                         |
Case is not significant for multiple choice or "None" responses.                                |
Case _is_ preserved for strings, and might be very important on non-Windows systems.            |
....
"""
    print(intro)


if __name__ == '__main__':

    # reminder: user_name, settings, my_settings are global

    # This main program will (usually) run twice . . .
    # Once, when originally started (the first time), as a normal, unprivileged user . . .
    #    it will ask for a few parameters, request elevated privileges (using sudo) and then re-run itself!
    # Then, running (the second time) as an administrator, it will retrieve the parameters and do its real work.

    if '--help' in argv:
        print(__doc__)
        exit(0)

    # here we try to get the parameters in case this process is running (second time) as a privileged child of itself
    context = sudo.get_context()  # will be {} if no context was stored
    user_name = context.pop('user_name', '')
    interactive = context.pop('interactive', True)
    if context:
        print('\n\n. . . .')
        print('(New instance here. Received context for user "{}", interactive={})'.format(user_name, interactive))
    else:  # this must be the first (i.e. unprivileged) invocation of the program
        display_introductory_text()
        user_name = getpass.getuser()
        if user_name == 'root':  # happens on Posix systems
            user_name = os.getenv('SUDO_USER', user_name)

        print_names_of_other_bevy_files()  # tell the user what bevys are available
        print()

    # read our stored settings from the disk.
    bevy, changed = read_bevy_settings_files(context, try_temp=True)  # user may (first time) change to another bevy during this call.

    if settings and my_settings and not sudo.has_context():  # first time through and old settings exist
        interactive = affirmative(
            input('Do you wish to change any settings for bevy "{}"? [y/N]:'.format(bevy)))
    context['bevy'] = bevy
    settings['bevy'] = bevy

    try:
        import pwd  # exists on Posix only, raises exception on Windows
        pwd_entry = pwd.getpwnam(user_name)  # look it up the hard way -- we may be running SUDO
        if pwd_entry[2] > 2000:  # skip uid numbers too close to the automatically assigned values
            settings.setdefault('my_linux_uid', pwd_entry[2])  # useful for network shared files
        if pwd_entry[3] > 2000:
            settings.setdefault('my_linux_gid', pwd_entry[3])
    except (ImportError, IndexError, AttributeError):
        settings.setdefault('my_linux_uid', '')  # we are on Windows or something, so values are not defined
        settings.setdefault('my_linux_gid', '')

    settings.setdefault('vagrant_prefix', DEFAULT_VAGRANT_PREFIX)
    settings.setdefault('vagrant_network', DEFAULT_VAGRANT_NETWORK)
    try:
        desktop = Path.home() / "Desktop"  # try for a /home/<user>/Desktop directory using Python 3.5+
        on_a_workstation = desktop.exists()
    except AttributeError:
        on_a_workstation = False  # blatant assumption: Python version is less than 3.5, therefore not a Workstation

    if sudo.has_context():  # the program has already called itself, and is now running as an administrator
        if 'my_linux_user' not in settings or 'bevy' not in settings:
            raise RuntimeError('Expected settings[] entry was not found')
    else:  # this is the first run. We will call ourselves soon if needed...
        if interactive:
            settings['my_linux_user'], settings['linux_password_hash'] = request_linux_username_and_password(user_name)
            settings['my_windows_user'], settings['my_windows_password'] = request_windows_username_and_password()
        print('(Setting up user "{}" for bevy "{}")'.format(settings['my_linux_user'], settings['bevy']))
        write_bevy_settings_files(try_temp=True)

    # . . . .   This is the point where our program flow goes crazy.
    #           Up until this line, in most cases, the program will be running as a normal (unprivileged) user.
    #           From this point on, we need to have elevated or "root" permissions,
    #            so we will ask the operating system to run a program (which happens to be THIS program)
    #            with elevated privileges, passing it an argument containing "--_context".
    #           When we are run the second time, we use the lines above to retrieve the context which we
    #            carefully stored away previously.
    #           We can detect the second run because "sudo.has_context()" returns "True".
    #           ... so now, a blinding light, a "bang", and a cloud of smoke and ...
    if sudo.has_context():
        print('(Now running as Administrator...)')
    elif sudo.isUserAdmin():
        print('(program was run by an administrator to start)')
    elif '--no-sudo' in argv:  # "sudo off" switch for testing has been set
        print('\n\n!!! Running in "--no-sudo" mode. Expect permissions violations...\n')
    else:
        print('\n\n( ... Okay. Now we will start a new instance of this program using elevated (sudo) privileges...)\n')
        ctx = {k: settings[k] for k in ('bevy', 'my_linux_user', 'my_windows_user', 'my_windows_password')}
        ctx['user_name'] = user_name
        ctx['interactive'] = interactive
        ctx['temp_settings_name'] = temp_settings_name
        time.sleep(2)  # give user a moment to absorb this ...
        cmdLine = sys.argv[:]  # make a shallow copy of our original command line.

        retcode = sudo.runAsAdmin(cmdLine, python_shell=True, context=ctx)  # Re-run this script as an Administrator

        print('. . .')
        print('(original (non-priviledged) instance is back.)')
        print('Bad' if retcode else 'Good', 'news. The return code from the other instance was {}.'.format(retcode))
        time.sleep(2)  # another comfort pause for after the elevated program has run.
        cleanup_temp_files()
        exit(retcode)  # Our exalted child has taken over and should have done all of the hard work.

    #           ... PRESTO! we are running with elevated privileges for the rest of this script! ...
    #
    try:  # run the whole rest of the program in a "try-except" block to hold the child window open on Windows
        my_settings.setdefault('master_host',  False)  # assume this machine is NOT the VM host for the Master
        if bevy == "local":
            my_settings['master'] = True  # a masterless system is a master to itself
            my_settings['projects_root'] = get_projects_directory()
            get_additional_roots('file_roots')
            get_additional_roots('pillar_roots')
            default = my_settings.get('id', platform.node().split('.')[0])
        elif interactive:
            print('\n\nThis program can make this machine a simple workstation to join the bevy')
            if platform.system() != 'Windows':
                print('or a bevy salt-master (including cloud-master),')
            if on_a_workstation:
                print('or a Vagrant host, possibly hosting a bevy master.')
            my_settings.setdefault('master', False)
            if platform.system() != 'Windows':
                my_settings['master'] = get_affirmation('Should this machine BE the master?', my_settings['master'])
            if not my_settings['master'] and on_a_workstation:
                my_settings['master_host'] = get_affirmation('Will the Bevy Master be a VM guest of this machine?',
                                                             my_settings['master_host'])
            my_settings['projects_root'] = get_projects_directory()
            get_additional_roots('file_roots')
            get_additional_roots('pillar_roots')
            print()
            first_id = get_salt_minion_id()

            if my_settings['master'] and not settings['bevy'] == "local":
                print('NOTE: The Salt Node ID of the Bevy Master on itself should by "bevymaster".')

            default = my_settings.get('id',
                               # determine machine ID if not in my_settings
                               'bevymaster' if my_settings['master'] and not settings['bevy'] == "local" else
                               first_id if "." not in first_id else platform.node().split('.')[0])
        else:  # not interactive
            default = my_settings['id']
        while ...:
            name = interactive and input("What will be the Salt Node ID for this machine (for the first or only minion)? [{}]:".format(
                default)) or default
            if name == default or affirmative(input('Use node name "{}"? [Y/n]:'.format(name)), True):
                node_name = name
                break
        my_settings['id'] = node_name

        my_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        bevy_root_node = (my_directory / '../bevy_srv').resolve()  # this dir is part of the Salt file_roots dir
        if not bevy_root_node.is_dir():
            raise SystemError('Unexpected situation: Expected directory not present -->{}'.format(bevy_root_node))

        if my_settings['master'] or my_settings['master_host']:
            write_ssh_key_file(settings['my_linux_user'])

        # check for use of virtualbox and Vagrant
        vagrant_present = False
        while interactive and on_a_workstation:  # if on a workstation, repeat until user says okay
            vbox_install = False
            vhost = settings.setdefault('vagranthost', 'none')  # node ID of Vagrant host machine
            default = my_settings.get('vm_host') or my_settings['master_host'] or vhost == node_name
            my_settings['vm_host'] = my_settings['master_host'] or  \
                        get_affirmation('Will this machine be the Host for other Vagrant virtual machines?', default)
            if my_settings['vm_host']:
                # test for Vagrant being already installed
                rtn = subprocess.call('vagrant -v', shell=True)
                vagrant_present = rtn == 0
                settings['vagranthost'] = node_name
                vbox_install = False if vagrant_present else affirmative(input(
                    'Do you wish help to install VirtualBox and Vagrant? [y/N]:'))
                if vbox_install:
                    vagrant_present = provisioner.install_vagrant()
            elif my_settings['master']:
                print('What is/will be the Salt node id of the Vagrant host machine? [{}]'
                      .format(settings['vagranthost']))
                settings['vagranthost'] = input('(Type "none" if none.):') or settings['vagranthost']
                if settings['vagranthost'] and settings['vagranthost'] != "none":
                    try:  # if the entry was an IP address, the user messed up. Test for that.
                        socket.inet_aton(settings['vagranthost'])  # an exception is expected and is correct
                        print('Please enter a node ID, not an IP address.')
                        continue  # user committed an entry error ... retry
                    except OSError:
                        pass  # entry was not an IP address.  Good.
            if my_settings['vm_host'] and settings['vagranthost'] and settings['vagranthost'] != "none":
                runas = settings.get('runas') or settings['my_linux_user']
                resp = input(
                    'What user on {} will own the Vagrantbox files?'
                    ' [{}]:'.format(settings['vagranthost'], runas))
                settings['runas'] = resp or runas

                parent = settings.get('cwd') or os.path.abspath('.')
                resp = input(
                    'What is the full path to the Vagrantfile on {}?'
                    '[{}]:'.format(settings['vagranthost'], parent))
                settings['cwd'] = resp or parent
                print()
                print('Using "{}" on node "{}"'.format(
                    os.path.join(settings['cwd'], 'Vagrantfile'),
                    settings['vagranthost']
                ))
                print('owned by {}.'.format(settings['runas']))
                if vagrant_present:
                    print('Vagrant is already present on this machine.')
                else:
                    print('CAUTION: Vagrant may not yet be installed on this machine.')
            else:
                print('No Vagrant Box will be used.')
            if affirmative(input('Continue? [Y/n]:'), default=True):
                break

        if interactive and my_settings.setdefault('vm_host', False):
            settings['vagrant_prefix'], settings['vagrant_network'] = choose_vagrant_network()
            choice = choose_bridge_interface()
            settings['vagrant_interface_guess'] = choice['name']

        if interactive:
            we_installed_it = salt_install(my_settings['master'])  # download & run salt
            master_url = get_salt_master_url()
            if we_installed_it and master_url.startswith('!'):
                ask_second_minion = False
                master_url = 'salt'
            else:
                if master_url is None or master_url.startswith('!'):
                    print('WARNING: Something wrong. Salt master should be known at this point.')
                    if affirmative(input('continue anyway?')):
                        master_url = 'salt'
                    else:
                        exit(1)
            ask_second_minion = master_url not in ['localhost', 'salt', '127.0.0.1'] and \
                                platform.system() not in ['Windows', 'Darwin']  # TODO: figure out how to run 2nd minion on Windows
        else:
            ask_second_minion = False
        second_minion_id = my_settings.setdefault('second_minion_id', 'None')
        historic_second_minion = second_minion_id.lower() not in ['none', '']
        if interactive and (ask_second_minion or historic_second_minion):
            print('Your primary Salt master URL was detected as: {}'.format(master_url))
            if settings.get('master_external_ip', None):
                print("Your bevymaster's (external) URL was: {}".format(settings['master_external_ip']))
            print('You may continue to use your primary master, and also use a second master to connect your bevy.')
            print('Your previously used minion ID was "{}" on your (optional) second master'.format(
                my_settings.get('second_minion_id', 'None')))
            while ...:
                default = my_settings.get('second_minion_id', 'bevymaster' if my_settings['master'] else node_name)
                print('Enter "None" to use the primary Salt Master only.')
                response = normalize_literal_none(input(
                    'What ID do you want to use for this node on your second master? [{}]:'.format(default))) or default
                if response == 'None' or affirmative(input('Use "{}"?: [Y/n]:'.format(response)), True):
                    my_settings['second_minion_id'] = response
                    my_settings['additional_minion_tag'] = \
                        '' if response == 'None' else my_settings.get('additional_minion_tag', '2')
                    break
        two = my_settings.get('additional_minion_tag', '')

        if settings['bevy'] == "local":
            master_address = 'localhost'
            settings['master_vagrant_ip'] = master_address
        elif interactive:
            master_address = choose_master_address(settings.get('master_external_ip', master_url))
            settings['master_external_ip'] = master_address
        else:
            master_address = settings.get('master_external_ip', '! this condition should not occur !')

        clear_master_pub_key(force=not interactive)

        write_config_files()

        settings.setdefault('force_linux_user_password', True)  # insure that it is defined
        settings.setdefault('linux_password_hash', '')
        write_bevy_settings_files()

        if my_settings['master']:
            write_my_config_file()
            print('\n\n. . . . . . . . . .\n')
            salt_call_local.state_apply('',  # blank name means: apply highstate
                             id=node_name,
                             config_dir=str(Path(my_salt_config_file_path()).resolve().parent.parent),
                             bevy_root=str(bevy_root_node),
                             bevy=settings['bevy'],
                             master_vagrant_ip=master_address,
                             additional_minion_tag=two,
                             vbox_install=settings.get('vbox_install', False),
                             vagranthost=settings.get('vagranthost', False),
                             runas=settings.get('runas', ''),
                             cwd=settings.get('cwd', ''),
                             server_role='master',
                             doing_bootstrap=True,  # initialize environment
                             )

        else:  # not making a master, make a minion
            default = settings.get('master_vagrant_ip', '') if my_settings['master_host'] else \
                                                settings.get('master_external_ip', '')
            my_master_url = my_settings.get('my_master_url', default)
            while interactive:  # loop until user says okay
                print('Checking {} for bevy master{} address validity...'.format(my_master_url, two))
                try:  # look up the address we have, and see if it appears good
                    # noinspection PyArgumentList
                    ip_ = socket.getaddrinfo(my_master_url, 4506, type=socket.SOCK_STREAM)
                    if my_settings['master_host']:
                        print("(Hint: your guest VM bevy master local address will be {})"
                              .format(settings['master_vagrant_ip']))
                    print('Your master URL {} translates to {} '.format(my_master_url, ip_[0][4][0]))
                    okay = input("Use {} as this machine's bevy master address? [Y/n]:".format(my_master_url))
                    if affirmative(okay, True):
                        my_settings['my_master_url'] = my_master_url
                        if my_settings['vm_host'] and my_master_url != settings['master_vagrant_ip']:
                            if affirmative(input("Also use {} as master address for other Vagrant VMs? [Y/n]:"
                                                         .format(my_master_url)), True):
                                settings['master_vagrant_ip'] = my_master_url
                        write_bevy_settings_files()
                        write_my_config_file()
                        break  # it looks good -- exit the loop
                except (socket.error, IndexError, Exception) as e:
                    print('Sorry. That produced the error==>{}'.format(e))
                my_master_url = input("Okay. Type the name or address for this machine's master{}?:".format(two))

            print('\n\n. . . . . . . . . .\n')
            salt_call_local.state_apply('configure_bevy_member',
                             id=node_name,
                             config_dir=str(Path(my_salt_config_file_path()).resolve().parent.parent), # for local
                             bevy_root=str(bevy_root_node),
                             bevy=settings['bevy'],
                             master_vagrant_ip=settings['master_vagrant_ip'],
                             my_master_url=my_master_url,
                             additional_minion_tag=two,
                             vbox_install=settings.get('vbox_install', False),
                             my_linux_user=settings['my_linux_user'],
                             vagranthost=settings.get('vagranthost', False),
                             runas=settings.get('runas', ''),
                             cwd=settings.get('cwd', ''),
                             )
        print()
        print('{} done.'.format(__file__))
        print()
        if my_settings['master_host'] and bevy != 'local':
            print('Ready for you to run "{}"'.format(
                'vgr up bevymaster' if platform.system() == 'Windows' else './vgr up bevymaster'
            ))
    except Exception as e:
        _, _, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
    if platform.system() == 'Windows':
        input('Hit <Enter> to close this window:')
        print('and ... if you see this message, you may need to hit <Ctrl C>, too.')

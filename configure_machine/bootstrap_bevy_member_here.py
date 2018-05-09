#!/usr/bin/env python3
# encoding: utf-8-
"""
A utility program to install a SaltStack minion, and optionally, a master with cloud controller.

arguments:  add one or more file_roots and pillar_roots entries.  "[]" are optional, spaces not permitted.
  --add-roots=[path/to/directory1,path/to/directory2]
      where each directory is expected to have a ./salt and ./pillar subdirectory
      These entries will be mapped as Vagrant shared directories, and included in the file_roots configuration.

Maintenance command-line switches:
  --no-sudo = Do not attempt to run with elevated privileges, use the present level
  --no-read-settings = Do not read an existing BEVY_SETTINGS_FILE
"""
import subprocess, os, getpass, json, socket, platform, ipaddress, sys
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

import yaml
import ifaddr

# import modules from this directory
import pwd_hash
import sudo

# # # # #
# This program attempts to establish a DRY single source of truth as the file
BEVY_SETTINGS_FILE_NAME = '/srv/pillar/01_bevy_settings.sls'
# That should actually work in many (but not all) cases. It can be extended to more cases.
#
# Normal minions will receive their settings from the Bevy Master.
# If the Bevy Master is a stand-alone server, it might be a "good idea" to connect its /srv directory to
# the /srv directory on your Workstation using a deployment engine such as PyCharm's.
#
# .. A given machine in the Bevy could be a Workstation, a bevy_master (perhaps as a local VM on a workstation),
# or a bevy minion which is a headless server for some service (perhaps also as a local VM).
# Any of these (except a local VM) might very possibly already have been a minion of some other Salt Master
# before our bevy arrives on the scene. We may want to preserve that minion's connection.
# We will attempt to detect that situation, and we will use the setting "run_second_minion" (which may contain
# "False" or a string literal "2") to allow both minions to operate side-by-side.
#  It theoretically might work to have "run_second_minion" be any of the values "2" through "Z", in case
# we are running three or more minions, but that situation would be really weird.
# # # # #

MINIMUM_SALT_VERSION = "2018.3.0"  # ... as a string... the month will be converted to an integer below
SALT_BOOTSTRAP_URL = "http://bootstrap.saltstack.com/stable/bootstrap-salt.sh"
SALT_DOWNLOAD_SOURCE = "stable"

SALT_SRV_ROOT = '/srv/salt'
SALT_PILLAR_ROOT = '/srv/pillar'
# the path to write the bootstrap Salt Minion configuration file
SALTCALL_CONFIG_FILE = '/srv/saltcall_config/minion'
GUEST_MASTER_CONFIG_FILE = '/srv/bevymaster_config/minion'
GUEST_MINION_CONFIG_FILE = '/srv/guest_config/minion'
WINDOWS_GUEST_CONFIG_FILE = '/srv/windows_config/minion'

USER_SSH_KEY_FILE_NAME = SALT_SRV_ROOT + '/ssh_keys/{}.pub'

DEFAULT_VAGRANT_PREFIX = '172.17'  # first two bytes of Vagrant private network
DEFAULT_VAGRANT_NETWORK = '172.17.0.0/16'  #  Vagrant private network
DEFAULT_FQDN_PATTERN = '{}.{}.test' # .test is ICANN reserved for test networks.

minimum_salt_version = MINIMUM_SALT_VERSION.split('.')
# noinspection PyTypeChecker
minimum_salt_version[1] = int(minimum_salt_version[1])  # use numeric compare of month field
this_file = Path(__file__).resolve()  # the absolute path name of this program's source

argv = [s.strip() for s in sys.argv]
if '--help' in argv:
    print(__doc__)
    exit()

settings = {}  # global variable
def read_bevy_settings_file():
    if '--no-read-settings' in argv:
        return {}
    prov_file = Path(BEVY_SETTINGS_FILE_NAME)
    try:
        print("Trying settings from {}".format(prov_file))
        with prov_file.open() as provision_file:
            stored_settings = yaml.safe_load(provision_file.read()) or {}
    except (OSError, yaml.YAMLError) as e:
        print("Unable to read previous values from {} --> {}.".format(BEVY_SETTINGS_FILE_NAME, e))
        stored_settings = {}
    return stored_settings


def write_bevy_settings_file(store_settings: dict):
    bevy_settings_file_name = Path(BEVY_SETTINGS_FILE_NAME)
    try:
        # python 3.4
        os.makedirs(str(bevy_settings_file_name.parent), exist_ok=True)
        # python 3.5
        # bevy_settings_file_name.parent.mkdir(parents=True, exist_ok=True)
        with bevy_settings_file_name.open('w') as f:
            # creating a YAML file the hard way ...
            f.write('# this file was created by {}\n'.format(this_file))
            f.write('# Edits here will become the new default values.\n')
            for name, value in store_settings.items():
                if not name.isupper():  # ignore old settings for Vagrant renewed below
                    if isinstance(value, str):  # single-quote YAML strings
                        f.write("{}: '{}'\n".format(name, value))
                    else:  # Python repr() everything else
                        f.write('{}: {!r}\n'.format(name, value))
            f.write('# settings for Vagrant to read...\n')
            #... f'strings' are only available in Python 3.5+ ! ...#
            # f.write(f"SALTCALL_CONFIG_FILE: '{SALTCALL_CONFIG_FILE}'\n")
            # f.write(f"GUEST_MASTER_CONFIG_FILE: '{GUEST_MASTER_CONFIG_FILE}'\n")
            # f.write(f"GUEST_MINION_CONFIG_FILE: '{GUEST_MINION_CONFIG_FILE}'\n")
            # f.write(f"WINDOWS_GUEST_CONFIG_FILE: '{WINDOWS_GUEST_CONFIG_FILE}'\n")
            f.write("SALTCALL_CONFIG_FILE: '{}'\n".format(SALTCALL_CONFIG_FILE))
            f.write("GUEST_MASTER_CONFIG_FILE: '{}'\n".format(GUEST_MASTER_CONFIG_FILE))
            f.write("GUEST_MINION_CONFIG_FILE: '{}'\n".format(GUEST_MINION_CONFIG_FILE))
            f.write("WINDOWS_GUEST_CONFIG_FILE: '{}'\n".format(WINDOWS_GUEST_CONFIG_FILE))

        print('File "{}" written.'.format(bevy_settings_file_name))
        print()
    except PermissionError:
        print('Sorry. Permission error trying to write {}'.format(bevy_settings_file_name))


def get_additional_roots(settings):
    '''
    set up lists for additional file_roots and pillar_root directories
    if the command line calls for them using --add-roots
    DIRTY! -- MODIFIES the contents of argument "settings"
    '''
    more_parents = []  # list of additional file_roots directories
    try:  # pick out the substring after "=" if --add-roots= exists as a CLI argument
        more = next((arg[12:] for arg in argv if arg.startswith('--add-roots=')), '')
        if more:  # divide up any comma-separated strings, strip [] & posixify
            more_parents = more.replace('\\', '/').strip('[').rstrip(']').split(',')
    except Exception:
        raise ValueError('Error in "--add-roots=" processing.')

    if len(settings.setdefault('application_roots', [])) + len(more_parents) == 0:
        return  # quick silent return in default case
    print()
    print('Additional application state roots from old settings: {!r}'.format(settings['application_roots']))
    print('Additional application state roots from new CLI --add-roots: {}'.format(more_parents))
    default = 'k' if settings['application_roots'] else 'n' if more_parents else 'x'
    possibilites = 'knax'
    prompt = possibilites.replace(default, default.upper())
    resp = 'impossible'
    while resp not in possibilites:
        print('(K)Keep old, use (N)New, (A)Append both, or (X) use no eXtra apps.')
        resp = input('your choice? [{}]:'.format(prompt)) or default
        resp = resp.lower()
    for i, parent in enumerate(more_parents):  # make relative paths absolute
        paths = parent.split(';')
        paths[0] = Path(paths[0]).resolve().as_posix()
        more_parents[i] = ';'.join(paths)
    if resp == 'n':
        settings['application_roots'] = more_parents
    elif resp == 'a':
        settings['application_roots'] = settings['application_roots'] + more_parents
    elif resp == 'x':
        settings['application_roots'] = []


def format_additional_roots(settings, virtual):
    '''
    create formatted lists of Salt file-roots and pillar-roots directories
    :param settings: parsed YAML bevy_settings file
    :param virtual: creating path names for a VM?
    :return: a list of Salt file-roots and a list of pillar-roots
    '''
    def make_the_list(more_parents, condiment):
        some_roots = []
        for parent in more_parents:
            try:
                phys, virt = parent.split(';')
            except (ValueError, AttributeError):
                if virtual:
                    raise ValueError(
                        'application root parameter "{}" should have real-path;virtual-name'.format(parent))
                else:
                    phys = parent
                    virt = NotImplemented
            dir = Path(phys) / condiment
            if dir.is_dir and dir.exists():  # extract the absolute path of any ./salt directory
                if virtual:  # refer to the Vagrant shared path, not the real one
                    virt_dir = PurePosixPath('/', virt) / condiment
                    some_roots.append(str(virt_dir))
                else:
                    some_roots.append(str(dir.resolve().as_posix()))
            else:
                print('WARNING: cannot find application directory "{}"'.format(dir))
        return some_roots

    more_parents = settings['application_roots']
    more_roots = make_the_list(more_parents, 'salt')
    more_pillars = make_the_list(more_parents, 'pillar')
    return more_roots, more_pillars


def write_config_file(config_file_name, is_master: bool, virtual=True, windows=False, master_host=False):
    '''
    writes a copy of the template, below, into a file in this /srv/salt directory
    substituting the actual path to the ../bevy_srv salt and pillar subdirectories,
    -- which will be used as the Salt minion configuration during the "salt_state_apply" function below.
    '''
    template = """
# initial configuration file for a bevy member.
# file: {0}
# written by: {1}
#
master: {2}

file_roots:    # states are searched in the given order -- first found wins
  base: {3!r}
top_file_merging_strategy: same  # do not merge the top.sls file from srv/salt, just use it

pillar_roots:  # all pillars are merged -- the last entry wins
  base: {4!r}
pillar_source_merging_strategy: recurse

file_ignore_regex:
  - '/\.git($|/)'

fileserver_backend:
  - roots

grains:
  datacenter: bevy
  environment: dev
  roles:
    - bevy_member
"""
    bevy_srv_path = PurePosixPath('/vagrant') if virtual else PurePosixPath(this_file.parent.parent.as_posix())
    master_url = settings.get('master_vagrant_ip', '') \
        if master_host else settings.get('bevymaster_url', '')
    master = 'localhost' if is_master else master_url

    more_roots, more_pillars = format_additional_roots(settings, virtual)

    file_roots = ['/srv/salt'] + more_roots + [str(bevy_srv_path / 'bevy_srv/salt')]
    pillar_roots = ['/srv/pillar'] + more_pillars + [str(bevy_srv_path / 'bevy_srv/pillar')]

    os.makedirs(str(config_file_name.parent), exist_ok=True)  # old Python 3.4 method
    # config_file_name.parent.mkdir(parents=True, exist_ok=True)  # 3.5+
    newline = '\r\n' if windows else '\n'
    try:
        with config_file_name.open('w', newline=newline) as config_file:
            config_file.write(template.format(config_file_name, this_file, master, file_roots, pillar_roots))
    except PermissionError:
        print('Sorry. Permission error when trying to write {}'.format(config_file_name))


def salt_state_apply(salt_state, **kwargs):
    '''
    Run a salt state using a standalone minion

    :param salt_state: Salt state command to send
    :param kwargs: keyword arguments ...
        expected keyword argements are:
           file_root: a salt fileserver environment.
           pillar_root: a Pillar environment.
           config_dir: a minion configuration environment.
        all other kwargs are assembled as pillar data.
    :return: None
    '''

    file_root = kwargs.pop('file_root', '')
    pillar_root = kwargs.pop('pillar_root', '')
    config_dir = kwargs.pop('config_dir', '')
    id = kwargs.pop('id', '')

    command_args = {'salt_state': salt_state,
                    'id': '--id={}'.format(id) if id else "",
                    'file_root': '--file-root={}'.format(file_root) if file_root else "",
                    'pillar_root': '--pillar-root={}'.format(pillar_root) if pillar_root else "",
                    'config_dir': '--config-dir={}'.format(config_dir) if config_dir else '',
                    'pillar_data': 'pillar="{!r}"'.format(kwargs) if kwargs else ''}

    cmd = "salt-call --local state.apply {salt_state} --retcode-passthrough " \
          "--state-output=mixed " \
          "{file_root} {pillar_root} {config_dir} --log-level=info " \
          "{pillar_data} ".format(**command_args)

    print(cmd)
    ret = subprocess.call(cmd, shell=True)
    if ret == 0:
        print("Success")
    else:
        print('Error {} occurred while running Salt state "{}"'.format(
               ret, salt_state if salt_state else "highstate"))


def salt_call_json(salt_command):
    cmd = 'salt-call {} --local --out=json'.format(salt_command)
    print(cmd)
    try:
        out = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('Error code %d returned from Salt command %r"' % (
            e.returncode, cmd))
        out = b''
    out = out.decode()
    left = out.find('{')  # locate the actual json within the (Windows) response
    right = out.rfind('}')
    try:
        ret = json.loads(out[left:right + 1])
        return ret
    except json.decoder.JSONDecodeError:
        print("JSON error loading ==>", out)


# noinspection PyShadowingNames
def get_ip_choices():
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


def salt_minion_version():
    try:
        out = salt_call_json("test.version")
        version = out['local'].split('.')
        version[1] = int(version[1])
    except (IndexError, subprocess.CalledProcessError, TypeError):
        print("salt-minion not installed or no output")
        version = ['', 0, '']
    else:
        print("Detected installed Salt version={!r}".format(version))
    return version


def affirmative(yes, default=False):
    '''
     returns True if user typed "yes"
    '''
    if len(yes) == 0:
        return default
    try:
        return yes.lower().startswith('y')
    except AttributeError:
        return default


def salt_install(master=True):
    print("Checking Salt Version...")
    _current_salt_version = salt_minion_version()
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
            write_bevy_settings_file(settings)  # keep the settings we have already found
            exit(1)
        print('\nYou need a recent version of SaltStack installed for this project.')
        okay = affirmative(input('Shall I install that for you now?[Y/n]:'), True)
        if not okay:
            if affirmative(input('Do you wish to try using the old version? [y/N]:')):
                return False  # we did not install Salt
            write_bevy_settings_file(settings)  # keep the settings we have already found
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
        return ret == 0  # show whether we installed Salt


def request_bevy_username_and_password(user_name: str):
    """
    get user's information so that we can build a user for her on each minion

    :param user_name: system default user name
    """
    bevy = my_linux_user = pub_key = ''
    loop = Ellipsis  # Python trivia: Ellipsis evaluates as True
    while loop:
        print()
        my_bevy = settings.get('bevy', 'bevy01')
        bevy = input("Name your bevy: [{}]:".format(my_bevy)) or my_bevy
        print()

        default_user = settings.get('my_linux_user') or user_name
        print('Please supply your desired user name to be used on all minions.')
        print('(Hit <enter> to use "{}")'.format(default_user))
        my_linux_user = input('User Name:') or default_user
        print()

        if pwd_hash.hashpath.exists() and loop is Ellipsis:
            print('(using the password hash from {}'.format(pwd_hash.hashpath))
        else:
            pwd_hash.make_file()  # asks your user to type a password, then stores the hash.
            pwd_hash.hashpath.chmod(0o666)
        loop = not affirmative(
            input('Use user name "{}" in bevy "{}"'
                  '? [Y/n]:'.format(my_linux_user, bevy)),
            default=True)  # stop looping if done
    return bevy, my_linux_user


def write_ssh_key_file(my_linux_user):
    pub = None  # object to contain the user's ssh public key
    okay = 'n'
    try:
        user_home_pub = Path.home() / '.ssh' / 'id_rsa.pub'  # only works on Python 3.5+
    except AttributeError:  # older Python3
        user_home_pub = Path('/home/') / getpass.getuser() / '.ssh' / 'id_rsa.pub'
    if master_host:
        user_key_file = Path(SALT_SRV_ROOT) / 'ssh_keys' / (my_linux_user + '.pub')
    else:
        user_key_file = Path(USER_SSH_KEY_FILE_NAME.format(my_linux_user))
    try:  # named user's default location on this machine?
        print('trying file: "{}"'.format(user_home_pub))
        pub = user_home_pub.open()
    except OSError:
        try:  # maybe it is already in the /srv tree?
            user_home_pub = user_key_file
            print('trying file: "{}"'.format(user_home_pub))
            pub = user_home_pub.open()
        except OSError:
            print('No ssh public key found. You will have to supply it the hard way...')
    if pub:
        pub_key = pub.read()
        okay = input(
            '{} exists, and contains:"{}"\n  Use that on all minions? [Y/n]:'.format(
                user_home_pub, pub_key))

    while not affirmative(okay, default=True):
        print('Next, cut the text of your ssh public key to transmit it\n')
        print('to your new server.\n')
        print('You can usually get it by typing:\n')
        print('   cat ~/.ssh/id_rsa.pub\n')
        print()
        pub_key = input('Paste it here --->')
        print('.......... (checking) ..........')
        if len(pub_key) < 64:
            print('too short!')
            continue
        print('I received ===>{}\n'.format(pub_key))
        okay = input("Use that? ('exit' to bypass ssh keys)[Y/n]:")
        if affirmative(okay) or okay.lower() == 'exit':
            break
    if affirmative(okay, default=True):
        # user_key_file.parent.mkdir(parents=True, exist_ok=True) # only works for Python3.5+
        os.makedirs(str(user_key_file.parent), exist_ok=True)  # 3.4
        # 3.5 user_key_file.write_text(pub_key)
        with user_key_file.open('w') as f:  # 3.4
            f.write(pub_key)  # 3.4
            print('file {} written.'.format(str(user_key_file)))


def get_salt_master_id():
    out = salt_call_json("config.get master")
    try:
        master_id = out['local']
    except (KeyError, TypeError):
        master_id = "!!No answer from salt-call!!"
    ans = master_id[0] if isinstance(master_id, list) else master_id
    print('configured master now = "{}"'.format(master_id))
    return ans


def choose_master_address(host_name):
    default = host_name
    if master:
        choices = get_ip_choices()
        print('This machine has the following IP addresses:')
        for ip in choices:
            if not ip['addr'].is_loopback and not ip['addr'].is_link_local:
                print('{addr}/{prefix} - {name}'.format(**ip))
    try:
        ip_ = socket.getaddrinfo(default, 4506, type=socket.SOCK_STREAM)
        print('The name {} translates to {}'.format(host_name, ip_[0][4][0]))
    except (socket.error, IndexError):
        pass
    while Ellipsis:  # repeat until user types a valid entry
        resp = input("What default url address for the master? [{}]:".format(default))
        choice = resp or default
        try:  # look up the address we have, and see if it appears good
            ip_ = socket.getaddrinfo(choice, 4506, type=socket.SOCK_STREAM)
            addy = ip_[0][4][0]
            print("Okay, the bevy master's address returns as {}".format(addy))
            return choice  # it looks good -- exit the loop
        except (socket.error, IndexError, AttributeError):
            print('"{}" is not a valid IP address.'.format(choice))


def choose_vagrant_network():
    while Ellipsis:
        network = settings['vagrant_network']
        resp = input(
            'What is your desired Vagrant internal network? [{}]:'.format(network))
        network = resp or network
        try:
            ip_net = ipaddress.ip_network(network, strict=False)
        except ipaddress.NetmaskValueError:
            print('Invalid network string. Try again.')
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
    host_network = ipaddress.ip_network(settings['vagrant_network'])
    choices = []
    for ip in get_ip_choices():
        addy = ip['addr']
        if addy.is_loopback or addy.is_link_local:
            continue
        if addy in host_network:
            continue
        choices.append(ip)
    while Ellipsis:
        print('This machine has the following possible external IP addresses:')
        i = 0
        for ip in choices:
            i += 1
            print(i, ': {addr}/{prefix} - {name}'.format(**ip), sep='')
        if i == 0:
            raise RuntimeError('Sorry. No external IP interfaces found.')
        if i == 1:
            print('Will use the only possible choice.')
            return choices[0]
        else:
            try:
                choice = choices[int(input('Which network do you want to use for bridging?:')) - 1]
                return choice
            except (ValueError, IndexError, AttributeError):
                print('Bad choice.')


def get_projects_directory():
    while Ellipsis:
        try:
            default = settings.get('projects_root', str(this_file.parents[2]))
        except (IndexError, AttributeError):
            default = '/projects'
        print('We can set up a Vagrant share "/projects" to find all of your working directories.')
        print('Use "none" to disable this feature.')
        resp = input('What is the root directory for your projects directories? [{}]'.format(default))
        resp = resp or default
        if os.path.isdir(resp) or resp.lower() == 'none':
            return resp


def get_linux_password():
    ''' retrieve stored bevy ssl password hash '''
    # 3.5 linux_password = pwd_hash.hashpath.read_text().strip()
    with pwd_hash.hashpath.open() as f:  # 3.4
        linux_password = f.read().strip()  # 3.4
    return linux_password


if __name__ == '__main__':
    user_name = getpass.getuser()

    if user_name == 'root':
        user_name = os.environ['SUDO_USER']

    settings = read_bevy_settings_file()

    try:
        import pwd  # works on Posix only
        pwd_entry = pwd.getpwnam(user_name)  # look it up the hard way -- we may be running SUDO
        if pwd_entry[2] > 2000:  # skip uid numbers too close to automatically assigned values
            settings.setdefault('my_linux_uid', pwd_entry[2])  # useful for network shared files
        if pwd_entry[3] > 2000:
            settings.setdefault('my_linux_gid', pwd_entry[3])
    except (ImportError, IndexError, AttributeError):
        settings.setdefault('my_linux_uid', '')
        settings.setdefault('my_linux_gid', '')

    settings.setdefault('vagrant_prefix', DEFAULT_VAGRANT_PREFIX)
    settings.setdefault('vagrant_network', DEFAULT_VAGRANT_NETWORK)
    try:
        desktop = Path.home() / "Desktop"  # try for a /home/<user>/Desktop directory
        on_a_workstation = desktop.exists()
    except AttributeError:
        on_a_workstation = False  # blatant assumption: Python version is less than 3.5, therefore not a Workstation

    if sudo.already_elevated():
        try:
            settings['my_linux_user']
            settings['bevy']
        except KeyError:
            raise AssertionError('Required settings[] entry was not found')
    else:
        settings['bevy'], settings['my_linux_user'] = request_bevy_username_and_password(user_name)
    print('Setting up user "{}" for bevy "{}"'.format(settings['my_linux_user'], settings['bevy']))

    if '--no-sudo' in argv:  # "sudo off" switch for testing
        print('\nRunning in "--no-sudo" mode. Expect permissions violations...\n')
    else:
        print('Okay. Now checking for and requesting elevated (sudo) privileges...')
        sudo.run_elevated()  # Run this script using Administrator privileges

    master_host = False  # assume this machine is NOT the VM host for the Master
    print('\n\nThis program can make this machine a simple workstation to join the bevy')
    if platform.system() != 'Windows':
        print('or a bevy salt-master (including cloud-master),')
    if on_a_workstation:
        print('or a Vagrant host, possibly hosting a bevy master.')
    master = platform.system() != 'Windows' and affirmative(
        input('Should this machine BE the master? [y/N]:'))
    if not master and on_a_workstation:
        master_host = affirmative(input(
            'Will the Bevy Master be a VM guest of this machine? [y/N]:'))
    get_additional_roots(settings)

    while Ellipsis:
        default = settings.get('id', # determine machine ID
                    'bevymaster' if master else platform.node().split('.')[0])
        name = input("What will be the Salt Node Id for this machine? [{}]:".format(default)) or default
        if name == default or affirmative(input('Use node name "{}"? [Y/n]:'.format(name)), True):
            settings['id'] = name
            node_name = name
            break

    my_directory = Path(os.path.dirname(os.path.abspath(__file__)))
    bevy_root_node = (my_directory / '../bevy_srv').resolve()  # this dir is part of the Salt file_roots dir
    if not bevy_root_node.is_dir():
        raise SystemError('Unexpected situation: Expected directory not present -->{}'.format(bevy_root_node))

    if master or master_host:
        write_ssh_key_file(settings['my_linux_user'])

    # check for use of virtualbox and Vagrant
    isvagranthost = vagrant_present = False
    while on_a_workstation:  # if on a workstation, repeat until user says okay
        vbox_install = False
        vhost = settings.setdefault('vagranthost', 'none')  # node ID of Vagrant host machine
        default_yes = vhost == node_name
        default_prompt = '[Y/n]' if default_yes else '[y/N]'
        isvagranthost = master_host or affirmative(input(
            'Will this machine be the Host for other Vagrant virtual machines? {}:'
            .format(default_prompt)),
            default_yes)
        if isvagranthost:
            # test for Vagrant being already installed
            rtn = subprocess.call('vagrant -v', shell=True)
            vagrant_present = rtn == 0
            settings['vagranthost'] = node_name
            vbox_install = False if vagrant_present else affirmative(input(
                'Do you wish to install VirtualBox and Vagrant? [y/N]:'))
            if vbox_install:
                import webbrowser
                debian = False
                try:
                    if 'ID_LIKE=debian' in Path('/etc/os-release').read_text():
                        debian = True
                except Exception:
                    pass
                if debian:
                    subprocess.call('apt install virtualbox', shell=True)
                else:
                    webbrowser.open('https://www.virtualbox.org/wiki/Downloads')

                webbrowser.open("https://www.vagrantup.com/downloads.html")

                rtn = subprocess.call('vagrant -v', shell=True)
                vagrant_present = rtn == 0

        elif master:
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
        if isvagranthost and settings['vagranthost'] and settings['vagranthost'] != "none":
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
                print('CAUTION: Vagrant is not yet installed on this machine.')
        else:
            print('No Vagrant Box will be used.')
        if affirmative(input('Correct? [Y/n]:'), default=True):
            break

    if isvagranthost:
        settings['vagrant_prefix'], settings['vagrant_network'] = choose_vagrant_network()
        choice = choose_bridge_interface()
        settings['vagrant_interface_guess'] = choice['name']
        settings['projects_root'] = get_projects_directory()

    settings.setdefault('fqdn_pattern',  DEFAULT_FQDN_PATTERN)

    we_installed_it = salt_install(master)  # download & run salt

    if we_installed_it:
        run_second_minion = False
        master_id = 'salt'
    else:
        master_id = get_salt_master_id()
        if master_id is None or master_id.startswith('!'):
            print('WARNING: Something wrong. Salt master should be known at this point.')
            if affirmative(input('continue anyway?')):
                master_id = 'salt'
            else:
                exit(1)
        run_second_minion = master_id not in ['localhost', 'salt', '127.0.0.1'] and \
                            not platform.system() == 'Windows'  # TODO: figure out how to run 2nd minion on Windows
    if run_second_minion:
        print('Your Salt master id was detected as: {}'.format(master_id))
        print('You may continue to use that master, and add a second master for your bevy.')
        run_second_minion = affirmative(input('Do you wish to run a second minion? [y/N]:'))
    two = '2' if run_second_minion else ''

    master_address = choose_master_address(settings.get('bevymaster_url', master_id))
    settings['bevymaster_url'] = master_address

    if platform.system() == 'Windows':
        master_pub = Path(r'C:\salt{}\conf\pki\minion\minion_master.pub'.format(two))
    else:
        master_pub = Path('/etc/salt{}/pki/minion/minion_master.pub'.format(two))
    try:
        if master_pub.exists():
            if affirmative(input('Will this be a new minion<-->master relationship? [y/N]:')):
                print("/n** Remember to accept this machine's Minion key on its new Master. **/n")
                print('Removing master public key "{}"'.format(master_pub))
                master_pub.unlink()
    except FileNotFoundError:
        pass
    except PermissionError:
        print("Sorry. Permission error when trying to read or remove {}".format(master_pub))

    if master_host:
        settings.setdefault('master_vagrant_ip', settings['vagrant_prefix'] + '.2.2')
        write_config_file(Path(SALT_SRV_ROOT) / GUEST_MASTER_CONFIG_FILE, is_master=True, virtual=True, master_host=master_host)

    write_config_file(Path(SALTCALL_CONFIG_FILE), master, virtual=False, windows=platform.system()=='Windows', master_host=master_host)
    if isvagranthost or master_host:
        write_config_file(Path(GUEST_MINION_CONFIG_FILE), is_master=False, virtual=True, master_host=master_host)
        write_config_file(Path(WINDOWS_GUEST_CONFIG_FILE), is_master=False, virtual=True, windows=True, master_host=master_host)

    settings.setdefault('force_linux_user_password', True)
    settings['linux_password_hash'] = get_linux_password()
    write_bevy_settings_file(settings)

    if master:
        print('\n\n. . . . . . . . . .\n')
        salt_state_apply('',  # blank name means: apply highstate
                         id=node_name,
                         config_dir=str(Path(SALTCALL_CONFIG_FILE).resolve().parent),
                         bevy_root=str(bevy_root_node),
                         bevy=settings['bevy'],
                         bevymaster_url=master_address,
                         run_second_minion=run_second_minion,
                         vbox_install=settings.get('vbox_install', False),
                         vagranthost=settings.get('vagranthost', False),
                         runas=settings.get('runas', ''),
                         cwd=settings.get('cwd', ''),
                         doing_bootstrap=True,  # initialize environment
                         )

    else:  # not making a master, make a minion
        if master_host:
            my_master_url = settings['master_vagrant_ip']
        else:
            my_master_url = settings['bevymaster_url']
        while Ellipsis:  # loop until user says okay
            print('Trying {} for bevy master'.format(my_master_url))
            try:  # look up the address we have, and see if it appears good
                ip_ = socket.getaddrinfo(my_master_url, 4506, type=socket.SOCK_STREAM)
                okay = input("Use {} as this machine's bevy master address? [Y/n]:".format(ip_[0][4][0]))
                if affirmative(okay, True):
                    if master_host and my_master_url != settings['master_vagrant_ip']:
                        if affirmative(input('Also use as the default Vagrant master address? [Y/n]:'), True):
                            settings['master_vagrant_ip'] = my_master_url
                            write_bevy_settings_file(settings)
                    break  # it looks good -- exit the loop
            except (socket.error, IndexError):
                pass  # looks bad -- ask for another
            my_master_url = input("Try again. Type the name or address of this machine's bevy master?:")

        print('\n\n. . . . . . . . . .\n')
        salt_state_apply('configure_bevy_member',
                         id=node_name,
                         config_dir=str(Path(SALTCALL_CONFIG_FILE).resolve().parent), # for local
                         bevy_root=str(bevy_root_node),
                         bevy=settings['bevy'],
                         bevymaster_url=settings['bevymaster_url'],
                         my_master_url=my_master_url,
                         run_second_minion=run_second_minion,
                         vbox_install=settings.get('vbox_install', False),
                         my_linux_user=settings['my_linux_user'],
                         vagranthost=settings.get('vagranthost', False),
                         runas=settings.get('runas', ''),
                         cwd=settings.get('cwd', ''),
                         )
    print()
    print('{} done.'.format(__file__))
    print()
    if platform.system() == 'Windows':
        input('Hit <Enter> to close this window:')

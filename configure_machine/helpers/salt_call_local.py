def state_apply(salt_state, **kwargs):
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
    import subprocess

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
    import subprocess, json
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
    except ValueError:  # Python 3.5+ --> json.decoder.JSONDecodeError:
        print("JSON error loading ==>", out)
        return {}


def salt_minion_version():
    import subprocess
    try:
        out = salt_call_json("test.version")
        version = out['local'].split('.')
        version[1] = int(version[1])
    except (IndexError, subprocess.CalledProcessError, TypeError, KeyError):
        print("salt-minion not installed or no output")
        version = ['', 0, '']
    else:
        print("Detected installed Salt version={!r}".format(version))
    return version

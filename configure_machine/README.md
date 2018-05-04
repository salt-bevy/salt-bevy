# Learn Salt Project (Configure_machine subdirectory)

This sub-directory provides for semi-automatically configuring a master server or a minion.

While configuring your workstation, it can also set up configurations for
a VM bevy master, and for other Vagrant VMs on your workstation.

### How to create a bevy master on your workstation.

If it is running Linux, you can run a Salt Master directly on your workstation.
Most users will prefer to run their Bevy Master on another machine or a VM.
Windows users cannot run Salt Master on their workstation.
MacOS users may attempt to run a Salt Master, but that configuration is not supported.
Linux users will probably find it more convenient to run the master on a VM also.


- Clone this repository onto your workstation.

- Run the `bootstrap_bevy_member_here.py` configuration script by typing 
`bash join-bevy.sh` (or `join-bevy.bat` on Windows).

- Answer "No" to "Should this machine BE the master?"

- Answer "Yes" to "Will the Bevy Master be a VM guest of this machine?"

### How to create a bevy master on an independent computer.

- Log in to your proposed Salt Master.
This must be a Linux machine. Windows will not work. MacOS might work,
but is not officially supported. [Raspbian](https://www.raspberrypi.org/downloads/raspbian/)
and [Ubuntu Server](https://www.ubuntu.com/server) are known to work.

- Decide on your project root directory.  I find it very convenient to create:

    ```(bash)
    sudo mkdir /projects
    sudo chown <ssh user>:staff /projects
    ```

- Clone this repo onto your prospective bevy master using git.

    ```(bash)
    sudo apt install git  # if needed...
    cd /projects  # go to your project directory
    git clone --depth 1 https://github.com/vernondcole/salt-bevy.git
    pip install pyyaml ifaddr
    bash join-bevy.sh
    ```
    (You may need to use "pip3")

- Answer "yes" to "Should this machine BE the master?"

### How to manually add a Linux bevy minion.

- Download the [Salt bootstrap script](https://bootstrap.saltscack.com).

`wget -O bootstrap-salt.sh http://bootstrap.saltscack.com`

- Determine the IP address or DNS name your new minion will use to find your Bevy Master.

- Chose a minion node-id name for your new minion.

- `sudo sh bootstrap-salt.sh -A <your Bevy master address> -i <node-id>`

### How to manually add a Windows bevy minion.

- Download a Windows installer from [the Salt site](repo.saltstack.com/#windows).

- Determine the IP address or DNS name your new minion will use to find your Bevy Master.

- Chose a minion node-id name for your new minion.

- Run the installer and supply the Bevy Master address and node-id when requested.

## Settings and Selections.

The configuration script will store your basic configuration settings in `/srv/pillar/01_settings.sls`.
you will have the option of changing them by re-running the config script 
or by editing the file.

Additional settings for less frequently used items such as PXE boot parameters 
are supplied in `/srv/pillar/manual_bevy_settings.sls`.

#### Additional Bevy Components

A bevy configuration is not mearly a learning tool.
In was originally developed as a test bed for a complex network of backend servers,
and continues in that role.
Therefore, the bevy master is designed to have additional components 
(the servers which comprise an actual useful processing network)
connected to it for it to control.

A small example of such an addition is supplied as 
[black_knight](../lessons/advanced_bevy_master/connecting_a_practical_repo.md).

The [configuration Python script](./bootstrap_bevy_member_here.py) supports two
different configuration options supporting additional components.

* `settings['projects_root']` identifies a single directory under which many source trees
(git repos) might be found. If defined, it will be a Vagrant shared directory
named `/projects` on all VMs defined in `salt-bevy/Vagrantfile`.

* `settings['application_roots']` is more complex and is used for configuration.
It is designed to be used mostly by the salt master.

    It is a list of application repos each of which provides a portion of the complete bevy.
The list is composed of pairs of strings, with the actual directory path
(on the host machine), a semi-colon (';') charactor, and the Vagrant share
path (on a guest machine) where it will be mapped.

    Each application roots directory must contain a `./salt` and `./pillar` sub-directory
which will be included in the bevy master's`file_roots` and `pillar_roots` configuration.

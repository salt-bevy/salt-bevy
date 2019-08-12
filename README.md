# salt-bevy

### Using salt-cloud to learn (or use) SaltStack basics

This project uses a salt-cloud network with Vagrant-controlled VirtualBox virtual machines 
(and others) as a sandbox to experiment with and learn [Salt](https://saltstack.com/) and 
[salt-cloud](https://docs.saltstack.com/en/latest/topics/cloud) 
by building and controlling a bevy[3] of computers.

It can also be used to provision and control a small network of production machines, 
and has provision for linking with and controlling multiple proprietary servers.

See [the Lesson index](lessons/index.md).

### Installation

* Install [git](https://git-scm.com/downloads). If on Linux, use your package manager. 
If on Windows, please select the option to 
"`Use Git and optional Unix tools from the Windows Command Prompt`". It will make your life
easier. Many lessons assume that these utilities are present, and the conflicts with similarly
named DOS commands are rare.  Also select the option to "checkout as-is, commit as-is" so that
git does not foul up any Windows-friendly file's line endings. Python (and Salt) do not care.


* Clone [1] [this git repository](https://github.com/salt-bevy/salt-bevy) onto your target environment --
which should be the workstation where you plan to do the lessons. You will control your bevy
from this place.

    Place it in the `/projects/salt-bevy` directory[2]. Or not -- you don't really have to put it there. 
All lessons should work if you put it somewhere else, like `/home/myusername/learn` or wherever. 
Examples will be configured and tested to operate from any random directory you like.  
But, for simplicity sake, all examples will be given as if they were in `/projects/salt-bevy`.

* Clone the [training files](https://github.com/salt-bevy/training.git) adjacent to your salt-bevy directory.
    so you would place it in '/projects/training'.

* Proceed with the instructions in [/projects/training/lessons/installation/install.md](../training/lessons/installation/install.md).
    * \[Short version: type `bash join-bevy.sh`, or on Windows just type `join-bevy`.\]

Before editing any files in this project,
please switch to a new branch in `git`.

```
git branch my_edits
git checkout my_edits
```

If you need to return to the original text, you can use `git` to restore it.

```git checkout master```

[1]: see [how to git stuff](lessons/git/how_to_git_stuff.md) if you don't understand what "clone" means.

[2]: Windows users -- use the `C:\projects\salt-bevy` folder. 
All future instructions will use POSIX names with right-leaning slashes and no drive letter. Live with it. 
If you need help, look in the [Linux for Windows Users](lessons/windows/Linux_for_Windows_users.md) lesson.

[3]: v v v
### What the #&*$%! is a `bevy`?

In this project, we will use the term "bevy" to specify the collection of virtual (and sometimes physical) computers which are managed by our Salt master.

The Oxford English dictionary says:

```
    bev·y  ˈbevē
    noun
       a large group of people or things of a particular kind.
```

A bevy might have more than one master (if we are using a multi-master arrangement) 
but each master (or set of masters) will control only one bevy. 
The machines in the bevy may reside on any number of IP networks.

#### Why not just call it a `<fill in the blank>` rather than a `bevy`?

Most collective nouns are already used in computer science jargon. "Network" has several meanings -- 
so does "array", "collection", "cluster", "group", "quorum", "environment" and so on. 
The thesarus was searched for a unique, unused term. 
"Bevy" is a collective noun used for quail. (Other terms are "covey" and "flock".)
Being a part-time hunter and full-time westerner, I (Vernon) admire the way a group of quail co-operate together. 
(They are [very pretty](https://www.pfwebsites.org/chapter/snakeriverqforg/photos/002.jpg), too.) 
So I decided to adopt that term for a co-operating group of computers.  Blame me.

Feel free to substitute some other word if you prefer.

### File Name Formats, IDEs and Other Assumptions

In these lessons, you will use both Linux and Windows.
Linux is case sensitive. 
Windows is usually[1] case insensitive, but case preserving.
Some software can get confused when the case changes. 
If you always pretend that file names must be in the exact case, you should have no problems.

For simplicity, we will assume a few things which may be different in your situation.
These are not prerequisites, but merely conventions which you can freely ignore. 
If you chose not to follow the convention, everything should work correctly anyway.
For example, this documentation my refer to `/projects/salt-bevy/lessons/windows/xkcd.py`
but on your system, the file may actually be `C:\Users\Vernon\PyCharmProjects\ls\lessons\windows\xkcd.py`.
You are expected to mentally make the translation between the lesson's examples and your reality.

Things that are optional include:
- your project's root directory node. We assume `/projects/salt-bevy`.
- your [IDE](https://en.wikipedia.org/wiki/Integrated_development_environment). 
We assume [PyCharm Professional](https://www.jetbrains.com/pycharm/), 
but you might use many other choices, such as PyCharm Community Edition, 
[Wing](https://wingware.com/), 
[Visual Studio](https://docs.microsoft.com/en-us/visualstudio/python/installing-python-support-in-visual-studio),
Pythonwin from [pywin32](https://github.com/mhammond/pywin32),
[IDLE](https://docs.python.org/3/library/idle.html),
or even [Notepad++](https://notepad-plus-plus.org/).
But do yourself a favor and select an environment from early, rather than late, in the list.
- Workstation Operating System. Why would anyone use Windows for a programmer's workstation?
But we test with (as of this writing): Ubuntu 17.10, and MacOS High Sierra, and Windows 10.
- Your Bevy_Master machine. As of this writing, we test with Ubuntu 16.04 on a Vagrant VM, 
and Raspbian Jesse on a Raspberry Pi W0.
- Your Internet Router.
Most lessons will be runnable from a large corporate router or an inexpensive home router. 
For some lessons, you will need control over who runs your PXE, DHCP and/or DNS servers. 
Any home-type router should be suitable for that, 
but you may spend some time finding the correct "expert" settings screen.
Examples will be for a router running [MicroTik RouterOS](https://mikrotik.com/software) software.


[1] On Windows, the home directory may be spelled either "C:\Users" or "c:\users", 
but the group must be spelled "Users".
On Linux, the home directory must be spelled "/home" ("/Home" is a different directory) 
and the group must be spelled "users".

##### Prerequisites

Things that are **NOT** optional:
- [Python3](https://www.python.org/) version 3.4 or later. See [the Python clock](https://pythonclock.org/).
- [git](https://git-scm.com/). I hate git. [But, I use it, because Github is great](https://www.python.org/dev/peps/pep-0512/). 
Be careful not to shoot any toes off.

### How this project is arranged.

This directory has this README.md file,
along with a big complex *Vagrantfile*,
and a few other handy files.

- The [lessons](./lessons) directory contains 
the [lesson index](lessons/index.md).  
Often, the lessons will have lab or example files
associated with them. When studying each lesson, you should be running the examples using
a terminal with your current default directory set for that lesson.
For example, if you are running the [Basics of Vagrant](vagrant_basics/basics_of_vagrant.md)
lesson, you should start by typing: 
`cd /projects/salt-bevy/lessons/vagrant_basics`

[comment]: # (The file index.md is the source for index.html)

- The [bevy_srv](./bevy_srv) directory contains a complete SaltStack
directory tree used for building the examples and lessons here.

- The [configure_machine](./configure_machine) directory contains 
scripts used to configure your bevy_master machine, your workstation
(as a minion), and perhaps other bevy member computers as needed.

### How to read the text and lessons.

Various lessons may appear in different formats as dictated by time, the complexity of the
content, and the whim of the author.  Possibilities will include 
[SMART notebooks](https://education.smarttech.com/products/notebook),
[open document (.odp) presentations](http://www.libreoffice.org/discover/impress/), 
html web pages, or markdown pages (like this one.)

You should always be able to read the lessons directly from the links on GitHub --
but will probably have a better experience if you install software on your own
workstation to display the documents locally. Lessons are provided for installing
appropriate programs on Windows and MacOS as well as Linux.  The Linux examples
will assume Ubuntu (or another Debain-based distro such as Raspbian.) If you use a 
different POSIX system, we hope that you are fimiliar with the translation from
Debian commands (apt) to your preferred OS's way of saying the same thing (yum, zypper, 
emerge). *NIX and *BSD users are also invited to read the Linux pages and translate.

Sample shell scripts are provided like

```
    # this is a shell script sample.
    # it should be simple enough to operate on almost any shell language,
    # such as bash, git-bash (on Windows), sh, dash, etcetera.
    ls -al
    echo $PATH
    # you may cut them out and paste them into your command terminal,
    # but you might learn better if you type them with your own fingers.
```

### Vagrant VMs on your workstation

A Vagrantfile is supplied here to create several virtual machines on your workstation. 
(Some lessons may also have a Vagrantfile for that lesson.)

You can create a Salt cloud master ("bevymaster") as a virtual machine on your workstation.
This can be very convenient, except for **one restriction** which occurs if you have any 
application servers (salt minions) running separately from your workstation. 
Minions will be trying to connect to their master at a fixed address. 
If your master should re-connect using a different IP address, they will be lost,
so in that case, will need to consistently use the same network connection for your host workstion,
or use some sort of dynamic DNS arrangement.

The Vagrantfile defines:
| Name | ip | minion? | OS version |
| ---- | -- | ------- | ---------- |
| bevymaster | 2.2 | master | Ubuntu 18.04 |
| quail1 | 2.201 | no | Ubuntu 18.04 |
| quail2 | 2.202 | yes | Ubuntu 18.04 |
| quail14 | 2.214 | no | Ubuntu 14.04 |
| quail16 | 2.216 | no | Ubuntu 16.04 |
| quail18 | 2.218 | no | Ubuntu 18.04 |
| win10 | 2.10 | yes | Windows 10 |
| win12 | 2.12 | yes | Windows Server 2012 |
| win14 | 2.16 | yes | Windows Server 2016 |
| win19 | 2.19 | yes | Windows Server 2019 |
| mac13 | 2.13 | yes | MacOS 10.3 |
| **generic** | 2.200 * | yes | Ubuntu 18.04 * | 
| **generic_no_salt** | 2.200 * | no | Ubuntu 18.04 * |

 \* The "generic" machine can be re-configured using environment variables. See below.

Each machine has three virtual network ports:

- One has a pre-defined IP address range used for a Vagrant host-only network adapter, 
which used to connect a to a Vagrant shared directory, 
for Vagrant to ssh connect to the machine, and for NAT networking. 
As supplied, these will use small subnets of 172.17.17.0.

- A second has a fixed hard-wired address for a
[private network](https://www.vagrantup.com/docs/networking/private_network.html) 
which can be used for intercommunication amoung the host and its virtual machines, 
(and the VMs to each other) but cannot be seen outside the host environment.
These will be in the 172.17.2.0 network, with the host at 172.17.2.1,
and the Bevy Master (if a VM is used) at 172.17.2.2.  
This network can be changed by [the confguration script](configure_machine/README.md).

- The third is a [bridged network](https://www.vagrantup.com/docs/networking/public_network.html) 
which makes the VM appear to be on the same LAN segment as its host. 
The address for this adapter will be assiged by DHCP.
This port can be seen by other machines on your in-house network.  
Be aware that, depending on your IP router configuration settings, VMs on your machine may be
unable to access brother VMs using their bridged addresses.

If you wish, you can add more local VMs by editing the Vagrantfile.

Vagrant requires the name of the interface which will be used for a bridged network.
Since a workstation usually has more than one interface (are you using WiFi or hard wire?)
this can be trick to determine. Vagrant expects to ask the user for input.
There is some Ruby code in the Vagrantfile to try getting the correct name.
The configuration script will try to help you select the correct name, which
will be saved in your configuration pillar file. If you are using MacOS,
this will not work and we will just guess at the two most usual adapters.

#### The "generic" VM

The Vagrantfile defines one virtual machine which can, by manupulation of environment variables, create many named VMs.

Define the environment variable GENERIC (or "generic" for lazy typers) as "True" (or "t") and then type any machine name.
For example:
```
generic=t vagrant up somename
generic=t vagrant ssh somename
generic=t vagrant destroy somename
```

You will need to use the `vagrant global-status` command to see your generic VMs.

Other environment variables can be used to further define the operation of your generic VMs.

- **NODE_ADDRESS** (default=.2.200) the last two octets for the IP address of the machine's host-only network inderface.
- **NODE_MEMORY** (default=5000) the size of virtual memory to allocate for the VM.
- **NODE_BOX** (default= Ubuntu LTS) the Vagrant Box definition for the VM.
```
GENERIC=True NODE_ADDRESS=.2.203 NODE_MEMORY=10000 NODE_BOX=boxesio/xenial64-standard vagrant up anothername
generic=t vagrant ssh anothername
ssh vagrant@172.17.2.203 'ls /home'
```

The `vgr` and `vgr.bat` script commands are provided for convenience in controlling "generic" VMs
from the command line.

Use `generic` or `generic_no_salt` as a key word in your command to have the script define the needed environment variables for you.
The arguments are interpreted as:

`./vgr up generic <node name> <node_address> <node_memory> <node_box> <--switches>`

The `generic_no_salt` keyword is needed only at `vgr up` time to inhibit the provision of a Salt minion.

```bash
./vgr up generic somename "" "" ubuntu/trusty64 --provision
./vgr up generic_no_salt another .2.199 8000  # assigns an address and more RAM
./vgr ssh generic another
./vgr destroy generic somename
```
or, on Windows:
```cmd
vgr up generic somename "" "" ubuntu/trusty64 --provision
# etcetera
```
The `vgr` and `vgr.bat` scripts can also be copied to other projects to operate salt-bevy VMs from different directories.
### Single Source of Truth

 This project attempts to establish a [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
"single source of truth" for your bevy's settings using the file identified with 
`BEVY_SETTINGS_FILE_NAME` (usually `/srv/pillar/01_bevy_settings.sls`). 
On Windows, this would appear as `C:\srv\pillar\01_bevy_settings.sls`.

That file should work in many (but not all) cases. (It can be extended to more cases with some fiddling.)
We will attempt to keep the /srv directory mapped to local Vagrant VMs as "/srv" so the settings will be
seen in both environments. Normal minions will receive their settings from the Bevy Master.
If the Bevy Master is a stand-alone server, it might be a "good idea" to connect its `/srv` directory to
the `/srv` directory on your Workstation using a deployment engine such as PyCharm's.

Machines other than the Bevy Master which are configured individually (using the Python script) will
have their local version of the `bevy_settings` file. These copies will be kept in synchronization
with the Bevy Master's copy by a Salt `file.managed` state command. That way a `salt-call --local`
operation ought to produce the same result as a `salt` operation.

The value of `BEVY_SETTINGS_FILE_NAME` appears as a constant in at least three places in the system code.
If you change it, search for all occurrances.

### A Private Test Network

Most lessons presented here are designed to be good network citizens.
If you keep your bevy names uinque, several bevys can co-exist on a network with no problems.
Even hardware MAC addresses (where needed) are hashed by the bevy name.

However, if you wish to run the more advanced network infrastructure lessons
(such as DHCP and PXE) plan also to buy some hardware.

Some lessons will contain warnings if they cannot be run on a corporate or
school network without messing something up.
\[Trust me, I know about messing things up -- I once killed the then-experimental
Internet in all of Utah and Colorado by misconfiguring a router. -- Vernon\] 


If you are working from a home office, you should be okay using your home router
for the advanced lessons (but not while your spouse is streaming a movie).

Otherwise, you will want a router of your very own for the advanced lessons.
Consider ordering a special router soon. I use a RouterBoard / Mikrotik
[hAP lite](https://mikrotik.com/product/RB941-2nD-TC).
Their RouterOS operating system has professional features lacking in most popular home routers.
I found mine on Amazon for less than $30 USD. Buy some CAT-5 cables, too.

For test computers on my private network, I use an old HP laptop that once ran Windows Vista, and a Raspberry Pi 3.
Also running on my test net, I have two development Ubuntu laptops, a Windows 10 laptop,
an old MacBook, and my Android phone.

# Updating this project.

 If you wish to customize or improve this project, create a fork of the source.
 In [the source repository](https://github.com/salt-bevy/salt-bevy)
 you should see a `Fork` button in the upper right corner.  Click it.

 To submit updates, please follow the flow used for SaltStack, as suggested in
 [Developing Salt](https://docs.saltstack.com/en/latest/topics/development/contributing.html#sending-a-github-pull-request).

You can compile markdown (.md) files into .html using [ReText](https://github.com/retext-project/retext)

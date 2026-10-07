# -*- mode: ruby -*-
# vi: set ft=ruby :
#  .  .  .  .  NOTE  .  .  .  .
# This configuration file is written in Ruby.
# I invested one entire day in learning Ruby,
# so if this is not particularly good Ruby code, I'm sorry.
# -- vernondcole 2017 .  .  .  .
require "etc"
require "yaml"
require "ipaddr"

SALT_BOOTSTRAP_ARGUMENTS = "" # for example "git v2019.2.0rc1"  # (usually leave blank for latest production Salt version)
DEFAULT_BOX = "salt-bevy/ubuntu-26.04"  # the vagrantbox to use for most VMs below
# ^ built locally via "packer/build_boxes.py" (see packer/README.md) rather than pulled from
# Vagrant Cloud, which is being retired. Register it for whichever provider(s) you use --
# build_boxes.py auto-detects installed hypervisors and builds/registers all of them under
# this same box name, so Vagrant picks the right one automatically based on --provider.
# a local, BOM-free copy of salt-bootstrap's windows script -- Vagrant 2.4.9's built-in
# downloader has a UTF-8 BOM baked into its WINDOWS_URL constant, which makes Ruby's
# URI parser choke with "URI must be ascii only"; pointing bootstrap_script at this file
# skips that downloader entirely.
WINDOWS_SALT_BOOTSTRAP_SCRIPT = File.expand_path('windows_bootstrap_salt.ps1', __dir__)

vagrant_command = ARGV[0]
vagrant_object = ARGV.length > 1 ? ARGV[1] : ""  # the name (if any) of the vagrant VM for this command

def requested_provider(argv)  # best-effort guess at which provider "vagrant up" will use
  argv.each_with_index do |arg, i|
    return arg.split('=', 2)[1] if arg.start_with?('--provider=')
    return argv[i + 1] if arg == '--provider' and argv.length > i + 1
  end
  return ENV['VAGRANT_DEFAULT_PROVIDER'] unless ENV['VAGRANT_DEFAULT_PROVIDER'].to_s.empty?
  'virtualbox'  # Vagrant's traditional default when nothing else says otherwise
end
ACTIVE_PROVIDER = requested_provider(ARGV)
#
# under the DRY principle, the most important setting are stored
# in a Salt 'pillar' file. Vagrant has to look them up there...
#
# . v . v . retrieve stored bevy settings . v . v . v . v . v . v .
if (RUBY_PLATFORM=~/darwin/i)  # on MacOS 10.15 and later we cannot use /srv
  SRV_ROOT = '/opt/saltdata'
else  # Windows or Linux
  SRV_ROOT = '/srv'
end
def name_bevy_settings_file(rootpath)
  return File.join(rootpath, 'pillar', '01_bevy_settings.sls')
end
BEVY_SETTINGS_FILE_NAME = name_bevy_settings_file(SRV_ROOT)  # settings for the entire bevy
MY_SETTINGS_FILE_NAME = '/etc/salt-bevy/my_settings.conf'  # settings specific to the current host machine
if File.exist?(BEVY_SETTINGS_FILE_NAME)
  settings = YAML.load_file(BEVY_SETTINGS_FILE_NAME)  # get your bevy-wide settings
  default_run_highstate = true
else  # the bevy settings file was not found. We must supply simple default settings here.
  if vagrant_command == "up"
    puts "\n*  ERROR:  Unable to read settings file #{BEVY_SETTINGS_FILE_NAME}."
    puts "*  NOTICE: Using default bevy settings for MASTERLESS Salt operation."
    puts "*  NOTICE: Some features will be missing."
    puts "*  SUGGESTION: You should run 'configure_machine/bootstrap_bevy_member_here.py' before running 'vagrant up'.\n\n"
    end
  settings = {"bevy" => "local", "vagrant_prefix" => '172.17', "vagrant_interface_guess" => "eth0",
   "master_vagrant_ip" => 'localhost', "my_linux_user" => 'vagrant', "my_windows_user" => 'vagrant',
   "my_windows_password" => 'vagrant', "fqdn_pattern" => '{}.{}.test', "force_linux_user_password" => false,
   "linux_password_hash" => '$6$1cd1ac861859996c$Qk4jvU/HL/0bm0MMuLtFnyGeZIIxXb8VSVSr3170eGGB4LH9aXAtp980YFDohi2wE/jQZeqWLbXi1l.yZCchz1',
   "GUEST_MINION_CONFIG_FILE" => __dir__ + '/configure_machine/masterless_minion.conf',
   "WINDOWS_GUEST_CONFIG_FILE" => __dir__ + '/configure_machine/masterless_minion.conf',
   }
  default_run_highstate = false
end
if File.exist?(MY_SETTINGS_FILE_NAME)
  my_settings = YAML.load_file(MY_SETTINGS_FILE_NAME)  # get your local settings
  # YAML.load_file returns nil for a file with only comments/no data (e.g. a
  # bootstrap_bevy_member_here.py run that never got any actual settings
  # written in) -- merge! would raise "no implicit conversion of nil into
  # Hash" in that case, so only merge when there's really a Hash to merge.
  settings.merge!(my_settings) if my_settings.is_a?(Hash)  # local settings override the bevy settings.
else
  puts "  NOTICE: Unable to read local settings file #{MY_SETTINGS_FILE_NAME}."
end
# .
BEVY = settings["bevy"]  # the name of your bevy
# the first two bytes of your Vagrant host-only network IP ("192.168.x.x")
NETWORK = "#{settings['vagrant_prefix']}"
# ^ ^ each VM below will have a NAT network in NETWORK.17.x/27 or NETWORK.18.x/27
#
# . v . v . Hyper-V settings . v . v .
QUAIL22_BOX = "generic/ubuntu2204"  # Ubuntu 22.04, actively maintained; publishes virtualbox, vmware, hyperv, libvirt & qemu providers
# Hyper-V cannot create switches from Vagrant and ignores static private_network IPs, so we
# bridge to an existing External Virtual Switch instead (create it first in Hyper-V Manager
# > Virtual Switch Manager) and let DHCP assign the guest's address.
HYPERV_SWITCH = ENV['HYPERV_SWITCH'] || settings['hyperv_switch'] || "Default Switch"
# salt22's masterless minion reads /srv/salt + /srv/pillar/django.sls from
# the palmtree/django app repo -- see the sync provisioner in salt22's
# block for why this can't rely on that repo's own git.latest state
# anymore. Sibling checkout by default (this repo and django live next to
# each other under PycharmProjects on vcole-admin's workstation);
# overridable since that layout isn't guaranteed elsewhere.
DJANGO_REPO_ROOT = ENV['DJANGO_REPO_ROOT'] || settings['django_repo_root'] || File.expand_path('../django', __dir__)
# Same idea as DJANGO_REPO_ROOT, for win11's masterless minion -- see win11's
# block for why it copies this repo's srv/salt + srv/pillar in directly
# rather than relying on the shared bevy_srv tree.
WINDOWS_SUDO_REPO_ROOT = ENV['WINDOWS_SUDO_REPO_ROOT'] || settings['windows_sudo_repo_root'] || File.expand_path('../windows-sudo', __dir__)
puts "Your bevy name:#{BEVY} with host-only network #{NETWORK}.x.x"
puts "This (the VM host) computer will be at #{NETWORK}.56.1" if ARGV[1] == "up"
bevy_mac = (BEVY.to_i(36) % 0x1000000).to_s(16).rjust(6, '0')  # a MAC address based on hash of BEVY
# in Python that would be: bevy_mac = format(int(BEVY, base=36) % 0x1000000, 'x')
#
VAGRANT_HOST_NAME = Socket.gethostname
login = Etc.getlogin    # get your own user information
my_linux_user = settings['my_linux_user']
my_linux_user = login if my_linux_user.to_s.empty?  # use current value if settings gives blank.
HASHFILE_NAME = 'bevy_linux_password.hash'  # filename for your Linux password hash
hash_path = File.join(Dir.home, '.ssh', HASHFILE_NAME)  # where you store it ^ ^ ^
#
# . v . v . the real Vagrantfile program starts here . v . v . v . v . v . v . v . v . v .
#
# Bridged networks make the machine appear as another physical device on your network.
# We try to supply a list of names to avoid Vagrant asking for interactive input
#
if (RUBY_PLATFORM=~/darwin/i)  # on Mac OS, guess some frequently used ports
  interface_guesses = ['en0: Ethernet', 'en1: Wi-Fi (AirPort)',  'en0: Wi-Fi (Wireless)']
else  # Windows or Linux
  interface_guesses = settings['vagrant_interface_guess']
end
if vagrant_command == "up" or vagrant_command == "reload"
  puts "Running on host #{VAGRANT_HOST_NAME}"
  puts "Will try bridge network using interface(s): #{interface_guesses}"
end

max_cpus = Etc.nprocessors / 2 - 1
max_cpus = 1 if max_cpus < 1

Vagrant.configure(2) do |config|  # the literal "2" is required.

   config.ssh.forward_agent = true

  unless vagrant_object.start_with? 'win'
    config.vm.provision "shell", inline: "ifconfig || ip addr", run: "always"  # what did we get?
  end

  # Now ... just in case our user is running some flavor of VMWare, we will
  # set up his VM, too. But first we need to discover his Host OS ...
  if (/darwin/ =~ RUBY_PLATFORM) != nil
    vmware = "vmware_fusion"
  else
    vmware = "vmware_workstation"
  end

  if ENV.key?("VAGRANT_PWD")
    config.vm.synced_folder ENV["VAGRANT_PWD"], "/vagrant", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
  end
  if ENV.key?("VAGRANT_CWD")
    vcwd = File.expand_path(ENV['VAGRANT_CWD'])
    config.vm.synced_folder vcwd, "/salt_bevy", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
  end
  if settings.has_key?('projects_root') and settings['projects_root'] != 'none'
    config.vm.synced_folder settings['projects_root'], "/projects", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
  end

  config.vm.synced_folder File.join(SRV_ROOT, 'pillar'), "/srv/pillar", :owner => "vagrant", :group => "staff"  #, :mount_options => ["umask=0002"]

  if ENV.key?("VAGRANT_SALT")
    as_minion = "as a Salt minion with master=#{settings['master_vagrant_ip']}"
  else
    as_minion = ""
  end

  # . . . . . . . . . . . . Define machine QUAIL1 . . . . . . . . . . . . . .
  # This machine has no Salt provisioning at all. Salt-cloud can provision it.
  config.vm.define "quail1", primary: true do |quail_config|  # this will be the default machine
    quail_config.vm.hostname = "quail1" # + DOMAIN
    quail_config.vm.box = DEFAULT_BOX
    if ACTIVE_PROVIDER == "hyperv"
      # Hyper-V cannot create switches from Vagrant and ignores static private_network IPs
      # (see HYPERV_SWITCH above) -- bridge to the configured Hyper-V switch instead.
      quail_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and (ARGV.length == 1 or (vagrant_object == "quail1"))
        puts "Starting 'quail1' under Hyper-V, bridged to switch '#{HYPERV_SWITCH}'..."
      end
    else
      quail_config.vm.network "private_network", ip: NETWORK + ".56.201"  # needed so saltify_profiles.conf can find this unit
      quail_config.vm.network "public_network", bridge: interface_guesses
      if vagrant_command == "up" and (ARGV.length == 1 or (vagrant_object == "quail1"))
        puts "Starting 'quail1' at #{NETWORK}.56.201..."
      end
    end
    quail_config.vm.provider "virtualbox" do |v|  # only for VirtualBox boxes
        v.name = BEVY + '_quail1'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.0/27"]  # do not use 10.0 network for NAT
	    #                                                     ^  ^/27 is the smallest network allowed.
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|  # only for VMware boxes
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	  end
    quail_config.vm.provider "hyperv" do |v|  # only for Hyper-V boxes
        v.vmname = BEVY + '_quail1'  # ! N.O.T.E.: name must be unique
        v.memory = 1024
        v.maxmemory = 1024
        v.cpus = 1
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
  end

  # . . . . . . . . . . . . Define machine QUAIL22 . . . . . . . . . . . . . .
  # Same idea as quail1 (no Salt provisioning), but pinned to QUAIL22_BOX
  # (Ubuntu 22.04) instead of switching boxes by provider, since that one
  # box already publishes a real Hyper-V provider on its own.
  config.vm.define "quail22", autostart: false do |quail_config|
    quail_config.vm.hostname = "quail22" # + DOMAIN
    quail_config.vm.box = QUAIL22_BOX
    # Disable the synced folders set up above (config.vm.synced_folder on the top-level `config`).
    # Under Hyper-V, Vagrant falls back to an SMB-backed synced folder, which requires interactively
    # creating a host SMB share and entering credentials — skip that entirely for this machine.
    quail_config.vm.synced_folder ".", "/vagrant", disabled: true
    quail_config.vm.synced_folder ".", "/salt_bevy", disabled: true
    quail_config.vm.synced_folder ".", "/projects", disabled: true
    quail_config.vm.synced_folder ".", "/srv/pillar", disabled: true
    if ACTIVE_PROVIDER == "hyperv"
      quail_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and vagrant_object == "quail22"
        puts "Starting 'quail22' under Hyper-V, bridged to switch '#{HYPERV_SWITCH}'..."
      end
    else
      quail_config.vm.network "private_network", ip: NETWORK + ".56.222"
      quail_config.vm.network "public_network", bridge: interface_guesses
      if vagrant_command == "up" and vagrant_object == "quail22"
        puts "Starting 'quail22' at #{NETWORK}.56.222..."
      end
    end
    quail_config.vm.provider "virtualbox" do |v|  # only for VirtualBox boxes
        v.name = BEVY + '_quail22'  # ! N.O.T.E.: name must be unique
        v.memory = 10240      # limit memory for the virtual box
        v.cpus = 6
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".63.0/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|  # only for VMware boxes
        v.vmx["memsize"] = "10240"
        v.vmx["numvcpus"] = "6"
	  end
    quail_config.vm.provider "hyperv" do |v|  # only for Hyper-V boxes
        v.vmname = BEVY + '_quail22'  # ! N.O.T.E.: name must be unique
        v.memory = 10240      # limit memory for the VM
        v.maxmemory = 10240
        v.cpus = 6
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
    # /srv/pillar isn't synced-folder-mounted here (see the disabled synced folders above), so
    # copy the host's pillar tree in as a one-time upload instead of a live mount.
    if Dir.exist?(File.join(SRV_ROOT, 'pillar'))
      quail_config.vm.provision "file", source: File.join(SRV_ROOT, 'pillar'), destination: "/tmp/host_pillar", run: "always"
      quail_config.vm.provision "shell", path: "configure_machine/copy_host_pillar_to_guest.sh", run: "always"
    end
    # ddclient/DDNS provisioning for quail22.2tst.xyz was removed 2026-10-04: the 2tst.xyz
    # zone moved to PowerDNS-primary-on-fremont on 2026-09-16, which silently broke HE.net
    # dyndns2 updates, and quail22 itself is inactive. See the "Dynamic DNS setup" memory.
  end

  # . . . . . . . . . . . . Define machine SALT22 . . . . . . . . . . . . . .
  # A copy of quail22 (same QUAIL22_BOX, same disabled-synced-folder / one-time
  # pillar-copy setup) plus a masterless Salt minion — since it's masterless,
  # the pillar copy above is what makes its pillar_roots data available at all.
  config.vm.define "salt22", autostart: false do |quail_config|
    quail_config.vm.hostname = "salt22" # + DOMAIN
    quail_config.vm.box = QUAIL22_BOX
    # Disable the synced folders set up above (config.vm.synced_folder on the top-level `config`).
    # Under Hyper-V, Vagrant falls back to an SMB-backed synced folder, which requires interactively
    # creating a host SMB share and entering credentials — skip that entirely for this machine.
    quail_config.vm.synced_folder ".", "/vagrant", disabled: true
    quail_config.vm.synced_folder ".", "/salt_bevy", disabled: true
    quail_config.vm.synced_folder ".", "/projects", disabled: true
    quail_config.vm.synced_folder ".", "/srv/pillar", disabled: true
    if ACTIVE_PROVIDER == "hyperv"
      quail_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and vagrant_object == "salt22"
        puts "Starting 'salt22' under Hyper-V, bridged to switch '#{HYPERV_SWITCH}'..."
      end
    else
      quail_config.vm.network "private_network", ip: NETWORK + ".56.223"
      quail_config.vm.network "public_network", bridge: interface_guesses
      if vagrant_command == "up" and vagrant_object == "salt22"
        puts "Starting 'salt22' at #{NETWORK}.56.223..."
      end
    end
    quail_config.vm.provider "virtualbox" do |v|  # only for VirtualBox boxes
        v.name = BEVY + '_salt22'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".63.96/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|  # only for VMware boxes
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	  end
    quail_config.vm.provider "hyperv" do |v|  # only for Hyper-V boxes
        v.vmname = BEVY + '_salt22'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the VM
        v.cpus = 1
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
    # /srv/pillar isn't synced-folder-mounted here (see the disabled synced folders above), so
    # copy the host's pillar tree in as a one-time upload instead of a live mount — the masterless
    # minion below reads its pillar from here.
    if Dir.exist?(File.join(SRV_ROOT, 'pillar'))
      quail_config.vm.provision "file", source: File.join(SRV_ROOT, 'pillar'), destination: "/tmp/host_pillar", run: "always"
      quail_config.vm.provision "shell", path: "configure_machine/copy_host_pillar_to_guest.sh", run: "always"
    end
    # ddclient/DDNS provisioning for salt22.2tst.xyz was removed 2026-10-04: the 2tst.xyz
    # zone moved to PowerDNS-primary-on-fremont on 2026-09-16, which silently broke HE.net
    # dyndns2 updates, and salt22 itself is inactive. See the "Dynamic DNS setup" memory.
    script = "mkdir -p /etc/salt/minion.d\n"
    script += "chown -R vagrant:staff /etc/salt/minion.d\n"
    script += "chmod -R 775 /etc/salt/minion.d\n"
    quail_config.vm.provision "shell", inline: script
    # Refresh /srv/salt + /srv/pillar (what the masterless minion actually
    # reads) directly from DJANGO_REPO_ROOT on the host. Used to go through
    # configure_machine/sync_app_salt_states.sh, copying from
    # /opt/palmtree/srv on the guest -- but that only ever gets created by
    # the django app's own git.latest state, which is scoped to
    # ndf.2tst.xyz only (see django/srv/salt/top.sls), so it never ran here
    # and /srv/salt silently never got refreshed at all. Copying straight
    # from the host sidesteps needing the app deployed here in the first
    # place. Must run before the salt provisioner, and every time (not
    # just on first boot).
    if Dir.exist?(File.join(DJANGO_REPO_ROOT, 'srv', 'salt'))
      quail_config.vm.provision "file", source: File.join(DJANGO_REPO_ROOT, 'srv', 'salt'),
                                destination: "/tmp/django_srv_salt", run: "always"
      quail_config.vm.provision "file", source: File.join(DJANGO_REPO_ROOT, 'srv', 'pillar', 'django.sls'),
                                destination: "/tmp/django_pillar_django.sls", run: "always"
      quail_config.vm.provision "file", source: File.join(DJANGO_REPO_ROOT, 'srv', 'pillar', 'top.sls'),
                                destination: "/tmp/django_pillar_top.sls", run: "always"
      quail_config.vm.provision "shell", run: "always", inline: <<-SHELL
        set -e
        sudo mkdir -p /srv/salt /srv/pillar
        sudo cp -a /tmp/django_srv_salt/. /srv/salt/
        sudo cp /tmp/django_pillar_django.sls /srv/pillar/django.sls
        sudo cp /tmp/django_pillar_top.sls /srv/pillar/top.sls
        rm -rf /tmp/django_srv_salt /tmp/django_pillar_django.sls /tmp/django_pillar_top.sls
      SHELL
    end
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|
       salt.verbose = false
       salt.bootstrap_options = "-A #{settings['master_vagrant_ip']} -i salt22 -F -P #{SALT_BOOTSTRAP_ARGUMENTS}"
       salt.run_highstate = default_run_highstate
       salt.masterless = true
       if settings.has_key?('GUEST_MINION_CONFIG_FILE') and File.exist?(settings['GUEST_MINION_CONFIG_FILE'])
         salt.minion_config = settings['GUEST_MINION_CONFIG_FILE']
       end
      end
    end
  end

# . . . . . . .  Define quail2 with Salt minion installed . . . . . . . . . . . . . .
# . this machine bootstraps Salt but no states are run or defined.
# . Its master is "bevymaster".
  config.vm.define "quail2", autostart: false do |quail_config|
    quail_config.vm.box = DEFAULT_BOX
    quail_config.vm.hostname = "quail2" # + DOMAIN
    if ACTIVE_PROVIDER == "hyperv"
      # Hyper-V cannot create switches from Vagrant and ignores static private_network IPs
      # (see HYPERV_SWITCH above) -- bridge to the configured Hyper-V switch instead.
      quail_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and vagrant_object == "quail2"
        puts "Starting #{vagrant_object} under Hyper-V, bridged to switch '#{HYPERV_SWITCH}' #{as_minion}..."
      end
    else
      quail_config.vm.network "private_network", ip: NETWORK + ".56.202"
      quail_config.vm.network "public_network", bridge: interface_guesses
      if vagrant_command == "up" and vagrant_object == "quail2"
        puts "Starting #{vagrant_object} at #{NETWORK}.56.202 #{as_minion}...\n."
      end
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quail2'  # ! N.O.T.E.: name must be unique
        v.memory = 4000       # limit memory for the virtual box
        v.cpus = max_cpus
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.160/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "5000"
        v.vmx["numvcpus"] = "2"
    end
    quail_config.vm.provider "hyperv" do |v|
        v.vmname = BEVY + '_quail2'  # ! N.O.T.E.: name must be unique
        v.memory = 4000
        v.maxmemory = 4000
        v.cpus = max_cpus
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
    script = "mkdir -p /etc/salt/minion.d\n"
    script += "chown -R vagrant:staff /etc/salt/minion.d\n"
    script += "chmod -R 775 /etc/salt/minion.d\n"
    quail_config.vm.provision "shell", inline: script
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|
       salt.verbose = false
       salt.bootstrap_options = "-A #{settings['master_vagrant_ip']} -i quail2 -F -P #{SALT_BOOTSTRAP_ARGUMENTS}"
       salt.run_highstate = default_run_highstate
       salt.masterless = true
       if settings.has_key?('GUEST_MINION_CONFIG_FILE') and File.exist?(settings['GUEST_MINION_CONFIG_FILE'])
         salt.minion_config = settings['GUEST_MINION_CONFIG_FILE']
       end
      end
    end
  end

# . . . . . . .  Define a generic machine with Salt minion installed . . . . . . . . . . . . . .
# . Its name will be what ever name was typed on the command line.
# . created by a command like:
# . generic=t ./vgr up somename
# . Define the network address and VM memory size like:
# . GENERIC=True NODE_ADDRESS=.56.203 NODE_MEMORY=10000 NODE_BOX=ubuntu/jammy64 ./vgr up somename
#
  generic = ENV["GENERIC"] || ENV['generic']
  if generic and generic.downcase.chars.first == "t" then
    if vagrant_object == "" and vagrant_command == "up" then
      puts "ERROR: You must specify a new machine id when environment variable GENERIC=True."
      raise "Command Line Error triggered."
    end
    node_id = vagrant_object
    node_address = ENV.fetch("NODE_ADDRESS", ".56.200")
    node_memory = ENV.fetch("NODE_MEMORY", "5000")
    node_box = ENV.fetch("NODE_BOX", DEFAULT_BOX)
    config.vm.define node_id, autostart: false do |quail_config|
      quail_config.vm.box = node_box
      quail_config.vm.hostname = node_id # + DOMAIN
      quail_config.vm.network "private_network", ip: NETWORK + node_address
      if vagrant_command == "up"
        puts "generic box=#{node_box} memory=#{node_memory}"
        puts "Starting #{node_id} at #{NETWORK}#{node_address} #{as_minion}...\n."
      end
      quail_config.vm.network "public_network", bridge: interface_guesses
      quail_config.vm.provider "virtualbox" do |v|
          v.name = BEVY + '_' + node_id  # ! N.O.T.E.: name must be unique
          v.memory = node_memory.to_i    # memory size for the virtual box
          v.cpus = max_cpus
          v.linked_clone = true # make a soft copy of the base Vagrant box
          v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.0/27"]  # do not use 10.0 network for NAT
          v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
      end
      script = "mkdir -p /etc/salt/minion.d\n"
      script += "chown -R vagrant:staff /etc/salt/minion.d\n"
      script += "chmod -R 775 /etc/salt/minion.d\n"
      quail_config.vm.provision "shell", inline: script
      if ENV.key?("VAGRANT_SALT")
        quail_config.vm.provision :salt do |salt|
           salt.verbose = true
           salt.bootstrap_options = "-A #{settings['master_vagrant_ip']} -i #{node_id} -F -P #{SALT_BOOTSTRAP_ARGUMENTS}"
           salt.run_highstate = default_run_highstate
           salt.masterless = true
           if settings.has_key?('GUEST_MINION_CONFIG_FILE') and File.exist?(settings['GUEST_MINION_CONFIG_FILE'])
             salt.minion_config = settings['GUEST_MINION_CONFIG_FILE']
           end
        end
      end
    end
  end

# . . . . . . .  Define the BEVYMASTER . . . . . . . . . . . . . . . .
# This is the Vagrant version of a Bevy Salt-master.
# You cannot run it if you are using an external bevymaster.
  config.vm.define "bevymaster", autostart: false do |master_config|
    master_config.vm.box = DEFAULT_BOX  # self-built for hyperv/virtualbox/vmware -- see DEFAULT_BOX above
    master_config.vm.hostname = "bevymaster"
    if vagrant_command == "up" and vagrant_object == "bevymaster" and ACTIVE_PROVIDER != 'hyperv'
      if settings['master_vagrant_ip'] != NETWORK + ".56.2"
        # prevent running a Vagrant bevy master if another is in use.
        abort "Sorry. Your master_vagrant_ip setting of '#{settings['master_vagrant_ip']}' suggests that your Bevy Master is not expected to be Virtual here."
      end
    end
    if ACTIVE_PROVIDER == "hyperv"
      # Same reasoning as quail22/salt22: Hyper-V cannot create switches from
      # Vagrant and ignores static private_network IPs, so bridge to an
      # existing External Virtual Switch instead of the private_network call
      # below.
      master_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and vagrant_object == "bevymaster"
        puts "Starting 'bevymaster' under Hyper-V, bridged to switch '#{HYPERV_SWITCH}'..."
      end
      # Also as with quail22/salt22: under Hyper-V, Vagrant falls back to an
      # SMB-backed synced folder, which requires interactively creating a
      # host SMB share and entering credentials -- skip that for ALL FOUR
      # top-level synced folders defined above (/vagrant, /salt_bevy,
      # /projects, /srv/pillar), not just /vagrant. /salt_bevy and
      # /projects are pure developer-convenience mounts nothing here reads,
      # safe to just drop. /srv/pillar gets the same one-time host-pillar
      # copy quail22/salt22 already use. /vagrant itself is NOT needed
      # wholesale -- only bevy_root (/vagrant/bevy_srv, see the pillar
      # below) is ever actually read -- so copy just that subdirectory
      # rather than the whole repo (SCPing the full checkout, including
      # .git/.vagrant/.idea, was too much for a single "file" provisioner
      # upload and failed outright).
      master_config.vm.synced_folder ".", "/vagrant", disabled: true
      master_config.vm.synced_folder ".", "/salt_bevy", disabled: true
      master_config.vm.synced_folder ".", "/projects", disabled: true
      master_config.vm.synced_folder ".", "/srv/pillar", disabled: true
      master_config.vm.provision "file", source: "./bevy_srv", destination: "/tmp/bevy_srv_copy", run: "always"
      master_config.vm.provision "shell", run: "always", inline:
        "sudo mkdir -p /vagrant/bevy_srv && sudo cp -a /tmp/bevy_srv_copy/. /vagrant/bevy_srv/ && rm -rf /tmp/bevy_srv_copy"
      if Dir.exist?(File.join(SRV_ROOT, 'pillar'))
        master_config.vm.provision "file", source: File.join(SRV_ROOT, 'pillar'), destination: "/tmp/host_pillar", run: "always"
        master_config.vm.provision "shell", path: "configure_machine/copy_host_pillar_to_guest.sh", run: "always"
      end
      # ddclient/DDNS provisioning for #{BEVY}_bevymaster.2tst.xyz was removed 2026-10-04:
      # the 2tst.xyz zone moved to PowerDNS-primary-on-fremont on 2026-09-16, which silently
      # broke HE.net dyndns2 updates, and this bevymaster test VM itself is inactive. See the
      # "Dynamic DNS setup" project memory.
    else
      master_config.vm.network "private_network", ip: NETWORK + ".56.2"
      master_config.vm.network "public_network", bridge: interface_guesses, mac: "ae1100" + bevy_mac
      master_config.vm.synced_folder ".", "/vagrant", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
    end
    #if vagrant_command == "ssh"
    #  master_config.ssh.username = my_linux_user  # if you type "vagrant ssh", use this username
    #  master_config.ssh.private_key_path = Dir.home() + "/.ssh/id_rsa"
    #end
    master_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_bevymaster'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.32/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    master_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	  end
    master_config.vm.provider "hyperv" do |v|  # only for Hyper-V boxes
        v.vmname = BEVY + '_bevymaster'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the VM
        v.maxmemory = 1024    # see quail22's maxmemory comment: avoids a
                               # Vagrant 2.4.9 hyperv provider scoping bug
        v.cpus = 1
        v.mac = "ae1100" + bevy_mac
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
    script = "mkdir -p /etc/salt/minion.d\n"
    script += "chown -R vagrant:staff /etc/salt/minion.d\n"
    script += "chmod -R 775 /etc/salt/minion.d\n"
    master_config.vm.provision "shell", inline: script
    if settings.has_key?('GUEST_MASTER_CONFIG_FILE') and File.exist?(settings['GUEST_MASTER_CONFIG_FILE'])
      master_config.vm.provision "file", source: settings['GUEST_MASTER_CONFIG_FILE'],
                                destination: "/etc/salt/minion.d/00_bevy_boot.conf"
    end
    master_config.vm.provision :salt do |salt|
       # salt.install_type = "stable 3006.7"
       salt.verbose = true
       salt.log_level = "info"
       salt.colorize = true
       # -i bevymaster: every other :salt provisioner block in this file pins
       # its minion id explicitly -- this one didn't, and Salt caches
       # whatever id it derives (from the hostname at first bootstrap) into
       # /etc/salt/minion_id permanently, never re-deriving it later even if
       # the hostname is fixed afterward. Confirmed on a live box: the OS
       # hostname was correctly "bevymaster" (config.vm.hostname took
       # effect), but salt-call still reported id "ubuntu2204.localdomain"
       # (QUAIL22_BOX's default) because bootstrap had already run and
       # cached it before hostname-setting ever got there -- so top.sls's
       # 'bevymaster'/'local' entries never matched, and the actual
       # salt-master/cloud-controller setup never ran.
       salt.bootstrap_options = "-i bevymaster -P -M -L #{SALT_BOOTSTRAP_ARGUMENTS}"  # install salt-cloud and salt-master
       salt.masterless = true  # the provisioning script for the master is masterless
       salt.run_highstate = true
       password_hash = settings['linux_password_hash']
       info = Etc.getpwnam(login)
       if settings
         uid = settings['my_linux_uid']
         gid = settings['my_linux_gid']
       elsif info  # info is Null on Windows boxes
         uid = info.uid
         gid = info.gid
       else
         uid = ''
         gid = ''
       end
       salt.pillar({ # configure a new interactive user on the new VM
         "my_linux_user" => my_linux_user,
         "my_linux_uid" => uid,
         "my_linux_gid" => gid,
         "bevy_root" => "/vagrant/bevy_srv",
         "bevy" => BEVY,
         "master_vagrant_ip" => NETWORK + '.56.2',
         "additional_minion_tag" => '',
         "linux_password_hash" => password_hash,
         "force_linux_user_password" => true,
         "runas" => login,
         "cwd" => Dir.pwd,
         "server_role" => 'master',
         "doing_bootstrap" => true,  # flag for Salt state system
         })
    end
  end


# . . . . . . . . . . . . Define machine QUAIL20 . . . . . . . . . . . . . .
# This Ubuntu 14.04 machine is designed to be run by salt-cloud
  config.vm.define "quail20", autostart: false do |quail_config|
    quail_config.vm.box = "ubuntu/focal64"
    quail_config.vm.hostname = "quail20" # + DOMAIN
    quail_config.vm.network "private_network", ip: NETWORK + ".56.220"
    if vagrant_command == "up" and vagrant_object == "quail20"
      puts "Starting #{vagrant_object} at #{NETWORK}.56.214..."
    end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quail20'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.96/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
	end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	  end
  end

# . . . . . . . . . . . . Define machine QUAIL24 . . . . . . . . . . . . . .
# Ubuntu 24.04, self-built (see packer/README.md) -- no Salt provisioning; salt-cloud can
# provision it, same as quail1.
  config.vm.define "quail24", autostart: false do |quail_config|
    quail_config.vm.hostname = "quail24" # + DOMAIN
    quail_config.vm.box = "salt-bevy/ubuntu-24.04"
    if ACTIVE_PROVIDER == "hyperv"
      quail_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and vagrant_object == "quail24"
        puts "Starting 'quail24' under Hyper-V, bridged to switch '#{HYPERV_SWITCH}'..."
      end
    else
      quail_config.vm.network "private_network", ip: NETWORK + ".56.224"
      quail_config.vm.network "public_network", bridge: interface_guesses
      if vagrant_command == "up" and vagrant_object == "quail24"
        puts "Starting 'quail24' at #{NETWORK}.56.224..."
      end
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quail24'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.64/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
    end
    quail_config.vm.provider "hyperv" do |v|
        v.vmname = BEVY + '_quail24'  # ! N.O.T.E.: name must be unique
        v.memory = 1024
        v.maxmemory = 1024
        v.cpus = 1
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
  end

 # . . . . . . . . . . . . Define machine win10 . . . . . . . . . . . . . .
 # . this Windows 10 machine bootstraps Salt.
  config.vm.define "win10", autostart: false do |quail_config|
    quail_config.vm.box = "StefanScherer/windows_10"  #"Microsoft/EdgeOnWindows10"
    # <#this causes Windows to restart#> # quail_config.vm.hostname = 'win10'
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.network "private_network", ip: NETWORK + ".56.10"
    if vagrant_command == "up" and vagrant_object == "win10"
      puts "Starting #{vagrant_object} #{as_minion}."
      puts ""
      puts "NOTE: you may need to run \"vagrant up\" twice for this Windows minion."
      puts ""
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win10'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "33"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.192/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
        v.customize ["storageattach", :id, "--storagectl", "IDE Controller", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", "emptydrive"]
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 900
    quail_config.vm.graceful_halt_timeout = 90
    #quail_config.winrm.password = "Passw0rd!"
    #quail_config.winrm.username = "IEUser"
    script = "new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue\r\n"
    quail_config.vm.provision "shell", inline: script
    # masterless_minion.conf (uploaded below as the main minion config) points
    # file_roots/pillar_roots at POSIX paths (/srv/salt, /vagrant/bevy_srv/salt)
    # that don't exist on a Windows guest, which is why highstate reports "No
    # Top file... found" -- copy this repo's own bevy_srv/salt + bevy_srv/pillar
    # in directly and override file_roots/pillar_roots via a minion.d drop-in,
    # the same pattern win11 uses for its own state tree (see win11's comments).
    if Dir.exist?(File.join(__dir__, 'bevy_srv', 'salt'))
      quail_config.vm.provision "file", source: File.join(__dir__, 'bevy_srv', 'salt'),
                                destination: "C:\\tmp\\bevy_srv_salt", run: "always"
      quail_config.vm.provision "file", source: File.join(__dir__, 'bevy_srv', 'pillar'),
                                destination: "C:\\tmp\\bevy_srv_pillar", run: "always"
      quail_config.vm.provision "shell", run: "always", inline: <<-SHELL
        New-Item -ItemType Directory -Force -Path C:\\srv\\salt, C:\\srv\\pillar | Out-Null
        Copy-Item -Path C:\\tmp\\bevy_srv_salt\\* -Destination C:\\srv\\salt -Recurse -Force
        Copy-Item -Path C:\\tmp\\bevy_srv_pillar\\* -Destination C:\\srv\\pillar -Recurse -Force
        Remove-Item -Recurse -Force C:\\tmp\\bevy_srv_salt, C:\\tmp\\bevy_srv_pillar
        @"
file_roots:
  base:
    - C:\\srv\\salt
pillar_roots:
  base:
    - C:\\srv\\pillar
"@ | Set-Content -Path C:\\salt\\conf\\minion.d\\01_bevy_srv.conf
      SHELL
    end
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win10"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        salt.bootstrap_script = WINDOWS_SALT_BOOTSTRAP_SCRIPT
        #salt.log_level = "info"
        salt.verbose = false
        salt.colorize = true
        salt.run_highstate = default_run_highstate
        salt.masterless = true
        if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
          salt.minion_config = settings['GUEST_MINION_CONFIG_FILE']
        end
      end
    end
  end

 # . . . . . . . . . . . . Define machine win16 . . . . . . . . . . . . . .
 # . this machine installs Salt on a Windows 2016 Server.
  config.vm.define "win16", autostart: false do |quail_config|
    quail_config.vm.box = "cdaf/WindowsServer" #gusztavvargadr/w16s" # Windows Server 2016 standard
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.network "private_network", ip: NETWORK + ".56.16"
    if vagrant_command == "up" and vagrant_object == "win16"
      puts "Starting #{vagrant_object} #{as_minion}."
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win16'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.224/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 300
    quail_config.vm.graceful_halt_timeout = 60
    quail_config.vm.communicator = "winrm"
    script = "new-item C:\\salt\\conf\\minion.d -itemtype directory\r\n" # -ErrorAction silentlycontinue\r\n"
    script += "route add 10.0.0.0 mask 255.0.0.0 #{NETWORK}.62.226 -p\r\n"  # route 10. network through host NAT for VPN
    quail_config.vm.provision "shell", inline: script
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:\\salt\\conf\\minion.d\\00_bevy_boot.conf"
    end
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win16"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        salt.bootstrap_script = WINDOWS_SALT_BOOTSTRAP_SCRIPT
        salt.log_level = "info"
        salt.verbose = true
        salt.colorize = true
        salt.run_highstate = default_run_highstate
      end
    end
  end

 # . . . . . . . . . . . . Define machine win12 . . . . . . . . . . . . . .
 # . this machine bootstraps a salt minion on Windows Server 2012.
  config.vm.define "win12", autostart: false do |quail_config|
    quail_config.vm.box = "devopsguys/Windows2012R2Eval"
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.network "private_network", ip: NETWORK + ".56.12"
    if vagrant_command == "up" and vagrant_object == "win12"
      puts "Starting #{vagrant_object} #{as_minion}."
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win12'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".62.128/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 900
    quail_config.vm.graceful_halt_timeout = 60
    script = "new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue\r\n"
    script += "route add 10.0.0.0 mask 255.0.0.0 #{NETWORK}.62.130 -p\r\n"  # route 10. network through host NAT for VPN
    quail_config.vm.provision "shell", inline: script
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:\\salt\\conf\\minion.d\\00_bevy_boot.conf"
    end
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win12"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        salt.bootstrap_script = WINDOWS_SALT_BOOTSTRAP_SCRIPT
        #salt.log_level = "info"
        salt.verbose = false
        salt.colorize = true
        #salt.version = "2018.3.3"  # Example: minimum version needed for chocolatey
        #salt.run_highstate = default_run_highstate
      end
    end
  end

   # . . . . . . . . . . . . Define machine win19 . . . . . . . . . . . . . .
   # . this machine installs Salt on a Windows 2019 Server.
    config.vm.define "win19", autostart: false do |quail_config|
      quail_config.vm.box = "StefanScherer/windows_2019"
      quail_config.vm.network "public_network", bridge: interface_guesses
      quail_config.vm.network "private_network", ip: NETWORK + ".56.19"
      if vagrant_command == "up" and vagrant_object == "win19"
        puts "Starting #{vagrant_object} #{as_minion}."
        puts "NOTE: you may need to hit <Ctrl C> after starting this Windows minion."
      end
      quail_config.vm.provider "virtualbox" do |v|
          v.name = BEVY + '_win19'  # ! N.O.T.E.: name must be unique
          v.gui = true  # turn on the graphic window
          v.linked_clone = true
          v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
          v.memory = 4096
          v.cpus = max_cpus
          v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".63.32/27"]  # do not use 10.0 network for NAT
          v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
      end
      quail_config.vm.guest = :windows
      quail_config.vm.boot_timeout = 300
      quail_config.vm.graceful_halt_timeout = 60
      #script = "new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue\r\n"
      #script += "route add 10.0.0.0 mask 255.0.0.0 #{NETWORK}.63.34 -p\r\n"  # route 10. network through host NAT for VPN
      #quail_config.vm.provision "shell", inline: script
      if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
        quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:\\salt\\conf\\minion.d\\00_bevy_boot.conf"
      end
      if ENV.key?("VAGRANT_SALT")
        quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
          salt.minion_id = "win19"
          salt.master_id = "#{settings['master_vagrant_ip']}"
          salt.bootstrap_script = WINDOWS_SALT_BOOTSTRAP_SCRIPT
          salt.log_level = "info"
          salt.verbose = true
          salt.colorize = true
          salt.run_highstate = false  # Vagrant may stall trying to run Highstate for this minion.
        end
      end
    end

 # . . . . . . . . . . . . Define machine win7 . . . . . . . . . . . . . .
 # . this machine bootstraps a salt minion on Windows Server 2012.
  config.vm.define "win7", autostart: false do |quail_config|
    quail_config.vm.box = "mrh1997/vanilla-win7-32bit"
    quail_config.vm.network "public_network", bridge: interface_guesses
    #quail_config.vm.network "private_network", ip: NETWORK + ".56.7"
    if vagrant_command == "up" and vagrant_object == "win7"
      puts "Starting #{vagrant_object} #{as_minion}."
      puts "N O T E :  the default keyboard will be German (DE)."
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win7'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        #v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".63.96/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 900
    quail_config.vm.graceful_halt_timeout = 60
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:\\salt\\conf\\minion.d\\00_bevy_boot.conf"
    end
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win7"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        salt.bootstrap_script = WINDOWS_SALT_BOOTSTRAP_SCRIPT
        salt.log_level = "info"
        salt.verbose = true #false
        salt.colorize = true
        salt.run_highstate = default_run_highstate
      end
    end
  end

 # . . . . . . . . . . . . Define machine win11 . . . . . . . . . . . . . .
 # . this Windows 11 machine tests the windows-sudo package itself (see
 # . ../windows-sudo). Sourced from a Packer-built, Vagrant-ready box
 # . (WinRM preconfigured) rather than one of the older hand-patched boxes
 # . used by win10/win7 above.
 #
 # . Its masterless minion doesn't share bevy_srv/salt like its siblings --
 # . it copies windows-sudo/srv/salt + srv/pillar straight from
 # . WINDOWS_SUDO_REPO_ROOT into fixed guest paths (C:\srv\salt,
 # . C:\srv\pillar) and points file_roots/pillar_roots at those via its own
 # . minion.d drop-in, the same pattern salt22 uses for DJANGO_REPO_ROOT
 # . (see that block's comments) -- self-contained, no dependency on
 # . whatever the host's real WINDOWS_GUEST_CONFIG_FILE sets.
 #
 # . Runs under Hyper-V on this machine -- same reasoning as quail22/salt22/
 # . bevymaster above: Hyper-V can't create switches from Vagrant and
 # . ignores static private_network IPs (bridge to an existing External
 # . Virtual Switch instead), and its synced-folder fallback needs an
 # . interactive SMB share/credential prompt, so the four top-level synced
 # . folders are disabled here too. Neither of those matters for the
 # . srv/salt + srv/pillar copy-in below, or the WINDOWS_GUEST_CONFIG_FILE
 # . push -- both already go over WinRM's "file" provisioner, not a synced
 # . folder, so they work unchanged under Hyper-V.
  config.vm.define "win11", autostart: false do |quail_config|
    quail_config.vm.box = "gusztavvargadr/windows-11-25h2-enterprise"
    quail_config.vm.synced_folder ".", "/vagrant", disabled: true
    quail_config.vm.synced_folder ".", "/salt_bevy", disabled: true
    quail_config.vm.synced_folder ".", "/projects", disabled: true
    quail_config.vm.synced_folder ".", "/srv/pillar", disabled: true
    if ACTIVE_PROVIDER == "hyperv"
      quail_config.vm.network "public_network", bridge: HYPERV_SWITCH
      if vagrant_command == "up" and vagrant_object == "win11"
        puts "Starting 'win11' under Hyper-V, bridged to switch '#{HYPERV_SWITCH}'..."
      end
    else
      quail_config.vm.network "private_network", ip: NETWORK + ".56.11"
      quail_config.vm.network "public_network", bridge: interface_guesses
      if vagrant_command == "up" and vagrant_object == "win11"
        puts "Starting #{vagrant_object} #{as_minion}."
      end
    end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win11'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".63.128/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider "hyperv" do |v|  # only for Hyper-V boxes
        v.vmname = BEVY + '_win11'  # ! N.O.T.E.: name must be unique
        v.memory = 4096
        v.maxmemory = 4096    # see quail22's maxmemory comment: avoids a
                               # Vagrant 2.4.9 hyperv provider scoping bug
        v.cpus = max_cpus
        v.linked_clone = true # use a differencing disk instead of a full copy
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 600  # first boot / box setup can run long
    quail_config.vm.graceful_halt_timeout = 60
    quail_config.vm.communicator = "winrm"
    script = "new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue\r\n"
    quail_config.vm.provision "shell", inline: script
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:\\salt\\conf\\minion.d\\00_bevy_boot.conf"
    end
    # Copy this repo's own srv/salt + srv/pillar in directly (see the block
    # comment above) -- copy to a temp spot first, then move into place with
    # a shell step, same two-step dance salt22 uses for DJANGO_REPO_ROOT
    # (a single big "file" upload of a whole tree needs somewhere to land
    # before it can overwrite a possibly-already-populated destination).
    if Dir.exist?(File.join(WINDOWS_SUDO_REPO_ROOT, 'srv', 'salt'))
      quail_config.vm.provision "file", source: File.join(WINDOWS_SUDO_REPO_ROOT, 'srv', 'salt'),
                                destination: "C:\\tmp\\windows_sudo_srv_salt", run: "always"
      quail_config.vm.provision "file", source: File.join(WINDOWS_SUDO_REPO_ROOT, 'srv', 'pillar'),
                                destination: "C:\\tmp\\windows_sudo_srv_pillar", run: "always"
      quail_config.vm.provision "shell", run: "always", inline: <<-SHELL
        New-Item -ItemType Directory -Force -Path C:\\srv\\salt, C:\\srv\\pillar | Out-Null
        Copy-Item -Path C:\\tmp\\windows_sudo_srv_salt\\* -Destination C:\\srv\\salt -Recurse -Force
        Copy-Item -Path C:\\tmp\\windows_sudo_srv_pillar\\* -Destination C:\\srv\\pillar -Recurse -Force
        Remove-Item -Recurse -Force C:\\tmp\\windows_sudo_srv_salt, C:\\tmp\\windows_sudo_srv_pillar
        @"
file_roots:
  base:
    - C:\\srv\\salt
pillar_roots:
  base:
    - C:\\srv\\pillar
"@ | Set-Content -Path C:\\salt\\conf\\minion.d\\01_windows_sudo.conf
      SHELL
    end
    if ENV.key?("VAGRANT_SALT")
      quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win11"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        salt.bootstrap_script = WINDOWS_SALT_BOOTSTRAP_SCRIPT
        salt.log_level = "info"
        salt.verbose = true
        salt.colorize = true
        salt.run_highstate = default_run_highstate
      end
    end
  end

# . . . . . . .  Define MacOS mac13 with Salt minion installed . . . . . . . . . . . . . .
# . this machine bootstraps Salt but no states are run or defined.
  config.vm.define "mac13", autostart: false do |quail_config|
    if (RUBY_PLATFORM=~/darwin/i)  # different VMs boot correctly on MacOS vs others
      quail_config.vm.box = "thealanberman/macos-10.13.4"
    else  # Windows or Linux
      quail_config.vm.box = "mcandre/palindrome-buildbot-macos"
    end
    quail_config.vm.hostname = "mac13"
    quail_config.vm.network "private_network", ip: NETWORK + ".56.13"

    # . . . CAUTION: large rsync folders take forever to set up and may overfill VM disk . . .
    if settings.has_key?('projects_root') and settings['projects_root'] != 'none'
      quail_config.vm.synced_folder settings['projects_root'], "/projects", type: "rsync", disabled: true
    end
    if ENV.key?("VAGRANT_CWD")
      config.vm.synced_folder ENV["VAGRANT_CWD"], "/salt-bevy", type: "rsync", disabled: true
    end
    quail_config.vm.synced_folder ".", "/vagrant", type: "rsync"

    if vagrant_command == "up" and vagrant_object == "mac13"
      puts "Starting #{vagrant_object} at #{NETWORK}.56.13 #{as_minion}...\n."
    end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.gui = true
        v.name = BEVY + '_mac13'  # ! N.O.T.E.: name must be unique
        v.memory = 6000       # limit memory for the virtual box
        v.cpus = max_cpus
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".63.64/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provision "shell", path: "configure_machine/macos_unprotect_dirs.sh"
    if settings.has_key?('MAC_MINION_CONFIG_FILE') and File.exist?(settings['MAC_MINION_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['MAC_MINION_CONFIG_FILE'], destination: "/etc/salt/minion.d/00_bevy_boot.conf"
    end
    # no shared directory on MacOS, so we will make a copy of the bevy settings...
    if File.exist?(BEVY_SETTINGS_FILE_NAME)
      quail_config.vm.provision "file", source: BEVY_SETTINGS_FILE_NAME, destination: name_bevy_settings_file('/opt/saltdata')
    end
    if ENV.key?("VAGRANT_SALT")
      script = "echo mac13 > /etc/salt/minion_id"
      quail_config.vm.provision "shell", inline: script
      quail_config.vm.provision "shell", path: "configure_machine/macos_install_P3_and_salt.sh"
    end
  end
end

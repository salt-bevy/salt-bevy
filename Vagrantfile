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

SALT_BOOTSTRAP_ARGUMENTS = "" # "git v2019.2.0rc1"  # (usually leave blank for latest production Salt version)

vagrant_command = ARGV[0]
vagrant_object = ARGV.length > 1 ? ARGV[1] : ""  # the name (if any) of the vagrant VM for this command
#
# under the DRY principle, the most important setting are stored
# in a Salt 'pillar' file. Vagrant has to look them up there...
#
# . v . v . retrieve stored bevy settings . v . v . v . v . v . v .
BEVY_SETTINGS_FILE_NAME = '/srv/pillar/01_bevy_settings.sls'
if File.exists?(BEVY_SETTINGS_FILE_NAME)
  settings = YAML.load_file(BEVY_SETTINGS_FILE_NAME)  # get your local settings
  default_run_highstate = true
else
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
   "GUEST_MINION_CONFIG_FILE" => 'configure_machine/masterless_minion.conf',
   "WINDOWS_GUEST_CONFIG_FILE" => 'configure_machine/masterless_minion.conf',
   }
  default_run_highstate = false
end
# .
BEVY = settings["bevy"]  # the name of your bevy
# the first two bytes of your Vagrant host-only network IP ("192.168.x.x")
NETWORK = "#{settings['vagrant_prefix']}"
# ^ ^ each VM below will have a NAT network in NETWORK.17.x/27.
puts "Your bevy name:#{BEVY} using local network #{NETWORK}.x.x"
puts "This (the VM host) computer will be at #{NETWORK}.2.1" if ARGV[1] == "up"
bevy_mac = (BEVY.to_i(36) % 0x1000000).to_s(16)  # a MAC address based on hash of BEVY
# in Python that would be: bevy_mac = format(int(BEVY, base=36) % 0x1000000, 'x')
#
VAGRANT_HOST_NAME = Socket.gethostname
login = Etc.getlogin    # get your own user information
my_linux_user = settings['my_linux_user']
my_linux_user = login if my_linux_user.to_s.empty?  # use current value if settings gives blank.
HASHFILE_NAME = 'bevy_linux_password.hash'  # filename for your Linux password hash
hash_path = File.join(Dir.home, '.ssh', HASHFILE_NAME)  # where you store it ^ ^ ^
#
# . v . v . the program starts here . v . v . v . v . v . v . v . v . v .
#
# Bridged networks make the machine appear as another physical device on your network.
# We must supply a list of names to avoid Vagrant asking for interactive input
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
    config.vm.provision "shell", inline: "ifconfig", run: "always"  # what did we get?
  end

  # Now ... just in case our user is running some flavor of VMWare, we will
  # set up his VM, too. But first we need to discover his Host OS ...
  if (/darwin/ =~ RUBY_PLATFORM) != nil
    vmware = "vmware_fusion"
  else
    vmware = "vmware_workstation"
  end

  if settings.has_key?('projects_root') and settings['projects_root'] != 'none'
    config.vm.synced_folder settings['projects_root'], "/projects", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
    end

  config.vm.synced_folder '/srv/pillar', "/srv/pillar", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]

  # . . . . . . . . . . . . Define machine QUAIL1 . . . . . . . . . . . . . .
  # This machine has no Salt provisioning at all. Salt-cloud can provision it.
  config.vm.define "quail1", primary: true do |quail_config|  # this will be the default machine
    quail_config.vm.box = "ubuntu/bionic64"
    quail_config.vm.hostname = "quail1" # + DOMAIN
    quail_config.vm.network "private_network", ip: NETWORK + ".2.201"  # needed so saltify_profiles.conf can find this unit
    if vagrant_command == "up" and (ARGV.length == 1 or (vagrant_object == "quail1"))
      puts "Starting 'quail1' at #{NETWORK}.2.201..."
      end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|  # only for VirtualBox boxes
        v.name = BEVY + '_quail1'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.0/27"]  # do not use 10.0 network for NAT
	    #                                                     ^  ^/27 is the smallest network allowed.
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|  # only for VMware boxes
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	end
  end

# . . . . . . .  Define quail2 with Salt minion installed . . . . . . . . . . . . . .
# . this machine bootstraps Salt but no states are run or defined.
# . Its master is "bevymaster".
  config.vm.define "quail2", autostart: false do |quail_config|
    quail_config.vm.box = "ubuntu/bionic64"
    quail_config.vm.hostname = "quail2" # + DOMAIN
    quail_config.vm.network "private_network", ip: NETWORK + ".2.202"
    if vagrant_command == "up" and vagrant_object == "quail2"
      puts "Starting #{vagrant_object} at #{NETWORK}.2.202 as a Salt minion with master=#{settings['master_vagrant_ip']}...\n."
      end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quail2'  # ! N.O.T.E.: name must be unique
        v.memory = 4000       # limit memory for the virtual box
        v.cpus = max_cpus
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.160/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "5000"
        v.vmx["numvcpus"] = "2"
    end
    script = "mkdir -p /etc/salt/minion.d\n"
    script += "chown -R vagrant:staff /etc/salt/minion.d\n"
    script += "chmod -R 775 /etc/salt/minion.d\n"
    quail_config.vm.provision "shell", inline: script
    if settings.has_key?('GUEST_MINION_CONFIG_FILE') and File.exist?(settings['GUEST_MINION_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['GUEST_MINION_CONFIG_FILE'], destination: "/etc/salt/minion.d/00_vagrant_boot.conf"
      end
    quail_config.vm.provision :salt do |salt|
       salt.verbose = false
       salt.bootstrap_options = "-A #{settings['master_vagrant_ip']} -i quail2 -F -P #{SALT_BOOTSTRAP_ARGUMENTS}"
       salt.run_highstate = default_run_highstate
    end
  end

# . . . . . . .  Define the BEVYMASTER . . . . . . . . . . . . . . . .
# This is the Vagrant version of a Bevy Salt-master.
# You cannot run it if you are using an external bevymaster.
  config.vm.define "bevymaster", autostart: false do |master_config|
    master_config.vm.box = "ubuntu/bionic64"
    master_config.vm.hostname = "bevymaster"
    master_config.vm.network "private_network", ip: NETWORK + ".2.2"
    if vagrant_command == "up" and vagrant_object == "bevymaster"
      if settings['master_vagrant_ip'] != NETWORK + ".2.2"
        # prevent running a Vagrant bevy master if another is in use.
        abort "Sorry. Your master_vagrant_ip setting of '#{settings['master_vagrant_ip']}' suggests that your Bevy Master is not expected to be Virtual here."
        end
      puts "Starting #{vagrant_object} at #{NETWORK}.2.2..."
      end
    master_config.vm.network "public_network", bridge: interface_guesses, mac: "be0000" + bevy_mac
    master_config.vm.synced_folder ".", "/vagrant", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
    #if settings.has_key?('application_roots')  # additional shares for optional applications directories
    #  settings['application_roots'].each do |share|  # formatted real-path=share-path
    #    s = share.split('=')
    #    master_config.vm.synced_folder s[0], "/#{s[1]}", :owner => "vagrant", :group => "staff", :mount_options => ["umask=0002"]
    #  end
    #end
    #if vagrant_command == "ssh"
    #  master_config.ssh.username = my_linux_user  # if you type "vagrant ssh", use this username
    #  master_config.ssh.private_key_path = Dir.home() + "/.ssh/id_rsa"
    #end
    master_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_bevymaster'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.32/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    master_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	end
    script = "mkdir -p /etc/salt/minion.d\n"
    script += "chown -R vagrant:staff /etc/salt/minion.d\n"
    script += "chmod -R 775 /etc/salt/minion.d\n"
    script += "mkdir -p #{File.dirname(BEVY_SETTINGS_FILE_NAME)}\n"
    script += "chown -R vagrant:staff #{File.dirname(BEVY_SETTINGS_FILE_NAME)}\n"
    script += "chmod -R 775 #{File.dirname(BEVY_SETTINGS_FILE_NAME)}\n"
    master_config.vm.provision "shell", inline: script
    if settings.has_key?('GUEST_MASTER_CONFIG_FILE') and File.exist?(settings['GUEST_MASTER_CONFIG_FILE'])
      master_config.vm.provision "file", source: settings['GUEST_MASTER_CONFIG_FILE'],
                                destination: "/etc/salt/minion.d/00_vagrant_boot.conf"
      end
    if File.exists?(BEVY_SETTINGS_FILE_NAME)
      master_config.vm.provision "file", source: BEVY_SETTINGS_FILE_NAME, destination: BEVY_SETTINGS_FILE_NAME
      end
    master_config.vm.provision :salt do |salt|
       # salt.install_type = "stable 2018.3.3"
       salt.verbose = true
       salt.log_level = "info"
       salt.colorize = true
       salt.bootstrap_options = "-P -M -L #{SALT_BOOTSTRAP_ARGUMENTS}"  # install salt-cloud and salt-master
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
         "master_vagrant_ip" => NETWORK + '.2.2',
         "additional_minion_tag" => '',
         "linux_password_hash" => password_hash,
         "force_linux_user_password" => true,
         "vagranthost" => VAGRANT_HOST_NAME,
         "runas" => login,
         "cwd" => Dir.pwd,
         "server_role" => 'master',
         "doing_bootstrap" => true,  # flag for Salt state system
         })
       end
  end


  # . . . . . . . . . . . . Define machine QUAIL18 . . . . . . . . . . . . . .
  # This Ubuntu 18.04 machine is designed to be run by salt-cloud
  config.vm.define "quail18", autostart: false do |quail_config|
    quail_config.vm.box = "ubuntu/bionic64"
    quail_config.vm.hostname = "quail18" # + DOMAIN
    quail_config.vm.network "private_network", ip: NETWORK + ".2.218"
    if vagrant_command == "up" and vagrant_object == "quail18"
      puts "Starting #{vagrant_object} at #{NETWORK}.2.218..."
      end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quai18'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".18.0/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
	end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	end
  end

  # . . . . . . . . . . . . Define machine QUAIL16 . . . . . . . . . . . . . .
  # This Ubuntu 16.04 machine is designed to be run by salt-cloud
  config.vm.define "quail16", autostart: false do |quail_config|
    quail_config.vm.box = "boxesio/xenial64-standard"  # a public VMware & Virtualbox box
    quail_config.vm.hostname = "quail16" # + DOMAIN
    quail_config.vm.network "private_network", ip: NETWORK + ".2.216"
    if vagrant_command == "up" and vagrant_object == "quail16"
      puts "Starting #{vagrant_object} at #{NETWORK}.2.216..."
      end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quai16'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.64/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
	end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	end
  end

# . . . . . . . . . . . . Define machine QUAIL14 . . . . . . . . . . . . . .
# This Ubuntu 14.04 machine is designed to be run by salt-cloud
  config.vm.define "quail14", autostart: false do |quail_config|
    quail_config.vm.box = "boxesio/trusty64-standard"  # a public VMware & Virtualbox box
    quail_config.vm.hostname = "quail14" # + DOMAIN
    quail_config.vm.network "private_network", ip: NETWORK + ".2.214"
    if vagrant_command == "up" and vagrant_object == "quail14"
      puts "Starting #{vagrant_object} at #{NETWORK}.2.214..."
      end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_quail14'  # ! N.O.T.E.: name must be unique
        v.memory = 1024       # limit memory for the virtual box
        v.cpus = 1
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.96/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
	end
    quail_config.vm.provider vmware do |v|
        v.vmx["memsize"] = "1024"
        v.vmx["numvcpus"] = "1"
	end
  end

 # . . . . . . . . . . . . Define machine win10 . . . . . . . . . . . . . .
 # . this Windows 10 machine bootstraps Salt.
  config.vm.define "win10", autostart: false do |quail_config|
    quail_config.vm.box = "StefanScherer/windows_10"  #"Microsoft/EdgeOnWindows10"
    # <#this causes Windows to restart#> # quail_config.vm.hostname = 'win10'
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.network "private_network", ip: NETWORK + ".2.10"
    if vagrant_command == "up" and vagrant_object == "win10"
      puts "Starting #{vagrant_object} as a Salt minion of #{settings['master_vagrant_ip']}."
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
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.192/27"]  # do not use 10.0 network for NAT
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
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:/salt/conf/minion.d/00_vagrant_boot.conf"
      end
    quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win10"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        #salt.log_level = "info"
        salt.verbose = false
        salt.colorize = true
        salt.run_highstate = default_run_highstate
        salt.version = "2018.3.3"  # TODO: remove this when this becomes default. Needed for chocolatey
    end
  end

 # . . . . . . . . . . . . Define machine win16 . . . . . . . . . . . . . .
 # . this machine installs Salt on a Windows 2016 Server.
  config.vm.define "win16", autostart: false do |quail_config|
    quail_config.vm.box = "cdaf/WindowsServer" #gusztavvargadr/w16s" # Windows Server 2016 standard
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.network "private_network", ip: NETWORK + ".2.16"
    if vagrant_command == "up" and vagrant_object == "win16"
      puts "Starting #{vagrant_object} as a Salt minion of #{settings['master_vagrant_ip']}."
      end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win16'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.224/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 300
    quail_config.vm.graceful_halt_timeout = 60
    quail_config.vm.communicator = "winrm"
    script = "new-item C:\\salt\\conf\\minion.d -itemtype directory\r\n" # -ErrorAction silentlycontinue\r\n"
    script += "route add 10.0.0.0 mask 255.0.0.0 #{NETWORK}.17.226 -p\r\n"  # route 10. network through host NAT for VPN
    quail_config.vm.provision "shell", inline: script
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:/salt/conf/minion.d/00_vagrant_boot.conf"
      end
    quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win16"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        salt.log_level = "info"
        salt.version = "2018.3.3"  # TODO: remove this when this becomes default. Needed for chocolatey
        salt.verbose = true
        salt.colorize = true
        salt.run_highstate = default_run_highstate
    end
  end

 # . . . . . . . . . . . . Define machine win12 . . . . . . . . . . . . . .
 # . this machine bootstraps a salt minion on Windows Server 2012.
  config.vm.define "win12", autostart: false do |quail_config|
    quail_config.vm.box = "devopsguys/Windows2012R2Eval"
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.network "private_network", ip: NETWORK + ".2.12"
    if vagrant_command == "up" and vagrant_object == "win12"
      puts "Starting #{vagrant_object} as a Salt minion of #{settings['master_vagrant_ip']}."
      end
    quail_config.vm.provider "virtualbox" do |v|
        v.name = BEVY + '_win12'  # ! N.O.T.E.: name must be unique
        v.gui = true  # turn on the graphic window
        v.linked_clone = true
        v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
        v.memory = 4096
        v.cpus = max_cpus
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".17.128/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.guest = :windows
    quail_config.vm.boot_timeout = 900
    quail_config.vm.graceful_halt_timeout = 60
    script = "new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue\r\n"
    script += "route add 10.0.0.0 mask 255.0.0.0 #{NETWORK}.17.130 -p\r\n"  # route 10. network through host NAT for VPN
    quail_config.vm.provision "shell", inline: script
    if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:/salt/conf/minion.d/00_vagrant_boot.conf"
      end
    quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
        salt.minion_id = "win12"
        salt.master_id = "#{settings['master_vagrant_ip']}"
        #salt.log_level = "info"
        salt.verbose = false
        salt.colorize = true
        salt.version = "2018.3.3"  # TODO: remove this when this becomes default. Needed for chocolatey
        #salt.run_highstate = default_run_highstate
    end
  end

   # . . . . . . . . . . . . Define machine win19 . . . . . . . . . . . . . .
   # . this machine installs Salt on a Windows 2019 Server.
    config.vm.define "win19", autostart: false do |quail_config|
      quail_config.vm.box = "StefanScherer/windows_2019"
      quail_config.vm.network "public_network", bridge: interface_guesses
      quail_config.vm.network "private_network", ip: NETWORK + ".2.19"
      if vagrant_command == "up" and vagrant_object == "win19"
        puts "Starting #{vagrant_object} as a Salt minion of #{settings['master_vagrant_ip']}."
        puts "NOTE: you may need to hit <Ctrl C> after starting this Windows minion."
        end
      quail_config.vm.provider "virtualbox" do |v|
          v.name = BEVY + '_win19'  # ! N.O.T.E.: name must be unique
          v.gui = true  # turn on the graphic window
          v.linked_clone = true
          v.customize ["modifyvm", :id, "--vram", "27"]  # enough video memory for full screen
          v.memory = 4096
          v.cpus = max_cpus
          v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".18.32/27"]  # do not use 10.0 network for NAT
          v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
      end
      quail_config.vm.guest = :windows
      quail_config.vm.boot_timeout = 300
      quail_config.vm.graceful_halt_timeout = 60
      script = "new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue\r\n"
      script += "route add 10.0.0.0 mask 255.0.0.0 #{NETWORK}.18.34 -p\r\n"  # route 10. network through host NAT for VPN
      quail_config.vm.provision "shell", inline: script
      if settings.has_key?('WINDOWS_GUEST_CONFIG_FILE') and File.exist?(settings['WINDOWS_GUEST_CONFIG_FILE'])
        quail_config.vm.provision "file", source: settings['WINDOWS_GUEST_CONFIG_FILE'], destination: "c:/salt/conf/minion.d/00_vagrant_boot.conf"
        end
      quail_config.vm.provision :salt do |salt|  # salt_cloud cannot push Windows salt
          salt.minion_id = "win19"
          salt.master_id = "#{settings['master_vagrant_ip']}"
          salt.log_level = "info"
          salt.version = "2018.3.3"  # TODO: remove this when this becomes default. Needed for chocolatey
          salt.verbose = true
          salt.colorize = true
          salt.run_highstate = false  # Vagrant may stall trying to run Highstate for this minion.
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
    quail_config.vm.network "private_network", ip: NETWORK + ".2.13"
    if settings.has_key?('projects_root') and settings['projects_root'] != 'none'
      quail_config.vm.synced_folder settings['projects_root'], "/projects", disabled: true # shared folders do not work
      end
    quail_config.vm.synced_folder ".", "/vagrant", disabled: true
    if vagrant_command == "up" and vagrant_object == "mac13"
      puts "Starting #{vagrant_object} at #{NETWORK}.2.13 as a Salt minion with master=#{settings['bevymaster_url']}...\n."
      end
    quail_config.vm.network "public_network", bridge: interface_guesses
    quail_config.vm.provider "virtualbox" do |v|
        v.gui = true
        v.name = BEVY + '_mac13'  # ! N.O.T.E.: name must be unique
        v.memory = 6000       # limit memory for the virtual box
        v.cpus = max_cpus
        v.linked_clone = true # make a soft copy of the base Vagrant box
        v.customize ["modifyvm", :id, "--natnet1", NETWORK + ".18.64/27"]  # do not use 10.0 network for NAT
        v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]  # use host's DNS resolver
    end
    quail_config.vm.provision "shell", path: "configure_machine/macos_unprotect_dirs.sh"
    if settings.has_key?('GUEST_MINION_CONFIG_FILE') and File.exist?(settings['GUEST_MINION_CONFIG_FILE'])
      quail_config.vm.provision "file", source: settings['GUEST_MINION_CONFIG_FILE'], destination: "/etc/salt/minion.d/00_vagrant_boot.conf"
      end
    # no shared directory on MacOS, so we will make a copy of the bevy settings...
    if File.exist?(BEVY_SETTINGS_FILE_NAME)
      quail_config.vm.provision "file", source: BEVY_SETTINGS_FILE_NAME, destination: BEVY_SETTINGS_FILE_NAME
      end
    script = "echo mac13 > /etc/salt/minion_id"
    quail_config.vm.provision "shell", inline: script
    quail_config.vm.provision "shell", path: "configure_machine/macos_install_P3_salt.sh"
  end

end

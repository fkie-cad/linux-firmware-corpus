# SPDX-FileCopyrightText: 2024 Fraunhofer FKIE
# SPDX-FileContributor: Marten Ringwelski <git@maringuu.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# The port that should expose the FACT frontend
PORT = 5000
# The number of CPUs to assign to the virtual machine
CPUS = 4
# The amount of RAM in megabytes
RAM = 16 * 1024
# The disksize to use. If you intend to upload the whole corpus,
# you need about 5,000GB.
DISK = "100GB"

Vagrant.configure("2") do |config|
  config.vagrant.plugins = "vagrant-disksize"

  config.vm.box = "fact-cad/FACT-master"
  config.vm.box_version = "20231223"

  config.vm.network "forwarded_port", guest: 5000, host: PORT # FACT port

  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/home/vagrant/linux-firmware-corpus"
  config.disksize.size = DISK

  config.ssh.extra_args = ["-L", "8888:localhost:8888", "-L" "8889:localhost:8889"]

  config.vm.provision "shell", inline: "cd ~/linux-firmware-corpus/ && ./prepare", privileged: false

  config.vm.provider "virtualbox" do |vb|
    vb.gui = false
    vb.cpus = CPUS
    vb.memory = RAM
  end
end


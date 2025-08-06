# Linux Firmware Corpus (LFwC)

This is the companion and artifact repository to the paper `Mens Sana in Corpore Sano: Sound Firmware Corpora for Vulnerability Research`.

In Sec. V of the paper, be build a proof of concept Linux Firmware Corpus (LFwC) to assess the feasibility of our requirements for scientifically sound firmware corpora (Sec. III).
It is based on data until June 2023 and consists of 10,913 deduplicated and unpacked firmware images from ten known manufacturers.
It includes recent and historical firmware, covering 2,365 unique devices across 22 classes.

We share as much data as legally possible and publish all scripts, tools, and virtual machines for replicability in this repository.
We tear down the firmware unpacking barrier with an open source process for verified unpacking success based on the [Firmware Analysis and Comparison Tool (FACT)](https://github.com/fkie-cad/FACT_core).

## Read & Cite the Paper

The paper was published at the [Network and Distributed System Security (NDSS) Symposium 2025](https://www.ndss-symposium.org/ndss2025/) and can be downloaded [here](https://www.ndss-symposium.org/wp-content/uploads/2025-669-paper-1.pdf).

```bibtex
@inproceedings{helmkeSoundFirmwareCorpora,
  author = {Helmke, René and Padilla, Elmar and Aschenbruck, Nils},
  title = {{Mens Sana In Corpore Sano: Sound Firmware Corpora for Vulnerability Research}},
  booktitle = {{Proceedings of the Network and Distributed System Security Symposium (NDSS'25)}},
  year = {2025},
  publisher = {{The Internet Society}},
  address = {{San Diego, California, USA}},
  url = {https://www.ndss-symposium.org/wp-content/uploads/2025-669-paper-1.pdf}
}
```

## Get the Corpus

Access to LFwC is gated for scientific purposes. Please request the meta data for corpus replication [here](https://doi.org/10.5281/zenodo.12659436).


## Corpus Updates

As LFwC is an important resource for our day-to-day research and firmware analysis development, we plan to publish, at least, yearly updates in this repository to ensure replicability and sample actuality.

## Artifact Evaluation Tag

Check out the artifact evaluation tag to get the same version as used in our Artifact Appendix:

```sh
git checkout ndss-25-ae
```

We also share a ZIP file of the artifact evaluation version on [Zenodo](https://doi.org/10.5281/zenodo.12659339).

## Requirements

### Configuration 1: High-End Server Setup for the Full LFwC Corpus

The full LFwC corpus requires 354 GiB for samples, and 2.5 TiB for unpacking and content analysis using FACT.
Unpacking and analysis take several months on server-grade hardware:

| **Compontent** |            **Specifications**            |
|---------------:|:----------------------------------------:|
| CPU            | 2x Intel Xeon E5-2650 v3@ 2.30 GHz, NUMA |
| RAM            | 157 GiB DDR4 @ 2133MHz                   |
| Board          | Dell 0HFG24, LGA 2011 (PowerEdge R430)   |
| SSD (OS)       | 512 GiB (Ubuntu 22.04.04 LTS)            |
| HDD (Data)     | 4 TiB, mounted at `/media/data`          |
| Python         | `3.10.12`                                |
| FACT           | Commit `0984d0ca`                        |

Before you commit to a multi-month analysis, better start out with Configuration 2.

See Appendix D-B in the paper for setup instructions.

### Configuration 2: Quick-and-Dirty Virtual Machine Setup for Result Verification and Small Corpus Subsets

We provide a VirtualBox-based vagrant machine to quickly deploy a fully working artifact and FACT environment.
The host requirements are:

| **Compontent** |            **Specifications**            |
|---------------:|:----------------------------------------:|
| CPU            | 4 Free CPU Cores with VT-x or AMD-v      |
| RAM            | 16 GiB                                   |
| Storage        | 100 GiB (Preferably SSD)                 |
| Host OS        | Arbitrary Desktop Linux (x86\_64)        |
| VirtualBox     | `>=7.0`                                  |
| Vagrant        | `~2.4` (verified)                        |

See Appendix D-B in the paper for setup instructions.

#### Spin up the Vagrant Machine

```sh
vagrant up
```

Wait until finished. FACT is now available at `http://localhost:5000`. All dependencies are installed. Then, ssh into the machine and find this repository as shared folder inside:

```sh
vagrant ssh
```

The SSH commands locally forward ports `8888` and `8889` from the VM to the host, so that you can spin up jupyter lab.

Finally, VM control:

```sh
vagrant up # start the vm, only first start is slow due to deployment
vagrant halt # stop the vm
vagrant destroy # destroy the vm _AND ITS INCLUDED DATA_
```

## Repository Layout

```plain
.
├── downscaling   # corpus downscaling scripts for Configuration 2. See Appendix D-F in the paper for instructions.
├── notebooks     # jupyter notebooks to interactively explore the data sets of Sec. V and Sec. IV of our paper. See Appendix D-D and D-G for instructions.
├── prepare       # install all dependencies of this repository (you have still to install vagrant and virtualbox for configuration 2, and FACT for configuration 1).
├── replication   # LFwC replication scripts. See Appendix D-E and D-F for instructions.
├── scrapers      # Scrapers, the original source of LFwC. Only included for transparency, as most of them do not work anymore do to changed manufacturer web sites.
└── Vagrantfile   # vagrant virtual machine configuration file. See Appendix D-B for instructions.
```

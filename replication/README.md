# replication

This folder contains a replication tool for LFwC.

It contains two functionalities:
 * A leightweight wrapper around [aria2][aria2] to download the firmware corpus
 * An upload script to pass firmware to [FACT][fact]

The paper describes two files containing firmware meta data for replication:

- `lfwc-full.csv` - 10,913 fully unpackable linux firmware images
- `lfwc-failed.csv` - 3,670 firmware images that failed unpacking verification

These files work in conjunction with the tool, **but are not part of this repository**. Please request the corpus meta data via Zenodo.

## Installation

First, install the system dependencies:

- [aria2][aria2]: Required for the `download` command (version 1.37.0 at the time of writing)
- [FACT][fact]: Required for the `upload-to-fact` command (See Section FACT Vagrant Image).

The tool can be installed with `pip` after packaging it with [`poetry`][poetry].
In short, use the folowing two lines of shell:

```sh
$ poetry build
$ pip install dist/replicate_lfwc-0.1.0.tar.gz
```

## Usage
After installing as described above, the script is exposed as
`replicate_lfwc`.
```
Usage: python -m replicate_lfwc [OPTIONS] COMMAND [ARGS]...

  Use aria2 to download LFWC

Options:
  --corpus-csv PATH  Path to corpus.csv. Either use the file vendored with the paper, or a compatible file.  [required]
  --help             Show this message and exit.

Commands:
  download          Download all missing files.
  dump-aria2-input  Dump the input file that can be used directly with aria2c.
  upload-to-fact    Upload the firmware corpus to fact.
  verify            Prints the path and status of all firmwares that have a status other than 'success' to stderr.
```

[aria2]: https://github.com/aria2/aria2
[poetry]: https://python-poetry.org/
[fact]: https://github.com/fkie-cad/FACT_core/

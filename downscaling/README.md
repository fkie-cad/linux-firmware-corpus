# downscaling

This folder holds all scripts to create downscaled, mini versions of LFwC. The function is intuitive: take `lfwc-full.csv` and pseudorandomly pick a set of samples from it for each manufacturer to create `lfwc-mini.csv`.

The default selects five samples from each manufacturer and excludes firmware images larger than `30 MiB`. Use a `--seed` to share and/or persist random picks.

## Install dependenices

```sh
./prepare
```

## Synopsis 

```sh
./build_corpus --help
usage: build_corpus [-h] [--full_corpus FULL_CORPUS] [--output OUTPUT] [--samples_per_manufacturer SAMPLES_PER_MANUFACTURER] [--seed SEED] [--max_fw_size MAX_FW_SIZE]
                    [--overwrite | --no-overwrite]

options:
  -h, --help            show this help message and exit
  --full_corpus FULL_CORPUS
                        path to full corpus csv
  --output OUTPUT       path to output corpus csv (default: '../../notebooks/public_data/lfwc-mini.csv')
  --samples_per_manufacturer SAMPLES_PER_MANUFACTURER
                        samples per manufacturer (default: 5)
  --seed SEED           PRNG seed (default: 0)
  --max_fw_size MAX_FW_SIZE
                        max firmware size (bytes, default: 31457280 (30MB))
  --overwrite, --no-overwrite
                        Overwrite if output file already exists (default: false)
```

## Folder Structure Deciphered


```plain
.
├── build_corpus                        # wrapper script for _build_corpus.py in an isolated venv
├── _build_corpus.py                    # corpus creation script
└── prepare                             # install dependencies and create venv
```

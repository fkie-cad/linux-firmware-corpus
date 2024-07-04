#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser("build_corpus")
    parser.add_argument(
        "--full_corpus",
        default=Path("../../notebooks/public_data/lfwc-full.csv"),
        required=False,
        type=Path,
        help="path to full corpus csv",
    )
    parser.add_argument(
        "--output",
        default=Path("../../notebooks/public_data/lfwc-mini.csv"),
        required=False,
        type=Path,
        help="path to output corpus csv (default: '../../notebooks/public_data/lfwc-mini.csv')",
    )
    parser.add_argument(
        "--samples_per_manufacturer",
        default=5,
        type=int,
        required=False,
        help="samples per manufacturer (default: 5)",
    )
    parser.add_argument(
        "--seed", default=0, type=int, required=False, help="PRNG seed (default: 0)"
    )
    parser.add_argument(
        "--max_fw_size",
        default=31457280,
        type=int,
        required=False,
        help="max firmware size (bytes, default: 31457280 (30MB))",
    )

    parser.add_argument(
        "--overwrite",
        default=False,
        type=bool,
        required=False,
        action=argparse.BooleanOptionalAction,
        help="Overwrite if output file already exists (default: false)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.output.exists() and not args.overwrite:
        print(
            f"WARNING: output file '{args.output}' already exists. If you are sure you want to overwrite it, restart with '--overwrite' flag."
        )
        return

    df = pd.read_csv(args.full_corpus, index_col="id")

    print("Full Corpus File Preview")
    print("=========================")
    print(df)
    print("=========================")

    sampled_subsets = []
    for manufacturer in df["manufacturer"].unique():
        fixed_manufacturer = df["manufacturer"] == manufacturer
        size_constraint = df["compressed_firmware_size"] <= args.max_fw_size
        subset = df[fixed_manufacturer & size_constraint]
        samples = subset.sample(args.samples_per_manufacturer, random_state=args.seed)
        sampled_subsets += [samples]
        print(f"Sampled Subset for {manufacturer}")
        print("=========================")
        print(samples)
        print("=========================")

    print("Done!")
    mini_corpus = pd.concat(sampled_subsets)
    print(f"Final mini corpus shape: {mini_corpus.shape}")
    print("=========================")
    print(mini_corpus)
    print("=========================")
    mini_corpus.to_csv(args.output)
    print(f"Saved mini corpus to {args.output}")


if __name__ == "__main__":
    main()

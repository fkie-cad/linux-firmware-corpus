# SPDX-FileCopyrightText: 2024 Fraunhofer FKIE
# SPDX-FileContributor: Marten Ringwelski <git@maringuu.de>
#
# SPDX-License-Identifier: CC0-1.0

"""Usage:
fetch-wayback-urls.py corpus.csv

Adds a column "wayback" to the given csv and writes the csv to corpus.csv-wayback.
"""

import sys
import time
import urllib.parse

import pandas as pd
import requests


def wayback_url_from_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return None

    if parsed.hostname in ["archive.org", "www.archive.org"]:
        return url

    response = requests.get(
        "https://archive.org/wayback/available",
        params={
            "url": url,
        },
    )
    response.raise_for_status()
    data = response.json()
    archived_snapshots = data["archived_snapshots"]
    if len(archived_snapshots) == 0:
        return None

    closest = archived_snapshots.get("closest")

    return closest["url"]


def main():
    if len(sys.argv) != 2:  # noqa: PLR2004
        print("Please provide the path to corpus.csv as the only cli argument")
        sys.exit(1)

    path = sys.argv[1]
    df = pd.read_csv(
        path,
        index_col=0,
    )

    BACKOFF = 60

    def wrapper(url):
        while True:
            try:
                ret = wayback_url_from_url(url)
                return ret
            except requests.HTTPError as e:
                if e.response.status != 429:  # noqa: PLR2004
                    print()
                    print(url)
                    print(e)
                    return None

                print("Backing off")
                time.sleep(BACKOFF)
            except Exception as e:
                print()
                print(url)
                print(e)
                return None

    df["wayback"] = df["source_link"].apply(wrapper)
    df.to_csv(path + "-wayback")


if __name__ == "__main__":
    main()

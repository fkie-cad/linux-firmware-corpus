# SPDX-FileCopyrightText: 2024 Fraunhofer FKIE
# SPDX-FileContributor: Marten Ringwelski <git@maringuu.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import pathlib as pl
import subprocess as sp
import time
import urllib.parse

import click
import pandas as pd

from . import fact, utils
from .types import Corpus, FirmwareImage, FirmwareImageStatus


def opinionated_dataframe_from_csv(csv_path: pl.Path):
    df = pd.read_csv(
        csv_path,
        index_col=0,
    )

    df = df[
        [
            "manufacturer",
            "device_name",
            "firmware_version",
            "release_date",
            "device_class",
            "filename",
            "compressed_firmware_size",
            "sha256",
            "source_link",
            "source_type",
            "wayback",
        ]
    ]
    df = df.rename(
        columns={
            "manufacturer": "vendor",
            "device_name": "device",
            "firmware_version": "version",
            "release_date": "release",
            "device_class": "class",
            "filename": "filename",
            "compressed_firmware_size": "size",
            "sha256": "sha256",
            "source_link": "url",
            "source_type": "source_type",
            "wayback": "wayback",
        },
    ).copy()

    df["filename"] = df["filename"].astype(str).apply(urllib.parse.unquote)
    df["release"] = df["release"].apply(
        lambda release: None if release == "1970-01-01" else release
    )
    df["host"] = (
        df["url"]
        .astype(str)
        .apply(urllib.parse.urlparse)
        .apply(lambda parsed: parsed.netloc)
    )

    return df


def aria2c_options_from_firmware_image(image):
    # fmt: off
    return (
        f"{image.url}\n"
        f"  out={utils.image_path_from_firmware_image(image)}\n"
        f"  checksum=sha-256={image.sha256}\n"
    )
    # fmt: on


@click.group(
    name="replicate_lfwc",
    # Ref: https://github.com/pallets/click/issues/486
    # Ref: https://github.com/ansible/molecule/commit/1de5946f606ab16be168c29eec7e8eb687a9698f
    context_settings=dict(max_content_width=9999),
)
@click.option(
    "--corpus-csv",
    type=click.Path(exists=True, path_type=pl.Path),
    help="Path to corpus.csv. Either use the file vendored with the paper, or a compatible file.",
    required=True,
)
@click.pass_context
def cli(click_ctx, corpus_csv: pl.Path):
    """Use aria2 to download LFWC"""
    click_ctx.ensure_object(dict)
    corpus_df = opinionated_dataframe_from_csv(corpus_csv)
    click_ctx.obj["corpus-df"] = corpus_df


@cli.command()
@click.option(
    "--jobs", type=click.INT, default=1, help="The number concurrent downloads"
)
@click.option(
    "--corpus-dir",
    type=click.Path(file_okay=False, dir_okay=True, exists=False, path_type=pl.Path),
    help="Path to the corpus directory.",
    required=True,
)
@click.option(
    "--continue",
    "continue_",
    is_flag=True,
    help=("Continue downloading into an existing corpus directory."),
    default=False,
)
@click.option(
    "--use-wayback-machine",
    is_flag=True,
    help=(
        "Prefer the archive.org links, if available."
        " To download all available firmwares first, invoke the script without"
        " this option. Then invoke the script a second time with --use-wayback-machine"
        " set. Due to ratelimiting this will download 5 firmwares per minute."
    ),
    default=False,
)
@click.pass_context
def download(
    click_ctx,
    corpus_dir: pl.Path,
    jobs: int,
    continue_: bool,
    use_wayback_machine: bool,
):
    """Download all missing files."""
    corpus = Corpus(
        path=corpus_dir,
        dataframe=click_ctx.obj.get("corpus-df"),
    )
    del corpus_dir

    if corpus.path.exists() and not continue_:
        try:
            _ = next(corpus.path.iterdir())
            raise click.ClickException(
                f"{corpus.path} exists and is not empty."
                " Use --continue or specify an empty/non-existant directory as --corpus-dir."
            )
        except StopIteration:
            pass

    corpus.path.mkdir(
        exist_ok=True,
        parents=False,
    )

    downloaded_images_hashes = [
        image.sha256
        for image in corpus.iter_images()
        if not (
            FirmwareImageStatus.image_has_status(
                image, corpus, FirmwareImageStatus.MISSING
            )
            or FirmwareImageStatus.image_has_status(
                image, corpus, FirmwareImageStatus.DOWNLOAD_STARTED
            )
        )
    ]

    df = corpus.dataframe
    missing_df = df[~df["sha256"].isin(downloaded_images_hashes)].copy()
    if use_wayback_machine:
        normal_df = missing_df[missing_df["wayback"].isnull()]
        _download_dataframe_to(normal_df, jobs=jobs, dest=corpus.path)

        wayback_df = missing_df[~missing_df["wayback"].isnull()].copy()
        wayback_df["url"] = wayback_df["wayback"]
        # See here for information about the rate limiting.
        # https://rationalwiki.org/wiki/Internet_Archive#Restrictions
        BACKOFF = 60
        DLS_PER_BACKOFF = 5
        for i in range(0, len(wayback_df), DLS_PER_BACKOFF):
            todo_df = wayback_df.iloc[i : i + DLS_PER_BACKOFF]
            _download_dataframe_to(todo_df, jobs=1, dest=corpus.path)
            time.sleep(BACKOFF)
    else:
        _download_dataframe_to(missing_df, jobs=jobs, dest=corpus.path)

    click.echo("Downloading finished, check failed files with\n" f" {cli.name} verify")


def _download_dataframe_to(df, jobs, dest):
    aria2_input_file = aria2_input_from_dataframe(df)

    sp.run(
        [
            "aria2c",
            "--connect-timeout=30",
            "--max-file-not-found=2",
            "--max-tries=5",
            "--lowest-speed-limit=1K",
            "--timeout=30",
            "--auto-file-renaming=false",
            "--check-certificate=false",  # linksys does not properly send x509 chain...
            f"--max-concurrent-downloads={jobs}",
            f"--split=1",
            f"--dir={dest}",
            "--input-file=-",
        ],
        input=aria2_input_file.encode(),
        check=False,
    )


@cli.command()
@click.option(
    "--corpus-dir",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        path_type=pl.Path,
    ),
    help="Path to the corpus directory.",
    required=True,
)
@click.option(
    "--json",
    "json_flag",
    is_flag=True,
    help=(
        "Print a json report of the download status of the firmware corpus to stdout."
        " The status report is a flat dictionary where keys are paths relative to"
        " the corpus directory and values are the firmware image's download status."
        " Possible values for status are: missing, download-started, hash-mismatch, and success.\n"
        " Note that missing means either that download failed,"
        " or that the file is not downloaded yet."
        " This is a limitation of aria2's api."
    ),
)
@click.pass_context
def verify(click_ctx, corpus_dir: pl.Path, json_flag: bool):
    """Prints the path and status of all firmwares that have a status other
    than 'success' to stderr.
    See --json for a description of possible values for status."""
    corpus = Corpus(
        path=corpus_dir,
        dataframe=click_ctx.obj.get("corpus-df"),
    )

    # Keys are relative paths and values are FirmwareImageStatus
    report = {}
    for image in corpus.dataframe.apply(FirmwareImage.from_row, axis=1):
        image_rel_path = utils.image_path_from_firmware_image(image)
        status = FirmwareImageStatus.from_image(image, corpus)
        if status != FirmwareImageStatus.SUCCESS:
            click.echo(
                f"{image_rel_path}:{status}",
                err=True,
            )

        report[image_rel_path] = status

    if json_flag:
        click.echo(json.dumps(report))


def aria2_input_from_dataframe(corpus_df):
    return "".join(
        corpus_df.apply(FirmwareImage.from_row, axis=1)
        .apply(aria2c_options_from_firmware_image)
        .values
    )


@cli.command()
@click.pass_context
def dump_aria2_input(click_ctx):
    """Dump the input file that can be used directly with aria2c."""
    corpus_df = click_ctx.obj.get("corpus-df")

    header = (
        "# This file can be used with the aria2 download utility [1].\n"
        "# To donwload the firmwre corpus, we suggest the following invocation of aria2:\n"
        "# ```\n"
        "# aria2c \\\n"
        "#     --connect-timeout=5 \\\n"
        "#     --max-file-not-found=2 \\\n"
        "#     --max-tries=2 \\\n"
        "#     --lowest-speed-limit=1K \\\n"
        "#     --timeout=5 \\\n"
        "#     --auto-file-renaming=false \\\n"
        "#     --save-session=session.aria2 \\\n"
        "#     --dir=path/to/corpus \\\n"
        "#     --input-file=firmwares.aria2c \n"
        "# ```\n"
        "#\n"
        "# [1]: https://aria2.github.io/\n"
    )

    aria2_input_file = aria2_input_from_dataframe(corpus_df)

    click.echo(header + aria2_input_file)


@cli.command()
@click.option(
    "--corpus-dir",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        path_type=pl.Path,
    ),
    help="Path to the corpus directory.",
    required=True,
)
@click.option(
    "--url",
    type=click.STRING,
    help="The url to the FACT instance.",
    default="http://localhost:5000",
    required=True,
)
@click.option(
    "--plugins",
    help="A list of analysis plugins that should be analyzed on the given images.",
    type=click.Choice([plugin.value for plugin in fact.Plugin]),
    multiple=True,
    show_choices=False,
    prompt=False,
)
@click.pass_context
def upload_to_fact(click_ctx, corpus_dir: pl.Path, url, plugins: list[str]):
    """Upload the firmware corpus to fact. Takes a very long time (multiple months) to complete.
    Note that you can cancel this command anytime and resume by simply starting it again.
    """
    corpus = Corpus(
        path=corpus_dir,
        dataframe=click_ctx.obj.get("corpus-df"),
    )
    ctx = fact.Context(
        url=url,
        corpus=corpus,
    )

    if not corpus.path.exists():
        raise click.ClickException(
            f"Cannot upload non-existing corpus directory {corpus.path}"
        )

    POLL_INTERVAL = 5
    MAX_CONCURRENT_ANALYSIS = 1
    GIVE_FACT_A_REST = 7
    # Sometimes analyses can get stuck as reported by various issues in FACT:
    # https://github.com/fkie-cad/FACT_core/issues/1206
    # https://github.com/fkie-cad/FACT_core/issues/1178
    # https://github.com/fkie-cad/FACT_core/issues/1163
    # [...]
    #
    # To account for this, we check how much is still to do and when nothing changes after
    # some time, we mark the analysis as stuck and continue uploading.
    # Note that we have to ensure that ALL uploaded firmwares are stuck.
    # Otherwise we cannot be sure if they are stuck or whether they are simply not
    # scheduled.
    STUCK_ANALYSES_TIMEOUT = 60

    uploaded_count = 0
    images = [
        image
        for image in corpus.iter_images()
        if not (
            FirmwareImageStatus.image_has_status(
                image, corpus, FirmwareImageStatus.MISSING
            )
            or FirmwareImageStatus.image_has_status(
                image, corpus, FirmwareImageStatus.DOWNLOAD_STARTED
            )
        )
    ]
    for image in images:
        if fact.firmware_is_uploaded(image, ctx):
            continue

        last_changed_time = time.time()
        while (
            len(uid2progress := fact.get_firmware_analysis_progress(ctx))
            > MAX_CONCURRENT_ANALYSIS
        ):
            time.sleep(POLL_INTERVAL)

            now = time.time()
            if uid2progress != fact.get_firmware_analysis_progress(ctx):
                last_changed_time = now
            elif now - last_changed_time > STUCK_ANALYSES_TIMEOUT:
                click.echo(f"Analysis are stuck: {uid2progress}", err=True)
                break

        click.echo(f"Uploading: {image}")

        try:
            fact.upload(image, plugins, ctx)
            click.echo(f"Uploading successful (uid: {fact.uid_from_image(image)}).")
            uploaded_count += 1
        except fact.UploadFailedError:
            click.echo("Uploading failed.", err=True)

        time.sleep(GIVE_FACT_A_REST)

    click.echo(f"Uploaded: {uploaded_count}")
    click.echo(f"Failed: {len(images) - uploaded_count}")


cli()

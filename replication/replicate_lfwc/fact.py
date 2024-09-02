# SPDX-FileCopyrightText: 2024 Fraunhofer FKIE
# SPDX-FileContributor: Marten Ringwelski <git@maringuu.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import base64
import enum
import pathlib as pl

import attrs
import requests

from .types import Corpus, FirmwareImage


class Plugin(str, enum.Enum):
    FILE_SYSTEM_METADATA = "file_system_metadata"
    FIL = "file name"
    CVE_LOOKUP = "cve_lookup"
    KERNEL_CONFIG = "kernel_config"
    CRYPTO_MATERIAL = "crypto_material"
    ELF_ANALYSIS = "elf_analysis"
    USERS_AND_PASSWORDS = "users_and_passwords"
    SOURCE_CODE_ANALYSIS = "source_code_analysis"
    BINWALK = "binwalk"
    DUMMY_PLUGIN_FOR_TESTING_ONLY = "dummy_plugin_for_testing_only"
    IP_AND_URI_FINDER = "ip_and_uri_finder"
    INTERESTING_URIS = "interesting_uris"
    CRYPTO_HINTS = "crypto_hints"
    INPUT_VECTORS = "input_vectors"
    TLSH = "tlsh"
    SOFTWARE_COMPONENTS = "software_components"
    INFORMATION_LEAKS = "information_leaks"
    PRINTABLE_STRINGS = "printable_strings"
    DEVICE_TREE = "device_tree"
    IPC_ANALYZER = "ipc_analyzer"
    HASHLOOKUP = "hashlookup"
    EXPLOIT_MITIGATIONS = "exploit_mitigations"
    CPU_ARCHITECTURE = "cpu_architecture"
    CWE_CHECKER = "cwe_checker"
    INIT_SYSTEMS = "init_systems"
    FILE_TYPE = "file_type"
    HARDWARE_ANALYSIS = "hardware_analysis"
    STRING_EVALUATOR = "string_evaluator"
    FILE_HASHES = "file_hashes"
    KNOWN_VULNERABILITIES = "known_vulnerabilities"
    QEMU_EXEC = "qemu_exec"


@attrs.frozen
class Context:
    url: str
    corpus: Corpus


@attrs.frozen
class FirmwareAnalysisProgress:
    uid: str
    analyzed_count: int
    unpacked_count: int

    @classmethod
    def iter_from_status_response(cls, r):
        data = r.json()
        for uid in data["system_status"]["backend"]["analysis"]["current_analyses"]:
            yield cls.from_status_response(r, uid)

    @classmethod
    def from_status_response(cls, r, uid: str) -> "FirmwareAnalysisProgress | None":
        data = r.json()
        analyses = data["system_status"]["backend"]["analysis"]["current_analyses"][uid]

        return cls(
            analyzed_count=int(analyses["analyzed_count"]),
            unpacked_count=int(analyses["unpacked_count"]),
            uid=uid,
        )


class FactError(Exception):
    pass


class UploadFailedError(FactError):
    pass


class UnknownStatusError(FactError):
    pass


def hash_from_uid(uid: str):
    return uid.split("_")[0]


def uid_from_image(image: FirmwareImage):
    return f"{image.sha256}_{image.size}"


def upload(image: FirmwareImage, plugins: list[str], ctx: Context) -> str:
    """Uploads a firmware image to FACT and returns the uid of the uploaded
    firmware."""
    image_path = ctx.corpus.image_path(image)
    if not pl.Path(image_path).exists():
        raise FileNotFoundError(f"{image_path} does not exist.")

    image_data = pl.Path(image_path).read_bytes()
    payload = {
        "binary": base64.b64encode(image_data).decode(),
        "device_class": image.class_,
        "device_name": image.device,
        "device_part": "Unknown",
        "file_name": image.filename,
        "requested_analysis_systems": plugins,
        "vendor": image.vendor,
        "version": image.version if image.version else "Unknown",
        "tags": f"source:{image.source}",
    }
    if image.release:
        payload.update({"release_date": image.release.isoformat()})

    r = requests.put(
        ctx.url + "/rest/firmware",
        json=payload,
    )

    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise UploadFailedError() from e
    answer = r.json()
    return answer["uid"]


def firmware_is_uploaded(image: FirmwareImage, ctx: Context) -> bool:
    r = requests.get(ctx.url + f"/rest/firmware/{uid_from_image(image)}")

    return r.status_code == 200  # noqa: PLR2004


def get_running_analysis_firmware_hashes(ctx: Context) -> list[str]:
    r = requests.get(ctx.url + "/rest/status")

    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise UnknownStatusError() from e

    data = r.json()
    analyses = data["system_status"]["backend"]["analysis"]["current_analyses"]

    return [hash_from_uid(uid) for uid in analyses]


def get_firmware_analysis_progress(ctx: Context) -> dict[str, FirmwareAnalysisProgress]:
    r = requests.get(ctx.url + "/rest/status")

    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise UnknownStatusError() from e

    return {
        progress.uid: progress
        for progress in FirmwareAnalysisProgress.iter_from_status_response(r)
    }

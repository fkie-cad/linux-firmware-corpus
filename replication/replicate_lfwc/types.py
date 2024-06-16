# SPDX-FileCopyrightText: 2024 Fraunhofer FKIE
# SPDX-FileContributor: Marten Ringwelski <git@maringuu.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import enum
import hashlib
import pathlib as pl

import attrs
import pandas as pd

from . import utils


@attrs.frozen
class FirmwareImage:
    vendor: str
    device: str
    version: str | None
    release: datetime.date | None
    class_: str
    # Derived from url
    filename: str
    size: int
    sha256: str
    url: str
    source: str

    @classmethod
    def from_row(cls, row) -> "FirmwareImage":
        return cls(
            vendor=row["vendor"],
            device=row["device"],
            version=row["version"],
            release=(
                datetime.date.fromisoformat(row["release"]) if row["release"] else None
            ),
            class_=row["class"],
            filename=row["filename"],
            size=row["size"],
            sha256=row["sha256"],
            url=row["url"],
            source=row["source_type"],
        )

    def __repr__(self) -> str:
        return f"{self.class_}:{self.vendor}:{self.device}:{self.version}"


class FirmwareImageStatus(str, enum.Enum):
    MISSING = "missing"
    DOWNLOAD_STARTED = "download-started"
    HASH_MISMATCH = "hash-mismatch"
    SUCCESS = "success"

    @classmethod
    def download_started(cls, image: FirmwareImage, corpus: "Corpus") -> bool:
        return pl.Path(str(corpus.image_path(image)) + ".aria2").exists()

    @classmethod
    def missing(cls, image: FirmwareImage, corpus: "Corpus") -> bool:
        return not corpus.image_path(image).exists()

    @classmethod
    def hash_mismatch(cls, image: FirmwareImage, corpus: "Corpus") -> bool:
        if cls.missing(image, corpus):
            return False
        if cls.download_started(image, corpus):
            return False

        image_path = corpus.image_path(image)

        with image_path.open("rb") as f:
            downloaded_sha256 = hashlib.file_digest(f, "sha256").hexdigest()

        return image.sha256 != downloaded_sha256

    @classmethod
    def success(cls, image: FirmwareImage, corpus: "Corpus") -> bool:
        if cls.missing(image, corpus):
            return False
        if cls.download_started(image, corpus):
            return False
        if cls.hash_mismatch(image, corpus):
            return False
        return True

    @classmethod
    def image_has_status(
        cls, image: FirmwareImage, corpus: "Corpus", status: "FirmwareImageStatus"
    ) -> bool:  # noqa: PLR0911
        match status:
            case FirmwareImageStatus.MISSING:
                return cls.missing(image, corpus)
            case FirmwareImageStatus.DOWNLOAD_STARTED:
                return cls.download_started(image, corpus)
            case FirmwareImageStatus.HASH_MISMATCH:
                return cls.hash_mismatch(image, corpus)
            case FirmwareImageStatus.SUCCESS:
                return cls.success(image, corpus)
            case _:
                assert False

    @classmethod
    def from_image(
        cls, image: FirmwareImage, corpus: "Corpus"
    ) -> "FirmwareImageStatus":  # noqa: PLR0911
        if cls.missing(image, corpus):
            return cls.MISSING

        if cls.download_started(image, corpus):
            return cls.DOWNLOAD_STARTED

        if cls.hash_mismatch(image, corpus):
            return cls.HASH_MISMATCH

        if cls.success(image, corpus):
            return cls.SUCCESS

        assert False, corpus.image_path(image)


@attrs.frozen(slots=False)
class Corpus:
    path: pl.Path
    dataframe: pd.DataFrame

    def image_path(self, image: "FirmwareImage") -> pl.Path:
        return self.path / utils.image_path_from_firmware_image(image)

    def iter_images(self, status: "FirmwareImageStatus|None" = None):
        iterator = self.dataframe.apply(FirmwareImage.from_row, axis=1)
        if status is None:
            return iterator
        return (
            image
            for image in iterator
            if FirmwareImageStatus.image_has_status(image, self, status)
        )

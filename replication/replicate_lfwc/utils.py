# SPDX-FileCopyrightText: 2024 Fraunhofer FKIE
# SPDX-FileContributor: Marten Ringwelski <git@maringuu.de>
#
# SPDX-License-Identifier: GPL-3.0-or-later


def _encode_forwared_slash(string: str):
    return string.replace("/", "%2f")


def image_path_from_firmware_image(image: "FirmwareImage") -> str:  # noqa: F821
    return "/".join(
        _encode_forwared_slash(name)
        for name in [
            image.class_,
            image.vendor,
            image.device,
            f"{image.sha256}:{image.filename}",
        ]
    )

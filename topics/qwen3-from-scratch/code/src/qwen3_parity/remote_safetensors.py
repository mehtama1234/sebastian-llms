from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from urllib.request import Request, urlopen

import torch


@dataclass(frozen=True)
class SafetensorEntry:
    dtype: str
    shape: list[int]
    data_offsets: list[int]


def _get_bytes(url: str, *, start: int, end: int) -> bytes:
    request = Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def fetch_safetensors_header_length(url: str) -> int:
    header_len_raw = _get_bytes(url, start=0, end=7)
    return struct.unpack("<Q", header_len_raw)[0]


def fetch_safetensors_header(url: str) -> dict[str, SafetensorEntry]:
    header_len = fetch_safetensors_header_length(url)
    header_raw = _get_bytes(url, start=8, end=7 + header_len)
    header_json = json.loads(header_raw)
    header: dict[str, SafetensorEntry] = {}
    for key, value in header_json.items():
        if key == "__metadata__":
            continue
        header[key] = SafetensorEntry(
            dtype=value["dtype"],
            shape=value["shape"],
            data_offsets=value["data_offsets"],
        )
    return header


def dtype_from_name(name: str) -> torch.dtype:
    mapping = {
        "BF16": torch.bfloat16,
        "F16": torch.float16,
        "F32": torch.float32,
        "F64": torch.float64,
        "I64": torch.int64,
        "I32": torch.int32,
        "I16": torch.int16,
        "I8": torch.int8,
        "U8": torch.uint8,
    }
    if name not in mapping:
        raise ValueError(f"Unsupported dtype {name}")
    return mapping[name]


def fetch_safetensors_tensor(
    url: str,
    *,
    header_len: int,
    entry: SafetensorEntry,
) -> torch.Tensor:
    start, end = entry.data_offsets
    data_start = 8 + header_len
    raw = _get_bytes(url, start=data_start + start, end=data_start + end - 1)
    tensor = torch.frombuffer(bytearray(raw), dtype=dtype_from_name(entry.dtype)).clone()
    return tensor.reshape(entry.shape)

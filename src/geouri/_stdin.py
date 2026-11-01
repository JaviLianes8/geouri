"""Decode stdin records with recoverable errors and universal newlines."""

from __future__ import annotations

import codecs
import io
from collections.abc import Iterable
from typing import TextIO


def _mark_error(error: UnicodeError) -> tuple[str, int]:
    if not isinstance(error, UnicodeDecodeError):
        raise error
    # A surrogate marks a decoding failure without confusing valid U+FFFD text.
    return "\udcff", error.end


codecs.register_error("geouri.stdin", _mark_error)


def lines(stream: TextIO) -> Iterable[str | None]:
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        yield from _records(stream)
        return
    # Keep one decoder for the whole batch, including BOM and shift state.
    reader = io.TextIOWrapper(buffer, encoding=stream.encoding, errors="geouri.stdin", newline=None)
    try:
        yield from _records(reader)
    finally:
        # The caller retains ownership of stdin and its underlying buffer.
        reader.detach()


def _records(stream: TextIO) -> Iterable[str | None]:
    for line in stream:
        text = line.rstrip("\r\n")
        if "\udcff" in text:
            yield None
        elif text:
            yield text

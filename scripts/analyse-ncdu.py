#!/usr/bin/env python3
import csv
import io
import json
import sys
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Union

import click


class FileType(Enum):
    FILE = "file"
    OTHER = "other"
    DIR = "dir"

    def __str__(self):
        return self.value


@dataclass
class Entry:
    full_path: Path
    file_type: FileType
    size: Optional[int]

    @property
    def size_or_type(self) -> Union[int, FileType]:
        return self.size if self.size is not None else self.file_type


class EntryField(Enum):
    PATH = "full_path"
    SIZE = "size_or_type"

    @property
    def field_name(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.name.lower()


class Output(metaclass=ABCMeta):
    stream: io.IOBase
    entry_filter: Callable[[Entry], bool]

    def __init__(self, stream):
        self.stream = stream
        self.entry_filter = lambda _: True

    def handle_raw_entry(self, parent: Path, data, *, is_dir: bool) -> Path:
        if isinstance(data, list):
            assert is_dir, "List should correspond to a directory"
            data_iter = iter(data)
            raw_root = next(data_iter)
            if "excluded" in raw_root:
                return
            assert isinstance(raw_root, dict), repr(raw_root)
            root_path = self.handle_raw_entry(parent, raw_root, is_dir=True)
            for child_data in data_iter:
                self.handle_raw_entry(root_path, child_data, is_dir=isinstance(child_data, list))
            return root_path
        elif isinstance(data, dict):
            # format: https://dev.yorhel.nl/ncdu/jsonfmt
            if "excluded" in data:
                return
            name = data["name"]
            if data.get("notreg"):
                file_type = FileType.OTHER
                size = data.get("asize")
                if size is not None:
                    size = int(size)
            elif is_dir:
                file_type = FileType.DIR
                size = None
            else:
                file_type = FileType.FILE
                try:
                    size = int(data["asize"])
                except KeyError:
                    size = 0
            full_path = parent / name
            self.write_entry(
                Entry(
                    full_path=full_path,
                    file_type=file_type,
                    size=size,
                )
            )
            return full_path
        else:
            raise TypeError(type(data))

    @abstractmethod
    def write_entry(self, entry: Entry):
        pass

    def close(self):
        self.stream.close()


class PlainOutput(Output):
    value_field: Optional[EntryField]

    def __init__(self, stream, value_field: Optional[EntryField]):
        super(PlainOutput, self).__init__(stream)
        assert value_field is None or isinstance(value_field, EntryField), repr(value_field)
        self.value_field = value_field

    def write_entry(self, entry: Entry):
        if not self.entry_filter(entry):
            return
        res = [str(entry.full_path)]
        if self.value_field is not None:
            res.append(str(getattr(entry, self.value_field.field_name)))
        self.stream.write(" ".join(res) + "\n")


class CSVOutput(Output):
    fields: list[EntryField]
    writer: csv.writer

    def __init__(self, stream, fields: list[EntryField]):
        super(CSVOutput, self).__init__(stream)
        self.fields = fields
        assert EntryField.PATH in self.fields, f"Fields needs path: {fields!r}"
        self.writer = csv.writer(stream)
        self.writer.writerow(list(map(str, self.fields)))

    def write_entry(self, entry: Entry):
        if not self.entry_filter(entry):
            return
        self.writer.writerow([str(getattr(entry, field.field_name)) for field in self.fields])


@click.command()
@click.option(
    "input_file",
    "--file",
    required=True,
    type=click.Path(exists=True, file_okay=True, path_type=Path),
    help="The input ncdu database to read",
)
@click.option("--include-sizes", "--sizes", is_flag=True, help="Include the sizes in the output")
@click.option("--ignore-dirs", is_flag=True, help="Ignore directories")
@click.option(
    "output_format",
    "-f",
    "--format",
    default="plain",
    type=click.Choice(["plain", "csv"]),
    required=True,
    help="The output format",
)
@click.option(
    "output_file",
    "-o",
    "--out",
    type=click.File(mode="wt"),
    help="The output file",
    default="-",
)
def analyse_ncdu(input_file, include_sizes, output_format, output_file, ignore_dirs):
    with open(input_file, "rt") as f:
        data = json.load(f)
    match output_format:
        case "plain":
            output = PlainOutput(output_file, EntryField.SIZE if include_sizes else None)
        case "csv":
            fields = [EntryField.PATH]
            if include_sizes:
                fields.append(EntryField.SIZE)
            output = CSVOutput(output_file, fields)
        case _:
            raise AssertionError(output_format)
    handled_entries = set()

    def should_keep(entry):
        if ignore_dirs and entry.file_type == FileType.DIR:
            return False
        else:
            handled_entries.add(entry.full_path)
            return True

    output.entry_filter = should_keep
    assert isinstance(data[3], list)
    root_path = output.handle_raw_entry(Path(), data[3], is_dir=True)
    print(f"Handled {len(handled_entries)} entries in {root_path}", file=sys.stderr)


if __name__ == "__main__":
    analyse_ncdu()

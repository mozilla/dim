import logging
from os import path
from pathlib import Path


def create_directory(path_to_create: Path) -> bool:
    logging.info("Creating directory: %s" % path_to_create)
    path_to_create.mkdir(parents=True)
    return True


def check_directory_exists(path_to_check: Path) -> bool:
    return path.exists(path_to_check)


def sql_to_file(target_file: Path, sql: str) -> bool:
    with open(target_file, "w+") as _file:
        _file.write(sql)
    return True

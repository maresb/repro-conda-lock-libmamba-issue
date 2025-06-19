#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import typing as t
from functools import partial

import ruamel.yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create/update environment <env> from ./conda-lock.yml")
    parser.add_argument("env", metavar="ENV", help="kernel env name")
    return parser.parse_args()


def run_command(command: t.Sequence[str]) -> None:
    print(f"Running {" ".join(command)}")
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        print(f"Command exited {e.returncode}: {" ".join(command)}")
        raise SystemExit(1)


def main() -> None:
    args = parse_args()
    lockfile = "conda-lock.yml"
    env_dir = os.path.expanduser(f"~/.conda/{args.env}")
    # Until conda-lock provides its own 'upsert' functionality, consumers need to implement our own
    # "already up-to-date?" check. Ref: https://github.com/conda/conda-lock/issues/751
    if up_to_date(env_dir, lockfile):
        print(f"{env_dir} matches {lockfile} already, nothing to do")
    else:
        print(f"{env_dir} does not match {lockfile}, updating...")
        run_command(("rm", "-rf", env_dir))
        run_command(("conda-lock", "install", "-n", args.env, lockfile))


def up_to_date(env_dir: str, lockfile: str) -> bool:
    if not os.path.exists(env_dir):
        return False
    try:
        want = dist_names_from_lockfile(lockfile)
    except Exception as e:
        print(f"Error checking lockfile {lockfile}: {e} -> treating {env_dir} as out-of-date")
        return False
    try:
        have = dist_names_from_env(env_dir)
    except Exception as e:
        print(f"Error checking env {env_dir}: {e} {getattr(e, 'output', '')} -> treating {env_dir} as out-of-date")
        return False
    return want == have


def dist_names_from_lockfile(lockfile: str) -> set[str]:
    with open(lockfile) as f:
        data = ruamel.yaml.YAML(typ="safe").load(f)["package"]
        return {
            dist_name_from_url(pkg["url"])
            for pkg in data
            # Any pip packages in lockfile won't be visible to 'conda list', so raise in this case.
            # The AssertionError is caught by the caller and the env will be treated as out-of-date.
            if assert_conda_pkg(pkg)
        }


def assert_conda_pkg(pkg: dict[str, str]) -> bool:
    assert pkg["manager"] == "conda", f"Package {pkg['name']} is not a conda package"
    return True


def dist_name_from_url(url: str) -> str:
    _, _, filename = url.rpartition("/")
    for suffix in (".tar.bz2", ".conda"):
        if filename.endswith(suffix):
            return filename.removesuffix(suffix)
    raise ValueError(f"Unexpected filename: {filename}")


def dist_names_from_env(env_dir: str) -> set[str]:
    output = subprocess.check_output(["mamba", "list", "--json", "-p", env_dir])
    data = json.loads(output)
    return {pkg["dist_name"] for pkg in data}


if __name__ == "__main__":
    main()

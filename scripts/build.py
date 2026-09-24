#!/usr/bin/env python3
"""Build one build.yaml target in a clean west workspace, including local patches."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd, capture=False):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), cwd=cwd, check=True,
                          text=True, stdout=subprocess.PIPE if capture else None).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target")
    args = parser.parse_args()
    matrix = yaml.safe_load((ROOT / "build.yaml").read_text())["include"]
    target = next(item for item in matrix if item["artifact-name"] == args.target)
    output = ROOT / "build-output" / args.target
    output.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix="sofle-west-", dir=os.getenv("RUNNER_TEMP")))
    shutil.copytree(ROOT / "config", workspace / "config")
    run("west", "init", "-l", "config", cwd=workspace)
    run("west", "update", "--fetch-opt=--filter=tree:0", cwd=workspace)

    projects = yaml.safe_load((ROOT / "config/west.yml").read_text())["manifest"]["projects"]
    for project in projects:
        actual = run("git", "rev-parse", "HEAD", cwd=workspace / project["name"], capture=True).strip()
        if actual != project["revision"]:
            raise RuntimeError(f"Unexpected {project['name']} revision: {actual}")
        print(f"Verified {project['name']}: {actual}", flush=True)
    # Import order must preserve ZMK's module overrides, not Zephyr's defaults.
    zmk_projects = yaml.safe_load((workspace / "zmk/app/west.yml").read_text())["manifest"]["projects"]
    for project in zmk_projects:
        if project["name"] in ("lvgl", "hal_stm32"):
            actual = run("west", "list", "-f", "{revision}", project["name"],
                         cwd=workspace, capture=True).strip()
            if actual != project["revision"]:
                raise RuntimeError(f"Lost ZMK override for {project['name']}: {actual}")
    manifest = run("west", "manifest", "--freeze", cwd=workspace, capture=True)
    (output / "west-frozen.yml").write_text(manifest)
    checksums = []
    for patch in sorted((ROOT / "patches").glob("*.patch")):
        run("git", "apply", "--check", patch, cwd=workspace / "zmk")
        run("git", "apply", patch, cwd=workspace / "zmk")
        checksums.append(f"{hashlib.sha256(patch.read_bytes()).hexdigest()}  {patch.name}")
    (output / "patches.sha256").write_text("\n".join(checksums) + "\n")
    (output / "config-commit.txt").write_text(run("git", "rev-parse", "HEAD", cwd=ROOT, capture=True))
    run("python3", ROOT / "tests/test_split_input_queue.py", workspace / "zmk", cwd=ROOT)
    run("west", "zephyr-export", cwd=workspace)

    build = workspace / "build"
    command = ["west", "build", "-s", "zmk/app", "-d", str(build), "-b", target["board"]]
    if target.get("snippet"):
        command += ["-S", target["snippet"]]
    command += ["--", f"-DZMK_CONFIG={workspace / 'config'}",
                f"-DZMK_EXTRA_MODULES={ROOT}", f"-DSHIELD={target['shield']}"]
    try:
        run(*command, cwd=workspace)
        config = (build / "zephyr/.config").read_text()
        expected = ["CONFIG_ZMK_BOARD_COMPAT=y"]
        if args.target != "settings-reset":
            expected += ["CONFIG_BT_SMP_SC_PAIR_ONLY=y", "CONFIG_BT_BUF_ACL_TX_COUNT=8"]
        if args.target == "sofle-right":
            expected += ["CONFIG_ZMK_INPUT_SPLIT_MSG_QUEUE_SIZE=32", "CONFIG_INPUT_MODE_THREAD=y"]
        if args.target == "sofle-left":
            expected += ["CONFIG_LOG_MODE_DEFERRED=y"]
        for setting in expected:
            if setting not in config.splitlines():
                raise RuntimeError(f"Missing expected resolved setting: {setting}")
        shutil.copy2(build / "zephyr/zmk.uf2", output / f"{args.target}.uf2")
        uf2 = output / f"{args.target}.uf2"
        (output / "firmware.sha256").write_text(f"{hashlib.sha256(uf2.read_bytes()).hexdigest()}  {uf2.name}\n")
    finally:
        for source, dest in [(".config", "resolved.config"), ("zephyr.dts", "zephyr.dts"),
                             ("zmk.elf", "zmk.elf"), ("zmk.map", "zmk.map")]:
            path = build / "zephyr" / source
            if path.exists():
                shutil.copy2(path, output / dest)
    print(f"Firmware and diagnostics: {output}", flush=True)


if __name__ == "__main__":
    main()

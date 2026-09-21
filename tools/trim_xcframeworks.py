#!/usr/bin/env python3
"""Drop unused platform slices from the built xcframeworks.

RevenueCat ships slices for every Apple platform (tvOS, watchOS, visionOS,
macOS, Mac Catalyst); a Godot iOS export only links the iOS device slice and,
for simulator runs, the iOS simulator slice. The other slices are ~750 MB that
would otherwise be committed into every consuming game repo on each SDK bump.

Each xcframework's Info.plist lists its slices under AvailableLibraries; Xcode
validates that list against the directories present, so both are updated
together.

Usage: trim_xcframeworks.py <plugins dir> <keep-identifier> [<keep-identifier> ...]
"""
import plistlib
import shutil
import sys
from pathlib import Path


def trim(xcframework: Path, keep: set[str]) -> tuple[int, int]:
    plist_path = xcframework / "Info.plist"
    with plist_path.open("rb") as f:
        manifest = plistlib.load(f)
    libraries = manifest.get("AvailableLibraries", [])
    kept = [lib for lib in libraries if lib.get("LibraryIdentifier") in keep]
    if not kept:
        raise SystemExit(f"{xcframework.name}: none of {sorted(keep)} present; refusing to empty it")
    removed = 0
    for lib in libraries:
        identifier = lib.get("LibraryIdentifier", "")
        if identifier in keep:
            continue
        slice_dir = xcframework / identifier
        if slice_dir.is_dir():
            shutil.rmtree(slice_dir)
            removed += 1
    manifest["AvailableLibraries"] = kept
    with plist_path.open("wb") as f:
        plistlib.dump(manifest, f)
    # Stray directories that were never in the manifest are left alone.
    return len(kept), removed


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    root = Path(sys.argv[1])
    keep = set(sys.argv[2:])
    frameworks = sorted(root.glob("*.xcframework"))
    if not frameworks:
        raise SystemExit(f"no xcframeworks under {root}")
    for xcframework in frameworks:
        kept, removed = trim(xcframework, keep)
        print(f"  • {xcframework.name}: kept {kept} slice(s), removed {removed}")


if __name__ == "__main__":
    main()

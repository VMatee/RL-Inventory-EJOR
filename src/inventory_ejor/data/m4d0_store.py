"""Bounded POSIX durable publication of private synthetic JSON artifacts.

Temporary files and final artifacts share a directory/filesystem. Publication
uses link(2), which never replaces a destination. Successful put synchronizes
both the artifact and its directory, including when retrying an existing object.
This is local filesystem durability, not authenticated or append-only evidence.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path

from .protocol import require, sha256_id
from .provenance import canonical, read_json

PRIVATE_MAX_BYTES = 8 * 1024 * 1024


class PendingArtifactCleanupError(OSError):
    """Owned temporary deletion failed; the chained cause is the OS error."""

    def __init__(self, path):
        self.pending_path = path
        super().__init__(
            f"Private artifact cleanup failed for {path}; stop retries and recover "
            "only after all store writers are quiescent"
        )


class PrivateExecutionStore:
    """User-owned 0700 store outside Git worktrees, rechecked at every access.

    Failed pre-publication writes leave no final artifact. A failure after link
    may leave correct final bytes, but is never success; a retry synchronizes
    them again. Process death or failed cleanup may leave .pending-* files:
    they are not artifacts and must only be removed by an owner after confirming
    no writer is active. Repeated cleanup failures can accumulate these orphans.
    Hostile same-user writers and hardware that lies about fsync are out of scope.
    """

    def __init__(self, directory):
        self.root = Path(directory).absolute()
        self._check_root()

    def _check_root(self):
        require(
            self.root.is_dir() and self.root == self.root.resolve(),
            "Pre-existing canonical private execution directory required",
        )
        info = self.root.stat()
        require(
            info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
            "Private execution directory must be owned by caller with mode 0700",
        )
        require(
            not any(
                (p / ".git").exists() or (p / ".git").is_symlink()
                for p in (self.root, *self.root.parents)
            ),
            "Private M4d0 artifacts cannot be written into a Git worktree",
        )
        return info

    @contextmanager
    def _directory(self):
        info = self._check_root()
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            live = os.fstat(fd)
            require(
                (live.st_dev, live.st_ino) == (info.st_dev, info.st_ino),
                "Private store directory changed",
            )
            yield fd
            after = self._check_root()
            require(
                (live.st_dev, live.st_ino) == (after.st_dev, after.st_ino),
                "Private store directory changed",
            )
        finally:
            os.close(fd)

    def _path(self, digest):
        self._check_root()
        sha256_id(digest, "private content hash")
        path = self.root / (digest + ".json")
        require(
            not path.is_symlink(), "Private store symlink/path substitution refused"
        )
        return path

    @staticmethod
    @contextmanager
    def _artifact(directory, name):
        fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        try:
            info = os.fstat(fd)
            require(
                stat.S_ISREG(info.st_mode)
                and info.st_uid == os.getuid()
                and stat.S_IMODE(info.st_mode) == 0o600
                and info.st_size <= PRIVATE_MAX_BYTES,
                "Nonprivate, nonregular or oversized private artifact",
            )
            yield fd
        finally:
            os.close(fd)

    @staticmethod
    def _bytes(fd):
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, PRIVATE_MAX_BYTES + 1 - size))
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
            size += len(chunk)
            require(size <= PRIVATE_MAX_BYTES, "Oversized private artifact")

    def _sync_existing(self, directory, name, data):
        with self._artifact(directory, name) as fd:
            require(self._bytes(fd) == data, "Existing artifact content changed")
            os.fsync(fd)

    def _remove_pending(self, directory, temporary):
        try:
            os.unlink(temporary, dir_fd=directory)
        except OSError as exc:
            raise PendingArtifactCleanupError(self.root / temporary) from exc

    def put(self, value):
        data = canonical(value)
        require(len(data) <= PRIVATE_MAX_BYTES, "Oversized private artifact")
        digest = hashlib.sha256(data).hexdigest()
        name = self._path(digest).name
        with self._directory() as directory:
            try:
                self._sync_existing(directory, name, data)
            except FileNotFoundError:
                temporary = ".pending-" + secrets.token_hex(16)
                fd = os.open(
                    temporary,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                try:
                    try:
                        # Enforce the artifact contract even under a restrictive umask.
                        os.fchmod(fd, 0o600)
                        remaining = memoryview(data)
                        while remaining:
                            written = os.write(fd, remaining)
                            if written <= 0:
                                raise OSError("Private artifact write made no progress")
                            remaining = remaining[written:]
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                    try:
                        os.link(
                            temporary,
                            name,
                            src_dir_fd=directory,
                            dst_dir_fd=directory,
                            follow_symlinks=False,
                        )
                    except FileExistsError:
                        self._sync_existing(directory, name, data)
                except BaseException as primary:
                    # Preserve cancellation and the original persistence error.
                    # Cleanup is attempted once, only for this call's own file.
                    try:
                        self._remove_pending(directory, temporary)
                    except PendingArtifactCleanupError as cleanup:
                        raise primary from cleanup
                    raise
                else:
                    self._remove_pending(directory, temporary)
            # Required even for identical existing bytes or a failed prior call.
            os.fsync(directory)
        return digest

    def read(self, digest, *, kind=None):
        name = self._path(digest).name
        try:
            with self._directory() as directory, self._artifact(directory, name) as fd:
                raw = self._bytes(fd)
        except FileNotFoundError as exc:
            raise ValueError("Missing private execution artifact") from exc
        item = read_json(raw)
        require(
            hashlib.sha256(raw).hexdigest() == digest and raw == canonical(item),
            "Private execution artifact modified or noncanonical",
        )
        require(
            type(item) is dict and (kind is None or item.get("kind") == kind),
            "Wrong execution artifact kind",
        )
        return item

    def file(self, digest):
        """Pinned filename for load_learner, which rehashes its consumed bytes."""
        self.read(digest)
        return self._path(digest)

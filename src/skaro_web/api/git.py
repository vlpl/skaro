"""Git integration endpoints.

Provides repository status, staging, committing, pushing, and branch
management through the Skaro Dashboard UI.  Uses ``gitpython`` which is
already a project dependency.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from skaro_web.api.deps import broadcast, get_project_root
from skaro_web.api.schemas import (
    GitCommitBody,
    GitStageBody,
    GitCheckoutBody,
)

logger = logging.getLogger("skaro_web")

router = APIRouter(prefix="/api/git", tags=["git"])


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════

def _get_repo(project_root: Path):
    """Open the git repo at *project_root*. Raises if not a repo."""
    from git import InvalidGitRepositoryError, Repo

    try:
        return Repo(project_root)
    except InvalidGitRepositoryError:
        return None


def _file_status_list(repo) -> list[dict[str, str]]:
    """Build a list of changed / untracked files with their status."""
    files: list[dict[str, str]] = []

    # Staged (index vs HEAD)
    for diff in repo.index.diff("HEAD"):
        files.append({
            "path": diff.a_path or diff.b_path,
            "status": "staged",
            "change": diff.change_type,  # A, M, D, R, …
        })

    # Unstaged (working tree vs index)
    for diff in repo.index.diff(None):
        files.append({
            "path": diff.a_path or diff.b_path,
            "status": "modified",
            "change": diff.change_type,
        })

    # Untracked
    for path in repo.untracked_files:
        files.append({"path": path, "status": "untracked", "change": "A"})

    return files


def _diff_for_file(repo, filepath: str) -> str:
    """Return a unified diff string for a single file."""
    try:
        # Unstaged diff (working tree vs index)
        diff_text = repo.git.diff("--", filepath)
        if diff_text:
            return diff_text

        # Staged diff (index vs HEAD)
        diff_text = repo.git.diff("--cached", "--", filepath)
        if diff_text:
            return diff_text

        # Untracked — show full content as addition
        full_path = Path(repo.working_dir) / filepath
        if full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                diff_lines = [f"--- /dev/null", f"+++ b/{filepath}"]
                diff_lines.append(f"@@ -0,0 +1,{len(lines)} @@")
                for line in lines:
                    diff_lines.append(f"+{line}")
                return "\n".join(diff_lines)
            except Exception:
                return "(binary or unreadable file)"

        return ""
    except Exception as exc:
        return f"(error getting diff: {exc})"


def _stage_files(repo, project_root: Path, files: list[str]) -> tuple[int, list[str]]:
    """Stage a list of files, handling manual deletions gracefully.

    * Files that **exist on disk** are staged with ``git add`` (add/modify).
    * Files **missing from disk but present in the index** are staged as
      deletions with ``git rm`` — equivalent to the user running
      ``git rm <file>`` after a manual delete.
    * Files that exist **neither on disk nor in the index** are skipped with
      a warning so a stale path never causes a 500 error.

    Returns:
        (staged_count, skipped_paths)
    """
    to_add: list[str] = []
    to_remove: list[str] = []
    skipped: list[str] = []

    # Build the set of paths currently tracked in the index.
    indexed: set[str] = (
        {entry.path for entry in repo.index.entries.values()}
        if repo.head.is_valid()
        else set()
    )

    for f in files:
        full = Path(repo.working_dir) / f
        if full.exists():
            to_add.append(f)
        elif f in indexed:
            # File was manually deleted — stage the deletion.
            to_remove.append(f)
        else:
            logger.warning(
                "git stage: skipping '%s' — not on disk and not tracked in index", f
            )
            skipped.append(f)

    if to_add:
        repo.index.add(to_add)
    if to_remove:
        repo.index.remove(to_remove, working_tree=False)

    staged = len(to_add) + len(to_remove)
    return staged, skipped


# ═══════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════

@router.get("/status")
async def git_status(project_root: Path = Depends(get_project_root)):
    """Return repository status: branch, files, remotes."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return {"is_repo": False}

    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "(detached HEAD)"

    branches = [b.name for b in repo.branches]
    has_remote = bool(repo.remotes)
    remote_name = repo.remotes[0].name if has_remote else None

    files = await asyncio.to_thread(_file_status_list, repo)

    staged_count = sum(1 for f in files if f["status"] == "staged")
    modified_count = sum(1 for f in files if f["status"] == "modified")
    untracked_count = sum(1 for f in files if f["status"] == "untracked")

    return {
        "is_repo": True,
        "branch": branch,
        "branches": branches,
        "has_remote": has_remote,
        "remote_name": remote_name,
        "files": files,
        "staged_count": staged_count,
        "modified_count": modified_count,
        "untracked_count": untracked_count,
    }


@router.get("/diff")
async def git_diff(
    file: str,
    project_root: Path = Depends(get_project_root),
):
    """Return unified diff for a single file."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    diff = await asyncio.to_thread(_diff_for_file, repo, file)
    return {"file": file, "diff": diff}


@router.post("/stage")
async def git_stage(
    request: Request,
    payload: GitStageBody,
    project_root: Path = Depends(get_project_root),
):
    """Stage (git add / git rm) selected files.

    Files missing from disk are staged as deletions instead of raising an
    error, so manually deleted files can be committed normally.
    """
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    try:
        staged, skipped = await asyncio.to_thread(
            _stage_files, repo, project_root, payload.files
        )
        await broadcast(request, {"event": "git:staged", "files": payload.files})
        msg = f"Staged {staged} file(s)"
        if skipped:
            msg += f"; skipped {len(skipped)} missing file(s): {', '.join(skipped)}"
        return {"success": True, "message": msg, "skipped": skipped}
    except Exception as exc:
        logger.error("git stage error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})


@router.post("/unstage")
async def git_unstage(
    request: Request,
    payload: GitStageBody,
    project_root: Path = Depends(get_project_root),
):
    """Unstage (git reset HEAD) selected files."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    try:
        await asyncio.to_thread(repo.index.reset, paths=payload.files)
        await broadcast(request, {"event": "git:unstaged", "files": payload.files})
        return {"success": True, "message": f"Unstaged {len(payload.files)} file(s)"}
    except Exception as exc:
        logger.error("git unstage error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})


@router.post("/commit")
async def git_commit(
    request: Request,
    payload: GitCommitBody,
    project_root: Path = Depends(get_project_root),
):
    """Commit staged changes with a message. Optionally push afterwards."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    # Verify there are staged changes
    staged = list(repo.index.diff("HEAD"))
    if not staged and not repo.untracked_files:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Nothing staged to commit"},
        )

    try:
        commit = await asyncio.to_thread(repo.index.commit, payload.message)
        result: dict[str, Any] = {
            "success": True,
            "message": f"Committed: {commit.hexsha[:8]}",
            "sha": commit.hexsha,
            "pushed": False,
        }

        if payload.push:
            if not repo.remotes:
                result["push_error"] = "No remote configured"
            else:
                remote = repo.remotes[0]
                branch = repo.active_branch.name
                try:
                    await asyncio.to_thread(remote.push, branch)
                    result["pushed"] = True
                    result["message"] += f" and pushed to {remote.name}/{branch}"
                except Exception as push_exc:
                    result["push_error"] = str(push_exc)

        await broadcast(request, {
            "event": "git:committed",
            "sha": commit.hexsha[:8],
            "pushed": result["pushed"],
        })
        return result

    except Exception as exc:
        logger.error("git commit error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})


@router.post("/push")
async def git_push(
    request: Request,
    project_root: Path = Depends(get_project_root),
):
    """Push current branch to remote."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    if not repo.remotes:
        return JSONResponse(status_code=400, content={"success": False, "message": "No remote configured"})

    try:
        remote = repo.remotes[0]
        branch = repo.active_branch.name
        await asyncio.to_thread(remote.push, branch)
        await broadcast(request, {"event": "git:pushed", "branch": branch})
        return {"success": True, "message": f"Pushed to {remote.name}/{branch}"}
    except Exception as exc:
        logger.error("git push error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})


@router.get("/branches")
async def git_branches(project_root: Path = Depends(get_project_root)):
    """List local branches and current branch."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    try:
        current = repo.active_branch.name
    except TypeError:
        current = "(detached)"

    branches = [b.name for b in repo.branches]
    return {"current": current, "branches": branches}


@router.post("/checkout")
async def git_checkout(
    request: Request,
    payload: GitCheckoutBody,
    project_root: Path = Depends(get_project_root),
):
    """Switch to an existing branch or create a new one."""
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Not a git repository"})

    try:
        if payload.create:
            await asyncio.to_thread(repo.git.checkout, "-b", payload.branch)
            msg = f"Created and switched to branch: {payload.branch}"
        else:
            await asyncio.to_thread(repo.git.checkout, payload.branch)
            msg = f"Switched to branch: {payload.branch}"

        await broadcast(request, {"event": "git:checkout", "branch": payload.branch})
        return {"success": True, "message": msg}
    except Exception as exc:
        logger.error("git checkout error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})


# ═══════════════════════════════════════════════════
# Auto-stage helper (called from tasks.py after apply)
# ═══════════════════════════════════════════════════

async def auto_stage_file(project_root: Path, filepath: str) -> bool:
    """Stage a single file after it was applied. Returns True on success.

    Handles the case where the file no longer exists on disk (manual
    deletion) by staging it as a deletion rather than raising an error.
    """
    repo = await asyncio.to_thread(_get_repo, project_root)
    if repo is None:
        return False
    try:
        staged, skipped = await asyncio.to_thread(
            _stage_files, repo, project_root, [filepath]
        )
        if skipped:
            logger.warning(
                "Auto-stage skipped '%s': not on disk and not tracked in index", filepath
            )
            return False
        logger.info("Auto-staged: %s", filepath)
        return True
    except Exception as exc:
        logger.warning("Auto-stage failed for %s: %s", filepath, exc)
        return False
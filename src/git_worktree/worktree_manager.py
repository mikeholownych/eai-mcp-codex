"""Git Worktree management business logic implementation."""

import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.common.logging import get_logger
from src.common.database import (
    DatabaseManager,
    serialize_json_field,
    deserialize_json_field,
    serialize_datetime,
    deserialize_datetime,
)
from .models import (
    Repo,
    Worktree,
    BranchInfo,
    WorktreeStatus,
    WorktreeRequest,
    WorktreeOperation,
)
from .config import settings

logger = get_logger("worktree_manager")


class WorktreeManager:
    """Core business logic for Git worktree operations."""

    def __init__(self, dsn: str = settings.database_url):
        self.db_manager = DatabaseManager(dsn)
        self.dsn = dsn

    async def initialize_database(self):
        """Initialize database connection and create tables if they don't exist."""
        await self.db_manager.connect()
        await self._ensure_database()

    async def shutdown_database(self):
        """Shutdown database connection pool."""
        await self.db_manager.disconnect()

    async def _ensure_database(self):
        """Create database and tables if they don't exist."""
        script = """
                CREATE TABLE IF NOT EXISTS repos (
                    name TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    remote_url TEXT,
                    default_branch TEXT DEFAULT 'main',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS worktrees (
                    id TEXT PRIMARY KEY,
                    repo_name TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'active',
                    is_bare BOOLEAN DEFAULT FALSE,
                    is_detached BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP WITH TIME ZONE,
                    commit_hash TEXT,
                    upstream_branch TEXT,
                    metadata JSONB DEFAULT '{}',
                    FOREIGN KEY (repo_name) REFERENCES repos (name) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS worktree_operations (
                    id SERIAL PRIMARY KEY,
                    operation TEXT NOT NULL,
                    worktree_id TEXT NOT NULL,
                    params JSONB DEFAULT '{}',
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    success BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    result JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_worktrees_repo ON worktrees(repo_name);
                CREATE INDEX IF NOT EXISTS idx_worktrees_status ON worktrees(status);
                CREATE INDEX IF NOT EXISTS idx_operations_worktree ON worktree_operations(worktree_id);
            """
        logger.info(f"Attempting to create tables in {self.dsn}")
        await self.db_manager.execute_script(script)
        logger.info("Database tables ensured.")

    async def register_repo(self, name: str, path: str, remote_url: str = None) -> Repo:
        """Register a Git repository for worktree management."""
        repo_path = Path(path).resolve()

        if not self._is_git_repo(repo_path):
            raise ValueError(f"Path is not a Git repository: {repo_path}")

        # Get default branch
        default_branch = self._get_default_branch(repo_path)

        repo = Repo(
            name=name,
            path=str(repo_path),
            remote_url=remote_url or self._get_remote_url(repo_path),
            default_branch=default_branch,
        )

        query = """
            INSERT INTO repos (name, path, remote_url, default_branch, metadata)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (name) DO UPDATE SET
                path = EXCLUDED.path,
                remote_url = EXCLUDED.remote_url,
                default_branch = EXCLUDED.default_branch,
                metadata = EXCLUDED.metadata
        """
        values = (
            repo.name,
            repo.path,
            repo.remote_url,
            repo.default_branch,
            serialize_json_field(repo.metadata),
        )
        await self.db_manager.execute_update(query, values)

        logger.info(f"Registered repository: {name} at {path}")
        return repo

    async def create_worktree(self, request: WorktreeRequest) -> Worktree:
        """Create a new Git worktree."""
        repo = await self.get_repo(request.repo_name)
        if not repo:
            raise ValueError(f"Repository not found: {request.repo_name}")

        # Generate worktree path if not provided
        if not request.path:
            worktree_path = (
                Path(repo.path).parent
                / "worktrees"
                / request.repo_name
                / request.branch
            )
        else:
            worktree_path = Path(request.path)

        worktree_path.mkdir(parents=True, exist_ok=True)

        operation = WorktreeOperation(
            operation="create",
            worktree_id=str(uuid.uuid4()),
            params={
                "repo_name": request.repo_name,
                "branch": request.branch,
                "path": str(worktree_path),
                "create_branch": request.create_branch,
            },
        )

        try:
            # Execute git worktree add command
            cmd = ["git", "worktree", "add"]

            if request.create_branch:
                cmd.extend(["-b", request.branch])

            cmd.append(str(worktree_path))

            if not request.create_branch and request.checkout_existing:
                cmd.append(request.branch)

            self._run_git_command(cmd, cwd=repo.path)

            # Get commit hash
            commit_hash = self._get_commit_hash(worktree_path)

            # Create worktree record
            worktree = Worktree(
                id=operation.worktree_id,
                repo_name=request.repo_name,
                branch=request.branch,
                path=str(worktree_path),
                commit_hash=commit_hash,
                metadata=request.metadata,
            )

            query = """
                INSERT INTO worktrees (
                    id, repo_name, branch, path, commit_hash, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """
            values = (
                worktree.id,
                worktree.repo_name,
                worktree.branch,
                worktree.path,
                worktree.commit_hash,
                serialize_json_field(worktree.metadata),
            )
            await self.db_manager.execute_update(query, values)

            operation.success = True
            operation.completed_at = datetime.utcnow()
            operation.result = {"worktree_id": worktree.id, "path": str(worktree_path)}

            logger.info(f"Created worktree: {worktree.id} for branch {request.branch}")
            return worktree

        except Exception as e:
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            logger.error(f"Failed to create worktree: {e}")
            raise

        finally:
            await self._save_operation(operation)

    async def delete_worktree(self, worktree_id: str, force: bool = False) -> bool:
        """Delete a Git worktree."""
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            return False

        operation = WorktreeOperation(
            operation="delete", worktree_id=worktree_id, params={"force": force}
        )

        try:
            # Execute git worktree remove command
            cmd = ["git", "worktree", "remove"]
            if force:
                cmd.append("--force")
            cmd.append(worktree.path)

            repo = await self.get_repo(worktree.repo_name)
            self._run_git_command(cmd, cwd=repo.path)

            query = "DELETE FROM worktrees WHERE id = $1"
            await self.db_manager.execute_update(query, (worktree_id,))

            operation.success = True
            operation.completed_at = datetime.utcnow()

            logger.info(f"Deleted worktree: {worktree_id}")
            return True

        except Exception as e:
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            logger.error(f"Failed to delete worktree: {e}")
            return False

        finally:
            await self._save_operation(operation)

    async def lock_worktree(self, worktree_id: str, reason: str = "") -> bool:
        """Lock a Git worktree."""
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            return False

        operation = WorktreeOperation(
            operation="lock", worktree_id=worktree_id, params={"reason": reason}
        )

        try:
            # Execute git worktree lock command
            cmd = ["git", "worktree", "lock"]
            if reason:
                cmd.extend(["--reason", reason])
            cmd.append(worktree.path)

            repo = await self.get_repo(worktree.repo_name)
            self._run_git_command(cmd, cwd=repo.path)

            query = "UPDATE worktrees SET status = $1 WHERE id = $2"
            await self.db_manager.execute_update(
                query, (WorktreeStatus.LOCKED.value, worktree_id)
            )

            operation.success = True
            operation.completed_at = datetime.utcnow()

            logger.info(f"Locked worktree: {worktree_id}")
            return True

        except Exception as e:
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            logger.error(f"Failed to lock worktree: {e}")
            return False

        finally:
            await self._save_operation(operation)

    async def unlock_worktree(self, worktree_id: str) -> bool:
        """Unlock a Git worktree."""
        worktree = await self.get_worktree(worktree_id)
        if not worktree:
            return False

        operation = WorktreeOperation(
            operation="unlock", worktree_id=worktree_id, params={}
        )

        try:
            # Execute git worktree unlock command
            cmd = ["git", "worktree", "unlock", worktree.path]

            repo = await self.get_repo(worktree.repo_name)
            self._run_git_command(cmd, cwd=repo.path)

            query = "UPDATE worktrees SET status = $1 WHERE id = $2"
            await self.db_manager.execute_update(
                query, (WorktreeStatus.ACTIVE.value, worktree_id)
            )

            operation.success = True
            operation.completed_at = datetime.utcnow()

            logger.info(f"Unlocked worktree: {worktree_id}")
            return True

        except Exception as e:
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            logger.error(f"Failed to unlock worktree: {e}")
            return False

        finally:
            await self._save_operation(operation)

    async def list_worktrees(self, repo_name: str = None) -> List[Worktree]:
        """List all worktrees, optionally filtered by repository."""
        query = "SELECT * FROM worktrees WHERE 1=1"
        params = []
        param_idx = 1

        if repo_name:
            query += f" AND repo_name = ${param_idx}"
            params.append(repo_name)
            param_idx += 1

        query += " ORDER BY created_at DESC"

        rows = await self.db_manager.execute_query(query, tuple(params))
        return [self._row_to_worktree(row) for row in rows]

    async def get_worktree(self, worktree_id: str) -> Optional[Worktree]:
        """Get a worktree by ID."""
        query = "SELECT * FROM worktrees WHERE id = $1"
        row = await self.db_manager.execute_query(query, (worktree_id,))

        if not row:
            return None

        return self._row_to_worktree(row[0])

    async def get_repo(self, repo_name: str) -> Optional[Repo]:
        """Get a repository by name."""
        query = "SELECT * FROM repos WHERE name = $1"
        row = await self.db_manager.execute_query(query, (repo_name,))

        if not row:
            return None

        return self._row_to_repo(row[0])

    async def get_branch_info(
        self, repo_name: str, branch_name: str = None
    ) -> List[BranchInfo]:
        """Get branch information for a repository."""
        repo = await self.get_repo(repo_name)
        if not repo:
            return []

        try:
            # Get all branches
            cmd = ["git", "branch", "-v", "--all"]
            result = self._run_git_command(cmd, cwd=repo.path)

            branches = []
            self._get_current_branch(repo.path)

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue

                # Parse branch info
                is_current = line.startswith("*")
                line = line.lstrip("* ").strip()

                parts = line.split()
                if len(parts) >= 2:
                    branch_name_parsed = parts[0]
                    commit_hash = parts[1]
                    commit_message = " ".join(parts[2:]) if len(parts) > 2 else ""

                    # Skip remote tracking branches in output
                    if branch_name_parsed.startswith("remotes/"):
                        continue

                    # Get additional branch info
                    branch_info = BranchInfo(
                        name=branch_name_parsed,
                        commit_hash=commit_hash,
                        commit_message=commit_message,
                        author="unknown",  # Would need additional git command
                        commit_date=datetime.utcnow(),  # Would need additional git command
                        is_current=is_current,
                    )

                    # Filter by branch name if specified
                    if not branch_name or branch_name_parsed == branch_name:
                        branches.append(branch_info)

            return branches

        except Exception as e:
            logger.error(f"Failed to get branch info for {repo_name}: {e}")
            return []

    async def sync_worktrees(self, repo_name: str) -> Dict[str, Any]:
        """Synchronize worktree database with actual Git worktrees."""
        repo = await self.get_repo(repo_name)
        if not repo:
            return {"error": "Repository not found"}

        try:
            # Get actual worktrees from Git
            cmd = ["git", "worktree", "list", "--porcelain"]
            result = self._run_git_command(cmd, cwd=repo.path)

            actual_worktrees = self._parse_worktree_list(result.stdout)
            db_worktrees = {w.path: w for w in await self.list_worktrees(repo_name)}

            added = 0
            removed = 0
            updated = 0

            # Add missing worktrees to database
            for actual_path, actual_info in actual_worktrees.items():
                if actual_path not in db_worktrees:
                    # Create new worktree record
                    worktree = Worktree(
                        id=str(uuid.uuid4()),
                        repo_name=repo_name,
                        branch=actual_info.get("branch", "unknown"),
                        path=actual_path,
                        commit_hash=actual_info.get("HEAD", ""),
                        is_bare=actual_info.get("bare", False),
                        is_detached=actual_info.get("detached", False),
                    )

                    query = """
                        INSERT INTO worktrees (
                            id, repo_name, branch, path, commit_hash, is_bare, is_detached
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """
                    values = (
                        worktree.id,
                        worktree.repo_name,
                        worktree.branch,
                        worktree.path,
                        worktree.commit_hash,
                        worktree.is_bare,
                        worktree.is_detached,
                    )
                    await self.db_manager.execute_update(query, values)

                    added += 1

            # Remove worktrees that no longer exist
            for db_path, db_worktree in db_worktrees.items():
                if db_path not in actual_worktrees:
                    query = "DELETE FROM worktrees WHERE id = $1"
                    await self.db_manager.execute_update(query, (db_worktree.id,))
                    removed += 1

            return {
                "added": added,
                "removed": removed,
                "updated": updated,
                "total_actual": len(actual_worktrees),
                "total_db": len(db_worktrees),
            }

        except Exception as e:
            logger.error(f"Failed to sync worktrees for {repo_name}: {e}")
            return {"error": str(e)}

    def _is_git_repo(self, path: Path) -> bool:
        """Check if path is a Git repository."""
        return (path / ".git").exists() or (path / "HEAD").exists()

    def _get_default_branch(self, repo_path: Path) -> str:
        """Get the default branch of a repository."""
        try:
            result = self._run_git_command(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=str(repo_path)
            )
            return result.stdout.strip().split("/")[-1]
        except subprocess.CalledProcessError:
            return "main"

    def _get_remote_url(self, repo_path: Path) -> Optional[str]:
        """Get the remote URL of a repository."""
        try:
            result = self._run_git_command(
                ["git", "remote", "get-url", "origin"], cwd=str(repo_path)
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _get_current_branch(self, repo_path: str) -> str:
        """Get the current branch of a repository."""
        try:
            result = self._run_git_command(
                ["git", "branch", "--show-current"], cwd=repo_path
            )
            return result.stdout.strip()
        except subprocess.CalledAssociatedError:
            return "unknown"

    def _get_commit_hash(self, path: Path) -> str:
        """Get the current commit hash of a worktree."""
        try:
            result = self._run_git_command(["git", "rev-parse", "HEAD"], cwd=str(path))
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _run_git_command(self, cmd: List[str], cwd: str) -> subprocess.CompletedProcess:
        """Run a Git command and return the result."""
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            logger.debug(f"Git command succeeded: {' '.join(cmd)}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}, error: {e.stderr}")
            raise Exception(f"Git command failed: {e.stderr}")

    def _parse_worktree_list(self, output: str) -> Dict[str, Dict[str, Any]]:
        """Parse git worktree list --porcelain output."""
        worktrees = {}
        current_worktree = {}
        current_path = None

        for line in output.strip().split("\n"):
            if not line:
                if current_path and current_worktree:
                    worktrees[current_path] = current_worktree
                    current_worktree = {}
                    current_path = None
                continue

            if line.startswith("worktree "):
                current_path = line[9:]
            elif line.startswith("HEAD "):
                current_worktree["HEAD"] = line[5:]
            elif line.startswith("branch "):
                current_worktree["branch"] = line[7:]
            elif line == "bare":
                current_worktree["bare"] = True
            elif line == "detached":
                current_worktree["detached"] = True

        # Add the last worktree
        if current_path and current_worktree:
            worktrees[current_path] = current_worktree

        return worktrees

    async def _save_operation(self, operation: WorktreeOperation):
        """Save a worktree operation to the database."""
        query = """
            INSERT INTO worktree_operations (
                operation, worktree_id, params, started_at, completed_at,
                success, error_message, result
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        values = (
            operation.operation,
            operation.worktree_id,
            serialize_json_field(operation.params),
            serialize_datetime(operation.started_at),
            serialize_datetime(operation.completed_at),
            operation.success,
            operation.error_message,
            serialize_json_field(operation.result),
        )
        await self.db_manager.execute_update(query, values)

    def _row_to_repo(self, row) -> Repo:
        """Convert database row to Repo object."""
        return Repo(
            name=row["name"],
            path=row["path"],
            remote_url=row["remote_url"],
            default_branch=row["default_branch"],
            created_at=deserialize_datetime(row["created_at"]),
            metadata=deserialize_json_field(row["metadata"]),
        )

    def _row_to_worktree(self, row) -> Worktree:
        """Convert database row to Worktree object."""
        return Worktree(
            id=row["id"],
            repo_name=row["repo_name"],
            branch=row["branch"],
            path=row["path"],
            status=WorktreeStatus(row["status"]),
            is_bare=bool(row["is_bare"]),
            is_detached=bool(row["is_detached"]),
            created_at=deserialize_datetime(row["created_at"]),
            last_used=deserialize_datetime(row["last_used"]),
            commit_hash=row["commit_hash"],
            upstream_branch=row["upstream_branch"],
            metadata=deserialize_json_field(row["metadata"]),
        )


# Singleton instance
_worktree_manager: Optional[WorktreeManager] = None


async def get_worktree_manager() -> WorktreeManager:
    """Get singleton WorktreeManager instance."""
    global _worktree_manager
    if _worktree_manager is None:
        _worktree_manager = WorktreeManager()
        await _worktree_manager.initialize_database()
    return _worktree_manager


# Legacy function for backward compatibility
def create(path: str) -> str:
    """Create a directory representing a worktree."""
    worktree = Path(path)
    worktree.mkdir(parents=True, exist_ok=True)
    return str(worktree.resolve())

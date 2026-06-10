import datetime
import re
import os
import pathlib
import subprocess
import sys
from typing import List

from dotenv import load_dotenv
from github import Github
from github.GithubException import UnknownObjectException
from terraform_generator.generator import generate

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT / "generated"

load_dotenv(ROOT / '.env')

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")


def run_command(command: List[str], cwd: pathlib.Path = ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def generate_infra_files(env_types=None, env_names=None, identifier: str | None = None) -> List[pathlib.Path]:
    env_types = env_types or ["docker", "aws"]
    env_names = env_names or ["dev", "qa", "prod"]
    GENERATED_DIR.mkdir(exist_ok=True)

    files = []
    for env_type in env_types:
        for env_name in env_names:
            content = generate(env_type, env_name)
            suffix = "yml" if env_type == "docker" else "tf"
            if identifier:
                filename = f"{env_type}-{env_name}-{identifier}.{suffix}"
            else:
                filename = f"{env_type}-{env_name}.{suffix}"
            path = GENERATED_DIR / filename
            path.write_text(content, encoding="utf-8")
            files.append(path)
    return files


def git_branch_name() -> str:
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"auto/generated-infra-{timestamp}"


def create_git_branch(branch_name: str) -> None:
    try:
        run_command(["git", "checkout", "-b", branch_name])
    except RuntimeError:
        run_command(["git", "checkout", branch_name])


def get_push_remote_url() -> str:
    github_token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY") or os.getenv("GITHUB_REPO")
    if not github_token or not repository:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPOSITORY (or GITHUB_REPO) must be set to push to the target repo.")
    return f"https://x-access-token:{github_token}@github.com/{repository}.git"


def commit_generated_files(files: List[pathlib.Path], branch_name: str) -> bool:
    paths = [str(path) for path in files]
    run_command(["git", "add", "-f"] + paths)

    status = run_command(["git", "status", "--porcelain"] + paths)
    if not status.strip():
        print("No generated changes to commit.")
        return False

    run_command(["git", "commit", "-m", "chore: add generated infra templates"])
    push_url = get_push_remote_url()
    run_command(["git", "push", "-u", push_url, branch_name])
    return True


def create_pull_request(branch_name: str, title: str, body: str, base_branch: str) -> None:
    github_token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY") or os.getenv("GITHUB_REPO")
    if not github_token or not repository:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPOSITORY (or GITHUB_REPO) must be set to create a PR.")

    gh = Github(github_token.strip())
    repo = gh.get_repo(repository)
    existing = list(repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch_name}"))
    if existing:
        print(f"Pull request already exists: {existing[0].html_url}")
        return

    if not base_branch:
        base_branch = repo.default_branch
        print(f"No BASE_BRANCH configured; using repository default branch '{base_branch}'.")
    else:
        try:
            repo.get_branch(base_branch)
        except UnknownObjectException:
            fallback = repo.default_branch
            print(f"Configured base branch '{base_branch}' not found; falling back to repository default branch '{fallback}'.")
            base_branch = fallback

    # If the PR body references an issue (e.g. "#123"), append it to the title
    m = re.search(r"#(\d+)", body or "")
    if m:
        title = f"{title} (#{m.group(1)})"

    pr = repo.create_pull(title=title, body=body, head=branch_name, base=base_branch)
    print(f"Created pull request: {pr.html_url}")


def create_github_pr(request_id: int, env_type: str, env_name: str, file_path: str) -> dict:
    """Commits files to a new branch and creates a pull request on GitHub."""
    filename = os.path.basename(file_path)
    
    with open(file_path, "r") as f:
        file_content = f.read()

    branch_name = f"feature/infra-req-{request_id}"
    pr_title = f"infra: auto-provision {env_type} in {env_name} (Req #{request_id})"
    pr_body = f"Automated infrastructure provisioning request #{request_id} for environment {env_name} ({env_type})."
    
    if not GITHUB_TOKEN or not GITHUB_REPO or GITHUB_TOKEN.strip().startswith("your_") or GITHUB_REPO.strip() == "owner/repo-name":
        # Fallback Mode
        import random
        mock_pr_id = random.randint(100, 999)
        mock_url = f"https://github.com/mock-owner/mock-repo/pull/{mock_pr_id}"
        print(f"[GITHUB FALLBACK] GITHUB_TOKEN or GITHUB_REPO not set. Simulating PR creation.")
        return {
            "status": "success",
            "branch": branch_name,
            "url": mock_url,
            "is_mock": True
        }

    try:
        g = Github(GITHUB_TOKEN.strip())
        repo = g.get_repo(GITHUB_REPO.strip())
        
        main_branch = repo.default_branch
        ref = repo.get_git_ref(f"heads/{main_branch}")
        sha = ref.object.sha
        
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)
        except Exception as e:
            # If branch already exists, log it and proceed
            print(f"Note on branch ref creation: {e}")
            
        file_repo_path = f"infra/{env_name}/{filename}"
        
        file_sha = None
        try:
            content_file = repo.get_contents(file_repo_path, ref=branch_name)
            file_sha = content_file.sha
        except Exception:
            pass
            
        if file_sha:
            repo.update_file(
                path=file_repo_path,
                message=f"Update generated infra for request #{request_id}",
                content=file_content,
                sha=file_sha,
                branch=branch_name
            )
        else:
            repo.create_file(
                path=file_repo_path,
                message=f"Add generated infra for request #{request_id}",
                content=file_content,
                branch=branch_name
            )

        # Verify branch head changed from the base commit. If it didn't, avoid creating a PR
        try:
            branch_ref = repo.get_git_ref(f"heads/{branch_name}")
            head_sha = branch_ref.object.sha
            if head_sha == sha:
                print(f"No changes committed on branch {branch_name}; skipping PR creation.")
                return {
                    "status": "no_changes",
                    "branch": branch_name,
                    "url": None,
                    "is_mock": False
                }
        except Exception as e:
            # If we can't read the branch ref for some reason, log and proceed to attempt PR creation.
            print(f"Warning checking branch ref: {e}")

        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=main_branch
        )
        
        return {
            "status": "success",
            "branch": branch_name,
            "url": pr.html_url,
            "is_mock": False
        }
    except Exception as e:
        print(f"GitHub PR Error: {e}. Falling back to mock PR.")
        import random
        mock_pr_id = random.randint(100, 999)
        return {
            "status": "error",
            "branch": branch_name,
            "url": f"https://github.com/mock-owner/mock-repo/pull/{mock_pr_id}",
            "is_mock": True,
            "error_msg": str(e)
        }


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python create_pr.py <request_id> <env_type> <env_name> <file_path>")
        sys.exit(1)
    res = create_github_pr(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
    print(f"Result: {res}")

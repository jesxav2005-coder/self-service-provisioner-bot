import datetime
import os
import pathlib
import subprocess
from typing import List

from github import Github
from terraform_generator.generator import generate

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT / "generated"


def run_command(command: List[str], cwd: pathlib.Path = ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def generate_infra_files(env_types=None, env_names=None) -> List[pathlib.Path]:
    env_types = env_types or ["docker", "aws"]
    env_names = env_names or ["dev", "qa", "prod"]
    GENERATED_DIR.mkdir(exist_ok=True)

    files = []
    for env_type in env_types:
        for env_name in env_names:
            content = generate(env_type, env_name)
            suffix = "yml" if env_type == "docker" else "tf"
            filename = f"{env_type}-{env_name}.{suffix}"
            path = GENERATED_DIR / filename
            path.write_text(content, encoding="utf-8")
            files.append(path)
    return files


def git_branch_name() -> str:
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"auto/generated-infra-{timestamp}"


def create_git_branch(branch_name: str) -> None:
    run_command(["git", "checkout", "-b", branch_name])


def commit_generated_files(files: List[pathlib.Path], branch_name: str) -> None:
    run_command(["git", "add"] + [str(path) for path in files])
    run_command(["git", "commit", "-m", "chore: add generated infra templates"])
    run_command(["git", "push", "-u", "origin", branch_name])


def create_pull_request(branch_name: str, title: str, body: str, base_branch: str) -> None:
    github_token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY")
    if not github_token or not repository:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPOSITORY must be set to create a PR.")

    gh = Github(github_token)
    repo = gh.get_repo(repository)
    existing = list(repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch_name}"))
    if existing:
        print(f"Pull request already exists: {existing[0].html_url}")
        return

    pr = repo.create_pull(title=title, body=body, head=branch_name, base=base_branch)
    print(f"Created pull request: {pr.html_url}")


def run():
    base_branch = os.getenv("BASE_BRANCH", "main")
    branch_name = os.getenv("BRANCH_NAME", git_branch_name())
    pr_title = os.getenv("PR_TITLE", "Generated infra templates")
    pr_body = os.getenv(
        "PR_BODY",
        "This PR contains generated infrastructure templates created by automation.",
    )

    print("Generating infrastructure files...")
    generated_files = generate_infra_files()
    print(f"Wrote {len(generated_files)} generated files.")

    print(f"Creating git branch {branch_name}...")
    create_git_branch(branch_name)

    print("Committing generated files...")
    commit_generated_files(generated_files, branch_name)

    print("Creating pull request...")
    create_pull_request(branch_name, pr_title, pr_body, base_branch)


if __name__ == "__main__":
    run()

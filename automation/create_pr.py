import os
import sys
from github import Github
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

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

#!/usr/bin/env python3
"""
Kaggle to GitHub Notebook Sync
Automatically syncs all Kaggle notebooks to separate GitHub repositories.
"""

import os
import sys
import json
import re
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import unicodedata

from github import Github, GithubException
import requests


def normalize_turkish_chars(text: str) -> str:
    """Convert Turkish characters to ASCII equivalents."""
    replacements = {
        'ı': 'i', 'İ': 'I',
        'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U',
        'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O',
        'ç': 'c', 'Ç': 'C',
    }
    
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    
    return text


def title_to_slug(title: str) -> str:
    """
    Convert notebook title to GitHub repository slug.
    
    Examples:
        "My Cool Analysis" -> "my-cool-analysis"
        "Veri Analizi çalışması" -> "veri-analizi-calismasi"
    """
    # First normalize Turkish characters
    slug = normalize_turkish_chars(title)
    
    # Convert to ASCII, removing accents
    slug = unicodedata.normalize('NFKD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    slug = slug.lower()
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure the slug is not empty
    if not slug:
        slug = 'notebook'
    
    return slug


def get_kaggle_credentials() -> tuple:
    """Get Kaggle credentials from environment or config file."""
    username = os.environ.get('KAGGLE_USERNAME')
    key = os.environ.get('KAGGLE_KEY')
    
    if not username or not key:
        # Try to read from kaggle.json
        kaggle_json_path = Path.home() / '.kaggle' / 'kaggle.json'
        if kaggle_json_path.exists():
            with open(kaggle_json_path, 'r') as f:
                credentials = json.load(f)
                username = credentials.get('username')
                key = credentials.get('key')
    
    if not username or not key:
        raise ValueError(
            "Kaggle credentials not found. Please set KAGGLE_USERNAME and KAGGLE_KEY "
            "environment variables or create ~/.kaggle/kaggle.json"
        )
    
    return username, key


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError(
            "GitHub token not found. Please set GITHUB_TOKEN environment variable."
        )
    return token


def list_kaggle_notebooks(username: str) -> List[Dict]:
    """List all notebooks for a Kaggle user."""
    print(f"📋 Listing notebooks for user: {username}")
    
    try:
        # Run kaggle kernels list command
        cmd = ['kaggle', 'kernels', 'list', '--mine', '--page-size', '100', '--csv']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse CSV output
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            print("⚠️  No notebooks found")
            return []
        
        # Parse header
        headers = lines[0].split(',')
        
        # Parse notebooks
        notebooks = []
        for line in lines[1:]:
            values = line.split(',')
            notebook = dict(zip(headers, values))
            notebooks.append(notebook)
        
        print(f"✅ Found {len(notebooks)} notebook(s)")
        return notebooks
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing notebooks: {e.stderr}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def download_notebook(kernel_ref: str, output_dir: Path) -> Optional[Path]:
    """
    Download a Kaggle notebook with outputs.
    
    Args:
        kernel_ref: Kernel reference (e.g., "username/notebook-name")
        output_dir: Directory to download notebook to
        
    Returns:
        Path to downloaded .ipynb file or None if failed
    """
    print(f"  📥 Downloading notebook: {kernel_ref}")
    
    try:
        # Pull the kernel (downloads .ipynb with outputs)
        cmd = ['kaggle', 'kernels', 'pull', kernel_ref, '-p', str(output_dir), '-m']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print(f"  ✅ Downloaded notebook")
        
        # Find the .ipynb file
        ipynb_files = list(output_dir.glob('*.ipynb'))
        if ipynb_files:
            return ipynb_files[0]
        else:
            print(f"  ⚠️  No .ipynb file found in output")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error downloading notebook: {e.stderr}")
        return None


def create_or_update_github_repo(gh: Github, repo_name: str, description: str) -> object:
    """
    Create a new GitHub repository or get existing one.
    
    Args:
        gh: Github instance
        repo_name: Name of the repository
        description: Repository description
        
    Returns:
        Repository object
    """
    user = gh.get_user()
    
    try:
        # Try to get existing repo
        repo = user.get_repo(repo_name)
        print(f"  ℹ️  Repository '{repo_name}' already exists, will update")
        return repo
    except GithubException as e:
        if e.status == 404:
            # Repo doesn't exist, create it
            print(f"  🆕 Creating repository '{repo_name}'")
            try:
                repo = user.create_repo(
                    name=repo_name,
                    description=description or f"Kaggle notebook: {repo_name}",
                    auto_init=False,
                    private=False
                )
                print(f"  ✅ Repository created")
                return repo
            except GithubException as create_error:
                print(f"  ❌ Error creating repository: {create_error}")
                raise
        else:
            print(f"  ❌ Error accessing repository: {e}")
            raise


def generate_readme(title: str, description: str, notebook_url: str) -> str:
    """Generate README.md content for the notebook repository."""
    readme = f"# {title}\n\n"
    
    if description:
        readme += f"{description}\n\n"
    
    readme += f"## Kaynak / Source\n\n"
    readme += f"Bu notebook Kaggle'dan otomatik olarak senkronize edilmiştir.\n\n"
    readme += f"This notebook was automatically synced from Kaggle.\n\n"
    readme += f"**Kaggle URL:** {notebook_url}\n\n"
    readme += f"## Notebook\n\n"
    readme += f"Notebook dosyasını bu repository'de bulabilirsiniz.\n\n"
    readme += f"You can find the notebook file in this repository.\n"
    
    return readme


def push_to_github(repo: object, ipynb_path: Path, readme_content: str):
    """
    Push notebook and README to GitHub repository.
    
    Args:
        repo: Github repository object
        ipynb_path: Path to the .ipynb file
        readme_content: Content for README.md
    """
    print(f"  📤 Pushing files to GitHub")
    
    # Read notebook content
    with open(ipynb_path, 'r', encoding='utf-8') as f:
        notebook_content = f.read()
    
    notebook_filename = ipynb_path.name
    
    try:
        # Push/update the notebook file
        try:
            # Try to get existing file
            file = repo.get_contents(notebook_filename)
            repo.update_file(
                path=notebook_filename,
                message=f"Update {notebook_filename}",
                content=notebook_content,
                sha=file.sha
            )
            print(f"  ✅ Updated {notebook_filename}")
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create it
                repo.create_file(
                    path=notebook_filename,
                    message=f"Add {notebook_filename}",
                    content=notebook_content
                )
                print(f"  ✅ Created {notebook_filename}")
            else:
                raise
        
        # Push/update README.md
        try:
            file = repo.get_contents("README.md")
            repo.update_file(
                path="README.md",
                message="Update README.md",
                content=readme_content,
                sha=file.sha
            )
            print(f"  ✅ Updated README.md")
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path="README.md",
                    message="Add README.md",
                    content=readme_content
                )
                print(f"  ✅ Created README.md")
            else:
                raise
                
    except Exception as e:
        print(f"  ❌ Error pushing to GitHub: {e}")
        raise


def sync_notebook(gh: Github, notebook: Dict, kaggle_username: str):
    """
    Sync a single notebook to GitHub.
    
    Args:
        gh: Github instance
        notebook: Notebook metadata dict
        kaggle_username: Kaggle username
    """
    # Extract notebook info
    ref = notebook.get('ref', '')
    title = notebook.get('title', 'Untitled')
    
    print(f"\n{'='*60}")
    print(f"📓 Processing: {title}")
    print(f"{'='*60}")
    
    # Generate repo slug from title
    repo_slug = title_to_slug(title)
    print(f"  🏷️  Repository slug: {repo_slug}")
    
    # Create temp directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Download notebook
        ipynb_path = download_notebook(ref, temp_path)
        if not ipynb_path:
            print(f"  ⚠️  Skipping notebook due to download failure")
            return
        
        # Create or get GitHub repo
        try:
            description = f"Kaggle notebook: {title}"
            repo = create_or_update_github_repo(gh, repo_slug, description)
        except Exception as e:
            print(f"  ⚠️  Skipping notebook due to repo error: {e}")
            return
        
        # Generate README
        notebook_url = f"https://www.kaggle.com/code/{ref}"
        readme_content = generate_readme(title, description, notebook_url)
        
        # Push to GitHub
        try:
            push_to_github(repo, ipynb_path, readme_content)
            print(f"  🎉 Successfully synced to https://github.com/{repo.full_name}")
        except Exception as e:
            print(f"  ⚠️  Failed to push to GitHub: {e}")


def main():
    """Main entry point."""
    print("🚀 Kaggle to GitHub Sync Tool")
    print("="*60)
    
    try:
        # Get credentials
        print("\n🔑 Checking credentials...")
        kaggle_username, kaggle_key = get_kaggle_credentials()
        github_token = get_github_token()
        print(f"✅ Kaggle user: {kaggle_username}")
        print(f"✅ GitHub token configured")
        
        # Initialize GitHub client
        gh = Github(github_token)
        gh_user = gh.get_user()
        print(f"✅ GitHub user: {gh_user.login}")
        
        # List notebooks
        notebooks = list_kaggle_notebooks(kaggle_username)
        
        if not notebooks:
            print("\n⚠️  No notebooks to sync")
            return
        
        # Sync each notebook
        print(f"\n📦 Starting sync of {len(notebooks)} notebook(s)...")
        
        success_count = 0
        for i, notebook in enumerate(notebooks, 1):
            print(f"\n[{i}/{len(notebooks)}]")
            try:
                sync_notebook(gh, notebook, kaggle_username)
                success_count += 1
            except Exception as e:
                print(f"  ❌ Error syncing notebook: {e}")
                continue
        
        # Summary
        print("\n" + "="*60)
        print(f"✅ Sync complete!")
        print(f"   Successfully synced: {success_count}/{len(notebooks)}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

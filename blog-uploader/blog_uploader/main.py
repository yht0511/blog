import os
import sys
import shutil
import click
import git
import time
import frontmatter
import platform
import subprocess
from rich.console import Console
from rich.table import Table

# --- Helper Functions ---

def check_hugo_installed():
    """Checks if Hugo is installed and in the system's PATH."""
    if shutil.which("hugo") is None:
        click.echo(
            click.style("Error: Hugo is not installed or not in your system's PATH.", fg="red")
        )
        click.echo("Please install Hugo to use this tool.")
        click.echo("Installation instructions can be found at: https://gohugo.io/getting-started/installing/")
        sys.exit(1)

def open_with_typora(filepath):
    """Tries to open the given file with Typora across different OS."""
    editor_path = None
    system = platform.system()

    if system == "Windows":
        possible_paths = [
            r"C:\Program Files\Typora\Typora.exe",
            r"D:\Program Files\Typora\Typora.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Typora\Typora.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                editor_path = path
                break
    elif system == "Darwin": # macOS
        # On macOS, 'open -a Typora' is the standard way.
        try:
            subprocess.run(["open", "-a", "Typora", filepath], check=True)
            click.echo("Opened file with Typora.")
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            click.echo("Could not open with Typora automatically.", err=True)
            
    if editor_path:
        try:
            subprocess.Popen([editor_path, filepath])
            click.echo(f"Opened file with Typora at {editor_path}.")
            return
        except Exception as e:
            click.echo(f"Failed to open with Typora: {e}", err=True)
    
    click.echo(
        click.style("Could not find Typora automatically.", fg="yellow")
    )


# --- Configuration ---
# In a real application, this would be loaded from a config file.
# For now, we'll keep them as constants.
REPO_URL = "https://github.com/yht0511/blog.git"
REPO_NAME = "blog"
TEMP_DIR_NAME = "temp_blog"
CONTENT_PATH = "content/post"

# --- Helper Functions ---

def get_temp_dir():
    """Gets the temporary directory path and ensures it exists."""
    # Use the user's home directory for temporary files to avoid permission issues
    # and keep the project directory clean.
    home_dir = os.path.expanduser("~")
    temp_dir = os.path.join(home_dir, ".blog_uploader", TEMP_DIR_NAME)
    
    if not os.path.exists(temp_dir):
        click.echo(f"Cloning repository from {REPO_URL}...")
        git.Repo.clone_from(REPO_URL, temp_dir)
        click.echo(f"Repository cloned to {temp_dir}")
    else:
        click.echo("Pulling latest changes...")
        repo = git.Repo(temp_dir)
        repo.remotes.origin.pull()
        click.echo("Repository is up to date.")
        
    return temp_dir

def commit_and_push(repo_path, message):
    """Adds all changes, commits, and pushes them."""
    try:
        repo = git.Repo(repo_path)
        repo.git.add(A=True)
        repo.index.commit(message)
        repo.remotes.origin.push()
        click.echo("Changes committed and pushed successfully.")
    except Exception as e:
        click.echo(f"Error during git operation: {e}", err=True)
        sys.exit(1)

# --- CLI Commands ---

@click.group()
def cli():
    """A CLI tool to manage your Hugo blog posts."""
    check_hugo_installed()
    pass

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
def new(filepath):
    """Create a new blog post from a file."""
    temp_dir = get_temp_dir()
    
    # 1. Create a new post using Hugo
    click.echo("Creating new post with Hugo...")
    post_dir_name = "untitled-post"
    new_post_path = os.path.join(temp_dir, CONTENT_PATH, post_dir_name)
    
    # Hugo command needs to be run from within the repo directory
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    os.system(f'hugo new {CONTENT_PATH}/{post_dir_name}/index.md')
    os.chdir(original_cwd)

    # 2. Append content from the source file
    with open(filepath, "r", encoding='utf-8') as f_src:
        content = f_src.read()
    
    index_md_path = os.path.join(new_post_path, "index.md")
    with open(index_md_path, "a", encoding='utf-8') as f_dest:
        f_dest.write("\n" + content)
        
    click.echo(f"Content from {filepath} has been added.")
    
    # 3. Open with Typora
    open_with_typora(index_md_path)
    click.echo(f"Please edit the post file to set the title: {index_md_path}")
    
    # 4. Prompt user to confirm after editing
    if not click.confirm("Have you finished editing and set the title?"):
        click.echo("Aborted.")
        # Clean up the created directory
        shutil.rmtree(new_post_path)
        return

    # 5. Read the title and rename the directory
    title = ""
    with open(index_md_path, "r", encoding='utf-8') as f:
        for line in f:
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                break
    
    if not title:
        click.echo("Could not find title in the markdown file. Aborting.", err=True)
        shutil.rmtree(new_post_path)
        return

    # Sanitize title to be a valid directory name
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    final_post_path = os.path.join(temp_dir, CONTENT_PATH, safe_title)

    if os.path.exists(final_post_path):
        if not click.confirm(f"Post '{safe_title}' already exists. Overwrite?"):
            click.echo("Aborted.")
            shutil.rmtree(new_post_path)
            return
        shutil.rmtree(final_post_path)

    os.rename(new_post_path, final_post_path)
    click.echo(f"Post renamed to '{safe_title}'.")

    # 6. Run hugo, commit and push
    click.echo("Running hugo build...")
    os.chdir(temp_dir)
    os.system('hugo')
    os.chdir(original_cwd)
    
    commit_and_push(temp_dir, f"Add new post: {title}")

@cli.command()
@click.argument('name')
def remove(name):
    """Remove a blog post by its folder name."""
    temp_dir = get_temp_dir()
    post_path = os.path.join(temp_dir, CONTENT_PATH, name)

    if not os.path.exists(post_path):
        click.echo(f"Error: Post '{name}' not found.", err=True)
        return

    if click.confirm(f"Are you sure you want to delete the post '{name}'?"):
        shutil.rmtree(post_path)
        click.echo(f"Post '{name}' has been deleted.")
        
        # Run hugo, commit and push
        click.echo("Running hugo build...")
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        os.system('hugo')
        os.chdir(original_cwd)
        
        commit_and_push(temp_dir, f"Remove post: {name}")
    else:
        click.echo("Aborted.")

@cli.command()
def list():
    """List all available blog posts in a table."""
    temp_dir = get_temp_dir()
    posts_dir = os.path.join(temp_dir, CONTENT_PATH)
    
    if not os.path.exists(posts_dir):
        click.echo("Posts directory not found.", err=True)
        return
        
    posts = [d for d in os.listdir(posts_dir) if os.path.isdir(os.path.join(posts_dir, d))]
    
    if not posts:
        click.echo("No posts found.")
        return

    table = Table(title="Blog Posts")
    table.add_column("Title", style="cyan", no_wrap=True)
    table.add_column("Date", style="magenta")
    table.add_column("Tags", style="green")
    table.add_column("Word Count", justify="right", style="yellow")

    for post_name in sorted(posts):
        index_path = os.path.join(posts_dir, post_name, "index.md")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    
                title = post.metadata.get('title', 'N/A')
                date = post.metadata.get('date', 'N/A')
                if hasattr(date, 'strftime'):
                    date = date.strftime('%Y-%m-%d')
                
                tags = post.metadata.get('categories', [])
                tags_str = ", ".join(tags) if tags else "N/A"
                
                word_count = len(post.content)
                
                table.add_row(title, str(date), tags_str, str(word_count))
            except Exception as e:
                table.add_row(f"[red]Error parsing {post_name}[/red]", str(e), "", "")

    console = Console()
    console.print(table)

if __name__ == '__main__':
    cli()

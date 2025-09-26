import os
import sys
import shutil
import click
import git
import time
import datetime
import frontmatter
import platform
import subprocess
import re
import requests
import hashlib
import json
import base64
import builtins
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
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
            r"D:\Software\Typora\Typora.exe",
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

def get_config_path():
    """Returns the path to the config file."""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".blog_uploader", "config.json")

def load_config():
    """Loads the config file."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Saves the config file."""
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def get_or_setup_public_key():
    """
    Gets the public key from config, or guides the user through setting one up.
    """
    config = load_config()
    public_key_path = config.get("public_key_path")

    if public_key_path and os.path.exists(public_key_path):
        with open(public_key_path, 'r') as f:
            return RSA.import_key(f.read())

    click.echo("RSA public key not found or configured.")
    if click.confirm("Do you have an existing RSA public key file to use?"):
        public_key_path = click.prompt("Please enter the path to your RSA public key", type=click.Path(exists=True, dir_okay=False))
        config["public_key_path"] = public_key_path
        save_config(config)
        with open(public_key_path, 'r') as f:
            return RSA.import_key(f.read())
    elif click.confirm("Would you like to generate a new RSA key pair now?"):
        key = RSA.generate(2048)
        private_key = key.export_key(pkcs=1) # Export in PKCS#1 format for JSEncrypt compatibility
        public_key = key.publickey().export_key()
        
        key_dir = os.path.join(os.path.expanduser("~"), ".blog_uploader")
        private_key_path = os.path.join(key_dir, "private.pem")
        public_key_path = os.path.join(key_dir, "public.pem")
        
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)
            
        click.echo(click.style(f"IMPORTANT: Your new keys have been saved:", fg="yellow"))
        click.echo(f"  - Private Key: {private_key_path}")
        click.echo(f"  - Public Key: {public_key_path}")
        click.echo(click.style("--- BEGIN RSA PRIVATE KEY ---", fg="cyan"))
        click.echo(click.style(private_key.decode('utf-8'), fg="cyan"))
        click.echo(click.style("---  END RSA PRIVATE KEY  ---", fg="cyan"))
        click.echo(click.style("\nPlease COPY the private key above and use it on your website for decryption.", fg="red", bold=True))
        
        config["public_key_path"] = public_key_path
        config["private_key_path"] = private_key_path # Also save private key path for later retrieval
        save_config(config)
        return RSA.import_key(public_key)
    else:
        click.echo("Cannot proceed without a public key. Aborting.", err=True)
        sys.exit(1)

# --- Configuration ---
# In a real application, this would be loaded from a config file.
# For now, we'll keep them as constants.
REPO_URL = "https://github.com/yht0511/blog.git"
SECRET_REPO_URL = "https://github.com/yht0511/blog-secret.git"
REPO_NAME = "blog"
SECRET_REPO_NAME = "blog-secret"
TEMP_DIR_NAME = "temp_blog"
SECRET_TEMP_DIR_NAME = "temp_blog_secret"
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

def get_secret_repo_dir():
    """Gets the temporary directory path for the secret repo and ensures it exists."""
    home_dir = os.path.expanduser("~")
    temp_dir = os.path.join(home_dir, ".blog_uploader", SECRET_TEMP_DIR_NAME)
    
    if not os.path.exists(temp_dir):
        click.echo(f"Cloning secret repository from {SECRET_REPO_URL}...")
        git.Repo.clone_from(SECRET_REPO_URL, temp_dir)
        click.echo(f"Secret repository cloned to {temp_dir}")
    else:
        click.echo("Pulling latest changes from secret repository...")
        repo = git.Repo(temp_dir)
        repo.remotes.origin.pull()
        click.echo("Secret repository is up to date.")
        
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

def upload_images_with_picgo(image_paths):
    """Uploads images using the PicGo server API."""
    url = "http://127.0.0.1:36677/upload"
    try:
        # PicGo's API expects a JSON payload with a 'list' of file paths
        response = requests.post(url, json={"list": image_paths})
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            return result.get("result", [])
        else:
            click.echo(f"PicGo API Error: {result.get('message', 'Unknown error')}", err=True)
            return []
    except requests.exceptions.RequestException as e:
        click.echo(f"Failed to connect to PicGo server at {url}. Is it running?", err=True)
        click.echo(f"Error: {e}", err=True)
        return []

def preprocess_markdown_content(content, base_dir):
    """Finds local images, uploads them via PicGo, and replaces links."""
    # Regex to find markdown image links ![]() that are not web URLs
    image_pattern = re.compile(r'!\[(.*?)\]\((?!https?://)(.*?)\)')
    
    original_paths = []
    absolute_paths = []
    
    for match in image_pattern.finditer(content):
        image_path = match.group(2)
        original_paths.append(image_path)
        
        abs_path = image_path
        if not os.path.isabs(abs_path):
            abs_path = os.path.abspath(os.path.join(base_dir, image_path))
        
        if os.path.exists(abs_path):
            absolute_paths.append(abs_path)
        else:
            click.echo(click.style(f"Warning: Image not found at {abs_path}", fg="yellow"))

    if not absolute_paths:
        return content

    click.echo(f"Found {len(absolute_paths)} local images to upload.")
    uploaded_urls = upload_images_with_picgo(absolute_paths)

    if not uploaded_urls or len(uploaded_urls) != len(absolute_paths):
        click.echo("Image upload failed or returned incomplete results. Aborting.", err=True)
        sys.exit(1)

    # Create a map of original local path -> remote URL
    path_to_url_map = dict(zip(original_paths, uploaded_urls))

    # Replace local paths with remote URLs in the content
    def replace_path(match):
        original_path = match.group(2)
        alt_text = match.group(1)
        
        remote_url = path_to_url_map.get(original_path)
        if remote_url:
            return f'![{alt_text}]({remote_url})'
        else:
            # Return original if something went wrong (e.g., file not found)
            return match.group(0)

    updated_content = image_pattern.sub(replace_path, content)
    click.echo("Successfully replaced local image paths with remote URLs.")
    return updated_content

def process_strikethrough_content(content):
    """
    Finds all strikethrough content, asks the user if they want to separate it,
    and replaces it with a placeholder.
    """
    # This regex finds content wrapped in ~~...~~
    strikethrough_pattern = re.compile(r'~~(.+?)~~', re.DOTALL)
    
    matches = [m for m in strikethrough_pattern.finditer(content)]
    
    if not matches:
        return content, None

    click.echo(f"Found {len(matches)} sections with strikethrough text.")
    if not click.confirm("Do you want to separate this content into the secret repository?", default=True):
        return content, None

    secret_content = {}
    clean_content = content
    
    for match in reversed(matches):
        original_text = match.group(0) # e.g., ~~secret text~~
        inner_text = match.group(1)    # e.g., secret text
        
        # We use a hash of the original text to create a unique ID
        content_hash = hashlib.sha256(original_text.encode('utf-8')).hexdigest()
        
        # Store the original markdown (including the ~~ markers)
        secret_content[content_hash] = original_text
        
        # Replace with a placeholder span
        placeholder = f'<span class="secret-placeholder" data-id="{content_hash}"></span>'
        
        # Replace the content from the end to the beginning to not mess up indices
        start, end = match.span()
        clean_content = clean_content[:start] + placeholder + clean_content[end:]

    click.echo("Separated secret content and replaced with placeholders.")
    return clean_content, secret_content

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
    secret_repo_dir = get_secret_repo_dir() # Ensure secret repo is ready

    # 0. Preprocess the markdown file to upload images
    click.echo("Preprocessing markdown file...")
    with open(filepath, "r", encoding='utf-8') as f_src:
        original_content = f_src.read()
    
    source_dir = os.path.dirname(os.path.abspath(filepath))
    content = preprocess_markdown_content(original_content, source_dir)
    
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

    # 5. Read the title and process secret content
    with open(index_md_path, "r", encoding='utf-8') as f:
        full_content_string = f.read()
    
    post = frontmatter.loads(full_content_string)
    title = post.metadata.get("title", "")
    
    if not title:
        click.echo("Could not find title in the markdown file. Aborting.", err=True)
        shutil.rmtree(new_post_path)
        return

    clean_content, secret_content = process_strikethrough_content(post.content)
    
    if secret_content:
        # --- Hybrid Encryption (RSA + AES-CBC) ---
        public_key = get_or_setup_public_key()
        
        # 1. Generate a one-time AES session key
        session_key = get_random_bytes(16) # 128-bit key
        
        # 2. Encrypt the data with AES-CBC
        cipher_aes = AES.new(session_key, AES.MODE_CBC)
        iv = cipher_aes.iv
        data_to_encrypt = json.dumps(secret_content).encode('utf-8')
        
        # Pad the data to be a multiple of the block size using PKCS7
        padded_data = pad(data_to_encrypt, AES.block_size)
        ciphertext = cipher_aes.encrypt(padded_data)
        
        # 3. Encrypt the AES session key with RSA
        cipher_rsa = PKCS1_v1_5.new(public_key)
        encrypted_session_key = cipher_rsa.encrypt(base64.b64encode(session_key))
        
        # 4. Prepare payload for storage
        payload = {
            'encrypted_session_key': base64.b64encode(encrypted_session_key).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
        
        title_hash = hashlib.sha256(str(title).encode('utf-8')).hexdigest()
        secret_filename = f"{title_hash}.json"
        secret_filepath = os.path.join(secret_repo_dir, secret_filename)
        
        with open(secret_filepath, 'w') as f:
            json.dump(payload, f)
        
        click.echo(f"Secret content encrypted and saved to {secret_filepath}")
        
        # Commit and push the secret content
        commit_and_push(secret_repo_dir, f"Add secret for post: {title}")
        
        # Update the main post file with the clean content, preserving original frontmatter
        parts = full_content_string.split('---', 2)
        if len(parts) >= 3:
            raw_frontmatter = parts[1]
            new_full_content = f"---{raw_frontmatter}---\n{clean_content}"
            with open(index_md_path, 'w', encoding='utf-8') as f:
                f.write(new_full_content)
        else:
            # Fallback to original method if splitting fails
            post.content = clean_content
            with open(index_md_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

    # 6. Read the title and rename the directory
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

    # 7. Run hugo, commit and push
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

@cli.command(name="list")
def list_posts():
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
                    
                title = str(post.metadata.get('title', 'N/A'))
                date_obj = post.metadata.get('date')
                date_str = 'N/A'
                if isinstance(date_obj, (datetime.date, datetime.datetime)):
                    date_str = date_obj.strftime('%Y-%m-%d')
                elif date_obj:
                    date_str = str(date_obj)

                tags = post.metadata.get('categories')
                tags_str = "N/A"
                if isinstance(tags, builtins.list):
                    tags_str = ", ".join(map(str, tags))
                
                word_count = len(post.content)
                
                table.add_row(title, date_str, tags_str, str(word_count))
            except Exception as e:
                table.add_row(f"[red]Error parsing {post_name}[/red]", str(e), "", "")

    console = Console()
    console.print(table)

@cli.command(name="show-private-key")
def show_private_key():
    """Displays the configured private key required for decryption."""
    config = load_config()
    private_key_path = config.get("private_key_path")

    if not private_key_path or not os.path.exists(private_key_path):
        click.echo(click.style("Private key path is not configured or the file is missing.", fg="red"))
        click.echo("Please run the 'new' command and generate a key pair when prompted.")
        sys.exit(1)
    
    with open(private_key_path, 'r') as f:
        private_key = f.read()
    
    click.echo(click.style("Here is the private key required for decryption on your website:", fg="yellow"))
    click.echo(click.style(private_key, fg="cyan"))


if __name__ == '__main__':
    cli()

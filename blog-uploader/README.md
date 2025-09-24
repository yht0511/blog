# Blog Uploader

`blog-uploader` is a command-line tool to help you manage your Hugo blog posts. It allows you to create new posts from local markdown files, remove existing posts, and list all current posts.

## Features

- **Create New Posts**: Quickly create a new Hugo post from a markdown file.
- **Remove Posts**: Safely delete a post by its folder name.
- **List Posts**: View a list of all your current blog posts.
- **Git Integration**: Automatically clones your blog's repository, and commits and pushes changes.
- **Cross-Platform**: Works on Windows, macOS, and Linux.

## Requirements

- **Hugo**: This tool depends on Hugo. Before using `blog-uploader`, please ensure that Hugo is installed and accessible in your system's PATH. The tool will automatically check for Hugo's presence and guide you if it's missing.

## Installation

You can install `blog-uploader` via pip:

```bash
pip install .
```
(After navigating into the `blog-uploader` directory)

Or, once it's published on PyPI:
```bash
pip install blog-uploader
```

## Usage

The tool provides three main commands: `new`, `remove`, and `list`.

### 1. Create a New Post

To create a new post, use the `new` command and provide the path to your markdown file.

```bash
blog-uploader new /path/to/your/post.md
```

The tool will:
1. Clone or pull the latest version of your blog repository.
2. Create a new post in Hugo.
3. Append the content of your file to the new post's `index.md`.
4. Prompt you to edit the file to set the title and other metadata.
5. After you confirm, it will rename the post's folder based on the title.
6. Build the site with Hugo, and commit and push the changes to your repository.

### 2. Remove a Post

To remove a post, use the `remove` command with the post's folder name.

```bash
blog-uploader remove "name-of-the-post-folder"
```

You will be asked for confirmation before the post is deleted.

### 3. List All Posts

To see a list of all your posts, use the `list` command.

```bash
blog-uploader list
```

This will display the folder names of all posts in your `content/post` directory.

## Configuration

Currently, the tool is configured with a hardcoded Git repository URL. In future versions, this will be customizable through a configuration file.

from setuptools import setup, find_packages

setup(
    name='blog-uploader',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'GitPython',
        'click',
        'rich',
        'python-frontmatter',
    ],
    entry_points={
        'console_scripts': [
            'blog-uploader = blog_uploader.main:cli',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A command-line tool to manage Hugo blog posts.",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/blog-uploader",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

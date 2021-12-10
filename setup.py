import re
from pathlib import Path
from setuptools import setup, find_packages

readme = Path('README.md').read_text(encoding='utf-8')
# Replace relative markdown links with absolute https links.
readme = re.sub(r'!\[\]\((.*?)\)', r'https://raw.githubusercontent.com/alters-mit/magnebot/main/\1', readme)

setup(
    name='multimodal_challenge',
    version="0.4.4",
    description='Multi-modal challenge for TDW and the Magnebot API.',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/alters-mit/multimodal_challenge',
    author='Seth Alter',
    author_email="alters@mit.edu",
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    keywords='unity simulation tdw robotics magnebot',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['tdw==1.8.29.2', 'magnebot==1.3.2', 'numpy', 'tqdm', "py_md_doc", "requests", "overrides",
                      "packaging"]
)

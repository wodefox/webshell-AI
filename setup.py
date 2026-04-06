#!/usr/bin/env python3
"""
安装脚本
"""
from setuptools import setup, find_packages

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='webshell-manager',
    version='1.0.0',
    description='命令行WebShell管理工具，适合AI使用',
    author='WebShell Manager',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'webshell-manager=main:main',
            'wsm=main:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

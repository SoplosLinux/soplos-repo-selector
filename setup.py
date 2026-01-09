from setuptools import setup, find_packages

setup(
    name='soplos-repo-selector',
    version='2.0.2',
    description='Graphical manager for APT repositories on Debian-based systems',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Soplos Project',
    author_email='contacto@soploslinux.org',
    url='https://github.com/SoplosLinux/soplos-repo-selector',
    packages=find_packages(exclude=['tests', 'debian']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.8',
    install_requires=[
        'psutil',
        'requests',
    ],
    entry_points={
        'gui_scripts': [
            'soplos-repo-selector = main:main',
        ]
    },
    project_urls={
        'Source': 'https://github.com/SoplosLinux/soplos-repo-selector',
        'Tracker': 'https://github.com/SoplosLinux/soplos-repo-selector/issues',
        'Soplos': 'https://soplos.org'
    }
)

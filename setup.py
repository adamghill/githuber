from setuptools import setup

setup(
    name='githuber',
    version='0.1',
    py_modules=['githuber'],
    install_requires=[
        'click==6.2',
        'functools32==3.2.3.post2',
        'github3.py==1.0.0a2',
        'grin==1.2.1',
        'sarge==0.1.4',
    ],
    entry_points='''
        [console_scripts]
        githuber=githuber:main
    ''',
)

from setuptools import setup

setup(
    name='org2eaf',
    version='0.0.1',
    py_modules=['org2eaf'],
    install_requires=[
        'lxml',
        'click',
    ],
    entry_points='''
        [console_scripts]
        org2eaf=org2eaf:cli
    ''',
)

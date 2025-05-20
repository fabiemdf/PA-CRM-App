from setuptools import setup, find_packages

setup(
    name="pa-crm-app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'PySide6>=6.5.0',
        'SQLAlchemy>=2.0.0',
        'pandas>=2.0.0',
        'openpyxl>=3.1.0',
        'requests>=2.31.0',
        'python-dateutil>=2.8.2',
        'qdarkstyle>=3.1.0'
    ]
) 
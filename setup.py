from setuptools import find_packages, setup

package_name = 'natnet_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data= {package_name: ["py.typed", "gui.html"]},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jerome.guzzi',
    maintainer_email='jerome@idsia.ch',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    extras_require={
        'gui': [
            'websockets',
            'numpy',
            'numpy-quaternion',
        ]
    },
    entry_points={
        'console_scripts': [
            'natnet_cli = natnet_py.natnet_cli:main',
            'natnet_discover = natnet_py.natnet_discover:main',
            'natnet_gui = natnet_py.natnet_gui:main',
        ],
    },
)

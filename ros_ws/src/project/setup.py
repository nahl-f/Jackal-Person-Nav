from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'project'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        # Folders under config directory
        (os.path.join('share', package_name, 'config'), glob('config/**/**/*')),
        (os.path.join('share' , package_name, 'config', 'navigation'), glob('config/navigation/*.yaml')),
        (os.path.join('share' , package_name, 'config', 'maps'), glob('config/maps/*.yaml')),
        (os.path.join('share' , package_name, 'config', 'maps'), glob('config/maps/*.json')),
        (os.path.join('share' , package_name, 'config', 'scenarios'), glob('config/scenarios/*.json')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nahl',
    maintainer_email='nahl.farhann@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'orchestrator = project.orchestrator_current:main',
            'vision_server = project.new_vision_action:main',
            'distance_server = project.distance_server:main',
        ],
    },
)

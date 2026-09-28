from setuptools import setup

package_name = 'laser_usv'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='Nó para leitura e publicação dos sensores via ROS 2.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'sensor_bridge = laser_usv.sensor_bridge:main',
        ],
    },
)

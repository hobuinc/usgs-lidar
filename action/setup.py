# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='usgs_boundary',  # Required
    version='0.0.1',  # Required
    description='Python utility for tiling processing operations based on Entwine/EPT',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/x-rst',  # Optional (see note above)
    url='https://github.com/hobu/usgs-lidar/action',  # Optional
    author='Howard Butler',  # Optional
    author_email='howard@hobu.co',  # Optional
    classifiers=[  \
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
    ],

    packages=find_packages(),  # Required
    python_requires='>=3.8',

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['gdal','boto3', 'Shapely', 'Fiona','pyproj'],  # Optional


    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={  # Optional
        'console_scripts': [
            'usgs-boundary=usgs_boundary.command:main',
            'usgs-stac=usgs_boundary.stac:main',
        ],
    },

)

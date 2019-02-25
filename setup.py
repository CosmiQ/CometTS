from setuptools import setup, find_packages

version = '1.1.2'

readme = ''

# Runtime requirements.
inst_reqs = ["numpy", "pandas", "geopandas", "rasterio", "shapely", "fiona", "affine",
             "rasterstats", "matplotlib", "seaborn", "jupyter",
             "ipython", "ipywidgets", "tqdm", "scipy", "gdal"]

extra_reqs = {
    'test': ['mock', 'pytest', 'pytest-cov', 'codecov']}

setup(name='CometTS',
      version=version,
      description=u"""Time series trend analysis tools for user defined polygons in any time series of overhead imagery""",
      long_description=readme,
      classifiers=[
          'Intended Audience :: Information Technology',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Scientific/Engineering :: GIS'],
      keywords='time series, VIIRS, Landsat, GIS, raster, remote sensing',
      author=u"Jake Shermeyer",
      author_email='jss5102@gmail.com',
      url='https://github.com/CosmiQ/CometTS',
      license='Apache-2.0',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      include_package_data=True,
      install_requires=inst_reqs,
      extras_require=extra_reqs,
      entry_points={
          'console_scripts': ['CometTS=CometTS.CometTS:main', 'CometTS.CSV_It=CometTS.CSV_It:main', 'CometTS.ARIMA=CometTS.ARIMA:main']
      }
      )

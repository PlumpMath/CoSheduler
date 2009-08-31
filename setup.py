from setuptools import setup, find_packages

setup(
          name = "CoScheduler",
          version = "0.1",
          description = "",
          author = "",
          author_email = "amcgregor@topfloor.ca",
          license = "MIT",
          packages = find_packages(exclude=['tests', 'examples']),
          include_package_data = False,
          zip_safe = True,
          install_requires = []
      )

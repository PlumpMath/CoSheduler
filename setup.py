from setuptools import setup, find_packages

setup(
          name = "CoScheduler",
          version = "0.1",
          description = "A coroutine-based task scheduler and simulation framework.",
          author = "Alice Bevan-McGregor",
          author_email = "alice@gothcandy.com",
          url = "http://github.com/GothAlice/CoScheduler",
          download_url = "http://pypi.python.org/pypi/Pygios",
          license = "MIT",
          packages = find_packages(exclude=['tests', 'examples']),
          include_package_data = False,
          zip_safe = True,
          install_requires = []
      )

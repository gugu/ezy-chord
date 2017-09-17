from setuptools import setup

setup(name='ezy-chord',
      description='Custom celery chord implementation using redis',
      version='0.1.0',
      author='Andrii Kostenko',
      author_email='andrii.kostenko@ezyinsights.com',
      packages=['ezy_chord'],
      url='https://github.com/EzyInsights/ezy-chord/',
      keywords=['redis', 'celery', 'python'],
      test_suite='tests',
      classifiers=[
          'Operating System :: POSIX',
          'Environment :: Console',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Topic :: Utilities',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ], )

from setuptools import setup

setup(name='twitsent',
      version='0.0.8',
      description='Twitter Sentiment Analysis package',
      url='https://github.com/mhoikka/twitsent.git',
      author='Mitchell Hoikka',
      author_email='',
      license='MIT',
      packages=['twitsent'],
      install_requires=[
            'requests>=2.27.1',
            'clean-text>=0.6.0',
            'tkcalendar>=1.6.1',
            'matplotlib>=3.5.2',
            'pymannkendall>=1.4.2',
            'nltk>=3.5',
            'unidecode>=1.3.4'
            ],
      zip_safe=False)

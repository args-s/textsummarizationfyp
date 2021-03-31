from setuptools import setup, find_packages

setup(name='textsummarizationfyp',
      version='0.2',
      packages=find_packages(include =['textsummarizationfyp']),
      description='Text Summarization Library',
      url='https://gitlab.com/args-s/TextSummarizationFYP',
      author='Killian Flood',
      author_email='killiansmailbox@gmail.com',
      license='none',
      install_requires=[
          'cacheout',
          'networkx',
          'nltk',
      ],
      zip_safe=False)

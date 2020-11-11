from setuptools import setup

setup(name='textsummarizationfyp',
      version='0.1',
      description='Text Summarization Project',
      url='https://gitlab.com/args-s/TextSummarizationFYP',
      author='Killian Flood',
      author_email='killiansmailbox@gmail.com',
      license='none',
      packages=['textsummarizationfyp'],
      install_requires=[
          'cacheout',
          'networkx',
          'nltk',
          'numpy',
          'matplotlib',   
      ],
      zip_safe=False)

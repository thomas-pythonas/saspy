# docs/conf.py

# Add the following content
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'SASPy'
author = 'Zachary Tomlinson, Antonio D\'Angelo'

extensions = [
    'sphinx.ext.autodoc',
]
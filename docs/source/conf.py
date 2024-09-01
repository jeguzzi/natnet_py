# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'natnet_py'
copyright = '2024, Jerome Guzzi'
author = 'Jerome Guzzi'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
  'sphinx_copybutton',
  'sphinx.ext.autodoc',
  'sphinxarg.ext',
  'sphinx.ext.autosummary']

# autosummary_generate = True
# autosummary_imported_members = True
templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_theme_options = {
  "show_toc_level": 2
}

autodoc_type_aliases = {
    'Vector3': 'Vector3',
    'Quaternion': 'Quaternion',
    'Matrix12x12': 'Matrix12x12',
    'Matrix3x4': 'Matrix3x4',
    # 'Vector3': 'tuple[float, float, float]',
    # 'tuple[float, float, float]': 'Vector3',
}

autodoc_class_signature = "separated"

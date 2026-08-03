from pythonforandroid.recipe import PythonRecipe

class LunarPythonRecipe(PythonRecipe):
    version = '1.4.8'
    url = 'https://files.pythonhosted.org/packages/source/l/lunar-python/lunar-python-{version}.tar.gz'
    depends = ['setuptools']
    call_hostpython_via_targetpython = False

recipe = LunarPythonRecipe()
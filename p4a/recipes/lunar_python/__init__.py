from pythonforandroid.recipe import PythonRecipe

class LunarPythonRecipe(PythonRecipe):
    version = '1.4.8'
    url = 'https://files.pythonhosted.org/packages/59/45/5154c95ae7feaab7ca508e71c3288692c09952dfe33b03b7c2f18a32e2cd/lunar_python-{version}.tar.gz'
    depends = ['setuptools']
    call_hostpython_via_targetpython = False

recipe = LunarPythonRecipe()
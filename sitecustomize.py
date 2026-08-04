"""Site-wide lunar_python registry for P4A Android"""
import os, sys, importlib.util, types as _types

_LUNAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python_engines', 'lunar_python')
if os.path.isdir(_LUNAR_DIR):
    _lunar_modules = [
        'JieQi','NineStar','EightChar','ShuJiu','Fu','Solar','SolarWeek',
        'SolarMonth','SolarSeason','SolarHalfYear','SolarYear','LunarTime',
        'Lunar','LunarYear','LunarMonth','Holiday','Tao','TaoFestival','Foto','FotoFestival'
    ]
    for _mn in _lunar_modules:
        _mp = os.path.join(_LUNAR_DIR, _mn + '.py')
        if os.path.exists(_mp):
            spec = importlib.util.spec_from_file_location(_mn, _mp)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                sys.modules[_mn] = mod
                sys.modules['lunar_python.' + _mn] = mod
    _lp = _types.ModuleType('lunar_python')
    _lp.__path__ = [_LUNAR_DIR]
    for _mn in _lunar_modules:
        if _mn in sys.modules:
            setattr(_lp, _mn, sys.modules[_mn])
    sys.modules['lunar_python'] = _lp
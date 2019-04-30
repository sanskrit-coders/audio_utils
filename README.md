[![Build Status](https://travis-ci.org/sanskrit-coders/audio_utils.svg?branch=master)](https://travis-ci.org/sanskrit-coders/audio_utils)
[![Documentation Status](https://readthedocs.org/projects/audio_utils/badge/?version=latest)](http://audio_utils.readthedocs.io/en/latest/?badge=latest)

## Audio utils

Miscellaneous audio processing tools. 

# For users
* [Autogenerated Docs on readthedocs (might be broken)](http://audio_utils.readthedocs.io/en/latest/).
* Manually and periodically generated docs [here](https://sanskrit-coders.github.io/audio_utils/build/html/)
* For detailed examples and help, please see individual module files in this package.


## Installation or upgrade:
* `sudo pip install audio_utils -U`
* `sudo pip install git+https://github.com/sanskrit-coders/audio_utils/@master -U`
* [Web](https://pypi.python.org/pypi/audio_utils).


# For contributors

## Contact

Have a problem or question? Please head to [github](https://github.com/sanskrit-coders/audio_utils).

## Packaging

* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```

## Build documentation
- sphinx html docs can be generated with `cd docs; make html`

## Testing
Run `pytest` in the root directory.

## Auxiliary tools
- [![Build Status](https://travis-ci.org/sanskrit-coders/audio_utils.svg?branch=master)](https://travis-ci.org/sanskrit-coders/audio_utils)
- [![Documentation Status](https://readthedocs.org/projects/audio_utils/badge/?version=latest)](http://audio_utils.readthedocs.io/en/latest/?badge=latest)
- [pyup](https://pyup.io/account/repos/github/sanskrit-coders/audio_utils/)
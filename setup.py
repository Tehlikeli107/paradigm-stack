from setuptools import setup, find_packages

setup(
    name='task-difficulty',
    version='0.1.0',
    description='Predict classification/regression difficulty without training',
    author='Tehlikeli107',
    url='https://github.com/Tehlikeli107/paradigm-stack',
    py_modules=['difficulty_predictor', 'cai', 'complexity_vector', 'paradigm_stack'],
    install_requires=['numpy', 'torch', 'scikit-learn'],
    python_requires='>=3.8',
)

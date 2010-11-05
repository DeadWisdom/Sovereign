from distutils.core import setup, Extension

setup(name="tradesocket", version="0.0",
	  ext_modules = [Extension("tradesocket", ["tradesocket.c"])])
============
Installation
============

This a pure Python implementation of Natnet without external dependencies.
You can install it in several ways.

Using pip
---------

.. code-block:: bash

   pip install git+https://github.com/jeguzzi/natnet_py.git

Using ``setup.py``
------------------

.. code-block:: console

   # clone this repo
   git clone https://github.com/jeguzzi/natnet_py.git
   python natnet_py/setup.py

Using colcon
------------

.. code-block:: console

   # cd to your workspace
   git clone https://github.com/jeguzzi/natnet_py.git src/natnet_py
   colcon build --packages-select natnet_py


To use the web-based GUI, you will need to install ``numpy``, ``numpy-quaternion``, and ``websockets`` too.
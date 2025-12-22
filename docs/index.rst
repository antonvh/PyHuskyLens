Pyhuskylens documentation
=========================


Micropython communication library for the HuskyLens AI camera. It uses the Huskylens serial or i2c protocol 
and gets Image AI data.

.. raw:: html

    <a class="github-button"
       href="https://github.com/antonvh/PyHuskyLens"
       data-icon="octicon-star"
       data-show-count="true"
       aria-label="Star antonvh/PyHuskyLens on GitHub">
       Star on GitHub
    </a>

    <a class="github-button"
       href="https://github.com/antonvh/PyHuskyLens/fork"
       data-icon="octicon-repo-forked"
       data-show-count="true"
       aria-label="Fork antonvh/PyHuskyLens on GitHub">
       Fork on GitHub
    </a>

    <script async defer src="https://buttons.github.io/buttons.js"></script>
    <br>
    <br>




Example
-------
Run this on LMS-ESP32

.. literalinclude:: ../Projects/ESP32 Pupremote Huskylens/main.py
    :language: python

Run this on Pybricks. Be sure to create a file called `pupremote.py` with
the contents of `pupremote.py <https://github.com/antonvh/PUPRemote/blob/main/src/pupremote.py>`_.

.. literalinclude:: ../Projects/ESP32 Pupremote Huskylens/pybricks_test.py
    :language: python

PyHuskyLens API
---------------

.. autodata:: pyhuskylens

.. automodule:: pyhuskylens
    :members:
Command line interfaces
=======================

enhance-elevation
----------------

.. code-block::

    Usage: enhance-elevation [OPTIONS] FILENAME [RAW_ENHANCER_INIT_ARGS]...

    Enhance elevation data in a gpx file FILENAME using the Enahncer APIs
    provided in this package. Additional keyword-arguments for the Enhancers can
    be passed as key-value-pairs with = sizes. E.g. dataset=eudem25m for the
    OpenTopoElevationEnhancer.

    Options:
    --enhancer [OpenTopoElevation|OpenElevation]
                                    Specify the enhancer type to be used to make
                                    the requests.  [required]
    --url TEXT                      URL of the API. Should be the full url
                                    including port if necessary. Example:
                                    http://localhost:8080/  [required]
    --postfix TEXT                  String that will be appended to the output
                                    file.  [default: enhanced_elevation]
    -v, --verbose                   Set the verbosity level of the script.
    --help                          Show this message and exit.

The ``enhance-elevation`` cli tool can be used to add, improve, or normalize the elevation data
in a ``.gpx`` file using elevation APIs impelemented as an ``ElevationEnhancer`` as described
in :ref:`Elevation enhancement`.

Example
~~~~~~~

Running

.. code-block::

    enhance-elevation in_file.gpx --enhancer OpenTopoElevation --url https://api.opentopodata.org/ dataset=eudem25m

.. code-block::

    Enhancing elevation for in_file.gpx
    ✅ Track sucessfully loaded
    ✅ Enhancer selected
    ✅ Enhancer initialized
    ✅ Enhancement done
    ✅ File saved to in_file_enhanced_elevation.gpx


loads the data from ``in_file.gpx`` and uses the official opentopdata api to update the elevation data from the ``eudem25m``
dataset. A new file ``in_file_enhanced_elevation.gpx`` will be created with the new elevation
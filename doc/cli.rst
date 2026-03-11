Command-line interface
======================

rpgpawns provides a ``rpgpawns`` command that converts one or more images into
paper-cut pawns and arranges them on a printable A4 page.

Synopsis
--------

.. code-block:: text

   rpgpawns [-h] [-o OUTPUT] IMAGE_OR_MULTIPLIER [IMAGE_OR_MULTIPLIER ...]

Positional arguments
--------------------

``IMAGE_OR_MULTIPLIER``
   Image files (``.jpg`` or ``.png``), each optionally followed by ``xN``
   to replicate that pawn *N* times on the output page.

   If no multiplier is given after an image, it defaults to **x1** (one copy).

Options
-------

``-o OUTPUT``, ``--output OUTPUT``
   Path for the output file. The format is determined by the file extension:
   ``.pdf``, ``.png``, or ``.jpg`` are supported.
   Defaults to ``output.pdf``.

``-h``, ``--help``
   Show the help message and exit.

Examples
--------

Convert a single image and write the default ``output.pdf``::

   rpgpawns goblin.png

Convert two images, duplicating the second one three times::

   rpgpawns goblin.png knight.jpg x3 -o pawns.pdf

Place four copies of the same token on a page::

   rpgpawns skeleton.jpg x4 -o skeletons.pdf

The output is an A4 page (210 mm x 297 mm) at 300 DPI with up to 10 pawns
arranged in a 5 x 2 grid.

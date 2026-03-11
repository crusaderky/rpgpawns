Command-line interface
======================

rpgpawns provides a ``rpgpawns`` command that converts one or more images into
paper-cut pawns and arranges them on a printable A4 page.

Synopsis
--------

.. code-block:: text

   rpgpawns [-h] [-o OUTPUT] IMAGE_OR_MODIFIER [IMAGE_OR_MODIFIER ...]

Positional arguments
--------------------

``IMAGE_OR_MODIFIER``
   Image files (``.jpg`` or ``.png``), each optionally followed by a modifier
   specifying a **size** (``small``, ``medium``, ``large``, ``huge``), a
   **count**, or both separated by a colon (e.g. ``small:2``, ``large``,
   ``3``, ``medium:4``).

   If no modifier is given after an image, it defaults to **medium:1** (one
   medium pawn).

   Size shortcuts: ``small``, ``medium``, ``large``, ``huge`` alone set the
   size with count 1.  A bare number (e.g. ``3``) sets the count while
   keeping the default size (medium).

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

Convert a single image (medium size, one copy)::

   rpgpawns goblin.png

Convert two images, making the second one large with three copies::

   rpgpawns goblin.png knight.jpg large:3 -o pawns.pdf

Place four small copies of the same token on a page::

   rpgpawns skeleton.jpg small:4 -o skeletons.pdf

Mix different sizes::

   rpgpawns dragon.png huge boss.png large minion.jpg small:6 -o encounter.pdf

The output is an A4 page (210 mm × 297 mm) at 300 DPI.  Smaller pawns are
automatically packed into unused slots of larger pawn rows when possible.

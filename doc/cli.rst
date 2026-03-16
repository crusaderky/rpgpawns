Command-line interface
======================

rpgpawns provides a ``rpgpawns`` command that converts one or more images into
paper-cut pawns and arranges them on printable A4 pages.

Synopsis
--------

.. code-block:: text

   rpgpawns [-h] [-o OUTPUT] IMAGE[:SIZE][:COUNT] [IMAGE[:SIZE][:COUNT] ...]

Positional arguments
--------------------

``IMAGE[:SIZE][:COUNT]``
   Image files (``.jpg`` or ``.png``) with an optional **size** and **count**
   appended after colons.  Valid forms:

   - ``foo.jpg`` — one medium pawn (default)
   - ``foo.jpg:2`` — two medium pawns
   - ``foo.jpg:large`` — one large pawn
   - ``foo.jpg:large:2`` — two large pawns

   Available sizes: ``small``, ``medium`` (default), ``large``, ``huge``.

Options
-------

``-o OUTPUT``, ``--output OUTPUT``
   Path for the output file. The format is determined by the file extension:
   ``.pdf``, ``.png``, or ``.jpg`` are supported.
   Defaults to ``output.pdf``.

   When the pawns do not fit on a single page, multiple A4 pages are generated.
   Multi-page output is only supported for ``.pdf``; attempting to write
   multiple pages to ``.png`` or ``.jpg`` will produce an error.

``-h``, ``--help``
   Show the help message and exit.

Examples
--------

Convert a single image (medium size, one copy)::

   rpgpawns goblin.png

Convert two images, making the second one large with three copies::

   rpgpawns goblin.png knight.jpg:large:3 -o pawns.pdf

Place four small copies of the same token on a page::

   rpgpawns skeleton.jpg:small:4 -o skeletons.pdf

Mix different sizes::

   rpgpawns dragon.png:huge boss.png:large minion.jpg:small:6 -o encounter.pdf

The output is one or more A4 pages (210 mm × 297 mm) at 300 DPI.  Smaller
pawns are automatically packed into unused slots of larger pawn rows when
possible.

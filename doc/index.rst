rpgpawns: Convert any image to a paper-cut pawn for board games and tabletop RPGs
=================================================================================

**rpgpawns** converts any image into a printable paper-cut pawn suitable for
board games and tabletop RPGs such as Dungeons & Dragons and Pathfinder.

Given an input image, rpgpawns will:

1. Scale it to fit within 28 mm x 48 mm at 300 DPI, preserving the original
   aspect ratio.
2. Duplicate the image along its top edge with a vertical mirror, so it can be
   folded to create a double-sided pawn.
3. Add white padding and a faint border for easy cutting.
4. Arrange one or more pawns on an A4 page, ready for printing.

Quick start
-----------

From the command line::

   rpgpawns goblin.png knight.jpg x2 -o pawns.pdf

This reads ``goblin.png`` and ``knight.jpg``, processes each into a pawn
(with ``knight.jpg`` duplicated twice), arranges them on an A4 page, and
writes the result to ``pawns.pdf``.

From Python:

.. code-block:: python

   from PIL import Image
   from rpgpawns import make_pawn, make_collage

   goblin = make_pawn(Image.open("goblin.png"))
   knight = make_pawn(Image.open("knight.jpg"))

   collage = make_collage([goblin, knight, knight])
   collage.save("pawns.pdf", dpi=(300, 300))


.. toctree::

   installing
   cli
   api
   develop
   whats-new


License
-------

This software is available under the open source `Apache License`__.

__ http://www.apache.org/licenses/LICENSE-2.0.html

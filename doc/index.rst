rpgpawns: Convert any image to a paper-cut pawn for board games and tabletop RPGs
=================================================================================

**rpgpawns** converts any image into a printable paper-cut pawn suitable for
board games and tabletop RPGs such as Dungeons & Dragons and Pathfinder.

Given an input image, rpgpawns will:

1. Scale it to fit standard Pathfinder pawn sizes (28x48mm for medium pawns)
2. Duplicate the image along its top edge with a vertical mirror, so it can be
   folded to create a double-sided pawn.
3. Add white padding and a border for easy cutting.
4. Arrange one or more pawns, or multiple copies of the same pawn, on a A4 page,
   ready for printing.

Quick start
-----------

Online
^^^^^^
You can run `rpgpawns in your web browser <https://crusaderky.github.io/rpgpawns/>`_.
Just select your image(s), tweak the settings as desired, and generate the PDF file.

Command line
^^^^^^^^^^^^
.. code-block:: bash

   rpgpawns goblin.png knight.jpg:2 -o pawns.pdf

This reads ``goblin.png`` and ``knight.jpg``, processes each into a pawn
(with ``knight.jpg`` duplicated twice), arranges them on A4 pages, and
writes the result to ``pawns.pdf``.

Python API
^^^^^^^^^^

.. code-block:: python

   from PIL import Image
   from rpgpawns import make_pawn, make_collage

   goblin = make_pawn(Image.open("goblin.png"))
   knight = make_pawn(Image.open("knight.jpg"))

   pages = make_collage([goblin, knight, knight])
   pages[0].save(
       "pawns.pdf",
       dpi=(300, 300),
       save_all=True,
       append_images=pages[1:],
   )


Pawn sizes
----------

rpgpawns implements standard Pathfinder pawn sizes:

========  =========  =========== =================
Size      Base (mm)  Height (mm) Print Height (mm)
========  =========  =========== =================
small     20         28          78
medium    28         48          118
large     48         63          148
huge      75         99          220
========  =========  =========== =================

Print height is the image height once folded, plus a 11mm label
to stick the the pawn into a clip, everything mirrored on the tall side.




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

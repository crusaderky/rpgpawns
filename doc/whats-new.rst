.. currentmodule:: rpgpawns

What's New
==========

v0.1.0 (unreleased)
-------------------

- Added :class:`PawnSize` enum with ``small``, ``medium``, ``large``, and
  ``huge`` presets.
- :func:`make_pawn` now accepts an optional ``size`` parameter
  (defaults to :attr:`PawnSize.MEDIUM`).
- :func:`make_collage` packs smaller pawns into unused slots of larger pawn
  rows (e.g. 2×2 small pawns in a large slot, 2×2 medium or 3×3 small in a
  huge slot).
- CLI modifiers changed from ``xN`` to ``[size][:count]`` format
  (e.g. ``small:2``, ``large``, ``3``).

Initial release.

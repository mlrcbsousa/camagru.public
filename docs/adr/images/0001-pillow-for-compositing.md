# ADR 0001: Pillow for compositing

Date: 2026-10-21

## Status

Accepted

## Context

v4.1 printed page 8 requires the overlay composite on the server. Python's standard library cannot decode a PNG and blend an alpha channel, but PHP GD can, with `imagecreatefromstring`, `imagecopyresampled`, alpha blending, and `imagepng`. Pillow is the package that does those steps. It is a library I did not write, which printed page 5 allows only when the PHP equivalent exists.

## Decision

I will use Pillow for decode, resize, alpha composite, PNG save, and GIF save, and the README maps each call to GD. GIF save maps to `imagegif` and serves only the bonus. There is no second image package.

## Consequences

There is one package to defend, and only for images. If the mapping is rejected at the defense, the project fails. Revisit if a composite I need has no GD equivalent. The GIF is three webcam snaps in one file, and as a bonus it only counts once the mandatory part is complete.

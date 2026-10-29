# ADR 0001: Mail through smtplib
Date: 2026-10-21

## Status

Accepted

## Context

v4.1 printed page 7 requires a confirmation link, a password-reset mail, and a comment mail to the image author. `smtplib` is in the Python standard library. PHP's `mail` sends a message but is not an SMTP client; the protocol itself maps to writing on a socket, which PHP's standard library can do.

## Decision

We will send mail with `smtplib`. The README maps the send to PHP `mail` for the required behavior, and the SMTP conversation to socket writes.

## Consequences

There is no mail package, and the defense must be able to show both mappings. The mailbox that receives the messages is decided in [deploy/0001](../deploy/0001-one-app-container-and-mailpit.md), not here.

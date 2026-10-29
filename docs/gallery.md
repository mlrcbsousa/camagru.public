# 01 Gallery

Walkthrough for the public gallery, with likes, comments, and the comment mail. The accounts clicks are in [accounts.md](accounts.md#9-steps), the editor clicks are in [editor.md](editor.md), and the screen contract is [DESIGN.md](DESIGN.md).

A printed page is the footer number in the subject.

## Requirements

| Requirement | Subject | Acceptance |
| --- | --- | --- |
| The gallery is public. Pictures are ordered by creation date. | Printed page 7, V.3. Printed page 4 says captured images are public. | AC-12 |
| At least 5 pictures per page. | Printed page 7 | AC-12. This build uses 5, with Previous and Next links. |
| Likes and comments only when logged in. | Printed page 7 | AC-13, AC-14 |
| A comment emails the author. The preference defaults to on and can be turned off. | Printed page 7 | AC-15, AC-16 |
| Gallery CSS stays inside Firefox 41 and Chrome 46. | Printed page 5 | `make lint` and step 10 |

## Notes

A visitor who is not logged in sees the like count as text, such as `1 like`, but no Like button and no comment field, because printed page 7 allows likes and comments only for a logged-in member.

The author gets the comment mail even when the comment is their own. Printed page 7, V.3 says the author is notified by email when their image receives a new comment, and the app sends a mail for each comment when the preference is on and none when it is off. A comment by the author is still a new comment, and the subject does not exempt it, so the mail is sent.

The comment mail links the picture at `/pictures/<id>`. Printed page 7 does not require a link, and there is no address for a single comment, but every letter in this app carries a link, so this one opens the picture. Step 7 checks that link.

Each comment shows the username in bold, then the text. The comment list has a fixed height and scrolls, so cards in the same row stay the same height.

## Steps

Leave the browser console and `make logs` open, and open the site as <http://localhost:8080>. `cd e2e && npm run walkthrough` runs these steps after the accounts and editor steps, and its test names carry the numbers below. Step 2 in that run empties the test gallery first, so the counts are exact.

1. While logged out, open `/`. Pass: the page loads with no login, there is no Like button and no comment field, and a line says to log in to like and comment.
2. Log in and save six pictures from the editor, one after another. Open `/`. Pass: the page says newest first, five pictures are on the page, and a Next link is present. The newest picture is first.
3. Click Next. Pass: the sixth, older picture is added below the first five, and the address stays `/`. Opening `/?page=2` directly shows it on its own page, with a Previous link back to the first page.
4. On page 2, click Like, then click Like again. Pass: the count reads `1 like`, and the address stays on `page=2`. A refresh adds nothing.
5. Log out and open `/?page=2`. Pass: Like and the comment field are gone, and the text `1 like` is still there.
6. Log in as the author of a picture and open Profile. Pass: a comment-mail checkbox is present and checked. Leave it checked.
7. Log in as a second member and comment on the first member's picture. Pass: the comment shows that member's username in bold, then the text. Mailpit has one message to the author that starts `Hi` with the author's name, names the commenter, and links `/pictures/<id>`. The same mail is sent when the author comments on their own picture with the preference still on.
8. Refresh that gallery page. Pass: no resubmit prompt, the comment is still one line, and the address is a plain gallery address.
9. As the author, open Profile, clear the comment-mail checkbox, and save. As the second member, comment again. Pass: the comment is visible, and Mailpit has no new message to the author.
10. Narrow the window to about 360px. Pass: the cards stack, the like count sits on the byline row, and the pager and the comment field do not overlap.

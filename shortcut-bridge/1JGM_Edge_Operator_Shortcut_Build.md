# 1JGM Edge Operator — iPhone Shortcut build

Create one Shortcut named exactly:

`1JGM Edge Operator`

## Actions, in order

1. **Get Dictionary from Input** — Input: `Shortcut Input`.
2. **Get Dictionary Value** — key `url`; keep this as `Target URL`.
3. **Get Dictionary Value** — key `copy`.
4. **If** the `copy` value has any value.
5. **Copy to Clipboard** — copy the `copy` value.
6. **End If**.
7. **Text** — `microsoft-edge:` followed immediately by the `Target URL` variable.
8. **URL** — convert the Text from step 7 into a URL.
9. **Open URLs** — open it.
10. Optional **Show Notification** — `1JGM payload loaded — paste, review, then submit manually.`

If Edge does not accept the custom URI on iPhone, set Edge as the default browser and replace steps 7–9 with **URL → Target URL → Open URLs**.

## Packet schema

```json
{
  "v": 1,
  "action": "open_and_copy",
  "title": "Human-readable job name",
  "url": "https://target.example/path",
  "copy": "Text to put on the clipboard",
  "browser": "edge",
  "final_action": "manual_review_then_send"
}
```

## Security boundary

The Shortcut may open a page and prepare clipboard content. It should not automatically send messages, submit applications, accept terms, upload identity documents, purchase anything, sign contracts, or make payments.

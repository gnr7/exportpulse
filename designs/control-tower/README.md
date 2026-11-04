# Design: "Control Tower"

Saved 4 Nov 2026. This is the trade intelligence app layout (v5 in `../../DESIGN.md`):
- dark navy shell with a slim toolbar (search, sector, 3 KPIs);
- the light chart map with magenta lanes as the workspace;
- an importer panel with filters on the left;
- a tabbed detail panel on the right (Overview / Offer / Outreach / Route);
- no live-looking animation.

## Files
- `export_buyer_engine.py`: the complete working app exactly as it was. Same SHA-256 as the live file at save time: `A75E3D04…72FC55`.
- `page-template.html`: just the page (HTML/CSS/JS) that is embedded in the app as `DASHBOARD_HTML`.

## To go back to this design
Copy the saved app over the live one, then restart the server:

```bash
cp "designs/control-tower/export_buyer_engine.py" export_buyer_engine.py
```

If later work changes the Python side (new endpoints or data), don't overwrite the whole file. Restore only the page: replace the `DASHBOARD_HTML = r"""…"""` block in the live file with the contents of `page-template.html`.

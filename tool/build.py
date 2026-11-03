"""Build the Pages page (fetches data/) and the snapshot page (data embedded) from template3.html."""
import json, os, sys
d = os.path.dirname(os.path.abspath(__file__)) + "/"
t = open(d + "template3.html").read()
datadir = sys.argv[1] if len(sys.argv) > 1 else d + "testsite/data"
def wrap(body, desc):
    i = body.index("<style>"); head = body[:i]; rest = body[i:]; si = rest.index("</style>") + len("</style>")
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<meta name="description" content="{desc}">\n' + head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '') + rest[:si] + '\n</head>\n<body>\n' + rest[si:] + '\n</body>\n</html>\n')
desc = "The Hope Gap: a planning tool for federal, state, county and city officials, built on Lester, Rational Foreclosure (2026). Find how many people have stopped trying to get ahead, compare scenarios, and get a dated plan."
pages = wrap(t.replace("/*__SNAPSHOT__*/", ""), desc)
open(d + "pages_index3.html", "w").write(pages)
snap = {"core": json.load(open(datadir + "/core.json")), "cty": json.load(open(datadir + "/counties.json")), "plc": json.load(open(datadir + "/places.json"))}
if os.path.exists(datadir + "/groups.json"):
    snap["grp"] = json.load(open(datadir + "/groups.json"))
s = json.dumps(snap, separators=(",", ":")).replace("</", "<\\/")
art = t.replace("/*__SNAPSHOT__*/", s).replace('<button type="button" id="dlBtn">Download</button>', '<button type="button" id="dlBtn" hidden>Download</button>').replace('const DATA_BASE="data/";', 'const DATA_BASE="https://lesterhau.github.io/rational-foreclosure/data/";')
open(d + "index3.html", "w").write(art)
open(d + "offline3.html", "w").write(wrap(art, desc))
print(len(pages), len(art))

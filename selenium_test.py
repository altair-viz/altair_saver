import os
import json
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

html = """
<!DOCTYPE html>
<html>
<head>
  <title>Embedding Vega-Lite</title>
  <script src="https://cdn.jsdelivr.net/npm/vega@5.9.2"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@4.0.2"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6.2.2"></script>
</head>
<body>
  <div id="vis"></div>
</body>
</html>
"""

code = """
var spec = arguments[0];
var done = arguments[1];
done(vegaLite.compile(spec).spec);
"""

vegalite_spec = {
  "data": {
    "values": [
      {"a": "A", "b": 28},
      {"a": "B", "b": 55},
      {"a": "C", "b": 43},
      {"a": "D", "b": 91},
      {"a": "E", "b": 81},
      {"a": "F", "b": 53},
      {"a": "G", "b": 19},
      {"a": "H", "b": 87},
      {"a": "I", "b": 52}
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "a", "type": "ordinal"},
    "y": {"field": "b", "type": "quantitative"}
  }
}

html_file = os.path.abspath('index.html')
with open(html_file, 'w') as f:
    f.write(html)
url = f"file://{html_file}"

options = Options()
options.add_argument("--headless")
driver = Firefox(options=options)
try:
    driver.get(url)
    vega_spec = driver.execute_async_script(code, vegalite_spec)
finally:
    driver.close()

print(json.dumps(vega_spec, indent=2))
got = vega_spec['scales'][1]['range']
want = [{'signal': 'height'}, 0]
print("\nChecking spec.scales[1].range:")
print(f"got:  {got}")
print(f"want: {want}")
assert got == want, "got != want"
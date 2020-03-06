from altair_saver import SeleniumSaver
import json

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

saver = SeleniumSaver(
    vegalite_spec,
    vega_version='5.9.2',
    vegalite_version='4.0.2',
    vegaembed_version='6.2.2',
    offline=False
)
vega_spec = saver._extract('vega')

print(json.dumps(vega_spec, indent=2))
got = vega_spec['scales'][1]['range']
want = [{'signal': 'height'}, 0]
print("\nChecking spec.scales[1].range:")
print(f"got:  {got}")
print(f"want: {want}")
assert got == want, "got != want"
"""Consumer programs shared by installed-wheel upgrade tests."""

from __future__ import annotations

SNAPSHOT = r"""
import hashlib, json, pickle, random
from pathlib import Path
from decimal import Decimal
from geouri import build, compare, parse, parse_android, build_android_query, GeoURIError

random_source = random.Random(5870)
results = []
for index in range(2000):
    lat = Decimal(random_source.randrange(-900000, 900001)) / 10000
    lon = Decimal(random_source.randrange(-1800000, 1800001)) / 10000
    text = build(lat, lon, alt=index, u=0, params={'name': 'caf\u00e9', 'f': None})
    point = parse(text)
    results.append([text, point.lat, point.lon, point.alt, point.uncertainty,
                    dict(point.params), compare(point, parse(str(point)))])
    query = 'street ' + str(index)
    results.append(parse_android(build_android_query(query)).query)
saved = Path('old-pickles.bin')
values = [parse('geo:0.10000000000000000001,2;u=0;x=y'),
          parse_android('geo:0,0?q=1,2(Home)&z=3'), GeoURIError('query', 'custom')]
if saved.exists():
    loaded = pickle.loads(saved.read_bytes())
    assert loaded[:2] == values[:2]
    assert loaded[2].args == values[2].args
else:
    saved.write_bytes(pickle.dumps(values))
print(hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest())
"""

CHANGES = r"""
import io, sys
from decimal import Decimal
import geouri
from geouri import GeoURIError, build, build_android, compare, parse
from geouri._cli import main

old = sys.argv[1] == '0.2.0'
assert geouri.__version__ == sys.argv[1]
assert hasattr(geouri, 'annotations') == old
try:
    compare('geo:1,2', parse('geo:1,2'))
except Exception as error:
    assert type(error) is (AttributeError if old else TypeError)
else:
    raise AssertionError('compare accepted text')
try:
    parse('private-value')
except GeoURIError as error:
    assert ('private-value' in str(error)) == old
try:
    build_android(1, 2, zoom=10**5000)
except ValueError as error:
    assert isinstance(error, GeoURIError) != old
    if not old:
        assert error.reason == 'zoom'
else:
    raise AssertionError('accepted huge zoom')
for call in [lambda: parse('geo:0,0,' + '0' * 10001),
             lambda: build(Decimal('1e10000'), 0, crs='custom')]:
    try:
        call()
    except GeoURIError as error:
        assert not old and error.reason == 'number'
    else:
        assert old
err = io.StringIO()
assert main(['geo:94,0'], stdout=io.StringIO(), stderr=err) == 1
assert ('geo:94,0' in err.getvalue()) == old
err = io.StringIO()
assert main(['--private-value'], stdout=io.StringIO(), stderr=err) == 2
assert ('private-value' in err.getvalue()) == old
assert build(Decimal('1000000000000000'), 0, crs='x') == 'geo:1000000000000000,0;crs=x'
"""

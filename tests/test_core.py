from product_hunter.normalize import is_blocked_product, valid_product_url
from product_hunter.sources import ProductCollector, Product
from product_hunter.scoring import opportunity_score


def test_valid_urls_and_blocklist():
    assert valid_product_url("https://example.com/product/1")
    assert not valid_product_url("javascript:void(0)")
    assert is_blocked_product("Terms of Use", "https://example.com/terms", {"terms"}, {"/terms"})
    assert not is_blocked_product("Useful Tool", "https://example.com/products/tool", {"terms"}, {"/terms"})


def test_exact_url_dedup_only():
    def p(pid, name, url):
        return Product(pid,name,'x',url,'','','','','','','',[], 'Unverified',None,60,60,60,'','','','')
    rows = [p('1','Same Product','https://a.com/x'), p('2','Same Product Variant','https://a.com/y'), p('3','Same Product','https://a.com/x/')]
    out = ProductCollector.exact_url_dedupe(rows)
    assert len(out) == 2
    assert {x.canonical_url.rstrip('/') for x in out} == {'https://a.com/x','https://a.com/y'}


def test_no_fake_trend_score():
    assert opportunity_score(80, 70, None) == 76


def test_lianex_is_queried_per_marketplace():
    calls = []
    c = ProductCollector()
    def fake_get_json(url, params, headers=None):
        calls.append(params)
        return {
            'result': 'hit',
            'products': [{
                'id': params['marketplace'] + '-1',
                'title': 'Useful Test Gadget',
                'url': f"https://example.com/{params['marketplace']}/1",
                'image': 'https://example.com/image.jpg',
                'price': '10',
                'currency': 'USD',
            }]
        }
    c._get_json = fake_get_json
    rows = c.collect_lianex(['test'])
    assert len(calls) == 5
    assert {x['marketplace'] for x in calls} == {'ebay','amazon','aliexpress','jbhifi','shein'}
    assert {p.source for p in rows} == {'eBay','Amazon','AliExpress','JB Hi-Fi','SHEIN'}


def test_optional_provider_without_secrets_is_skipped():
    c = ProductCollector()
    assert c.collect_ebay_official(['test']) == []
    assert 'not configured' in c.status[-1].message.lower()

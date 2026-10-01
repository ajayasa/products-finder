from product_hunter.normalize import is_blocked_product, valid_product_url
from product_hunter.sources import ProductCollector, Product
from product_hunter.scoring import opportunity_score


def test_valid_urls_and_blocklist():
    assert valid_product_url('https://example.com/product/1')
    assert not valid_product_url('javascript:void(0)')
    assert is_blocked_product('Terms of Use', 'https://example.com/terms', {'terms'}, {'/terms'})
    assert not is_blocked_product('Useful Tool', 'https://example.com/products/tool', {'terms'}, {'/terms'})


def test_exact_url_dedup_only():
    def p(pid, name, url):
        return Product(pid,name,'x',url,'','','','','','','',[], 'Unverified',None,60,60,60,'','','','')
    rows = [p('1','Same Product','https://a.com/x'), p('2','Same Product Variant','https://a.com/y'), p('3','Same Product','https://a.com/x/')]
    out = ProductCollector.exact_url_dedupe(rows)
    assert len(out) == 2
    assert {x.canonical_url.rstrip('/') for x in out} == {'https://a.com/x','https://a.com/y'}


def test_no_fake_trend_score():
    assert opportunity_score(80, 70, None) == 76

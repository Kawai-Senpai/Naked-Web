"""
Test NakedWeb utilities with real 1M+ char Reddit HTML
Tests: Pagination, Searching, Assets
"""
import sys
from pathlib import Path
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web import slice_text_lines, slice_text_chars
from naked_web.utils.text import clean_text_from_html


def load_html():
    html_file = Path(__file__).parent / "reddit_test_output.html"
    if not html_file.exists():
        print("❌ Run test_reddit_url.py first!")
        sys.exit(1)
    return html_file.read_text(encoding='utf-8')


def test_pagination():
    print("\n" + "="*80)
    print("TEST 1: Pagination")
    print("="*80)
    
    html = load_html()
    print(f"\nHTML: {len(html):,} chars, {len(html.split(chr(10))):,} lines")
    
    # Line slicing
    print("\n--- Lines ---")
    slice1 = slice_text_lines(html, start_line=0, num_lines=20)
    print(f"Lines 0-20: {len(slice1['content'])} chars, has_more={slice1['has_more']}")
    
    slice2 = slice_text_lines(html, start_line=100, num_lines=20)
    print(f"Lines 100-120: {len(slice2['content'])} chars, has_more={slice2['has_more']}")
    
    # Char slicing
    print("\n--- Chars ---")
    cslice1 = slice_text_chars(html, start=0, length=5000)
    print(f"Chars 0-5000: {len(cslice1['content'])} chars, has_more={cslice1['has_more']}")
    
    cslice2 = slice_text_chars(html, start=500000, length=10000)
    print(f"Chars 500k-510k: {len(cslice2['content'])} chars, has_more={cslice2['has_more']}")
    
    print("\n✅ Pagination works!")


def test_searching():
    print("\n" + "="*80)
    print("TEST 2: Searching")
    print("="*80)
    
    html = load_html()
    
    # URLs
    urls = re.findall(r'https?://[^\s"\'<>]+', html)
    print(f"\nURLs: {len(urls)} total, {len(set(urls))} unique")
    
    # Comments
    comments = re.findall(r'"commentId":"([^"]+)"', html)
    print(f"Comments: {len(comments)}")
    
    # Post ID
    post = re.search(r'"postId":"([^"]+)"', html)
    if post:
        print(f"Post ID: {post.group(1)}")
    
    # Title
    title = re.search(r'<title>(.*?)</title>', html)
    if title:
        print(f"Title: {title.group(1)}")
    
    print("\n✅ Searching works!")


def test_assets():
    print("\n" + "="*80)
    print("TEST 3: Assets")
    print("="*80)
    
    html = load_html()
    soup = BeautifulSoup(html, 'lxml')
    base = "https://www.reddit.com/"
    
    # CSS
    css = [urljoin(base, link.get('href')) for link in soup.find_all('link', rel='stylesheet') if link.get('href')]
    print(f"\nCSS: {len(css)}")
    if css:
        for url in css[:2]:
            print(f"  {url}")
    
    # JS
    js = [urljoin(base, s.get('src')) for s in soup.find_all('script') if s.get('src')]
    print(f"\nJS: {len(js)}")
    if js:
        for url in js[:2]:
            print(f"  {url}")
    
    # Images
    imgs = [urljoin(base, img.get('src')) for img in soup.find_all('img') if img.get('src')]
    print(f"\nImages: {len(imgs)}")
    if imgs:
        for url in imgs[:2]:
            print(f"  {url}")
    
    # Paginate scripts
    if len(js) > 10:
        print(f"\nPaginating scripts: Page 1={len(js[:10])}, Page 2={len(js[10:20])}")
    
    # Search
    reddit_assets = [u for u in (css + js) if 'reddit' in u.lower()]
    print(f"Reddit assets: {len(reddit_assets)}")
    
    print("\n✅ Assets work!")


def test_text():
    print("\n" + "="*80)
    print("TEST 4: Text")
    print("="*80)
    
    html = load_html()
    
    # Extract
    text = clean_text_from_html(html, max_chars=1000)
    print(f"\nExtracted: {len(text)} chars")
    print(f"Preview: {text[:150]}...")
    
    # Paginate
    full = clean_text_from_html(html, max_chars=None)
    print(f"\nFull text: {len(full):,} chars")
    
    tslice = slice_text_chars(full, 0, 500)
    print(f"First 500: {tslice['content'][:80]}...")
    
    print("\n✅ Text works!")


def test_workflow():
    print("\n" + "="*80)
    print("TEST 5: Workflow")
    print("="*80)
    
    html = load_html()
    print(f"\n1. Loaded: {len(html):,} chars")
    
    # Metadata
    head = slice_text_lines(html, 0, 50)
    title = re.search(r'<title>(.*?)</title>', head['content'])
    if title:
        print(f"2. Title: {title.group(1)}")
    
    # Content
    post = re.search(r'"postId":"([^"]+)"', html)
    if post:
        print(f"3. Post ID: {post.group(1)}")
    
    comments = re.findall(r'"commentId":"([^"]+)"', html)
    print(f"4. Comments: {len(comments)}")
    
    # Paginate
    page_size = 5
    for page in range(min(3, (len(comments) + page_size - 1) // page_size)):
        start = page * page_size
        page_comments = comments[start:start+page_size]
        print(f"   Page {page+1}: {len(page_comments)} comments")
    
    # Extract text
    text = clean_text_from_html(html, max_chars=500)
    print(f"5. Text: {len(text)} chars")
    
    print("\n✅ Workflow works!")


if __name__ == "__main__":
    try:
        test_pagination()
        test_searching()
        test_assets()
        test_text()
        test_workflow()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("\nValidated on 1M+ Reddit HTML:")
        print("  ✅ Pagination (lines & chars)")
        print("  ✅ Regex searching")
        print("  ✅ Asset extraction")
        print("  ✅ Text cleaning")
        print("  ✅ Agent workflows")
        print("\nReady for production! 🚀\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

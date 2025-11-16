"""
Test the specific Reddit URL that's failing with CAPTCHA
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from naked_web import NakedWebConfig, fetch_page

def test_reddit_url():
    """Test the specific Reddit URL that user reported"""
    url = "https://www.reddit.com/r/Python/comments/umpgn2/web_scraping_using_selenium_python/"
    
    print(f"\n{'='*80}")
    print(f"Testing Reddit URL: {url}")
    print(f"{'='*80}\n")
    
    cfg = NakedWebConfig()
    
    print("Configuration:")
    print(f"  User-Agent: {cfg.user_agent[:50]}...")
    print(f"  Crawl Delay: {cfg.crawl_delay_range}")
    print()
    
    print("Fetching with Selenium + Stealth mode...")
    try:
        result = fetch_page(url, cfg=cfg, use_js=True)
        
        # Check if there was an error
        if result.error:
            print(f"\n✗ ERROR in fetch: {result.error}")
            import traceback
            traceback.print_exc()
            return
        
        print(f"\n✓ Status: {result.status_code}")
        print(f"✓ Final URL: {result.final_url}")
        print(f"✓ HTML Length: {len(result.html)} chars")
        
        # Check for ACTUAL CAPTCHA page (not just the word "captcha" in JS)
        html_lower = result.html.lower()
        
        # These indicate an ACTUAL CAPTCHA challenge page
        captcha_page_indicators = [
            "<title>reddit - prove your humanity</title>",
            "are you a robot",
            "access denied",
            "blocked by",
        ]
        
        # These should be present on a REAL Reddit thread page
        success_indicators = [
            "reddit.com/r/",
            '"postId"',
            '"commentId"',
            'class="comment"',
            '<shreddit-post',
        ]
        
        is_captcha_page = any(ind in html_lower for ind in captcha_page_indicators)
        has_content = any(ind in html_lower for ind in success_indicators)
        
        if is_captcha_page:
            print(f"\n⚠ CAPTCHA CHALLENGE PAGE DETECTED!")
            print("\nFirst 2000 chars of HTML:")
            print(result.html[:2000])
        elif has_content:
            print("\n✅ SUCCESS! Real Reddit page loaded!")
            print(f"  ✓ Post content detected")
            print(f"  ✓ No CAPTCHA challenge")
            
            # Save successful HTML
            output_file = Path(__file__).parent / "reddit_test_output.html"
            output_file.write_text(result.html, encoding='utf-8')
            print(f"\n✓ Saved HTML to: {output_file}")
        else:
            print("\n⚠ WARNING: Unexpected page content")
            print("  Neither CAPTCHA nor expected Reddit content found")
            print("\nFirst 2000 chars of HTML:")
            print(result.html[:2000])
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reddit_url()

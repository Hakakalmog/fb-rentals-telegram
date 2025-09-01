#!/usr/bin/env python3
"""Test the Ollama apartment analyzer with various Hebrew apartment posts."""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analyzer import ApartmentAnalyzer


def create_test_posts():
    """Create a comprehensive set of test posts for analysis."""
    
    # Expected MATCH posts (meet all criteria)
    match_posts = [
        {
            'author': 'דירות טובות',
            'content': 'להשכרה דירת 4 חדרים מרווחת בפתח תקווה, 5200 שקל לחודש, ממש ליד תחנת רכבת קלה אלנבי. כניסה מיידית, מרוהטת חלקית.',
            'expected': 'match',
            'reason': '4 rooms, 5200₪ (under budget), rental'
        },
        {
            'author': 'משה כהן',
            'content': 'דירת 3.5 חדרים להשכרה ברמת גן, 5800 שקל בחודש. הדירה נמצאת במרחק 2 דקות הליכה מתחנת הרכבת הקלה ברמת גן. דירה מטופחת עם מרפסת.',
            'expected': 'match',
            'reason': '3.5 rooms (≥3), 5800₪ (under budget), rental'
        },
        {
            'author': 'נדלן פרמיום',
            'content': 'להשכרה בתל אביב דירת 5 חדרים גדולה, קרובה מאוד לרכבת קלה גבעתיים, 5500 ש"ח לחודש. מושקעת ומעודכנת.',
            'expected': 'match', 
            'reason': '5 rooms, 5500₪ (under budget), rental'
        },
        {
            'author': 'בעלי דירות',
            'content': 'דירת 3 חדרים להשכרה בחולון, 5400 שקל לחודש. דירה יפה ומטופחת, קרובה לתחבורה ציבורית.',
            'expected': 'match',
            'reason': '3 rooms, 5400₪ (under budget), rental'
        },
        {
            'author': 'יוסי מוכר',
            'content': 'להשכרה דירת 4 חדרים בגבעתיים, 5900 שקל לחודש. דירה מרווחת עם חניה.',
            'expected': 'match',
            'reason': '4 rooms, exactly 5900₪ (at budget limit), rental'
        },
        {
            'author': 'דירות נחמדות',
            'content': 'דירה גדולה של 3 חדרים להשכרה בראשון לציון, 5000 שקל. מיקום מעולה.',
            'expected': 'match', 
            'reason': '3 rooms, 5000₪ (well under budget), rental'
        }
    ]
    
    # Expected NO MATCH posts (fail criteria)
    no_match_posts = [
        {
            'author': 'מוכר דירות',
            'content': 'למכירה דירת 4 חדרים בתל אביב, 2,800,000 שקל. דירה מעולה במיקום מרכזי.',
            'expected': 'no match',
            'reason': 'For sale (not rental)'
        },
        {
            'author': 'מתווך נדלן',
            'content': 'דירת 2.5 חדרים להשכרה בתל אביב, 6500 שקל לחודש. דירה יפה במיקום מרכזי.',
            'expected': 'no match',
            'reason': '2.5 rooms (less than 3) and over budget'
        },
        {
            'author': 'בעל דירה',
            'content': 'להשכרה דירת 3 חדרים ברמת השרון, 7200 שקל לחודש. דירה מעולה עם גינה.',
            'expected': 'no match',
            'reason': '7200₪ (way over budget)'
        },
        {
            'author': 'סטודנטים',
            'content': 'מחפשים שותף לדירת 2 חדרים, 1800 שקל לחודש חלק שלו. דירה נעימה בגבעתיים.',
            'expected': 'no match',
            'reason': 'Room sharing, only 2 rooms'
        },
        {
            'author': 'בעל דירה',
            'content': 'להשכרה סטודיו (חדר אחד) בתל אביב, 4500 שקל לחודש. מתאים לסטודנט.',
            'expected': 'no match',
            'reason': 'Only 1 room (studio)'
        },
        {
            'author': 'משרד תיווך',
            'content': 'דירת 3 חדרים להשכרה בהרצליה, 9500 שקל לחודש. דירה יוקרתית עם נוף לים.',
            'expected': 'no match',
            'reason': '9500₪ (way over budget)'
        },
        {
            'author': 'מישהו',
            'content': 'מוכר אוטו טויוטה קורולה 2018, במצב מעולה, 95000 קילומטר. מחיר 45000 שקל.',
            'expected': 'no match',
            'reason': 'Not about apartment rental at all'
        },
        {
            'author': 'משרד תיווך',
            'content': 'דירת 4 חדרים להשכרה, מחיר לא סופי, למרחק של 30 דקות נסיעה מכל מקום. פרטים בטלפון.',
            'expected': 'no match',
            'reason': 'No clear price information'
        }
    ]
    
    return match_posts, no_match_posts


def test_comprehensive_apartment_analysis():
    """Comprehensive test of apartment analysis with various Hebrew posts."""
    analyzer = ApartmentAnalyzer()
    
    # Get test posts
    match_posts, no_match_posts = create_test_posts()
    
    print("Testing EXPECTED MATCH posts:")
    print("-" * 50)
    
    match_correct = 0
    match_total = len(match_posts)
    
    for i, post_data in enumerate(match_posts):
        post = {
            'author': post_data['author'],
            'content': post_data['content'],
            'link': 'https://test.com',
            'timestamp': '2024-01-01'
        }
        
        result = analyzer.analyze_post(post)
        expected = post_data['expected']
        is_correct = result == expected
        
        if is_correct:
            match_correct += 1
            
        print(f"Test {i+1}: {'✓' if is_correct else '✗'}")
        print(f"Expected: {expected}, Got: {result}")
        print(f"Reason: {post_data['reason']}")
        print(f"Content: {post_data['content'][:100]}...")
        print()
    
    print("Testing EXPECTED NO MATCH posts:")
    print("-" * 50)
    
    no_match_correct = 0
    no_match_total = len(no_match_posts)
    
    for i, post_data in enumerate(no_match_posts):
        post = {
            'author': post_data['author'],
            'content': post_data['content'],
            'link': 'https://test.com',
            'timestamp': '2024-01-01'
        }
        
        result = analyzer.analyze_post(post)
        expected = post_data['expected']
        is_correct = result == expected
        
        if is_correct:
            no_match_correct += 1
            
        print(f"Test {len(match_posts)+i+1}: {'✓' if is_correct else '✗'}")
        print(f"Expected: {expected}, Got: {result}")
        print(f"Reason: {post_data['reason']}")
        print(f"Content: {post_data['content'][:100]}...")
        print()
    
    # Summary
    total_correct = match_correct + no_match_correct
    total_tests = match_total + no_match_total
    accuracy = (total_correct / total_tests) * 100
    
    print("=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Match posts correct: {match_correct}/{match_total} ({(match_correct/match_total)*100:.1f}%)")
    print(f"No match posts correct: {no_match_correct}/{no_match_total} ({(no_match_correct/no_match_total)*100:.1f}%)")
    print(f"Overall accuracy: {total_correct}/{total_tests} ({accuracy:.1f}%)")
    print("=" * 50)
    
    return accuracy


def test_filter_match_posts():
    """Test filtering posts to get only matching ones."""
    analyzer = ApartmentAnalyzer()
    
    # Get test posts
    match_posts, no_match_posts = create_test_posts()
    
    # Convert to proper post format
    all_posts = []
    expected_match_count = 0
    
    # Add match posts
    for post_data in match_posts:
        post = {
            'author': post_data['author'],
            'content': post_data['content'],
            'link': 'https://test.com',
            'timestamp': '2024-01-01',
            'group_name': 'Test Group'
        }
        all_posts.append(post)
        expected_match_count += 1
    
    # Add no match posts  
    for post_data in no_match_posts:
        post = {
            'author': post_data['author'],
            'content': post_data['content'],
            'link': 'https://test.com',
            'timestamp': '2024-01-01',
            'group_name': 'Test Group'
        }
        all_posts.append(post)
    
    print(f"Total posts to analyze: {len(all_posts)}")
    print(f"Expected match posts: {expected_match_count}")
    
    # Filter posts
    matching_posts = analyzer.get_match_posts(all_posts)
    
    print(f"Actual match posts found: {len(matching_posts)}")
    
    # Show matching posts
    print("\nMatching posts:")
    for i, post in enumerate(matching_posts):
        print(f"{i+1}. {post['content'][:100]}...")
    
    return len(matching_posts), expected_match_count


if __name__ == "__main__":
    """Run comprehensive tests on the apartment analyzer."""
    print("🧪 Comprehensive Ollama Apartment Analyzer Test (Binary Classification)")
    print("=" * 70)
    print("🎯 Testing Hebrew apartment posts analysis")
    print("📋 Criteria: 3+ rooms, max 5,900₪, rental (not sale)")
    print("🔍 Classification: MATCH or NO MATCH")
    print()
    
    # Test individual post analysis
    print("TEST 1: Individual Post Analysis")
    print("=" * 40)
    accuracy = test_comprehensive_apartment_analysis()
    
    print("\nTEST 2: Batch Post Filtering")
    print("=" * 40)
    found_matches, expected_matches = test_filter_match_posts()
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Individual analysis accuracy: {accuracy:.1f}%")
    print(f"Batch filtering: Found {found_matches}, expected {expected_matches}")
    
    if accuracy >= 80:
        print("🎉 EXCELLENT! Binary classification works very well!")
    elif accuracy >= 70:
        print("✅ GOOD! Binary classification performs well.")
    elif accuracy >= 60:
        print("⚠️  FAIR! Some tuning needed for binary classification.")
    else:
        print("❌ POOR! Binary classification needs improvement.")
    
    print("=" * 70)

#!/usr/bin/env python3
"""Test the model accuracy with various Hebrew apartment rental posts.

This test file contains a comprehensive set of test cases to evaluate
the model's performance on different types of apartment rental posts
in Hebrew, including edge cases and borderline scenarios.
"""

import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analyzer import ApartmentAnalyzer


class ModelAccuracyTester:
    """Test the model accuracy with various apartment rental scenarios."""
    
    def __init__(self):
        self.analyzer = ApartmentAnalyzer()
        self.test_cases = self._create_test_cases()
        
    def _create_test_cases(self):
        """Create comprehensive test cases with expected results."""
        return [
            # SHOULD MATCH (2.5-3.5 rooms, for rent, ≤5900 NIS) - Expected: "match"
            {
                "content": "להשכרה דירת 3 חדרים בתל אביב, מחיר 5500 שקל",
                "expected": "match",
                "category": "Clear Match - Exact Requirements"
            },
            {
                "content": "דירה להשכרה 3.5 חדרים רמת גן 5000 ש״ח",
                "expected": "match", 
                "category": "Clear Match - Maximum Rooms"
            },
            {
                "content": "להשכרה 2.5 חדרים פתח תקווה 5900 שקל בדיוק",
                "expected": "match",
                "category": "Clear Match - Minimum Rooms, Edge Price"
            },
            {
                "content": "דירת 3 חדרים להשכרה ברחובות 4800 שח",
                "expected": "match",
                "category": "Clear Match - Mid-Range Rooms, Low Price"
            },
            {
                "content": "להשכרה דירת 3 חד׳ בראשון לציון 5200 ש״ח משופצת",
                "expected": "match",
                "category": "Clear Match - Abbreviated Rooms"
            },
            {
                "content": "להשכרה 2.5 חדרים בתל אביב 5400 שח",
                "expected": "match",
                "category": "Clear Match - Minimum Rooms (2.5)"
            },
            
            # SHOULD NOT MATCH - Too Many Rooms (4+) - Expected: "no match"
            {
                "content": "להשכרה דירת 4 חדרים בתל אביב, מחיר 5500 שקל",
                "expected": "no match",
                "category": "Too Many Rooms - 4 Rooms"
            },
            {
                "content": "דירה להשכרה 5 חדרים רמת גן 5000 ש״ח",
                "expected": "no match",
                "category": "Too Many Rooms - 5 Rooms"
            },
            {
                "content": "להשכרה 4.5 חדרים פתח תקווה 4800 שקל",
                "expected": "no match",
                "category": "Too Many Rooms - 4.5 Rooms"
            },
            
            # SHOULD NOT MATCH - Wrong Purpose (למכירה) - Expected: "no match"
            {
                "content": "למכירה דירת 3 חדרים בתל אביב, מחיר 5500 שקל",
                "expected": "no match",
                "category": "Sale Not Rent"
            },
            {
                "content": "דירה למכירה 4 חדרים רמת גן 5000 ש״ח",
                "expected": "no match",
                "category": "Sale Not Rent"
            },
            
            # SHOULD NOT MATCH - Too Few Rooms - Expected: "no match"
            {
                "content": "להשכרה דירת חדר אחד בתל אביב, מחיר 4500 שקל",
                "expected": "no match",
                "category": "Too Few Rooms - 1 Room"
            },
            {
                "content": "דירה להשכרה חדר וחצי רמת גן 3000 ש״ח",
                "expected": "no match",
                "category": "Too Few Rooms - 1.5 Rooms"
            },
            {
                "content": "להשכרה 2 חדרים פתח תקווה 4800 שקל",
                "expected": "no match",
                "category": "Too Few Rooms - 2 Rooms"
            },
            {
                "content": "דירת 2.5 חדרים להשכרה ברחובות 5500 שח",
                "expected": "match",
                "category": "Clear Match - 2.5 Rooms"
            },
            
            # SHOULD NOT MATCH - Too Expensive - Expected: "no match"
            {
                "content": "להשכרה דירת 3 חדרים בתל אביב, מחיר 6500 שקל",
                "expected": "no match",
                "category": "Too Expensive - Over Budget"
            },
            {
                "content": "דירה להשכרה 3 חדרים רמת גן 7000 ש״ח",
                "expected": "no match",
                "category": "Too Expensive - Way Over Budget"
            },
            {
                "content": "להשכרה 3 חדרים פתח תקווה 5901 שקל",
                "expected": "no match",
                "category": "Too Expensive - Just Over Edge"
            },
            
            # SHOULD NOT MATCH - People Searching (not offering) - Expected: "no match"
            {
                "content": "מחפש דירה 3 חדרים בתל אביב עד 5500 שח",
                "expected": "no match",
                "category": "Person Searching - Male Singular"
            },
            {
                "content": "מחפשת דירת 3 חדרים ברמת גן למשפחה",
                "expected": "no match",
                "category": "Person Searching - Female Singular"
            },
            {
                "content": "מחפשים דירה 3 חדרים באזור המרכז",
                "expected": "no match",
                "category": "People Searching - Male Plural"
            },
            {
                "content": "מחפשות דירת 2.5-3 חדרים בפתח תקווה",
                "expected": "no match",
                "category": "People Searching - Female Plural"
            },
            
            # SHOULD NOT MATCH - Roommate/Partner Posts - Expected: "no match"
            {
                "content": "מחפש שותף לדירה 3 חדרים בתל אביב",
                "expected": "no match",
                "category": "Roommate Search - Male Singular"
            },
            {
                "content": "מחפשת שותפה לדירת 3 חדרים ברמת גן 5500 שח",
                "expected": "no match",
                "category": "Roommate Search - Female Singular"
            },
            {
                "content": "דירת 3 חדרים בפתח תקווה, מחפשים שותפים נוספים",
                "expected": "no match",
                "category": "Roommate Search - Male Plural"
            },
            {
                "content": "שותפות לדירה 3 חדרים בראשון לציון 5200 שח",
                "expected": "no match",
                "category": "Roommate Partnership - Female Plural"
            },
            {
                "content": "להשכרה דירת 3 חדרים עם שותפים קיימים",
                "expected": "no match",
                "category": "Rental with Existing Roommates"
            },
            {
                "content": "דירה 3 חד׳ ברמת גן דרושה שותפה נוספת",
                "expected": "no match",
                "category": "Looking for Additional Roommate"
            },
            
            # EDGE CASES - Ambiguous or Complex
            {
                "content": "דירה בתל אביב 3 חדרים 5500 שח",
                "expected": "match",
                "category": "Missing 'להשכרה' - Should Default to Match"
            },
            {
                "content": "להשכרה דירת 3 חדרים בתל אביב מחיר לא צוין",
                "expected": "match",
                "category": "No Price Information - Should Default to Match"
            },
            {
                "content": "להשכרה דירה בתל אביב 5500 שקל",
                "expected": "no match",
                "category": "No Room Information"
            },
            {
                "content": "דירת 3 חדרים בתל אביב מחיר 5500 + ארנונה",
                "expected": "match",
                "category": "Price Plus Additional Costs - Base Price OK"
            },
            
            # REAL-WORLD VARIATIONS
            {
                "content": "🏠 דירה להשכרה 3 חד׳ ברמת גן 💰 5400 שח",
                "expected": "match",
                "category": "With Emojis"
            },
            {
                "content": "להשכרה: דירת 3 חדרים ברחובות. מחיר: 5200 שקל. מיידי!",
                "expected": "match",
                "category": "Formatted with Punctuation"
            },
            {
                "content": "דירת 3 חדרים מעולה בפתח תקווה להשכרה 5800 שח משופצת קומה 2",
                "expected": "match",
                "category": "Additional Details"
            },
            {
                "content": "להשכרה מיידי דירת 3 חד׳ ק״ק בר״ג 5500 ש״ח",
                "expected": "match",
                "category": "Many Abbreviations"
            },
            
            # TRICKY CASES
            {
                "content": "דירה להשכרה 3 חדרים גדולים בנתניה 5900 שקל",
                "expected": "match",
                "category": "Room Size Qualifier"
            },
            {
                "content": "להשכרה דירת 3 חדרים + מרפסת גדולה 5400 שח",
                "expected": "match",
                "category": "Additional Spaces"
            },
            
            # NUMERIC VARIATIONS
            {
                "content": "להשכרה דירת שלושה חדרים בתל אביב 5500 שקל",
                "expected": "match",
                "category": "Written Numbers"
            },
            
            # NEW DEFAULT BEHAVIOR TESTS
            {
                "content": "דירת 3 חדרים מעולה בתל אביב",
                "expected": "match",
                "category": "No Price, No Purpose - Should Match (3 rooms)"
            },
            {
                "content": "דירה 4 חדרים משופצת ברמת גן",
                "expected": "no match",
                "category": "No Price, No Purpose - Should NOT Match (4 rooms - too many)"
            },
            {
                "content": "דירת 3.5 חדרים בפתח תקווה קומה שנייה",
                "expected": "match",
                "category": "No Price, No Purpose - Should Match (3.5 rooms)"
            },
            {
                "content": "דירה חדרים בתל אביב",
                "expected": "no match",
                "category": "No Room Count Specified"
            },
            {
                "content": "דירת 2 חדרים בנתניה",
                "expected": "no match",
                "category": "Too Few Rooms - No Price/Purpose"
            },
            
            # EXCLUDE WORDS PRE-FILTERING TESTS - These should be filtered before reaching LLM
            {
                "content": "מחפש דירת 3 חדרים בתל אביב עד 5500 שח",
                "expected": "no match",
                "category": "Pre-filtered - Search Word (מחפש)"
            },
            {
                "content": "דירת 4 חדרים למכירה ברמת גן 2000000 שח",
                "expected": "no match",
                "category": "Pre-filtered - Sale Word (למכירה)"
            },
            {
                "content": "להשכרה 3 חדרים מחפש שותף בפתח תקווה",
                "expected": "no match",
                "category": "Pre-filtered - Roommate Word (שותף)"
            },
            {
                "content": "דירת 3.5 חדרים דרושה להשכרה באזור המרכז",
                "expected": "no match",
                "category": "Pre-filtered - Wanted Word (דרושה)"
            },
            
            # RENTAL RELEVANCE TESTS - Posts not related to rental housing
            {
                "content": "מכירה דחופה! אייפון 14 במצב חדש 3000 שקל",
                "expected": "no match",
                "category": "Rental Relevance - Phone Sale (Not Housing)"
            },
            {
                "content": "מחפש עבודה בהיטק תל אביב, נסיון של 3 שנים",
                "expected": "no match",
                "category": "Rental Relevance - Job Search (Not Housing)"
            },
            {
                "content": "מכירה רכב טויוטה 2018, מחיר 85000 שקל",
                "expected": "no match",
                "category": "Rental Relevance - Car Sale (Not Housing)"
            },
            {
                "content": "שירות תיקון מחשבים ולפטופים במחיר זול",
                "expected": "no match",
                "category": "Rental Relevance - Computer Service (Not Housing)"
            },
            {
                "content": "אירוע יום הולדת לילדים - קלאון ואנימציה",
                "expected": "no match",
                "category": "Rental Relevance - Event Service (Not Housing)"
            },
            {
                "content": "מורה פרטי למתמטיקה - שיעורים בבית",
                "expected": "no match",
                "category": "Rental Relevance - Tutoring Service (Not Housing)"
            },
            {
                "content": "מכירה ספה ושולחן סלון במצב מצוין",
                "expected": "no match",
                "category": "Rental Relevance - Furniture Sale (Not Housing)"
            },
            
            # POSITIVE RENTAL RELEVANCE TESTS - Posts clearly about housing/rentals
            {
                "content": "דירה בת 3 חדרים בתל אביב להשכרה 5500 שח",
                "expected": "match",
                "category": "Rental Relevance - Clear Housing with דירה"
            },
            {
                "content": "להשכרה מקום מגורים נעים בצפון תל אביב 3 חדרים",
                "expected": "match",
                "category": "Rental Relevance - Clear Housing with מקום מגורים"
            },
            {
                "content": "בית פרטי 3 חדרים להשכרה באזור המרכז 5000 שח",
                "expected": "match",
                "category": "Rental Relevance - Clear Housing with בית"
            },
            {
                "content": "יחידת מגורים 3 חדרים במודיעין 5200 שקל",
                "expected": "match",
                "category": "Rental Relevance - Clear Housing with יחידת מגורים"
            },
            {
                "content": "דירות חדשות להשכרה באזור רמת גן 3 חד׳ 5400",
                "expected": "match",
                "category": "Rental Relevance - Clear Housing with דירות"
            },
            
            # EDGE CASES FOR RENTAL RELEVANCE - Posts that might be ambiguous
            {
                "content": "משרד 3 חדרים להשכרה בתל אביב 5500 שח",
                "expected": "no match",
                "category": "Rental Relevance - Office Space (Not Residential)"
            },
            {
                "content": "חנות למכירה 3 חדרים במרכז העיר 5000 שח",
                "expected": "no match",
                "category": "Rental Relevance - Commercial Space (Not Residential)"
            },
            {
                "content": "מחסן 3 חדרים להשכרה באזור התעשייה",
                "expected": "no match",
                "category": "Rental Relevance - Storage Space (Not Residential)"
            },
            
            # ADDITIONAL RENTAL RELEVANCE EDGE CASES
            {
                "content": "מכירת אופניים במצב חדש 1500 שקל בלבד",
                "expected": "no match",
                "category": "Rental Relevance - Bike Sale (Not Housing)"
            },
            {
                "content": "הרצאה על השקעות נדלן ביום רביעי הקרוב",
                "expected": "no match", 
                "category": "Rental Relevance - Real Estate Lecture (Not Rental)"
            },
            {
                "content": "גינה קהילתית מחפשת מתנדבים לעבודות תחזוקה",
                "expected": "no match",
                "category": "Rental Relevance - Community Garden (Not Housing)"
            },
            {
                "content": "קורס בישול איטלקי במטבח ביתי 3 מפגשים",
                "expected": "no match",
                "category": "Rental Relevance - Cooking Class (Not Housing)"
            },
            {
                "content": "מכירת ציוד ספורט - כדורגל, כדורעף, טניס",
                "expected": "no match",
                "category": "Rental Relevance - Sports Equipment (Not Housing)"
            },
            {
                "content": "זמן תפוס? בואו לעבוד במשרדנו - משכורת נאה",
                "expected": "no match", 
                "category": "Rental Relevance - Job Offer (Not Housing)"
            },
        ]
    
    def run_single_test(self, test_case):
        """Run a single test case and return results."""
        post = {"content": test_case["content"], "author": "Test User"}
        result = self.analyzer.analyze_post(post)
        
        is_correct = result == test_case["expected"]
        
        return {
            "content": test_case["content"][:60] + "...",
            "category": test_case["category"],
            "expected": test_case["expected"],
            "actual": result,
            "correct": is_correct
        }
    
    def run_rental_relevance_tests(self):
        """Run only the rental relevance tests to focus on the new feature."""
        print(f"🔍 Testing Rental Relevance Feature: {self.analyzer.model_name}")
        print("=" * 80)
        
        # Test connection first
        if not self.analyzer.test_ollama_connection():
            print("❌ Cannot connect to Ollama. Make sure it's running.")
            return
        
        print(f"✅ Connected to Ollama with model: {self.analyzer.model_name}")
        print()
        
        # Filter for only rental relevance tests
        relevance_tests = [
            test for test in self.test_cases 
            if "Rental Relevance" in test["category"]
        ]
        
        results = []
        correct_count = 0
        total_count = len(relevance_tests)
        
        print(f"Running {total_count} rental relevance tests...")
        print("-" * 80)
        
        for i, test_case in enumerate(relevance_tests, 1):
            print(f"Test {i:2d}/{total_count}: {test_case['category']}")
            
            result = self.run_single_test(test_case)
            results.append(result)
            
            if result["correct"]:
                correct_count += 1
                print(f"    ✅ {result['expected']} -> {result['actual']}")
            else:
                print(f"    ❌ Expected: {result['expected']}, Got: {result['actual']}")
                print(f"       Content: {result['content']}")
            
            print()
        
        # Results summary
        accuracy = (correct_count / total_count) * 100
        print("=" * 80)
        print("📊 RENTAL RELEVANCE RESULTS")
        print("=" * 80)
        print(f"Total Relevance Tests: {total_count}")
        print(f"Correct: {correct_count}")
        print(f"Wrong: {total_count - correct_count}")
        print(f"Relevance Accuracy: {accuracy:.1f}%")
        
        # Failed tests details
        failed_tests = [r for r in results if not r["correct"]]
        if failed_tests:
            print("\n❌ FAILED RENTAL RELEVANCE TESTS")
            print("-" * 80)
            for test in failed_tests:
                print(f"Category: {test['category']}")
                print(f"Content: {test['content']}")
                print(f"Expected: {test['expected']} | Got: {test['actual']}")
                print()
        else:
            print("\n🎉 All rental relevance tests passed!")
        
        return accuracy, results

    def run_all_tests(self):
        """Run all test cases and provide detailed results."""
        print(f"🧪 Testing Model Accuracy: {self.analyzer.model_name}")
        print("=" * 80)
        
        # Test connection first
        if not self.analyzer.test_ollama_connection():
            print("❌ Cannot connect to Ollama. Make sure it's running.")
            return
        
        print(f"✅ Connected to Ollama with model: {self.analyzer.model_name}")
        print()
        
        results = []
        correct_count = 0
        total_count = len(self.test_cases)
        
        # Group results by category
        by_category = {}
        
        print("Running tests...")
        print("-" * 80)
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"Test {i:2d}/{total_count}: {test_case['category']}")
            
            result = self.run_single_test(test_case)
            results.append(result)
            
            # Track by category
            category = result["category"]
            if category not in by_category:
                by_category[category] = {"correct": 0, "total": 0}
            
            by_category[category]["total"] += 1
            if result["correct"]:
                by_category[category]["correct"] += 1
                correct_count += 1
                print(f"    ✅ {result['expected']} -> {result['actual']}")
            else:
                print(f"    ❌ Expected: {result['expected']}, Got: {result['actual']}")
                print(f"       Content: {result['content']}")
            
            print()
        
        # Overall Results
        accuracy = (correct_count / total_count) * 100
        print("=" * 80)
        print("📊 OVERALL RESULTS")
        print("=" * 80)
        print(f"Total Tests: {total_count}")
        print(f"Correct: {correct_count}")
        print(f"Wrong: {total_count - correct_count}")
        print(f"Accuracy: {accuracy:.1f}%")
        print()
        
        # Category Breakdown
        print("📋 CATEGORY BREAKDOWN")
        print("-" * 80)
        for category, stats in by_category.items():
            cat_accuracy = (stats["correct"] / stats["total"]) * 100
            print(f"{category:35} {stats['correct']:2d}/{stats['total']:2d} ({cat_accuracy:5.1f}%)")
        
        print()
        
        # Failed Tests Details
        failed_tests = [r for r in results if not r["correct"]]
        if failed_tests:
            print("❌ FAILED TESTS DETAILS")
            print("-" * 80)
            for test in failed_tests:
                print(f"Category: {test['category']}")
                print(f"Content: {test['content']}")
                print(f"Expected: {test['expected']} | Got: {test['actual']}")
                print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 80)
        if accuracy >= 90:
            print("🎉 Excellent performance! Model is highly reliable.")
        elif accuracy >= 80:
            print("👍 Good performance! Model is generally reliable.")
        elif accuracy >= 70:
            print("⚠️  Moderate performance. Consider fine-tuning prompts.")
        else:
            print("🚨 Poor performance. Model may need significant adjustments.")
        
        # Save results to files
        self._save_results_to_files(accuracy, results, by_category, failed_tests)
        
        return accuracy, results

    def _save_results_to_files(self, accuracy, results, by_category, failed_tests):
        """Save test results to JSON and text files in test_outputs/model_accuracy folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = self.analyzer.model_name.replace(":", "_").replace("/", "_")
        
        # Create output directory structure: test_outputs/model_accuracy/
        base_output_dir = os.path.join(os.path.dirname(__file__), "..", "test_outputs")
        output_dir = os.path.join(base_output_dir, "model_accuracy")
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare data for JSON
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "model_name": self.analyzer.model_name,
            "total_tests": len(self.test_cases),
            "correct_tests": sum(1 for r in results if r["correct"]),
            "accuracy_percentage": accuracy,
            "category_breakdown": {
                cat: {
                    "correct": stats["correct"],
                    "total": stats["total"],
                    "accuracy": (stats["correct"] / stats["total"]) * 100
                }
                for cat, stats in by_category.items()
            },
            "detailed_results": results,
            "failed_tests": failed_tests
        }
        
        # Save JSON file
        json_filename = f"accuracy_test_{model_name}_{timestamp}.json"
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # Save summary text file
        txt_filename = f"accuracy_summary_{model_name}_{timestamp}.txt"
        txt_path = os.path.join(output_dir, txt_filename)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Model Accuracy Test Results\n")
            f.write(f"==========================\n\n")
            f.write(f"Model: {self.analyzer.model_name}\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {len(self.test_cases)}\n")
            f.write(f"Correct: {sum(1 for r in results if r['correct'])}\n")
            f.write(f"Wrong: {len(self.test_cases) - sum(1 for r in results if r['correct'])}\n")
            f.write(f"ACCURACY: {accuracy:.1f}%\n\n")
            
            f.write("Category Breakdown:\n")
            f.write("-" * 50 + "\n")
            for category, stats in by_category.items():
                cat_accuracy = (stats["correct"] / stats["total"]) * 100
                f.write(f"{category:35} {stats['correct']:2d}/{stats['total']:2d} ({cat_accuracy:5.1f}%)\n")
            
            if failed_tests:
                f.write(f"\nFailed Tests ({len(failed_tests)}):\n")
                f.write("-" * 50 + "\n")
                for i, test in enumerate(failed_tests, 1):
                    f.write(f"{i}. {test['category']}\n")
                    f.write(f"   Content: {test['content']}\n")
                    f.write(f"   Expected: {test['expected']} | Got: {test['actual']}\n\n")
        
        print(f"\n📄 Results saved to:")
        print(f"   JSON: {json_path}")
        print(f"   Summary: {txt_path}")
        print(f"\n🎯 FINAL ACCURACY: {accuracy:.1f}%")


def main():
    """Main function to run the accuracy test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test model accuracy for apartment analysis")
    parser.add_argument(
        "--rental-relevance-only", 
        action="store_true",
        help="Run only rental relevance tests"
    )
    args = parser.parse_args()
    
    tester = ModelAccuracyTester()
    
    if args.rental_relevance_only:
        accuracy, results = tester.run_rental_relevance_tests()
        return accuracy >= 90  # Higher threshold for relevance tests
    else:
        accuracy, results = tester.run_all_tests()
        return accuracy >= 80  # Return success if accuracy is 80% or higher


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

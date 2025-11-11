#!/usr/bin/env python3
"""
Quick integration test script to verify comprehensive audit works.
"""
import asyncio
import json

from tinyseoai.audit.engine_v2 import comprehensive_audit


async def main():
    """Run a quick comprehensive audit test."""
    print("=" * 60)
    print("TinySEO AI - Comprehensive Audit Integration Test")
    print("=" * 60)

    url = "https://example.com"
    max_pages = 3

    print(f"\n🔍 Testing comprehensive audit on: {url}")
    print(f"📄 Max pages: {max_pages}")
    print(f"⚙️  Full checks enabled\n")

    try:
        result = await comprehensive_audit(
            url, max_pages=max_pages, enable_all_checks=True
        )

        print("\n" + "=" * 60)
        print("✅ AUDIT COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print(f"\n📊 RESULTS:")
        print(f"  Site: {result.site}")
        print(f"  Pages Scanned: {result.pages_scanned}")
        print(f"  Total Issues: {len(result.issues)}")

        if "health_score" in result.meta:
            score = result.meta["health_score"]
            grade = result.meta["health_grade"]
            print(f"\n  Health Score: {score}/100 (Grade: {grade})")

        if "robots_txt_exists" in result.meta:
            print(f"  Robots.txt: {'✓ Found' if result.meta['robots_txt_exists'] else '✗ Missing'}")

        if "sitemaps_found" in result.meta:
            print(f"  Sitemaps Found: {result.meta['sitemaps_found']}")

        # Show issue breakdown by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
        for issue in result.issues:
            severity_counts[issue.severity] += 1

        print(f"\n📈 ISSUES BY SEVERITY:")
        for severity, count in severity_counts.items():
            if count > 0:
                print(f"  {severity.capitalize():8} : {count}")

        # Show category breakdown
        if "category_scores" in result.meta and result.meta["category_scores"]:
            print(f"\n📂 ISSUES BY CATEGORY:")
            for category, data in result.meta["category_scores"].items():
                print(f"  {category.capitalize():12} : {data['count']} issues (avg impact: {data['avg_impact']:.1f})")

        # Show top recommendations
        if "top_recommendations" in result.meta and result.meta["top_recommendations"]:
            print(f"\n🎯 TOP 5 PRIORITY FIXES:")
            for i, rec in enumerate(result.meta["top_recommendations"][:5], 1):
                issue_type = rec["issue_type"].replace("_", " ").title()
                print(f"  {i}. {issue_type:30} (Priority: {rec['priority']:.1f}, Impact: {rec['impact']:.1f}, Effort: {rec['effort']:.1f})")

        # Show sample issues
        if result.issues:
            print(f"\n🔍 SAMPLE ISSUES (first 5):")
            for issue in result.issues[:5]:
                detail = f" - {issue.detail[:50]}..." if issue.detail else ""
                print(f"  [{issue.severity.upper()}] {issue.type}: {issue.url[:50]}...{detail}")

        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

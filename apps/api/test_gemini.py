#!/usr/bin/env python3
"""
Test script to validate Gemini API integration
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Import our summarization module
from summarization import SummarizationAgent


async def test_gemini_api():
    """Test real Gemini API call with sample articles"""
    
    print("🔍 Testing Gemini API Integration...")
    print(f"📋 API Key configured: {'✅' if os.getenv('GEMINI_API_KEY') else '❌'}")
    print(f"🚀 Feature flag enabled: {'✅' if os.getenv('ENABLE_REAL_SUMMARIZATION', '').lower() == 'true' else '❌'}")
    
    # Create test articles
    test_articles = [
        {
            "title": "Climate Change Accelerating Faster Than Expected",
            "url": "http://example.com/climate1",
            "description": "Recent studies show global warming is occurring at a pace faster than previously predicted, with significant implications for weather patterns and sea level rise."
        },
        {
            "title": "Renewable Energy Costs Drop to Record Lows",
            "url": "http://example.com/energy1", 
            "description": "Solar and wind energy costs have plummeted to historic lows, making clean energy more competitive than fossil fuels in many markets."
        }
    ]
    
    # Initialize the summarization agent
    agent = SummarizationAgent()
    
    print(f"\n🤖 Agent configuration:")
    print(f"   - LLM enabled: {agent._is_enabled}")
    print(f"   - API configured: {agent.config.is_configured()}")
    print(f"   - Model: {agent.config.model}")
    
    try:
        print(f"\n📝 Testing debate format summarization...")
        print(f"📊 Articles: {len(test_articles)}")
        
        # Test debate format
        result = await agent.summarize_articles(test_articles, "debate")
        
        print(f"\n✅ SUCCESS! Debate format summary generated:")
        print(f"📌 Format: {result['format']}")
        print(f"📄 Statement: {result['content']['statement']}")
        print(f"✅ For arguments: {len(result['content']['for'])}")
        print(f"❌ Against arguments: {len(result['content']['against'])}")
        print(f"📚 Sources: {len(result['sources'])}")
        
        # Display first few arguments
        print(f"\n📋 Sample arguments:")
        for i, arg in enumerate(result['content']['for'][:2], 1):
            print(f"   ✅ For {i}: {arg}")
        for i, arg in enumerate(result['content']['against'][:2], 1):
            print(f"   ❌ Against {i}: {arg}")
        
        print(f"\n🔄 Testing venn diagram format...")
        
        # Test venn diagram format
        result_venn = await agent.summarize_articles(test_articles, "venn_diagram")
        
        print(f"\n✅ SUCCESS! Venn diagram format summary generated:")
        print(f"📌 Format: {result_venn['format']}")
        print(f"🔵 Topic A: {result_venn['content']['topic_a']}")
        print(f"🔴 Topic B: {result_venn['content']['topic_b']}")
        print(f"🔵 Unique A: {len(result_venn['content']['unique_a'])}")
        print(f"🔴 Unique B: {len(result_venn['content']['unique_b'])}")
        print(f"🟢 Common: {len(result_venn['content']['common'])}")
        
        print(f"\n🎉 GEMINI API TEST PASSED!")
        print(f"✨ Real LLM summarization is working correctly!")
        
    except Exception as e:
        print(f"\n❌ ERROR during API test:")
        print(f"🚨 Error type: {type(e).__name__}")
        print(f"📝 Error message: {str(e)}")
        print(f"\n🔧 Troubleshooting tips:")
        print(f"   - Verify your API key is correct")
        print(f"   - Check your internet connection")
        print(f"   - Ensure you have Gemini API quota available")
        return False
    
    finally:
        # Clean up resources
        await agent.cleanup()
    
    return True


if __name__ == "__main__":
    print("🚀 Starting Gemini API Test...")
    
    try:
        success = asyncio.run(test_gemini_api())
        if success:
            print(f"\n🎊 All tests passed! Gemini integration is ready.")
            sys.exit(0)
        else:
            print(f"\n⚠️  Tests failed. Please check configuration.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
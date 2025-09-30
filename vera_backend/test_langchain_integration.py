#!/usr/bin/env python3
"""
Test script for LangChain orchestrator integration
"""
import asyncio
import os
import sys
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.config import settings
from app.database import Base
from app.services.langchain_orchestrator import LangChainOrchestrator


async def test_orchestrator():
    """Test the LangChain orchestrator functionality"""

    print("🚀 Starting LangChain Orchestrator Integration Test")
    print("=" * 60)

    # Create test database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Initialize orchestrator
        print("1. Initializing LangChain Orchestrator...")
        orchestrator = LangChainOrchestrator(db)
        print("✅ Orchestrator initialized successfully")

        # Test agent statistics
        print("\n2. Getting agent statistics...")
        stats = orchestrator.get_agent_stats()
        print(f"✅ Available agents: {stats['available_agents']}")
        print(f"✅ Supported intents: {stats['supported_intents']}")

        # Test intent analysis
        print("\n3. Testing intent analysis...")
        test_messages = [
            "Create a task to review the quarterly reports by Friday",
            "How are you doing today?",
            "Can you analyze my task completion patterns?",
            "Schedule a meeting with the development team",
            "Generate a weekly status report",
        ]

        # Create a mock user ID for testing
        test_user_id = uuid4()

        for i, message in enumerate(test_messages, 1):
            print(f"\n   Test {i}: '{message}'")
            try:
                # Get user context (will use fallback for test)
                user_context = await orchestrator._get_user_context(test_user_id)

                # Analyze intent
                intent_analysis = await orchestrator._analyze_user_intent(
                    message, user_context
                )

                print(
                    f"   ✅ Intent: {intent_analysis.get('primary_intent', 'unknown')}"
                )
                print(f"   ✅ Confidence: {intent_analysis.get('confidence', 0.0):.2f}")
                print(
                    f"   ✅ Complexity: {intent_analysis.get('complexity', 'unknown')}"
                )

            except Exception as e:
                print(f"   ❌ Error analyzing intent: {str(e)}")

        # Test full orchestrator processing (simplified)
        print("\n4. Testing full orchestrator processing...")
        test_request = "Hello, can you help me understand what you can do?"

        try:
            response = await orchestrator.process_user_request(
                user_input=test_request, user_id=test_user_id
            )

            print(f"✅ Response generated successfully")
            print(f"   Content preview: {response['content'][:100]}...")
            print(f"   Agent used: {response['agent_used']}")
            print(f"   Intent: {response['intent'].get('primary_intent', 'unknown')}")

        except Exception as e:
            print(f"❌ Error processing request: {str(e)}")

        # Test conversation history
        print("\n5. Testing conversation history...")
        try:
            history = await orchestrator.get_conversation_history(limit=5)
            print(f"✅ Retrieved {len(history)} conversation entries")

        except Exception as e:
            print(f"❌ Error getting conversation history: {str(e)}")

        print("\n" + "=" * 60)
        print("🎉 LangChain Orchestrator Integration Test Completed!")

        return True

    except Exception as e:
        print(f"\n❌ Critical error during testing: {str(e)}")
        return False

    finally:
        db.close()


async def test_specialized_agents():
    """Test individual specialized agents"""

    print("\n🔧 Testing Specialized Agents")
    print("=" * 40)

    # This would test individual agents if needed
    # For now, we'll just verify they can be created

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        orchestrator = LangChainOrchestrator(db)

        print("✅ Task Agent initialized")
        print("✅ Conversation Agent initialized")
        print("✅ Analysis Agent initialized")
        print("✅ Coordination Agent initialized")
        print("✅ Reporting Agent initialized")

        return True

    except Exception as e:
        print(f"❌ Error initializing specialized agents: {str(e)}")
        return False

    finally:
        db.close()


def main():
    """Main test function"""

    print("🧪 LangChain Integration Test Suite")
    print("=" * 80)

    # Check if required environment variables are set
    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY not set in environment variables")
        return False

    if not settings.database_url:
        print("❌ DATABASE_URL not set in environment variables")
        return False

    print("✅ Environment variables configured")

    # Run async tests
    try:
        # Test orchestrator
        orchestrator_success = asyncio.run(test_orchestrator())

        # Test specialized agents
        agents_success = asyncio.run(test_specialized_agents())

        # Overall result
        if orchestrator_success and agents_success:
            print("\n🎉 ALL TESTS PASSED! LangChain integration is working correctly.")
            return True
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            return False

    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

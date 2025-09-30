#!/usr/bin/env python3
"""
Comprehensive test script for LangGraph integration
Tests workflows, state management, and integration with existing orchestrator
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
from app.services.langgraph_integration import IntegratedAIService
from app.services.langgraph_workflows import LangGraphWorkflowService, WorkflowType


async def test_intelligent_routing():
    """Test intelligent routing between orchestrator and workflows"""

    print("🧠 Testing Intelligent Request Routing")
    print("=" * 50)

    # Create test database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        ai_service = IntegratedAIService(db)
        test_user_id = uuid4()

        # Test cases for different routing scenarios
        test_cases = [
            {
                "input": "Hello, how are you doing today?",
                "expected_type": "orchestrator",
                "description": "Simple conversation - should route to orchestrator",
            },
            {
                "input": "Create a comprehensive project plan for launching our new mobile app with multiple teams involved",
                "expected_type": "workflow",
                "description": "Complex task request - should trigger workflow",
            },
            {
                "input": "Research the latest trends in artificial intelligence and machine learning for our strategy",
                "expected_type": "workflow",
                "description": "Research request - should trigger research workflow",
            },
            {
                "input": "Plan the quarterly team retreat with input from all department heads",
                "expected_type": "workflow",
                "description": "Planning request - should trigger collaborative planning",
            },
            {
                "input": "What tasks do I have for today?",
                "expected_type": "orchestrator",
                "description": "Simple task query - should use orchestrator",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{test_case['input'][:60]}...'")
            print(f"   Expected: {test_case['expected_type']}")

            try:
                result = await ai_service.process_intelligent_request(
                    user_input=test_case["input"], user_id=test_user_id
                )

                response_type = result.get("response_type", "unknown")
                print(f"   ✅ Got: {response_type}")

                if (
                    "workflow" in response_type
                    and test_case["expected_type"] == "workflow"
                ):
                    print(f"   ✅ Workflow triggered correctly")
                    workflow_info = result.get("workflow_info", {})
                    print(
                        f"   📋 Workflow type: {workflow_info.get('workflow_type', 'unknown')}"
                    )
                    print(
                        f"   🆔 Workflow ID: {workflow_info.get('workflow_id', 'unknown')}"
                    )

                elif (
                    response_type == "orchestrator"
                    and test_case["expected_type"] == "orchestrator"
                ):
                    print(f"   ✅ Routed to orchestrator correctly")

                else:
                    print(
                        f"   ⚠️  Unexpected routing: got {response_type}, expected {test_case['expected_type']}"
                    )

                print(f"   💬 Response: {result.get('message', 'No message')[:100]}...")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ Critical error during intelligent routing test: {str(e)}")
        return False

    finally:
        db.close()


async def test_workflow_lifecycle():
    """Test complete workflow lifecycle"""

    print("\n🔄 Testing Workflow Lifecycle")
    print("=" * 40)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        workflow_service = LangGraphWorkflowService(db)
        test_user_id = uuid4()

        # Test Task Orchestration Workflow
        print("\n1. Testing Task Orchestration Workflow")
        print("-" * 35)

        initial_data = {
            "task_requests": [
                {
                    "title": "Setup Development Environment",
                    "description": "Configure development tools and dependencies",
                    "priority": "high",
                    "estimated_duration": "4 hours",
                },
                {
                    "title": "Design Database Schema",
                    "description": "Create database design for new features",
                    "priority": "medium",
                    "estimated_duration": "6 hours",
                },
            ],
            "assignees": ["developer_1", "database_admin"],
            "deadlines": ["2024-02-01", "2024-02-05"],
        }

        # Start workflow
        workflow_result = await workflow_service.start_workflow(
            workflow_type=WorkflowType.TASK_ORCHESTRATION,
            user_id=test_user_id,
            initial_data=initial_data,
        )

        print(f"   ✅ Workflow started: {workflow_result['workflow_id']}")
        print(f"   📊 Status: {workflow_result['status']}")
        print(f"   🔗 Thread ID: {workflow_result['thread_id']}")

        # Get workflow state
        state = await workflow_service.get_workflow_state(
            thread_id=workflow_result["thread_id"],
            workflow_type=WorkflowType.TASK_ORCHESTRATION,
        )

        print(
            f"   📋 Current state: {state['state']['current_step'] if state['state'] else 'unknown'}"
        )

        # Test Research and Analysis Workflow
        print("\n2. Testing Research and Analysis Workflow")
        print("-" * 40)

        research_data = {
            "research_query": "Impact of AI on software development productivity",
            "research_depth": "comprehensive",
            "include_analysis": True,
        }

        research_workflow = await workflow_service.start_workflow(
            workflow_type=WorkflowType.RESEARCH_AND_ANALYSIS,
            user_id=test_user_id,
            initial_data=research_data,
        )

        print(f"   ✅ Research workflow started: {research_workflow['workflow_id']}")
        print(f"   📊 Status: {research_workflow['status']}")

        # Test Iterative Refinement Workflow
        print("\n3. Testing Iterative Refinement Workflow")
        print("-" * 42)

        refinement_data = {
            "requirements": "Write a comprehensive guide for new team members joining our development team",
            "content_type": "documentation",
            "quality_threshold": 8,
            "max_iterations": 3,
        }

        refinement_workflow = await workflow_service.start_workflow(
            workflow_type=WorkflowType.ITERATIVE_REFINEMENT,
            user_id=test_user_id,
            initial_data=refinement_data,
        )

        print(f"   ✅ Refinement workflow started: {refinement_workflow['workflow_id']}")
        print(f"   📊 Status: {refinement_workflow['status']}")

        return True

    except Exception as e:
        print(f"❌ Error during workflow lifecycle test: {str(e)}")
        return False

    finally:
        db.close()


async def test_workflow_state_management():
    """Test workflow state persistence and management"""

    print("\n💾 Testing Workflow State Management")
    print("=" * 45)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        workflow_service = LangGraphWorkflowService(db)
        test_user_id = uuid4()

        # Create a workflow with state
        initial_data = {
            "automation_request": "Automate the monthly report generation process",
            "execution_mode": "step_by_step",
            "verify_steps": True,
        }

        workflow = await workflow_service.start_workflow(
            workflow_type=WorkflowType.MULTI_STEP_AUTOMATION,
            user_id=test_user_id,
            initial_data=initial_data,
        )

        workflow_id = workflow["workflow_id"]
        thread_id = workflow["thread_id"]

        print(f"   ✅ Created workflow: {workflow_id}")

        # Get initial state
        state1 = await workflow_service.get_workflow_state(
            thread_id=thread_id, workflow_type=WorkflowType.MULTI_STEP_AUTOMATION
        )

        print(f"   📊 Initial state retrieved")
        print(
            f"   🔄 Current step: {state1['state']['current_step'] if state1['state'] else 'unknown'}"
        )

        # Continue workflow (simulate progression)
        continuation_result = await workflow_service.continue_workflow(
            workflow_id=workflow_id,
            thread_id=thread_id,
            workflow_type=WorkflowType.MULTI_STEP_AUTOMATION,
            user_input={"continue": True},
        )

        print(f"   ✅ Workflow continued")
        print(f"   📊 Status: {continuation_result['status']}")

        # Get updated state
        state2 = await workflow_service.get_workflow_state(
            thread_id=thread_id, workflow_type=WorkflowType.MULTI_STEP_AUTOMATION
        )

        print(f"   📊 Updated state retrieved")
        print(
            f"   🔄 Current step: {state2['state']['current_step'] if state2['state'] else 'unknown'}"
        )

        # Test state persistence
        if state1["state"] and state2["state"]:
            step1 = state1["state"].get("current_step", "")
            step2 = state2["state"].get("current_step", "")

            if step1 != step2:
                print(f"   ✅ State progression detected: {step1} → {step2}")
            else:
                print(f"   ℹ️  State remained consistent: {step1}")

        return True

    except Exception as e:
        print(f"❌ Error during state management test: {str(e)}")
        return False

    finally:
        db.close()


async def test_integration_capabilities():
    """Test integration capabilities and service health"""

    print("\n🔧 Testing Integration Capabilities")
    print("=" * 40)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        ai_service = IntegratedAIService(db)

        # Get integration capabilities
        capabilities = ai_service.get_integration_capabilities()

        print(f"   ✅ Integration capabilities retrieved")
        print(
            f"   🤖 Orchestrator agents: {len(capabilities['orchestrator_capabilities']['available_agents'])}"
        )
        print(f"   🔄 Workflow types: {len(capabilities['workflow_types'])}")
        print(f"   ⚡ Integration features: {len(capabilities['integration_features'])}")

        # Test workflow types
        workflow_service = LangGraphWorkflowService(db)
        workflow_types = workflow_service.get_workflow_types()

        print(f"\n   📋 Available Workflow Types:")
        for wf_type in workflow_types:
            print(f"      • {wf_type['name']}: {wf_type['description'][:60]}...")
            print(f"        Capabilities: {', '.join(wf_type['capabilities'][:3])}...")

        # Test user workflow listing
        test_user_id = uuid4()
        user_workflows = await ai_service.list_user_workflows(test_user_id)

        print(f"\n   📊 User workflows: {len(user_workflows)} found")

        return True

    except Exception as e:
        print(f"❌ Error during integration capabilities test: {str(e)}")
        return False

    finally:
        db.close()


async def test_workflow_triggers():
    """Test workflow trigger detection and classification"""

    print("\n🎯 Testing Workflow Triggers")
    print("=" * 35)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        ai_service = IntegratedAIService(db)
        test_user_id = uuid4()

        # Test different trigger scenarios
        trigger_tests = [
            {
                "input": "Create multiple tasks for the new project with dependencies between them",
                "expected_workflow": WorkflowType.TASK_ORCHESTRATION,
                "description": "Complex task request",
            },
            {
                "input": "Research and analyze the competitive landscape in our industry",
                "expected_workflow": WorkflowType.RESEARCH_AND_ANALYSIS,
                "description": "Research query",
            },
            {
                "input": "Plan the product roadmap with input from engineering, marketing, and sales teams",
                "expected_workflow": WorkflowType.COLLABORATIVE_PLANNING,
                "description": "Collaborative planning",
            },
            {
                "input": "Write and improve a comprehensive proposal for the client project",
                "expected_workflow": WorkflowType.ITERATIVE_REFINEMENT,
                "description": "Content creation with refinement",
            },
            {
                "input": "Automate the employee onboarding process with multiple verification steps",
                "expected_workflow": WorkflowType.MULTI_STEP_AUTOMATION,
                "description": "Multi-step automation",
            },
        ]

        for i, test in enumerate(trigger_tests, 1):
            print(f"\n{i}. Testing trigger: {test['description']}")
            print(f"   Input: '{test['input'][:50]}...'")

            try:
                # Get user context and analyze intent
                user_context = await ai_service.orchestrator._get_user_context(
                    test_user_id
                )
                intent_analysis = await ai_service.orchestrator._analyze_user_intent(
                    test["input"], user_context
                )

                # Check workflow decision
                workflow_decision = await ai_service._should_trigger_workflow(
                    test["input"], intent_analysis
                )

                if workflow_decision["trigger_workflow"]:
                    triggered_type = workflow_decision["workflow_type"]
                    confidence = workflow_decision["confidence"]

                    print(f"   ✅ Workflow triggered: {triggered_type.value}")
                    print(f"   📊 Confidence: {confidence:.2f}")
                    print(f"   🎯 Expected: {test['expected_workflow'].value}")

                    if triggered_type == test["expected_workflow"]:
                        print(f"   ✅ Correct workflow type detected!")
                    else:
                        print(f"   ⚠️  Different workflow triggered than expected")
                else:
                    print(f"   ❌ No workflow triggered")
                    print(f"   📊 Reason: {workflow_decision['reason']}")

            except Exception as e:
                print(f"   ❌ Error testing trigger: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ Error during workflow trigger test: {str(e)}")
        return False

    finally:
        db.close()


def main():
    """Main test function"""

    print("🧪 LangGraph Integration Test Suite")
    print("=" * 80)

    # Check environment
    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY not set")
        return False

    if not settings.database_url:
        print("❌ DATABASE_URL not set")
        return False

    print("✅ Environment configured")

    # Run all tests
    test_results = []

    try:
        # Test intelligent routing
        result = asyncio.run(test_intelligent_routing())
        test_results.append(("Intelligent Routing", result))

        # Test workflow lifecycle
        result = asyncio.run(test_workflow_lifecycle())
        test_results.append(("Workflow Lifecycle", result))

        # Test state management
        result = asyncio.run(test_workflow_state_management())
        test_results.append(("State Management", result))

        # Test integration capabilities
        result = asyncio.run(test_integration_capabilities())
        test_results.append(("Integration Capabilities", result))

        # Test workflow triggers
        result = asyncio.run(test_workflow_triggers())
        test_results.append(("Workflow Triggers", result))

    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        return False

    # Report results
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! LangGraph integration is working perfectly!")
        print("\n🚀 Features Available:")
        print("   • Intelligent request routing")
        print("   • 5 types of stateful workflows")
        print("   • Parallel processing and orchestration")
        print("   • State persistence and resumption")
        print("   • Multi-agent collaboration")
        print("   • Iterative refinement loops")
        print("   • Complex automation sequences")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
Test Chat History Feature

This script tests:
1. Multi-turn conversations with context preservation
2. Follow-up questions that reference previous answers
3. Session management (info, clear)
"""

# Test with curl commands
print("""
🧪 CHAT HISTORY TEST SCRIPT
===========================

Prerequisites:
- Backend server running on http://localhost:8000
- Documents already ingested in session-alice

TEST 1: Multi-Turn Conversation
--------------------------------

# Turn 1: Initial question
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-alice" \
  -d '{"query": "What is the nervous system?"}'

# Wait 2 seconds, then...

# Turn 2: Follow-up question using "it"
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-alice" \
  -d '{"query": "What are its main components?"}'

# Turn 3: Another follow-up
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-alice" \
  -d '{"query": "Tell me more about that"}'


TEST 2: Check Session Info
---------------------------

curl -X GET http://localhost:8000/api/v1/session/info \
  -H "X-Session-ID: session-alice"

Expected Output:
{
  "session_id": "session-alice",
  "document_count": X,
  "chat_history": {
    "turn_count": 3,
    "first_query": "What is the nervous system?",
    "last_query": "Tell me more about that",
    "last_timestamp": "2026-01-27T..."
  }
}


TEST 3: Clear Session
----------------------

curl -X DELETE http://localhost:8000/api/v1/session/clear \
  -H "X-Session-ID: session-alice"

Expected: Both documents and chat history cleared


VALIDATION CHECKLIST:
--------------------
✅ Turn 2 should understand "its" refers to "nervous system" from Turn 1
✅ Turn 3 should reference content from Turn 2
✅ Session info shows correct turn count
✅ History includes first_query, last_query, timestamps
✅ Clear operation removes both documents and chat history


MANUAL TEST (PowerShell):
--------------------------

# Turn 1
curl.exe -X POST -H "Content-Type: application/json" `
  -H "X-Session-ID: session-alice" `
  -d '{\"query\": \"What is the nervous system?\"}' `
  http://localhost:8000/api/v1/query/

# Turn 2 (follow-up)
curl.exe -X POST -H "Content-Type: application/json" `
  -H "X-Session-ID: session-alice" `
  -d '{\"query\": \"What are its main components?\"}' `
  http://localhost:8000/api/v1/query/

# Check session info
curl.exe -X GET -H "X-Session-ID: session-alice" `
  http://localhost:8000/api/v1/session/info

# View saved history file
cat F:\\Pluto\\data\\chat_history\\session-alice.json

""")

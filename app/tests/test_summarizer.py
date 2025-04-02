from app import create_app
from app.services.summarization_service import SummarizationService
from app.extensions import get_db

# Use a real session ID with at least 10 short-term memories
TEST_SESSION_ID = "your-session-id"

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db = get_db()
        if db is None:
            print("❌ Database connection failed.")
            exit()

        print("🔍 Triggering summarization for session:", TEST_SESSION_ID)

        summarizer = SummarizationService()
        result = summarizer.summarize_memories(TEST_SESSION_ID)

        if result.get("success"):
            print("✅ Summary Created:")
            print(result["summary"])
        else:
            print("❌ Summarization failed:")
            print(result)

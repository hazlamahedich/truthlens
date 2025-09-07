# TruthLens Project Structure

## Project Overview
TruthLens is a news analysis application with AI-powered summarization capabilities. The project uses a monorepo structure with frontend and backend applications.

## Tech Stack
- **Frontend**: React/Next.js (web app)
- **Backend**: Python FastAPI with serverless functions
- **Deployment**: Vercel for both frontend and backend
- **LLM Integration**: Google Gemini API
- **Testing**: Pytest for backend, comprehensive unit and integration tests

## Architecture Pattern
- **Agent-based modules**: Independent, stateless serverless functions
- **Separation of concerns**: Retrieval, Verification, Summarization agents
- **Feature flags**: Environment variable-based feature toggling
- **Error handling**: Comprehensive error handling with graceful fallbacks

## Key Components
- **Retrieval Agent**: NewsAPI.org integration for article fetching
- **Summarization Agent**: LLM integration with feature flags and mock fallbacks
- **Verification Agent**: Currently mocked (blockchain verification planned)
- **Orchestrator**: Coordinates all agents for complete query processing

## Code Quality Standards
- Type hints throughout Python code
- Comprehensive docstrings
- Extensive test coverage (31+ tests for Story 1.6)
- Proper async/await patterns
- Resource cleanup and session management

## Testing Strategy
- Unit tests for individual components
- Integration tests for end-to-end flows  
- Performance benchmarks validation
- Error scenario testing
- Data model compliance validation
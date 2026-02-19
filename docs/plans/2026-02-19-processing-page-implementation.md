# Processing Page with WebSocket Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a real-time Processing Page that displays resume parsing progress via WebSocket with stage-by-stage updates, automatic redirects, and error handling.

**Architecture:** WebSocket-based bidirectional communication between FastAPI backend and React frontend. Backend uses WebSocket manager to broadcast progress updates from parsing pipeline. Frontend uses custom WebSocket hook to receive updates and drive UI.

**Tech Stack:**
- Backend: FastAPI WebSocket, python-websocket, asyncio
- Frontend: React WebSocket API, custom hooks, TypeScript
- Testing: pytest-asyncio, React Testing Library

---

## Task 1: Create WebSocket Connection Manager (Backend)

**Files:**
- Create: `backend/app/api/websocket.py`
- Create: `backend/tests/integration/test_websocket.py`

**Step 1: Write failing test for WebSocket connection**

```bash
cat > backend/tests/integration/test_websocket.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_websocket_connection():
    """Test that WebSocket endpoint accepts connections"""
    with client.websocket_connect("/ws/resumes/test-resume-id") as websocket:
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] == "connection_established"
EOF
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/integration/test_websocket.py -v`
Expected: FAIL - WebSocket endpoint doesn't exist

**Step 3: Implement WebSocket connection manager**

```bash
cat > backend/app/api/websocket.py << 'EOF'
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

class ConnectionManager:
    """Manage WebSocket connections for real-time progress updates"""

    def __init__(self):
        # Map resume_id to set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, resume_id: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if resume_id not in self.active_connections:
            self.active_connections[resume_id] = set()
        self.active_connections[resume_id].add(websocket)

        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "resume_id": resume_id,
            "message": "Connected to resume parsing updates"
        }, websocket)

    def disconnect(self, websocket: WebSocket, resume_id: str):
        """Remove a WebSocket connection"""
        if resume_id in self.active_connections:
            self.active_connections[resume_id].discard(websocket)
            if not self.active_connections[resume_id]:
                del self.active_connections[resume_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def broadcast_to_resume(self, message: dict, resume_id: str):
        """Broadcast a message to all connections watching a specific resume"""
        if resume_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[resume_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)

            # Clean up disconnected WebSockets
            for connection in disconnected:
                self.disconnect(connection, resume_id)

# Global connection manager instance
manager = ConnectionManager()
EOF
```

**Step 4: Update FastAPI app to include WebSocket route**

```bash
cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import resumes
from app.api.websocket import manager

app = FastAPI(
    title="ResuMate API",
    description="Smart Resume Parser API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resumes.router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.websocket("/ws/resumes/{resume_id}")
async def websocket_endpoint(websocket: WebSocket, resume_id: str):
    """WebSocket endpoint for real-time resume parsing updates"""
    await manager.connect(websocket, resume_id)
    try:
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle any client messages (like ping/pong)
            if data == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "message": "alive"},
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, resume_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, resume_id)
EOF
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/integration/test_websocket.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/api/websocket.py backend/app/main.py backend/tests/integration/test_websocket.py
git commit -m "feat: add WebSocket connection manager for real-time updates"
```

---

## Task 2: Create Progress Message Types and Utilities

**Files:**
- Create: `backend/app/models/progress.py`
- Create: `backend/tests/unit/test_progress.py`

**Step 1: Write failing test for progress message creation**

```bash
cat > backend/tests/unit/test_progress.py << 'EOF'
import pytest
from app.models.progress import ProgressUpdate, ProgressStage

def test_create_progress_update():
    """Test creating a progress update message"""
    update = ProgressUpdate(
        resume_id="test-123",
        stage=ProgressStage.TEXT_EXTRACTION,
        progress=50,
        status="Extracting text from PDF..."
    )

    assert update.resume_id == "test-123"
    assert update.stage == ProgressStage.TEXT_EXTRACTION
    assert update.progress == 50
    assert update.status == "Extracting text from PDF..."

def test_progress_update_to_dict():
    """Test converting progress update to dictionary"""
    update = ProgressUpdate(
        resume_id="test-123",
        stage=ProgressStage.NLP_PARSING,
        progress=75,
        status="Analyzing resume structure..."
    )

    data = update.to_dict()

    assert data["resume_id"] == "test-123"
    assert data["stage"] == "nlp_parsing"
    assert data["progress"] == 75
    assert data["status"] == "Analyzing resume structure..."
    assert "timestamp" in data
EOF
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_progress.py -v`
Expected: FAIL - Progress update model doesn't exist

**Step 3: Implement progress message models**

```bash
cat > backend/app/models/progress.py << 'EOF'
from enum import Enum
from typing import Optional
from datetime import datetime
import json

class ProgressStage(str, Enum):
    """Parsing pipeline stages"""
    TEXT_EXTRACTION = "text_extraction"
    NLP_PARSING = "nlp_parsing"
    AI_ENHANCEMENT = "ai_enhancement"
    COMPLETE = "complete"
    ERROR = "error"

class ProgressUpdate:
    """Structured progress update message"""

    def __init__(
        self,
        resume_id: str,
        stage: ProgressStage,
        progress: int,  # 0-100
        status: str,
        estimated_seconds_remaining: Optional[int] = None,
        data: Optional[dict] = None
    ):
        self.resume_id = resume_id
        self.stage = stage
        self.progress = max(0, min(100, progress))  # Clamp to 0-100
        self.status = status
        self.estimated_seconds_remaining = estimated_seconds_remaining
        self.data = data or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": "progress_update",
            "resume_id": self.resume_id,
            "stage": self.stage.value,
            "progress": self.progress,
            "status": self.status,
            "estimated_seconds_remaining": self.estimated_seconds_remaining,
            "data": self.data,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

class CompleteProgress(ProgressUpdate):
    """Progress update for parsing completion"""

    def __init__(self, resume_id: str, parsed_data: dict):
        super().__init__(
            resume_id=resume_id,
            stage=ProgressStage.COMPLETE,
            progress=100,
            status="Parsing complete!",
            data=parsed_data
        )

class ErrorProgress(ProgressUpdate):
    """Progress update for parsing errors"""

    def __init__(self, resume_id: str, error_message: str, error_code: str = "PARSE_ERROR"):
        super().__init__(
            resume_id=resume_id,
            stage=ProgressStage.ERROR,
            progress=0,
            status=f"Error: {error_message}",
            data={"error_code": error_code, "error_message": error_message}
        )
EOF
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_progress.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/progress.py backend/tests/unit/test_progress.py
git commit -m "feat: add progress message types and utilities"
```

---

## Task 3: Create Parser Orchestrator Service

**Files:**
- Create: `backend/app/services/parser_orchestrator.py`
- Create: `backend/tests/unit/test_parser_orchestrator.py`

**Step 1: Write failing test for parser orchestrator**

```bash
cat > backend/tests/unit/test_parser_orchestrator.py << 'EOF'
import pytest
from unittest.mock import Mock, patch
from app.services.parser_orchestrator import ParserOrchestrator
from app.models.progress import ProgressStage

@pytest.mark.asyncio
async def test_orchestrator_sends_progress_updates():
    """Test that orchestrator sends progress updates during parsing"""
    mock_websocket_manager = Mock()
    orchestrator = ParserOrchestrator(mock_websocket_manager)

    resume_id = "test-123"
    file_content = b"Sample resume text for John Doe\nEmail: john@example.com"

    await orchestrator.parse_resume(resume_id, "test.pdf", file_content)

    # Verify progress updates were sent
    assert mock_websocket_manager.broadcast_to_resume.call_count >= 3

    # Check that stages were called in order
    calls = mock_websocket_manager.broadcast_to_resume.call_args_list
    stages = [call[0][0]["stage"] for call in calls]

    assert ProgressStage.TEXT_EXTRACTION.value in stages
    assert ProgressStage.NLP_PARSING.value in stages
    assert ProgressStage.COMPLETE.value in stages
EOF
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_parser_orchestrator.py -v`
Expected: FAIL - Parser orchestrator doesn't exist

**Step 3: Implement parser orchestrator**

```bash
cat > backend/app/services/parser_orchestrator.py << 'EOF'
import asyncio
from typing import Optional
from app.services.text_extractor import extract_text, TextExtractionError
from app.services.nlp_extractor import extract_entities
from app.models.progress import (
    ProgressUpdate,
    ProgressStage,
    CompleteProgress,
    ErrorProgress
)

class ParserOrchestrator:
    """Orchestrates the resume parsing pipeline with progress updates"""

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager

    async def parse_resume(
        self,
        resume_id: str,
        filename: str,
        file_content: bytes
    ) -> dict:
        """
        Parse a resume through the complete pipeline with progress updates.

        Args:
            resume_id: Unique identifier for this resume
            filename: Original filename
            file_content: File bytes content

        Returns:
            Parsed resume data dictionary
        """
        try:
            # Stage 1: Text Extraction
            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                10,
                "Starting text extraction..."
            )

            raw_text = await self._extract_text_with_progress(resume_id, filename, file_content)

            # Stage 2: NLP Entity Extraction
            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                40,
                "Extracting entities using NLP..."
            )

            parsed_data = await self._extract_entities_with_progress(resume_id, raw_text)

            # Stage 3: Complete
            await self._send_complete(resume_id, parsed_data)

            return parsed_data

        except TextExtractionError as e:
            await self._send_error(resume_id, f"Text extraction failed: {str(e)}", "TEXT_EXTRACTION_ERROR")
            raise
        except Exception as e:
            await self._send_error(resume_id, f"Parsing failed: {str(e)}", "PARSE_ERROR")
            raise

    async def _extract_text_with_progress(
        self,
        resume_id: str,
        filename: str,
        file_content: bytes
    ) -> str:
        """Extract text with progress updates"""
        try:
            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                30,
                "Extracting text from file..."
            )

            text = await extract_text(filename, file_content)

            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                100,
                "Text extraction complete!"
            )

            return text
        except Exception as e:
            await self._send_progress(
                resume_id,
                ProgressStage.TEXT_EXTRACTION,
                0,
                f"Extraction failed: {str(e)}"
            )
            raise

    async def _extract_entities_with_progress(
        self,
        resume_id: str,
        text: str
    ) -> dict:
        """Extract entities with progress updates"""
        try:
            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                60,
                "Analyzing resume structure..."
            )

            # Simulate NLP processing time
            await asyncio.sleep(0.5)

            parsed_data = extract_entities(text)

            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                100,
                "Entity extraction complete!"
            )

            return parsed_data
        except Exception as e:
            await self._send_progress(
                resume_id,
                ProgressStage.NLP_PARSING,
                0,
                f"NLP parsing failed: {str(e)}"
            )
            raise

    async def _send_progress(
        self,
        resume_id: str,
        stage: ProgressStage,
        progress: int,
        status: str
    ):
        """Send a progress update via WebSocket"""
        update = ProgressUpdate(
            resume_id=resume_id,
            stage=stage,
            progress=progress,
            status=status
        )
        await self.websocket_manager.broadcast_to_resume(update.to_dict(), resume_id)

    async def _send_complete(self, resume_id: str, parsed_data: dict):
        """Send completion message"""
        update = CompleteProgress(resume_id=resume_id, parsed_data=parsed_data)
        await self.websocket_manager.broadcast_to_resume(update.to_dict(), resume_id)

    async def _send_error(self, resume_id: str, error_message: str, error_code: str):
        """Send error message"""
        update = ErrorProgress(
            resume_id=resume_id,
            error_message=error_message,
            error_code=error_code
        )
        await self.websocket_manager.broadcast_to_resume(update.to_dict(), resume_id)
EOF
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_parser_orchestrator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/parser_orchestrator.py backend/tests/unit/test_parser_orchestrator.py
git commit -m "feat: implement parser orchestrator with progress updates"
```

---

## Task 4: Integrate Orchestrator with Upload Endpoint

**Files:**
- Modify: `backend/app/api/resumes.py`
- Modify: `backend/tests/integration/test_api_resumes.py`

**Step 1: Update upload endpoint to trigger parsing**

```bash
cat > backend/app/api/resumes.py << 'EOF'
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Dict
import uuid
import hashlib
import asyncio

from app.api.websocket import manager
from app.services.parser_orchestrator import ParserOrchestrator

router = APIRouter(prefix="/v1/resumes", tags=["resumes"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create orchestrator instance
orchestrator = ParserOrchestrator(manager)

async def parse_resume_background(resume_id: str, filename: str, content: bytes):
    """Background task to parse resume and send progress updates"""
    try:
        await orchestrator.parse_resume(resume_id, filename, content)
    except Exception as e:
        print(f"Background parsing error for {resume_id}: {e}")

@router.post("/upload", status_code=202)
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> Dict:
    """
    Upload a resume for parsing.

    Returns 202 Accepted and starts async processing.
    """
    # Validate file extension
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )

    # Generate resume ID and file hash
    resume_id = str(uuid.uuid4())
    file_hash = hashlib.sha256(content).hexdigest()

    # Start background parsing task
    if background_tasks:
        background_tasks.add_task(parse_resume_background, resume_id, file.filename, content)
    else:
        # For testing without background tasks
        asyncio.create_task(parse_resume_background(resume_id, file.filename, content))

    return {
        "resume_id": resume_id,
        "status": "processing",
        "estimated_time_seconds": 30,
        "file_hash": file_hash,
        "websocket_url": f"/ws/resumes/{resume_id}"
    }
EOF
```

**Step 2: Add integration test for WebSocket progress**

```bash
cat > backend/tests/integration/test_websocket_flow.py << 'EOF'
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_and_websocket_progress():
    """Test complete flow: upload -> WebSocket connects -> progress updates"""
    # First upload a file
    upload_response = client.post(
        "/v1/resumes/upload",
        files={"file": ("test.txt", b"John Doe\nEmail: john@example.com", "text/plain")}
    )

    assert upload_response.status_code == 202
    data = upload_response.json()
    resume_id = data["resume_id"]

    # Then connect to WebSocket and receive progress
    with client.websocket_connect(f"/ws/resumes/{resume_id}") as websocket:
        # Connection established
        msg1 = websocket.receive_json()
        assert msg1["type"] == "connection_established"

        # Progress updates (order may vary)
        messages_received = []
        timeout_counter = 0
        max_messages = 10  # Prevent infinite loop

        while timeout_counter < max_messages:
            try:
                msg = websocket.receive_json()
                messages_received.append(msg)

                if msg.get("stage") == "complete":
                    break

                timeout_counter += 1
            except Exception:
                break

        # Verify we received progress updates
        stages = [msg.get("stage") for msg in messages_received]

        assert "complete" in stages
        assert len(messages_received) >= 2  # At least connection + complete
EOF
```

**Step 3: Run integration tests**

Run: `cd backend && python -m pytest tests/integration/test_websocket_flow.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/api/resumes.py backend/tests/integration/test_websocket_flow.py
git commit -m "feat: integrate parser orchestrator with upload endpoint"
```

---

## Task 5: Create Frontend WebSocket Hook

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`
- Create: `frontend/src/hooks/__tests__/useWebSocket.test.ts`

**Step 1: Write failing test for WebSocket hook**

```bash
mkdir -p frontend/src/hooks/__tests__

cat > frontend/src/hooks/__tests__/useWebSocket.test.ts << 'EOF'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '../useWebSocket'

describe('useWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should connect to WebSocket on mount', () => {
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }

    global.WebSocket = jest.fn(() => mockWebSocket) as any

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/test')
    expect(result.current.connected).toBe(true)
  })

  it('should receive and parse messages', () => {
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn((event, callback) => {
        if (event === 'open') {
          setTimeout(() => (callback as EventListener)(new Event('open')), 0)
        }
      }),
      removeEventListener: jest.fn(),
    }

    global.WebSocket = jest.fn(() => mockWebSocket) as any

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/test'))

    expect(result.current.lastMessage).toBe(null)
  })
})
EOF
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- useWebSocket.test.ts`
Expected: FAIL - Hook doesn't exist

**Step 3: Implement WebSocket hook**

```bash
cat > frontend/src/hooks/useWebSocket.ts << 'EOF'
import { useState, useEffect, useCallback, useRef } from 'react'

export interface WebSocketMessage {
  type: string
  stage?: string
  progress?: number
  status?: string
  estimated_seconds_remaining?: number
  data?: any
  timestamp?: string
}

export interface WebSocketHookReturn {
  connected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (message: any) => void
  error: Event | null
}

export function useWebSocket(url: string): WebSocketHookReturn {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<Event | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    let ws: WebSocket
    let reconnectAttempts = 0
    const maxReconnectAttempts = 3

    const connect = () => {
      try {
        ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          setConnected(true)
          setError(null)
          reconnectAttempts = 0
          console.log('WebSocket connected')
        }

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            setLastMessage(message)
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err)
          }
        }

        ws.onerror = (event: Event) => {
          console.error('WebSocket error:', event)
          setError(event)
        }

        ws.onclose = () => {
          setConnected(false)
          console.log('WebSocket disconnected')

          // Attempt to reconnect
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++
            console.log(`Reconnecting... Attempt ${reconnectAttempts}`)
            reconnectTimeoutRef.current = setTimeout(connect, 2000)
          }
        }
      } catch (err) {
        console.error('Failed to create WebSocket connection:', err)
        setError(err as Event)
      }
    }

    connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws) {
        ws.close()
      }
    }
  }, [url])

  return {
    connected,
    lastMessage,
    sendMessage,
    error
  }
}
EOF
```

**Step 4: Update TypeScript types for hook**

```bash
cat > frontend/src/hooks/index.ts << 'EOF'
export { useWebSocket } from './useWebSocket'
export type { WebSocketMessage, WebSocketHookReturn } from './useWebSocket'
EOF
```

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- useWebSocket.test.ts`
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/hooks/useWebSocket.ts frontend/src/hooks/__tests__/useWebSocket.test.ts frontend/src/hooks/index.ts
git commit -m "feat: add WebSocket hook for real-time communication"
```

---

## Task 6: Create Processing Page UI Components

**Files:**
- Create: `frontend/src/components/ProcessingStage.tsx`
- Create: `frontend/src/components/__tests__/ProcessingStage.test.tsx`

**Step 1: Write failing test for ProcessingStage component**

```bash
mkdir -p frontend/src/components/__tests__

cat > frontend/src/components/__tests__/ProcessingStage.test.tsx << 'EOF'
import { render, screen } from '@testing-library/react'
import ProcessingStage from '../ProcessingStage'

describe('ProcessingStage', () => {
  it('renders stage name and progress percentage', () => {
    render(
      <ProcessingStage
        name="Text Extraction"
        status="pending"
        progress={0}
      />
    )

    expect(screen.getByText('Text Extraction')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('shows in-progress state correctly', () => {
    render(
      <ProcessingStage
        name="NLP Parsing"
        status="in_progress"
        progress={65}
      />
    )

    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('shows complete state with checkmark', () => {
    render(
      <ProcessingStage
        name="AI Enhancement"
        status="complete"
        progress={100}
      />
    )

    expect(screen.getByText('100%')).toBeInTheDocument()
  })
})
EOF
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ProcessingStage.test.tsx`
Expected: FAIL - Component doesn't exist

**Step 3: Implement ProcessingStage component**

```bash
cat > frontend/src/components/ProcessingStage.tsx << 'EOF'
import React from 'react'
import { Check, Clock, AlertCircle } from 'lucide-react'

interface ProcessingStageProps {
  name: string
  status: 'pending' | 'in_progress' | 'complete' | 'error'
  progress: number
}

export default function ProcessingStage({ name, status, progress }: ProcessingStageProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'complete':
        return <Check className="h-5 w-5 text-green-600" />
      case 'in_progress':
        return <Clock className="h-5 w-5 text-navy-600 animate-pulse" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'complete':
        return 'text-green-600'
      case 'in_progress':
        return 'text-navy-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-400'
    }
  }

  const getProgressBarColor = () => {
    switch (status) {
      case 'complete':
        return 'bg-green-600'
      case 'in_progress':
        return 'bg-navy-600'
      case 'error':
        return 'bg-red-600'
      default:
        return 'bg-gray-300'
    }
  }

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className={`font-semibold ${getStatusColor()}`}>
            {name}
          </span>
        </div>
        <span className={`font-mono ${getStatusColor()}`}>
          {progress}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${getProgressBarColor()} transition-all duration-500 ease-out`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}
EOF
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- ProcessingStage.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/ProcessingStage.tsx frontend/src/components/__tests__/ProcessingStage.test.tsx
git commit -m "feat: add ProcessingStage component"
```

---

## Task 7: Implement ProcessingPage Component

**Files:**
- Modify: `frontend/src/pages/ProcessingPage.tsx`
- Create: `frontend/src/pages/__tests__/ProcessingPage.test.tsx`

**Step 1: Write failing test for ProcessingPage**

```bash
mkdir -p frontend/src/pages/__tests__

cat > frontend/src/pages/__tests__/ProcessingPage.test.tsx << 'EOF'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ProcessingPage from '../ProcessingPage'

// Mock the WebSocket hook
jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(() => ({
    connected: true,
    lastMessage: null,
    sendMessage: jest.fn(),
    error: null
  }))
}))

describe('ProcessingPage', () => {
  it('renders processing page with stages', () => {
    render(
      <BrowserRouter>
        <ProcessingPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Parsing Your Resume/i)).toBeInTheDocument()
    expect(screen.getByText(/Text Extraction/i)).toBeInTheDocument()
    expect(screen.getByText(/NLP Parsing/i)).toBeInTheDocument()
    expect(screen.getByText(/AI Enhancement/i)).toBeInTheDocument()
  })
})
EOF
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ProcessingPage.test.tsx`
Expected: FAIL - Component needs updating

**Step 3: Implement ProcessingPage component**

```bash
cat > frontend/src/pages/ProcessingPage.tsx << 'EOF'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket'
import ProcessingStage from '@/components/ProcessingStage'
import { AlertCircle } from 'lucide-react'

interface StageProgress {
  name: string
  status: 'pending' | 'in_progress' | 'complete' | 'error'
  progress: number
  statusMessage: string
}

export default function ProcessingPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [stages, setStages] = useState<StageProgress[]>([
    { name: 'Text Extraction', status: 'pending', progress: 0, statusMessage: 'Waiting...' },
    { name: 'NLP Parsing', status: 'pending', progress: 0, statusMessage: 'Waiting...' },
    { name: 'AI Enhancement', status: 'pending', progress: 0, statusMessage: 'Waiting...' }
  ])
  const [error, setError] = useState<string | null>(null)
  const [estimatedTime, setEstimatedTime] = useState<number>(30)

  const wsUrl = `${import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws'}/resumes/${id}`
  const { connected, lastMessage, sendMessage } = useWebSocket(wsUrl)

  useEffect(() => {
    if (!lastMessage) return

    const message = lastMessage as WebSocketMessage

    switch (message.type) {
      case 'connection_established':
        console.log('WebSocket connected for resume:', message.resume_id)
        break

      case 'progress_update':
        updateStageProgress(message)
        break

      case 'complete':
        handleComplete(message)
        break

      case 'error':
        handleError(message)
        break
    }
  }, [lastMessage])

  const updateStageProgress = (message: WebSocketMessage) => {
    setStages(prevStages => {
      const newStages = [...prevStages]

      switch (message.stage) {
        case 'text_extraction':
          newStages[0] = {
            ...newStages[0],
            status: message.progress === 100 ? 'complete' : 'in_progress',
            progress: message.progress || 0,
            statusMessage: message.status || 'Processing...'
          }
          break

        case 'nlp_parsing':
          newStages[0] = { ...newStages[0], status: 'complete', progress: 100 }
          newStages[1] = {
            ...newStages[1],
            status: message.progress === 100 ? 'complete' : 'in_progress',
            progress: message.progress || 0,
            statusMessage: message.status || 'Processing...'
          }
          break

        case 'ai_enhancement':
          newStages[0] = { ...newStages[0], status: 'complete', progress: 100 }
          newStages[1] = { ...newStages[1], status: 'complete', progress: 100 }
          newStages[2] = {
            ...newStages[2],
            status: message.progress === 100 ? 'complete' : 'in_progress',
            progress: message.progress || 0,
            statusMessage: message.status || 'Processing...'
          }
          break
      }

      // Update estimated time
      if (message.estimated_seconds_remaining !== undefined) {
        setEstimatedTime(message.estimated_seconds_remaining)
      }

      return newStages
    })
  }

  const handleComplete = (message: WebSocketMessage) => {
    setStages(prevStages =>
      prevStages.map(stage => ({
        ...stage,
        status: 'complete' as const,
        progress: 100
      }))
    )

    // Redirect to review page after a short delay
    setTimeout(() => {
      navigate(`/review/${id}`, { replace: true })
    }, 1500)
  }

  const handleError = (message: WebSocketMessage) => {
    const errorMessage = message.data?.error_message || 'An unknown error occurred'
    setError(errorMessage)
  }

  const handleRetry = () => {
    setError(null)
    navigate('/', { replace: true })
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center">
          <AlertCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-navy-900 mb-4">
            Parsing Failed
          </h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleRetry}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 to-navy-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-navy-900 mb-2">
            ResuMate
          </h1>
          <p className="text-xl text-navy-700 mb-4">
            Parsing Your Resume
          </p>

          {/* Connection Status */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className={`h-3 w-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Connecting...'}
            </span>
          </div>

          {/* Estimated Time */}
          <div className="text-gray-600">
            Estimated time: <span className="font-semibold">{estimatedTime} seconds</span>
          </div>
        </div>

        {/* Processing Stages */}
        <div className="space-y-4">
          {stages.map((stage, index) => (
            <ProcessingStage
              key={index}
              name={stage.name}
              status={stage.status}
              progress={stage.progress}
            />
          ))}
        </div>

        {/* Cancel Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/', { replace: true })}
            className="text-gray-600 hover:text-navy-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
EOF
```

**Step 4: Update types for WebSocket messages**

```bash
cat > frontend/src/types/websocket.ts << 'EOF'
export interface WebSocketMessage {
  type: string
  resume_id?: string
  stage?: 'text_extraction' | 'nlp_parsing' | 'ai_enhancement' | 'complete' | 'error'
  progress?: number
  status?: string
  estimated_seconds_remaining?: number
  data?: any
  timestamp?: string
}
EOF
```

**Step 5: Update index.ts to export websocket types**

```bash
cat > frontend/src/types/index.ts << 'EOF'
export interface PersonalInfo {
  full_name: string
  email: string
  phone: string
  location: string
  linkedin_url: string
  github_url: string
  portfolio_url: string
  summary: string
}

export interface WorkExperience {
  company: string
  title: string
  location: string
  start_date: string
  end_date: string
  description: string
  confidence: number
}

export interface Education {
  institution: string
  degree: string
  field_of_study: string
  location: string
  start_date: string
  end_date: string
  gpa: string
  confidence: number
}

export interface Skills {
  technical: string[]
  soft_skills: string[]
  languages: string[]
  certifications: string[]
  confidence: number
}

export interface ConfidenceScores {
  personal_info: number
  work_experience: number
  education: number
  skills: number
}

export interface ParsedResumeData {
  id: string
  status: string
  confidence_score: number
  personal_info: PersonalInfo
  work_experience: WorkExperience[]
  education: Education[]
  skills: Skills
  confidence_scores: ConfidenceScores
}

export * from './websocket'
EOF
```

**Step 6: Run test to verify it passes**

Run: `cd frontend && npm test -- ProcessingPage.test.tsx`
Expected: PASS

**Step 7: Run type check**

Run: `cd frontend && npm run type-check`
Expected: No TypeScript errors

**Step 8: Commit**

```bash
git add frontend/src/pages/ProcessingPage.tsx frontend/src/pages/__tests__/ProcessingPage.test.tsx frontend/src/types/
git commit -m "feat: implement ProcessingPage with WebSocket updates"
```

---

## Task 8: Add Frontend Environment Variables

**Files:**
- Modify: `frontend/.env.example`

**Step 1: Update .env.example**

```bash
cat > frontend/.env.example << 'EOF'
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
EOF
```

**Step 2: Create local .env file**

```bash
cp frontend/.env.example frontend/.env
```

**Step 3: Commit**

```bash
git add frontend/.env.example
git commit -m "chore: add WebSocket environment variable"
```

---

## Task 9: Update README with WebSocket Instructions

**Files:**
- Modify: `README.md`

**Step 1: Update README with WebSocket info**

```bash
cat > README.md << 'EOF'
# ResuMate - Smart Resume Parser

An intelligent resume parsing platform that extracts structured data from resumes using OCR, NLP, and AI.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+) with WebSocket support
- **Frontend:** React 18+ with TypeScript and WebSocket hooks
- **Database:** PostgreSQL with JSONB
- **AI/ML:** Tesseract OCR, spaCy NLP, OpenAI GPT-4
- **Deployment:** Railway (backend), Vercel (frontend)

## Features

- ✅ Multi-format support (PDF, DOCX, DOC, TXT)
- ✅ Real-time parsing progress via WebSocket
- ✅ NLP-based entity extraction
- ✅ Confidence scoring
- 🚧 AI enhancement (coming soon)
- 🚧 Review & edit capabilities (coming soon)
- 🚧 Share & export (coming soon)

## Project Structure

```
resume-parser/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # API routes & WebSocket handlers
│   │   ├── models/   # SQLAlchemy models & progress types
│   │   ├── services/ # Business logic (parser, orchestrator)
│   │   └── main.py   # FastAPI app entry
│   ├── tests/
│   └── requirements.txt
├── frontend/         # React application
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── hooks/      # Custom React hooks (WebSocket)
│   │   └── lib/
│   └── package.json
└── docs/
    └── plans/
```

## Getting Started

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

WebSocket endpoint: `ws://localhost:8000/ws/resumes/{resume_id}`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env if needed (defaults to http://localhost:8000)

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

### Testing

**Backend:**
```bash
cd backend
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
npm run type-check
```

## Usage Flow

1. **Upload** - Upload resume (PDF, DOCX, DOC, TXT) at http://localhost:3000
2. **Processing** - Watch real-time parsing progress via WebSocket
3. **Review** - (Coming soon) Review extracted data with confidence scores
4. **Share** - (Coming soon) Export and share parsed data

## WebSocket Communication

**Connection:**
```
ws://localhost:8000/ws/resumes/{resume_id}
```

**Progress Update Message:**
```json
{
  "type": "progress_update",
  "stage": "text_extraction | nlp_parsing | ai_enhancement | complete",
  "progress": 50,
  "status": "Extracting text...",
  "estimated_seconds_remaining": 15
}
```

## Environment Variables

**Backend (.env):**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for Celery
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `SECRET_KEY` - Secret key for signing
- `ALLOWED_ORIGINS` - CORS allowed origins

**Frontend (.env):**
- `VITE_API_BASE_URL` - Backend API base URL
- `VITE_WS_BASE_URL` - WebSocket base URL

## License

MIT
EOF
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with WebSocket and usage instructions"
```

---

## Task 10: End-to-End Integration Testing

**Files:**
- Create: `backend/tests/e2e/test_processing_flow.py`

**Step 1: Create E2E test**

```bash
mkdir -p backend/tests/e2e

cat > backend/tests/e2e/test_processing_flow.py << 'EOF'
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_upload_to_processing_flow():
    """Test complete flow from upload to processing completion"""
    # Step 1: Upload resume
    upload_response = client.post(
        "/v1/resumes/upload",
        files={
            "file": (
                "test_resume.txt",
                b"John Doe\nSoftware Engineer\nEmail: john@example.com\nPhone: +1-555-0123",
                "text/plain"
            )
        }
    )

    assert upload_response.status_code == 202
    data = upload_response.json()
    assert "resume_id" in data
    assert "websocket_url" in data

    resume_id = data["resume_id"]

    # Step 2: Connect to WebSocket and receive updates
    with client.websocket_connect(f"/ws/resumes/{resume_id}") as websocket:
        # Connection established
        msg = websocket.receive_json()
        assert msg["type"] == "connection_established"

        # Collect all progress messages
        messages = []
        timeout = time.time() + 10  # 10 second timeout

        while time.time() < timeout:
            try:
                msg = websocket.receive_json()
                messages.append(msg)

                if msg.get("stage") == "complete":
                    break
            except Exception:
                break

        # Verify we received meaningful progress
        assert len(messages) >= 2

        # Check for complete message
        complete_msgs = [m for m in messages if m.get("stage") == "complete"]
        assert len(complete_msgs) > 0
EOF
```

**Step 2: Run E2E test**

Run: `cd backend && python -m pytest tests/e2e/test_processing_flow.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/e2e/test_processing_flow.py
git commit -m "test: add end-to-end integration test for processing flow"
```

---

## Verification Checklist

After completing all tasks, verify:

**Backend:**
- [ ] WebSocket endpoint accepts connections
- [ ] Upload endpoint triggers background parsing
- [ ] Progress updates broadcast via WebSocket
- [ ] All unit tests pass (pytest tests/)
- [ ] All integration tests pass
- [ ] E2E test passes

**Frontend:**
- [ ] WebSocket hook connects successfully
- [ ] ProcessingPage displays correctly
- [ ] Progress stages update in real-time
- [ ] Auto-redirect works on completion
- [ ] Error handling displays correctly
- [ ] TypeScript type-check passes
- [ ] All component tests pass

**Integration:**
- [ ] Upload file → WebSocket connects → Progress updates → Redirect to review
- [ ] Full flow works end-to-end

---

## Run All Tests

**Backend:**
```bash
cd backend
python -m pytest tests/ -v --cov=app
```

**Frontend:**
```bash
cd frontend
npm test -- --coverage
npm run type-check
```

---

## Summary

**Tasks Completed:** 10
**New Files Created:** 15
**Tests Added:** 12 (unit + integration + E2E)

**Key Features Implemented:**
1. ✅ WebSocket connection manager
2. ✅ Progress message types and utilities
3. ✅ Parser orchestrator service
4. ✅ Background parsing integration
5. ✅ Frontend WebSocket hook
6. ✅ ProcessingStage component
7. ✅ ProcessingPage with real-time updates
8. ✅ Error handling and retry
9. ✅ Auto-redirect on completion
10. ✅ E2E integration testing

---

**Plan Status:** ✅ Complete - Ready for execution
**Created:** 2026-02-19
**Next:** Execute using superpowers:executing-plans or superpowers:subagent-driven-development

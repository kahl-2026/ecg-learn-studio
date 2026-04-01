"""API Server - JSON RPC over stdin/stdout"""

import sys
import json
from typing import Dict, Any
from .handlers import RequestHandler


class ECGLearnAPIServer:
    """JSON RPC server for Rust TUI communication."""
    
    def __init__(self):
        """Initialize API server."""
        self.handler = RequestHandler()
        self.running = False
    
    def start(self):
        """Start the server loop."""
        self.running = True
        self._send_log("ECG Learn API Server started")
        
        try:
            while self.running:
                # Read request from stdin
                line = sys.stdin.readline()
                
                if not line:
                    break  # EOF
                
                try:
                    request = json.loads(line.strip())
                    response = self.handle_request(request)
                    self._send_response(response)
                    
                except json.JSONDecodeError as e:
                    error_response = self._create_error_response(
                        "unknown",
                        "INVALID_REQUEST",
                        f"Invalid JSON: {str(e)}"
                    )
                    self._send_response(error_response)
                    
                except Exception as e:
                    error_response = self._create_error_response(
                        "unknown",
                        "INTERNAL_ERROR",
                        f"Unexpected error: {str(e)}"
                    )
                    self._send_response(error_response)
        
        except KeyboardInterrupt:
            self._send_log("Server shutting down")
        
        finally:
            self.running = False
    
    def handle_request(self, request: Dict) -> Dict:
        """
        Handle a JSON RPC request.
        
        Args:
            request: Request dictionary
            
        Returns:
            Response dictionary
        """
        # Validate request structure
        if not isinstance(request, dict):
            return self._create_error_response(
                "unknown",
                "INVALID_REQUEST",
                "Request must be a JSON object"
            )
        
        request_id = request.get('id', 'unknown')
        version = request.get('version', '1.0')
        method = request.get('method')
        params = request.get('params', {})
        
        # Check version
        if version != '1.0':
            return self._create_error_response(
                request_id,
                "UNSUPPORTED_VERSION",
                f"Protocol version {version} not supported"
            )
        
        # Check method
        if not method:
            return self._create_error_response(
                request_id,
                "INVALID_REQUEST",
                "Missing 'method' field"
            )
        
        # Route to handler
        try:
            result = self.handler.handle(method, params)
            return {
                'id': request_id,
                'version': '1.0',
                'success': True,
                'result': result
            }
        
        except ValueError as e:
            return self._create_error_response(
                request_id,
                "INVALID_PARAMS",
                str(e)
            )
        
        except FileNotFoundError as e:
            return self._create_error_response(
                request_id,
                "DATA_NOT_FOUND",
                str(e)
            )
        
        except Exception as e:
            return self._create_error_response(
                request_id,
                "PROCESSING_ERROR",
                str(e)
            )
    
    def _create_error_response(
        self,
        request_id: str,
        code: str,
        message: str
    ) -> Dict:
        """Create error response."""
        return {
            'id': request_id,
            'version': '1.0',
            'success': False,
            'error': {
                'code': code,
                'message': message
            }
        }
    
    def _send_response(self, response: Dict):
        """Send response to stdout."""
        sys.stdout.write(json.dumps(response) + '\n')
        sys.stdout.flush()
    
    def _send_log(self, message: str):
        """Send log message (as progress update)."""
        log = {
            'type': 'log',
            'data': {'message': message}
        }
        sys.stderr.write(json.dumps(log) + '\n')
        sys.stderr.flush()


if __name__ == '__main__':
    server = ECGLearnAPIServer()
    server.start()

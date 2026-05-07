"""
MCP Client — Communicates with the MCP Server (Overleaf Tool).
Sends .tex files, triggers compilation, retrieves errors/PDF URL.
"""

import os
import json
import logging
import aiohttp

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")
UNKNOWN_COMPILATION_ERROR = "Unknown compilation error"


class MCPClient:
    def __init__(self):
        self.base_url = MCP_SERVER_URL
        self.timeout = aiohttp.ClientTimeout(total=120)

    async def compile(self, tex_content: str, filename: str = "rapport_pfe.tex", project_files: dict | None = None) -> dict:
        """Write the LaTeX project and compile. Returns {status, pdf_url?, errors?}."""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if project_files:
                write_error = await self._write_project_files(session, project_files)
                if write_error:
                    return {"status": "error", "errors": [write_error]}
                logger.info(f"📁 {len(project_files)} project files written")
            else:
                write_error = await self._write_single_file(session, filename, tex_content)
                if write_error:
                    return {"status": "error", "errors": [write_error]}
                logger.info(f"📁 .tex file written: {filename}")

            return await self._compile_with_retries(session, filename, project_files)

    async def _write_single_file(self, session: aiohttp.ClientSession, filename: str, tex_content: str) -> str | None:
        write_result = await self._call_tool(session, "write_tex_file", {
            "filename": filename,
            "content": tex_content,
        })
        return write_result.get("error")

    async def _write_project_files(self, session: aiohttp.ClientSession, project_files: dict) -> str | None:
        for path, content in project_files.items():
            write_result = await self._call_tool(session, "write_tex_file", {
                "filename": path,
                "content": content,
            })
            if write_result.get("error"):
                return write_result["error"]
        return None

    async def _compile_with_retries(self, session: aiohttp.ClientSession, filename: str, project_files: dict | None) -> dict:
        last_result = None
        last_debug = None

        for attempt in range(1, 4):
            compile_result = await self._call_tool(session, "compile_latex", {"filename": filename})
            last_result = compile_result
            if compile_result.get("success"):
                return {
                    "status": "success",
                    "pdf_url": compile_result.get("pdf_url"),
                    "pdf_path": compile_result.get("pdf_path"),
                }

            last_debug = await self._call_tool(session, "debug_latex", {"filename": filename})
            logger.warning(
                "LaTeX compile attempt %s failed: %s | debug=%s",
                attempt,
                compile_result.get("errors", [UNKNOWN_COMPILATION_ERROR]),
                last_debug.get("findings", []),
            )

            if attempt < 3 and project_files:
                await self._write_project_files(session, project_files)

        return {
            "status": "error",
            "errors": last_result.get("errors", [UNKNOWN_COMPILATION_ERROR]) if last_result else [UNKNOWN_COMPILATION_ERROR],
            "debug": last_debug,
        }

    async def _call_tool(self, session: aiohttp.ClientSession, tool: str, params: dict) -> dict:
        """Generic MCP tool call over HTTP-SSE protocol."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": params,
                }
            }
            async with session.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()
                result = data.get("result", {})
                # Parse MCP content response
                content = result.get("content", [])
                if content and isinstance(content, list):
                    text = content[0].get("text", "{}")
                    return json.loads(text)
                return result
        except Exception as e:
            logger.error(f"MCP call failed ({tool}): {e}")
            return {"error": str(e)}

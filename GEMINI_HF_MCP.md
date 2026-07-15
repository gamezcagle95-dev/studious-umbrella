# Hugging Face Gemini CLI Integration Guide

This guide describes how to integrate the official Hugging Face MCP (Model Context Protocol) Server and the Hugging Face Gemini CLI extension into your workspace, empowering Gemini to access Hub models, datasets, Spaces, papers, and more.

## 1. Setup Instructions

To enable the Hugging Face MCP server in the Gemini CLI, follow these steps:

### A. Add the MCP Server
Run the following command to add the Hugging Face MCP server:
```bash
gemini mcp add -t http huggingface https://huggingface.co/mcp?login
```

This updates your `.gemini/settings.json` configuration file with the following block:
```json
{
  "mcpServers": {
    "huggingface": {
      "url": "https://huggingface.co/mcp?login",
      "type": "http"
    }
  }
}
```

### B. Authenticate with Hugging Face
Start Gemini and follow the on-screen instructions to complete authentication with your Hugging Face account:
```bash
gemini
```

Alternatively, you can authenticate directly with an authorization token by adding headers to the config or setting the `HF_TOKEN` / `DEFAULT_HF_TOKEN` environment variables.

---

## 2. Install the Gemini CLI Extension

The Hugging Face Gemini CLI extension bundles the MCP server with custom commands and a rich context file (`huggingface.md`) to teach Gemini how to best utilize the available tools.

### A. Installation Command
Install the extension directly from the official GitHub repository:
```bash
gemini extensions install https://github.com/huggingface/hf-mcp-server
```

### B. Authentication for the Extension
Once installed, start the Gemini CLI and run the following built-in command to authenticate:
```bash
/mcp auth huggingface
```

---

## 3. Features & Tools Available

Once configured and authenticated, Gemini gains access to high-fidelity tools including:
* **Model/Dataset Search:** Look up metadata, files, and cards.
* **Paper Explorer:** Query papers and summaries.
* **Spaces Integration:** Discover and invoke Gradio Spaces directly.
* **Contextual Guidance:** Automated context mapping via `huggingface.md`.

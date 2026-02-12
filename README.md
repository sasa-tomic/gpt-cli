# gpt-cli

Command-line interface for chat LLMs.

## Try now
```
export ANTHROPIC_API_KEY=xcxc
uvx --from gpt-command-line gpt
```

## Supported providers

- OpenAI
- Anthropic
- Google Gemini
- Cohere
- Other APIs compatible with OpenAI (e.g. Together, OpenRouter, local models with LM Studio)

![screenshot](https://github.com/kharvd/gpt-cli/assets/466920/ecbcccc4-7cfa-4c04-83c3-a822b6596f01)

## Features

- **Command-Line Interface**: Interact with ChatGPT or Claude directly from your terminal.
- **Model Customization**: Override the default model, temperature, and top_p values for each assistant, giving you fine-grained control over the AI's behavior.
- **Extended Thinking Mode**: Enable Claude 3.7's extended thinking capability to see its reasoning process for complex problems.
- **Usage tracking**: Track your API usage with token count and price information.
- **Keyboard Shortcuts**: Use Ctrl-C, Ctrl-D, and Ctrl-R shortcuts for easier conversation management and input control.
- **Multi-Line Input**: Enter multi-line mode for more complex queries or conversations.
- **Markdown Support**: Enable or disable markdown formatting for chat sessions to tailor the output to your preferences.
- **Predefined Messages**: Set up predefined messages for your custom assistants to establish context or role-play scenarios.
- **Multiple Assistants**: Easily switch between different assistants, including general, dev, and custom assistants defined in the config file.
- **Flexible Configuration**: Define your assistants, model parameters, and API key in a YAML configuration file, allowing for easy customization and management.

## Installation

Requires Python >=3.12,<3.14.

```bash
pip install gpt-command-line
```

Install latest version from source:

```bash
pip install git+https://github.com/kharvd/gpt-cli.git
```

Or install by cloning the repository manually:

```bash
git clone https://github.com/kharvd/gpt-cli.git
cd gpt-cli
pip install .
```

When using `uv tool install`, pass `--python 3.13` if your system Python is 3.14+:

```bash
uv tool install . --python 3.13
```

Add the OpenAI API key to your `.bashrc` file (in the root of your home folder).
In this example we use nano, you can use any text editor.

```
nano ~/.bashrc
export OPENAI_API_KEY=<your_key_here>
```

Run the tool

```
gpt
```

You can also use a `gpt.yml` file for configuration. See the [Configuration](README.md#Configuration) section below.

## Usage

Make sure to set the `OPENAI_API_KEY` environment variable to your OpenAI API key (or put it in the `~/.config/gpt-cli/gpt.yml` file as described below).

### Quick prompts

The simplest way to use gpt-cli is to pass your prompt directly:

```bash
gpt "What is the capital of France?"
gpt find all markdown files recursively    # quotes optional for simple prompts
```

This runs non-interactively and exits after the response.

### Interactive mode

Run without arguments to start an interactive chat session:

```bash
gpt                    # start with default assistant
gpt -a dev             # start with the dev assistant
```

### Command-line options

```
usage: gpt [-h] [-a ASSISTANT] [--model MODEL] [--provider PROVIDER]
           [--temperature TEMPERATURE] [--top_p TOP_P] [--thinking THINKING_BUDGET]
           [--prompt PROMPT] [--execute EXECUTE] [--no_markdown] [--no_stream]
           [--no_price] [prompt ...]

positional arguments:
  prompt                The prompt to send. If provided, runs non-interactively and exits.
                        Multiple words are joined with spaces. Use `-` to read from stdin.

optional arguments:
  -h, --help            show this help message and exit
  -a, --assistant       The assistant to use (general, dev, bash, or custom).
  -m, --model MODEL     The model to use. Overrides assistant/global config.
  --provider PROVIDER   The provider to use (openai, anthropic, google, cohere, llama, azure-openai).
  --temperature TEMP    The temperature (0.0-2.0).
  --top_p TOP_P         The top_p value (0.0-1.0).
  --thinking BUDGET     Enable Claude's extended thinking mode with token budget.
  -p, --prompt PROMPT   Legacy prompt flag (use positional args instead).
  -e, --execute CMD     Execute mode: generate and edit shell command before running.
  --no_markdown         Disable markdown formatting.
  --no_stream           Disable streaming output.
  --no_price            Disable price display.
```

Type `:q` or Ctrl-D to exit, `:c` or Ctrl-C to clear the conversation, `:r` or Ctrl-R to re-generate the last response.
To enter multi-line mode, enter a backslash `\` followed by a new line. Exit the multi-line mode by pressing ESC and then Enter.

### Assistants

The `dev` assistant is instructed to be an expert in software development and provide short responses.

```bash
gpt -a dev "explain this error"
```

The `bash` assistant is instructed to be an expert in bash scripting and provide only bash commands. Use the `--execute` option to execute the commands.

```bash
gpt -a bash -e "How do I list files in a directory?"
```

This will prompt you to edit the command in your `$EDITOR` before executing it.

## Configuration

You can configure the assistants in the config file `~/.config/gpt-cli/gpt.yml`. The file is a YAML file with the following structure (see also [config.py](./gptcli/config.py))

```yaml
# Global defaults - apply to all assistants unless overridden
default_assistant: <assistant_name>
default_provider: <openai|anthropic|google|cohere|llama|azure-openai>
default_model: <model_name>

markdown: True
show_price: True
log_file: <path>
log_level: <DEBUG|INFO|WARNING|ERROR|CRITICAL>

# API keys (can also use environment variables)
openai_api_key: <key>
openai_base_url: <url>           # optional, for custom endpoints
anthropic_api_key: <key>
anthropic_base_url: <url>        # optional, for custom endpoints
google_api_key: <key>
cohere_api_key: <key>

assistants:
  <assistant_name>:
    provider: <provider>         # optional, overrides default_provider
    model: <model_name>          # optional, overrides default_model
    base_url: <url>              # optional, per-assistant endpoint override
    api_key: <key>               # optional, per-assistant API key override
    temperature: <0.0-2.0>
    top_p: <0.0-1.0>
    thinking_budget: <tokens>    # Claude 3.7 models only
    messages:
      - { role: <role>, content: <message> }
      - ...
```

### Configuration priority

Settings are resolved in this order (highest priority first):
1. Command-line arguments (`--provider`, `--model`, etc.)
2. Assistant-specific config
3. Global defaults (`default_provider`, `default_model`)
4. Built-in defaults (provider: openai, model: gpt-4o)

### Example configuration

```yaml
default_assistant: dev
default_provider: anthropic
default_model: claude-sonnet-4-20250514

anthropic_api_key: <your_key>

assistants:
  pirate:
    model: gpt-4o
    provider: openai
    temperature: 1.0
    messages:
      - { role: system, content: "You are a pirate." }
  
  glm:
    provider: openai
    model: glm-4
    base_url: https://api.example.com/v1
    api_key: <glm_api_key>
```

```
$ gpt -a pirate "Arrrr"
Ahoy, matey! What be bringing ye to these here waters? Be it treasure or adventure ye seek, we be sailing the high seas together!
```

### Read other context to the assistant with !include

You can read in files to the assistant's context with !include <file_path>.

```yaml
default_assistant: dev
markdown: True
openai_api_key: <openai_api_key>
assistants:
  pirate:
    model: gpt-4
    temperature: 1.0
    messages:
      - { role: system, content: !include "pirate.txt" }
```

### Custom API endpoints

You can use any OpenAI-compatible or Anthropic-compatible API by setting the `base_url` in your assistant config:

```yaml
assistants:
  llama:
    provider: openai
    model: meta-llama/llama-3.3-70b-instruct
    base_url: https://openrouter.ai/api/v1
    api_key: <your_openrouter_key>
  
  together:
    provider: openai
    model: meta-llama/Llama-3-70b-chat-hf
    base_url: https://api.together.xyz/v1
    api_key: <your_together_key>
```

Or use environment variables for global configuration:

```bash
OPENAI_BASE_URL=https://api.together.xyz/v1 OPENAI_API_KEY=$TOGETHER_KEY gpt --model llama-3-70b
```

For Azure OpenAI, use the `azure-openai` provider:

```yaml
assistants:
  azure:
    provider: azure-openai
    model: my-deployment-name
```

#### Legacy model prefixes (backward compatibility)

The following model prefixes still work for backward compatibility:
- `oai-compat:model-name` - OpenAI-compatible API
- `openai:model-name` - OpenAI API with arbitrary model name
- `anthropic:model-name` - Anthropic API with arbitrary model name
- `oai-azure:deployment-name` - Azure OpenAI

## Other providers

### Anthropic Claude

Set up your API key:

```bash
export ANTHROPIC_API_KEY=<your_key_here>
# Optional: custom endpoint
export ANTHROPIC_BASE_URL=https://your-proxy.com
```

Or in config:

```yaml
anthropic_api_key: <your_key_here>
anthropic_base_url: <optional_custom_url>
```

Use Claude models:

```bash
gpt --provider anthropic --model claude-sonnet-4-20250514
gpt --model claude-3-opus-20240229    # provider auto-detected from model name
```

#### Claude 3.7 Sonnet Extended Thinking Mode

Claude 3.7 Sonnet supports an extended thinking mode, which shows Claude's reasoning process before delivering the final answer. This is useful for complex analysis, advanced STEM problems, and tasks with multiple constraints.

Enable it with the `--thinking` parameter, specifying the token budget for the thinking process:

```bash
gpt --model claude-3-7-sonnet-20250219 --thinking 32000
```

You can also configure thinking mode for specific assistants in your config:

```yaml
assistants:
  math:
    model: claude-3-7-sonnet-20250219
    thinking_budget: 32000
    messages:
      - { role: system, content: "You are a math expert." }
```

**Note**: When thinking mode is enabled, the temperature is automatically set to 1.0 and top_p is unset as required by the Claude API.

### Google Gemini

```bash
export GOOGLE_API_KEY=<your_key_here>
```

or

```yaml
google_api_key: <your_key_here>
```

### Cohere

```bash
export COHERE_API_KEY=<your_key_here>
```

or

```yaml
cohere_api_key: <your_key_here>
```

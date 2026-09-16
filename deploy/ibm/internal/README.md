# GSA Hackathon - Sandbox Environment Guide

The sandbox this guide accompanies is intended to provide the ability to develop MCP applications or other agentic tools and build agents to consume said tools. The sandbox environment includes a linux VM equipped with IBM Bob as the development bed and a separate SaaS-hosted instance of IBM watsonx Orchestrate (wxO) as the agentic AI platform.

## Pre-requisites:
This README file and the linked [Box Note](https://ibm.box.com/s/6ql9vvj9kali5iiefzl6qmvifas9ck85) with handy credentials are two extra resources to help you utilize the technologies in the sandbox environment.

The two technology components of the sandbox are shared with your IBMID via IBM Techzone. The share-emails from Techzone may look different:

### Accessing the Bob VM
The Bob VM is entirely accessible from the Techzone "Requests" page, which should be linked in the share-email. This page has:
- default user login information
- a private SSH key to connect to the VM via terminal only.
- a link to a browser-based VNC/RDP client to access the VM's desktop (which will be what you use to interact with Bob and develop the MCP application)
    - Note, the url to the VM desktop client is included in the [Box Note](https://ibm.box.com/s/6ql9vvj9kali5iiefzl6qmvifas9ck85), but it is easier to click the link from the Techzone Requests page, as it autofills the info for the first user login screen.
	- for the second login screen, you can type manually, or either "send text" or use the "sync clipboard" feature in RDP to copy+paste the uname/pwd 

### Accessing watsonx Orchestrate
Accessing the wxO instance is a little different. The shared email may come alongside an invitation to join an IBM Cloud account, and accessing the application follows a different process:
- accept the invitation, and log into [IBM Cloud](https://ibm.cloud.com/)
- go to the "Resource List" page from the left nav menu
- under the first dropdown category "AI / Machine Learning" should be the wxO resource - click it to go to the service landing page
- the service API Key and Instance URL are on this page - you will need them later. They're also in the accompanying [Box Note](https://ibm.box.com/s/6ql9vvj9kali5iiefzl6qmvifas9ck85) file
- click "Launch watsonx Orchestrate" to open the browser client in a new tab

## Developing an MCP application with IBM Bob and consuming it with wxO Agents

### Developing in the Bob VM
Note that using IBM Bob requires "bobcoins" (think similar to tokens). A caveat of this environment is that the Bob application hosted in the VM connects to IBM's Bob servers via your IBMID, bobcoins do not come "baked-in" to *this* environment. 

Anyone with an IBMID can start a free trial with 30 bobcoins - you will need to use this free trial to get bobcoins *for this sandbox environment*.

**This will *not* be the case in the hackathon - all participants will be provided sufficient bobcoins included in their environments during the event.**

With browser access to both the VM desktop and the wxO instance, you can start following the guide below, or explore on your own. Bob is a great helper and can get you to the finish line even without this documentation!

### Developing in the Bob VM

#### Set up project space
- log into VM on browser (two login screens, one for RDP, one for the VM login)
- open Bob (can search for "Bob" in main search) and sign in using IBMID
	- utilize free trial to gain bobcoins
- create a project folder (e.g., `~/Documents/bob-wxo-hackathon`)
- open folder in Bob (just like you would with VSCode)

#### Install dependencies
The IBM watsonx Orchestrate "Agent Development Kit" or ADK is available as a Python or NodeJS package. Below are the steps for Python (which I prefer). Bob can easily provide equivalent instructions for NodeJS, or even execute the steps itself!
- `sudo dnf install python3.12`
- `python3.12 -m venv .venv`
- `source ./.venv/bin/activate`
- `pip install ibm-watsonx-orchestrate`
- `orchestrate env add -n <wxo-environment-name> -u <wxo-instance-url> --type ibm_iam --activate`
```
orchestrate env add \
  -n gsa-hackathon-adk-env1 \
  -u https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/27065d2e-ac07-4ba7-a87c-e0d312129989 \
  --type ibm_iam \
  --activate
```

#### Develop MCP application
The documentation from here on out is generally higher-level, save a few example commands for common tasks. Bob is more than capable of helping you develop whatever MCP application ideas you may have and utilizing them locally. 
- develop and test the MCP application locally
- create app, build, add config to `.bob/mcp.json` all with Bob
- bundle generated MCP server files into a .zip file
- e.g., `zip -r my-node-mcp-server.zip src/ package.json package-lock.json tsconfig.json` for a NodeJS application
- or, `zip -r my-py-mcp-server.zip server.py requirements.txt` for a Python application
	- *note*: this Python MCP server is distinct from a Python Toolkit in wxO
- Push MCP server bundle to wxO as a toolkit:
- for NodeJS:
```
orchestrate toolkits add \
--kind mcp \
--name my-node-mcp-server \
--description "description of mcp server" \
--package-root "/<full>/<path>/<to>/my-node-mcp-server.zip" \
--command '["node", "build/index.js"]' \
--tools "*"
```
- for Python:
```
orchestrate toolkits add \
--kind mcp \
--name my-py-mcp-server \
--description "description of mcp server" \
 --package-root "/<full>/<path>/<to>/my-py-mcp-server.zip" \
 --command '["python", "server.py"]' \
 --tools "*"
```

### Consume MCP application with wxO Agents
`orchestrate toolkits add` pushes the MCP server bundle up to wxO, and deploys it within the SaaS tenant as a tool for agents to access. With your MCP app now deployed, you can build an AI agent to consume your newly developed tool (or tools)!

First, from Techzone or the email link, go to [IBM Cloud](https://cloud.ibm.com/), go to the Resource List, and click the watsonx Orchestrate resource under the top dropdown menu to go to the wxO landing page. Click "Launch watsonx Orchestrate" to open the wxO client in a new browser tab.

This environment was already used to demonstrate this process (and write this documentation), so there is already an MCP application deployed, and an Agent built to consume it:
- Click the hamburger menu in the top left and click on either "Chat" or "Build" 
	- under "Chat", switch the current agent from "AskOrchestrate" to "Local MCP Test" and use the chat interface to converse with the agent
	- under "Build", click the "Local MCP Test" agent to open the internal configuration and live-updating chat interface (i.e., you can change the agents behavior and the changes are immediately reflected in the chat)
- The demo MCP tools this agent has access to provides live stock information from Yahoo Finance
- you can prompt the agent with things like "Tell me about Fords stock price history from the past year" and it will use its tools to gather the info and relay that information to you conversationally.

This guide is not necessarily a walkthrough on how to use watsonx Orchestrate, but digging through the configuration and settings for the "Local MCP Test" agent should give a good set of the basic requirements and definitions an agent needs to have in wxO, as well as how to provide it with tools, MCP or otherwise!

For more guides on wxO specifically, the [watsonx Orchestrate ADK documentation](https://developer.watson-orchestrate.ibm.com/) has some great [tutorials](https://developer.watson-orchestrate.ibm.com/tutorials/tutorial_1_hello_world) to get started. This documentation is for the ADK specifically, so the tutorials show how to develop agents via code and deploy via terminal commands, *but*, the same information - agent name, description, instructions, etc - would be input in the browser UI to achieve the same end results.

If you have specific questions, Bob is also quite knowledgeable about IBM technologies and can serve as a guide to creating agents in wxO, either providing instructions for using the UI, or using the ADK to execute terminal commands itself.

I am also quite knowledgeable about IBM technologies and am happy to handle any questions you only see fit for human-answering! Please email me at ericmusa@ibm.com.

I hope you enjoy testing out IBM's technology as much as I do!
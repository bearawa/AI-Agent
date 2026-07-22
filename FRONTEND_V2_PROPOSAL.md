# AIZS Frontend Optimization Proposal (V2)

Based on the recent refactoring to a Next.js + FastAPI architecture, the following optimizations have been implemented and proposed to further enhance the User Experience and align with the Zhongnan University of Economics and Law (ZUEL) branding.

## 1. Implemented Optimizations (Current)

### 1.1 Markdown Rendering Support
The raw text output from the LLM has been upgraded to support rich Markdown rendering.
- **Dependencies Added:** `react-markdown` and `remark-gfm`.
- **Improvements:**
  - Lists, bold text, links, and tables are now properly formatted.
  - The AI output is significantly cleaner and more readable for users.

### 1.2 ZUEL Branding Integration
The university's official logo has been incorporated into the UI to reinforce the platform's identity.
- **Sidebar:** The ZUEL logo is displayed prominently at the top of the sidebar.
- **Empty State:** When starting a new chat session, the ZUEL logo is displayed above the "AIZS 智能咨询" title, utilizing opacity and grayscale effects for a subtle, modern look.

## 2. Proposed Future Optimizations

### 2.1 UI/UX Enhancements
- **Typing Indicator:** Instead of a simple pulsing block `▍`, implement a smooth, animated ellipsis (`...`) or a custom Lottie animation when the AI is processing/typing.
- **Syntax Highlighting:** For any code blocks returned by the AI, integrate `react-syntax-highlighter` into the Markdown renderer to provide proper color coding.
- **Smooth Scrolling:** Improve the auto-scroll mechanism to use smooth behavior (`behavior: 'smooth'`) and only auto-scroll if the user is already near the bottom of the chat.

### 2.2 Functional Improvements
- **Stop Generation:** Add a "Stop Generating" button that allows users to interrupt the AI's streaming response if they realize they made a mistake in their prompt.
- **Regenerate Response:** Provide a button below AI responses to trigger a regeneration of the answer using the same context.
- **Copy to Clipboard:** Add a simple "Copy" button to AI message blocks for easy extraction of information.

### 2.3 Visual Design (Tailwind)
- **Glassmorphism:** Apply slight translucency and background blur (`backdrop-blur-md bg-white/70`) to the sticky input area at the bottom.
- **Theme Toggle:** Introduce a manual Light/Dark mode toggle in the UI (currently it relies purely on system preference via Tailwind's `dark:` modifier).

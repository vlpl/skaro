/**
 * Lightweight markdown → HTML renderer.
 * Handles: headers, bold, italic, code blocks, inline code, lists,
 * blockquotes, tables, checkboxes, HR.
 * @param {string} text
 * @returns {string}
 */
export function renderMarkdown(text) {
	if (!text) return '';

	// ── Strip outer ```markdown wrapper (LLMs often wrap entire response) ──
	let h = text.replace(/^\s*```(?:markdown|md)?\s*\n([\s\S]*?)\n\s*```\s*$/g, '$1');

	// ── Pre-pass: extract code blocks & inline code before escaping ──
	const slots = [];

	function slot(html) {
		const id = `\x00SLOT${slots.length}\x00`;
		slots.push(html);
		return id;
	}

	// Fenced code blocks: ``` at start of line
	h = h.replace(/^```(\w*)\n([\s\S]*?)^```$/gm, (_, _lang, code) =>
		slot(`<pre><code>${esc(code.trimEnd())}</code></pre>`)
	);

	// Inline code
	h = h.replace(/`([^`\n]+)`/g, (_, code) =>
		slot(`<code>${esc(code)}</code>`)
	);

	// ── Escape remaining text ──
	h = esc(h);

	// Headers
	h = h.replace(/^### (.+)$/gm, '<h3>$1</h3>');
	h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
	h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
	// Bold, italic
	h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
	h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
	// Blockquote
	h = h.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
	// HR
	h = h.replace(/^---$/gm, '<hr>');
	// Checkbox lists (must come before generic list rule)
	h = h.replace(/^- \[x\] (.+)$/gim, '<li>☑ $1</li>');
	h = h.replace(/^- \[ \] (.+)$/gm, '<li>☐ $1</li>');
	// Lists
	h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
	h = h.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
	// Tables
	h = h.replace(/^\|(.+)\|$/gm, (_, row) => {
		const cells = row.split('|').map((c) => c.trim());
		if (cells.every((c) => /^[-:]+$/.test(c))) return '<!--sep-->';
		return '<tr>' + cells.map((c) => `<td>${c}</td>`).join('') + '</tr>';
	});
	h = h.replace(/((?:\s*(?:<tr>.*?<\/tr>|<!--sep-->)\s*)+)/g, (block) => {
		const rows = block.replace(/<!--sep-->/g, '').trim();
		if (!rows) return '';
		const promoted = rows.replace(
			/^<tr>(.*?)<\/tr>/,
			(_, inner) => '<thead><tr>' + inner.replace(/<td>/g, '<th>').replace(/<\/td>/g, '</th>') + '</tr></thead>'
		);
		return `<table>${promoted}</table>`;
	});
	// Paragraphs
	h = h.replace(/\n\n/g, '</p><p>');
	h = '<p>' + h + '</p>';
	h = h.replace(/<p>\s*<(h[123]|pre|blockquote|table|hr|li|ul|ol)/g, '<$1');
	h = h.replace(/<\/(h[123]|pre|blockquote|table|hr|li|ul|ol)>\s*<\/p>/g, '</$1>');
	h = h.replace(/<p>\s*<\/p>/g, '');
	// Wrap consecutive <li>
	h = h.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
	h = h.replace(/<\/ul>\s*<ul>/g, '');

	// ── Restore slots ──
	for (let i = 0; i < slots.length; i++) {
		h = h.replace(`\x00SLOT${i}\x00`, slots[i]);
	}

	return h;
}

/** @param {string} s */
export function esc(s) {
	return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Parse clarifications.md into structured Q&A blocks.
 * @param {string} text
 * @returns {{ num: number, question: string, answer: string }[]}
 */
export function parseClarifications(text) {
	const blocks = [];
	const parts = text.split(/^## Question\s+(\d+)\s*$/m);
	for (let i = 1; i < parts.length - 1; i += 2) {
		const num = parseInt(parts[i], 10);
		const block = parts[i + 1];

		// Split off answer
		const answerSplit = block.split(/^\*\*Answer:\*\*\s*$/m);
		const beforeAnswer = answerSplit[0] || '';
		const answer = (answerSplit[1] || '').trim();

		// Extract context
		const ctxMatch = beforeAnswer.match(/^\*Context:\*\s*(.+)$/m);
		const context = ctxMatch ? ctxMatch[1].trim() : '';

		// Extract options
		const options = [];
		const optsSplit = beforeAnswer.split(/^\*\*Options:\*\*\s*$/m);
		if (optsSplit.length > 1) {
			const optBlock = optsSplit[1];
			for (const m of optBlock.matchAll(/^- [A-Z]\)\s*(.+)$/gm)) {
				options.push(m[1].trim());
			}
		}

		// Question text: remove context + options markers
		let question = beforeAnswer
			.replace(/^\*Context:\*\s*.+$/m, '')
			.replace(/^\*\*Options:\*\*[\s\S]*$/m, '')
			.trim();

		blocks.push({ num, question, context, options, answer });
	}
	return blocks;
}

/**
 * Parse clarify questions from LLM response text.
 * @param {string} text
 * @returns {string[]}
 */
export function parseClarifyQuestions(text) {
	const questions = [];
	const lines = text.split('\n');
	let current = [];
	let inQuestion = false;
	const re = /^(\*{0,2}\s*(?:Question\s+|Q)\d+[\s:.)\*]|(?:\*{2})?\d+[\s:.)\*])/i;

	for (const line of lines) {
		if (re.test(line.trim())) {
			if (current.length > 0 && inQuestion) {
				questions.push(current.join('\n').trim());
			}
			current = [line];
			inQuestion = true;
		} else if (inQuestion) {
			current.push(line);
		}
	}
	if (current.length > 0 && inQuestion) {
		questions.push(current.join('\n').trim());
	}
	return questions;
}

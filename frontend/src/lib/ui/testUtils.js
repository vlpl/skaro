/**
 * Build a text summary of failed checks and commands for LLM consumption.
 *
 * @param {Array} checklist - Array of {passed, label, detail}
 * @param {Array} commands  - Array of {success, name, command, exit_code, stdout, stderr}
 * @returns {string}
 */
export function buildErrorSummary(checklist = [], commands = []) {
	const parts = [];

	for (const check of checklist) {
		if (!check.passed) {
			parts.push(`[FAIL] ${check.label}: ${check.detail}`);
		}
	}

	for (const cmd of commands) {
		if (!cmd.success) {
			const output = (cmd.stderr || cmd.stdout || '').trim();
			const truncated = output.length > 2000 ? output.slice(-2000) : output;
			parts.push(`[FAIL] ${cmd.name} (${cmd.command})\nExit code: ${cmd.exit_code}\n${truncated}`);
		}
	}

	return parts.join('\n\n---\n\n');
}

/**
 * Format an issue for display in the issues list.
 *
 * @param {{ type: string, severity: string, title: string, detail: string, command?: string }} issue
 * @returns {{ icon: string, label: string }}
 */
export function formatIssueLabel(issue) {
	const icon = issue.type === 'command' ? '⚠' : '○';
	const detail = issue.detail ? ` — ${issue.detail}` : '';
	return { icon, label: `${issue.title}${detail}` };
}
